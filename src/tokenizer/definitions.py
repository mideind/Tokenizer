# -*- encoding: utf-8 -*-
"""

    Definitions used for tokenization of Icelandic text

    Copyright(C) 2019 Miðeind ehf.
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

"""

from __future__ import absolute_import
from __future__ import unicode_literals

import sys
import re


# Mask away difference between Python 2 and 3
if sys.version_info >= (3, 0):
    items = lambda d: d.items()
    keys = lambda d: d.keys()
    make_str = lambda s: s
    unicode_chr = lambda c: chr(c)
else:
    items = lambda d: d.iteritems()
    keys = lambda d: d.iterkeys()

    def make_str(s):
        if isinstance(s, unicode):
            return s
        # Assume that incoming byte strings are UTF-8 encoded
        return s.decode("utf-8")

    unicode_chr = lambda c: unichr(c)


# TODO: These options will become settable configuration switches
# Auto-convert numbers to Icelandic format (1,234.56 -> 1.234,56)?
CONVERT_NUMBERS = False
# Auto-convert telephone numbers (8881234 -> 888-1234)?
CONVERT_TELNOS = False

ACCENT = unicode_chr(769)
UMLAUT = unicode_chr(776)
SOFT_HYPHEN = unicode_chr(173)
ZEROWIDTH_SPACE = unicode_chr(8203)
ZEROWIDTH_NBSP = unicode_chr(65279)

# Preprocessing of unicode characters before tokenization
UNICODE_REPLACEMENTS = {
    # Translations of separate umlauts and accents to single glyphs.
    # The strings to the left in each tuple are two Unicode code
    # points: vowel + COMBINING ACUTE ACCENT (chr(769)) or
    # vowel + COMBINING DIAERESIS (chr(776)).
    "a" + ACCENT: "á",
    "a" + UMLAUT: "ä",
    "e" + ACCENT: "é",
    "e" + UMLAUT: "ë",
    "i" + ACCENT: "í",
    "o" + ACCENT: "ó",
    "u" + ACCENT: "ú",
    "u" + UMLAUT: "ü",
    "y" + ACCENT: "ý",
    "o" + UMLAUT: "ö",
    "A" + UMLAUT: "Ä",
    "A" + ACCENT: "Á",
    "E" + ACCENT: "É",
    "E" + UMLAUT: "Ë",
    "I" + ACCENT: "Í",
    "O" + ACCENT: "Ó",
    "U" + ACCENT: "Ú",
    "U" + UMLAUT: "Ü",
    "Y" + ACCENT: "Ý",
    "O" + UMLAUT: "Ö",
    # Also remove these unwanted characters
    SOFT_HYPHEN: "",
    ZEROWIDTH_SPACE: "",
    ZEROWIDTH_NBSP: "",
}
UNICODE_REGEX = re.compile("|".join(map(re.escape, keys(UNICODE_REPLACEMENTS))))

# Hyphens that are cast to '-' for parsing and then re-cast
# to normal hyphens, en or em dashes in final rendering
HYPHEN = "-"  # Normal hyphen
EN_DASH = "–"
EM_DASH = "—"

HYPHENS = HYPHEN + EN_DASH + EM_DASH

# Hyphens that may indicate composite words ('fjármála- og efnahagsráðuneyti')
COMPOSITE_HYPHENS = HYPHEN + EN_DASH
COMPOSITE_HYPHEN = EN_DASH

# Recognized punctuation
LEFT_PUNCTUATION = "([„‚«#$€£¥₽<"
RIGHT_PUNCTUATION = ".,:;)]!%?“»”’‛‘…>°"
CENTER_PUNCTUATION = '"*&+=@©|'
NONE_PUNCTUATION = "/±'´~\\" + HYPHEN + EN_DASH + EM_DASH
PUNCTUATION = (
    LEFT_PUNCTUATION + CENTER_PUNCTUATION + RIGHT_PUNCTUATION + NONE_PUNCTUATION
)
PUNCTUATION_REGEX = "[{0}]".format("|".join(re.escape(p) for p in PUNCTUATION))

# Punctuation types: left, center or right of word

TP_LEFT = 1  # Whitespace to the left
TP_CENTER = 2  # Whitespace to the left and right
TP_RIGHT = 3  # Whitespace to the right
TP_NONE = 4  # No whitespace
TP_WORD = 5  # Flexible whitespace depending on surroundings

# Matrix indicating correct spacing between tokens

TP_SPACE = (
    # Next token is:
    # LEFT  CENTER RIGHT   NONE   WORD
    # Last token was TP_LEFT:
    (False, True, False, False, False),
    # Last token was TP_CENTER:
    (True, True, True, True, True),
    # Last token was TP_RIGHT:
    (True, True, False, False, True),
    # Last token was TP_NONE:
    (False, True, False, False, False),
    # Last token was TP_WORD:
    (True, True, False, False, True),
)

# Punctuation that ends a sentence
END_OF_SENTENCE = frozenset([".", "?", "!"])  # Removed […]
# Punctuation symbols that may additionally occur at the end of a sentence
SENTENCE_FINISHERS = frozenset([")", "]", "“", "»", "”", "’", '"', "[…]"])
# Punctuation symbols that may occur inside words
PUNCT_INSIDE_WORD = frozenset([".", "'", "‘", "´", "’"])  # Period and apostrophes

# Single and double quotes
SQUOTES = "'‚‛‘´"
DQUOTES = '"“„”«»'

CLOCK_WORD = "klukkan"
CLOCK_ABBREV = "kl"

TELNO_PREFIXES = "45678"

# Prefixes that can be applied to adjectives with an intervening hyphen
ADJECTIVE_PREFIXES = frozenset(("hálf", "marg", "semí", "full"))

# Words that can precede a year number; will be assimilated into the year token
YEAR_WORD = frozenset(("árið", "ársins", "árinu"))

# Numeric digits
DIGITS = frozenset([d for d in "0123456789"])  # Set of digit characters

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
    "desember": 12,
    "jan.": 1,
    "feb.": 2,
    "mar.": 3,
    "apr.": 4,
    "jún.": 6,
    "júl.": 7,
    "ág.": 8,
    "ágú.": 8,
    "sep.": 9,
    "sept.": 9,
    "okt.": 10,
    "nóv.": 11,
    "des.": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jún": 6,
    "júl": 7,
    "ág": 8,
    "ágú": 8,
    "sep": 9,
    "sept": 9,
    "okt": 10,
    "nóv": 11,
    "des": 12,
}

# The masculine Icelandic name should not be identified as a month
MONTH_BLACKLIST = frozenset(("Ágúst",))

# Days of the month spelled out
DAYS_OF_MONTH = {
    "fyrsti": 1,
    "fyrsta": 1,
    "annar": 2,
    "annan": 2,
    "þriðji": 3,
    "þriðja": 3,
    "fjórði": 4,
    "fjórða": 4,
    "fimmti": 5,
    "fimmta": 5,
    "sjötti": 6,
    "sjötta": 6,
    "sjöundi": 7,
    "sjöunda": 7,
    "áttundi": 8,
    "áttunda": 8,
    "níundi": 9,
    "níunda": 9,
    "tíundi": 10,
    "tíunda": 10,
    "ellefti": 11,
    "ellefta": 11,
    "tólfti": 12,
    "tólfta": 12,
    "þrettándi": 13,
    "þrettánda": 13,
    "fjórtándi": 14,
    "fjórtánda": 14,
    "fimmtándi": 15,
    "fimmtánda": 15,
    "sextándi": 16,
    "sextánda": 16,
    "sautjándi": 17,
    "sautjánda": 17,
    "átjándi": 18,
    "átjánda": 18,
    "nítjándi": 19,
    "nítjánda": 19,
    "tuttugasti": 20,
    "tuttugasta": 20,
    "þrítugasti": 30,
    "þrítugasta": 30,
}

# Time of day expressions spelled out
CLOCK_NUMBERS = {
    "eitt": [1, 0, 0],
    "tvö": [2, 0, 0],
    "þrjú": [3, 0, 0],
    "fjögur": [4, 0, 0],
    "fimm": [5, 0, 0],
    "sex": [6, 0, 0],
    "sjö": [7, 0, 0],
    "átta": [8, 0, 0],
    "níu": [9, 0, 0],
    "tíu": [10, 0, 0],
    "ellefu": [11, 0, 0],
    "tólf": [12, 0, 0],
    "hálfeitt": [12, 30, 0],
    "hálftvö": [1, 30, 0],
    "hálfþrjú": [2, 30, 0],
    "hálffjögur": [3, 30, 0],
    "hálffimm": [4, 30, 0],
    "hálfsex": [5, 30, 0],
    "hálfsjö": [6, 30, 0],
    "hálfátta": [7, 30, 0],
    "hálfníu": [8, 30, 0],
    "hálftíu": [9, 30, 0],
    "hálfellefu": [10, 30, 0],
    "hálftólf": [11, 30, 0],
}

# Set of words only possible in temporal phrases
CLOCK_HALF = frozenset(
    [
        "hálfeitt",
        "hálftvö",
        "hálfþrjú",
        "hálffjögur",
        "hálffimm",
        "hálfsex",
        "hálfsjö",
        "hálfátta",
        "hálfníu",
        "hálftíu",
        "hálfellefu",
        "hálftólf",
    ]
)

# 'Current Era', 'Before Current Era'
CE = frozenset(("e.Kr", "e.Kr."))  # !!! Add AD and CE here?
BCE = frozenset(("f.Kr", "f.Kr."))  # !!! Add BCE here?
CE_BCE = CE | BCE

# Supported ISO 4217 currency codes
CURRENCY_ABBREV = frozenset(
    (
        "ISK",  # Icelandic króna
        "DKK",  # Danish krone
        "NOK",  # Norwegian krone
        "SEK",  # Swedish krona
        "GBP",  # British pounds sterling
        "USD",  # US dollar
        "EUR",  # Euro
        "CAD",  # Canadian dollar
        "AUD",  # Australian dollar
        "CHF",  # Swiss franc
        "JPY",  # Japanese yen
        "PLN",  # Polish złoty
        "RUB",  # Russian ruble
        "CZK",  # Czech koruna
        "INR",  # Indian rupee
        "IDR",  # Indonesian rupiah
        "CNY",  # Chinese renminbi
        "RMB",  # Chinese renminbi (alternate)
        "HKD",  # Hong Kong dollar
        "NZD",  # New Zealand dollar
        "SGD",  # Singapore dollar
        "MXN",  # Mexican peso
        "ZAR",  # South African rand
    )
)

# Map symbols to currency abbreviations
CURRENCY_SYMBOLS = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",  # Also used for China's renminbi (yuan)
    "₽": "RUB",  # Russian ruble
}

# Single-character vulgar fractions in Unicode
SINGLECHAR_FRACTIONS = "↉⅒⅑⅛⅐⅙⅕¼⅓½⅖⅔⅜⅗¾⅘⅝⅚⅞"

# Derived unit : (base SI unit, conversion factor/function)
SI_UNITS = {
    "m²": ("m²", 1.0),
    "fm": ("m²", 1.0),
    "cm²": ("m²", 1.0e-2),
    "m³": ("m³", 1.0),
    "cm³": ("m³", 1.0e-6),
    "l": ("m³", 1.0e-3),
    "ltr": ("m³", 1.0e-3),
    "dl": ("m³", 1.0e-4),
    "cl": ("m³", 1.0e-5),
    "ml": ("m³", 1.0e-6),
    "°C": ("K", lambda x: x + 273.15),
    "°F": ("K", lambda x: (x + 459.67) * 5 / 9),
    "K": ("K", 1.0),
    "g": ("g", 1.0),
    "gr": ("g", 1.0),
    "kg": ("g", 1.0e3),
    "t": ("g", 1.0e6),
    "mg": ("g", 1.0e-3),
    "μg": ("g", 1.0e-6),
    "m": ("m", 1.0),
    "km": ("m", 1.0e3),
    "mm": ("m", 1.0e-3),
    "μm": ("m", 1.0e-6),
    "cm": ("m", 1.0e-2),
    "sm": ("m", 1.0e-2),
    "s": ("s", 1.0),
    "ms": ("s", 1.0e-3),
    "μs": ("s", 1.0e-6),
    "Nm": ("J", 1.0),
    "klst": ("s", 3600.0),
    "mín": ("s", 60.0),
    "W": ("W", 1.0),
    "mW": ("W", 1.0e-3),
    "kW": ("W", 1.0e3),
    "MW": ("W", 1.0e6),
    "GW": ("W", 1.0e9),
    "TW": ("W", 1.0e12),
    "J": ("J", 1.0),
    "kJ": ("J", 1.0e3),
    "MJ": ("J", 1.0e6),
    "GJ": ("J", 1.0e9),
    "TJ": ("J", 1.0e12),
    "kWh": ("J", 3.6e6),
    "MWh": ("J", 3.6e9),
    "kWst": ("J", 3.6e6),
    "MWst": ("J", 3.6e9),
    "kcal": ("J", 4184),
    "cal": ("J", 4.184),
    "N": ("N", 1.0),
    "kN": ("N", 1.0e3),
    "V": ("V", 1.0),
    "mV": ("V", 1.0e-3),
    "kV": ("V", 1.0e3),
    "A": ("A", 1.0),
    "mA": ("A", 1.0e-3),
    "Hz": ("Hz", 1.0),
    "kHz": ("Hz", 1.0e3),
    "MHz": ("Hz", 1.0e6),
    "GHz": ("Hz", 1.0e9),
    "Pa": ("Pa", 1.0),
    "hPa": ("Pa", 1.0e2),
    "°": ("°", 1.0),  # Degree
}

# If the handle_kludgy_ordinals option is set to
# KLUDGY_ORDINALS_PASS_THROUGH, we do not convert
# kludgy ordinals but pass them through as word tokens.
KLUDGY_ORDINALS_PASS_THROUGH = 0
# If the handle_kludgy_ordinals option is set to
# KLUDGY_ORDINALS_MODIFY, we convert '1sti' to 'fyrsti', etc.,
# and return the modified word as a token.
KLUDGY_ORDINALS_MODIFY = 1
# If the handle_kludgy_ordinals option is set to
# KLUDGY_ORDINALS_TRANSLATE, we convert '1sti' to TOK.Ordinal('1sti', 1), etc.,
# but otherwise pass the original word through as a word token ('2ja').
KLUDGY_ORDINALS_TRANSLATE = 2

# Incorrectly written ('kludgy') ordinals
ORDINAL_ERRORS = {
    "1sti": "fyrsti",
    "1sta": "fyrsta",
    "1stu": "fyrstu",
    "3ji": "þriðji",
    "3ja": "þriðja",  # eða þriggja!
    "3ju": "þriðju",
    "4ði": "fjórði",
    "4ða": "fjórða",
    "4ðu": "fjórðu",
    "5ti": "fimmti",
    "5ta": "fimmta",
    "5tu": "fimmtu",
    "2svar": "tvisvar",
    "3svar": "þrisvar",
    "2ja": "tveggja",
    # "3ja" : "þriggja",
    "4ra": "fjögurra",
}

# Translations of kludgy ordinal words into numbers
ORDINAL_NUMBERS = {
    "1sti": 1,
    "1sta": 1,
    "1stu": 1,
    "3ji": 3,
    "3ja": 3,
    "3ju": 3,
    "4ði": 4,
    "4ða": 4,
    "4ðu": 4,
    "5ti": 5,
    "5ta": 5,
    "5tu": 5
}

# Handling of Roman numerals

RE_ROMAN_NUMERAL = re.compile(
    r"^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$"
)

ROMAN_NUMERAL_MAP = tuple(
    zip(
        (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1),
        ("M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"),
    )
)


def roman_to_int(s):
    """ Quick and dirty conversion of an already validated Roman numeral to integer """
    # Adapted from http://code.activestate.com/recipes/81611-roman-numerals/
    i = result = 0
    for integer, numeral in ROMAN_NUMERAL_MAP:
        while s[i : i + len(numeral)] == numeral:
            result += integer
            i += len(numeral)
    assert i == len(s)
    return result


# Recognize words that multiply numbers
MULTIPLIERS = {
    # "núll": 0,
    # "hálfur": 0.5,
    # "helmingur": 0.5,
    # "þriðjungur": 1.0 / 3,
    # "fjórðungur": 1.0 / 4,
    # "fimmtungur": 1.0 / 5,
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
    # "par": 2,
    # "tugur": 10,
    # "tylft": 12,
    "hundrað": 100,
    "þúsund": 1000,  # !!! Bæði hk og kvk!
    "þús.": 1000,
    "milljón": 1e6,
    "milla": 1e6,
    "millj.": 1e6,
    "mljó.": 1e6,
    "milljarður": 1e9,
    "miljarður": 1e9,
    "ma.": 1e9,
    "mrð.": 1e9,
}

# Recognize words for percentages
PERCENTAGES = {"prósent": 1, "prósenta": 1, "hundraðshluti": 1, "prósentustig": 1}

# Amount abbreviations including 'kr' for the ISK
# Corresponding abbreviations are found in Abbrev.conf
AMOUNT_ABBREV = {
    "kr.": 1,
    "kr": 1,
    "krónur": 1,
    "þ.kr.": 1e3,
    "þ.kr": 1e3,
    "þús.kr.": 1e3,
    "þús.kr": 1e3,
    "m.kr.": 1e6,
    "m.kr": 1e6,
    "mkr.": 1e6,
    "mkr": 1e6,
    "millj.kr.": 1e6,
    "millj.kr": 1e6,
    "mljó.kr.": 1e6,
    "mljó.kr": 1e6,
    "ma.kr.": 1e9,
    "ma.kr": 1e9,
    "mö.kr.": 1e9,
    "mö.kr": 1e9,
    "mlja.kr.": 1e9,
    "mlja.kr": 1e9,
}

# Króna amount strings allowed before a number, e.g. "kr. 9.900"
ISK_AMOUNT_PRECEDING = frozenset(("kr.", "kr", "krónur"))


URL_PREFIXES = ("http://", "https://",)


TOP_LEVEL_DOMAINS = frozenset(
    (
        "com",
        "org",
        "net",
        "edu",
        "gov",
        "mil",
        "int",
        "arpa",
        "eu",
        "biz",
        "info",
        "xyz",
        "online",
        "site",
        "tech",
        "top",
        "space",
        "news",
        "pro",
        "club",
        "loan",
        "win",
        "vip",
        "icu",
        "app",
        "blog",
        "shop",
        "work",
        "ltd",
        "mobi",
        "live",
        "store",
        "gdn",
        # ccTLDs
        "ac",
        "ad",
        "ae",
        "af",
        "ag",
        "ai",
        "al",
        "am",
        "ao",
        "aq",
        "ar",
        "as",
        "at",
        "au",
        "aw",
        "ax",
        "az",
        "ba",
        "bb",
        "bd",
        "be",
        "bf",
        "bg",
        "bh",
        "bi",
        "bj",
        "bm",
        "bn",
        "bo",
        "br",
        "bs",
        "bt",
        "bw",
        "by",
        "bz",
        "ca",
        "cc",
        "cd",
        "cf",
        "cg",
        "ch",
        "ci",
        "ck",
        "cl",
        "cm",
        "cn",
        "co",
        "cr",
        "cu",
        "cv",
        "cw",
        "cx",
        "cy",
        "cz",
        "de",
        "dj",
        "dk",
        "dm",
        "do",
        "dz",
        "ec",
        "ee",
        "eg",
        "er",
        "es",
        "et",
        "eu",
        "fi",
        "fj",
        "fk",
        "fm",
        "fo",
        "fr",
        "ga",
        "gd",
        "ge",
        "gf",
        "gg",
        "gh",
        "gi",
        "gl",
        "gm",
        "gn",
        "gp",
        "gq",
        "gr",
        "gs",
        "gt",
        "gu",
        "gw",
        "gy",
        "hk",
        "hm",
        "hn",
        "hr",
        "ht",
        "hu",
        "id",
        "ie",
        "il",
        "im",
        "in",
        "io",
        "iq",
        "ir",
        "is",
        "it",
        "je",
        "jm",
        "jo",
        "jp",
        "ke",
        "kg",
        "kh",
        "ki",
        "km",
        "kn",
        "kp",
        # "kr", # Gives us trouble with "kr" abbreviation (e.g. "þús.kr" is a legitimate domain name)
        "kw",
        "ky",
        "kz",
        "la",
        "lb",
        "lc",
        "li",
        "lk",
        "lr",
        "ls",
        "lt",
        "lu",
        "lv",
        "ly",
        "ma",
        "mc",
        "md",
        "me",
        "mg",
        "mh",
        "mk",
        "ml",
        "mm",
        "mn",
        "mo",
        "mp",
        "mq",
        "mr",
        "ms",
        "mt",
        "mu",
        "mv",
        "mw",
        "mx",
        "my",
        "mz",
        "na",
        "nc",
        "ne",
        "nf",
        "ng",
        "ni",
        "nl",
        "no",
        "np",
        "nr",
        "nu",
        "nz",
        "om",
        "pa",
        "pe",
        "pf",
        "pg",
        "ph",
        "pk",
        "pl",
        "pm",
        "pn",
        "pr",
        "ps",
        "pt",
        "pw",
        "py",
        "qa",
        "re",
        "ro",
        "rs",
        "ru",
        "rw",
        "sa",
        "sb",
        "sc",
        "sd",
        "se",
        "sg",
        "sh",
        "si",
        "sk",
        "sl",
        "sm",
        "sn",
        "so",
        "sr",
        "ss",
        "st",
        "sv",
        "sx",
        "sy",
        "sz",
        "tc",
        "td",
        "tf",
        "tg",
        "th",
        "tj",
        "tk",
        "tl",
        "tm",
        "tn",
        "to",
        "tr",
        "tt",
        "tv",
        "tw",
        "tz",
        "ua",
        "ug",
        "uk",
        "us",
        "uy",
        "uz",
        "va",
        "vc",
        "ve",
        "vg",
        "vi",
        "vn",
        "vu",
        "wf",
        "ws",
        "ye",
        "yt",
        "za",
        "zm",
        "zw",
    )
)

# Regex to recognise domain names
MIN_DOMAIN_LENGTH = 4  # E.g. "t.co"
DOMAIN_REGEX = re.compile(
    r"({0})({1}*)$".format(
        r"|".join([r"\w\." + d for d in map(re.escape, TOP_LEVEL_DOMAINS)]),
        PUNCTUATION_REGEX,
    ),
    re.UNICODE,
)
