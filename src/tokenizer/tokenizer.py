"""

Tokenizer for Icelandic text

Copyright (C) 2016-2025 Miðeind ehf.
Original author: Vilhjálmur Þorsteinsson

This software is licensed under the MIT License:

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without restriction,
    including without limitation the rights to use, copy, modify, merge,
    publish, distribute, sublicense, and/or sell copies of the Software,
    and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


The function tokenize() consumes a text string and
returns a generator of tokens. Each token is a
named tuple, having the form (kind, txt, val),
where kind is one of the constants specified in the
TOK class, txt is the original source text,
and val contains auxiliary information
depending on the token type (such as the meaning of
an abbreviation, or the day, month and year for dates).

"""

from typing import (
    Any,
    Callable,
    Deque,
    Iterable,
    Iterator,
    List,
    Mapping,
    Match,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

import datetime
import re
import unicodedata  # type: ignore
from collections import deque

from .abbrev import Abbreviations
from .definitions import *  # noqa: F403

_T = TypeVar("_T", bound="Tok")


# Set of punctuation characters that are grouped into one
# normalized exclamation
EXCLAMATIONS = frozenset(("!", "?"))

# Global constants for readability
SPAN_START = 0
SPAN_END = 1


class Tok:
    """Information about a single token"""

    def __init__(
        self,
        kind: int,
        txt: Optional[str],
        val: ValType,
        original: Optional[str] = None,
        origin_spans: Optional[list[int]] = None,
    ) -> None:
        # Type of token
        self.kind: int = kind
        # Text of the token
        self.txt: str = txt or ""
        # Value of the token (e.g. if it is a date or currency)
        self.val: ValType = val
        # The full original source string behind this token.
        # If this is None then we're not tracking origins.
        self.original: Optional[str] = original
        # origin_spans contains an integer for each character in 'txt'.
        # Each such integer index maps the corresponding character
        # (which may have substitutions) to its index in 'original'.
        # This is required to preserve 'original' correctly when splitting.
        self.origin_spans: Optional[list[int]] = origin_spans

    @classmethod
    def from_txt(cls: Type[_T], txt: str) -> _T:
        """Create a token from text"""
        return cls(TOK.RAW, txt, None, txt, list(range(len(txt))))

    @classmethod
    def from_token(cls: Type[_T], t: "Tok") -> _T:
        """Create a new Tok instance by copying from a previously existing one"""
        return cls(
            t.kind,
            t.txt,
            t.val,
            t.original,
            None if t.origin_spans is None else t.origin_spans[:],
        )

    @property
    def punctuation(self) -> str:
        """Return the punctuation symbol associated with the
        token, if it is in fact a punctuation token"""

        if self.kind != TOK.PUNCTUATION:
            # This is not a punctuation token. In that case,
            # we return the Unicode 'unrecognized character'
            # code, which will not match any 'x in s' checks
            # where s is a legitimate string or set.
            return "\ufffd"
        return cast(PunctuationTuple, self.val)[1]

    @property
    def number(self) -> float:
        """Return a float embedded in a Number or Year token"""
        if self.kind == TOK.YEAR:
            return float(cast(int, self.val))
        if self.kind == TOK.NUMBER:
            return cast(NumberTuple, self.val)[0]
        raise ValueError("Expected NUMBER or YEAR token in Tok.number()")

    @property
    def integer(self) -> int:
        """Return an integer from a token, which is assumed
        to be a Number or a Year token"""
        if self.kind == TOK.YEAR:
            return cast(int, self.val)
        if self.kind == TOK.NUMBER:
            return int(cast(NumberTuple, self.val)[0])
        raise ValueError("Expected NUMBER or YEAR token in Tok.integer()")

    @property
    def ordinal(self) -> int:
        """Return an ordinal number from a token,
        which is assumed to be a Number or an Ordinal token"""
        if self.kind == TOK.ORDINAL:
            return cast(int, self.val)
        if self.kind == TOK.NUMBER:
            return int(cast(NumberTuple, self.val)[0])
        raise ValueError("Expected NUMBER or ORDINAL token in Tok.ordinal()")

    @property
    def has_meanings(self) -> bool:
        """Return True if this is a word token and has meanings,
        i.e. associated BIN_Tuple instances"""
        if self.kind != TOK.WORD:
            return False
        return bool(self.val)

    @property
    def meanings(self) -> BIN_TupleList:
        """Return the meanings of this token if it is a word,
        otherwise return an empty list"""
        if self.kind != TOK.WORD:
            return []
        return cast(BIN_TupleList, self.val) or []

    @property
    def person_names(self) -> PersonNameList:
        """Return the person names of this token if it denotes a PERSON,
        otherwise return an empty list"""
        if self.kind != TOK.PERSON:
            return []
        return cast(PersonNameList, self.val) or []

    def split(self, pos: int) -> Tuple["Tok", "Tok"]:
        """Split this token into two at 'pos'.
        The first token returned will have 'pos'
        characters and the second one will have the rest.
        """
        # TODO: What happens if you split a token that has
        # txt=="" and original!=""?
        # TODO: What should we do with val?

        ltk: Tok
        rtk: Tok

        if self.origin_spans is not None and self.original is not None:
            if pos >= len(self.origin_spans):
                ltk = Tok(
                    self.kind,
                    self.txt,
                    self.val,
                    self.original,
                    self.origin_spans,
                )
                rtk = Tok(self.kind, "", None, "", [])
            else:
                ltk = Tok(
                    self.kind,
                    self.txt[:pos],
                    self.val,
                    self.original[: self.origin_spans[pos]],
                    self.origin_spans[:pos],
                )
                rtk = Tok(
                    self.kind,
                    self.txt[pos:],
                    self.val,
                    self.original[self.origin_spans[pos] :],
                    [x - self.origin_spans[pos] for x in self.origin_spans[pos:]],
                )
        else:
            ltk = Tok(self.kind, self.txt[:pos], self.val)
            rtk = Tok(self.kind, self.txt[pos:], self.val)

        return ltk, rtk

    def substitute(self, span: Tuple[int, int], new: str) -> None:
        """Substitute a span with a single or empty character 'new'."""
        self.txt = self.txt[: span[0]] + new + self.txt[span[1] :]
        if self.origin_spans is not None:
            # Remove origin entries that correspond to characters that are gone.
            self.origin_spans = (
                self.origin_spans[: span[0] + len(new)] + self.origin_spans[span[1] :]
            )

    def substitute_longer(self, span: Tuple[int, int], new: str) -> None:
        """Substitute a span with a potentially longer string"""

        # This tracks origin differently from the regular
        # substitution function.
        # Due to the inobviousness of how to assign origin to
        # the new string we simply make it have an empty origin.
        # This will probably cause some weirdness if this string
        # later gets split or substituted but that should not
        # happen in the current implementation.

        self.txt = self.txt[: span[0]] + new + self.txt[span[1] :]

        if self.origin_spans is not None and self.original is not None:
            head = self.origin_spans[: span[0]]
            tail = self.origin_spans[span[1] :]

            # The origin span of the new stuff will be of length 0 since we can't
            # proprely attribute it to individual characters in the original string.

            if len(tail) == 0:
                # We're replacing the end of the string
                # Can't pick the next element after the removed
                # string since it doesn't exist
                # Use the length instead
                new_origin = len(self.original)
            else:
                new_origin = self.origin_spans[span[1]]

            self.origin_spans = head + [new_origin] * len(new) + tail

    def substitute_all(self, old_str: str, new_char: str) -> None:
        """Substitute all occurrences of 'old_str' with 'new_char'.
        The new character may be empty.
        """
        # NOTE: This implementation is worst-case-quadratic in the
        #       length of the token text.
        #       Fortunately tokens are almost always (?) short so
        #       this is an acceptable tradeoff for a simple implementation.
        # TODO: Support arbitrary length substitutions?
        #       What does that do to origin tracking?

        assert len(new_char) <= 1, f"'new_char' ({new_char}) was too long."

        while True:
            i = self.txt.find(old_str)
            if i == -1:
                # No occurences of 'old_str' remain
                break
            self.substitute((i, i + len(old_str)), new_char)

    def concatenate(
        self,
        other: "Tok",
        *,
        separator: str = "",
        metadata_from_other: bool = False,
    ) -> "Tok":
        """Return a new token that consists of self with other
        concatenated to the end.
        A separator can optionally be supplied.
        The new token will have metadata (kind and val)
        from self unless 'metadata_from_other' is True.
        """
        new_kind = self.kind if not metadata_from_other else other.kind
        new_val = self.val if not metadata_from_other else other.val

        self_txt = self.txt or ""
        other_txt = other.txt or ""
        new_txt = self_txt + separator + other_txt

        self_original = self.original or ""
        other_original = other.original or ""
        new_original = self_original + other_original

        self_origin_spans = self.origin_spans or []
        other_origin_spans = other.origin_spans or []
        separator_origin_spans: List[int] = (
            [len(self_original)] * len(separator) if len(other_origin_spans) > 0 else []
        )
        new_origin_spans = (
            self_origin_spans
            + separator_origin_spans
            + [i + len(self_original) for i in other_origin_spans]
        )

        return Tok(new_kind, new_txt, new_val, new_original, new_origin_spans)

    @property
    def as_tuple(self) -> Tuple[Any, ...]:
        """Return the contents of this token as a generic tuple,
        suitable e.g. for serialization"""
        return (self.kind, self.txt, self.val)

    def __getitem__(self, i: int) -> Union[int, str, ValType]:
        """Backwards compatibility for when Tok was a namedtuple."""
        if i == 0:
            return self.kind
        elif i == 1:
            return self.txt
        elif i == 2:
            return self.val
        else:
            raise IndexError("Tok can only be indexed by 0, 1 or 2")

    def equal(self, other: "Tok") -> bool:
        """Equality of content between two tokens, i.e. ignoring the
        'original' and 'origin_spans' attributes"""
        return (
            self.kind == other.kind and self.txt == other.txt and self.val == other.val
        )

    def __eq__(self, o: object) -> bool:
        """Full equality between two Tok instances"""
        if not isinstance(o, Tok):
            return False
        return (
            self.kind == o.kind
            and self.txt == o.txt
            and self.val == o.val
            and self.original == o.original
            and self.origin_spans == o.origin_spans
        )

    def __repr__(self) -> str:
        def quoted_string_repr(obj: object) -> str:
            if isinstance(obj, str):
                return f'"{obj}"'
            return str(obj)

        return (
            f"Tok({self.kind}, {quoted_string_repr(self.txt)}, "
            f"{self.val}, {quoted_string_repr(self.original)}, {self.origin_spans})"
        )


class TOK:
    """
    The TOK class contains constants that define token types and
    constructors for creating token instances.

    Each of the various constructors can accept as first parameter either
    a string or a Tok object.

    The string version is the old one (from versions 2 and earlier).
    These take in a string and sometimes value and return a token with
    that string and value.
    This should be preserved while there are downstream users that depend on
    this behavior. The tokenizer does not use this internally.

    The Tok version of the constructors isn't really a constructor but rather
    a converter. It takes in a token and returns a token with the given type
    and value but preserves other attributes, in particular origin tracking.
    Note that the current version modifies the input and returns it again.
    This particular detail should not be depended on (assume the input is eaten
    and something new is returned).

    If, at some point, we can be reasonably certain that downstream users are
    not using the string version any more we should consider removing it.
    """

    # Token types

    # Raw minimally processed token
    RAW = -1

    # Punctuation
    PUNCTUATION = 1
    # Time hh:mm:ss
    TIME = 2
    # Date yyyy-mm-dd
    DATE = 3
    # Year, four digits
    YEAR = 4
    # Number, integer or real
    NUMBER = 5
    # Word, which may contain hyphens and apostrophes
    WORD = 6
    # Telephone number: 7 digits, eventually preceded by country code
    TELNO = 7
    # Percentage (number followed by percent or promille sign)
    PERCENT = 8
    # A Uniform Resource Locator (URL): https://example.com/path?p=100
    URL = 9
    # An ordinal number, eventually using Roman numerals (1., XVII.)
    ORDINAL = 10
    # A timestamp (not emitted by Tokenizer)
    TIMESTAMP = 11
    # A currency sign or code
    CURRENCY = 12
    # An amount, i.e. a quantity with a currency code
    AMOUNT = 13
    # Person name (not used by Tokenizer)
    PERSON = 14
    # E-mail address (somebody@somewhere.com)
    EMAIL = 15
    # Entity name (not used by Tokenizer)
    ENTITY = 16
    # Unknown token type
    UNKNOWN = 17
    # Absolute date
    DATEABS = 18
    # Relative date
    DATEREL = 19
    # Absolute time stamp, yyyy-mm-dd hh:mm:ss
    TIMESTAMPABS = 20
    # Relative time stamp, yyyy-mm-dd hh:mm:ss
    # where at least of yyyy, mm or dd is missing
    TIMESTAMPREL = 21
    # A measured quantity with its unit (220V, 0.5 km)
    MEASUREMENT = 22
    # Number followed by letter (a-z), often seen in addresses (Skógarstígur 4B)
    NUMWLETTER = 23
    # Internet domain name (an.example.com)
    DOMAIN = 24
    # Hash tag (#metoo)
    HASHTAG = 25
    # Chemical compound ('H2SO4')
    MOLECULE = 26
    # Social security number ('kennitala')
    SSN = 27
    # Social media user name ('@username_123')
    USERNAME = 28
    # Serial number ('394-8362')
    SERIALNUMBER = 29
    # Company name ('Google Inc.')
    COMPANY = 30

    # Sentinel value to for metatokens.
    # Metatokens are tokens that are not directly based on characters in the text.
    # Users can compare a token's kind with META_BEGIN to distinguish between
    # metatokens and other tokens.
    # Regular token kinds have a value less than META_BEGIN and
    # metatokens have a kind greater than META_BEGIN.
    META_BEGIN = 9999

    # Sentence split token
    S_SPLIT = 10000
    # Paragraph begin
    P_BEGIN = 10001
    # Paragraph end
    P_END = 10002
    # Sentence begin
    S_BEGIN = 11001
    # Sentence end
    S_END = 11002
    # End sentinel
    X_END = 12001

    END = frozenset((P_END, S_END, X_END, S_SPLIT))
    BEGIN = frozenset((P_BEGIN, S_BEGIN))
    TEXT = frozenset((WORD, PERSON, ENTITY, MOLECULE, COMPANY))
    TEXT_EXCL_PERSON = frozenset((WORD, ENTITY, MOLECULE, COMPANY))

    # Token descriptive names

    descr: Mapping[int, str] = {
        PUNCTUATION: "PUNCTUATION",
        TIME: "TIME",
        TIMESTAMP: "TIMESTAMP",
        TIMESTAMPABS: "TIMESTAMPABS",
        TIMESTAMPREL: "TIMESTAMPREL",
        DATE: "DATE",
        DATEABS: "DATEABS",
        DATEREL: "DATEREL",
        YEAR: "YEAR",
        NUMBER: "NUMBER",
        NUMWLETTER: "NUMWLETTER",
        CURRENCY: "CURRENCY",
        AMOUNT: "AMOUNT",
        MEASUREMENT: "MEASUREMENT",
        PERSON: "PERSON",
        WORD: "WORD",
        UNKNOWN: "UNKNOWN",
        TELNO: "TELNO",
        PERCENT: "PERCENT",
        URL: "URL",
        DOMAIN: "DOMAIN",
        HASHTAG: "HASHTAG",
        EMAIL: "EMAIL",
        ORDINAL: "ORDINAL",
        ENTITY: "ENTITY",
        MOLECULE: "MOLECULE",
        SSN: "SSN",
        USERNAME: "USERNAME",
        SERIALNUMBER: "SERIALNUMBER",
        COMPANY: "COMPANY",
        S_SPLIT: "SPLIT SENT",
        P_BEGIN: "BEGIN PARA",
        P_END: "END PARA",
        S_BEGIN: "BEGIN SENT",
        S_END: "END SENT",
    }

    # Token constructors

    @staticmethod
    def Punctuation(t: Union[Tok, str], normalized: Optional[str] = None) -> Tok:
        tp = TP_CENTER  # Default punctuation type
        if normalized is None:
            if isinstance(t, str):
                normalized = t
            else:
                normalized = t.txt
        if normalized and len(normalized) == 1:
            if normalized in LEFT_PUNCTUATION:
                tp = TP_LEFT
            elif normalized in RIGHT_PUNCTUATION:
                tp = TP_RIGHT
            elif normalized in NONE_PUNCTUATION:
                tp = TP_NONE
        if isinstance(t, str):
            return Tok(TOK.PUNCTUATION, t, (tp, normalized))
        t.kind = TOK.PUNCTUATION
        t.val = (tp, normalized)
        return t

    @staticmethod
    def Time(t: Union[Tok, str], h: int, m: int, s: int) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.TIME, t, (h, m, s))
        t.kind = TOK.TIME
        t.val = (h, m, s)
        return t

    @staticmethod
    def Date(t: Union[Tok, str], y: int, m: int, d: int) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.DATE, t, (y, m, d))
        t.kind = TOK.DATE
        t.val = (y, m, d)
        return t

    @staticmethod
    def Dateabs(t: Union[Tok, str], y: int, m: int, d: int) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.DATEABS, t, (y, m, d))
        t.kind = TOK.DATEABS
        t.val = (y, m, d)
        return t

    @staticmethod
    def Daterel(t: Union[Tok, str], y: int, m: int, d: int) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.DATEREL, t, (y, m, d))
        t.kind = TOK.DATEREL
        t.val = (y, m, d)
        return t

    @staticmethod
    def Timestamp(
        t: Union[Tok, str], y: int, mo: int, d: int, h: int, m: int, s: int
    ) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.TIMESTAMP, t, (y, mo, d, h, m, s))
        t.kind = TOK.TIMESTAMP
        t.val = (y, mo, d, h, m, s)
        return t

    @staticmethod
    def Timestampabs(
        t: Union[Tok, str], y: int, mo: int, d: int, h: int, m: int, s: int
    ) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.TIMESTAMPABS, t, (y, mo, d, h, m, s))
        t.kind = TOK.TIMESTAMPABS
        t.val = (y, mo, d, h, m, s)
        return t

    @staticmethod
    def Timestamprel(
        t: Union[Tok, str], y: int, mo: int, d: int, h: int, m: int, s: int
    ) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.TIMESTAMPREL, t, (y, mo, d, h, m, s))
        t.kind = TOK.TIMESTAMPREL
        t.val = (y, mo, d, h, m, s)
        return t

    @staticmethod
    def Year(t: Union[Tok, str], n: int) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.YEAR, t, n)
        t.kind = TOK.YEAR
        t.val = n
        return t

    @staticmethod
    def Telno(t: Union[Tok, str], telno: str, cc: str = "354") -> Tok:
        # The t parameter is the original token text,
        # while telno has the standard form 'DDD-DDDD' (with hyphen)
        # cc is the country code
        if isinstance(t, str):
            return Tok(TOK.TELNO, t, (telno, cc))
        t.kind = TOK.TELNO
        t.val = (telno, cc)
        return t

    @staticmethod
    def Email(t: Union[Tok, str]) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.EMAIL, t, None)
        t.kind = TOK.EMAIL
        t.val = None
        return t

    @staticmethod
    def Number(
        t: Union[Tok, str],
        n: float,
        cases: Optional[list[str]] = None,
        genders: Optional[list[str]] = None,
    ) -> Tok:
        # The cases parameter is a list of possible cases for this number
        # (if it was originally stated in words)
        if isinstance(t, str):
            return Tok(TOK.NUMBER, t, (n, cases, genders))
        t.kind = TOK.NUMBER
        t.val = (n, cases, genders)
        return t

    @staticmethod
    def NumberWithLetter(t: Union[Tok, str], n: int, c: str) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.NUMWLETTER, t, (n, c))
        t.kind = TOK.NUMWLETTER
        t.val = (n, c)
        return t

    @staticmethod
    def Currency(
        t: Union[Tok, str],
        iso: str,
        cases: Optional[list[str]] = None,
        genders: Optional[list[str]] = None,
    ) -> Tok:
        # The cases parameter is a list of possible cases for this currency name
        # (if it was originally stated in words, i.e. not abbreviated)
        if isinstance(t, str):
            return Tok(TOK.CURRENCY, t, (iso, cases, genders))
        t.kind = TOK.CURRENCY
        t.val = (iso, cases, genders)
        return t

    @staticmethod
    def Amount(
        t: Union[Tok, str],
        iso: str,
        n: float,
        cases: Optional[list[str]] = None,
        genders: Optional[list[str]] = None,
    ) -> Tok:
        # The cases parameter is a list of possible cases for this amount
        # (if it was originally stated in words)
        if isinstance(t, str):
            return Tok(TOK.AMOUNT, t, (n, iso, cases, genders))
        t.kind = TOK.AMOUNT
        t.val = (n, iso, cases, genders)
        return t

    @staticmethod
    def Percent(
        t: Union[Tok, str],
        n: float,
        cases: Optional[list[str]] = None,
        genders: Optional[list[str]] = None,
    ) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.PERCENT, t, (n, cases, genders))
        t.kind = TOK.PERCENT
        t.val = (n, cases, genders)
        return t

    @staticmethod
    def Ordinal(t: Union[Tok, str], n: int) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.ORDINAL, t, n)
        t.kind = TOK.ORDINAL
        t.val = n
        return t

    @staticmethod
    def Url(t: Union[Tok, str]) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.URL, t, None)
        t.kind = TOK.URL
        t.val = None
        return t

    @staticmethod
    def Domain(t: Union[Tok, str]) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.DOMAIN, t, None)
        t.kind = TOK.DOMAIN
        t.val = None
        return t

    @staticmethod
    def Hashtag(t: Union[Tok, str]) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.HASHTAG, t, None)
        t.kind = TOK.HASHTAG
        t.val = None
        return t

    @staticmethod
    def Ssn(t: Union[Tok, str]) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.SSN, t, None)
        t.kind = TOK.SSN
        t.val = None
        return t

    @staticmethod
    def Molecule(t: Union[Tok, str]) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.MOLECULE, t, None)
        t.kind = TOK.MOLECULE
        t.val = None
        return t

    @staticmethod
    def Username(t: Union[Tok, str], username: str) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.USERNAME, t, username)
        t.kind = TOK.USERNAME
        t.val = username
        return t

    @staticmethod
    def SerialNumber(t: Union[Tok, str]) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.SERIALNUMBER, t, None)
        t.kind = TOK.SERIALNUMBER
        t.val = None
        return t

    @staticmethod
    def Measurement(t: Union[Tok, str], unit: str, val: float) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.MEASUREMENT, t, (unit, val))
        t.kind = TOK.MEASUREMENT
        t.val = (unit, val)
        return t

    @staticmethod
    def Word(t: Union[Tok, str], m: Optional[BIN_TupleList] = None) -> Tok:
        # The m parameter is intended for a list of BIN_Tuple instances
        # fetched from the BÍN database, in 'SHsnid' format
        if isinstance(t, str):
            return Tok(TOK.WORD, t, m)
        t.kind = TOK.WORD
        t.val = m
        return t

    @staticmethod
    def Unknown(t: Union[Tok, str]) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.UNKNOWN, t, None)
        t.kind = TOK.UNKNOWN
        t.val = None
        return t

    @staticmethod
    def Person(t: Union[Tok, str], m: Optional[PersonNameList] = None) -> Tok:
        # The m parameter is intended for a list of PersonName tuples:
        # (name, gender, case)
        if isinstance(t, str):
            return Tok(TOK.PERSON, t, m)
        t.kind = TOK.PERSON
        t.val = m
        return t

    @staticmethod
    def Entity(t: Union[Tok, str]) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.ENTITY, t, None)
        t.kind = TOK.ENTITY
        t.val = None
        return t

    @staticmethod
    def Company(t: Union[Tok, str]) -> Tok:
        if isinstance(t, str):
            return Tok(TOK.COMPANY, t, None)
        t.kind = TOK.COMPANY
        t.val = None
        return t

    @staticmethod
    def Begin_Paragraph() -> Tok:
        """Return a special paragraph begin marker token"""
        marker = Tok(TOK.P_BEGIN, "[[", None, "[[", list(range(2)))
        marker.substitute((0, 2), "")
        return marker

    @staticmethod
    def End_Paragraph() -> Tok:
        """Return a special paragraph end marker token"""
        marker = Tok(TOK.P_END, "]]", None, "]]", list(range(2)))
        marker.substitute((0, 2), "")
        return marker

    @staticmethod
    def Begin_Sentence(
        t: Optional[Tok] = None,
        num_parses: int = 0,
        err_index: Optional[int] = None,
    ) -> Tok:
        if t is None:
            return Tok(TOK.S_BEGIN, None, (num_parses, err_index))
        t.kind = TOK.S_BEGIN
        t.val = (num_parses, err_index)
        return t

    @staticmethod
    def End_Sentence(t: Optional[Tok] = None) -> Tok:
        if t is None:
            return Tok(TOK.S_END, None, None)
        t.kind = TOK.S_END
        t.val = None
        return t

    @staticmethod
    def End_Sentinel(t: Optional[Tok] = None) -> Tok:
        if t is None:
            return Tok(TOK.X_END, None, None)
        t.kind = TOK.X_END
        t.val = None
        return t

    @staticmethod
    def Split_Sentence(t: Optional[Tok] = None) -> Tok:
        if t is None:
            return Tok(TOK.S_SPLIT, None, None)
        t.kind = TOK.S_SPLIT
        t.val = None
        return t


class TokenStream:
    """Wrapper for token iterator allowing lookahead."""

    def __init__(self, token_it: Iterator[Tok], *, lookahead_size: int = 2):
        """Initialize from token iterator."""
        self._it: Iterator[Tok] = token_it
        if lookahead_size <= 0:
            lookahead_size = 1
        self._lookahead: Deque[Tok] = deque(maxlen=lookahead_size)
        self._max_lookahead: int = lookahead_size

    def __next__(self) -> Tok:
        if self._lookahead:
            return self._lookahead.popleft()
        return next(self._it)

    def __iter__(self):
        return self

    def __getitem__(self, i: int) -> Optional[Tok]:
        if 0 <= i < self._max_lookahead:
            llk = len(self._lookahead)
            try:
                while llk <= i:
                    # Extend deque to lookahead
                    self._lookahead.append(next(self._it))
                    llk += 1
                return self._lookahead[i]
            except StopIteration:
                pass
        return None

    def txt(self, i: int = 0) -> Optional[str]:
        """Return token.txt for token at index i."""
        t = self[i]
        return t.txt if t else None

    def kind(self, i: int = 0) -> Optional[int]:
        """Return token.kind for token at index i."""
        t = self[i]
        return t.kind if t else None

    def punctuation(self, i: int = 0) -> Optional[str]:
        """Return token.punctuation for token at index i."""
        t = self[i]
        return t.punctuation if t else None

    def number(self, i: int = 0) -> Optional[float]:
        """Return token.number for token at index i."""
        t = self[i]
        return t.number if t else None

    def integer(self, i: int = 0) -> Optional[int]:
        """Return token.integer for token at index i."""
        t = self[i]
        return t.integer if t else None

    def ordinal(self, i: int = 0) -> Optional[int]:
        """Return token.ordinal for token at index i."""
        t = self[i]
        return t.ordinal if t else None

    def has_meanings(self, i: int = 0) -> Optional[bool]:
        """Return token.has_meanings for token at index i."""
        t = self[i]
        return t.has_meanings if t else None

    def meanings(self, i: int = 0) -> Optional[BIN_TupleList]:
        """Return token.meanings for token at index i."""
        t = self[i]
        return t.meanings if t else None

    def person_names(self, i: int = 0) -> Optional[PersonNameList]:
        """Return token.person_names for token at index i."""
        t = self[i]
        return t.person_names if t else None

    def as_tuple(self, i: int = 0) -> Optional[tuple[Any, ...]]:
        """Return token.as_tuple for token at index i."""
        t = self[i]
        return t.as_tuple if t else None

    def could_be_end_of_sentence(self, i: int = 0, *args: Any) -> bool:
        """Wrapper to safely check if token at index i could be end of sentence."""
        t = self[i]
        return could_be_end_of_sentence(t, *args) if t else False


def normalized_text(token: Tok) -> str:
    """Returns token text after normalizing punctuation"""
    return (
        cast(tuple[int, str], token.val)[1]
        if token.kind == TOK.PUNCTUATION
        else token.txt
    )


def text_from_tokens(tokens: Iterable[Tok]) -> str:
    """Return text from a list of tokens, without normalization"""
    return " ".join(t.txt for t in tokens if t.txt)


def normalized_text_from_tokens(tokens: Iterable[Tok]) -> str:
    """Return text from a list of tokens, with normalization"""
    return " ".join(filter(None, map(normalized_text, tokens)))


def is_valid_date(y: int, m: int, d: int) -> bool:
    """Returns True if y, m, d is a valid date"""
    if (1776 <= y <= 2100) and (1 <= m <= 12) and (1 <= d <= DAYS_IN_MONTH[m]):
        try:
            datetime.datetime(year=y, month=m, day=d)
            return True
        except ValueError:
            pass
    return False


def parse_digits(tok: Tok, convert_numbers: bool) -> Tuple[Tok, Tok]:
    """Parse a raw token starting with a digit"""
    w = tok.txt
    s: Optional[Match[str]] = re.match(r"\d{1,2}:\d\d:\d\d,\d\d(?!\d)", w)
    g: str
    n: str
    if s:
        # Looks like a 24-hour clock with milliseconds, H:M:S:MS
        # TODO use millisecond information in token
        g = s.group()
        p = g.split(":")
        h = int(p[0])
        m = int(p[1])
        sec = int(p[2].split(",")[0])
        if (0 <= h < 24) and (0 <= m < 60) and (0 <= sec < 60):
            t, rest = tok.split(s.end())
            return TOK.Time(t, h, m, sec), rest

    s = re.match(r"\d{1,2}:\d\d:\d\d(?!\d)", w)
    if s:
        # Looks like a 24-hour clock, H:M:S
        g = s.group()
        p = g.split(":")
        h = int(p[0])
        m = int(p[1])
        sec = int(p[2])
        if (0 <= h < 24) and (0 <= m < 60) and (0 <= sec < 60):
            t, rest = tok.split(s.end())
            return TOK.Time(t, h, m, sec), rest

    s = re.match(r"\d{1,2}:\d\d(?!\d)", w)
    if s:
        # Looks like a 24-hour clock, H:M
        g = s.group()
        p = g.split(":")
        h = int(p[0])
        m = int(p[1])
        if (0 <= h < 24) and (0 <= m < 60):
            t, rest = tok.split(s.end())
            return TOK.Time(t, h, m, 0), rest

    s = re.match(r"((\d{4}-\d\d-\d\d)|(\d{4}/\d\d/\d\d))(?!\d)", w)
    if s:
        # Looks like an ISO format date: YYYY-MM-DD or YYYY/MM/DD
        g = s.group()
        if "-" in g:
            p = g.split("-")
        else:
            p = g.split("/")
        y = int(p[0])
        m = int(p[1])
        d = int(p[2])
        if is_valid_date(y, m, d):
            t, rest = tok.split(s.end())
            return TOK.Date(t, y, m, d), rest

    s = (
        re.match(r"\d{1,2}\.\d{1,2}\.\d{2,4}(?!\d)", w)
        or re.match(r"\d{1,2}/\d{1,2}/\d{2,4}(?!\d)", w)
        or re.match(r"\d{1,2}-\d{1,2}-\d{2,4}(?!\d)", w)
    )
    if s:
        # Looks like a date with day, month and year parts
        g = s.group()
        if "/" in g:
            p = g.split("/")
        elif "-" in g:
            p = g.split("-")
        else:
            p = g.split(".")
        y = int(p[2])
        if y <= 99:
            # 50 means 2050, but 51 means 1951
            y += 1900 if y > 50 else 2000
        m = int(p[1])
        d = int(p[0])
        if m > 12 >= d:
            # Probably wrong way (i.e. U.S. American way) around
            m, d = d, m
        if is_valid_date(y, m, d):
            t, rest = tok.split(s.end())
            return TOK.Date(t, y, m, d), rest

    s = re.match(r"(\d{2})\.(\d{2})(?!\d)", w)
    if s:
        # A date in the form dd.mm
        # (Allowing hyphens here would interfere with for instance
        # sports scores and phrases such as 'Það voru 10-12 manns þarna.')
        g = s.group()
        d = int(s.group(1))
        m = int(s.group(2))
        if (1 <= m <= 12) and (1 <= d <= DAYS_IN_MONTH[m]):
            t, rest = tok.split(s.end())
            return TOK.Daterel(t, y=0, m=m, d=d), rest

    s = re.match(r"(\d{2})[-.](\d{4})(?!\d)", w)
    if s:
        # A date in the form of mm.yyyy or mm-yyyy
        g = s.group()
        m = int(s.group(1))
        y = int(s.group(2))
        if (1776 <= y <= 2100) and (1 <= m <= 12):
            t, rest = tok.split(s.end())
            return TOK.Daterel(t, y=y, m=m, d=0), rest

    # Note: the following must use re.UNICODE to make sure that
    # \w matches all Icelandic characters under Python 2
    s = re.match(r"\d+([a-zA-Z])(?!\w)", w, re.UNICODE)
    if s:
        # Looks like a number with a single trailing character, e.g. 14b, 33C, 1122f
        g = s.group()
        c = g[-1:]
        # Only match if the single character is not a
        # unit of measurement (e.g. 'A', 'l', 'V')
        if c not in SI_UNITS_SET:
            nw = int(g[:-1])
            t, rest = tok.split(s.end())
            return TOK.NumberWithLetter(t, nw, c), rest

    s = NUM_WITH_UNIT_REGEX1.match(w)
    if s:
        # Icelandic-style number followed by an SI unit, or degree/percentage,
        # or currency symbol
        g = s.group()
        val = float(s.group(1).replace(".", "").replace(",", "."))
        unit = s.group(4)
        if unit in CURRENCY_SYMBOLS:
            # This is an amount with a currency symbol at the end
            iso = CURRENCY_SYMBOLS[unit]
            t, rest = tok.split(s.end())
            return TOK.Amount(t, iso, val), rest
        unit, factor = SI_UNITS[unit]
        if callable(factor):
            val = factor(val)
        else:
            # Simple scaling factor
            val *= factor
        if unit in ("%", "‰"):
            t, rest = tok.split(s.end())
            return TOK.Percent(t, val), rest
        t, rest = tok.split(s.end())
        return TOK.Measurement(t, unit, val), rest

    s = NUM_WITH_UNIT_REGEX2.match(w)
    if s:
        # English-style number followed by an SI unit, or degree/percentage,
        # or currency symbol
        g = s.group()
        val = float(s.group(1).replace(",", ""))
        unit = s.group(4)
        if unit in CURRENCY_SYMBOLS:
            # This is an amount with a currency symbol at the end
            iso = CURRENCY_SYMBOLS[unit]
            t, rest = tok.split(s.end())
            return TOK.Amount(t, iso, val), rest
        unit, factor = SI_UNITS[unit]
        if callable(factor):
            val = factor(val)
        else:
            # Simple scaling factor
            val *= factor
        t, rest = tok.split(s.end())
        if convert_numbers:
            t.substitute_all(",", "x")  # Change thousands separator to 'x'
            t.substitute_all(".", ",")  # Change decimal separator to ','
            t.substitute_all("x", ".")  # Change 'x' to '.'
        if unit in ("%", "‰"):
            return TOK.Percent(t, val), rest
        return TOK.Measurement(t, unit, val), rest

    s = NUM_WITH_UNIT_REGEX3.match(w)
    if s:
        # One or more digits, followed by a unicode
        # vulgar fraction char (e.g. '2½') and an SI unit,
        # percent/promille, or currency code
        g = s.group()
        ln = s.group(1)
        vf = s.group(2)
        orig_unit = s.group(3)
        value = float(ln) + unicodedata.numeric(vf)
        if orig_unit in CURRENCY_SYMBOLS:
            # This is an amount with a currency symbol at the end
            iso = CURRENCY_SYMBOLS[orig_unit]
            t, rest = tok.split(s.end())
            return TOK.Amount(t, iso, value), rest
        unit, factor = SI_UNITS[orig_unit]
        if callable(factor):
            value = factor(value)
        else:
            # Simple scaling factor
            value *= factor
        if unit in ("%", "‰"):
            t, rest = tok.split(s.end())
            return TOK.Percent(t, value), rest
        t, rest = tok.split(s.end())
        return TOK.Measurement(t, unit, value), rest

    s = re.match(r"(\d+)([\u00BC-\u00BE\u2150-\u215E])", w, re.UNICODE)
    if s:
        # One or more digits, followed by a unicode vulgar fraction char (e.g. '2½')
        g = s.group()
        ln = s.group(1)
        vf = s.group(2)
        val = float(ln) + unicodedata.numeric(vf)
        t, rest = tok.split(s.end())
        return TOK.Number(t, val), rest

    # Can't end with digits.digits
    s = re.match(r"[\+\-]?\d+(\.\d\d\d)*,\d+(?!\d*\.\d)", w)
    if s:
        # Icelandic-style real number formatted with decimal comma (,)
        # and possibly thousands separators (.)
        # (we need to check this before checking integers)
        g = s.group()
        if re.match(r",\d+", w[len(g) :]):
            # English-style thousand separator multiple times
            s = None
        else:
            n = re.sub(r"\.", "", g)  # Eliminate thousands separators
            n = re.sub(",", ".", n)  # Convert decimal comma to point
            t, rest = tok.split(s.end())
            return TOK.Number(t, float(n)), rest

    s = re.match(r"[\+\-]?\d+(\.\d\d\d)+(?!\d)", w)
    if s:
        # Integer with a '.' thousands separator
        # (we need to check this before checking dd.mm dates)
        g = s.group()
        n = re.sub(r"\.", "", g)  # Eliminate thousands separators
        t, rest = tok.split(s.end())
        return TOK.Number(t, int(n)), rest

    s = re.match(r"\d{1,2}/\d{1,2}(?!\d)", w)
    if s:
        # Looks like a date (and not something like 10/2007)
        g = s.group()
        p = g.split("/")
        m = int(p[1])
        d = int(p[0])
        if (
            p[0][0] != "0"
            and p[1][0] != "0"
            and ((d <= 5 and m <= 6) or (d == 1 and m <= 10))
        ):
            # This is probably a fraction, not a date
            # (1/2, 1/3, 1/4, 1/5, 1/6, 2/3, 2/5, 5/6 etc.)
            # Return a number
            t, rest = tok.split(s.end())
            return TOK.Number(t, float(d) / m), rest
        if m > 12 >= d:
            # Date is probably wrong way around
            m, d = d, m
        if (1 <= m <= 12) and (1 <= d <= DAYS_IN_MONTH[m]):
            # Looks like a (roughly) valid date
            t, rest = tok.split(s.end())
            return TOK.Daterel(t, y=0, m=m, d=d), rest

    s = re.match(r"\d\d\d\d(?!\d)", w)
    if s:
        nn = int(s.group())
        if 1776 <= nn <= 2100:
            # Looks like a year
            t, rest = tok.split(4)
            return TOK.Year(t, nn), rest

    s = re.match(r"\d{6}\-\d{4}(?!\d)", w)
    if s:
        # Looks like a social security number
        g = s.group()
        if valid_ssn(g):
            t, rest = tok.split(11)
            return TOK.Ssn(t), rest

    s = re.match(r"\d\d\d\-\d\d\d\d(?!\d)", w)
    if s and w[0] in TELNO_PREFIXES:
        # Looks like a telephone number
        telno = s.group()
        t, rest = tok.split(8)
        return TOK.Telno(t, telno), rest
    if s:
        # Most likely some sort of serial number
        # Unknown token for now, don't want it separated
        t, rest = tok.split(s.end())
        return TOK.SerialNumber(t), rest

    s = re.match(r"\d+\-\d+(\-\d+)+", w)
    if s:
        # Multi-component serial number
        t, rest = tok.split(s.end())
        return TOK.SerialNumber(t), rest

    s = re.match(r"\d\d\d\d\d\d\d(?!\d)", w)
    if s and w[0] in TELNO_PREFIXES:
        # Looks like a telephone number
        telno = w[0:3] + "-" + w[3:7]
        t, rest = tok.split(7)
        return TOK.Telno(t, telno), rest

    s = re.match(r"\d+\.\d+(\.\d+)+", w)
    if s:
        # Some kind of ordinal chapter number: 2.5.1 etc.
        # (we need to check this before numbers with decimal points)
        g = s.group()
        # !!! TODO: A better solution would be to convert 2.5.1 to (2,5,1)
        n = re.sub(r"\.", "", g)  # Eliminate dots, 2.5.1 -> 251
        t, rest = tok.split(s.end())
        return TOK.Ordinal(t, int(n)), rest

    s = re.match(r"[\+\-]?\d+(,\d\d\d)*\.\d+", w)
    if s:
        # English-style real number with a decimal point (.),
        # and possibly commas as thousands separators (,)
        g = s.group()
        n = re.sub(",", "", g)  # Eliminate thousands separators
        # !!! TODO: May want to mark this as an error
        t, rest = tok.split(s.end())
        if convert_numbers:
            t.substitute_all(",", "x")  # Change thousands separator to 'x'
            t.substitute_all(".", ",")  # Change decimal separator to ','
            t.substitute_all("x", ".")  # Change 'x' to '.'
        return TOK.Number(t, float(n)), rest

    s = re.match(r"[\+\-]?\d+(,\d\d\d)*(?!\d)", w)
    if s:
        # Integer, possibly with a ',' thousands separator
        g = s.group()
        n = re.sub(",", "", g)  # Eliminate thousands separators
        # !!! TODO: May want to mark this as an error
        t, rest = tok.split(s.end())
        if convert_numbers:
            # Change thousands separator to a dot
            t.substitute_all(",", ".")
        return TOK.Number(t, int(n)), rest

    # Strange thing
    # !!! TODO: May want to mark this as an error
    # !!! TODO: is this the correct thing for the rest token?
    return (
        TOK.Unknown(tok),
        Tok(TOK.RAW, "", None, "", []),
    )


def html_escape(match: Match[str]) -> Tuple[Tuple[int, int], str]:
    """Regex substitution function for HTML escape codes"""
    g = match.group(4)
    if g is not None:
        # HTML escape string: 'acute'
        return match.span(), HTML_ESCAPES[g]
    g = match.group(2)
    if g is not None:
        # Hex code: '#xABCD'
        return match.span(), chr(int(g[2:], base=16))
    g = match.group(3)
    assert g is not None
    # Decimal code: '#8930'
    return match.span(), chr(int(g[1:]))


def composite_replacement(token: Tok) -> Tok:
    """Replace composite glyphs with single code points"""
    total_reduction = 0
    for m in COMPOSITE_REGEX.finditer(token.txt):
        span, new_letter = m.span(), COMPOSITE_REPLACEMENTS[m.group(0)]
        token.substitute(
            (span[0] - total_reduction, span[1] - total_reduction), new_letter
        )
        total_reduction += span[1] - span[0] - len(new_letter)
    return token


def zerowidth_replacement(token: Tok) -> Tok:
    """Remove zero-width characters (always applied)"""
    total_reduction = 0
    for m in ZEROWIDTH_REGEX.finditer(token.txt):
        span, new_letter = m.span(), ZEROWIDTH_CHARACTERS[m.group(0)]
        token.substitute(
            (span[0] - total_reduction, span[1] - total_reduction), new_letter
        )
        total_reduction += span[1] - span[0] - len(new_letter)
    return token


def unicode_replacement(token: Tok) -> Tok:
    """Replace some composite glyphs with single code points (backward compatibility)"""
    # This function maintains backward compatibility by doing both replacements
    token = composite_replacement(token)
    token = zerowidth_replacement(token)
    return token


def html_replacement(token: Tok) -> Tok:
    """Replace html escape sequences with their proper characters"""
    total_reduction = 0
    for m in HTML_ESCAPE_REGEX.finditer(token.txt):
        span, new_letter = html_escape(m)
        token.substitute(
            (span[0] - total_reduction, span[1] - total_reduction), new_letter
        )
        total_reduction += span[1] - span[0] - len(new_letter)
    return token


def generate_rough_tokens_from_txt(text: str) -> Iterator[Tok]:
    """Generate rough tokens from a string."""
    # Rough tokens are tokens that are separated by whitespace, i.e. the regex (\\s*).
    # pos tracks the index in the text we have covered so far.
    # We want to track pos, instead of treating text as a buffer,
    # since that would lead to a lot of unnecessary copying.
    pos = 0
    while pos < len(text):
        match = ROUGH_TOKEN_REGEX.match(text, pos)
        assert match is not None
        match_span = match.span(ROUGH_TOKEN_REGEX_ENTIRE_MATCH)
        tok = Tok.from_txt(text[match_span[SPAN_START] : match_span[SPAN_END]])
        pos = match_span[SPAN_END]
        yield tok


def generate_rough_tokens_from_tok(tok: Tok) -> Iterator[Tok]:
    """Generate rough tokens from a token."""
    # Some tokens might have whitespace characters after we replace
    # composite unicode glyphs and replace HTML escapes.
    # This function further splits those tokens into multiple tokens.
    # Rough tokens are tokens that are separated by white space, i.e. the regex (\\s*).

    def shift_span(span: Tuple[int, int], pos: int) -> Tuple[int, int]:
        """Shift a span by a given amount"""
        return (span[SPAN_START] + pos, span[SPAN_END] + pos)

    text = tok.txt
    # pos tracks the index in the text we have covered so far.
    # We want to track pos, instead of treating text as a buffer,
    # since that would lead to a lot of unnecessary copying.
    pos = 0
    while pos < len(text):
        match = ROUGH_TOKEN_REGEX.match(text, pos)
        assert match is not None
        # Since the match indexes the text of the original token,
        # we need to shift the indices so that they match the current token.
        shifted_all_group_span = shift_span(
            match.span(ROUGH_TOKEN_REGEX_ENTIRE_MATCH), -pos
        )
        shifted_white_space_span = shift_span(
            match.span(ROUGH_TOKEN_REGEX_WHITE_SPACE_GROUP), -pos
        )
        # Then we split the current token using the shifted spans
        small_tok, tok = tok.split(shifted_all_group_span[SPAN_END])
        # Remove whitespace characters from the start of the token
        small_tok.substitute(shifted_white_space_span, "")
        # The pos is not shifted
        pos = match.span(ROUGH_TOKEN_REGEX_ENTIRE_MATCH)[SPAN_END]
        yield small_tok


def generate_raw_tokens(
    text_or_gen: Union[str, Iterable[str]],
    replace_composite_glyphs: bool = True,
    replace_html_escapes: bool = False,
    one_sent_per_line: bool = False,
) -> Iterator[Tok]:
    """Generate raw tokens from a string or an iterable
    that contains strings"""

    if isinstance(text_or_gen, str):
        if not text_or_gen:
            # Empty string: yield nothing
            return
        # The parameter is a single string: wrap it in an iterable
        text_or_gen = [text_or_gen]

    # Iterate through text_or_gen, which is assumed to yield strings
    saved: Optional[Tok] = None

    # The following declaration seems to be required for Pylance
    big_text: str

    for big_text in text_or_gen:
        if not one_sent_per_line and not big_text:
            # An explicit empty string in the input always
            # causes a sentence split
            yield TOK.Split_Sentence(saved)
            saved = None
            continue

        if saved is not None:
            # The following strange code satisfies Pylance
            so: Optional[str] = saved.original
            big_text = (so or "") + big_text
            saved = None

        # Force sentence splits
        # Case 1: Two newlines with only whitespace between appear anywhere
        #         in 'big_text'. I.e. force sentence split when we see an empty line.
        # Case 2: 'big_txt' contains only whitespace.
        #         This only means "empty line" if each element in text_or_gen is assumed
        #         to be a line (even if they don't contain any newline characters).
        #         That does not strictly have to be true and is not a declared
        #         assumption, except in tests, but the tokenizer has had this behavior
        #         for a long time.

        if one_sent_per_line:
            # We know there's a single sentence per line
            # Only split on newline
            sentence_split_pattern = r"(\n)"
        else:
            # Split on empty lines, eventually containing whitespace,
            # but also on paragraph splits within a line
            sentence_split_pattern = r"(\n\s*\n|^\s+$|\]\]\[\[)"

        splits = re.split(sentence_split_pattern, big_text)
        # We know that splits will contain alternatively useful text and the splitting
        # pattern, starting and ending with useful text. See the documentation on
        # re.split.
        is_text = True
        for text in splits:
            if is_text:
                # 'text' is text to be tokenized
                paragraph_end = 0
                if not one_sent_per_line:
                    # Convert paragraph separators to TOK.P_BEGIN and TOK.P_END tokens
                    while text.startswith("[["):
                        # Begin paragraph
                        text = text[2:]
                        yield TOK.Begin_Paragraph()
                    while text.endswith("]]"):
                        # End paragraph
                        text = text[:-2]
                        # Postpone the yield until after the raw token loop
                        paragraph_end += 1
                for tok in generate_rough_tokens_from_txt(text):
                    # Always remove zero-width characters
                    tok = zerowidth_replacement(tok)
                    if replace_composite_glyphs:
                        # Replace composite glyphs with single code points
                        tok = composite_replacement(tok)
                    if replace_html_escapes:
                        # Replace HTML escapes: '&aacute;' -> 'á'
                        tok = html_replacement(tok)
                    # HTML escapes and unicode may contain whitespace characters
                    # e.g. Em space '&#8195;' and non-breaking space '&nbsp;'
                    # Here we split those tokens into multiple tokens.
                    for small_tok in generate_rough_tokens_from_tok(tok):
                        if small_tok.txt == "":
                            # There was whitespace at the end of the last token.
                            # We do not want to yield a token with empty text if possible.
                            # We want to attach it in front of the next token, if there is one.
                            # If there is no next token, we attach it in front of the next 'big_text'.
                            # This will happen:
                            # 1. When 'text' has whitespace at the end
                            # 2. When we have replaced a composite glyph or an HTML
                            #    escape with whitespace.
                            # See ROUGH_TOKEN_REGEX to convince yourself this is true.
                            saved = small_tok
                        else:
                            if saved is not None:
                                # Attach the saved token in front of the current token
                                small_tok = saved.concatenate(small_tok)
                                saved = None
                            yield small_tok

                while paragraph_end:
                    # Yield the postponed TOK.P_END token
                    yield TOK.End_Paragraph()
                    paragraph_end -= 1
            elif text == "]][[":
                # Paragraph split: Yield TOK.P_BEGIN and TOK.P_END tokens
                yield TOK.End_Paragraph()
                yield TOK.Begin_Paragraph()
            else:
                # Sentence split: 'text' is the split pattern
                tok_split = Tok.from_txt(text)
                # This token should have no output text, but we still want to preserve
                # the original text.
                tok_split.substitute((0, len(text)), "")
                yield TOK.Split_Sentence(tok_split)

            is_text = not is_text

    if saved is not None:
        # There is trailing whitespace at the end of everything.
        # The only option to conserve this is to emit a token with empty text.
        # Set the type to S_SPLIT to get proper sentence detection in later phases.
        yield TOK.Split_Sentence(saved)


def could_be_end_of_sentence(
    next_token: Tok,
    test_set: frozenset[int] = TOK.TEXT,
    multiplier: bool = False,
) -> bool:
    """Return True if next_token could be ending the current sentence or
    starting the next one"""
    return next_token.kind in TOK.END or (
        # Check whether the next token is an uppercase word, except if
        # it is a month name (frequently misspelled in uppercase) or
        # roman numeral, or a currency abbreviation if preceded by a
        # multiplier (for example þ. USD for thousands of USD)
        next_token.kind in test_set
        and next_token.txt[0].isupper()
        and next_token.txt.lower() not in MONTHS
        and not RE_ROMAN_NUMERAL.match(next_token.txt)
        and not (next_token.txt in CURRENCY_ABBREV and multiplier)
    )


class LetterParser:
    """Parses a sequence of alphabetic characters off the front of a raw token.
    Fast path for standard characters using isalpha()."""

    def __init__(self, rt: Tok) -> None:
        self.rt = rt
        
    def _is_letter(self, char: str) -> bool:
        """Test if character is alphabetic - fast path."""
        return char.isalpha()

    def parse(self) -> Iterable[Tok]:
        """Parse the raw token, yielding result tokens"""
        rt = self.rt
        lw = len(rt.txt)
        i = 1
        while i < lw and (
            self._is_letter(rt.txt[i])
            or (
                rt.txt[i] in PUNCT_INSIDE_WORD
                and i + 1 < lw
                and self._is_letter(rt.txt[i + 1])
            )
        ):
            # We allow dots to occur inside words in the case of
            # abbreviations; also apostrophes are allowed within
            # words and at the end (albeit not consecutively)
            # (O'Malley, Mary's, it's, childrens', O‘Donnell).
            # The same goes for ² and ³
            i += 1
        if i < lw and rt.txt[i] in PUNCT_ENDING_WORD:
            i += 1
        # Make a special check for the occasional erroneous source text
        # case where sentences run together over a period without a space:
        # 'sjávarútvegi.Það'
        # TODO STILLING Viljum merkja sem villu fyrir málrýni, og hafa
        # sem mögulega stillingu.
        ww: str = rt.txt[0:i]
        a = ww.split(".")

        if (
            len(a) == 2
            # First part must be more than one letter for us to split
            and len(a[0]) > 1
            # The first part may start with an uppercase or lowercase letter
            # but the rest of it must be lowercase
            and a[0][1:].islower()
            and a[1]
            # The second part must start with an uppercase letter
            and a[1][0].isupper()
            # Corner case: an abbrev such as 'f.Kr' should not be split
            and rt.txt[0 : i + 1] not in Abbreviations.DICT
        ):
            # We have a lowercase word immediately followed by a period
            # and an uppercase word
            word1, rt = rt.split(len(a[0]))
            punct, rt = rt.split(1)
            word2, rt = rt.split(len(a[1]))
            yield TOK.Word(word1)
            yield TOK.Punctuation(punct)
            yield TOK.Word(word2)

        elif ww.endswith("-og") or ww.endswith("-eða"):
            # Handle missing space before 'og'/'eða',
            # such as 'fjármála-og efnahagsráðuneyti'
            a = ww.split("-")

            word1, rt = rt.split(len(a[0]))
            punct, rt = rt.split(1)
            word2, rt = rt.split(len(a[1]))
            yield TOK.Word(word1)
            yield TOK.Punctuation(punct, normalized=COMPOSITE_HYPHEN)
            yield TOK.Word(word2)

        else:
            word, rt = rt.split(i)
            yield TOK.Word(word)

        if rt.txt and rt.txt[0] in COMPOSITE_HYPHENS:
            # This is a hyphen or en dash directly appended to a word:
            # might be a continuation ('fjármála- og efnahagsráðuneyti')
            # Yield a special hyphen as a marker
            punct, rt = rt.split(1)
            yield TOK.Punctuation(punct, normalized=COMPOSITE_HYPHEN)

        self.rt = rt


class LetterParserComposite(LetterParser):
    """Parses a sequence of alphabetic characters off the front of a raw token.
    Handles combining characters when --keep_composite_glyphs is specified."""
    
    def _is_letter(self, char: str) -> bool:
        """Test if character is alphabetic or a combining mark."""
        cat = unicodedata.category(char)
        return cat.startswith(('L', 'M'))


class NumberParser:
    """Parses a sequence of digits off the front of a raw token"""

    def __init__(
        self, rt: Tok, handle_kludgy_ordinals: int, convert_numbers: bool
    ) -> None:
        self.rt = rt
        self.handle_kludgy_ordinals = handle_kludgy_ordinals
        self.convert_numbers = convert_numbers

    def parse(self) -> Iterable[Tok]:
        """Parse the raw token, yielding result tokens"""
        # Handle kludgy ordinals: '3ji', '5ti', etc.
        rt = self.rt
        handle_kludgy_ordinals = self.handle_kludgy_ordinals
        convert_numbers = self.convert_numbers
        for key, val in ORDINAL_ERRORS.items():
            rtxt = rt.txt
            if rtxt.startswith(key):
                # This is a kludgy ordinal
                key_tok, rt = rt.split(len(key))
                if handle_kludgy_ordinals == KLUDGY_ORDINALS_MODIFY:
                    # Convert ordinals to corresponding word tokens:
                    # '1sti' -> 'fyrsti', '3ji' -> 'þriðji', etc.
                    key_tok.substitute_longer((0, len(key)), val)
                    yield TOK.Word(key_tok)
                elif (
                    handle_kludgy_ordinals == KLUDGY_ORDINALS_TRANSLATE
                    and key in ORDINAL_NUMBERS
                ):
                    # Convert word-form ordinals into ordinal tokens,
                    # i.e. '1sti' -> TOK.Ordinal('1sti', 1),
                    # but leave other kludgy constructs ('2ja')
                    # as word tokens
                    yield TOK.Ordinal(key_tok, ORDINAL_NUMBERS[key])
                else:
                    # No special handling of kludgy ordinals:
                    # yield them unchanged as word tokens
                    yield TOK.Word(key_tok)
                break  # This skips the for loop 'else'
        else:
            # Not a kludgy ordinal: eat tokens starting with a digit
            t, rt = parse_digits(rt, convert_numbers)
            yield t

        # Continue where the digits parser left off
        if rt.txt:
            # Check for an SI unit immediately following a number
            r = SI_UNITS_REGEX.match(rt.txt)
            if r:
                # Handle the case where a measurement unit is
                # immediately following a number, without an intervening space
                # (note that some of them contain nonalphabetic characters,
                # so they won't be caught by the isalpha() check below)
                unit, rt = rt.split(r.end())
                yield TOK.Word(unit)

        self.rt = rt


class PunctuationParser:
    """Parses a sequence of punctuation off the front of a raw token"""

    def __init__(self) -> None:
        self.rt = cast(Tok, None)
        self.ate = False

    def parse(self, rt: Tok) -> Iterable[Tok]:
        """Parse the raw token, yielding result tokens"""
        ate = False
        while rt.txt and rt.txt[0] in PUNCTUATION:
            ate = True
            rtxt = rt.txt
            lw = len(rtxt)
            if rtxt.startswith("[...]"):
                punct, rt = rt.split(5)
                yield TOK.Punctuation(punct, normalized="[…]")
            elif rtxt.startswith("[…]"):
                punct, rt = rt.split(3)
                yield TOK.Punctuation(punct)
            elif rtxt.startswith("...") or rtxt.startswith("…"):
                # Treat >= 3 periods as ellipsis, one piece of punctuation
                numdots = 0
                for c in rtxt:
                    if c == "." or c == "…":
                        numdots += 1
                    else:
                        break
                dots, rt = rt.split(numdots)
                yield TOK.Punctuation(dots, normalized="…")
            elif rtxt.startswith(".."):
                # Normalize two periods to one
                dots, rt = rt.split(2)
                yield TOK.Punctuation(dots, normalized=".")
            elif rtxt.startswith(",,"):
                if rtxt[2:3].isalnum():
                    # Probably someone trying to type opening double quotes with commas
                    punct, rt = rt.split(2)
                    yield TOK.Punctuation(punct, normalized="„")
                else:
                    # Coalesce multiple commas into one normalized comma
                    numcommas = 2
                    for c in rtxt[2:]:
                        if c == ",":
                            numcommas += 1
                        else:
                            break
                    punct, rt = rt.split(numcommas)
                    yield TOK.Punctuation(punct, normalized=",")
            elif rtxt[0] in HYPHENS:
                # Normalize all hyphens the same way
                punct, rt = rt.split(1)
                yield TOK.Punctuation(punct, normalized=HYPHEN)
            elif rtxt[0] in DQUOTES:
                # Convert to a proper closing double quote
                punct, rt = rt.split(1)
                yield TOK.Punctuation(punct, normalized="“")
            elif rtxt[0] in SQUOTES:
                # Left with a single quote, convert to proper closing quote
                punct, rt = rt.split(1)
                yield TOK.Punctuation(punct, normalized="‘")
            elif lw > 1 and rtxt.startswith("#"):
                # Might be a hashtag, processed later
                ate = False
                break
            elif lw > 1 and rtxt.startswith("@"):
                # Username on Twitter or other social media platforms
                # User names may contain alphabetic characters, digits
                # and embedded periods (but not consecutive ones)
                s = re.match(r"\@[0-9a-zA-Z_]+(\.[0-9a-zA-Z_]+)*", rtxt)
                if s:
                    g = s.group()
                    username, rt = rt.split(s.end())
                    yield TOK.Username(username, g[1:])
                else:
                    # Return the @-sign and leave the rest
                    punct, rt = rt.split(1)
                    yield TOK.Punctuation(punct)
            elif len(rtxt) >= 2 and frozenset(rtxt) <= EXCLAMATIONS:
                # Possibly '???!!!' or something of the sort
                numpunct = 2
                for p in rtxt[2:]:
                    if p in EXCLAMATIONS:
                        numpunct += 1
                    else:
                        break
                punct, rt = rt.split(numpunct)
                yield TOK.Punctuation(punct, normalized=rtxt[0])
            else:
                punct, rt = rt.split(1)
                yield TOK.Punctuation(punct)

        # End of punctuation loop
        self.rt = rt
        self.ate = ate


def parse_mixed(
    rt: Tok, handle_kludgy_ordinals: int, convert_numbers: bool, replace_composite_glyphs: bool = True
) -> Iterable[Tok]:
    """Parse a mixed raw token string, from the token rt"""

    # Select the appropriate letter parser class based on composite glyph handling
    LetterParserClass = LetterParser if replace_composite_glyphs else LetterParserComposite

    # Initialize a singleton parser for punctuation
    pp = PunctuationParser()

    while rt.txt:
        # Handle punctuation
        yield from pp.parse(rt)
        rt, ate = pp.rt, pp.ate

        # Check for specific token types other than punctuation

        rtxt = rt.txt
        if rtxt and "@" in rtxt:
            # Check for valid e-mail
            # Note: we don't allow double quotes (simple or closing ones) in e-mails
            # here even though they're technically allowed according to the RFCs
            s = re.match(r"[^@\s]+@[^@\s]+(\.[^@\s\.,/:;\"\(\)%#!\?”]+)+", rtxt)
            if s:
                email, rt = rt.split(s.end())
                yield TOK.Email(email)
                ate = True

        # Unicode single-char vulgar fractions
        # TODO: Support multiple-char unicode fractions that
        # use super/subscript w. DIVISION SLASH (U+2215)
        if rt.txt and rt.txt[0] in SINGLECHAR_FRACTIONS:
            num, rt = rt.split(1)
            yield TOK.Number(num, unicodedata.numeric(num.txt[0]))
            ate = True

        rtxt = rt.txt
        if rtxt and rtxt.startswith(URI_PREFIXES):
            # Handle URL: cut RIGHT_PUNCTUATION characters off its end,
            # even though many of them are actually allowed according to
            # the IETF RFC
            endp = ""
            w = rtxt
            while w and w[-1] in RIGHT_PUNCTUATION:
                endp = w[-1] + endp
                w = w[:-1]
            url, rt = rt.split(len(w))
            yield TOK.Url(url)
            ate = True

        if rtxt and len(rtxt) >= 2 and re.match(r"#\w", rtxt, re.UNICODE):
            # Handle hashtags. Eat all text up to next punctuation character
            # so we can handle strings like "#MeToo-hreyfingin" as two words
            w = rtxt
            tag = w[:1]
            w = w[1:]
            while w and w[0] not in PUNCTUATION:
                tag += w[0]
                w = w[1:]
            tag_tok, rt = rt.split(len(tag))
            if re.match(r"#\d+$", tag):
                # Hash is being used as a number sign, e.g. "#12"
                yield TOK.Ordinal(tag_tok, int(tag[1:]))
            else:
                yield TOK.Hashtag(tag_tok)
            ate = True

        rtxt = rt.txt
        # Domain name (e.g. greynir.is)
        if (
            rtxt
            and len(rtxt) >= MIN_DOMAIN_LENGTH
            and rtxt[0].isalnum()  # All domains start with an alphanumeric char
            and "." in rtxt[1:-2]  # Optimization, TLD is at least 2 chars
            and DOMAIN_REGEX.search(rtxt)
        ):
            w = rtxt
            endp = ""
            while w and w[-1] in PUNCTUATION:
                endp = w[-1] + endp
                w = w[:-1]
            domain, rt = rt.split(len(w))
            yield TOK.Domain(domain)
            ate = True

        rtxt = rt.txt
        # Numbers or other stuff starting with a digit
        # (eventually prefixed by a '+' or '-')
        if rtxt and (
            rtxt[0] in DIGITS_PREFIX
            or (rtxt[0] in SIGN_PREFIX and len(rtxt) >= 2 and rtxt[1] in DIGITS_PREFIX)
        ):
            np = NumberParser(rt, handle_kludgy_ordinals, convert_numbers)
            yield from np.parse()
            rt = np.rt
            ate = True

        # Check for molecular formula ('H2SO4')
        if rt.txt:
            r = MOLECULE_REGEX.match(rt.txt)
            if r is not None:
                g = r.group()
                if g not in Abbreviations.DICT and MOLECULE_FILTER.search(g):
                    # Correct format, containing at least one digit
                    # and not separately defined as an abbreviation:
                    # We assume that this is a molecular formula
                    molecule, rt = rt.split(r.end())
                    yield TOK.Molecule(molecule)
                    ate = True

        # Check for currency abbreviations immediately followed by a number
        if len(rt.txt) > 3 and rt.txt[0:3] in CURRENCY_ABBREV and rt.txt[3].isdigit():
            # TODO: This feels a little hacky
            temp_tok = Tok(TOK.RAW, rt.txt[3:], None)
            digit_tok, _ = parse_digits(temp_tok, convert_numbers)
            if digit_tok.kind == TOK.NUMBER:
                amount, rt = rt.split(3 + len(digit_tok.txt))
                yield TOK.Amount(amount, amount.txt[:3], digit_tok.number)
                ate = True

        # Alphabetic characters
        # Note: the initial character must be a proper letter,
        # not a combining accent, for the letter parser to be applied.
        # However, the letter parser allows subsequent characters to
        # be combining accents.
        if rt.txt and rt.txt[0].isalpha():
            lp = LetterParserClass(rt)
            yield from lp.parse()
            rt = lp.rt
            ate = True

        # Special case for quotes attached on the right hand side to other stuff,
        # assumed to be closing quotes rather than opening ones
        if rt.txt:
            if rt.txt[0] in SQUOTES:
                punct, rt = rt.split(1)
                yield TOK.Punctuation(punct, normalized="‘")
                ate = True
            elif rt.txt[0] in DQUOTES:
                punct, rt = rt.split(1)
                yield TOK.Punctuation(punct, normalized="“")
                ate = True

        if not ate:
            # Ensure that we eat everything, even unknown stuff
            unk, rt = rt.split(1)
            yield TOK.Unknown(unk)


def is_word_with_composites(txt: str) -> bool:
    """Return true if txt is an alphabetic word in the wider sense that
    it can contain composite characters (combining accents, etc.). However,
    the word must start with a proper alphabetic character, since combining
    accents musth *follow* a letter - they can't *precede* it."""
    return len(txt) > 1 and txt[0].isalpha() and all(
        unicodedata.category(char).startswith(('L', 'M')) for char in txt[1:]
    )


def parse_tokens(txt: Union[str, Iterable[str]], **options: Any) -> Iterator[Tok]:
    """Generator that parses contiguous text into a stream of tokens"""

    # Obtain individual flags from the options dict
    convert_numbers: bool = options.get("convert_numbers", False)
    replace_composite_glyphs: bool = options.get("replace_composite_glyphs", True)
    replace_html_escapes: bool = options.get("replace_html_escapes", False)
    one_sent_per_line: bool = options.get("one_sent_per_line", False)

    # The default behavior for kludgy ordinals is to pass them
    # through as word tokens
    handle_kludgy_ordinals: int = options.get(
        "handle_kludgy_ordinals", KLUDGY_ORDINALS_PASS_THROUGH
    )

    # This code proceeds roughly as follows:
    # 1) The text is split into raw tokens on whitespace boundaries.
    # 2) (By far the most common case:) Raw tokens that are purely
    #    alphabetic are yielded as word tokens.
    # 3) Punctuation from the front of the remaining raw token is identified
    #    and yielded. A special case applies for quotes.
    # 4) A set of checks is applied to the rest of the raw token, identifying
    #    tokens such as e-mail addresses, domains and @usernames. These can
    #    start with digits, so the checks must occur before step 5.
    # 5) Tokens starting with a digit (eventually preceded
    #    by a + or - sign) are sent off to a separate function that identifies
    #    integers, real numbers, dates, telephone numbers, etc. via regexes.
    # 6) After such checks, alphabetic sequences (words) at the start of the
    #    raw token are identified. Such a sequence can, by the way, also
    #    contain embedded apostrophes and hyphens (Dunkin' Donuts, Mary's,
    #    marg-ítrekaðri).
    # 7) The process is repeated from step 4) until the current raw token is
    #    exhausted. At that point, we obtain the next token and start from 2).

    rtxt: str = ""

    for rt in generate_raw_tokens(
        txt, replace_composite_glyphs, replace_html_escapes, one_sent_per_line
    ):
        # rt: raw token

        if rt.kind in {TOK.S_SPLIT, TOK.P_BEGIN, TOK.P_END}:
            # Sentence split markers and paragraph separators require
            # no further processing. Yield them immediately.
            yield rt
            continue

        rtxt = rt.txt
        if rtxt.isalpha() or rtxt in SI_UNITS:
            # Shortcut for most common case: pure word
            yield TOK.Word(rt)
            continue
        elif not replace_composite_glyphs and is_word_with_composites(rtxt):
            # This is a word with combining characters when --keep_composite_glyphs is specified
            yield TOK.Word(rt)
            continue

        if len(rtxt) > 1:
            if rtxt[0] in SIGN_PREFIX and rtxt[1] in DIGITS_PREFIX:
                # Digit, preceded by sign (+/-): parse as a number
                # Note that we can't immediately parse a non-signed number
                # here since kludges such as '3ja' and domain names such as '4chan.com'
                # need to be handled separately below
                t, rt = parse_digits(rt, convert_numbers)
                yield t
                if not rt.txt:
                    continue
            elif rtxt[0] in COMPOSITE_HYPHENS and rtxt[1].isalpha():
                # This may be something like '-menn' in 'þingkonur og -menn'
                i = 2
                while i < len(rtxt) and rtxt[i].isalpha():
                    i += 1
                # We allow -menn and -MENN, but not -Menn or -mEnn
                # We don't allow -Á or -Í, i.e. single-letter uppercase combos
                if rtxt[:i].islower() or (i > 2 and rtxt[:i].isupper()):
                    head, rt = rt.split(i)
                    yield TOK.Word(head)
            rtxt = rt.txt

        # Shortcut for quotes around a single word
        if len(rtxt) >= 3:
            if rtxt[0] in DQUOTES and rtxt[-1] in DQUOTES:
                # Convert to matching Icelandic quotes
                # yield TOK.Punctuation("„")
                if rtxt[1:-1].isalpha():
                    first_punct, rt = rt.split(1)
                    word, last_punct = rt.split(-1)
                    yield TOK.Punctuation(first_punct, normalized="„")
                    yield TOK.Word(word)
                    yield TOK.Punctuation(last_punct, normalized="“")
                    continue
            elif rtxt[0] in SQUOTES and rtxt[-1] in SQUOTES:
                # Convert to matching Icelandic quotes
                # yield TOK.Punctuation("‚")
                if rtxt[1:-1].isalpha():
                    first_punct, rt = rt.split(1)
                    word, last_punct = rt.split(-1)
                    yield TOK.Punctuation(first_punct, normalized="‚")
                    yield TOK.Word(word)
                    yield TOK.Punctuation(last_punct, normalized="‘")
                    continue

        # Special case for leading quotes, which are interpreted
        # as opening quotes
        if len(rtxt) > 1:
            if rtxt[0] in DQUOTES:
                # Convert simple quotes to proper opening quotes
                punct, rt = rt.split(1)
                yield TOK.Punctuation(punct, normalized="„")
            elif rt.txt[0] in SQUOTES:
                # Convert simple quotes to proper opening quotes
                punct, rt = rt.split(1)
                yield TOK.Punctuation(punct, normalized="‚")

        # More complex case of mixed punctuation, letters and numbers
        yield from parse_mixed(rt, handle_kludgy_ordinals, convert_numbers, replace_composite_glyphs)

    # Yield a sentinel token at the end that will be cut off by the final generator
    yield TOK.End_Sentinel()


def parse_particles(token_stream: Iterator[Tok], **options: Any) -> Iterator[Tok]:
    """Parse a stream of tokens looking for 'particles'
    (simple token pairs and abbreviations) and making substitutions"""

    convert_measurements = options.pop("convert_measurements", False)

    def is_abbr_with_period(txt: str) -> bool:
        """Return True if the given token text is an abbreviation
        when followed by a period"""
        if "." in txt:
            # There is already a period in it: must be an abbreviation
            # (this applies for instance to "t.d" but not to "mbl.is")
            return True
        if txt in Abbreviations.SINGLES:
            # The token's literal text is defined as an abbreviation
            # followed by a single period
            return True
        if txt.lower() in Abbreviations.SINGLES:
            # The token is in upper or mixed case:
            # We allow it as an abbreviation unless the exact form
            # (most often uppercase) is an abbreviation that doesn't
            # require a period (i.e. isn't in SINGLES).
            # This applies for instance to DR which means
            # "Danmark's Radio" instead of "doktor" (dr.)
            return txt not in Abbreviations.DICT
        return False

    def lookup(abbrev: str) -> Optional[list[BIN_Tuple]]:
        """Look up an abbreviation, both in original case and in lower case,
        and return either None if not found or a meaning list having one entry"""
        m = Abbreviations.DICT.get(abbrev)
        if not m:
            m = Abbreviations.DICT.get(abbrev.lower())
        return list(m) if m else None

    token = cast(Tok, None)
    try:
        # Use TokenStream wrapper for this phase (for lookahead)
        token_stream = TokenStream(token_stream)
        # Maintain a one-token lookahead
        token = next(token_stream)
        while True:
            next_token = next(token_stream)
            # Make the lookahead checks we're interested in
            # Check for currency symbol followed by number, e.g. $10
            if (
                token.kind == TOK.PUNCTUATION
                and token.txt in CURRENCY_SYMBOLS
                and (next_token.kind == TOK.NUMBER or next_token.kind == TOK.YEAR)
            ):
                currabbr = CURRENCY_SYMBOLS[token.txt]
                token = TOK.Amount(
                    token.concatenate(next_token), currabbr, next_token.number
                )
                next_token = next(token_stream)

            # Special case for a DATEREL token of the form "25.10.",
            # i.e. with a trailing period: It can end a sentence
            if token.kind == TOK.DATEREL and "." in token.txt:
                if (
                    next_token.txt == "."
                    and not token_stream.could_be_end_of_sentence()
                ):
                    # This is something like 'Ég fæddist 25.9. í Svarfaðardal.'
                    y, m, d = cast(tuple[int, int, int], token.val)
                    token = TOK.Daterel(token.concatenate(next_token), y, m, d)
                    next_token = next(token_stream)

            # Coalesce abbreviations ending with a period into a single
            # abbreviation token
            if next_token.punctuation == ".":
                if (
                    token.kind == TOK.WORD
                    and token.txt[-1] != "."
                    and is_abbr_with_period(token.txt)
                ):
                    # Abbreviation ending with period: make a special token for it
                    # and advance the input stream
                    follow_token = next(token_stream)
                    abbrev = token.txt + "."

                    # Check whether we might be at the end of a sentence, i.e.
                    # the following token is an end-of-sentence or end-of-paragraph,
                    # or uppercase (and not a month name misspelled in upper case).

                    if abbrev in Abbreviations.NAME_FINISHERS:
                        # For name finishers (such as 'próf.') we don't consider a
                        # following person name as an indicator of an end-of-sentence
                        # TODO: This does not work as intended because person names
                        # have not been recognized at this phase in the token pipeline.
                        test_set = TOK.TEXT_EXCL_PERSON
                    else:
                        test_set = TOK.TEXT

                    # TODO STILLING í MONTHS eru einhverjar villur eins og "septembers",
                    # þær þarf að vera hægt að sameina í þessa flóknari tóka en viljum
                    # geta merkt það sem villu. Ætti líklega að setja í sérlista,
                    # WRONG_MONTHS, og sérif-lykkju og setja inn villu í tókann.
                    finish = could_be_end_of_sentence(
                        follow_token, test_set, abbrev in NUMBER_ABBREV
                    )
                    if finish:
                        # Potentially at the end of a sentence
                        if abbrev in Abbreviations.FINISHERS:
                            # We see this as an abbreviation even if the next sentence
                            # seems to be starting just after it.
                            # Yield the abbreviation without a trailing dot, and then
                            # an 'extra' period token to end the current sentence.
                            token = TOK.Word(token, lookup(abbrev))
                            yield token
                            # Set token to the period
                            token = next_token
                        elif (
                            abbrev in Abbreviations.NOT_FINISHERS
                            or abbrev.lower() in Abbreviations.NOT_FINISHERS
                        ):
                            # This is a potential abbreviation that we don't interpret
                            # as such if it's at the end of a sentence
                            # ('dags.', 'próf.', 'mín.'). Note that this also
                            # applies for uppercase versions: 'Örn.', 'Próf.'
                            yield token
                            token = next_token
                        else:
                            # Substitute the abbreviation and eat the period
                            token = TOK.Word(
                                token.concatenate(next_token), lookup(abbrev)
                            )
                    else:
                        # 'Regular' abbreviation in the middle of a sentence:
                        # Eat the period and yield the abbreviation as a single token
                        token = TOK.Word(token.concatenate(next_token), lookup(abbrev))

                    next_token = follow_token

            # Coalesce 'klukkan'/[kl.] + time or number into a time
            if next_token.kind == TOK.TIME or next_token.kind == TOK.NUMBER:
                if token.kind == TOK.WORD and token.txt.lower() in CLOCK_ABBREVS:
                    # Match: coalesce and step to next token
                    if next_token.kind == TOK.NUMBER:
                        # next_token.txt may be a real number, i.e. 13,40,
                        # which may have been converted from 13.40
                        # If we now have hh.mm, parse it as such
                        a = "{0:.2f}".format(next_token.number).split(".")
                        h, m = int(a[0]), int(a[1])
                        token = TOK.Time(
                            token.concatenate(next_token, separator=" "),
                            h,
                            m,
                            0,
                        )
                    else:
                        # next_token.kind is TOK.TIME
                        dt = cast(DateTimeTuple, next_token.val)
                        token = TOK.Time(
                            token.concatenate(next_token, separator=" "),
                            dt[0],
                            dt[1],
                            dt[2],
                        )
                    next_token = next(token_stream)

            # Coalesce 'klukkan/kl. átta/hálfátta' into a time
            elif (
                next_token.kind == TOK.WORD and next_token.txt.lower() in CLOCK_NUMBERS
            ):
                if token.kind == TOK.WORD and token.txt.lower() in CLOCK_ABBREVS:
                    # Match: coalesce and step to next token
                    next_txt = next_token.txt.lower()
                    token = TOK.Time(
                        token.concatenate(next_token, separator=" "),
                        *CLOCK_NUMBERS.get(next_txt, (0, 0, 0)),
                    )
                    next_token = next(token_stream)

            # Coalesce 'klukkan/kl. hálf átta' into a time
            elif next_token.kind == TOK.WORD and next_token.txt.lower() == "hálf":
                if token.kind == TOK.WORD and token.txt.lower() in CLOCK_ABBREVS:
                    time_token = next(token_stream)
                    time_txt = time_token.txt.lower() if time_token.txt else ""
                    if time_txt in CLOCK_NUMBERS and not time_txt.startswith("hálf"):
                        # Match
                        temp_tok = token.concatenate(next_token, separator=" ")
                        temp_tok = temp_tok.concatenate(time_token, separator=" ")
                        token = TOK.Time(temp_tok, *CLOCK_NUMBERS["hálf" + time_txt])
                        next_token = next(token_stream)
                    else:
                        # Not a match: must retreat
                        yield token
                        token = next_token
                        next_token = time_token

            # Words like 'hálftólf' are only used in temporal expressions
            # so can stand alone
            if token.txt in CLOCK_HALF:
                token = TOK.Time(token, *CLOCK_NUMBERS.get(token.txt, (0, 0, 0)))

            # Coalesce 'árið' + [year|number] into year
            if (token.kind == TOK.WORD and token.txt.lower() in YEAR_WORD) and (
                next_token.kind == TOK.YEAR or next_token.kind == TOK.NUMBER
            ):
                token = TOK.Year(
                    token.concatenate(next_token, separator=" "),
                    next_token.integer,
                )
                next_token = next(token_stream)

            # Coalesece 3-digit number followed by 4-digit number into tel. no.
            if (
                token.kind == TOK.NUMBER
                and (next_token.kind == TOK.NUMBER or next_token.kind == TOK.YEAR)
                and token.txt[0] in TELNO_PREFIXES
                and re.search(r"^\d\d\d$", token.txt)
                and re.search(r"^\d\d\d\d$", next_token.txt)
            ):
                telno = token.txt + "-" + next_token.txt
                token = TOK.Telno(token.concatenate(next_token, separator=" "), telno)
                next_token = next(token_stream)

            # Coalesce percentages or promilles into a single token
            if next_token.punctuation in ("%", "‰"):
                if token.kind == TOK.NUMBER:
                    # Percentage: convert to a single 'tight' percentage token
                    # In this case, there are no cases and no gender
                    sign = next_token.txt
                    # Store promille as one-tenth of a percentage
                    factor = 1.0 if sign == "%" else 0.1
                    token = TOK.Percent(
                        token.concatenate(next_token), token.number * factor
                    )
                    next_token = next(token_stream)

            # Coalesce ordinals (1. = first, 2. = second...) into a single token
            if next_token.punctuation == ".":
                if (token.kind == TOK.NUMBER and "," not in token.txt) or (
                    token.kind == TOK.WORD
                    and RE_ROMAN_NUMERAL.match(token.txt)
                    # Don't interpret a known abbreviation as a Roman numeral,
                    # for instance the newspaper 'DV'
                    and token.txt not in Abbreviations.DICT
                ):
                    # Ordinal, i.e. whole number or Roman numeral followed by period:
                    # convert to an ordinal token
                    ord_token: Optional[Tok] = token_stream[0]
                    if ord_token and not (
                        ord_token.kind in TOK.END
                        or ord_token.punctuation in {"„", '"'}
                        or (
                            ord_token.kind == TOK.WORD
                            and ord_token.txt[0].isupper()
                            and month_for_token(ord_token, True) is None
                        )
                    ):
                        # OK: replace the number/Roman numeral and the period
                        # with an ordinal token
                        num = (
                            token.integer
                            if token.kind == TOK.NUMBER
                            else roman_to_int(token.txt)
                        )
                        token = TOK.Ordinal(token.concatenate(next_token), num)
                        # Continue with the following word
                        next_token = next(token_stream)

            # Convert "1920 mm" or "30 °C" to a single measurement token
            if (
                token.kind == TOK.NUMBER or token.kind == TOK.YEAR
            ) and next_token.txt in SI_UNITS:
                value = token.number
                orig_unit = next_token.txt
                unit: str
                unit, factor_func = SI_UNITS.get(orig_unit, ("", 1.0))
                if callable(factor_func):
                    # We have a lambda conversion function
                    value = factor_func(value)
                else:
                    # Simple scaling factor
                    assert isinstance(factor_func, float)
                    value *= factor_func
                if unit in ("%", "‰"):
                    token = TOK.Percent(
                        token.concatenate(next_token, separator=" "), value
                    )
                else:
                    token = TOK.Measurement(
                        token.concatenate(next_token, separator=" "),
                        unit,
                        value,
                    )
                next_token = next(token_stream)

                # Special case for km/klst.
                if (
                    token.kind == TOK.MEASUREMENT
                    and orig_unit == "km"
                    and next_token.txt == "/"
                    and token_stream.txt(0) == "klst"
                ):
                    slashtok = next_token
                    next_token = next(token_stream)

                    unit = token.txt + "/" + next_token.txt
                    temp_tok = token.concatenate(slashtok)
                    temp_tok = temp_tok.concatenate(next_token)
                    token = TOK.Measurement(temp_tok, unit, value)
                    # Eat extra unit
                    next_token = next(token_stream)

            if (
                token.kind == TOK.MEASUREMENT
                and cast(MeasurementTuple, token.val)[0] == "°"
                and next_token.kind == TOK.WORD
                and next_token.txt in {"C", "F", "K"}
            ):
                # Handle 200° C
                new_unit = "°" + next_token.txt
                unit, factor_func = SI_UNITS.get(new_unit, ("", 1.0))
                v = cast(MeasurementTuple, token.val)[1]
                if callable(factor_func):
                    val = factor_func(v)
                else:
                    assert isinstance(factor_func, float)
                    val = factor_func * v

                if convert_measurements:
                    txt: str = token.txt
                    lentoken = len(txt)
                    degree_symbol_span = (lentoken - 1, lentoken)
                    # Remove the ° symbol
                    token.substitute(degree_symbol_span, "")
                    # Add it again in the correct place along with the unit
                    token = token.concatenate(next_token, separator=" °")
                    token = TOK.Measurement(
                        token,
                        unit,
                        val,
                    )
                else:
                    token = TOK.Measurement(
                        token.concatenate(next_token, separator=" "),
                        unit,
                        val,
                    )

                next_token = next(token_stream)

            # Special case for measurement abbreviations
            # erroneously ending with a period.
            # We only allow this for measurements that end with
            # an alphabetic character, i.e. not for ², ³, °, %, ‰.
            # [ Uncomment the last condition for this behavior:
            # We don't do this for measurement units which
            # have other meanings - such as 'gr' (grams), as
            # 'gr.' is probably the abbreviation for 'grein'. ]
            txt = token.txt
            if (
                token.kind == TOK.MEASUREMENT
                and next_token.kind == TOK.PUNCTUATION
                and next_token.txt == "."
                and txt[-1].isalpha()
                # and token.txt.split()[-1] + "." not in Abbreviations.DICT
                and not token_stream.could_be_end_of_sentence()
            ):
                unit, value = cast(MeasurementTuple, token.val)
                # Add the period to the token text
                token = TOK.Measurement(token.concatenate(next_token), unit, value)
                next_token = next(token_stream)

            # Cases such as USD. 44
            if (
                token.txt in CURRENCY_ABBREV
                and next_token.kind == TOK.PUNCTUATION
                and next_token.txt == "."
                and not token_stream.could_be_end_of_sentence()
            ):
                txt = token.txt  # Hack to avoid Pylance/Pyright message
                token = TOK.Currency(token.concatenate(next_token), txt)
                next_token = next(token_stream)

            # Cases such as 19 $, 199.99 $
            if (
                token.kind == TOK.NUMBER
                and next_token.kind == TOK.PUNCTUATION
                and next_token.txt in CURRENCY_SYMBOLS
            ):
                token = TOK.Amount(
                    token.concatenate(next_token, separator=" "),
                    CURRENCY_SYMBOLS.get(next_token.txt, ""),
                    token.number,
                )
                next_token = next(token_stream)

            # Replace straight abbreviations
            # (i.e. those that don't end with a period)
            if token.kind == TOK.WORD and token.val is None:
                txt = token.txt
                if Abbreviations.has_meaning(txt):
                    # Add a meaning to the token
                    token = TOK.Word(token, Abbreviations.get_meaning(txt))

            # Yield the current token and advance to the lookahead
            yield token
            token = next_token

    except StopIteration:
        # Final token (previous lookahead)
        if token:
            yield token


def parse_sentences(token_stream: Iterator[Tok]) -> Iterator[Tok]:
    """Parse a stream of tokens looking for sentences, i.e. substreams within
    blocks delimited by sentence finishers (periods, question marks,
    exclamation marks, etc.)"""

    in_sentence = False
    token: Optional[Tok] = None
    tok_begin_sentence = TOK.Begin_Sentence()
    tok_end_sentence = TOK.End_Sentence()

    try:
        # Maintain a one-token lookahead
        token = next(token_stream)
        while True:
            next_token = next(token_stream)
            if token.kind == TOK.P_BEGIN or token.kind == TOK.P_END:
                # Block start or end: finish the current sentence, if any
                if in_sentence:
                    # If there's whitespace (or something else) hanging on token,
                    # then move it to the end of sentence token.
                    yield tok_end_sentence
                    in_sentence = False
                if token.kind == TOK.P_BEGIN and next_token.kind == TOK.P_END:
                    # P_BEGIN immediately followed by P_END: skip both and continue
                    # The double assignment to token is necessary to ensure that
                    # we are in a correct state if next() raises StopIteration

                    # To preserve origin tracking through this operation we must:
                    # 1. squish the two tokens together
                    _skip_me = token.concatenate(next_token, metadata_from_other=True)
                    # 2. replace their text with nothing (while preserving the original text)
                    _skip_me.substitute((0, len(_skip_me.txt)), "")
                    token = cast(Tok, None)
                    # 3. attach them to the front of the next token
                    token = _skip_me.concatenate(
                        next(token_stream), metadata_from_other=True
                    )
                    continue
            elif token.kind == TOK.X_END:
                assert not in_sentence
            elif token.kind == TOK.S_SPLIT:
                # Empty line in input: make sure to finish the current
                # sentence, if any, even if no ending punctuation has
                # been encountered
                if in_sentence:
                    yield TOK.End_Sentence(token)
                    in_sentence = False
                    token = next_token
                else:
                    # Swallow the S_SPLIT token but preserve any origin whitespace
                    token = token.concatenate(next_token, metadata_from_other=True)
                continue
            else:
                if not in_sentence:
                    # This token starts a new sentence
                    yield tok_begin_sentence
                    in_sentence = True
                if (
                    token.punctuation in PUNCT_INDIRECT_SPEECH
                    and next_token.punctuation in DQUOTES
                ):
                    yield token
                    token = next_token
                    next_token = next(token_stream)
                    if next_token.txt.islower():
                        # Probably indirect speech
                        # „Er einhver þarna?“ sagði konan.
                        yield token
                        token = next_token
                        next_token = next(token_stream)
                    else:
                        yield token
                        token = tok_end_sentence
                        in_sentence = False
                if token.punctuation in END_OF_SENTENCE and not (
                    token.punctuation == "…"
                    and not could_be_end_of_sentence(
                        next_token
                    )  # Excluding sentences with ellipsis in the middle
                ):
                    # Combining punctuation ('??!!!')
                    while (
                        token.punctuation in PUNCT_COMBINATIONS
                        and next_token.punctuation in PUNCT_COMBINATIONS
                    ):
                        # Normalized form comes from the first token except with "…?"
                        v = token.punctuation
                        if v == "…" and next_token.punctuation == "?":
                            v = next_token.punctuation
                        token = TOK.Punctuation(token.concatenate(next_token), v)
                        next_token = next(token_stream)
                    # We may be finishing a sentence with not only a period
                    # but also right parenthesis and quotation marks
                    while next_token.punctuation in SENTENCE_FINISHERS:
                        yield token
                        token = next_token
                        next_token = next(token_stream)
                    # The sentence is definitely finished now
                    yield token
                    token = tok_end_sentence
                    in_sentence = False

            yield token
            token = next_token

    except StopIteration:
        pass

    # Final token (previous lookahead)
    if token is not None and token.kind != TOK.S_SPLIT:
        if not in_sentence and token.kind not in TOK.END:
            # Starting something here
            yield tok_begin_sentence
            in_sentence = True
        yield token
        if in_sentence and token.kind in {TOK.S_END, TOK.P_END}:
            in_sentence = False

    # Done with the input stream
    # If still inside a sentence, finish it
    if in_sentence:
        yield tok_end_sentence


def match_stem_list(token: Tok, stems: Mapping[str, float]) -> Optional[float]:
    """Find the stem of a word token in given dict, or return None if not found"""
    if token.kind != TOK.WORD:
        return None
    return stems.get(token.txt.lower(), None)


def month_for_token(token: Tok, after_ordinal: bool = False) -> Optional[int]:
    """Return a number, 1..12, corresponding to a month name,
    or None if the token does not contain a month name"""
    if not after_ordinal and token.txt in MONTH_BLACKLIST:
        # Special case for 'Ágúst', which we do not recognize
        # as a month name unless it follows an ordinal number
        return None
    m = match_stem_list(token, MONTHS)
    return None if m is None else int(m)


def parse_phrases_1(token_stream: Iterator[Tok]) -> Iterator[Tok]:
    """Handle dates and times"""

    token = cast(Tok, None)
    try:
        # Maintain a one-token lookahead
        token = next(token_stream)
        while True:
            next_token = next(token_stream)
            # Coalesce abbreviations and trailing period
            if token.kind == TOK.WORD and next_token.txt == ".":
                abbrev = token.txt + next_token.txt
                if abbrev in Abbreviations.FINISHERS:
                    token = TOK.Word(
                        token.concatenate(next_token),
                        cast(Optional[list[BIN_Tuple]], token.val),
                    )
                    next_token = next(token_stream)

            # Coalesce [year|number] + ['e.Kr.'|'f.Kr.'] into year
            if token.kind == TOK.YEAR or token.kind == TOK.NUMBER:
                val = token.integer
                nval = None
                if next_token.txt in BCE:  # f.Kr.
                    # Yes, we set year X BCE as year -X ;-)
                    nval = -val
                elif next_token.txt in CE:  # e.Kr.
                    nval = val
                if nval is not None:
                    token = TOK.Year(token.concatenate(next_token, separator=" "), nval)
                    next_token = next(token_stream)
                    if next_token.txt == ".":
                        token = TOK.Year(token.concatenate(next_token), nval)
                        next_token = next(token_stream)
            # Check for [number | ordinal] [month name]
            if (
                token.kind == TOK.ORDINAL or token.kind == TOK.NUMBER
            ) and next_token.kind == TOK.WORD:
                if next_token.txt == "gr.":
                    # Corner case: If we have an ordinal followed by
                    # the abbreviation "gr.", we assume that the only
                    # interpretation of the abbreviation is "grein".
                    next_token = TOK.Word(
                        next_token,
                        [BIN_Tuple("grein", 0, "kvk", "skst", "gr.", "-")],
                    )

                month = month_for_token(next_token, True)
                if month is not None:
                    if token.kind == TOK.NUMBER and "." not in token.txt:
                        # Cases such as "5 mars"
                        token.txt = token.txt + "."
                    token = TOK.Date(
                        token.concatenate(next_token, separator=" "),
                        y=0,
                        m=month,
                        d=token.ordinal,
                    )
                    # Eat the month name token
                    next_token = next(token_stream)

            # Check for [date] [year]
            if token.kind == TOK.DATE and next_token.kind == TOK.YEAR:
                dt = cast(DateTimeTuple, token.val)
                if not dt[0]:
                    # No year yet: add it
                    token = TOK.Date(
                        token.concatenate(next_token, separator=" "),
                        y=cast(int, next_token.val),
                        m=dt[1],
                        d=dt[2],
                    )
                    # Eat the year token
                    next_token = next(token_stream)

            # Check for [date] [time]
            if token.kind == TOK.DATE and next_token.kind == TOK.TIME:
                # Create a time stamp
                y, mo, d = cast(DateTimeTuple, token.val)
                h, m, s = cast(DateTimeTuple, next_token.val)
                token = TOK.Timestamp(
                    token.concatenate(next_token, separator=" "),
                    y=y,
                    mo=mo,
                    d=d,
                    h=h,
                    m=m,
                    s=s,
                )
                # Eat the time token
                next_token = next(token_stream)

            if (
                token.kind == TOK.NUMBER
                and next_token.kind == TOK.TELNO
                and token.txt in COUNTRY_CODES
            ):
                # Check for country code in front of telephone number
                token = TOK.Telno(
                    token.concatenate(next_token, separator=" "),
                    cast(TelnoTuple, next_token.val)[0],
                    cc=token.txt,
                )
                next_token = next(token_stream)

            # Yield the current token and advance to the lookahead
            yield token
            token = next_token

    except StopIteration:
        pass

    # Final token (previous lookahead)
    if token:
        yield token


def parse_date_and_time(token_stream: Iterator[Tok]) -> Iterator[Tok]:
    """Handle dates and times, absolute and relative."""

    token = cast(Tok, None)
    try:
        # Maintain a one-token lookahead
        token = next(token_stream)

        while True:
            next_token = next(token_stream)
            # DATEABS and DATEREL made
            # Check for [number | ordinal] [month name]
            if (
                token.kind == TOK.ORDINAL or token.kind == TOK.NUMBER
            ) and next_token.kind == TOK.WORD:
                month = month_for_token(next_token, True)
                if month is not None:
                    token = TOK.Date(
                        token.concatenate(next_token, separator=" "),
                        y=0,
                        m=month,
                        d=token.ordinal,
                    )
                    # Eat the month name token
                    next_token = next(token_stream)

            # Check for [DATE] [year]
            if token.kind == TOK.DATE and (
                next_token.kind == TOK.NUMBER or next_token.kind == TOK.YEAR
            ):
                dt = cast(DateTimeTuple, token.val)
                if not dt[0]:
                    # No year yet: add it
                    year = next_token.integer
                    if next_token.kind == TOK.NUMBER and not (1776 <= year <= 2100):
                        # If the year is specified by a number, don't
                        # accept it if it is outside the range 1776-2100
                        year = 0
                    if year != 0:
                        token = TOK.Date(
                            token.concatenate(next_token, separator=" "),
                            y=year,
                            m=dt[1],
                            d=dt[2],
                        )
                        # Eat the year token
                        next_token = next(token_stream)

            # Check for [month name] [year|YEAR]
            if token.kind == TOK.WORD and (
                next_token.kind == TOK.NUMBER or next_token.kind == TOK.YEAR
            ):
                month = month_for_token(token)
                if month is not None:
                    year = next_token.integer
                    if next_token.kind == TOK.NUMBER and not (1776 <= year <= 2100):
                        year = 0
                    if year != 0:
                        token = TOK.Date(
                            token.concatenate(next_token, separator=" "),
                            y=year,
                            m=month,
                            d=0,
                        )
                        # Eat the year token
                        next_token = next(token_stream)

            # Check for a single month, change to DATEREL
            if token.kind == TOK.WORD:
                month = month_for_token(token)
                # Don't automatically interpret "mar", etc. as month names,
                # since they are ambiguous
                if month is not None and token.txt not in AMBIGUOUS_MONTH_NAMES:
                    token = TOK.Daterel(token, y=0, m=month, d=0)

            # Split DATE into DATEABS and DATEREL
            if token.kind == TOK.DATE:
                dt = cast(DateTimeTuple, token.val)
                if dt[0] and dt[1] and dt[2]:
                    token = TOK.Dateabs(token, y=dt[0], m=dt[1], d=dt[2])
                else:
                    token = TOK.Daterel(token, y=dt[0], m=dt[1], d=dt[2])

            # Split TIMESTAMP into TIMESTAMPABS and TIMESTAMPREL
            if token.kind == TOK.TIMESTAMP:
                ts: TimeStampTuple = cast(TimeStampTuple, token.val)
                if all(x != 0 for x in ts[0:3]):
                    # Year, month and day all non-zero (h, m, s can be zero)
                    token = TOK.Timestampabs(token, *ts)
                else:
                    token = TOK.Timestamprel(token, *ts)

            # Swallow "e.Kr." and "f.Kr." postfixes
            if token.kind == TOK.DATEABS:
                dt = cast(DateTimeTuple, token.val)
                if next_token.kind == TOK.WORD and next_token.txt in CE_BCE:
                    y = dt[0]
                    if next_token.txt in BCE:
                        # Change year to negative number
                        y = -y
                    token = TOK.Dateabs(
                        token.concatenate(next_token, separator=" "),
                        y=y,
                        m=dt[1],
                        d=dt[2],
                    )
                    # Swallow the postfix
                    next_token = next(token_stream)

            # Check for [date] [time] (absolute)
            if token.kind == TOK.DATEABS:
                if next_token.kind == TOK.TIME:
                    # Create an absolute time stamp
                    y, mo, d = cast(DateTimeTuple, token.val)
                    h, m, s = cast(DateTimeTuple, next_token.val)
                    token = TOK.Timestampabs(
                        token.concatenate(next_token, separator=" "),
                        y=y,
                        mo=mo,
                        d=d,
                        h=h,
                        m=m,
                        s=s,
                    )
                    # Eat the time token
                    next_token = next(token_stream)

            # Check for [date] [time] (relative)
            if token.kind == TOK.DATEREL:
                if next_token.kind == TOK.TIME:
                    # Create a time stamp
                    y, mo, d = cast(DateTimeTuple, token.val)
                    h, m, s = cast(DateTimeTuple, next_token.val)
                    token = TOK.Timestamprel(
                        token.concatenate(next_token, separator=" "),
                        y=y,
                        mo=mo,
                        d=d,
                        h=h,
                        m=m,
                        s=s,
                    )
                    # Eat the time token
                    next_token = next(token_stream)

            # Yield the current token and advance to the lookahead
            yield token
            token = next_token

    except StopIteration:
        pass

    # Final token (previous lookahead)
    if token:
        yield token


def parse_phrases_2(
    token_stream: Iterator[Tok], coalesce_percent: bool = False
) -> Iterator[Tok]:
    """Handle numbers, amounts and composite words."""

    token = cast(Tok, None)
    try:
        # Maintain a one-token lookahead
        token = next(token_stream)

        while True:
            next_token = next(token_stream)

            # Logic for numbers and fractions that are partially or entirely
            # written out in words

            # Check for [CURRENCY] [number] (e.g. kr. 9.900 or USD 50)
            if next_token.kind == TOK.NUMBER and (
                token.txt in ISK_AMOUNT_PRECEDING or token.txt in CURRENCY_ABBREV
            ):
                curr = "ISK" if token.txt in ISK_AMOUNT_PRECEDING else token.txt
                token = TOK.Amount(
                    token.concatenate(next_token, separator=" "),
                    curr,
                    next_token.number,
                )
                next_token = next(token_stream)

            # Check for [number] [ISK_AMOUNT|CURRENCY|PERCENTAGE]
            elif token.kind == TOK.NUMBER and next_token.kind == TOK.WORD:
                if next_token.txt in AMOUNT_ABBREV:
                    # Abbreviations for ISK amounts
                    # For abbreviations, we do not know the case,
                    # but we try to retain the previous case information if any
                    token = TOK.Amount(
                        token.concatenate(next_token, separator=" "),
                        "ISK",
                        token.number * AMOUNT_ABBREV[next_token.txt],
                    )
                    next_token = next(token_stream)

                elif next_token.txt in CURRENCY_ABBREV:
                    # A number followed by an ISO currency abbreviation
                    token = TOK.Amount(
                        token.concatenate(next_token, separator=" "),
                        next_token.txt,
                        token.number,
                    )
                    next_token = next(token_stream)

                else:
                    # Check for [number] 'prósent/prósentustig/hundraðshlutar'
                    if coalesce_percent:
                        percentage = match_stem_list(next_token, PERCENTAGES)
                    else:
                        percentage = None

                    if percentage is not None:
                        # We have '17 prósent': coalesce into a single token
                        token = TOK.Percent(
                            token.concatenate(next_token, separator=" "),
                            token.number,
                        )
                        # Eat the percent word token
                        next_token = next(token_stream)

            # Check for composites:
            # 'stjórnskipunar- og eftirlitsnefnd'
            # 'dómsmála-, viðskipta- og iðnaðarráðherra'
            tq: List[Tok] = []
            while token.kind == TOK.WORD and next_token.punctuation == COMPOSITE_HYPHEN:
                # Accumulate the prefix in tq
                tq.append(token)
                tq.append(TOK.Punctuation(next_token, normalized=HYPHEN))
                # Check for optional comma after the prefix
                comma_token = next(token_stream)
                if comma_token.punctuation == ",":
                    # A comma is present: append it to the queue
                    # and skip to the next token
                    tq.append(comma_token)
                    comma_token = next(token_stream)
                # Reset our two lookahead tokens
                token = comma_token
                next_token = next(token_stream)

            if tq:
                # We have accumulated one or more prefixes
                # ('dómsmála-, viðskipta-')
                if token.kind == TOK.WORD and token.txt in ("og", "eða"):
                    # We have 'viðskipta- og'
                    if next_token.kind != TOK.WORD:
                        # Incorrect: yield the accumulated token
                        # queue and keep the current token and the
                        # next_token lookahead unchanged
                        for t in tq:
                            yield t
                    else:
                        # We have 'viðskipta- og iðnaðarráðherra'
                        # Return a single token with the meanings of
                        # the last word, but an amalgamated token text.
                        # Note: there is no meaning check for the first
                        # part of the composition, so it can be an unknown word.
                        _acc = tq[0]
                        for t in tq[1:] + [token, next_token]:
                            _acc = _acc.concatenate(
                                t, separator=" ", metadata_from_other=True
                            )
                        _acc.substitute_all(" -", "-")
                        _acc.substitute_all(" ,", ",")
                        token = _acc
                        next_token = next(token_stream)
                else:
                    # Incorrect prediction: make amends and continue
                    for t in tq:
                        yield t

            # Yield the current token and advance to the lookahead
            yield token
            token = next_token

    except StopIteration:
        pass

    # Final token (previous lookahead)
    if token:
        yield token


def tokenize(text_or_gen: Union[str, Iterable[str]], **options: Any) -> Iterator[Tok]:
    """Tokenize text in several phases, returning a generator
    (iterable sequence) of tokens that processes tokens on-demand."""

    # Thank you Python for enabling this programming pattern ;-)

    # Make sure that the abbreviation config file has been read
    Abbreviations.initialize()
    with_annotation = options.pop("with_annotation", True)
    coalesce_percent = options.pop("coalesce_percent", False)

    token_stream = parse_tokens(text_or_gen, **options)
    token_stream = parse_particles(token_stream, **options)
    token_stream = parse_sentences(token_stream)
    token_stream = parse_phrases_1(token_stream)
    token_stream = parse_date_and_time(token_stream)

    # Skip the parse_phrases_2 pass if the with_annotation option is False
    if with_annotation:
        token_stream = parse_phrases_2(token_stream, coalesce_percent=coalesce_percent)

    return (t for t in token_stream if t.kind != TOK.X_END)


def tokenize_without_annotation(
    text_or_gen: Union[str, Iterable[str]], **options: Any
) -> Iterator[Tok]:
    """Tokenize without the last pass which can be done more thoroughly
    if BÍN annotation is available, for instance in GreynirEngine."""
    return tokenize(text_or_gen, with_annotation=False, **options)


def split_into_sentences(
    text_or_gen: Union[str, Iterable[str]], **options: Any
) -> Iterator[str]:
    """Shallow tokenization of the input text, which can be either
    a text string or a generator of lines of text (such as a file).
    This function returns a generator of strings, where each string
    is a sentence, and tokens are separated by spaces."""
    to_text: Callable[[Tok], str]
    og = options.pop("original", False)
    if options.pop("normalize", False):
        to_text = normalized_text
    elif og:
        to_text = lambda t: t.original or t.txt
    else:
        to_text = lambda t: t.txt
    curr_sent: List[str] = []
    for t in tokenize_without_annotation(text_or_gen, **options):
        if t.kind in TOK.END:
            # End of sentence/paragraph
            # Note that curr_sent can be an empty list,
            # and in that case we yield an empty string
            if t.kind == TOK.S_END or t.kind == TOK.S_SPLIT:
                if og:
                    yield "".join(curr_sent)
                else:
                    yield " ".join(curr_sent)
            curr_sent = []
        elif t.kind not in TOK.BEGIN:
            txt = to_text(t)
            if txt:
                curr_sent.append(txt)
    if curr_sent:
        if og:
            yield "".join(curr_sent)
        else:
            yield " ".join(curr_sent)


def mark_paragraphs(txt: str) -> str:
    """Insert paragraph markers into plaintext, by newlines"""
    if not txt:
        return "[[]]"
    return "[[" + "]][[".join(t for t in txt.split("\n") if t) + "]]"


def paragraphs(tokens: Iterable[Tok]) -> Iterator[list[tuple[int, list[Tok]]]]:
    """Generator yielding paragraphs from token iterable. Each paragraph is a list
    of sentence tuples. Sentence tuples consist of the index of the first token
    of the sentence (the TOK.S_BEGIN token) and a list of the tokens within the
    sentence, not including the starting TOK.S_BEGIN or the terminating TOK.S_END
    tokens."""

    def valid_sent(sent: Optional[list[Tok]]) -> bool:
        """Return True if the token list in sent is a proper
        sentence that we want to process further"""
        if not sent:
            return False
        # A sentence with only punctuation is not valid
        return any(t[0] != TOK.PUNCTUATION for t in sent)

    sent: List[Tok] = []  # Current sentence
    sent_begin = 0
    current_p: List[Tuple[int, List[Tok]]] = []  # Current paragraph

    for ix, t in enumerate(tokens):
        t0 = t[0]
        if t0 == TOK.S_BEGIN:
            sent = []
            sent_begin = ix
        elif t0 == TOK.S_END:
            if valid_sent(sent):
                # Do not include or count zero-length sentences
                current_p.append((sent_begin, sent))
            sent = []
        elif t0 == TOK.P_BEGIN or t0 == TOK.P_END:
            # New paragraph marker: Start a new paragraph if we didn't have one before
            # or if we already had one with some content
            if valid_sent(sent):
                current_p.append((sent_begin, sent))
            sent = []
            if current_p:
                yield current_p
                current_p = []
        else:
            sent.append(t)

    if valid_sent(sent):
        current_p.append((sent_begin, sent))
    if current_p:
        yield current_p


RE_SPLIT_STR = (
    # The following regex catches Icelandic numbers with dots and a comma
    r"([\+\-\$€]?\d{1,3}(?:\.\d\d\d)+\,\d+)"  # +123.456,789
    # The following regex catches English numbers with commas and a dot
    r"|([\+\-\$€]?\d{1,3}(?:\,\d\d\d)+\.\d+)"  # +123,456.789
    # The following regex catches Icelandic numbers with a comma only
    r"|([\+\-\$€]?\d+\,\d+(?!\.\d))"  # -1234,56
    # The following regex catches English numbers with a dot only
    r"|([\+\-\$€]?\d+\.\d+(?!\,\d))"  # -1234.56
    # The following regex catches Icelandic abbreviations, e.g. a.m.k., A.M.K., þ.e.a.s.
    r"|([^\W\d_]+\.(?:[^\W\d_]+\.)+)(?![^\W\d_]+\s)"
    # The following regex catches degree characters, i.e. °C, °F
    r"|(°[CF])"
    # Finally, space and punctuation
    r"|([~\s" + "".join("\\" + c for c in PUNCTUATION) + r"])"
)
RE_SPLIT = re.compile(RE_SPLIT_STR)


def correct_spaces(s: str) -> str:
    """Utility function to split and re-compose a string
    with correct spacing between tokens.
    NOTE that this function uses a quick-and-dirty approach
    which may not handle all edge cases!"""
    r: List[str] = []
    last = TP_NONE
    double_quote_count = 0
    for w in RE_SPLIT.split(s):
        if w is None:
            continue
        w = w.strip()
        if not w:
            continue
        if len(w) > 1:
            this = TP_WORD
        elif w == '"':
            # For English-type double quotes, we glue them alternatively
            # to the right and to the left token
            this = (TP_LEFT, TP_RIGHT)[double_quote_count % 2]
            double_quote_count += 1
        elif w in LEFT_PUNCTUATION:
            this = TP_LEFT
        elif w in RIGHT_PUNCTUATION:
            this = TP_RIGHT
        elif w in NONE_PUNCTUATION:
            this = TP_NONE
        elif w in CENTER_PUNCTUATION:
            this = TP_CENTER
        else:
            this = TP_WORD
        if (
            (w == "og" or w == "eða")
            and len(r) >= 2
            and r[-1] == "-"
            and r[-2].lstrip().isalpha()
        ):
            # Special case for compounds such as "fjármála- og efnahagsráðuneytið"
            # and "Iðnaðar-, ferðamála- og atvinnuráðuneytið":
            # detach the hyphen from "og"/"eða"
            r.append(" " + w)
        elif (
            this == TP_WORD
            and len(r) >= 2
            and r[-1] == "-"
            and w.isalpha()
            and (r[-2] == "," or r[-2].lstrip() in ("og", "eða"))
        ):
            # Special case for compounds such as
            # "bensínstöðvar, -dælur og -tankar"
            r[-1] = " -"
            r.append(w)
        elif (
            TP_SPACE[last - 1][this - 1]
            and r
            and not (
                # Special case for colon-separated time or duration
                # such as "12:00", "3:15" or "37:02:29"
                w.isnumeric()
                and len(w) == 2
                and len(r) >= 2
                and r[-1] == ":"
                and (p := r[-2].strip()).isnumeric()
                and len(p) in {1, 2}
            )
        ):
            r.append(" " + w)
        else:
            r.append(w)
        last = this
    return "".join(r)


def detokenize(tokens: Iterable[Tok], normalize: bool = False) -> str:
    """Utility function to convert an iterable of tokens back
    to a correctly spaced string. If normalize is True,
    punctuation is normalized before assembling the string."""
    to_text: Callable[[Tok], str] = normalized_text if normalize else lambda t: t.txt
    r: List[str] = []
    last = TP_NONE
    double_quote_count = 0
    for t in tokens:
        w = to_text(t)
        if not w:
            continue
        this = TP_WORD
        if t.kind == TOK.PUNCTUATION:
            if len(w) > 1:
                pass
            elif w == '"':
                # For English-type double quotes, we glue them alternatively
                # to the right and to the left token
                this = (TP_LEFT, TP_RIGHT)[double_quote_count % 2]
                double_quote_count += 1
            elif w in LEFT_PUNCTUATION:
                this = TP_LEFT
            elif w in RIGHT_PUNCTUATION:
                this = TP_RIGHT
            elif w in NONE_PUNCTUATION:
                this = TP_NONE
            elif w in CENTER_PUNCTUATION:
                this = TP_CENTER
        if TP_SPACE[last - 1][this - 1] and r:
            r.append(" " + w)
        else:
            r.append(w)
        last = this
    return "".join(r)


def calculate_indexes(
    tokens: Iterable[Tok], last_is_end: bool = False
) -> Tuple[List[int], List[int]]:
    """Calculate character and byte indexes for a token stream.
    The indexes are the start positions of each token in the original
    text that was tokenized.
    'last_is_end' determines whether to include a "past-the-end" index
    at the end. This index is also the total length of the sequence.
    """

    def byte_len(string: str) -> int:
        return len(bytes(string, encoding="utf-8"))

    char_indexes = [0]
    byte_indexes = [0]

    for t in tokens:
        if t.original:
            char_indexes.append(char_indexes[-1] + len(t.original))
            byte_indexes.append(byte_indexes[-1] + byte_len(t.original))
        else:
            if t.txt:
                # Origin tracking failed for this token.
                # TODO: Can we do something better here?
                # Or guarantee that it doesn't happen?
                raise ValueError(
                    f"Origin tracking failed at {t.txt} near index {char_indexes[-1]}"
                )
            else:
                # This is some marker token that has no text
                pass

    if not last_is_end:
        char_indexes = char_indexes[:-1]
        byte_indexes = byte_indexes[:-1]

    return char_indexes, byte_indexes
