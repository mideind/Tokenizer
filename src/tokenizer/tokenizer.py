# -*- encoding: utf-8 -*-
"""

    Tokenizer for Icelandic text

    Copyright (C) 2018 Miðeind ehf.
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
from __future__ import print_function
from __future__ import unicode_literals

from collections import namedtuple

import re
import datetime

from .abbrev import Abbreviations


# Recognized punctuation

LEFT_PUNCTUATION = "([„«#$€<"
RIGHT_PUNCTUATION = ".,:;)]!%?“»”’…°>"
CENTER_PUNCTUATION = '"*&+=@©|—'
NONE_PUNCTUATION = "-–/'~‘\\"
PUNCTUATION = LEFT_PUNCTUATION + CENTER_PUNCTUATION + RIGHT_PUNCTUATION + NONE_PUNCTUATION

# Punctuation that ends a sentence
END_OF_SENTENCE = frozenset(['.', '?', '!', '[…]'])
# Punctuation symbols that may additionally occur at the end of a sentence
SENTENCE_FINISHERS = frozenset([')', ']', '“', '»', '”', '’', '"', '[…]'])
# Punctuation symbols that may occur inside words
PUNCT_INSIDE_WORD = frozenset(['.', "'", '‘', "´", "’"]) # Period and apostrophes

# Hyphens that are cast to '-' for parsing and then re-cast
# to normal hyphens, en or em dashes in final rendering
HYPHENS = "—–-"
HYPHEN = '-' # Normal hyphen

# Hyphens that may indicate composite words ('fjármála- og efnahagsráðuneyti')
COMPOSITE_HYPHENS = "–-"
COMPOSITE_HYPHEN = '–' # en dash

CLOCK_WORD = "klukkan"
CLOCK_ABBREV = "kl"

# Prefixes that can be applied to adjectives with an intervening hyphen
ADJECTIVE_PREFIXES = frozenset(["hálf", "marg", "semí"])

# Punctuation types: left, center or right of word

TP_LEFT = 1   # Whitespace to the left
TP_CENTER = 2 # Whitespace to the left and right
TP_RIGHT = 3  # Whitespace to the right
TP_NONE = 4   # No whitespace
TP_WORD = 5   # Flexible whitespace depending on surroundings

# Matrix indicating correct spacing between tokens

TP_SPACE = (
    # Next token is:
    # LEFT    CENTER  RIGHT   NONE    WORD
    # Last token was TP_LEFT:
    ( False,  True,   False,  False,  False),
    # Last token was TP_CENTER:
    ( True,   True,   True,   True,   True),
    # Last token was TP_RIGHT:
    ( True,   True,   False,  False,  True),
    # Last token was TP_NONE:
    ( False,  True,   False,  False,  False),
    # Last token was TP_WORD:
    ( True,   True,   False,  False,  True)
)

# Numeric digits

DIGITS = frozenset([d for d in "0123456789"]) # Set of digit characters

# Month names and numbers

MONTHS = {
    "janúar": 1,
    "febrúar": 2,
    "mars": 3,
    "apríl": 4,
    "maí": 5,
    "júní": 6,
    "júlí": 7,
    "ágúst": 8,
    "september": 9,
    "október": 10,
    "nóvember": 11,
    "desember": 12
}

# Handling of Roman numerals

RE_ROMAN_NUMERAL = re.compile(r"^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")

ROMAN_NUMERAL_MAP = tuple(zip(
    (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1),
    ('M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I')
))

def roman_to_int(s):
    """ Quick and dirty conversion of an already validated Roman numeral to integer """
    # Adapted from http://code.activestate.com/recipes/81611-roman-numerals/
    i = result = 0
    for integer, numeral in ROMAN_NUMERAL_MAP:
        while s[i:i + len(numeral)] == numeral:
            result += integer
            i += len(numeral)
    assert i == len(s)
    return result

# Named tuple for tokens

Tok = namedtuple('Tok', ['kind', 'txt', 'val'])

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

    P_BEGIN = 10001 # Paragraph begin
    P_END = 10002 # Paragraph end

    S_BEGIN = 11001 # Sentence begin
    S_END = 11002 # Sentence end

    X_END = 12001 # End sentinel

    END = frozenset((P_END, S_END, X_END))
    TEXT = frozenset((WORD, PERSON, ENTITY))
    TEXT_EXCL_PERSON = frozenset((WORD, ENTITY))

    # Token descriptive names

    descr = {
        PUNCTUATION: "PUNCTUATION",
        TIME: "TIME",
        TIMESTAMP: "TIMESTAMP",
        DATE: "DATE",
        YEAR: "YEAR",
        NUMBER: "NUMBER",
        CURRENCY: "CURRENCY",
        AMOUNT: "AMOUNT",
        PERSON: "PERSON",
        WORD: "WORD",
        UNKNOWN: "UNKNOWN",
        TELNO: "TELNO",
        PERCENT: "PERCENT",
        URL: "URL",
        EMAIL: "EMAIL",
        ORDINAL: "ORDINAL",
        ENTITY: "ENTITY",
        P_BEGIN: "P_BEGIN",
        P_END: "P_END",
        S_BEGIN: "S_BEGIN",
        S_END: "S_END"
    }

    # Token constructors
    @staticmethod
    def Punctuation(w):
        tp = TP_CENTER # Default punctuation type
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
    def Timestamp(w, y, mo, d, h, m, s):
        return Tok(TOK.TIMESTAMP, w, (y, mo, d, h, m, s))

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
    def Word(w, m = None):
        """ m is a list of BIN_Meaning tuples fetched from the BÍN database """
        return Tok(TOK.WORD, w, m)

    @staticmethod
    def Unknown(w):
        return Tok(TOK.UNKNOWN, w, None)

    @staticmethod
    def Person(w, m = None):
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
    def Begin_Sentence(num_parses = 0, err_index = None):
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
            datetime.datetime(year = y, month = m, day = d)
            return True
        except ValueError:
            pass
    return False


def parse_digits(w):
    """ Parse a raw token starting with a digit """

    s = re.match(r'\d{1,2}:\d\d:\d\d', w)
    if s:
        # Looks like a 24-hour clock, H:M:S
        w = s.group()
        p = w.split(':')
        h = int(p[0])
        m = int(p[1])
        sec = int(p[2])
        if (0 <= h < 24) and (0 <= m < 60) and (0 <= sec < 60):
            return TOK.Time(w, h, m, sec), s.end()
    s = re.match(r'\d{1,2}:\d\d', w)
    if s:
        # Looks like a 24-hour clock, H:M
        w = s.group()
        p = w.split(':')
        h = int(p[0])
        m = int(p[1])
        if (0 <= h < 24) and (0 <= m < 60):
            return TOK.Time(w, h, m, 0), s.end()
    s = re.match(r'\d{1,2}\.\d{1,2}\.\d{2,4}', w) or re.match(r'\d{1,2}/\d{1,2}/\d{2,4}', w)
    if s:
        # Looks like a date
        w = s.group()
        if '/' in w:
            p = w.split('/')
        else:
            p = w.split('.')
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
            return TOK.Date(w, y, m, d), s.end()
    s = re.match(r'\d+(\.\d\d\d)*,\d+', w)
    if s:
        # Real number formatted with decimal comma and possibly thousands separator
        # (we need to check this before checking integers)
        w = s.group()
        n = re.sub(r'\.', '', w) # Eliminate thousands separators
        n = re.sub(r',', '.', n) # Convert decimal comma to point
        return TOK.Number(w, float(n)), s.end()
    s = re.match(r'\d+(\.\d\d\d)+', w)
    if s:
        # Integer with a '.' thousands separator
        # (we need to check this before checking dd.mm dates)
        w = s.group()
        n = re.sub(r'\.', '', w) # Eliminate thousands separators
        return TOK.Number(w, int(n)), s.end()
    s = re.match(r'\d{1,2}/\d{1,2}', w)
    if s and (s.end() >= len(w) or w[s.end()] not in DIGITS):
        # Looks like a date (and not something like 10/2007)
        w = s.group()
        p = w.split('/')
        m = int(p[1])
        d = int(p[0])
        if p[0][0] != '0' and p[1][0] != '0' and ((d <= 5 and m <= 6) or (d == 1 and m <= 10)):
            # This is probably a fraction, not a date
            # (1/2, 1/3, 1/4, 1/5, 1/6, 2/3, 2/5, 5/6 etc.)
            # Return a number
            return TOK.Number(w, float(d) / m), s.end()
        if m > 12 >= d:
            # Date is probably wrong way around
            m, d = d, m
        if (1 <= d <= 31) and (1 <= m <= 12):
            # Looks like a (roughly) valid date
            return TOK.Date(w, 0, m, d), s.end()
    s = re.match(r'\d\d\d\d$', w) or re.match(r'\d\d\d\d[^\d]', w)
    if s:
        n = int(w[0:4])
        if 1776 <= n <= 2100:
            # Looks like a year
            return TOK.Year(w[0:4], n), 4
    s = re.match(r'\d\d\d-\d\d\d\d', w) or re.match(r'\d\d\d\d\d\d\d', w)
    if s:
        # Looks like a telephone number
        return TOK.Telno(s.group()), s.end()
    s = re.match(r'\d+\.\d+(\.\d+)+', w)
    if s:
        # Some kind of ordinal chapter number: 2.5.1 etc.
        # (we need to check this before numbers with decimal points)
        w = s.group()
        n = re.sub(r'\.', '', w) # Eliminate dots, 2.5.1 -> 251
        return TOK.Ordinal(w, int(n)), s.end()
    s = re.match(r'\d+(,\d\d\d)*\.\d+', w)
    if s:
        # Real number, possibly with a thousands separator and decimal comma/point
        w = s.group()
        n = re.sub(r',', '', w) # Eliminate thousands separators
        return TOK.Number(w, float(n)), s.end()
    s = re.match(r'\d+(,\d\d\d)*', w)
    if s:
        # Integer, possibly with a ',' thousands separator
        w = s.group()
        n = re.sub(r',', '', w) # Eliminate thousands separators
        return TOK.Number(w, int(n)), s.end()
    # Strange thing
    return TOK.Unknown(w), len(w)


def parse_tokens(txt):
    """ Generator that parses contiguous text into a stream of tokens """

    rough = txt.split()

    for w in rough:
        # Handle each sequence of non-whitespace characters

        if w.isalpha():
            # Shortcut for most common case: pure word
            yield TOK.Word(w, None)
            continue

        # More complex case of mixed punctuation, letters and numbers
        if len(w) > 1 and w[0] == '"':
            # Convert simple quotes to proper opening quotes
            yield TOK.Punctuation('„')
            w = w[1:]

        while w:
            # Punctuation
            ate = False
            while w and w[0] in PUNCTUATION:
                ate = True
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
                elif w.startswith(",,"):
                    # Probably an idiot trying to type opening double quotes with commas
                    yield TOK.Punctuation('„')
                    w = w[2:]
                elif len(w) == 2 and (w == "[[" or w == "]]"):
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
                else:
                    yield TOK.Punctuation(w[0])
                    w = w[1:]
                if w == '"':
                    # We're left with a simple double quote: Convert to proper closing quote
                    w = '”'
            if w and '@' in w:
                # Check for valid e-mail
                # Note: we don't allow double quotes (simple or closing ones) in e-mails here
                # even though they're technically allowed according to the RFCs
                s = re.match(r"[^@\s]+@[^@\s]+(\.[^@\s\.,/:;\"”]+)+", w)
                if s:
                    ate = True
                    yield TOK.Email(s.group())
                    w = w[s.end():]
            # Numbers or other stuff starting with a digit
            if w and w[0] in DIGITS:
                ate = True
                t, eaten = parse_digits(w)
                yield t
                # Continue where the digits parser left off
                w = w[eaten:]
            if w and w.startswith("http://") or w.startswith("https://"):
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
            # Alphabetic characters
            if w and w[0].isalpha():
                ate = True
                i = 1
                lw = len(w)
                while i < lw and (w[i].isalpha() or (w[i] in PUNCT_INSIDE_WORD and (i+1 == lw or w[i+1].isalpha()))):
                    # We allow dots to occur inside words in the case of
                    # abbreviations; also apostrophes are allowed within words and at the end
                    # (O'Malley, Mary's, it's, childrens', O‘Donnell)
                    i += 1
                # Make a special check for the occasional erroneous source text case where sentences
                # run together over a period without a space: 'sjávarútvegi.Það'
                a = w.split('.')
                if len(a) == 2 and a[0] and a[0][0].islower() and a[1] and a[1][0].isupper():
                    # We have a lowercase word immediately followed by a period and an uppercase word
                    yield TOK.Word(a[0], None)
                    yield TOK.Punctuation('.')
                    yield TOK.Word(a[1], None)
                    w = None
                else:
                    while w[i-1] == '.':
                        # Don't eat periods at the end of words
                        i -= 1
                    yield TOK.Word(w[0:i], None)
                    w = w[i:]
                    if w and w[0] in COMPOSITE_HYPHENS:
                        # This is a hyphen or en dash directly appended to a word:
                        # might be a continuation ('fjármála- og efnahagsráðuneyti')
                        # Yield a special hyphen as a marker
                        yield TOK.Punctuation(COMPOSITE_HYPHEN)
                        w = w[1:]
            if not ate:
                # Ensure that we eat everything, even unknown stuff
                yield TOK.Unknown(w[0])
                w = w[1:]
            # We have eaten something from the front of the raw token.
            # Check whether we're left with a simple double quote,
            # in which case we convert it to a proper closing double quote
            if w and w[0] == '"':
                w = '”' + w[1:]

    # Yield a sentinel token at the end that will be cut off by the final generator
    yield TOK.End_Sentinel()


def parse_particles(token_stream):
    """ Parse a stream of tokens looking for 'particles'
        (simple token pairs and abbreviations) and making substitutions """

    def is_abbr_with_period(txt):
        """ Return True if the given token text is an abbreviation when followed by a period """
        if '.' in txt:
            # There is already a period in it: must be an abbreviation
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
            return [ m ]
        m = Abbreviations.DICT.get(abbrev.lower())
        return None if m is None else [ m ]

    token = None
    try:

        # Maintain a one-token lookahead
        token = next(token_stream)
        while True:
            next_token = next(token_stream)
            # Make the lookahead checks we're interested in

            clock = False

            # Check for $[number]
            if token.kind == TOK.PUNCTUATION and token.txt == '$' and \
                next_token.kind == TOK.NUMBER:

                token = TOK.Amount(token.txt + next_token.txt, "USD", next_token.val[0])
                next_token = next(token_stream)

            # Check for €[number]
            if token.kind == TOK.PUNCTUATION and token.txt == '€' and \
                next_token.kind == TOK.NUMBER:

                token = TOK.Amount(token.txt + next_token.txt, "EUR", next_token.val[0])
                next_token = next(token_stream)

            # Coalesce abbreviations ending with a period into a single
            # abbreviation token
            if next_token.kind == TOK.PUNCTUATION and next_token.txt == '.':

                if token.kind == TOK.WORD and token.txt[-1] != '.' and is_abbr_with_period(token.txt):
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
                        # !!! BUG: This does not work as intended because person names
                        # !!! have not been recognized at this phase in the token pipeline.
                        test_set = TOK.TEXT_EXCL_PERSON
                    else:
                        test_set = TOK.TEXT

                    finish = ((follow_token.kind in TOK.END) or
                        (follow_token.kind in test_set and
                            follow_token.txt[0].isupper() and
                            follow_token.txt.lower() not in MONTHS and
                            not RE_ROMAN_NUMERAL.match(follow_token.txt))
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
                if clock or (token.kind == TOK.WORD and token.txt.lower() == CLOCK_WORD):
                    # Match: coalesce and step to next token
                    if next_token.kind == TOK.NUMBER:
                        token = TOK.Time(CLOCK_ABBREV + ". " + next_token.txt, next_token.val[0], 0, 0)
                    else:
                        token = TOK.Time(CLOCK_ABBREV + ". " + next_token.txt,
                            next_token.val[0], next_token.val[1], next_token.val[2])
                    next_token = next(token_stream)

            # Coalesce percentages into a single token
            if next_token.kind == TOK.PUNCTUATION and next_token.txt == '%':
                if token.kind == TOK.NUMBER:
                    # Percentage: convert to a percentage token
                    # In this case, there are no cases and no gender
                    token = TOK.Percent(token.txt + '%', token.val[0])
                    next_token = next(token_stream)

            # Coalesce ordinals (1. = first, 2. = second...) into a single token
            if next_token.kind == TOK.PUNCTUATION and next_token.txt == '.':
                if (token.kind == TOK.NUMBER and not ('.' in token.txt or ',' in token.txt)) or \
                    (token.kind == TOK.WORD and RE_ROMAN_NUMERAL.match(token.txt)):
                    # Ordinal, i.e. whole number or Roman numeral followed by period: convert to an ordinal token
                    follow_token = next(token_stream)
                    if follow_token.kind in TOK.END or \
                        (follow_token.kind == TOK.PUNCTUATION and follow_token.txt in {'„', '"'}) or \
                        (follow_token.kind == TOK.WORD and follow_token.txt[0].isupper() and
                        follow_token.txt.lower() not in MONTHS):
                        # Next token is a sentence or paragraph end,
                        # or opening quotes,
                        # or an uppercase word (and not a month name misspelled in upper case):
                        # fall back from assuming that this is an ordinal
                        yield token # Yield the number or Roman numeral
                        token = next_token # The period
                        next_token = follow_token # The following (uppercase) word or sentence end
                    else:
                        # OK: replace the number/Roman numeral and the period with an ordinal token
                        num = token.val[0] if token.kind == TOK.NUMBER else roman_to_int(token.txt)
                        token = TOK.Ordinal(token.txt + '.', num)
                        # Continue with the following word
                        next_token = follow_token

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
                    token = None # Make sure we have correct status if next() raises StopIteration
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
                    while next_token.kind == TOK.PUNCTUATION and next_token.txt in SENTENCE_FINISHERS:
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
        if in_sentence and token.kind in { TOK.S_END, TOK.P_END }:
            in_sentence = False

    # Done with the input stream
    # If still inside a sentence, finish it
    if in_sentence:
        yield tok_end_sentence


# Recognize words that multiply numbers
MULTIPLIERS = {
    #"núll": 0,
    #"hálfur": 0.5,
    #"helmingur": 0.5,
    #"þriðjungur": 1.0 / 3,
    #"fjórðungur": 1.0 / 4,
    #"fimmtungur": 1.0 / 5,
    "einn": 1,
    "tveir": 2,
    "þrír": 3,
    "fjórir": 4,
    "fimm": 5,
    "sex": 6,
    "sjö": 7,
    "átta": 8,
    "níu": 9,
    "tíu": 10,
    "ellefu": 11,
    "tólf": 12,
    "þrettán": 13,
    "fjórtán": 14,
    "fimmtán": 15,
    "sextán": 16,
    "sautján": 17,
    "seytján": 17,
    "átján": 18,
    "nítján": 19,
    "tuttugu": 20,
    "þrjátíu": 30,
    "fjörutíu": 40,
    "fimmtíu": 50,
    "sextíu": 60,
    "sjötíu": 70,
    "áttatíu": 80,
    "níutíu": 90,
    #"par": 2,
    #"tugur": 10,
    #"tylft": 12,
    "hundrað": 100,
    "þúsund": 1000, # !!! Bæði hk og kvk!
    "þús.": 1000,
    "milljón": 1e6,
    "milla": 1e6,
    "milljarður": 1e9,
    "miljarður": 1e9,
    "ma.": 1e9
}

# Recognize words for percentages
PERCENTAGES = {
    "prósent": 1,
    "prósenta": 1,
    "hundraðshluti": 1,
    "prósentustig": 1
}

# Amount abbreviations including 'kr' for the ISK
# Corresponding abbreviations are found in Abbrev.conf
AMOUNT_ABBREV = {
    "þ.kr.": 1e3,
    "þús.kr.": 1e3,
    "m.kr.": 1e6,
    "mkr.": 1e6,
    "ma.kr.": 1e9
}


def match_stem_list(token, stems):
    """ Find the stem of a word token in given dict, or return None if not found """
    if token.kind != TOK.WORD:
        return None
    return stems.get(token.txt.lower(), None)


def parse_phrases_1(token_stream):

    """ Handle dates and times """

    token = None
    try:

        # Maintain a one-token lookahead
        token = next(token_stream)
        while True:
            next_token = next(token_stream)

            # Check for [number | ordinal] [month name]
            if (token.kind == TOK.ORDINAL or token.kind == TOK.NUMBER) and next_token.kind == TOK.WORD:

                month = match_stem_list(next_token, MONTHS)
                if month is not None:
                    token = TOK.Date(token.txt + " " + next_token.txt, y = 0, m = month,
                        d = token.val if token.kind == TOK.ORDINAL else token.val[0])
                    # Eat the month name token
                    next_token = next(token_stream)

            # Check for [date] [year]
            if token.kind == TOK.DATE and next_token.kind == TOK.YEAR:

                if not token.val[0]:
                    # No year yet: add it
                    token = TOK.Date(token.txt + " " + next_token.txt,
                        y = next_token.val, m = token.val[1], d = token.val[2])
                    # Eat the year token
                    next_token = next(token_stream)

            # Check for [date] [time]
            if token.kind == TOK.DATE and next_token.kind == TOK.TIME:

                # Create a time stamp
                y, mo, d = token.val
                h, m, s = next_token.val
                token = TOK.Timestamp(token.txt + " " + next_token.txt,
                    y = y, mo = mo, d = d, h = h, m = m, s = s)
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
            while (token.kind == TOK.NUMBER or multiplier is not None) \
                and next_token.kind == TOK.WORD:

                multiplier_next = number(next_token)

                def convert_to_num(token):
                    if multiplier is not None:
                        token = TOK.Number(token.txt, multiplier)
                    return token

                if multiplier_next is not None:
                    # Retain the case of the last multiplier
                    token = convert_to_num(token)
                    token = TOK.Number(token.txt + " " + next_token.txt,
                        token.val[0] * multiplier_next)
                    # Eat the multiplier token
                    next_token = next(token_stream)
                elif next_token.txt in AMOUNT_ABBREV:
                    # Abbreviations for ISK amounts
                    # For abbreviations, we do not know the case,
                    # but we try to retain the previous case information if any
                    token = convert_to_num(token)
                    token = TOK.Amount(token.txt + " " + next_token.txt, "ISK",
                        token.val[0] * AMOUNT_ABBREV[next_token.txt]) # Cases and gender
                    next_token = next(token_stream)
                else:
                    # Check for [number] 'percent'
                    percentage = match_stem_list(next_token, PERCENTAGES)
                    if percentage is not None:
                        token = convert_to_num(token)
                        token = TOK.Percent(token.txt + " " + next_token.txt, token.val[0])
                        # Eat the percentage token
                        next_token = next(token_stream)
                    else:
                        break

                multiplier = None

            # Check for composites:
            # 'stjórnskipunar- og eftirlitsnefnd'
            # 'viðskipta- og iðnaðarráðherra'
            # 'marg-ítrekaðri'
            if token.kind == TOK.WORD and \
                next_token.kind == TOK.PUNCTUATION and next_token.txt == COMPOSITE_HYPHEN:

                og_token = next(token_stream)
                if og_token.kind != TOK.WORD or (og_token.txt != "og" and og_token.txt != "eða"):
                    # Incorrect prediction: make amends and continue
                    handled = False
                    if og_token.kind == TOK.WORD:
                        composite = token.txt + "-" + og_token.txt
                        if token.txt.lower() in ADJECTIVE_PREFIXES:
                            # hálf-opinberri, marg-ítrekaðri
                            token = TOK.Word(composite)
                            next_token = next(token_stream)
                            handled = True
                    if not handled:
                        yield token
                        # Put a normal hyphen instead of the composite one
                        token = TOK.Punctuation(HYPHEN)
                        next_token = og_token
                else:
                    # We have 'viðskipta- og'
                    final_token = next(token_stream)
                    if final_token.kind != TOK.WORD:
                        # Incorrect: unwind
                        yield token
                        yield TOK.Punctuation(HYPHEN) # Normal hyphen
                        token = og_token
                        next_token = final_token
                    else:
                        # We have 'viðskipta- og iðnaðarráðherra'
                        # Return a single token with the meanings of
                        # the last word, but an amalgamated token text.
                        # Note: there is no meaning check for the first
                        # part of the composition, so it can be an unknown word.
                        txt = token.txt + "- " + og_token.txt + \
                            " " + final_token.txt
                        token = TOK.Word(txt)
                        next_token = next(token_stream)

            # Yield the current token and advance to the lookahead
            yield token
            token = next_token

    except StopIteration:
        pass

    # Final token (previous lookahead)
    if token:
        yield token


def tokenize(text):
    """ Tokenize text in several phases, returning a generator (iterable sequence) of tokens
        that processes tokens on-demand. """

    # Thank you Python for enabling this programming pattern ;-)

    Abbreviations.initialize() # Make sure that the abbreviation config file has been read

    token_stream = parse_tokens(text)
    token_stream = parse_particles(token_stream)
    token_stream = parse_sentences(token_stream)
    token_stream = parse_phrases_1(token_stream)
    token_stream = parse_phrases_2(token_stream)

    return (t for t in token_stream if t.kind != TOK.X_END)


def tokenize_without_annotation(text):
    """ Tokenize without the last pass which can be done more thoroughly if BÍN
        annotation is available, for instance in ReynirPackage. """

    Abbreviations.initialize() # Make sure that the abbreviation config file has been read

    token_stream = parse_tokens(text)
    token_stream = parse_particles(token_stream)
    token_stream = parse_sentences(token_stream)
    token_stream = parse_phrases_1(token_stream)

    return (t for t in token_stream if t.kind != TOK.X_END)


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
    sent = [] # Current sentence
    sent_begin = 0
    current_p = [] # Current paragraph

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


RE_SPLIT = (
    # The following regex catches Icelandic numbers with dots and a comma
    r"([\+\-\$€]?\d{1,3}(?:\.\d\d\d)+\,\d+)"    # +123.456,789
    # The following regex catches English numbers with commas and a dot
    r"|([\+\-\$€]?\d{1,3}(?:\,\d\d\d)+\.\d+)"     # +123,456.789
    # The following regex catches Icelandic numbers with a comma only
    r"|([\+\-\$€]?\d+\,\d+)"                      # -1234,56
    # The following regex catches English numbers with a dot only
    r"|([\+\-\$€]?\d+\.\d+)"                      # -1234.56
    # Finally, space and punctuation
    r"|([~\s" + "".join("\\" + c for c in PUNCTUATION) + r"])"
)

def correct_spaces(s):
    """ Utility function to split and re-compose a string with correct spacing between tokens"""
    r = []
    last = TP_NONE
    for w in re.split(RE_SPLIT, s):
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

