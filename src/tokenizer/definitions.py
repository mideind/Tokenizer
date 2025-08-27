"""

Definitions used for tokenization of Icelandic text

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

"""

from typing import (
    Mapping,
    Union,
    Callable,
    Sequence,
    Optional,
    NamedTuple,
    Tuple,
    List,
    cast,
)

import re


BeginTuple = Tuple[int, Optional[int]]
PunctuationTuple = Tuple[int, str]
NumberTuple = Tuple[float, Optional[List[str]], Optional[List[str]]]
DateTimeTuple = Tuple[int, int, int]
MeasurementTuple = Tuple[str, float]
TimeStampTuple = Tuple[int, int, int, int, int, int]
AmountTuple = Tuple[float, str, Optional[List[str]], Optional[List[str]]]
TelnoTuple = Tuple[str, str]
CurrencyTuple = Tuple[str, Optional[List[str]], Optional[List[str]]]


class BIN_Tuple(NamedTuple):
    stofn: str
    utg: int
    ordfl: str
    fl: str
    ordmynd: str
    beyging: str


BIN_TupleList = Sequence[BIN_Tuple]


class PersonNameTuple(NamedTuple):
    name: str
    gender: Optional[str]
    case: Optional[str]


PersonNameList = Sequence[PersonNameTuple]

# All possible contents of the Tok.val attribute
ValType = Union[
    None,
    int,  # YEAR, ORDINAL
    str,  # USERNAME
    BeginTuple,  # S_BEGIN
    PunctuationTuple,  # PUNCTUATION, NUMWLETTER
    MeasurementTuple,  # MEASUREMENT
    TelnoTuple,  # TELNO
    DateTimeTuple,  # DATE, TIME
    TimeStampTuple,  # TIMESTAMP
    NumberTuple,  # PERCENT, NUMBER
    AmountTuple,  # AMOUNT
    CurrencyTuple,  # CURRENCY
    BIN_TupleList,  # WORD
    PersonNameList,  # PERSON
]

# This seems to be needed as a workaround for Pylance/Pyright
_escape = cast(Callable[[str], str], re.escape)

ACCENT = chr(769)
UMLAUT = chr(776)
SOFT_HYPHEN = chr(173)
ZEROWIDTH_SPACE = chr(8203)
ZEROWIDTH_NBSP = chr(65279)

# Preprocessing of unicode characters before tokenization
# Composite glyph replacements - only combining accents and umlauts
COMPOSITE_REPLACEMENTS: Mapping[str, str] = {
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
}

# Zero-width characters that should always be removed
ZEROWIDTH_CHARACTERS: Mapping[str, str] = {
    SOFT_HYPHEN: "",
    ZEROWIDTH_SPACE: "",
    ZEROWIDTH_NBSP: "",
}

# Combined dictionary for backward compatibility
UNICODE_REPLACEMENTS: Mapping[str, str] = {**COMPOSITE_REPLACEMENTS, **ZEROWIDTH_CHARACTERS}

# Regex for composite glyphs only
COMPOSITE_REGEX = re.compile(
    r"|".join(map(_escape, COMPOSITE_REPLACEMENTS.keys())), re.UNICODE
)

# Regex for zero-width characters only
ZEROWIDTH_REGEX = re.compile(
    r"|".join(map(_escape, ZEROWIDTH_CHARACTERS.keys())), re.UNICODE
)

# Combined regex for backward compatibility
UNICODE_REGEX = re.compile(
    r"|".join(map(_escape, UNICODE_REPLACEMENTS.keys())), re.UNICODE
)

# Used for the first step of token splitting
ROUGH_TOKEN_REGEX = re.compile(r"(\s*)([^\s]*)", re.UNICODE)
# Constants for readability when using the ROUGH_TOKEN_REGEX
ROUGH_TOKEN_REGEX_ENTIRE_MATCH = 0
ROUGH_TOKEN_REGEX_WHITE_SPACE_GROUP = 1
ROUGH_TOKEN_REGEX_TOKEN_GROUP = 2

# Hyphens are normalized to '-'
HYPHEN = "-"  # Normal hyphen
EN_DASH = "\u2013"  # "–"
EM_DASH = "\u2014"  # "—"

HYPHENS = HYPHEN + EN_DASH + EM_DASH

# Hyphens that may indicate composite words ('fjármála- og efnahagsráðuneyti')
COMPOSITE_HYPHENS = HYPHEN + EN_DASH
COMPOSITE_HYPHEN = EN_DASH

# Recognized punctuation
LEFT_PUNCTUATION = "([„‚«#$€£¥₽<"
RIGHT_PUNCTUATION = ".,:;)]!%‰?“»”’‛‘…>°"
CENTER_PUNCTUATION = '"*•&+=@©|'
NONE_PUNCTUATION = "^/±'´~\\" + HYPHEN + EN_DASH + EM_DASH
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
END_OF_SENTENCE = frozenset([".", "?", "!", "…"])  # Removed […]
# Punctuation symbols that may additionally occur at the end of a sentence
SENTENCE_FINISHERS = frozenset([")", "]", "“", "»", "”", "’", '"', "[…]"])
# Punctuation symbols that may occur inside words
# Note that an EM_DASH is not allowed inside a word and will split words if present
PUNCT_INSIDE_WORD = frozenset([".", "'", "‘", "´", "’", HYPHEN, EN_DASH])
# Punctuation symbols that can end words
PUNCT_ENDING_WORD = frozenset(["'", "²", "³"])
# Punctuation symbols that may occur together
PUNCT_COMBINATIONS = frozenset(["?", "!", "…"])
# Punctuation in end of indirect speech that doesn't necessarily end sentences
PUNCT_INDIRECT_SPEECH = frozenset(["?", "!"])


# Single and double quotes
SQUOTES = "'‚‛‘´"
DQUOTES = '"“„”«»'

CLOCK_ABBREVS = frozenset(("kl", "kl.", "klukkan"))

# Allowed first digits in Icelandic telephone numbers
TELNO_PREFIXES = "45678"

# Known telephone country codes
COUNTRY_CODES = frozenset(
    (
        "354",
        "+354",
        "00354",
    )
)

# Words that can precede a year number; will be assimilated into the year token
YEAR_WORD = frozenset(("árið", "ársins", "árinu"))

# Characters that can start a numeric token
DIGITS_PREFIX = frozenset([d for d in "0123456789"])
SIGN_PREFIX = frozenset(("+", "-"))

# Month names and numbers
MONTHS: Mapping[str, int] = {
    "janúar": 1,
    "janúars": 1,
    "febrúar": 2,
    "febrúars": 2,
    "mars": 3,
    "apríl": 4,
    "apríls": 4,
    "maí": 5,
    "maís": 5,
    "júní": 6,
    "júnís": 6,
    "júlí": 7,
    "júlís": 7,
    "ágúst": 8,
    "ágústs": 8,
    "september": 9,
    "septembers": 9,
    "október": 10,
    "októbers": 10,
    "nóvember": 11,
    "nóvembers": 11,
    "desember": 12,
    "desembers": 12,
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

# Word forms that are not unambiguous as month names
AMBIGUOUS_MONTH_NAMES = frozenset(
    ("jan", "Jan", "mar", "Mar", "júl", "Júl", "des", "Des", "Ágúst")
)

# Max number of days in each month, indexed so that 1=January
DAYS_IN_MONTH = (0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

# Days of the month spelled out
# DAYS_OF_MONTH = {
#     "fyrsti": 1,
#     "fyrsta": 1,
#     "annar": 2,
#     "annan": 2,
#     "þriðji": 3,
#     "þriðja": 3,
#     "fjórði": 4,
#     "fjórða": 4,
#     "fimmti": 5,
#     "fimmta": 5,
#     "sjötti": 6,
#     "sjötta": 6,
#     "sjöundi": 7,
#     "sjöunda": 7,
#     "áttundi": 8,
#     "áttunda": 8,
#     "níundi": 9,
#     "níunda": 9,
#     "tíundi": 10,
#     "tíunda": 10,
#     "ellefti": 11,
#     "ellefta": 11,
#     "tólfti": 12,
#     "tólfta": 12,
#     "þrettándi": 13,
#     "þrettánda": 13,
#     "fjórtándi": 14,
#     "fjórtánda": 14,
#     "fimmtándi": 15,
#     "fimmtánda": 15,
#     "sextándi": 16,
#     "sextánda": 16,
#     "sautjándi": 17,
#     "sautjánda": 17,
#     "átjándi": 18,
#     "átjánda": 18,
#     "nítjándi": 19,
#     "nítjánda": 19,
#     "tuttugasti": 20,
#     "tuttugasta": 20,
#     "þrítugasti": 30,
#     "þrítugasta": 30,
# }

# Time of day expressions spelled out
CLOCK_NUMBERS: Mapping[str, tuple[int, int, int]] = {
    "eitt": (1, 0, 0),
    "tvö": (2, 0, 0),
    "þrjú": (3, 0, 0),
    "fjögur": (4, 0, 0),
    "fimm": (5, 0, 0),
    "sex": (6, 0, 0),
    "sjö": (7, 0, 0),
    "átta": (8, 0, 0),
    "níu": (9, 0, 0),
    "tíu": (10, 0, 0),
    "ellefu": (11, 0, 0),
    "tólf": (12, 0, 0),
    "hálfeitt": (12, 30, 0),
    "hálftvö": (1, 30, 0),
    "hálfþrjú": (2, 30, 0),
    "hálffjögur": (3, 30, 0),
    "hálffimm": (4, 30, 0),
    "hálfsex": (5, 30, 0),
    "hálfsjö": (6, 30, 0),
    "hálfátta": (7, 30, 0),
    "hálfníu": (8, 30, 0),
    "hálftíu": (9, 30, 0),
    "hálfellefu": (10, 30, 0),
    "hálftólf": (11, 30, 0),
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
CURRENCY_SYMBOLS: Mapping[str, str] = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",  # Also used for China's renminbi (yuan)
    "₽": "RUB",  # Russian ruble
}

# Single-character vulgar fractions in Unicode
SINGLECHAR_FRACTIONS = "↉⅒⅑⅛⅐⅙⅕¼⅓½⅖⅔⅜⅗¾⅘⅝⅚⅞"

# Derived unit : (base SI unit, conversion factor/function)
SI_UNITS: Mapping[str, tuple[str, Union[float, Callable[[float], float]]]] = {
    # Distance
    "m": ("m", 1.0),
    "mm": ("m", 1.0e-3),
    "μm": ("m", 1.0e-6),
    "cm": ("m", 1.0e-2),
    "sm": ("m", 1.0e-2),
    "km": ("m", 1.0e3),
    "ft": ("m", 0.3048),  # feet
    "mi": ("m", 1609.34),  # miles
    # Area
    "m²": ("m²", 1.0),
    "fm": ("m²", 1.0),
    "km²": ("m²", 1.0e6),
    "cm²": ("m²", 1.0e-2),
    "ha": ("m²", 1.0e4),
    # Volume
    "m³": ("m³", 1.0),
    "cm³": ("m³", 1.0e-6),
    "km³": ("m³", 1.0e9),
    "l": ("m³", 1.0e-3),
    "ltr": ("m³", 1.0e-3),
    "dl": ("m³", 1.0e-4),
    "cl": ("m³", 1.0e-5),
    "ml": ("m³", 1.0e-6),
    "gal": ("m³", 3.78541e-3),
    "bbl": ("m³", 158.987294928e-3),
    # Temperature
    "K": ("K", 1.0),
    "°K": ("K", 1.0),  # Strictly speaking this should be K, not °K
    "°C": ("K", lambda x: x + 273.15),
    "°F": ("K", lambda x: (x + 459.67) * 5 / 9),
    # Mass
    "g": ("kg", 1.0e-3),
    "gr": ("kg", 1.0e-3),
    "kg": ("kg", 1.0),
    "t": ("kg", 1.0e3),
    "mg": ("kg", 1.0e-6),
    "μg": ("kg", 1.0e-9),
    "tn": ("kg", 1.0e3),
    "lb": ("kg", 0.453592),
    # Duration
    "s": ("s", 1.0),
    "ms": ("s", 1.0e-3),
    "μs": ("s", 1.0e-6),
    "klst": ("s", 3600.0),
    "mín": ("s", 60.0),
    # Force
    "N": ("N", 1.0),
    "kN": ("N", 1.0e3),
    # Energy
    "Nm": ("J", 1.0),
    "J": ("J", 1.0),
    "kJ": ("J", 1.0e3),
    "MJ": ("J", 1.0e6),
    "GJ": ("J", 1.0e9),
    "TJ": ("J", 1.0e12),
    "kWh": ("J", 3.6e6),
    "MWh": ("J", 3.6e9),
    "kWst": ("J", 3.6e6),
    "MWst": ("J", 3.6e9),
    "kcal": ("J", 4184.0),
    "cal": ("J", 4.184),
    # Power
    "W": ("W", 1.0),
    "mW": ("W", 1.0e-3),
    "kW": ("W", 1.0e3),
    "MW": ("W", 1.0e6),
    "GW": ("W", 1.0e9),
    "TW": ("W", 1.0e12),
    # Electric potential
    "V": ("V", 1.0),
    "mV": ("V", 1.0e-3),
    "kV": ("V", 1.0e3),
    # Electric current
    "A": ("A", 1.0),
    "mA": ("A", 1.0e-3),
    # Frequency
    "Hz": ("Hz", 1.0),
    "kHz": ("Hz", 1.0e3),
    "MHz": ("Hz", 1.0e6),
    "GHz": ("Hz", 1.0e9),
    # Pressure
    "Pa": ("Pa", 1.0),
    "hPa": ("Pa", 1.0e2),
    # Angle
    "°": ("°", 1.0),  # Degree
    # Percentage and promille
    "%": ("%", 1.0),
    "‰": ("‰", 0.1),
    # Velocity
    "m/s": ("m/s", 1.0),
    "km/klst": ("m/s", 1000.0 / (60 * 60)),
    # "km/klst.": ("m/s", 1000.0/(60*60)),
}

DIRECTIONS: Mapping[str, str] = {
    "N": "Norður",
}

_unit_lambda: Callable[[str], str] = lambda unit: (
    unit + r"(?!\w)" if unit[-1].isalpha() else unit
)

SI_UNITS_SET: frozenset[str] = frozenset(SI_UNITS.keys())
SI_UNITS_REGEX_STRING = r"|".join(
    map(
        # If the unit ends with a letter, don't allow the next character
        # after it to be a letter (i.e. don't match '220Volts' as '220V')
        _unit_lambda,
        # Sort in descending order by length, so that longer strings
        # are matched before shorter ones
        sorted(SI_UNITS.keys(), key=len, reverse=True),
    )
)
SI_UNITS_REGEX = re.compile(r"({0})".format(SI_UNITS_REGEX_STRING), re.UNICODE)

CURRENCY_REGEX_STRING = r"|".join(
    map(
        # Sort in descending order by length, so that longer strings
        # are matched before shorter ones
        _escape,
        sorted(CURRENCY_SYMBOLS.keys(), key=lambda s: len(s), reverse=True),
    )
)

# Combined pattern regex for SI units, percentage, promille and currency symbols
UNIT_REGEX_STRING = SI_UNITS_REGEX_STRING + r"|" + CURRENCY_REGEX_STRING

# Icelandic-style number, followed by a unit
NUM_WITH_UNIT_REGEX1 = re.compile(
    r"([-+]?\d+(\.\d\d\d)*(,\d+)?)({0})".format(UNIT_REGEX_STRING), re.UNICODE
)

# English-style number, followed by a unit
NUM_WITH_UNIT_REGEX2 = re.compile(
    r"([-+]?\d+(,\d\d\d)*(\.\d+)?)({0})".format(UNIT_REGEX_STRING), re.UNICODE
)

# One or more digits, followed by a unicode vulgar fraction char (e.g. '2½')
# and a unit (SI, percent or currency symbol)
NUM_WITH_UNIT_REGEX3 = re.compile(
    r"(\d+)([\u00BC-\u00BE\u2150-\u215E])({0})".format(UNIT_REGEX_STRING), re.UNICODE
)


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
ORDINAL_ERRORS: Mapping[str, str] = {
    "1sti": "fyrsti",
    "1sta": "fyrsta",
    "1stu": "fyrstu",
    "3ji": "þriðji",
    # "3ja": "þriðja",  # þriggja
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
    "3ja": "þriggja",
    "4ra": "fjögurra",
}

# Translations of kludgy ordinal words into numbers
ORDINAL_NUMBERS: Mapping[str, int] = {
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
    "5tu": 5,
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


def roman_to_int(s: str) -> int:
    """Quick and dirty conversion of an already validated Roman numeral to integer"""
    # Adapted from http://code.activestate.com/recipes/81611-roman-numerals/
    i = result = 0
    for integer, numeral in ROMAN_NUMERAL_MAP:
        while s[i : i + len(numeral)] == numeral:
            result += integer
            i += len(numeral)
    assert i == len(s)
    return result


NUMBER_ABBREV: Mapping[str, int] = {
    "þús.": 1000,
    "millj.": 10**6,
    "mljó.": 10**6,
    "ma.": 10**9,
    "mrð.": 10**9,
    "billj.": 10**12,
    "bljó.": 10**12,
    "trillj.": 10**18,
}

# Recognize words for percentages
PERCENTAGES: Mapping[str, int] = {
    "prósent": 1,
    "prósenta": 1,
    "prósenti": 1,
    "prósents": 1,
    "prósentur": 1,
    "prósentum": 1,
    "hundraðshluti": 1,
    "hundraðshluta": 1,
    "hundraðshlutar": 1,
    "hundraðshlutum": 1,
    "prósentustig": 1,
    "prósentustigi": 1,
    "prósentustigs": 1,
    "prósentustigum": 1,
    "prósentustiga": 1,
}

# Amount abbreviations including 'kr' for the ISK
# Corresponding abbreviations are found in Abbrev.conf
AMOUNT_ABBREV: Mapping[str, Union[int, float]] = {
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
    # "mrð.kr.": 1e9,
    # "mrð.kr": 1e9,
    # "billj.kr.": 1e12,
    # "billj.kr": 1e12,
    # "trillj.kr.": 1e18,
    # "trillj.kr": 1e18,
}

# Króna amount strings allowed before a number, e.g. "kr. 9.900"
ISK_AMOUNT_PRECEDING = frozenset(("kr.", "kr", "krónur"))

# URI scheme prefixes
URI_PREFIXES = (
    "http://",
    "https://",
    "file://",
    "ftp://",
    "ssh://",
    "sftp://",
    "smb://",
    "git://",
    "git+ssh://",
    "svn://",
    "svn+ssh://",
    "imap://",
    "rtmp://",
    "rtsp://",
    "telnet://",
    "udp://",
    "vnc://",
    "irc://",
    "nntp://",
    "wss://",
    "ws://",
    "xmpp://",
    "mtqp://",
    "afp://",
    "nfs://",
    "mms://",
    "tftp://",
    "ldap://",
)

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
        "art",
        "events",
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
        # "kr", # Clashes with "kr" abbreviation (e.g. "þús.kr" is a legitimate domain name)
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
        r"|".join(r"\w\." + d for d in map(_escape, TOP_LEVEL_DOMAINS)),
        PUNCTUATION_REGEX,
    ),
    re.UNICODE,
)

# A list of the symbols of the natural elements.
# Note that single-letter symbols should follow two-letter symbols,
# so that regexes do not match the single-letter ones greedily before
# the two-letter ones.
ELEMENTS = (
    "Ac",
    "Ag",
    "Al",
    "Am",
    "Ar",
    "As",
    "At",
    "Au",
    "Ba",
    "Be",
    "Bh",
    "Bi",
    "Bk",
    "Br",
    "B",
    "Ca",
    "Cd",
    "Ce",
    "Cf",
    "Cl",
    "Cm",
    "Cn",
    "Co",
    "Cr",
    "Cs",
    "Cu",
    "C",
    "Db",
    "Ds",
    "Dy",
    "Er",
    "Es",
    "Eu",
    "Fe",
    "Fl",
    "Fm",
    "Fr",
    "F",
    "Ga",
    "Gd",
    "Ge",
    "He",
    "Hf",
    "Hg",
    "Ho",
    "Hs",
    "H",
    "In",
    "Ir",
    "I",
    "Kr",
    "K",
    "La",
    "Li",
    "Lr",
    "Lu",
    "Lv",
    "Mc",
    "Md",
    "Mg",
    "Mn",
    "Mo",
    "Mt",
    "Na",
    "Nb",
    "Nd",
    "Ne",
    "Nh",
    "Ni",
    "No",
    "Np",
    "N",
    "Og",
    "Os",
    "O",
    "Pa",
    "Pb",
    "Pd",
    "Pm",
    "Po",
    "Pr",
    "Pt",
    "Pu",
    "P",
    "Ra",
    "Rb",
    "Re",
    "Rf",
    "Rg",
    "Rh",
    "Rn",
    "Ru",
    "Sb",
    "Sc",
    "Se",
    "Sg",
    "Si",
    "Sm",
    "Sn",
    "Sr",
    "S",
    "Ta",
    "Tb",
    "Tc",
    "Te",
    "Th",
    "Ti",
    "Tl",
    "Tm",
    "Ts",
    "U",
    "V",
    "W",
    "Xe",
    "Yb",
    "Y",
    "Zn",
    "Zr",
)

# Regex to recognize molecules ('H2SO4')
# Note that we place a further constraint on the token so that
# it must contain at least one digit to qualify as a molecular formula
ELEMENTS_REGEX = r"|".join(ELEMENTS)
MOLECULE_REGEX = re.compile(r"^(({0})+\d*)+".format(ELEMENTS_REGEX))
MOLECULE_FILTER = re.compile(r"\d")


# Validation of Icelandic social security numbers
KT_MAGIC = [3, 2, 7, 6, 5, 4, 0, 3, 2]


def valid_ssn(kt: str) -> bool:
    """Validate Icelandic social security number ("kennitala")"""
    if not kt or len(kt) != 11 or kt[6] != "-":
        return False
    m = 11 - sum((ord(kt[i]) - 48) * KT_MAGIC[i] for i in range(9)) % 11
    c = ord(kt[9]) - 48
    return m == 11 if c == 0 else m == c


# HTML escaped characters/ligatures, e.g. '&aacute;' meaning 'á'.
# The following is a subset of HTML escape codes, roughly selected
# by analyzing the content of the Icelandic Gigaword Corpus (Risamálheild).
HTML_ESCAPES: Mapping[str, str] = {
    # Icelandic letters
    "aacute": "á",
    "eth": "ð",
    "eacute": "é",
    "iacute": "í",
    "oacute": "ó",
    "uacute": "ú",
    "yacute": "ý",
    "thorn": "þ",
    "aelig": "æ",
    "ouml": "ö",
    "Aacute": "Á",
    "ETH": "Ð",
    "Eacute": "É",
    "Iacute": "Í",
    "Oacute": "Ó",
    "Uacute": "Ú",
    "Yacute": "Ý",
    "THORN": "Þ",
    "AElig": "Æ",
    "Ouml": "Ö",
    # Punctuation
    "amp": "&",
    "lt": "<",
    "gt": ">",
    "quot": '"',
    "apos": "'",
    "bdquo": "„",
    "ldquo": "“",
    "rdquo": "”",
    "lsquo": "‘",
    "acute": "´",
    "lcub": "{",
    "rcub": "}",
    "darr": "↓",
    "uarr": "↑",
    "ring": "˚",
    "deg": "°",
    "diam": "⋄",
    "ordm": "º",
    "ogon": "˛",
    "hellip": "…",
    "copy": "©",
    "reg": "®",
    "trade": "™",
    # Spaces - all spaces are mapped to \x20
    "nbsp": " ",
    "ensp": " ",
    "emsp": " ",
    "thinsp": " ",
    # Dashes and hyphens
    "ndash": "–",
    "mdash": "—",
    # The soft hyphen &shy; is mapped to an empty string
    "shy": "",
    # Other non-ASCII letters
    "uuml": "ü",
    "Uuml": "Ü",
    "zcaron": "ž",
    "Zcaron": "Ž",
    "lstrok": "ł",
    "Lstrok": "Ł",
    "ntilde": "ñ",
    "inodot": "ı",
    # Ligatures
    "filig": "fi",
    "fllig": "fl",
}

ESCAPES_REGEX = r"|".join(HTML_ESCAPES.keys())
HTML_ESCAPE_REGEX = re.compile(
    r"&((#x[0-9a-fA-F]{r1})|(#\d{r2})|({ex}))\;".format(
        r1="{1,8}", r2="{1,10}", ex=ESCAPES_REGEX
    )
)
