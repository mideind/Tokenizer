# -*- encoding: utf-8 -*-
"""

    Tokenizer for Icelandic text

    Copyright (C) 2019 Miðeind ehf.
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
    returns a generator of tokens. Each token is a tuple,
    typically having the form (type, word, meaning),
    where type is one of the constants specified in the
    TOK class, word is the original word found in the
    source text, and meaning contains auxiliary information
    depending on the token type (such as the definition of
    an abbreviation, or the day, month and year for dates).

"""

from __future__ import absolute_import
from __future__ import unicode_literals

from collections import namedtuple

import re
import datetime
import unicodedata

from .abbrev import Abbreviations
from .definitions import *


# Named tuple for tokens
Tok = namedtuple("Tok", ["kind", "txt", "val"])

# Token types
class TOK:

    PUNCTUATION = 1
    TIME = 2
    DATE = 3
    YEAR = 4
    NUMBER = 5
    WORD = 6
    TELNO = 7
    PERCENT = 8
    URL = 9
    ORDINAL = 10
    TIMESTAMP = 11
    CURRENCY = 12
    AMOUNT = 13
    PERSON = 14
    EMAIL = 15
    ENTITY = 16
    UNKNOWN = 17
    DATEABS = 18
    DATEREL = 19
    TIMESTAMPABS = 20
    TIMESTAMPREL = 21
    MEASUREMENT = 22
    NUMWLETTER = 23
    DOMAIN = 24
    HASHTAG = 25

    P_BEGIN = 10001  # Paragraph begin
    P_END = 10002  # Paragraph end

    S_BEGIN = 11001  # Sentence begin
    S_END = 11002  # Sentence end

    X_END = 12001  # End sentinel

    END = frozenset((P_END, S_END, X_END))
    TEXT = frozenset((WORD, PERSON, ENTITY))
    TEXT_EXCL_PERSON = frozenset((WORD, ENTITY))

    # Token descriptive names

    descr = {
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
        NUMWLETTER: "NUMBER WITH LETTER",
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
        P_BEGIN: "BEGIN PARA",
        P_END: "END PARA",
        S_BEGIN: "BEGIN SENT",
        S_END: "END SENT",
    }

    # Token constructors
    @staticmethod
    def Punctuation(w):
        tp = TP_CENTER  # Default punctuation type
        if w:
            if w[0] in LEFT_PUNCTUATION:
                tp = TP_LEFT
            elif w[0] in RIGHT_PUNCTUATION:
                tp = TP_RIGHT
            elif w[0] in NONE_PUNCTUATION:
                tp = TP_NONE
        return Tok(TOK.PUNCTUATION, w, tp)

    @staticmethod
    def Time(w, h, m, s):
        return Tok(TOK.TIME, w, (h, m, s))

    @staticmethod
    def Date(w, y, m, d):
        return Tok(TOK.DATE, w, (y, m, d))

    @staticmethod
    def Dateabs(w, y, m, d):
        return Tok(TOK.DATEABS, w, (y, m, d))

    @staticmethod
    def Daterel(w, y, m, d):
        return Tok(TOK.DATEREL, w, (y, m, d))

    @staticmethod
    def Timestamp(w, y, mo, d, h, m, s):
        return Tok(TOK.TIMESTAMP, w, (y, mo, d, h, m, s))

    @staticmethod
    def Timestampabs(w, y, mo, d, h, m, s):
        return Tok(TOK.TIMESTAMPABS, w, (y, mo, d, h, m, s))

    @staticmethod
    def Timestamprel(w, y, mo, d, h, m, s):
        return Tok(TOK.TIMESTAMPREL, w, (y, mo, d, h, m, s))

    @staticmethod
    def Year(w, n):
        return Tok(TOK.YEAR, w, n)

    @staticmethod
    def Telno(w):
        return Tok(TOK.TELNO, w, None)

    @staticmethod
    def Email(w):
        return Tok(TOK.EMAIL, w, None)

    @staticmethod
    def Number(w, n, cases=None, genders=None):
        """ cases is a list of possible cases for this number
            (if it was originally stated in words) """
        return Tok(TOK.NUMBER, w, (n, cases, genders))

    @staticmethod
    def NumberWithLetter(w, n, l):
        return Tok(TOK.NUMWLETTER, w, (n, l))

    @staticmethod
    def Currency(w, iso, cases=None, genders=None):
        """ cases is a list of possible cases for this currency name
            (if it was originally stated in words, i.e. not abbreviated) """
        return Tok(TOK.CURRENCY, w, (iso, cases, genders))

    @staticmethod
    def Amount(w, iso, n, cases=None, genders=None):
        """ cases is a list of possible cases for this amount
            (if it was originally stated in words) """
        return Tok(TOK.AMOUNT, w, (n, iso, cases, genders))

    @staticmethod
    def Percent(w, n, cases=None, genders=None):
        return Tok(TOK.PERCENT, w, (n, cases, genders))

    @staticmethod
    def Ordinal(w, n):
        return Tok(TOK.ORDINAL, w, n)

    @staticmethod
    def Url(w):
        return Tok(TOK.URL, w, None)

    @staticmethod
    def Domain(w):
        return Tok(TOK.DOMAIN, w, None)

    @staticmethod
    def Hashtag(w):
        return Tok(TOK.HASHTAG, w, None)

    @staticmethod
    def Measurement(w, unit, val):
        return Tok(TOK.MEASUREMENT, w, (unit, val))

    @staticmethod
    def Word(w, m=None):
        """ m is a list of BIN_Meaning tuples fetched from the BÍN database """
        return Tok(TOK.WORD, w, m)

    @staticmethod
    def Unknown(w):
        return Tok(TOK.UNKNOWN, w, None)

    @staticmethod
    def Person(w, m=None):
        """ m is a list of PersonName tuples: (name, gender, case) """
        return Tok(TOK.PERSON, w, m)

    @staticmethod
    def Entity(w):
        return Tok(TOK.ENTITY, w, None)

    @staticmethod
    def Begin_Paragraph():
        return Tok(TOK.P_BEGIN, None, None)

    @staticmethod
    def End_Paragraph():
        return Tok(TOK.P_END, None, None)

    @staticmethod
    def Begin_Sentence(num_parses=0, err_index=None):
        return Tok(TOK.S_BEGIN, None, (num_parses, err_index))

    @staticmethod
    def End_Sentence():
        return Tok(TOK.S_END, None, None)

    @staticmethod
    def End_Sentinel():
        return Tok(TOK.X_END, None, None)


def is_valid_date(y, m, d):
    """ Returns True if y, m, d is a valid date """
    if (1776 <= y <= 2100) and (1 <= m <= 12) and (1 <= d <= 31):
        try:
            datetime.datetime(year=y, month=m, day=d)
            return True
        except ValueError:
            pass
    return False


def parse_digits(w, convert_numbers, convert_telnos):
    """ Parse a raw token starting with a digit """
    s = re.match(r"\d{1,2}:\d\d:\d\d", w)
    if s:
        # Looks like a 24-hour clock, H:M:S
        w = s.group()
        p = w.split(":")
        h = int(p[0])
        m = int(p[1])
        sec = int(p[2])
        if (0 <= h < 24) and (0 <= m < 60) and (0 <= sec < 60):
            return TOK.Time(w, h, m, sec), s.end()
    s = re.match(r"\d{1,2}:\d\d", w)
    if s:
        # Looks like a 24-hour clock, H:M
        w = s.group()
        p = w.split(":")
        h = int(p[0])
        m = int(p[1])
        if (0 <= h < 24) and (0 <= m < 60):
            return TOK.Time(w, h, m, 0), s.end()
    s = re.match(r"\d{1,2}\.\d{1,2}\.\d{2,4}", w) or re.match(
        r"\d{1,2}/\d{1,2}/\d{2,4}", w
    )
    if s:
        # Looks like a date
        g = s.group()
        if "/" in g:
            p = g.split("/")
        else:
            p = g.split(".")
        y = int(p[2])
        # noinspection PyAugmentAssignment
        if y <= 99:
            y = 2000 + y
        m = int(p[1])
        d = int(p[0])
        if m > 12 >= d:
            # Probably wrong way around
            m, d = d, m
        if is_valid_date(y, m, d):
            return TOK.Date(g, y, m, d), s.end()
    # Note: the following must use re.UNICODE to make sure that
    # \w matches all Icelandic characters under Python 2
    s = re.match(r"\d+([a-zA-Z])(?!\w)", w, re.UNICODE)
    if s:
        # Looks like a number with a single trailing character, e.g. 14b, 33C, 1122f
        g = s.group()
        l = g[-1:]
        # Only match if the single character is not a unit of measurement (e.g. 'A', 'l', 'V')
        if l not in SI_UNITS.keys():
            n = int(g[:-1])
            return TOK.NumberWithLetter(g, n, l), s.end()
    s = re.match(r"(\d+)([\u00BC-\u00BE\u2150-\u215E])", w)
    if s:
        # One or more digits, followed by a unicode vulgar fraction char (e.g. '2½')
        ln = s.group(1)
        vf = s.group(2)
        val = float(ln) + unicodedata.numeric(vf)
        return TOK.Number(w, val), s.end()
    s = re.match(r"\d+(\.\d\d\d)*,\d+(?!\d*\.\d)", w)  # Can't end with digits.digits
    if s:
        # Real number formatted with decimal comma and possibly thousands separator
        # (we need to check this before checking integers)
        g = s.group()
        n = re.sub(r"\.", "", g)  # Eliminate thousands separators
        n = re.sub(",", ".", n)  # Convert decimal comma to point
        return TOK.Number(g, float(n)), s.end()
    s = re.match(r"\d+(\.\d\d\d)+", w)
    if s:
        # Integer with a '.' thousands separator
        # (we need to check this before checking dd.mm dates)
        g = s.group()
        n = re.sub(r"\.", "", g)  # Eliminate thousands separators
        return TOK.Number(g, int(n)), s.end()
    s = re.match(r"\d{1,2}/\d{1,2}", w)
    if s and (s.end() >= len(w) or w[s.end()] not in DIGITS):
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
            return TOK.Number(g, float(d) / m), s.end()
        if m > 12 >= d:
            # Date is probably wrong way around
            m, d = d, m
        if (1 <= d <= 31) and (1 <= m <= 12):
            # Looks like a (roughly) valid date
            return TOK.Date(g, 0, m, d), s.end()
    s = re.match(r"\d\d\d\d$", w) or re.match(r"\d\d\d\d[^\d]", w)
    if s:
        n = int(w[0:4])
        if 1776 <= n <= 2100:
            # Looks like a year
            return TOK.Year(w[0:4], n), 4
    s = re.match(r"\d\d\d-\d\d\d\d", w)
    if s and s.group()[0] in TELNO_PREFIXES:
        # Looks like a telephone number
        return TOK.Telno(s.group()), s.end()
    s = re.match(r"\d\d\d\d\d\d\d", w)
    if s and s.group()[0] in TELNO_PREFIXES:
        # Looks like a telephone number
        telno = s.group()
        if convert_telnos:
            telno = telno[:3] + "-" + telno[3:]
        return TOK.Telno(telno), s.end()
    s = re.match(r"\d+\.\d+(\.\d+)+", w)
    if s:
        # Some kind of ordinal chapter number: 2.5.1 etc.
        # (we need to check this before numbers with decimal points)
        g = s.group()
        n = re.sub(r"\.", "", g)  # Eliminate dots, 2.5.1 -> 251
        return TOK.Ordinal(g, int(n)), s.end()
    s = re.match(r"\d+(,\d\d\d)*\.\d+", w)
    if s:
        # Real number, possibly with a thousands separator and decimal comma/point
        g = s.group()
        n = re.sub(",", "", g)  # Eliminate thousands separators
        if convert_numbers:
            g = re.sub(",", "x", g)  # Change thousands separator to 'x'
            g = re.sub(r"\.", ",", g)  # Change decimal separator to ','
            g = re.sub("x", ".", g)  # Change 'x' to '.'
        return TOK.Number(g, float(n)), s.end()
    s = re.match(r"\d+(,\d\d\d)*", w)
    if s:
        # Integer, possibly with a ',' thousands separator
        g = s.group()
        n = re.sub(",", "", g)  # Eliminate thousands separators
        if convert_numbers:
            g = re.sub(",", ".", g)  # Change thousands separator to a dot
        return TOK.Number(g, int(n)), s.end()
    # Strange thing
    return TOK.Unknown(w), len(w)


def prepare(txt):
    """ Convert txt to Unicode (on Python 2.7) and replace composite glyphs
        with single code points """
    return UNICODE_REGEX.sub(
        lambda match: UNICODE_REPLACEMENTS[match.group(0)], make_str(txt)
    )


def parse_tokens(txt, options):
    """ Generator that parses contiguous text into a stream of tokens """

    convert_numbers = options.get("convert_numbers", False)
    convert_telnos = options.get("convert_telnos", False)
    # The default behavior for kludgy ordinals is to pass them
    # through as word tokens
    handle_kludgy_ordinals = options.get(
        "handle_kludgy_ordinals", KLUDGY_ORDINALS_PASS_THROUGH
    )

    rough = prepare(txt).split()

    for w in rough:
        # Handle each sequence of non-whitespace characters

        qmark = False

        if w.isalpha() or w in SI_UNITS:
            # Shortcut for most common case: pure word
            yield TOK.Word(w, None)
            continue

        # More complex case of mixed punctuation, letters and numbers
        if len(w) > 2:
            if w[0] in DQUOTES and w[-1] in DQUOTES:
                # Convert to matching Icelandic quotes
                qmark = True
                yield TOK.Punctuation("„")
                if w[1:-1].isalpha():
                    yield TOK.Word(w[1:-1], None)
                    yield TOK.Punctuation("“")
                    qmark = False
                    continue
                w = w[1:-1] + "“"
            elif w[0] in SQUOTES and w[-1] in SQUOTES:
                # Convert to matching Icelandic quotes
                qmark = True
                yield TOK.Punctuation("‚")
                if w[1:-1].isalpha():
                    yield TOK.Word(w[1:-1], None)
                    yield TOK.Punctuation("‘")
                    qmark = False
                    continue
                w = w[1:-1] + "‘"

        if len(w) > 1:
            if w[0] in DQUOTES:
                # Convert simple quotes to proper opening quotes
                yield TOK.Punctuation("„")
                w = w[1:]
            elif w[0] in SQUOTES:
                # Convert simple quotes to proper opening quotes
                yield TOK.Punctuation("‚")
                w = w[1:]

        while w:
            # Punctuation
            ate = False
            while w and w[0] in PUNCTUATION:
                ate = True
                lw = len(w)
                if w.startswith("[...]"):
                    yield TOK.Punctuation("[…]")
                    w = w[5:]
                elif w.startswith("[…]"):
                    yield TOK.Punctuation("[…]")
                    w = w[3:]
                elif w.startswith("..."):
                    # Treat ellipsis as one piece of punctuation
                    yield TOK.Punctuation("…")
                    w = w[3:]
                elif w == ",,":
                    # Was at the end of a word or by itself, should be ",". GrammCorr 1K
                    yield TOK.Punctuation(",")
                    w = ""
                elif w.startswith(",,"):
                    # Probably an idiot trying to type opening double quotes with commas
                    yield TOK.Punctuation("„")
                    w = w[2:]
                elif lw == 2 and (w == "[[" or w == "]]"):
                    # Begin or end paragraph marker
                    if w == "[[":
                        yield TOK.Begin_Paragraph()
                    else:
                        yield TOK.End_Paragraph()
                    w = w[2:]
                elif w[0] in HYPHENS:
                    # Represent all hyphens the same way
                    yield TOK.Punctuation(HYPHEN)
                    w = w[1:]
                    # Any sequence of hyphens is treated as a single hyphen
                    while w and w[0] in HYPHENS:
                        w = w[1:]
                elif lw == 1 and w in DQUOTES:
                    # Convert to a proper closing double quote
                    yield TOK.Punctuation("“")
                    w = ""
                    qmark = False
                elif lw == 1 and w in SQUOTES:
                    # Left with a single quote, convert to proper closing quote
                    yield TOK.Punctuation("‘")
                    w = ""
                    qmark = False
                elif lw > 1 and w.startswith("#"):
                    # Might be a hashtag, processed later
                    ate = False
                    break
                else:
                    yield TOK.Punctuation(w[0])
                    w = w[1:]
            if w and "@" in w:
                # Check for valid e-mail
                # Note: we don't allow double quotes (simple or closing ones) in e-mails here
                # even though they're technically allowed according to the RFCs
                s = re.match(r"[^@\s]+@[^@\s]+(\.[^@\s\.,/:;\"”]+)+", w)
                if s:
                    ate = True
                    yield TOK.Email(s.group())
                    w = w[s.end() :]

            # Unicode single-char vulgar fractions
            # TODO: Support multiple-char unicode fractions that
            # use super/subscript w. DIVISION SLASH (U+2215)
            if w and w[0] in SINGLECHAR_FRACTIONS:
                ate = True
                yield TOK.Number(w[0], unicodedata.numeric(w[0]))
                w = w[1:]
            if w and w.startswith(URL_PREFIXES):
                # Handle URL: cut RIGHT_PUNCTUATION characters off its end,
                # even though many of them are actually allowed according to
                # the IETF RFC
                endp = ""
                while w and w[-1] in RIGHT_PUNCTUATION:
                    endp = w[-1] + endp
                    w = w[:-1]
                yield TOK.Url(w)
                ate = True
                w = endp
            if w and len(w) >= 2 and re.search(r"^#\w", w, re.UNICODE):
                # Handle hashtags. Eat all text up to next punctuation character
                # so we can handle strings like "#MeToo-hreyfingin" as two words
                tag = w[:1]
                w = w[1:]
                while w and w[0] not in PUNCTUATION:
                    tag += w[0]
                    w = w[1:]
                if re.search(r"^#\d+$", tag):
                    # Hash is being used as a number sign, e.g. "#12"
                    yield TOK.Ordinal(tag, int(tag[1:]))
                else:
                    yield TOK.Hashtag(tag)
                ate = True
            # Domain name (e.g. greynir.is)
            if (
                w
                and len(w) >= MIN_DOMAIN_LENGTH
                and w[0].isalnum()  # All domains start with an alphanumeric char
                and "." in w[1:-2]  # Optimization, TLD is at least 2 chars
                and DOMAIN_REGEX.search(w)
            ):
                endp = ""
                while w and w[-1] in PUNCTUATION:
                    endp = w[-1] + endp
                    w = w[:-1]
                yield TOK.Domain(w)
                ate = True
                w = endp
            # Numbers or other stuff starting with a digit
            if w and w[0] in DIGITS:
                # Handle kludgy ordinals: '3ji', '5ti', etc.
                for key, val in items(ORDINAL_ERRORS):
                    if w.startswith(key):
                        # This is a kludgy ordinal
                        if handle_kludgy_ordinals == KLUDGY_ORDINALS_MODIFY:
                            # Convert ordinals to corresponding word tokens:
                            # '1sti' -> 'fyrsti', '3ji' -> 'þriðji', etc.
                            yield TOK.Word(val)
                        elif (
                            handle_kludgy_ordinals == KLUDGY_ORDINALS_TRANSLATE
                            and key in ORDINAL_NUMBERS
                        ):
                            # Convert word-form ordinals into ordinal tokens,
                            # i.e. '1sti' -> TOK.Ordinal('1sti', 1),
                            # but leave other kludgy constructs ('2ja')
                            # as word tokens
                            yield TOK.Ordinal(key, ORDINAL_NUMBERS[key])
                        else:
                            # No special handling of kludgy ordinals:
                            # yield them unchanged as word tokens
                            yield TOK.Word(key)
                        eaten = len(key)
                        break  # This skips the for loop 'else'
                else:
                    # Not a kludgy ordinal: eat tokens starting with a digit
                    t, eaten = parse_digits(w, convert_numbers, convert_telnos)
                    yield t
                # Continue where the digits parser left off
                ate = True
                w = w[eaten:]
                if w in SI_UNITS:
                    # Handle the case where a measurement unit is
                    # immediately following a number, without an intervening space
                    # (note that some of them contain nonalphabetic characters,
                    # so they won't be caught by the isalpha() check below)
                    yield TOK.Word(w, None)
                    w = ""
            # Alphabetic characters
            if w and w[0].isalpha():
                ate = True
                i = 1
                lw = len(w)
                while i < lw and (
                    w[i].isalpha()
                    or (
                        w[i] in PUNCT_INSIDE_WORD
                        and (i + 1 == lw or w[i + 1].isalpha())
                    )
                ):
                    # We allow dots to occur inside words in the case of
                    # abbreviations; also apostrophes are allowed within words and at the end
                    # (O'Malley, Mary's, it's, childrens', O‘Donnell)
                    i += 1
                # Make a special check for the occasional erroneous source text case where sentences
                # run together over a period without a space: 'sjávarútvegi.Það'
                a = w.split(".")
                if (
                    len(a) == 2
                    and a[0]
                    and a[0][0].islower()
                    and a[1]
                    and a[1][0].isupper()
                ):
                    # We have a lowercase word immediately followed by a period and an uppercase word
                    yield TOK.Word(a[0])
                    yield TOK.Punctuation(".")
                    yield TOK.Word(a[1])
                    w = None
                else:
                    while w[i - 1] == ".":
                        # Don't eat periods at the end of words
                        i -= 1
                    yield TOK.Word(w[0:i])
                    w = w[i:]
                    if w and w[0] in COMPOSITE_HYPHENS:
                        # This is a hyphen or en dash directly appended to a word:
                        # might be a continuation ('fjármála- og efnahagsráðuneyti')
                        # Yield a special hyphen as a marker
                        yield TOK.Punctuation(COMPOSITE_HYPHEN)
                        w = w[1:]
                    if qmark and w and w[:-1].isalpha():
                        yield TOK.Word(w[:-1])
                        w = w[-1:]
                        if w in SQUOTES:
                            yield TOK.Punctuation("‘")
                            w = ""
                        elif w in DQUOTES:
                            yield TOK.Punctuation("“")
                            w = ""
                        qmark = False
            if not ate:
                # Ensure that we eat everything, even unknown stuff
                yield TOK.Unknown(w[0])
                w = w[1:]
            # We have eaten something from the front of the raw token.
            # Check whether we're left with a simple double quote,
            # in which case we convert it to a proper closing double quote
            if w:
                if w[0] in DQUOTES:
                    w = "“" + w[1:]
                elif w[0] in SQUOTES:
                    w = "‘" + w[1:]

    # Yield a sentinel token at the end that will be cut off by the final generator
    yield TOK.End_Sentinel()


def parse_particles(token_stream, options):
    """ Parse a stream of tokens looking for 'particles'
        (simple token pairs and abbreviations) and making substitutions """

    convert_telnos = options.get("convert_telnos", False)

    def is_abbr_with_period(txt):
        """ Return True if the given token text is an abbreviation when followed by a period """
        if "." in txt and txt not in Abbreviations.DICT:
            # There is already a period in it: must be an abbreviation
            # (this applies for instance to "t.d" but not to "mbl.is")
            return True
        if txt in Abbreviations.SINGLES:
            # The token's literal text is defined as an abbreviation followed by a single period
            return True
        if txt.lower() in Abbreviations.SINGLES:
            # The token is in upper or mixed case:
            # We allow it as an abbreviation unless the exact form (most often uppercase)
            # is an abbreviation that doesn't require a period (i.e. isn't in SINGLES).
            # This applies for instance to DR which means "Danmark's Radio" instead of "doktor" (dr.)
            return txt not in Abbreviations.DICT
        return False

    def lookup(abbrev):
        """ Look up an abbreviation, both in original case and in lower case,
            and return either None if not found or a meaning list having one entry """
        m = Abbreviations.DICT.get(abbrev)
        if m is not None:
            return [m]
        m = Abbreviations.DICT.get(abbrev.lower())
        return None if m is None else [m]

    token = None
    try:

        # Maintain a one-token lookahead
        token = next(token_stream)
        while True:
            next_token = next(token_stream)
            # Make the lookahead checks we're interested in

            clock = False

            # Check for currency symbol followed by number, e.g. $10
            if token.txt in CURRENCY_SYMBOLS:
                for symbol, currabbr in CURRENCY_SYMBOLS.items():
                    if (
                        token.kind == TOK.PUNCTUATION
                        and token.txt == symbol
                        and next_token.kind == TOK.NUMBER
                    ):
                        token = TOK.Amount(
                            token.txt + next_token.txt, currabbr, next_token.val[0]
                        )
                        next_token = next(token_stream)
                        break

            # Coalesce abbreviations ending with a period into a single
            # abbreviation token
            if next_token.kind == TOK.PUNCTUATION and next_token.txt == ".":

                if (
                    token.kind == TOK.WORD
                    and token.txt[-1] != "."
                    and is_abbr_with_period(token.txt)
                ):
                    # Abbreviation ending with period: make a special token for it
                    # and advance the input stream

                    clock = token.txt.lower() == CLOCK_ABBREV
                    follow_token = next(token_stream)
                    abbrev = token.txt + "."

                    # Check whether we might be at the end of a sentence, i.e.
                    # the following token is an end-of-sentence or end-of-paragraph,
                    # or uppercase (and not a month name misspelled in upper case).

                    if abbrev in Abbreviations.NAME_FINISHERS:
                        # For name finishers (such as 'próf.') we don't consider a
                        # following person name as an indicator of an end-of-sentence
                        # !!! TODO: This does not work as intended because person names
                        # !!! have not been recognized at this phase in the token pipeline.
                        test_set = TOK.TEXT_EXCL_PERSON
                    else:
                        test_set = TOK.TEXT

                    finish = (follow_token.kind in TOK.END) or (
                        follow_token.kind in test_set
                        and follow_token.txt[0].isupper()
                        and follow_token.txt.lower() not in MONTHS
                        and not RE_ROMAN_NUMERAL.match(follow_token.txt)
                        and not (
                            abbrev in MULTIPLIERS
                            and follow_token.txt in CURRENCY_ABBREV
                        )
                    )

                    if finish:
                        # Potentially at the end of a sentence
                        if abbrev in Abbreviations.FINISHERS:
                            # We see this as an abbreviation even if the next sentence seems
                            # to be starting just after it.
                            # Yield the abbreviation without a trailing dot,
                            # and then an 'extra' period token to end the current sentence.
                            token = TOK.Word(token.txt, lookup(abbrev))
                            yield token
                            token = next_token
                        elif abbrev in Abbreviations.NOT_FINISHERS:
                            # This is an abbreviation that we don't interpret as such
                            # if it's at the end of a sentence ('dags.', 'próf.', 'mín.')
                            yield token
                            token = next_token
                        else:
                            # Substitute the abbreviation and eat the period
                            token = TOK.Word(abbrev, lookup(abbrev))
                    else:
                        # 'Regular' abbreviation in the middle of a sentence:
                        # swallow the period and yield the abbreviation as a single token
                        token = TOK.Word(abbrev, lookup(abbrev))

                    next_token = follow_token

            # Coalesce 'klukkan'/[kl.] + time or number into a time
            if next_token.kind == TOK.TIME or next_token.kind == TOK.NUMBER:
                if clock or (
                    token.kind == TOK.WORD and token.txt.lower() == CLOCK_WORD
                ):
                    # Match: coalesce and step to next token
                    txt = CLOCK_ABBREV + "." if clock else token.txt
                    if next_token.kind == TOK.NUMBER:
                        # next_token.txt may be a real number, i.e. 13,40,
                        # which may have been converted from 13.40
                        # If we now have hh.mm, parse it as such
                        a = "{0:.2f}".format(next_token.val[0]).split(".")
                        h, m = int(a[0]), int(a[1])
                        token = TOK.Time(txt + " " + next_token.txt, h, m, 0)
                    else:
                        # next_token.kind is TOK.TIME
                        token = TOK.Time(
                            txt + " " + next_token.txt,
                            next_token.val[0],
                            next_token.val[1],
                            next_token.val[2],
                        )
                    next_token = next(token_stream)

            # Coalesce 'klukkan/kl. átta/hálfátta' into a time
            elif next_token.txt in CLOCK_NUMBERS:
                if clock or (
                    token.kind == TOK.WORD and token.txt.lower() == CLOCK_WORD
                ):
                    txt = CLOCK_ABBREV + "." if clock else token.txt
                    # Match: coalesce and step to next token
                    token = TOK.Time(
                        txt + " " + next_token.txt, *CLOCK_NUMBERS[next_token.txt]
                    )
                    next_token = next(token_stream)

            # Words like 'hálftólf' only used in temporal expressions so can stand alone
            if token.txt in CLOCK_HALF:
                token = TOK.Time(token.txt, *CLOCK_NUMBERS[token.txt])

            # Coalesce 'árið' + [year|number] into year
            if (token.kind == TOK.WORD and token.txt.lower() in YEAR_WORD) and (
                next_token.kind == TOK.YEAR or next_token.kind == TOK.NUMBER
            ):
                token = TOK.Year(
                    token.txt + " " + next_token.txt,
                    next_token.val
                    if next_token.kind == TOK.YEAR
                    else next_token.val[0],
                )
                next_token = next(token_stream)

            # Coalesece 3-digit number followed by 4-digit number into tel. no.
            # NB: This will not catch phone numbers ending what has previously
            # been identified as a year (e.g. 699 2018)
            if (
                token.kind == TOK.NUMBER
                and (next_token.kind == TOK.NUMBER or next_token.kind == TOK.YEAR)
                and token.txt[0] in TELNO_PREFIXES
                and re.search(r"^\d\d\d$", token.txt)
                and re.search(r"^\d\d\d\d$", next_token.txt)
            ):
                if convert_telnos:
                    telno = token.txt + "-" + next_token.txt
                else:
                    telno = token.txt + " " + next_token.txt
                token = TOK.Telno(telno)
                next_token = next(token_stream)

            # Coalesce percentages into a single token
            if next_token.kind == TOK.PUNCTUATION and next_token.txt == "%":
                if token.kind == TOK.NUMBER:
                    # Percentage: convert to a percentage token
                    # In this case, there are no cases and no gender
                    token = TOK.Percent(token.txt + "%", token.val[0])
                    next_token = next(token_stream)

            # Coalesce ordinals (1. = first, 2. = second...) into a single token
            if next_token.kind == TOK.PUNCTUATION and next_token.txt == ".":
                if (
                    token.kind == TOK.NUMBER
                    and not ("." in token.txt or "," in token.txt)
                ) or (token.kind == TOK.WORD and RE_ROMAN_NUMERAL.match(token.txt)):
                    # Ordinal, i.e. whole number or Roman numeral followed by period: convert to an ordinal token
                    follow_token = next(token_stream)
                    if (
                        follow_token.kind in TOK.END
                        or (
                            follow_token.kind == TOK.PUNCTUATION
                            and follow_token.txt in {"„", '"'}
                        )
                        or (
                            follow_token.kind == TOK.WORD
                            and follow_token.txt[0].isupper()
                            and month_for_token(follow_token, True) is None
                        )
                    ):
                        # Next token is a sentence or paragraph end, or opening quotes,
                        # or an uppercase word (and not a month name misspelled in
                        # upper case): fall back from assuming that this is an ordinal
                        yield token  # Yield the number or Roman numeral
                        token = next_token  # The period
                        # The following (uppercase) word or sentence end
                        next_token = follow_token
                    else:
                        # OK: replace the number/Roman numeral and the period
                        # with an ordinal token
                        num = (
                            token.val[0]
                            if token.kind == TOK.NUMBER
                            else roman_to_int(token.txt)
                        )
                        token = TOK.Ordinal(token.txt + ".", num)
                        # Continue with the following word
                        next_token = follow_token

            if (
                token.kind == TOK.NUMBER or token.kind == TOK.YEAR
            ) and next_token.txt in SI_UNITS:
                # Convert "1800 mm" or "30 °C" to a single measurement token
                value = token.val[0] if token.kind == TOK.NUMBER else token.val
                unit, factor = SI_UNITS[next_token.txt]
                if callable(factor):
                    # We have a lambda conversion function
                    value = factor(value)
                else:
                    # Simple scaling factor
                    value *= factor
                if next_token.txt in RIGHT_PUNCTUATION:
                    # Probably a degree (°)
                    token = TOK.Measurement(token.txt + next_token.txt, unit, value)
                else:
                    token = TOK.Measurement(
                        token.txt + " " + next_token.txt, unit, value
                    )
                next_token = next(token_stream)

            if (
                token.kind == TOK.MEASUREMENT
                and token.val[0] == "°"
                and next_token.kind == TOK.WORD
                and next_token.txt in {"C", "F"}
            ):
                # Handle 200° C
                new_unit = "°" + next_token.txt
                unit, factor = SI_UNITS[new_unit]
                # Both °C and °F have callable (lambda) factors
                assert callable(factor)
                token = TOK.Measurement(
                    token.txt[:-1] + " " + new_unit,  # 200 °C
                    unit,  # K
                    factor(token.val[1]),  # 200 converted to Kelvin
                )
                next_token = next(token_stream)

            # Replace straight abbreviations (i.e. those that don't end with
            # a period)
            if token.kind == TOK.WORD and token.val is None:
                if token.txt in Abbreviations.DICT:
                    # Add a meaning to the token
                    token = TOK.Word(token.txt, [Abbreviations.DICT[token.txt]])

            # Yield the current token and advance to the lookahead
            yield token
            token = next_token

    except StopIteration:
        # Final token (previous lookahead)
        if token:
            yield token


def parse_sentences(token_stream):
    """ Parse a stream of tokens looking for sentences, i.e. substreams within
        blocks delimited by sentence finishers (periods, question marks,
        exclamation marks, etc.) """

    in_sentence = False
    token = None
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
                    yield tok_end_sentence
                    in_sentence = False
                if token.kind == TOK.P_BEGIN and next_token.kind == TOK.P_END:
                    # P_BEGIN immediately followed by P_END:
                    # skip both and continue
                    # Make sure we have correct status if next() raises StopIteration
                    token = None
                    token = next(token_stream)
                    continue
            elif token.kind == TOK.X_END:
                assert not in_sentence
            else:
                if not in_sentence:
                    # This token starts a new sentence
                    yield tok_begin_sentence
                    in_sentence = True
                if token.kind == TOK.PUNCTUATION and token.txt in END_OF_SENTENCE:
                    # We may be finishing a sentence with not only a period but also
                    # right parenthesis and quotation marks
                    while (
                        next_token.kind == TOK.PUNCTUATION
                        and next_token.txt in SENTENCE_FINISHERS
                    ):
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
    if token is not None:
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


def match_stem_list(token, stems):
    """ Find the stem of a word token in given dict, or return None if not found """
    if token.kind != TOK.WORD:
        return None
    return stems.get(token.txt.lower(), None)


def month_for_token(token, after_ordinal=False):
    """ Return a number, 1..12, corresponding to a month name,
        or None if the token does not contain a month name """
    if not(after_ordinal) and token.txt in MONTH_BLACKLIST:
        # Special case for 'Ágúst', which we do not recognize
        # as a month name unless it follows an ordinal number
        return None
    return match_stem_list(token, MONTHS)

  
def parse_phrases_1(token_stream):
    """ Handle dates and times """

    token = None
    try:

        # Maintain a one-token lookahead
        token = next(token_stream)
        while True:
            next_token = next(token_stream)

            # Coalesce [year|number] + ['e.Kr.'|'f.Kr.'] into year
            if token.kind == TOK.YEAR or token.kind == TOK.NUMBER:
                val = token.val if token.kind == TOK.YEAR else token.val[0]
                if next_token.txt in BCE:  # f.Kr.
                    # Yes, we set year X BCE as year -X ;-)
                    token = TOK.Year(token.txt + " " + next_token.txt, -val)
                    next_token = next(token_stream)
                elif next_token.txt in CE:  # e.Kr.
                    token = TOK.Year(token.txt + " " + next_token.txt, val)
                    next_token = next(token_stream)

            # Check for [number | ordinal] [month name]
            if (
                token.kind == TOK.ORDINAL or token.kind == TOK.NUMBER
            ) and next_token.kind == TOK.WORD:

                month = month_for_token(next_token, True)
                if month is not None:
                    token = TOK.Date(
                        token.txt + " " + next_token.txt,
                        y=0,
                        m=month,
                        d=token.val if token.kind == TOK.ORDINAL else token.val[0],
                    )
                    # Eat the month name token
                    next_token = next(token_stream)

            # Check for [date] [year]
            if token.kind == TOK.DATE and next_token.kind == TOK.YEAR:

                if not token.val[0]:
                    # No year yet: add it
                    token = TOK.Date(
                        token.txt + " " + next_token.txt,
                        y=next_token.val,
                        m=token.val[1],
                        d=token.val[2],
                    )
                    # Eat the year token
                    next_token = next(token_stream)

            # Check for [date] [time]
            if token.kind == TOK.DATE and next_token.kind == TOK.TIME:

                # Create a time stamp
                y, mo, d = token.val
                h, m, s = next_token.val
                token = TOK.Timestamp(
                    token.txt + " " + next_token.txt, y=y, mo=mo, d=d, h=h, m=m, s=s
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


def parse_date_and_time(token_stream):
    """ Handle dates and times, absolute and relative. """

    token = None
    try:

        # Maintain a one-token lookahead
        token = next(token_stream)
        while True:
            next_token = next(token_stream)

            # DATEABS and DATEREL made
            # Check for [number | ordinal] [month name]
            if (
                token.kind == TOK.ORDINAL
                or token.kind == TOK.NUMBER
                or (token.txt and token.txt.lower() in DAYS_OF_MONTH)
            ) and next_token.kind == TOK.WORD:

                month = month_for_token(next_token, True)
                if month is not None:
                    token = TOK.Date(
                        token.txt + " " + next_token.txt,
                        y=0,
                        m=month,
                        d=(
                            token.val
                            if token.kind == TOK.ORDINAL
                            else token.val[0]
                            if token.kind == TOK.NUMBER
                            else DAYS_OF_MONTH[token.txt.lower()]
                        ),
                    )
                    # Eat the month name token
                    next_token = next(token_stream)

            # Check for [DATE] [year]
            if token.kind == TOK.DATE and (
                next_token.kind == TOK.NUMBER or next_token.kind == TOK.YEAR
            ):
                if not token.val[0]:
                    # No year yet: add it
                    year = (
                        next_token.val
                        if next_token.kind == TOK.YEAR
                        else next_token.val[0]
                        if 1776 <= next_token.val[0] <= 2100
                        else 0
                    )
                    if year != 0:
                        token = TOK.Date(
                            token.txt + " " + next_token.txt,
                            y=year,
                            m=token.val[1],
                            d=token.val[2],
                        )
                        # Eat the year token
                        next_token = next(token_stream)

            # Check for [month name] [year|YEAR]
            if token.kind == TOK.WORD and (
                next_token.kind == TOK.NUMBER or next_token.kind == TOK.YEAR
            ):
                month = month_for_token(token)
                if month is not None:
                    year = (
                        next_token.val
                        if next_token.kind == TOK.YEAR
                        else next_token.val[0]
                        if 1776 <= next_token.val[0] <= 2100
                        else 0
                    )
                    if year != 0:
                        token = TOK.Date(
                            token.txt + " " + next_token.txt, y=year, m=month, d=0
                        )
                        # Eat the year token
                        next_token = next(token_stream)

            # Check for a single YEAR, change to DATEREL -- changed to keep distinction
            # if token.kind == TOK.YEAR:
            #     token = TOK.Daterel(token.txt, y = token.val, m = 0, d = 0)

            # Check for a single month, change to DATEREL
            if token.kind == TOK.WORD:
                month = month_for_token(token)
                # Don't automatically interpret "mar", etc. as month names,
                # since they are ambiguous
                if month is not None and token.txt not in {
                    "jan",
                    "Jan",
                    "mar",
                    "Mar",
                    "júl",
                    "Júl",
                    "des",
                    "Des",
                    "Ágúst",
                }:
                    token = TOK.Daterel(token.txt, y=0, m=month, d=0)

            # Split DATE into DATEABS and DATEREL
            if token.kind == TOK.DATE:
                if token.val[0] and token.val[1] and token.val[2]:
                    token = TOK.Dateabs(
                        token.txt, y=token.val[0], m=token.val[1], d=token.val[2]
                    )
                else:
                    token = TOK.Daterel(
                        token.txt, y=token.val[0], m=token.val[1], d=token.val[2]
                    )

            # Split TIMESTAMP into TIMESTAMPABS and TIMESTAMPREL
            if token.kind == TOK.TIMESTAMP:
                if all(x != 0 for x in token.val[0:3]):
                    # Year, month and date all non-zero (h, m, s can be zero)
                    token = TOK.Timestampabs(token.txt, *token.val)
                else:
                    token = TOK.Timestamprel(token.txt, *token.val)

            # Swallow "e.Kr." and "f.Kr." postfixes
            if token.kind == TOK.DATEABS:
                if next_token.kind == TOK.WORD and next_token.txt in CE_BCE:
                    y = token.val[0]
                    if next_token.txt in BCE:
                        # Change year to negative number
                        y = -y
                    token = TOK.Dateabs(
                        token.txt + " " + next_token.txt,
                        y=y,
                        m=token.val[1],
                        d=token.val[2],
                    )
                    # Swallow the postfix
                    next_token = next(token_stream)

            # Check for [date] [time] (absolute)
            if token.kind == TOK.DATEABS:
                if next_token.kind == TOK.TIME:
                    # Create an absolute time stamp
                    y, mo, d = token.val
                    h, m, s = next_token.val
                    token = TOK.Timestampabs(
                        token.txt + " " + next_token.txt, y=y, mo=mo, d=d, h=h, m=m, s=s
                    )
                    # Eat the time token
                    next_token = next(token_stream)

            # Check for [date] [time] (relative)
            if token.kind == TOK.DATEREL:
                if next_token.kind == TOK.TIME:
                    # Create a time stamp
                    y, mo, d = token.val
                    h, m, s = next_token.val
                    token = TOK.Timestamprel(
                        token.txt + " " + next_token.txt, y=y, mo=mo, d=d, h=h, m=m, s=s
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


def parse_phrases_2(token_stream):
    """ Handle numbers, amounts and composite words. """

    token = None
    try:

        # Maintain a one-token lookahead
        token = next(token_stream)
        while True:
            next_token = next(token_stream)

            # Logic for numbers and fractions that are partially or entirely
            # written out in words

            def number(tok):
                """ If the token denotes a number, return that number - or None """
                if tok.txt.lower() == "áttu":
                    # Do not accept 'áttu' (stem='átta', no kvk) as a number
                    return None
                return match_stem_list(tok, MULTIPLIERS)

            # Check whether we have an initial number word
            multiplier = number(token) if token.kind == TOK.WORD else None

            # Check for [number] 'hundred|thousand|million|billion'
            while (
                token.kind == TOK.NUMBER or multiplier is not None
            ) and next_token.kind == TOK.WORD:

                multiplier_next = number(next_token)

                def convert_to_num(token):
                    if multiplier is not None:
                        token = TOK.Number(token.txt, multiplier)
                    return token

                if multiplier_next is not None:
                    # Retain the case of the last multiplier
                    token = convert_to_num(token)
                    token = TOK.Number(
                        token.txt + " " + next_token.txt, token.val[0] * multiplier_next
                    )
                    # Eat the multiplier token
                    next_token = next(token_stream)
                elif next_token.txt in AMOUNT_ABBREV:
                    # Abbreviations for ISK amounts
                    # For abbreviations, we do not know the case,
                    # but we try to retain the previous case information if any
                    token = convert_to_num(token)
                    token = TOK.Amount(
                        token.txt + " " + next_token.txt,
                        "ISK",
                        token.val[0] * AMOUNT_ABBREV[next_token.txt],
                    )
                    next_token = next(token_stream)
                elif next_token.txt in CURRENCY_ABBREV:
                    # A number followed by an ISO currency abbreviation
                    token = TOK.Amount(
                        token.txt + " " + next_token.txt, next_token.txt, token.val[0]
                    )
                    next_token = next(token_stream)
                else:
                    # Check for [number] 'percent'
                    percentage = match_stem_list(next_token, PERCENTAGES)
                    if percentage is not None:
                        token = convert_to_num(token)
                        token = TOK.Percent(
                            token.txt + " " + next_token.txt, token.val[0]
                        )
                        # Eat the percentage token
                        next_token = next(token_stream)
                    else:
                        break

                multiplier = None

            # Check for [currency] [number] (e.g. kr. 9.900 or USD 50)
            if next_token.kind == TOK.NUMBER and (
                token.txt in ISK_AMOUNT_PRECEDING or token.txt in CURRENCY_ABBREV
            ):
                curr = "ISK" if token.txt in ISK_AMOUNT_PRECEDING else token.txt
                token = TOK.Amount(
                    token.txt + " " + next_token.txt, curr, next_token.val[0]
                )
                next_token = next(token_stream)

            # Check for composites:
            # 'stjórnskipunar- og eftirlitsnefnd'
            # 'dómsmála-, viðskipta- og iðnaðarráðherra'
            # 'marg-ítrekaðri'
            tq = []
            while (
                token.kind == TOK.WORD
                and next_token.kind == TOK.PUNCTUATION
                and next_token.txt == COMPOSITE_HYPHEN
            ):
                # Accumulate the prefix in tq
                tq.append(token)
                tq.append(TOK.Punctuation(HYPHEN))
                # Check for optional comma after the prefix
                comma_token = next(token_stream)
                if comma_token.kind == TOK.PUNCTUATION and comma_token.txt == ",":
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
                if token.kind == TOK.WORD and (token.txt == "og" or token.txt == "eða"):
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
                        txt = " ".join(t.txt for t in tq + [token, next_token])
                        txt = txt.replace(" -", "-").replace(" ,", ",")
                        token = TOK.Word(txt)
                        next_token = next(token_stream)
                else:
                    # Incorrect prediction: make amends and continue
                    if (
                        token.kind == TOK.WORD
                        and len(tq) == 2
                        and tq[1].txt == HYPHEN
                        and tq[0].txt.lower() in ADJECTIVE_PREFIXES
                    ):
                        # hálf-opinberri, marg-ítrekaðri
                        token = TOK.Word(tq[0].txt + "-" + token.txt)
                    else:
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


def tokenize(text, **options):
    """ Tokenize text in several phases, returning a generator (iterable sequence) of tokens
        that processes tokens on-demand. """

    # Thank you Python for enabling this programming pattern ;-)

    Abbreviations.initialize()  # Make sure that the abbreviation config file has been read

    token_stream = parse_tokens(text, options)
    token_stream = parse_particles(token_stream, options)
    token_stream = parse_sentences(token_stream)
    token_stream = parse_phrases_1(token_stream)
    token_stream = parse_date_and_time(token_stream)
    token_stream = parse_phrases_2(token_stream)

    return (t for t in token_stream if t.kind != TOK.X_END)


def tokenize_without_annotation(text, **options):
    """ Tokenize without the last pass which can be done more thoroughly if BÍN
        annotation is available, for instance in ReynirPackage. """

    Abbreviations.initialize()  # Make sure that the abbreviation config file has been read

    token_stream = parse_tokens(text, options)
    token_stream = parse_particles(token_stream, options)
    token_stream = parse_sentences(token_stream)
    token_stream = parse_phrases_1(token_stream)
    token_stream = parse_date_and_time(token_stream)

    return (t for t in token_stream if t.kind != TOK.X_END)


def mark_paragraphs(txt):
    """ Insert paragraph markers into plaintext, by newlines """
    if not txt:
        return "[[ ]]"
    return "[[ " + " ]] [[ ".join(txt.split("\n")) + " ]]"


def paragraphs(toklist):
    """ Generator yielding paragraphs from a token list. Each paragraph is a list
        of sentence tuples. Sentence tuples consist of the index of the first token
        of the sentence (the TOK.S_BEGIN token) and a list of the tokens within the
        sentence, not including the starting TOK.S_BEGIN or the terminating TOK.S_END
        tokens. """

    def valid_sent(sent):
        """ Return True if the token list in sent is a proper
            sentence that we want to process further """
        if not sent:
            return False
        # A sentence with only punctuation is not valid
        return any(t[0] != TOK.PUNCTUATION for t in sent)

    if not toklist:
        return
    sent = []  # Current sentence
    sent_begin = 0
    current_p = []  # Current paragraph

    for ix, t in enumerate(toklist):
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
    # Finally, space and punctuation
    r"|([~\s"
    + "".join("\\" + c for c in PUNCTUATION)
    + r"])"
)
RE_SPLIT = re.compile(RE_SPLIT_STR)


def correct_spaces(s):
    """ Utility function to split and re-compose a string
        with correct spacing between tokens """
    r = []
    last = TP_NONE
    for w in RE_SPLIT.split(s):
        if w is None:
            continue
        w = w.strip()
        if not w:
            continue
        if len(w) > 1:
            this = TP_WORD
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
        if TP_SPACE[last - 1][this - 1] and r:
            r.append(" " + w)
        else:
            r.append(w)
        last = this
    return "".join(r)
