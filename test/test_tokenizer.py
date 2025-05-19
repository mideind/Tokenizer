# type: ignore
"""

    test_tokenizer.py

    Tests for Tokenizer module

    Copyright (C) 2016-2025 by Miðeind ehf.
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

from typing import Any, Iterable, Iterator, Union, cast

import tokenizer as t
from tokenizer.definitions import BIN_Tuple, ValType

TOK = t.TOK
Tok = t.Tok

TestCase = Union[tuple[str, int], tuple[str, int, ValType], tuple[str, list[Tok]]]


def strip_originals(tokens: list[Tok]) -> list[Tok]:
    """Remove origin tracking info from a list of tokens.
    This is useful for simplifying tests where we don't care about tracking
    origins.
    TODO: This could be removed if we get a feature to disable origin
    tracking during tokenization.
    """

    for tk in tokens:
        tk.original = None
        tk.origin_spans = None

    return tokens


def get_text_and_norm(orig: str) -> tuple[str, str]:
    toklist = list(t.tokenize(orig))
    return t.text_from_tokens(toklist), t.normalized_text_from_tokens(toklist)


def test_single_tokens() -> None:
    TEST_CASES = [
        (".", TOK.PUNCTUATION),
        (",", TOK.PUNCTUATION),
        ("!", TOK.PUNCTUATION),
        ('"', [Tok(TOK.PUNCTUATION, "“", None)]),
        ("13:45", [Tok(TOK.TIME, "13:45", (13, 45, 0))]),
        (
            "13:450",
            [
                Tok(TOK.NUMBER, "13", (13, None, None)),
                Tok(TOK.PUNCTUATION, ":", None),
                Tok(TOK.NUMBER, "450", (450, None, None)),
            ],
        ),
        ("kl. 13:45", [Tok(TOK.TIME, "kl. 13:45", (13, 45, 0))]),
        ("klukkan 13:45", [Tok(TOK.TIME, "klukkan 13:45", (13, 45, 0))]),
        ("Klukkan 13:45", [Tok(TOK.TIME, "Klukkan 13:45", (13, 45, 0))]),
        ("hálftólf", [Tok(TOK.TIME, "hálftólf", (11, 30, 0))]),
        ("kl. hálfátta", [Tok(TOK.TIME, "kl. hálfátta", (7, 30, 0))]),
        ("kl. hálf átta", [Tok(TOK.TIME, "kl. hálf átta", (7, 30, 0))]),
        ("klukkan hálfátta", [Tok(TOK.TIME, "klukkan hálfátta", (7, 30, 0))]),
        ("klukkan hálf átta", [Tok(TOK.TIME, "klukkan hálf átta", (7, 30, 0))]),
        ("klukkan þrjú", [Tok(TOK.TIME, "klukkan þrjú", (3, 00, 0))]),
        ("Kl. hálfátta", [Tok(TOK.TIME, "Kl. hálfátta", (7, 30, 0))]),
        ("Kl. hálf átta", [Tok(TOK.TIME, "Kl. hálf átta", (7, 30, 0))]),
        ("Klukkan hálfátta", [Tok(TOK.TIME, "Klukkan hálfátta", (7, 30, 0))]),
        ("Klukkan hálf átta", [Tok(TOK.TIME, "Klukkan hálf átta", (7, 30, 0))]),
        ("Klukkan þrjú", [Tok(TOK.TIME, "Klukkan þrjú", (3, 00, 0))]),
        ("17/6", [Tok(TOK.DATEREL, "17/6", (0, 6, 17))]),
        (
            "17.6.",
            [
                Tok(TOK.NUMBER, "17.6", (17.6, None, None)),
                Tok(TOK.PUNCTUATION, ".", None),
            ],
        ),
        (
            "17.16.",
            [
                Tok(TOK.NUMBER, "17.16", (17.16, None, None)),
                Tok(TOK.PUNCTUATION, ".", None),
            ],
        ),
        (
            "30.9.",
            [
                Tok(TOK.NUMBER, "30.9", (30.9, None, None)),
                Tok(TOK.PUNCTUATION, ".", None),
            ],
        ),
        (
            "31.9.",
            [
                Tok(TOK.NUMBER, "31.9", (31.9, None, None)),
                Tok(TOK.PUNCTUATION, ".", None),
            ],
        ),
        (
            "17/60",
            [
                Tok(TOK.NUMBER, "17", (17, None, None)),
                Tok(TOK.PUNCTUATION, "/", None),
                Tok(TOK.NUMBER, "60", (60, None, None)),
            ],
        ),
        ("3. maí", [Tok(TOK.DATEREL, "3. maí", (0, 5, 3))]),
        ("Ágúst", TOK.WORD),  # Not month name if capitalized
        ("13. ágúst", [Tok(TOK.DATEREL, "13. ágúst", (0, 8, 13))]),
        ("nóvember 1918", [Tok(TOK.DATEREL, "nóvember 1918", (1918, 11, 0))]),
        (
            "nóvember 19180",
            [
                Tok(TOK.DATEREL, "nóvember", (0, 11, 0)),
                Tok(TOK.NUMBER, "19180", (19180, None, None)),
            ],
        ),
        (
            "sautjánda júní",
            [
                Tok(TOK.WORD, "sautjánda", None),
                Tok(TOK.DATEREL, "júní", (0, 6, 0)),
            ],
        ),
        (
            "sautjánda júní 1811",
            [
                Tok(TOK.WORD, "sautjánda", None),
                Tok(TOK.DATEREL, "júní 1811", (1811, 6, 0)),
            ],
        ),
        (
            "Sautjánda júní árið 1811",
            [
                Tok(TOK.WORD, "Sautjánda", None),
                Tok(TOK.DATEREL, "júní árið 1811", (1811, 6, 0)),
            ],
        ),
        (
            "Fimmtánda mars árið 44 f.Kr.",
            [
                Tok(TOK.WORD, "Fimmtánda", None),
                Tok(TOK.DATEREL, "mars árið 44 f.Kr.", (-44, 3, 0)),
            ],
        ),
        ("17/6/2013", [Tok(TOK.DATEABS, "17/6/2013", (2013, 6, 17))]),
        (
            "17/6/20130",
            [
                Tok(TOK.DATEREL, "17/6", (0, 6, 17)),
                Tok(TOK.PUNCTUATION, "/", None),
                Tok(TOK.NUMBER, "20130", (20130, None, None)),
            ],
        ),
        ("2013-06-17", [Tok(TOK.DATEABS, "2013-06-17", (2013, 6, 17))]),
        ("2013/06/17", [Tok(TOK.DATEABS, "2013/06/17", (2013, 6, 17))]),
        (
            "2013-06-170",
            [
                Tok(TOK.YEAR, "2013", 2013),
                Tok(TOK.PUNCTUATION, "-", None),
                Tok(TOK.NUMBER, "06", (6, None, None)),
                Tok(TOK.PUNCTUATION, "-", None),
                Tok(TOK.NUMBER, "170", (170, None, None)),
            ],
        ),
        ("2013", [Tok(TOK.YEAR, "2013", 2013)]),
        ("20130", [Tok(TOK.NUMBER, "20130", (20130, None, None))]),
        ("874 e.Kr.", [Tok(TOK.YEAR, "874 e.Kr.", 874)]),
        ("2013 f.Kr.", [Tok(TOK.YEAR, "2013 f.Kr.", -2013)]),
        ("árið 2013", [Tok(TOK.YEAR, "árið 2013", 2013)]),
        ("árinu 874", [Tok(TOK.YEAR, "árinu 874", 874)]),
        ("ársins 2013", [Tok(TOK.YEAR, "ársins 2013", 2013)]),
        ("ársins 320 f.Kr.", [Tok(TOK.YEAR, "ársins 320 f.Kr.", -320)]),
        ("213", [Tok(TOK.NUMBER, "213", (213, None, None))]),
        ("2.013", [Tok(TOK.NUMBER, "2.013", (2013, None, None))]),
        ("2,013", [Tok(TOK.NUMBER, "2,013", (2.013, None, None))]),
        ("2.013,45", [Tok(TOK.NUMBER, "2.013,45", (2013.45, None, None))]),
        (
            "2.0134,45",
            [
                Tok(TOK.NUMBER, "2.0134", (2.0134, None, None)),
                Tok(TOK.PUNCTUATION, ",", None),
                Tok(TOK.NUMBER, "45", (45, None, None)),
            ],
        ),
        ("2,013.45", [Tok(TOK.NUMBER, "2,013.45", (2013.45, None, None))]),
        (
            "2,0134.45",
            [
                Tok(TOK.NUMBER, "2", (2, None, None)),
                Tok(TOK.PUNCTUATION, ",", None),
                Tok(TOK.NUMBER, "0134.45", (134.45, None, None)),
            ],
        ),
        ("1/2", [Tok(TOK.NUMBER, "1/2", (0.5, None, None))]),
        ("1/20", [Tok(TOK.DATEREL, "1/20", (0, 1, 20))]),
        (
            "1/37",
            [
                Tok(TOK.NUMBER, "1", (1, None, None)),
                Tok(TOK.PUNCTUATION, "/", None),
                Tok(TOK.NUMBER, "37", (37, None, None)),
            ],
        ),
        ("1/4", [Tok(TOK.NUMBER, "1/4", (0.25, None, None))]),
        ("¼", [Tok(TOK.NUMBER, "¼", (0.25, None, None))]),
        ("2⅞", [Tok(TOK.NUMBER, "2⅞", (2.875, None, None))]),
        ("33⅗", [Tok(TOK.NUMBER, "33⅗", (33.6, None, None))]),
        ("1sti", [Tok(TOK.WORD, "1sti", None)]),
        ("4ðu", [Tok(TOK.WORD, "4ðu", None)]),
        ("2svar", [Tok(TOK.WORD, "2svar", None)]),
        ("4ra", [Tok(TOK.WORD, "4ra", None)]),
        ("2ja", [Tok(TOK.WORD, "2ja", None)]),
        ("þjóðhátíð", TOK.WORD),
        ("Þjóðhátíð", TOK.WORD),
        ("marg-ítrekað", TOK.WORD),
        ("full-ítarlegur", TOK.WORD),
        ("hálf-óviðbúinn", TOK.WORD),
        ("750 þús.kr.", [Tok(TOK.AMOUNT, "750 þús.kr.", (750e3, "ISK", None, None))]),
        ("750 þús.kr", [Tok(TOK.AMOUNT, "750 þús.kr", (750e3, "ISK", None, None))]),
        ("10 m.kr", [Tok(TOK.AMOUNT, "10 m.kr", (1e7, "ISK", None, None))]),
        (
            "m.kr.",
            [
                Tok(
                    TOK.WORD,
                    "m.kr.",
                    [BIN_Tuple("milljónir króna", 0, "kvk", "skst", "m.kr.", "-")],
                ),
            ],
        ),
        (
            "ma.kr.",
            [
                Tok(
                    TOK.WORD,
                    "ma.kr.",
                    [BIN_Tuple("milljarðar króna", 0, "kk", "skst", "ma.kr.", "-")],
                ),
            ],
        ),
        (
            "30,7 mö.kr.",
            [Tok(TOK.AMOUNT, "30,7 mö.kr.", (30.7e9, "ISK", None, None))],
        ),
        ("sjötíu", [Tok(TOK.WORD, "sjötíu", None)]),
        ("hundrað", [Tok(TOK.WORD, "hundrað", None)]),
        ("hundruð", [Tok(TOK.WORD, "hundruð", None)]),
        ("þúsund", [Tok(TOK.WORD, "þúsund", None)]),
        ("milljón", [Tok(TOK.WORD, "milljón", None)]),
        ("milljarður", [Tok(TOK.WORD, "milljarður", None)]),
        ("billjón", [Tok(TOK.WORD, "billjón", None)]),
        (
            "kvintilljón",
            [Tok(TOK.WORD, "kvintilljón", None)],
        ),
        (
            "t.d.",
            [
                Tok(
                    TOK.WORD,
                    "t.d.",
                    [BIN_Tuple("til dæmis", 0, "ao", "frasi", "t.d.", "-")],
                )
            ],
        ),
        ("hr.", TOK.WORD, [BIN_Tuple("herra", 0, "kk", "skst", "hr.", "-")]),
        (
            "dags. 10/7",
            [
                Tok(
                    TOK.WORD,
                    "dags.",
                    [
                        BIN_Tuple("dagsetja", 0, "so", "skst", "dags.", "-"),
                        BIN_Tuple("dagsettur", 0, "lo", "skst", "dags.", "-"),
                    ],
                ),
                Tok(TOK.DATEREL, "10/7", (0, 7, 10)),
            ],
        ),
        ("Hr.", TOK.WORD, [BIN_Tuple("herra", 0, "kk", "skst", "hr.", "-")]),
        (
            "nk.",
            [
                Tok(
                    TOK.WORD,
                    "nk.",
                    [BIN_Tuple("næstkomandi", 0, "lo", "skst", "nk.", "-")],
                ),
            ],
        ),
        (
            "sl.",
            [
                Tok(
                    TOK.WORD,
                    "sl.",
                    [BIN_Tuple("síðastliðinn", 0, "lo", "skst", "sl.", "-")],
                ),
            ],
        ),
        (
            "o.s.frv.",
            [
                Tok(
                    TOK.WORD,
                    "o.s.frv.",
                    [BIN_Tuple("og svo framvegis", 0, "ao", "frasi", "o.s.frv.", "-")],
                ),
            ],
        ),
        ("BSRB", TOK.WORD),
        ("stjórnskipunar- og eftirlitsnefnd", TOK.WORD),
        ("dómsmála-, viðskipta- og iðnaðarráðherra", TOK.WORD),
        ("dómsmála- viðskipta- og iðnaðarráðherra", TOK.WORD),
        ("ferðamála- dómsmála- viðskipta- og iðnaðarráðherra", TOK.WORD),
        ("ferðamála-, dómsmála-, viðskipta- og iðnaðarráðherra", TOK.WORD),
        # Test backoff if composition is not successful
        (
            "ferðamála- ráðherra",
            [
                Tok(TOK.WORD, "ferðamála", None),
                Tok(TOK.PUNCTUATION, "-", None),
                Tok(TOK.WORD, "ráðherra", None),
            ],
        ),
        (
            "ferðamála-, iðnaðar- ráðherra",
            [
                Tok(TOK.WORD, "ferðamála", None),
                Tok(TOK.PUNCTUATION, "-", None),
                Tok(TOK.PUNCTUATION, ",", None),
                Tok(TOK.WORD, "iðnaðar", None),
                Tok(TOK.PUNCTUATION, "-", None),
                Tok(TOK.WORD, "ráðherra", None),
            ],
        ),
        (
            "ferðamála- og 500",
            [
                Tok(TOK.WORD, "ferðamála", None),
                Tok(TOK.PUNCTUATION, "-", None),
                Tok(TOK.WORD, "og", None),
                Tok(TOK.NUMBER, "500", (500, None, None)),
            ],
        ),
        ("591213-1480", TOK.SSN),
        (
            "591214-1480",
            [
                Tok(TOK.NUMBER, "591214", (591214, None, None)),
                Tok(TOK.PUNCTUATION, "-", None),
                Tok(TOK.NUMBER, "1480", (1480, None, None)),
            ],
        ),
        (
            "591213-14803",
            [
                Tok(TOK.NUMBER, "591213", (591213, None, None)),
                Tok(TOK.PUNCTUATION, "-", None),
                Tok(TOK.NUMBER, "14803", (14803, None, None)),
            ],
        ),
        ("9000000", TOK.NUMBER),
        ("1234567", TOK.NUMBER),
        ("1965", TOK.YEAR),
        ("525-4764", [Tok(TOK.TELNO, "525-4764", ("525-4764", "354"))]),
        ("4204200", [Tok(TOK.TELNO, "4204200", ("420-4200", "354"))]),
        ("699 2422", [Tok(TOK.TELNO, "699 2422", ("699-2422", "354"))]),
        ("354 699 2422", [Tok(TOK.TELNO, "354 699 2422", ("699-2422", "354"))]),
        ("+354 699 2422", [Tok(TOK.TELNO, "+354 699 2422", ("699-2422", "+354"))]),
        ("12,3%", TOK.PERCENT),
        ("12,3 %", [Tok(TOK.PERCENT, "12,3 %", (12.3, None, None))]),
        ("http://www.greynir.is", TOK.URL),
        ("https://greynir.is", TOK.URL),
        ("https://pypi.org/project/tokenizer/", TOK.URL),
        ("http://tiny.cc/28695y", TOK.URL),
        ("www.greynir.is", TOK.DOMAIN),
        ("mbl.is", TOK.DOMAIN),
        ("RÚV.is", TOK.DOMAIN),
        ("Eitthvað.org", TOK.DOMAIN),
        ("9gag.com", TOK.DOMAIN),
        ("SannLeikurinn.com", TOK.DOMAIN),
        ("ílénumeruíslenskir.stafir-leyfilegir.net", TOK.DOMAIN),
        ("#MeToo", TOK.HASHTAG),
        ("#12stig12", TOK.HASHTAG),
        ("#égermeðíslenskastafi", TOK.HASHTAG),
        ("#", TOK.PUNCTUATION),
        (
            "19/3/1977 14:56:10",
            [Tok(TOK.TIMESTAMPABS, "19/3/1977 14:56:10", (1977, 3, 19, 14, 56, 10))],
        ),
        (
            "19/3/1977 kl. 14:56:10",
            [
                Tok(
                    TOK.TIMESTAMPABS,
                    "19/3/1977 kl. 14:56:10",
                    (1977, 3, 19, 14, 56, 10),
                )
            ],
        ),
        ("¥212,11", TOK.AMOUNT),
        ("EUR 200", TOK.AMOUNT),
        ("kr. 5.999", TOK.AMOUNT),
        ("$472,64", [Tok(TOK.AMOUNT, "$472,64", (472.64, "USD", None, None))]),
        ("€472,64", [Tok(TOK.AMOUNT, "€472,64", (472.64, "EUR", None, None))]),
        ("£199,99", [Tok(TOK.AMOUNT, "£199,99", (199.99, "GBP", None, None))]),
        ("$472.64", [Tok(TOK.AMOUNT, "$472.64", (472.64, "USD", None, None))]),
        ("€472.64", [Tok(TOK.AMOUNT, "€472.64", (472.64, "EUR", None, None))]),
        ("£199.99", [Tok(TOK.AMOUNT, "£199.99", (199.99, "GBP", None, None))]),
        ("$1,472.64", [Tok(TOK.AMOUNT, "$1,472.64", (1472.64, "USD", None, None))]),
        ("€3,472.64", [Tok(TOK.AMOUNT, "€3,472.64", (3472.64, "EUR", None, None))]),
        ("£5,199.99", [Tok(TOK.AMOUNT, "£5,199.99", (5199.99, "GBP", None, None))]),
        ("$1.472,64", [Tok(TOK.AMOUNT, "$1.472,64", (1472.64, "USD", None, None))]),
        ("€3.472,64", [Tok(TOK.AMOUNT, "€3.472,64", (3472.64, "EUR", None, None))]),
        ("£5.199,99", [Tok(TOK.AMOUNT, "£5.199,99", (5199.99, "GBP", None, None))]),
        ("$1,472", [Tok(TOK.AMOUNT, "$1,472", (1.472, "USD", None, None))]),
        ("€3,472", [Tok(TOK.AMOUNT, "€3,472", (3.472, "EUR", None, None))]),
        ("£5,199", [Tok(TOK.AMOUNT, "£5,199", (5.199, "GBP", None, None))]),
        ("$1.472", [Tok(TOK.AMOUNT, "$1.472", (1472, "USD", None, None))]),
        ("€3.472", [Tok(TOK.AMOUNT, "€3.472", (3472, "EUR", None, None))]),
        ("£5.199", [Tok(TOK.AMOUNT, "£5.199", (5199, "GBP", None, None))]),
        ("$1965", [Tok(TOK.AMOUNT, "$1965", (1965.0, "USD", None, None))]),
        ("€1965", [Tok(TOK.AMOUNT, "€1965", (1965.0, "EUR", None, None))]),
        ("¥1965", [Tok(TOK.AMOUNT, "¥1965", (1965.0, "JPY", None, None))]),
        ("fake@news.is", TOK.EMAIL),
        ("jon.jonsson.99@netfang.is", TOK.EMAIL),
        ("valid@my-domain.reallylongtld", TOK.EMAIL),
        ("7a", [Tok(TOK.NUMWLETTER, "7a", (7, "a"))]),
        ("33B", [Tok(TOK.NUMWLETTER, "33B", (33, "B"))]),
        ("1129c", [Tok(TOK.NUMWLETTER, "1129c", (1129, "c"))]),
        ("1965c", [Tok(TOK.NUMWLETTER, "1965c", (1965, "c"))]),
        ("7l", [Tok(TOK.MEASUREMENT, "7l", ("m³", 0.007))]),
        ("1965l", [Tok(TOK.MEASUREMENT, "1965l", ("m³", 1.965))]),
        ("17 ltr", [Tok(TOK.MEASUREMENT, "17 ltr", ("m³", 17.0e-3))]),
        ("150m", [Tok(TOK.MEASUREMENT, "150m", ("m", 150))]),
        ("1965m", [Tok(TOK.MEASUREMENT, "1965m", ("m", 1965))]),
        ("220V", [Tok(TOK.MEASUREMENT, "220V", ("V", 220))]),
        (
            "220Volt",
            [Tok(TOK.NUMBER, "220", (220, None, None)), Tok(TOK.WORD, "Volt", None)],
        ),
        ("11A", [Tok(TOK.MEASUREMENT, "11A", ("A", 11))]),
        ("100 mm", [Tok(TOK.MEASUREMENT, "100 mm", ("m", 0.1))]),
        ("30,7°C", [Tok(TOK.MEASUREMENT, "30,7°C", ("K", 273.15 + 30.7))]),
        ("30,7 °C", [Tok(TOK.MEASUREMENT, "30,7 °C", ("K", 273.15 + 30.7))]),
        ("30,7° C", [Tok(TOK.MEASUREMENT, "30,7° C", ("K", 273.15 + 30.7))]),
        ("30,7 ° C", [Tok(TOK.MEASUREMENT, "30,7 ° C", ("K", 273.15 + 30.7))]),
        ("32°F", [Tok(TOK.MEASUREMENT, "32°F", ("K", 273.15))]),
        ("32 °F", [Tok(TOK.MEASUREMENT, "32 °F", ("K", 273.15))]),
        ("32° F", [Tok(TOK.MEASUREMENT, "32° F", ("K", 273.15))]),
        ("32 ° F", [Tok(TOK.MEASUREMENT, "32 ° F", ("K", 273.15))]),
        ("1965°C", [Tok(TOK.MEASUREMENT, "1965°C", ("K", 273.15 + 1965.0))]),
        ("1965 °C", [Tok(TOK.MEASUREMENT, "1965 °C", ("K", 273.15 + 1965.0))]),
        ("1965° C", [Tok(TOK.MEASUREMENT, "1965° C", ("K", 273.15 + 1965.0))]),
        ("1965 ° C", [Tok(TOK.MEASUREMENT, "1965 ° C", ("K", 273.15 + 1965.0))]),
        ("180°", [Tok(TOK.MEASUREMENT, "180°", ("°", 180))]),
        ("180 °", [Tok(TOK.MEASUREMENT, "180 °", ("°", 180))]),
        ("6.500 kg", [Tok(TOK.MEASUREMENT, "6.500 kg", ("kg", 6.5e3))]),
        ("690 MW", [Tok(TOK.MEASUREMENT, "690 MW", ("W", 690e6))]),
        ("1800 MWst", [Tok(TOK.MEASUREMENT, "1800 MWst", ("J", 6480e9))]),
        ("1976kWst", [Tok(TOK.MEASUREMENT, "1976kWst", ("J", 7113.6e6))]),
        ("CO2", TOK.MOLECULE),
        ("CO", TOK.WORD),
        ("H2O", TOK.MOLECULE),
        ("B5", TOK.MOLECULE),
        ("H2SO4", TOK.MOLECULE),
        ("350-6678", TOK.SERIALNUMBER),
        ("123-456-7890", TOK.SERIALNUMBER),
        ("1-45-7890", TOK.SERIALNUMBER),
        ("1-800-1234", TOK.SERIALNUMBER),
        ("1-800-1234-545566", TOK.SERIALNUMBER),
    ]

    TEST_CASES_KLUDGY_MODIFY = [
        ("1sti", [Tok(TOK.WORD, "fyrsti", None)]),
        ("4ðu", [Tok(TOK.WORD, "fjórðu", None)]),
        ("2svar", [Tok(TOK.WORD, "tvisvar", None)]),
        ("4ra", [Tok(TOK.WORD, "fjögurra", None)]),
        ("2ja", [Tok(TOK.WORD, "tveggja", None)]),
    ]

    TEST_CASES_KLUDGY_TRANSLATE = [
        ("1sti", [Tok(TOK.ORDINAL, "1sti", 1)]),
        ("4ðu", [Tok(TOK.ORDINAL, "4ðu", 4)]),
        ("2svar", [Tok(TOK.WORD, "2svar", None)]),
        ("4ra", [Tok(TOK.WORD, "4ra", None)]),
    ]

    TEST_CASES_CONVERT_TELNOS = [
        ("525-4764", TOK.TELNO),
        ("4204200", [Tok(TOK.TELNO, "4204200", ("420-4200", "354"))]),
        ("699 2422", [Tok(TOK.TELNO, "699 2422", ("699-2422", "354"))]),
        ("699 2012", [Tok(TOK.TELNO, "699 2012", ("699-2012", "354"))]),
        ("354 699 2012", [Tok(TOK.TELNO, "354 699 2012", ("699-2012", "354"))]),
        ("+354 699 2012", [Tok(TOK.TELNO, "+354 699 2012", ("699-2012", "+354"))]),
    ]

    TEST_CASES_CONVERT_NUMBERS = [
        ("$472,64", [Tok(TOK.AMOUNT, "$472,64", (472.64, "USD", None, None))]),
        ("€472,64", [Tok(TOK.AMOUNT, "€472,64", (472.64, "EUR", None, None))]),
        ("£199,99", [Tok(TOK.AMOUNT, "£199,99", (199.99, "GBP", None, None))]),
        ("$472.64", [Tok(TOK.AMOUNT, "$472,64", (472.64, "USD", None, None))]),
        ("€472.64", [Tok(TOK.AMOUNT, "€472,64", (472.64, "EUR", None, None))]),
        ("£199.99", [Tok(TOK.AMOUNT, "£199,99", (199.99, "GBP", None, None))]),
        ("$1,472.64", [Tok(TOK.AMOUNT, "$1.472,64", (1472.64, "USD", None, None))]),
        ("€3,472.64", [Tok(TOK.AMOUNT, "€3.472,64", (3472.64, "EUR", None, None))]),
        ("£5,199.99", [Tok(TOK.AMOUNT, "£5.199,99", (5199.99, "GBP", None, None))]),
        ("$1.472,64", [Tok(TOK.AMOUNT, "$1.472,64", (1472.64, "USD", None, None))]),
        ("€3.472,64", [Tok(TOK.AMOUNT, "€3.472,64", (3472.64, "EUR", None, None))]),
        ("£5.199,99", [Tok(TOK.AMOUNT, "£5.199,99", (5199.99, "GBP", None, None))]),
        ("$1,472", [Tok(TOK.AMOUNT, "$1,472", (1.472, "USD", None, None))]),
        ("€3,472", [Tok(TOK.AMOUNT, "€3,472", (3.472, "EUR", None, None))]),
        ("£5,199", [Tok(TOK.AMOUNT, "£5,199", (5.199, "GBP", None, None))]),
        ("$1.472", [Tok(TOK.AMOUNT, "$1.472", (1472, "USD", None, None))]),
        ("€3.472", [Tok(TOK.AMOUNT, "€3.472", (3472, "EUR", None, None))]),
        ("£5.199", [Tok(TOK.AMOUNT, "£5.199", (5199, "GBP", None, None))]),
    ]

    TEST_CASES_COALESCE_PERCENT = [
        ("12,3prósent", [Tok(TOK.PERCENT, "12,3 prósent", (12.3, None, None))]),
        ("12,3 prósent", TOK.PERCENT),
        (
            "12,3hundraðshlutar",
            [Tok(TOK.PERCENT, "12,3 hundraðshlutar", (12.3, None, None))],
        ),
        ("12,3 hundraðshlutar", TOK.PERCENT),
        ("12,3 prósentustig", TOK.PERCENT),
    ]

    TEST_CASES_CONVERT_MEASUREMENTS = [
        ("200° C", [Tok(TOK.MEASUREMENT, "200 °C", ("K", 473.15))]),
        ("80° F", [Tok(TOK.MEASUREMENT, "80 °F", ("K", 299.8166666666667))]),
    ]

    def run_test(test_cases: Iterable[TestCase], **options: Any) -> None:
        for test_case in test_cases:
            if len(test_case) == 3:
                txt, kind, val = cast(tuple[str, int, ValType], test_case)
                c = [Tok(kind, txt, val)]
            elif isinstance(test_case[1], list):
                txt, c = cast(tuple[str, list[Tok]], test_case)
            else:
                txt, kind = cast(tuple[str, int], test_case)
                c = [Tok(kind, txt, None)]
            lt = list(t.tokenize(txt, **options))
            assert len(lt) == len(c) + 2, repr(lt)
            assert lt[0].kind == TOK.S_BEGIN, repr(lt[0])
            assert lt[-1].kind == TOK.S_END, repr(lt[-1])
            for tok, check in zip(lt[1:-1], c):
                assert tok.kind == check.kind, (
                    tok.txt
                    + ": "
                    + repr(TOK.descr[tok.kind])
                    + " "
                    + repr(TOK.descr[check.kind])
                )
                if check.kind == TOK.PUNCTUATION and check.val is None:
                    # Check normalized form of token
                    assert tok.punctuation == check.txt, (
                        tok.punctuation + " != " + check.txt
                    )
                else:
                    assert tok.txt == check.txt, tok.txt + " != " + check.txt
                if check.val is not None:
                    if check.kind == TOK.WORD:
                        # Test set equivalence, since the order of word meanings
                        # is not deterministic
                        assert set(cast(list[BIN_Tuple], tok.val) or []) == set(
                            cast(list[BIN_Tuple], check.val) or []
                        ), (repr(tok.val) + " != " + repr(check.val))
                    else:
                        assert tok.val == check.val, (
                            repr(tok.val) + " != " + repr(check.val)
                        )

    run_test(cast(Iterable[TestCase], TEST_CASES))
    run_test(cast(Iterable[TestCase], TEST_CASES_CONVERT_TELNOS))
    run_test(TEST_CASES_KLUDGY_MODIFY, handle_kludgy_ordinals=t.KLUDGY_ORDINALS_MODIFY)
    run_test(
        TEST_CASES_KLUDGY_TRANSLATE, handle_kludgy_ordinals=t.KLUDGY_ORDINALS_TRANSLATE
    )
    run_test(TEST_CASES_CONVERT_NUMBERS, convert_numbers=True)
    run_test(
        cast(Iterable[TestCase], TEST_CASES_COALESCE_PERCENT), coalesce_percent=True
    )
    run_test(TEST_CASES_CONVERT_MEASUREMENTS, convert_measurements=True)


def test_sentences() -> None:
    KIND = {
        "B": TOK.S_BEGIN,
        "E": TOK.S_END,
        "W": TOK.WORD,
        "P": TOK.PUNCTUATION,
        "T": TOK.TIME,
        "DR": TOK.DATEREL,
        "DA": TOK.DATEABS,
        "Y": TOK.YEAR,
        "N": TOK.NUMBER,
        "NL": TOK.NUMWLETTER,
        "TEL": TOK.TELNO,
        "PC": TOK.PERCENT,
        "U": TOK.URL,
        "O": TOK.ORDINAL,
        "TS": TOK.TIMESTAMP,
        "C": TOK.CURRENCY,
        "A": TOK.AMOUNT,
        "M": TOK.EMAIL,
        "ME": TOK.MEASUREMENT,
        "DM": TOK.DOMAIN,
        "HT": TOK.HASHTAG,
        "K": TOK.SSN,
        "MO": TOK.MOLECULE,
        "SE": TOK.SERIALNUMBER,
        "X": TOK.UNKNOWN,
    }

    def test_sentence(text: str, expected: str, **options: Any) -> None:
        exp = expected.split()
        s = list(t.tokenize(text, **options))
        assert len(s) == len(exp)

        for token, e in zip(s, exp):
            assert e in KIND
            ekind = KIND[e]
            assert token.kind == ekind, "%s should be %s, not %s" % (
                token.txt,
                TOK.descr[ekind],
                TOK.descr[token.kind],
            )

    test_sentence(
        "  Málinu var vísað til stjórnskipunar- og eftirlitsnefndar "
        "skv. 3. gr. XVII. kafla laga nr. 10/2007 þann 3. janúar 2010.",
        "B W      W   W     W   W                                   "
        "W    O  W   O     W     W    W   N P Y   W    DA            P E",
    )

    test_sentence(
        "  Góðan daginn! Ég á 10.000 kr. í vasanum, €100 og $40.Gengi USD er 103,45. "
        "Í dag er 10. júlí. Klukkan er 15:40 núna.Ég fer kl. 13 niður á Hlemm o.s.frv. ",
        "B W     W     P E B W W A       W W      P A    W  A  P E B W W   W  N     P E "
        "B W W W  DR      P E B W   W  T     W   P E B W W T    W     W W     W      E",
    )

    test_sentence(
        "Jæja, bjór í Bretlandi kominn upp í £4.29 (ISK 652).  Dýrt!     Í Japan er hann bara ¥600.",
        "B W P W    W W         W      W   W A    P A   P P E  B W P E B W W     W  W    W    A   P E",
    )

    test_sentence(
        "Almennt verð er krónur 9.900,- en kr. 8.000,- fyrir félagsmenn. Maður borgar 99 kr. 10 sinnum. "
        "USD900 fyrir Bandaríkjamenn en 700 EUR fyrir Þjóðverja. Ég hef spilað RISK 100 sinnum.",
        "B W     W    W  A          P P W  A       P P W     W        P E B  W W      A      N  W   P E "
        "B A    W     W              W  A       W     W      P E B W W  W      W    N   W    P E",
    )

    # '\u00AD': soft hyphen
    # '\u200B': zero-width space
    # '\uFEFF': zero-width non-breaking space
    test_sentence(
        "Lands\u00ADbank\u00ADinn er í 98\u200B,2 pró\u00ADsent eigu\u200B íslenska rík\uFEFFis\u00ADins.",
        "B W                      W  W PC                       W          W        W                  P E",
        coalesce_percent=True,
    )

    test_sentence(
        "Lands\u00ADbank\u00ADinn er í 98\u200B,2 pró\u00ADsent eigu\u200B íslenska rík\uFEFFis\u00ADins.",
        "B W                      W  W N          W             W          W        W                  P E",
        coalesce_percent=False,
    )

    test_sentence(
        "Málið um BSRB gekk marg-ítrekað til stjórnskipunar- og eftirlitsnefndar í 10. sinn "
        "skv. XVII. kafla þann 24. september 2015 nk. Ál-verið notar 60 MWst á ári.",
        "B W   W  W    W    W            W   W                                   W O   W    "
        "W    O     W     W    DA                 W E B W    W     ME      W W  P E",
    )

    test_sentence(
        "Ég er t.d. með tölvupóstfangið fake@news.com, vefföngin "
        "http://greynir.is og https://greynir.is, og síma 6638999. Hann gaf mér 1000 kr. Ég keypti mér 1/2 kaffi. "
        "Það er hægt að ná í mig í s 623 7892, eða vinnusíma, 7227979 eða eitthvað.",
        "B W W W    W   W               M            P W "
        "U                 W  U             P W  W    TEL    P E B W W  W   A       E B W W   W   N   W    P E "
        "B W W  W    W  W  W W   W W        TEL     P W   W        P  TEL     W   W P E",
    )

    test_sentence(
        "Þetta voru 300 1000 kílóa pokar, og 4000 500 kílóa pokar. "
        "Einnig 932 800 kílóa pokar, svo og 177 4455 millilítra skammtar.",
        "B W   W    N   N    W     W    P W  N    N   W     W    P E "
        "B W    N   N   W     W    P W   W  N   N    W          W       P E",
    )

    test_sentence(
        "Skoðaðu vörunúmerin 000-1224 eða 121-2233. Hafðu síðan samband í síma 692 2073. "
        "Þeir voru 313 2012 en 916 árið 2013.",
        "B W     W           SE       W   SE      P E B W  W     W       W W    TEL P E "
        "B W  W    N   Y    W  N    Y P E",
    )

    test_sentence(
        "Hann starfaði við stofnunina árin 1944-50.",
        "B W  W        W   W          W    Y   P N P E",
    )

    test_sentence(
        "Landnám er talið hafa hafist um árið 874 e.Kr. en óvissa er nokkur.",
        "B W     W  W     W    W      W  Y              W  W      W  W     P E",
    )

    test_sentence(
        'Hitinn í "pottinum" var orðinn 30,7 °C þegar 2.000 l voru komnir í hann.',
        "B W    W P W        P W   W      ME      W     ME      W    W      W W   P E",
    )

    test_sentence(
        "Skrifað var undir friðarsamninga í nóvember 1918. Júlíus Sesar var myrtur "
        "þann fimmtánda mars árið 44 f.Kr. og þótti harmdauði.",
        "B W     W   W     W              W DR           P E B W  W     W   W "
        "W    W         DR                 W  W     W        P E",
    )

    test_sentence(
        "1.030 hPa lægð gengur yfir landið árið 2019 e.Kr. Jógúrtin inniheldur 80 kcal.",
        "B ME      W    W      W    W      Y              E B W     W          ME     P E",
    )

    test_sentence(
        "Maður var lagður inn á deild 33C eftir handtöku á Bárugötu 14a þann nítjánda júlí 2016.",
        "B W   W   W      W   W W     NL  W     W        W W        NL  W    W        DR       P E",
    )

    test_sentence(
        "Þessir 10Milljón vírar með 20A straum kostuðu 3000ISK og voru geymdir á Hagamel á 2hæð.",
        "B W    N W       W     W   ME  W      W       A       W  W    W       W W       W N W P E",
    )

    test_sentence(
        "Hitinn í dag var 32°C en á morgun verður hann 33° C og svo 37 °C.",
        "B W    W W   W   ME   W  W W      W      W    ME    W  W   ME   P E",
    )

    test_sentence(
        "Hitinn í dag var 100,3°F en á morgun verður hann 102,7 ° F og svo 99.88 °F.",
        "B W    W W   W   ME      W  W W      W      W    ME        W  W   ME      P E",
    )

    test_sentence(
        "Ég tók stefnu 45° til suðurs og svo 70°N en eftir það 88 ° vestur.",
        "B W W  W      ME  W   W      W  W   ME W W  W     W   ME   W     P E",
    )

    test_sentence(
        "Byrjum á 2½ dl af rjóma því ¼-½ matskeið er ekki nóg. Helmingur er ½. Svarið er 42, ekki 41⅞.",
        "B    W W ME    W  W     W  N P N W       W  W    W P E B W      W  N P E B W W  N P W    N P E",
    )

    test_sentence(
        "Ágúst bjó á hæð númer 13. Ágúst kunni vel við Ágúst í ágúst, enda var 12. ágúst. ÞAÐ VAR 12. ÁGÚST!",
        "B W   W   W W   W     DR        W     W   W   W     W DR   P W    W   DR       P E B W W DR       P E",
    )

    test_sentence(
        "Þórdís Kolbrún Reykfjörð Gylfadóttir var skipuð dómsmála-, ferðamála- og iðnaðarráðherra þann 12. mars 2019.",
        "B W    W       W         W           W   W      W                                        W    DA           P E",
    )

    test_sentence(
        "Þórdís Kolbrún Reykfjörð Gylfadóttir var skipuð viðskipta- dómsmála- ferðamála- og iðnaðarráðherra þann 12. mars 2019.",
        "B W    W       W         W           W   W      W                                                  W    DA           P E",
    )

    test_sentence(
        "#MeToo-byltingin er til staðar á Íslandsmóti #1. #12stig í Eurovision en #égerekkiaðfílaþað! #ruv50.",
        "B HT  P W        W  W   W      W W           O P E B HT  W W          W  HT                P E B HT P E",
    )

    test_sentence(
        "Mbl.is er fjölsóttari en www.visir.is, og Rúv.is... En greynir.is, hann er skemmtilegri.Far þú þangað, ekki á 4chan.org!",
        "B DM   W  W           W  DM          P W  DM    P   E B W DM     P W    W  W        P E B W W W      P W    W DM     P E",
    )

    test_sentence(
        "Sjá nánar á NRK.no eða WhiteHouse.gov. Some.how.com er fínn vefur, skárri en dailymail.co.uk, eða Extrabladet.dk.",
        "B W W     W DM     W   DM          P E B DM         W  W    W    P W      W  DM             P W   DM          P E",
    )

    test_sentence(
        "Fyrri setningin var í þgf. en sú seinni í nf. Ég stóð í ef. en hann í þf. Hvað ef.",
        "B W   W         W   W W    W  W  W      W W E B W  W    W W   W  W    W W E B W W P E",
    )

    test_sentence(
        "Ég vildi [...] fara út. [...] Hann sá mig.",
        "B W W    P     W    W P P   E B W  W  W  P E",
    )

    test_sentence(
        "Ég fæddist 15.10. í Skaftárhreppi en systir mín 25.9. Hún var eldri en ég.",
        "B W W      DR     W W             W  W      W   N   P E B W W W     W  W P E",
    )

    test_sentence(
        "Jón fæddist 15.10. MCMXCVII í Skaftárhreppi.",
        "B W W       DR     W        W W            P E",
    )

    test_sentence(
        "Ég þvoði hárið með H2SO4, og notaði efni (Ag2FeSi) við það, en það hjálpaði ekki.",
        "B W W    W     W   MO   P W  W      W    P MO    P W   W  P W  W   W        W   P E",
    )

    test_sentence(
        "Ég þvoði hárið með H2SO4, og notaði efni (AgFeSi) við það, en það hjálpaði ekki.",
        "B W W    W     W   MO   P W  W      W    P W    P W   W  P W  W   W        W   P E",
    )

    test_sentence(
        "Kennitala fyrirtækisins er 591213-1480, en ekki 591214-1480.",
        "B W       W             W  K          P W  W    N     P N  P E",
    )

    test_sentence(
        "Jón, kt. 301265-5309, vann 301265-53090 kr. H2O var drukkið.",
        "B W P W  K          P W    N     P A       E B MO W W     P E",
    )

    test_sentence(
        "Anna-María var í St. Mary's en prófaði aldrei að fara á Dunkin' Donuts.",
        "B W        W   W W   W      W  W       W      W  W    W W       W     P E",
    )

    test_sentence(
        "Þingmenn og -konur versluðu marg-ítrekað í Tösku- og hanskabúðinni.",
        "B W      W  W      W        W            W W                      P E",
    )

    test_sentence(
        "Tösku- og hanskabúðin, sálug, var á Lauga- eða Skothúsvegi.",
        "B W                 P W    P W   W W                    P E",
    )

    test_sentence(
        "Tösku-og hanskabúðin, sálug, var á Lauga-eða Skothúsvegi.",
        "B W                 P W    P W   W W                    P E",
    )

    test_sentence(
        "Friðgeir fór út kl. hálf átta en var hálf slompaður.",
        "B W      W   W  T             W  W   W    W        P E",
    )

    test_sentence(
        "Klukkan hálf sjö fór Friðgeir út.",
        "B T              W   W        W P E",
    )

    test_sentence(
        "Gummi keypti sjö hundruð áttatíu og sjö kindur.",
        "B W   W      W   W       W       W  W   W     P E",
    )

    test_sentence(
        "Sex milljón manns horfðu á trilljarð Bandaríkjadala fuðra upp.",
        "B W W       W     W      W W         W              W     W  P E",
    )

    test_sentence(
        "Einn, tveir, þrír, fjórir, fimm Dimmalimm.",
        "B W P W    P W   P W     P W    W        P E",
    )

    test_sentence(
        "Einn milljarður tvö hundruð þrjátíu og fjögur þúsund fimm hundruð sextíu og sjö.",
        "B W  W          W   W       W       W  W      W      W    W       W      W  W  P E",
    )

    test_sentence(
        "Níu hundruð áttatíu og sjö milljónir sex hundruð fimmtíu og fjögur þúsund þrjú hundruð tuttugu og eitt.",
        "B W W       W       W  W   W         W   W       W       W  W      W      W    W       W       W  W P E",
    )

    test_sentence(
        "Þrjár septilljónir og einn kvaðrilljarður billjarða.",
        "B W   W            W  W    W              W        P E",
    )

    test_sentence(
        "Allir komast fyrir í fjögurra sæta bíl.",
        "B W   W      W     W W        W    W P E",
    )

    test_sentence(
        "Einn fannst í skóginum, ein í hlíðinni og eitt á túninu.",
        "B W  W      W W       P W   W W        W  W    W W     P E",
    )

    test_sentence(
        "Ég bókaði einnar nætur ferð til Volgograd.",
        "B W W     W      W     W    W   W        P E",
    )

    test_sentence(
        "Tveir af tveimur eiga tveggja sæta bíl.",
        "B W   W  W       W    W       W    W  P E",
    )

    test_sentence(
        "Bóndinn á tvo hunda, tvær kindur og tvö lömb.",
        "B W     W W   W    P W    W      W  W   W   P E",
    )

    test_sentence(
        "Þrír þeirra kynntust þremur þriggja ára hestum.",
        "B W  W      W        W      W       W   W     P E",
    )

    test_sentence(
        "Betri eru þrjú ber í hendi en fjögur í skógi.",
        "B W   W   W    W   W W     W  W      W W    P E",
    )

    test_sentence(
        "Þrjá karla og fjórar konur vantaði.",
        "B W  W     W  W      W     W      P E",
    )

    test_sentence(
        "Þrjár teskeiðar af salti í fjögra lítra skál.",
        "B W   W         W  W     W W      W     W   P E",
    )

    test_sentence(
        "Þarna eru fjórir menn og um fjóra þeirra gilti að "
        "þeir fengu fjögurra ára dóm fyrir fjórum árum.",
        "B W   W   W      W    W  W  W     W      W     W "
        "W    W     W        W   W   W     W      W   P E",
    )


def test_unicode() -> None:
    """Test composite Unicode characters, where a glyph has two code points"""
    # Mask away Python 2/3 difference
    # pylint: disable=undefined-variable
    ACUTE = chr(769)
    UMLAUT = chr(776)
    sent = (
        "Ko" + UMLAUT + "rfuboltamaðurinn og KR-ingurinn Kristo" + ACUTE + "fer Acox "
        "heldur a" + ACUTE + " vit ævinty" + ACUTE + "ranna."
    )
    tokens = list(t.tokenize(sent))
    assert tokens[1].txt == "Körfuboltamaðurinn"
    assert tokens[3].txt == "KR-ingurinn"
    assert tokens[4].txt == "Kristófer"
    assert tokens[7].txt == "á"
    assert tokens[9].txt == "ævintýranna"


def test_correction() -> None:
    SENT = [
        (
            """Hann sagði: "Þú ert fífl"! Ég mótmælti því.""",
            """Hann sagði: „Þú ert fífl“! Ég mótmælti því.""",
        ),
        (
            """Hann sagði: Þú ert "fífl"! Ég mótmælti því.""",
            """Hann sagði: Þú ert „fífl“! Ég mótmælti því.""",
        ),
        (
            """Hann sagði: Þú ert «fífl»! Ég mótmælti því.""",
            """Hann sagði: Þú ert „fífl“! Ég mótmælti því.""",
        ),
        (
            """Hann sagði: ´Þú ert fífl´! Farðu í 3ja sinn.""",
            """Hann sagði: ‚Þú ert fífl‘! Farðu í 3ja sinn.""",
        ),
        (
            """Hann sagði: ´Þú ert fífl´! Farðu í 1sta sinn.""",
            """Hann sagði: ‚Þú ert fífl‘! Farðu í 1sta sinn.""",
        ),
        (
            """Hann sagði: ´Þú ert fífl´! Farðu 2svar í bað.""",
            """Hann sagði: ‚Þú ert fífl‘! Farðu 2svar í bað.""",
        ),
        (
            """Ég keypti 4ra herbergja íbúð á verði 2ja herbergja.""",
            """Ég keypti 4ra herbergja íbúð á verði 2ja herbergja.""",
        ),
        (
            """Hann sagði: Þú ert ´fífl´! Hringdu í 7771234.""",
            """Hann sagði: Þú ert ‚fífl‘! Hringdu í 7771234.""",
        ),
        (
            """Hann sagði: Þú ert (´fífl´)! Ég mótmælti því.""",
            """Hann sagði: Þú ert (‘ fífl‘)! Ég mótmælti því.""",  # !!!
        ),
        (
            """Hann "gaf" mér 10,780.65 dollara.""",
            """Hann „gaf“ mér 10,780.65 dollara.""",
        ),
        (
            """Hann "gaf" mér €10,780.65.""",
            """Hann „gaf“ mér €10,780.65.""",
        ),
        (
            """Hann "gaf" mér €10.780,65.""",
            """Hann „gaf“ mér €10.780,65.""",
        ),
    ]
    SENT_KLUDGY_ORDINALS_MODIFY = [
        (
            """Hann sagði: ´Þú ert fífl´! Farðu í 3ja herbergja íbúð.""",
            """Hann sagði: ‚Þú ert fífl‘! Farðu í þriggja herbergja íbúð.""",
        ),
        (
            """Hann sagði: ´Þú ert fífl´! Farðu í 1sta sinn.""",
            """Hann sagði: ‚Þú ert fífl‘! Farðu í fyrsta sinn.""",
        ),
        (
            """Hann sagði: ´Þú ert fífl´! Farðu 2svar í bað.""",
            """Hann sagði: ‚Þú ert fífl‘! Farðu tvisvar í bað.""",
        ),
        (
            """Ég keypti 4ra herbergja íbúð á verði 2ja herbergja.""",
            """Ég keypti fjögurra herbergja íbúð á verði tveggja herbergja.""",
        ),
    ]
    SENT_KLUDGY_ORDINALS_TRANSLATE = [
        (
            """Hann sagði: ´Þú ert fífl´! Farðu í 3ja sinn.""",
            """Hann sagði: ‚Þú ert fífl‘! Farðu í 3ja sinn.""",
        ),
        (
            """Hann sagði: ´Þú ert fífl´! Farðu í 1sta sinn.""",
            """Hann sagði: ‚Þú ert fífl‘! Farðu í 1sta sinn.""",
        ),
        (
            """Hann sagði: ´Þú ert fífl´! Farðu 2svar í bað.""",
            """Hann sagði: ‚Þú ert fífl‘! Farðu 2svar í bað.""",
        ),
        (
            """Ég keypti 4ra herbergja íbúð á verði 2ja herbergja.""",
            """Ég keypti 4ra herbergja íbúð á verði 2ja herbergja.""",
        ),
    ]
    SENT_CONVERT_NUMBERS = [
        (
            """Hann "gaf" mér 10,780.65 dollara.""",
            """Hann „gaf“ mér 10.780,65 dollara.""",
        ),
        ("""Hann "gaf" mér €10,780.65.""", """Hann „gaf“ mér €10.780,65."""),
        (
            """Hann "gaf" mér €10.780,65.""",
            """Hann „gaf“ mér €10.780,65.""",
        ),
    ]
    for sent, correct in SENT:
        s = t.tokenize(sent)
        txt = t.detokenize(s, normalize=True)
        assert txt == correct
    for sent, correct in SENT_KLUDGY_ORDINALS_MODIFY:
        s = t.tokenize(sent, handle_kludgy_ordinals=t.KLUDGY_ORDINALS_MODIFY)
        txt = t.detokenize(s, normalize=True)
        assert txt == correct
    for sent, correct in SENT_KLUDGY_ORDINALS_TRANSLATE:
        s = t.tokenize(sent, handle_kludgy_ordinals=t.KLUDGY_ORDINALS_TRANSLATE)
        txt = t.detokenize(s, normalize=True)
        assert txt == correct
    for sent, correct in SENT_CONVERT_NUMBERS:
        s = t.tokenize(sent, convert_numbers=True)
        txt = t.detokenize(s, normalize=True)
        assert txt == correct


def test_correct_spaces() -> None:
    s = t.correct_spaces("Bensínstöðvar, -dælur og -brúsar eru bannaðir.")
    assert s == "Bensínstöðvar, -dælur og -brúsar eru bannaðir."
    s = t.correct_spaces("Fjármála- og efnahagsráðuneytið")
    assert s == "Fjármála- og efnahagsráðuneytið"
    s = t.correct_spaces("Iðnaðar-, ferðamála- og nýsköpunarráðuneytið")
    assert s == "Iðnaðar-, ferðamála- og nýsköpunarráðuneytið"
    s = t.correct_spaces(
        "Ég hef aldrei verslað í húsgagna-, byggingavöru- eða timburverslun."
    )
    assert s == "Ég hef aldrei verslað í húsgagna-, byggingavöru- eða timburverslun."
    s = t.correct_spaces(
        "Frétt \n  dagsins:Jón\t ,Friðgeir og Páll ! 100,8  /  2  =   50.4"
    )
    assert s == "Frétt dagsins: Jón, Friðgeir og Páll! 100,8/2 = 50.4"
    s = t.correct_spaces(
        "Hitinn    var\n-7,4 \t gráður en   álverðið var  \n $10,348.55."
    )
    assert s == "Hitinn var -7,4 gráður en álverðið var $10,348.55."
    s = t.correct_spaces(
        "\n Breytingin var   +4,10 þingmenn \t  en dollarinn er nú á €1,3455  ."
    )
    assert s == "Breytingin var +4,10 þingmenn en dollarinn er nú á €1,3455."
    s = t.correct_spaces("Jón- sem var formaður — mótmælti málinu.")
    assert s == "Jón-sem var formaður—mótmælti málinu."
    s = t.correct_spaces("Það á   að geyma mjólkina við  20 ±  3 °C")
    assert s == "Það á að geyma mjólkina við 20±3 °C"
    s = t.correct_spaces("Við förum t.d. til Íslands o.s.frv.")
    assert s == "Við förum t.d. til Íslands o.s.frv."
    s = t.correct_spaces("Við förum t. d. til Íslands o. s. frv.")
    assert (
        s == "Við förum t. d. til Íslands o. s. frv."
    )  # This shouldn't be corrected here
    s = t.correct_spaces("M.a. lögum við bil.")
    assert s == "M.a. lögum við bil."
    s = t.correct_spaces("HANN BORÐAR Þ.Á.M. EPLI.")
    assert s == "HANN BORÐAR Þ.Á.M. EPLI."
    s = t.correct_spaces("Ég fór til Írlands 6.júní og þar var 17.4°C hiti eða 230.3K.")
    assert s == "Ég fór til Írlands 6. júní og þar var 17.4 °C hiti eða 230.3 K."
    s = t.correct_spaces(
        "Þetta er setning.Þetta er önnur setning.Líka.En hvað með þetta?"
    )
    assert s == "Þetta er setning. Þetta er önnur setning. Líka. En hvað með þetta?"
    # Test that colon-separated times are not space-separated
    s = t.correct_spaces("Klukkan er 12: 00 og ég ætla að fara út .")
    assert s == "Klukkan er 12:00 og ég ætla að fara út."
    s = t.correct_spaces("Tíminn byrjar kl . 4: 14 og klukkan er núna 5:00 .")
    assert s == "Tíminn byrjar kl. 4:14 og klukkan er núna 5:00."
    s = t.correct_spaces("Veislan verður kl . 12 : 00 - 14 : 00.")
    assert s == "Veislan verður kl. 12:00-14:00."
    s = t.correct_spaces("Hún kom í mark á tímanum 3 : 59 : 04 ,rétt fyrir lokin.")
    assert s == "Hún kom í mark á tímanum 3:59:04, rétt fyrir lokin."


def test_abbrev() -> None:
    tokens = list(t.tokenize("Í dag las ég fréttina um IBM t.d. á Mbl."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        # We are testing that 'Í' is not an abbreviation
        Tok(kind=TOK.WORD, txt="Í", val=None),
        Tok(kind=TOK.WORD, txt="dag", val=None),
        Tok(kind=TOK.WORD, txt="las", val=None),
        Tok(kind=TOK.WORD, txt="ég", val=None),
        Tok(kind=TOK.WORD, txt="fréttina", val=None),
        Tok(kind=TOK.WORD, txt="um", val=None),
        Tok(
            kind=TOK.WORD,
            txt="IBM",
            val=[
                BIN_Tuple(
                    "International Business Machines", 0, "hk", "skst", "IBM", "-"
                )
            ],
        ),
        Tok(
            kind=TOK.WORD,
            txt="t.d.",
            val=[BIN_Tuple("til dæmis", 0, "ao", "frasi", "t.d.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="á", val=None),
        Tok(
            kind=TOK.WORD,
            txt="Mbl",
            val=[BIN_Tuple("Morgunblaðið", 0, "hk", "skst", "Mbl", "-")],
        ),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Reykjavík er stór m.v. Akureyri."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Reykjavík", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="stór", val=None),
        Tok(
            kind=TOK.WORD,
            txt="m.v.",
            val=[BIN_Tuple("miðað við", 0, "fs", "frasi", "m.v.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="Akureyri", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Ég nefndi t.d. Guðmund."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Ég", val=None),
        Tok(kind=TOK.WORD, txt="nefndi", val=None),
        Tok(
            kind=TOK.WORD,
            txt="t.d.",
            val=[BIN_Tuple("til dæmis", 0, "ao", "frasi", "t.d.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="Guðmund", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Jón var sérfr. Guðmundur var læknir."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Jón", val=None),
        Tok(kind=TOK.WORD, txt="var", val=None),
        Tok(
            kind=TOK.WORD,
            txt="sérfr.",
            val=[BIN_Tuple("sérfræðingur", 0, "kk", "skst", "sérfr.", "-")],
        ),
        Tok(kind=TOK.S_END, txt=None, val=None),
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Guðmundur", val=None),
        Tok(kind=TOK.WORD, txt="var", val=None),
        Tok(kind=TOK.WORD, txt="læknir", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Jón var t.h. Guðmundur var t.v. á myndinni."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Jón", val=None),
        Tok(kind=TOK.WORD, txt="var", val=None),
        Tok(
            kind=TOK.WORD,
            txt="t.h.",
            val=[BIN_Tuple("til hægri", 0, "ao", "frasi", "t.h.", "-")],
        ),
        Tok(kind=TOK.S_END, txt=None, val=None),
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Guðmundur", val=None),
        Tok(kind=TOK.WORD, txt="var", val=None),
        Tok(
            kind=TOK.WORD,
            txt="t.v.",
            val=[BIN_Tuple("til vinstri", 0, "ao", "frasi", "t.v.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="á", val=None),
        Tok(kind=TOK.WORD, txt="myndinni", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Bréfið var dags. 20. maí."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Bréfið", val=None),
        Tok(kind=TOK.WORD, txt="var", val=None),
        Tok(
            kind=TOK.WORD,
            txt="dags.",
            val=[
                BIN_Tuple("dagsetja", 0, "so", "skst", "dags.", "-"),
                BIN_Tuple("dagsettur", 0, "lo", "skst", "dags.", "-"),
            ],
        ),
        Tok(kind=TOK.DATEREL, txt="20. maí", val=(0, 5, 20)),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Ég ræddi við hv. þm. Halldóru Mogensen."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Ég", val=None),
        Tok(kind=TOK.WORD, txt="ræddi", val=None),
        Tok(kind=TOK.WORD, txt="við", val=None),
        Tok(
            kind=TOK.WORD,
            txt="hv.",
            val=[
                BIN_Tuple("hæstvirtur", 0, "lo", "skst", "hv.", "-"),
                BIN_Tuple("háttvirtur", 0, "lo", "skst", "hv.", "-"),
            ],
        ),
        Tok(
            kind=TOK.WORD,
            txt="þm.",
            val=[BIN_Tuple("þingmaður", 0, "kk", "skst", "þm.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="Halldóru", val=None),
        Tok(kind=TOK.WORD, txt="Mogensen", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Það var snemma dags. Fuglarnir sungu."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Það", val=None),
        Tok(kind=TOK.WORD, txt="var", val=None),
        Tok(kind=TOK.WORD, txt="snemma", val=None),
        Tok(kind=TOK.WORD, txt="dags", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Fuglarnir", val=None),
        Tok(kind=TOK.WORD, txt="sungu", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Nú er s. 550-1234 hjá bankanum."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Nú", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(
            kind=TOK.WORD,
            txt="s.",
            val=[BIN_Tuple("símanúmer", 0, "hk", "skst", "s.", "-")],
        ),
        Tok(kind=TOK.TELNO, txt="550-1234", val=("550-1234", "354")),
        Tok(kind=TOK.WORD, txt="hjá", val=None),
        Tok(kind=TOK.WORD, txt="bankanum", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Ég er með s. 550-1234."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Ég", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="með", val=None),
        Tok(
            kind=TOK.WORD,
            txt="s.",
            val=[BIN_Tuple("símanúmer", 0, "hk", "skst", "s.", "-")],
        ),
        Tok(kind=TOK.TELNO, txt="550-1234", val=("550-1234", "354")),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Ég er með s. en hin er með símanúmer."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Ég", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="með", val=None),
        Tok(
            kind=TOK.WORD,
            txt="s.",
            val=[BIN_Tuple("símanúmer", 0, "hk", "skst", "s.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="en", val=None),
        Tok(kind=TOK.WORD, txt="hin", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="með", val=None),
        Tok(kind=TOK.WORD, txt="símanúmer", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Ég er með s. Hin er með símanúmer."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Ég", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="með", val=None),
        Tok(
            kind=TOK.WORD,
            txt="s.",
            val=[BIN_Tuple("símanúmer", 0, "hk", "skst", "s.", "-")],
        ),
        Tok(kind=TOK.S_END, txt=None, val=None),
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Hin", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="með", val=None),
        Tok(kind=TOK.WORD, txt="símanúmer", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Ég er með s. Hinrik er með símanúmer."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Ég", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="með", val=None),
        Tok(
            kind=TOK.WORD,
            txt="s.",
            val=[BIN_Tuple("símanúmer", 0, "hk", "skst", "s.", "-")],
        ),
        Tok(kind=TOK.S_END, txt=None, val=None),
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Hinrik", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="með", val=None),
        Tok(kind=TOK.WORD, txt="símanúmer", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Ég er með rknr. 0123-26-123456 í bankanum."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Ég", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="með", val=None),
        Tok(
            kind=TOK.WORD,
            txt="rknr.",
            val=[BIN_Tuple("reikningsnúmer", 0, "hk", "skst", "rknr.", "-")],
        ),
        Tok(kind=TOK.SERIALNUMBER, txt="0123-26-123456", val=None),
        Tok(kind=TOK.WORD, txt="í", val=None),
        Tok(kind=TOK.WORD, txt="bankanum", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Ég er með rknr. 0123-26-123456."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Ég", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="með", val=None),
        Tok(
            kind=TOK.WORD,
            txt="rknr.",
            val=[BIN_Tuple("reikningsnúmer", 0, "hk", "skst", "rknr.", "-")],
        ),
        Tok(kind=TOK.SERIALNUMBER, txt="0123-26-123456", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Ég er með rknr. en hin er með reikningsnúmer."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Ég", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="með", val=None),
        Tok(
            kind=TOK.WORD,
            txt="rknr.",
            val=[BIN_Tuple("reikningsnúmer", 0, "hk", "skst", "rknr.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="en", val=None),
        Tok(kind=TOK.WORD, txt="hin", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="með", val=None),
        Tok(kind=TOK.WORD, txt="reikningsnúmer", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Hallur tók 11 frák. en Valur 12."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Hallur", val=None),
        Tok(kind=TOK.WORD, txt="tók", val=None),
        Tok(kind=TOK.NUMBER, txt="11", val=(11, None, None)),
        Tok(
            kind=TOK.WORD,
            txt="frák.",
            val=[BIN_Tuple("fráköst", 0, "hk", "skst", "frák.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="en", val=None),
        Tok(kind=TOK.WORD, txt="Valur", val=None),
        Tok(kind=TOK.NUMBER, txt="12", val=(12, None, None)),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Hallur tók 11 frák. Marteinn tók 12."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Hallur", val=None),
        Tok(kind=TOK.WORD, txt="tók", val=None),
        Tok(kind=TOK.NUMBER, txt="11", val=(11, None, None)),
        Tok(
            kind=TOK.WORD,
            txt="frák.",
            val=[BIN_Tuple("fráköst", 0, "hk", "skst", "frák.", "-")],
        ),
        Tok(kind=TOK.S_END, txt=None, val=None),
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Marteinn", val=None),
        Tok(kind=TOK.WORD, txt="tók", val=None),
        Tok(kind=TOK.NUMBER, txt="12", val=(12, None, None)),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Hallur tók 11 frák. Hinn tók tólf."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Hallur", val=None),
        Tok(kind=TOK.WORD, txt="tók", val=None),
        Tok(kind=TOK.NUMBER, txt="11", val=(11, None, None)),
        Tok(
            kind=TOK.WORD,
            txt="frák.",
            val=[BIN_Tuple("fráköst", 0, "hk", "skst", "frák.", "-")],
        ),
        Tok(kind=TOK.S_END, txt=None, val=None),
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Hinn", val=None),
        Tok(kind=TOK.WORD, txt="tók", val=None),
        Tok(kind=TOK.WORD, txt="tólf", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Ath. ekki ganga um gólf."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(
            kind=TOK.WORD,
            txt="Ath.",
            val=[BIN_Tuple("athuga", 0, "so", "skst", "ath.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="ekki", val=None),
        Tok(kind=TOK.WORD, txt="ganga", val=None),
        Tok(kind=TOK.WORD, txt="um", val=None),
        Tok(kind=TOK.WORD, txt="gólf", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Ath. Marteinn verður ekki við á morgun."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(
            kind=TOK.WORD,
            txt="Ath.",
            val=[BIN_Tuple("athuga", 0, "so", "skst", "ath.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="Marteinn", val=None),
        Tok(kind=TOK.WORD, txt="verður", val=None),
        Tok(kind=TOK.WORD, txt="ekki", val=None),
        Tok(kind=TOK.WORD, txt="við", val=None),
        Tok(kind=TOK.WORD, txt="á", val=None),
        Tok(kind=TOK.WORD, txt="morgun", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Jón keypti átta kýr, ath. heimildir."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Jón", val=None),
        Tok(kind=TOK.WORD, txt="keypti", val=None),
        Tok(kind=TOK.WORD, txt="átta", val=None),
        Tok(kind=TOK.WORD, txt="kýr", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=",", val=(3, ",")),
        Tok(
            kind=TOK.WORD,
            txt="ath.",
            val=[BIN_Tuple("athuga", 0, "so", "skst", "ath.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="heimildir", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Ég er ástfangin, ps. ekki lesa dagbókina mína."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Ég", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="ástfangin", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=",", val=(3, ",")),
        Tok(
            kind=TOK.WORD,
            txt="ps.",
            val=[BIN_Tuple("eftirskrift", 0, "kvk", "skst", "ps.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="ekki", val=None),
        Tok(kind=TOK.WORD, txt="lesa", val=None),
        Tok(kind=TOK.WORD, txt="dagbókina", val=None),
        Tok(kind=TOK.WORD, txt="mína", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Vala er með M.Sc. í málfræði."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Vala", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="með", val=None),
        Tok(
            kind=TOK.WORD,
            txt="M.Sc.",
            val=[BIN_Tuple("Master of Science", 0, "hk", "erl", "M.Sc.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="í", val=None),
        Tok(kind=TOK.WORD, txt="málfræði", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Vala jafnaði M.Sc. Halls."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Vala", val=None),
        Tok(kind=TOK.WORD, txt="jafnaði", val=None),
        Tok(
            kind=TOK.WORD,
            txt="M.Sc.",
            val=[BIN_Tuple("Master of Science", 0, "hk", "erl", "M.Sc.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="Halls", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Vala er með M.Sc. Hallur er með grunnskólapróf."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Vala", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="með", val=None),
        Tok(
            kind=TOK.WORD,
            txt="M.Sc.",
            val=[BIN_Tuple("Master of Science", 0, "hk", "erl", "M.Sc.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="Hallur", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="með", val=None),
        Tok(kind=TOK.WORD, txt="grunnskólapróf", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Vala er með M.Sc. Hinn er með grunnskólapróf."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Vala", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="með", val=None),
        Tok(
            kind=TOK.WORD,
            txt="M.Sc.",
            val=[BIN_Tuple("Master of Science", 0, "hk", "erl", "M.Sc.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="Hinn", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="með", val=None),
        Tok(kind=TOK.WORD, txt="grunnskólapróf", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Það er kalt í dag m.v. veðurspána."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Það", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="kalt", val=None),
        Tok(kind=TOK.WORD, txt="í", val=None),
        Tok(kind=TOK.WORD, txt="dag", val=None),
        Tok(
            kind=TOK.WORD,
            txt="m.v.",
            val=[BIN_Tuple("miðað við", 0, "fs", "frasi", "m.v.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="veðurspána", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Jóna er hávaxin m.v. Martein."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Jóna", val=None),
        Tok(kind=TOK.WORD, txt="er", val=None),
        Tok(kind=TOK.WORD, txt="hávaxin", val=None),
        Tok(
            kind=TOK.WORD,
            txt="m.v.",
            val=[BIN_Tuple("miðað við", 0, "fs", "frasi", "m.v.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="Martein", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Jóna þarf að velja á milli matar vs. reikninga."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Jóna", val=None),
        Tok(kind=TOK.WORD, txt="þarf", val=None),
        Tok(kind=TOK.WORD, txt="að", val=None),
        Tok(kind=TOK.WORD, txt="velja", val=None),
        Tok(kind=TOK.WORD, txt="á", val=None),
        Tok(kind=TOK.WORD, txt="milli", val=None),
        Tok(kind=TOK.WORD, txt="matar", val=None),
        Tok(
            kind=TOK.WORD,
            txt="vs.",
            val=[BIN_Tuple("gegn", 0, "fs", "skst", "vs.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="reikninga", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(t.tokenize("Jóna þarf að velja á milli Íslands vs. Svíþjóðar."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Jóna", val=None),
        Tok(kind=TOK.WORD, txt="þarf", val=None),
        Tok(kind=TOK.WORD, txt="að", val=None),
        Tok(kind=TOK.WORD, txt="velja", val=None),
        Tok(kind=TOK.WORD, txt="á", val=None),
        Tok(kind=TOK.WORD, txt="milli", val=None),
        Tok(kind=TOK.WORD, txt="Íslands", val=None),
        Tok(
            kind=TOK.WORD,
            txt="vs.",
            val=[BIN_Tuple("gegn", 0, "fs", "skst", "vs.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="Svíþjóðar", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Ég keypti 3 km. af Marteini."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Ég", val=None),
        Tok(kind=TOK.WORD, txt="keypti", val=None),
        Tok(kind=TOK.MEASUREMENT, txt="3 km.", val=("m", 3000.0)),
        Tok(kind=TOK.WORD, txt="af", val=None),
        Tok(kind=TOK.WORD, txt="Marteini", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(
        t.tokenize("Ég jafnaði 3 km. Marteins.")
    )  # TODO can't handle cases before names in same sentence
    tokens = strip_originals(tokens)
    # assert tokens == [
    #    Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
    #    Tok(kind=TOK.WORD, txt="Ég", val=None),
    #    Tok(kind=TOK.WORD, txt="jafnaði", val=None),
    #    Tok(kind=TOK.MEASUREMENT, txt="3 km.", val=('m', 3000.0)),
    #    Tok(kind=TOK.WORD, txt="Marteins", val=None),
    #    Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
    #    Tok(kind=TOK.S_END, txt=None, val=None),
    # ]
    tokens = list(t.tokenize("Ég keypti 3 km. Hinn keypti átta."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Ég", val=None),
        Tok(kind=TOK.WORD, txt="keypti", val=None),
        Tok(kind=TOK.MEASUREMENT, txt="3 km", val=("m", 3000.0)),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Hinn", val=None),
        Tok(kind=TOK.WORD, txt="keypti", val=None),
        Tok(kind=TOK.WORD, txt="átta", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Ég keypti 3 kcal. af Marteini."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Ég", val=None),
        Tok(kind=TOK.WORD, txt="keypti", val=None),
        Tok(kind=TOK.MEASUREMENT, txt="3 kcal.", val=("J", 12552)),
        Tok(kind=TOK.WORD, txt="af", val=None),
        Tok(kind=TOK.WORD, txt="Marteini", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]
    tokens = list(
        t.tokenize("Ég jafnaði 3 kcal. Marteins.")
    )  # TODO can't handle cases before names in same sentence
    tokens = strip_originals(tokens)
    # assert tokens == [
    #    Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
    #    Tok(kind=TOK.WORD, txt="Ég", val=None),
    #    Tok(kind=TOK.WORD, txt="jafnaði", val=None),
    #    Tok(kind=TOK.MEASUREMENT, txt="3 kcal.", val=('J', 12552)),
    #    Tok(kind=TOK.WORD, txt="Marteins", val=None),
    #    Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
    #    Tok(kind=TOK.S_END, txt=None, val=None),
    # ]
    tokens = list(t.tokenize("Ég keypti 3 kcal. Hinn keypti átta."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Ég", val=None),
        Tok(kind=TOK.WORD, txt="keypti", val=None),
        Tok(kind=TOK.MEASUREMENT, txt="3 kcal", val=("J", 12552.0)),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Hinn", val=None),
        Tok(kind=TOK.WORD, txt="keypti", val=None),
        Tok(kind=TOK.WORD, txt="átta", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    # m/s og km/klst.
    tokens = list(t.tokenize("Úti var 18 m/s og kuldi."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Úti", val=None),
        Tok(kind=TOK.WORD, txt="var", val=None),
        Tok(kind=TOK.MEASUREMENT, txt="18 m/s", val=("m/s", 18.0)),
        Tok(kind=TOK.WORD, txt="og", val=None),
        Tok(kind=TOK.WORD, txt="kuldi", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(
        t.tokenize("Bíllinn keyrði á 14 km/klst. Nonni keyrði á hámarkshraða.")
    )
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Bíllinn", val=None),
        Tok(kind=TOK.WORD, txt="keyrði", val=None),
        Tok(kind=TOK.WORD, txt="á", val=None),
        Tok(
            kind=TOK.MEASUREMENT, txt="14 km/klst", val=("14 km/klst", 14000.0)
        ),  # TODO wrong val but correct tokenization
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Nonni", val=None),
        Tok(kind=TOK.WORD, txt="keyrði", val=None),
        Tok(kind=TOK.WORD, txt="á", val=None),
        Tok(kind=TOK.WORD, txt="hámarkshraða", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Bílarnir keyrðu á 14 km/klst hraða."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Bílarnir", val=None),
        Tok(kind=TOK.WORD, txt="keyrðu", val=None),
        Tok(kind=TOK.WORD, txt="á", val=None),
        Tok(kind=TOK.MEASUREMENT, txt="14 km/klst", val=("m/s", 3.8888888888888893)),
        Tok(kind=TOK.WORD, txt="hraða", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Sjö millj. krónur fóru í lagfæringarnar."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Sjö", val=None),
        Tok(
            kind=TOK.WORD,
            txt="millj.",
            val=[
                BIN_Tuple(
                    stofn="milljónir",
                    utg=0,
                    ordfl="kvk",
                    fl="skst",
                    ordmynd="millj.",
                    beyging="-",
                ),
                BIN_Tuple(
                    stofn="milljarðar",
                    utg=0,
                    ordfl="kk",
                    fl="skst",
                    ordmynd="millj.",
                    beyging="-",
                ),
            ],
        ),
        Tok(kind=TOK.WORD, txt="krónur", val=None),  # Should this be amount?
        Tok(kind=TOK.WORD, txt="fóru", val=None),
        Tok(kind=TOK.WORD, txt="í", val=None),
        Tok(kind=TOK.WORD, txt="lagfæringarnar", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Aðgerðin kostaði níutíu þús.kr."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Aðgerðin", val=None),
        Tok(kind=TOK.WORD, txt="kostaði", val=None),
        Tok(kind=TOK.WORD, txt="níutíu", val=None),
        Tok(
            kind=TOK.WORD,
            txt="þús.kr.",
            val=[BIN_Tuple("þúsundir króna", 0, "kvk", "skst", "þús.kr.", "-")],
        ),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Aðgerðin kostaði 14 þús.kr."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Aðgerðin", val=None),
        Tok(kind=TOK.WORD, txt="kostaði", val=None),
        Tok(kind=TOK.AMOUNT, txt="14 þús.kr.", val=(14e3, "ISK", None, None)),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Aðgerðin þann 5.     mars kostaði 14     þús.kr."))
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(
            kind=TOK.WORD,
            txt="Aðgerðin",
            val=None,
            original="Aðgerðin",
            origin_spans=[0, 1, 2, 3, 4, 5, 6, 7],
        ),
        Tok(
            kind=TOK.WORD,
            txt="þann",
            val=None,
            original=" þann",
            origin_spans=[1, 2, 3, 4],
        ),
        Tok(
            kind=TOK.DATEREL,
            txt="5. mars",
            val=(0, 3, 5),
            original=" 5.     mars",
            origin_spans=[1, 2, 3, 8, 9, 10, 11],
        ),
        Tok(
            kind=TOK.WORD,
            txt="kostaði",
            val=None,
            original=" kostaði",
            origin_spans=[1, 2, 3, 4, 5, 6, 7],
        ),
        Tok(
            kind=TOK.AMOUNT,
            txt="14 þús.kr.",
            val=(14000.0, "ISK", None, None),
            original=" 14     þús.kr.",
            origin_spans=[1, 2, 3, 8, 9, 10, 11, 12, 13, 14],
        ),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Aðgerðin þann 5.mars kostaði 14þús.kr."))
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(
            kind=TOK.WORD,
            txt="Aðgerðin",
            val=None,
            original="Aðgerðin",
            origin_spans=[0, 1, 2, 3, 4, 5, 6, 7],
        ),
        Tok(
            kind=TOK.WORD,
            txt="þann",
            val=None,
            original=" þann",
            origin_spans=[1, 2, 3, 4],
        ),
        Tok(
            kind=TOK.DATEREL,
            txt="5. mars",
            val=(0, 3, 5),
            original=" 5.mars",
            origin_spans=[1, 2, 3, 3, 4, 5, 6],
        ),
        Tok(
            kind=TOK.WORD,
            txt="kostaði",
            val=None,
            original=" kostaði",
            origin_spans=[1, 2, 3, 4, 5, 6, 7],
        ),
        Tok(
            kind=TOK.AMOUNT,
            txt="14 þús.kr.",
            val=(14000.0, "ISK", None, None),
            original=" 14þús.kr.",
            origin_spans=[1, 2, 3, 3, 4, 5, 6, 7, 8, 9],
        ),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Átta menn áttu að fara að hátta klukkan átta."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Átta", val=None),
        Tok(kind=TOK.WORD, txt="menn", val=None),
        Tok(kind=TOK.WORD, txt="áttu", val=None),
        Tok(kind=TOK.WORD, txt="að", val=None),
        Tok(kind=TOK.WORD, txt="fara", val=None),
        Tok(kind=TOK.WORD, txt="að", val=None),
        Tok(kind=TOK.WORD, txt="hátta", val=None),
        Tok(kind=TOK.TIME, txt="klukkan átta", val=(8, 0, 0)),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(
        t.tokenize(
            "Níu þúsund kvaðrilljarðar billjarða tuttugu og ein milljón og eitt."
        )
    )
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Níu", val=None),
        Tok(kind=TOK.WORD, txt="þúsund", val=None),
        Tok(kind=TOK.WORD, txt="kvaðrilljarðar", val=None),
        Tok(kind=TOK.WORD, txt="billjarða", val=None),
        Tok(kind=TOK.WORD, txt="tuttugu", val=None),
        Tok(kind=TOK.WORD, txt="og", val=None),
        Tok(kind=TOK.WORD, txt="ein", val=None),
        Tok(kind=TOK.WORD, txt="milljón", val=None),
        Tok(kind=TOK.WORD, txt="og", val=None),
        Tok(kind=TOK.WORD, txt="eitt", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Oktilljón septilljónir og ein kvintilljón."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Oktilljón", val=None),
        Tok(kind=TOK.WORD, txt="septilljónir", val=None),
        Tok(kind=TOK.WORD, txt="og", val=None),
        Tok(kind=TOK.WORD, txt="ein", val=None),
        Tok(kind=TOK.WORD, txt="kvintilljón", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(
        t.tokenize(
            "Um 14,5 milljarðar króna hafa verið greiddir í tekjufalls- og viðspyrnustyrki."
        )
    )
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Um", val=None),
        Tok(kind=TOK.NUMBER, txt="14,5", val=(14.5, None, None)),
        Tok(kind=TOK.WORD, txt="milljarðar", val=None),
        Tok(kind=TOK.WORD, txt="króna", val=None),
        Tok(kind=TOK.WORD, txt="hafa", val=None),
        Tok(kind=TOK.WORD, txt="verið", val=None),
        Tok(kind=TOK.WORD, txt="greiddir", val=None),
        Tok(kind=TOK.WORD, txt="í", val=None),
        Tok(kind=TOK.WORD, txt="tekjufalls- og viðspyrnustyrki", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Ekki einn einasti maður var hlynntur breytingunum."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Ekki", val=None),
        Tok(kind=TOK.WORD, txt="einn", val=None),
        Tok(kind=TOK.WORD, txt="einasti", val=None),
        Tok(kind=TOK.WORD, txt="maður", val=None),
        Tok(kind=TOK.WORD, txt="var", val=None),
        Tok(kind=TOK.WORD, txt="hlynntur", val=None),
        Tok(kind=TOK.WORD, txt="breytingunum", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Barnið var eins árs en gekk eitt í skólann."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Barnið", val=None),
        Tok(kind=TOK.WORD, txt="var", val=None),
        # Tok(kind=TOK.NUMBER, txt="eins", val=(1, None, None)),
        Tok(kind=TOK.WORD, txt="eins", val=None),  # TODO
        Tok(kind=TOK.WORD, txt="árs", val=None),
        Tok(kind=TOK.WORD, txt="en", val=None),
        Tok(kind=TOK.WORD, txt="gekk", val=None),
        Tok(kind=TOK.WORD, txt="eitt", val=None),
        Tok(kind=TOK.WORD, txt="í", val=None),
        Tok(kind=TOK.WORD, txt="skólann", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Það eina sem vantaði í lautarferðina var góða skapið."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Það", val=None),
        Tok(kind=TOK.WORD, txt="eina", val=None),
        Tok(kind=TOK.WORD, txt="sem", val=None),
        Tok(kind=TOK.WORD, txt="vantaði", val=None),
        Tok(kind=TOK.WORD, txt="í", val=None),
        Tok(kind=TOK.WORD, txt="lautarferðina", val=None),
        Tok(kind=TOK.WORD, txt="var", val=None),
        Tok(kind=TOK.WORD, txt="góða", val=None),
        Tok(kind=TOK.WORD, txt="skapið", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Þriggja daga ferð ílengdist þegar þrjú börn veiktust."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Þriggja", val=None),
        Tok(kind=TOK.WORD, txt="daga", val=None),
        Tok(kind=TOK.WORD, txt="ferð", val=None),
        Tok(kind=TOK.WORD, txt="ílengdist", val=None),
        Tok(kind=TOK.WORD, txt="þegar", val=None),
        Tok(kind=TOK.WORD, txt="þrjú", val=None),
        Tok(kind=TOK.WORD, txt="börn", val=None),
        Tok(kind=TOK.WORD, txt="veiktust", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(
        t.tokenize("Þær voru ekki einar um það að hafa lesið Þúsund og eina nótt.")
    )
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Þær", val=None),
        Tok(kind=TOK.WORD, txt="voru", val=None),
        Tok(kind=TOK.WORD, txt="ekki", val=None),
        Tok(kind=TOK.WORD, txt="einar", val=None),
        Tok(kind=TOK.WORD, txt="um", val=None),
        Tok(kind=TOK.WORD, txt="það", val=None),
        Tok(kind=TOK.WORD, txt="að", val=None),
        Tok(kind=TOK.WORD, txt="hafa", val=None),
        Tok(kind=TOK.WORD, txt="lesið", val=None),
        Tok(kind=TOK.WORD, txt="Þúsund", val=None),
        Tok(kind=TOK.WORD, txt="og", val=None),
        Tok(kind=TOK.WORD, txt="eina", val=None),
        Tok(kind=TOK.WORD, txt="nótt", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]

    tokens = list(t.tokenize("Eitt sinn, fyrir langa löngu, í fjarlægri vetrarbraut."))
    tokens = strip_originals(tokens)
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Eitt", val=None),
        Tok(kind=TOK.WORD, txt="sinn", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=",", val=(3, ",")),
        Tok(kind=TOK.WORD, txt="fyrir", val=None),
        Tok(kind=TOK.WORD, txt="langa", val=None),
        Tok(kind=TOK.WORD, txt="löngu", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=",", val=(3, ",")),
        Tok(kind=TOK.WORD, txt="í", val=None),
        Tok(kind=TOK.WORD, txt="fjarlægri", val=None),
        Tok(kind=TOK.WORD, txt="vetrarbraut", val=None),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=(3, ".")),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]


def test_overlap() -> None:
    # Make sure that there is no overlap between the punctuation sets
    assert not (
        set(t.definitions.LEFT_PUNCTUATION)
        & set(t.definitions.RIGHT_PUNCTUATION)
        & set(t.definitions.CENTER_PUNCTUATION)
        & set(t.definitions.NONE_PUNCTUATION)
    )


def test_split_sentences() -> None:
    """Test shallow tokenization"""
    s = (
        "3.janúar sl. keypti   ég 64kWst rafbíl. Hann kostaði € 30.000.  \n"
        "200.000 manns mótmæltu.\n"
        "Hér byrjar ný setning"
    )
    g = t.split_into_sentences(s)
    sents = list(g)
    assert len(sents) == 4
    assert sents[0] == "3. janúar sl. keypti ég 64kWst rafbíl ."
    assert sents[1] == "Hann kostaði €30.000 ."
    assert sents[2] == "200.000 manns mótmæltu ."
    assert sents[3] == "Hér byrjar ný setning"

    # Test using a generator as input into split_into_sentences()
    st = (
        "3.janúar sl. keypti   ég 64kWst rafbíl. Hann kostaði € 30.000.  \n",
        "200.000 manns mótmæltu\n",
        "\n",
        "Hér byrjar ný setning\n",
    )

    def gen(s: Iterable[str]) -> Iterator[str]:
        for line in s:
            yield line

    g = t.split_into_sentences(gen(st))
    sents = list(g)
    assert len(sents) == 4
    assert sents[0] == "3. janúar sl. keypti ég 64kWst rafbíl ."
    assert sents[1] == "Hann kostaði €30.000 ."
    assert sents[2] == "200.000 manns mótmæltu"
    assert sents[3] == "Hér byrjar ný setning"

    # Test the normalize option
    s = (
        'Hún sagði: "Þú ert leiðinlegur"! Hann svaraði engu -- '
        "en hætti við ferðina.  \n"
    )
    g = t.split_into_sentences(s, normalize=True)
    sents = list(g)
    assert len(sents) == 2
    assert sents[0] == "Hún sagði : „ Þú ert leiðinlegur “ !"
    assert sents[1] == "Hann svaraði engu - - en hætti við ferðina ."
    g = t.split_into_sentences(s, normalize=False)
    sents = list(g)
    assert len(sents) == 2
    assert sents[0] == 'Hún sagði : " Þú ert leiðinlegur " !'
    assert sents[1] == "Hann svaraði engu - - en hætti við ferðina ."

    g = t.split_into_sentences(
        "Aðalsteinn Jónsson SU á leið til hafnar í "
        "Reykjavík.Flutningaskipið Selfoss kom til Reykjavíkur.Rósin sigldi með "
        "ferðamenn í hvalaskoðun."
    )
    sents = list(g)
    assert len(sents) == 3
    assert sents == [
        "Aðalsteinn Jónsson SU á leið til hafnar í Reykjavík .",
        "Flutningaskipið Selfoss kom til Reykjavíkur .",
        "Rósin sigldi með ferðamenn í hvalaskoðun .",
    ]

    g = t.split_into_sentences(
        s
        for s in [
            "Aðalsteinn Jónsson SU á leið til hafnar í ",
            "Reykjavík.Flutningaskipið Selfoss kom til Reykjavíkur.Rósin sigldi með ",
            "ferðamenn í hvalaskoðun.",
        ]
    )
    sents = list(g)
    assert len(sents) == 3
    assert sents == [
        "Aðalsteinn Jónsson SU á leið til hafnar í Reykjavík .",
        "Flutningaskipið Selfoss kom til Reykjavíkur .",
        "Rósin sigldi með ferðamenn í hvalaskoðun .",
    ]

    g = t.split_into_sentences(
        s
        for s in [
            "Aðalsteinn Jónsson SU á leið \n til hafnar í ",
            "Reykjavík.\nFlutningaskipið Selfoss \nkom til Reykjavíkur.Rósin sigldi með ",
            "ferðamenn í\nhvalaskoðun.\n\n\n",
        ]
    )
    sents = list(g)
    assert len(sents) == 3
    assert sents == [
        "Aðalsteinn Jónsson SU á leið til hafnar í Reykjavík .",
        "Flutningaskipið Selfoss kom til Reykjavíkur .",
        "Rósin sigldi með ferðamenn í hvalaskoðun .",
    ]

    g = t.split_into_sentences(
        s
        for s in [
            "Aðalsteinn Jónsson SU á leið \n til hafnar í ",
            "Reykjavík\n \t  \nFlutningaskipið Selfoss \nkom til Reykjavíkur",
            "",
            "Rósin sigldi með ",
            "ferðamenn í\nhvalaskoðun\n\n\nVigur kom með fullfermi að landi",
        ]
    )
    sents = list(g)
    assert len(sents) == 4
    assert sents == [
        "Aðalsteinn Jónsson SU á leið til hafnar í Reykjavík",
        "Flutningaskipið Selfoss kom til Reykjavíkur",
        "Rósin sigldi með ferðamenn í hvalaskoðun",
        "Vigur kom með fullfermi að landi",
    ]

    g = t.split_into_sentences("")
    sents = list(g)
    assert len(sents) == 0

    g = t.split_into_sentences("Athugum [hvort [setningin sé rétt skilin]].")
    sents = list(g)
    assert len(sents) == 1
    assert sents == ["Athugum [ hvort [ setningin sé rétt skilin ] ] ."]

    g = t.split_into_sentences("Þessi [ætti [líka að]] vera rétt skilin.")
    sents = list(g)
    assert len(sents) == 1
    assert sents == ["Þessi [ ætti [ líka að ] ] vera rétt skilin ."]

    # g = t.split_into_sentences("Þessi á [[líka að]] vera rétt skilin.")
    # sents = list(g)
    # assert len(sents) == 3
    # assert sents == [
    #     "Þessi á",
    #     "[[ líka að ]]",
    #     "vera rétt skilin ."
    # ]
    # Test onesentperline

    # Test whether indirect speech is split up
    g = t.split_into_sentences("„Er einhver þarna?“ sagði konan.")
    sents = list(g)
    assert len(sents) == 1
    assert sents == ["„ Er einhver þarna ? “ sagði konan ."]

    g = t.split_into_sentences("„Er einhver þarna?“ Maðurinn þorði varla fram.")
    sents = list(g)
    assert len(sents) == 2
    assert sents == ["„ Er einhver þarna ? “", "Maðurinn þorði varla fram ."]

    g = t.split_into_sentences("„Hún hló,“ sagði barnið.")
    sents = list(g)
    assert len(sents) == 1
    assert sents == ["„ Hún hló , “ sagði barnið ."]

    # g = t.split_into_sentences("„Hvað meinarðu??“ sagði barnið.")
    # sents = list(g)
    # assert len(sents) == 1
    # assert sents == ["„ Hvað meinarðu ?? “ sagði barnið ."]


def test_normalization() -> None:
    text, norm = get_text_and_norm('Hann sagði: "Þú ert ágæt!".')

    assert text == 'Hann sagði : " Þú ert ágæt ! " .'
    assert norm == "Hann sagði : „ Þú ert ágæt ! “ ."

    text, norm = get_text_and_norm("Hún vinnur í fjármála-og efnahagsráðuneytinu.")
    assert text == "Hún vinnur í fjármála- og efnahagsráðuneytinu ."
    assert norm == "Hún vinnur í fjármála- og efnahagsráðuneytinu ."

    text, norm = get_text_and_norm("Þetta er tyrfið...")
    assert text == "Þetta er tyrfið ..."
    assert norm == "Þetta er tyrfið …"

    text, norm = get_text_and_norm("Þetta er gaman..")
    assert text == "Þetta er gaman .."
    assert norm == "Þetta er gaman ."

    text, norm = get_text_and_norm("Þetta er hvellur.....")
    assert text == "Þetta er hvellur ....."
    assert norm == "Þetta er hvellur …"

    text, norm = get_text_and_norm("Þetta er mergjað………")
    assert text == "Þetta er mergjað ………"
    assert norm == "Þetta er mergjað …"

    text, norm = get_text_and_norm("Haldið var áfram [...] eftir langt hlé.")
    assert text == "Haldið var áfram [...] eftir langt hlé ."
    assert norm == "Haldið var áfram […] eftir langt hlé ."

    text, norm = get_text_and_norm("Þetta er tyrfið,, en við höldum áfram.")
    assert text == "Þetta er tyrfið ,, en við höldum áfram ."
    assert norm == "Þetta er tyrfið , en við höldum áfram ."

    text, norm = get_text_and_norm('Hinn svokallaði ,,Galileóhestur" hvarf.')
    assert text == 'Hinn svokallaði ,, Galileóhestur " hvarf .'
    assert norm == "Hinn svokallaði „ Galileóhestur “ hvarf ."

    text, norm = get_text_and_norm("Mars - hin rauða pláneta - skín bjart í nótt.")
    assert text == "Mars - hin rauða pláneta - skín bjart í nótt ."
    assert norm == "Mars - hin rauða pláneta - skín bjart í nótt ."

    text, norm = get_text_and_norm("Mars – hin rauða pláneta – skín bjart í nótt.")
    assert text == "Mars – hin rauða pláneta – skín bjart í nótt ."
    assert norm == "Mars - hin rauða pláneta - skín bjart í nótt ."

    text, norm = get_text_and_norm("Mars — hin rauða pláneta — skín bjart í nótt.")
    assert text == "Mars — hin rauða pláneta — skín bjart í nótt ."
    assert norm == "Mars - hin rauða pláneta - skín bjart í nótt ."

    text, norm = get_text_and_norm("Hvernig gastu gert þetta???!!!!!")
    assert text == "Hvernig gastu gert þetta ???!!!!!"
    assert norm == "Hvernig gastu gert þetta ?"

    toklist = list(t.tokenize('Hann sagði: ,,Þú ert ágæt!!??!".'))
    assert t.text_from_tokens(toklist) == 'Hann sagði : ,, Þú ert ágæt !!??! " .'
    assert t.normalized_text_from_tokens(toklist) == "Hann sagði : „ Þú ert ágæt ! “ ."

    toklist = list(t.tokenize('Hann sagði: ,,Þú ert ágæt??!?".'))
    assert t.text_from_tokens(toklist) == 'Hann sagði : ,, Þú ert ágæt ??!? " .'
    assert t.normalized_text_from_tokens(toklist) == "Hann sagði : „ Þú ert ágæt ? “ ."

    toklist = list(t.tokenize("Jón,, farðu út."))
    assert t.text_from_tokens(toklist) == "Jón ,, farðu út ."
    assert t.normalized_text_from_tokens(toklist) == "Jón , farðu út ."

    toklist = list(t.tokenize("Jón ,,farðu út."))
    assert t.text_from_tokens(toklist) == "Jón ,, farðu út ."
    assert t.normalized_text_from_tokens(toklist) == "Jón „ farðu út ."

    toklist = list(t.tokenize('Hann sagði: ,,Þú ert ágæt.....".'))
    assert t.text_from_tokens(toklist) == 'Hann sagði : ,, Þú ert ágæt ..... " .'
    assert t.normalized_text_from_tokens(toklist) == "Hann sagði : „ Þú ert ágæt … “ ."

    toklist = list(t.tokenize('Hann sagði: ,,Þú ert ágæt…..".'))
    assert t.text_from_tokens(toklist) == 'Hann sagði : ,, Þú ert ágæt ….. " .'
    assert t.normalized_text_from_tokens(toklist) == "Hann sagði : „ Þú ert ágæt … “ ."


def test_abbr_at_eos() -> None:
    """Test that 'Örn.' is not treated as an abbreviation here"""
    toklist = list(
        t.tokenize(
            "„Mér leiddist ekki,“ segir Einar Örn. Hann telur þó að "
            "sýningin líði fyrir það ástand sem hefur skapast "
            "vegna heimsfaraldursins."
        )
    )
    assert len([tok for tok in toklist if tok.kind == TOK.S_BEGIN]) == 2
    assert len([tok for tok in toklist if tok.kind == TOK.S_END]) == 2


def test_time_token() -> None:
    toklist = list(
        t.tokenize("2.55pm - Síðasta tilraun setur Knights fram klukkan hálf")
    )
    assert len(toklist) == 12
    assert toklist[-2].kind == TOK.WORD
    assert toklist[-2].txt == "hálf"
    assert toklist[-3].kind == TOK.WORD
    assert toklist[-3].txt == "klukkan"


def test_html_escapes() -> None:
    toklist = list(
        t.tokenize(
            "Ég&nbsp;fór &aacute; &lt;bömmer&gt; og bor&shy;ðaði köku.",
            replace_html_escapes=True,
        )
    )
    toklist = strip_originals(toklist)
    correct = [
        Tok(kind=11001, txt=None, val=(0, None)),
        Tok(kind=6, txt="Ég", val=None),
        Tok(kind=6, txt="fór", val=None),
        Tok(kind=6, txt="á", val=None),
        Tok(kind=1, txt="<", val=(1, "<")),
        Tok(kind=6, txt="bömmer", val=None),
        Tok(kind=1, txt=">", val=(3, ">")),
        Tok(kind=6, txt="og", val=None),
        Tok(kind=6, txt="borðaði", val=None),
        Tok(kind=6, txt="köku", val=None),
        Tok(kind=1, txt=".", val=(3, ".")),
        Tok(kind=11002, txt=None, val=None),
    ]
    assert toklist == correct
    toklist = list(
        t.tokenize(
            # En space and Em space
            "Ég&#8194;fór &aacute; &lt;bömmer&gt;&#8195;og bor&shy;ðaði köku.",
            replace_html_escapes=True,
        )
    )
    toklist = strip_originals(toklist)
    assert toklist == correct
    toklist = list(
        t.tokenize(
            "Ég fór &uacute;t og &#97;fs&#x61;kaði mig", replace_html_escapes=True
        )
    )
    toklist = strip_originals(toklist)
    correct = [
        Tok(kind=11001, txt=None, val=(0, None)),
        Tok(kind=6, txt="Ég", val=None),
        Tok(kind=6, txt="fór", val=None),
        Tok(kind=6, txt="út", val=None),
        Tok(kind=6, txt="og", val=None),
        Tok(kind=6, txt="afsakaði", val=None),
        Tok(kind=6, txt="mig", val=None),
        Tok(kind=11002, txt=None, val=None),
    ]
    assert toklist == correct


def test_one_sent_per_line() -> None:
    toklist = list(t.tokenize("Hér er hestur\nmaður beit hund", one_sent_per_line=True))
    toklist = strip_originals(toklist)

    correct = [
        Tok(kind=11001, txt=None, val=(0, None)),
        Tok(kind=6, txt="Hér", val=None),
        Tok(kind=6, txt="er", val=None),
        Tok(kind=6, txt="hestur", val=None),
        Tok(
            kind=11002, txt="", val=None
        ),  # txt is not None due to origin tracking of the newline
        Tok(kind=11001, txt=None, val=(0, None)),
        Tok(kind=6, txt="maður", val=None),
        Tok(kind=6, txt="beit", val=None),
        Tok(kind=6, txt="hund", val=None),
        Tok(kind=11002, txt=None, val=None),
    ]
    assert toklist == correct

    # Test without option
    toklist = list(
        t.tokenize("Hér er hestur\nmaður beit hund", one_sent_per_line=False)
    )
    toklist = strip_originals(toklist)

    correct = [
        Tok(kind=11001, txt=None, val=(0, None)),
        Tok(kind=6, txt="Hér", val=None),
        Tok(kind=6, txt="er", val=None),
        Tok(kind=6, txt="hestur", val=None),
        Tok(kind=6, txt="maður", val=None),
        Tok(kind=6, txt="beit", val=None),
        Tok(kind=6, txt="hund", val=None),
        Tok(kind=11002, txt=None, val=None),
    ]
    assert toklist == correct
