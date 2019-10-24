# -*- encoding: utf-8 -*-
"""

    test_tokenizer.py

    Tests for Tokenizer module

    Copyright(C) 2019 by Miðeind ehf.
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
import tokenizer as t


TOK = t.TOK
Tok = t.Tok


def test_single_tokens():

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
            ]
        ),
        ("kl. 13:45", [Tok(TOK.TIME, "kl. 13:45", (13, 45, 0))]),
        ("klukkan 13:45", [Tok(TOK.TIME, "klukkan 13:45", (13, 45, 0))]),
        ("Klukkan 13:45", [Tok(TOK.TIME, "Klukkan 13:45", (13, 45, 0))]),
        ("hálftólf", [Tok(TOK.TIME, "hálftólf", (11, 30, 0))]),
        ("kl. hálfátta", [Tok(TOK.TIME, "kl. hálfátta", (7, 30, 0))]),
        ("klukkan þrjú", [Tok(TOK.TIME, "klukkan þrjú", (3, 00, 0))]),
        ("17/6", [Tok(TOK.DATEREL, "17/6", (0, 6, 17))]),
        (
            "17/60",
            [
                Tok(TOK.NUMBER, "17", (17, None, None)),
                Tok(TOK.PUNCTUATION, "/", None),
                Tok(TOK.NUMBER, "60", (60, None, None)),
            ]
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
            ]
        ),
        ("sautjánda júní", [Tok(TOK.DATEREL, "sautjánda júní", (0, 6, 17))]),
        (
            "sautjánda júní 1811",
            [Tok(TOK.DATEABS, "sautjánda júní 1811", (1811, 6, 17))],
        ),
        (
            "Sautjánda júní árið 1811",
            [Tok(TOK.DATEABS, "Sautjánda júní árið 1811", (1811, 6, 17))],
        ),
        (
            "Fimmtánda mars árið 44 f.Kr.",
            [
                Tok(TOK.DATEABS, "Fimmtánda mars árið 44 f.Kr", (-44, 3, 15)),
                Tok(TOK.PUNCTUATION, ".", None),
            ],
        ),
        ("17/6/2013", [Tok(TOK.DATEABS, "17/6/2013", (2013, 6, 17))]),
        (
            "17/6/20130",
            [
                Tok(TOK.DATEREL, "17/6", (0, 6, 17)),
                Tok(TOK.PUNCTUATION, "/", None),
                Tok(TOK.NUMBER, "20130", (20130, None, None)),
            ]
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
            ]
        ),
        ("2013", [Tok(TOK.YEAR, "2013", 2013)]),
        ("20130", [Tok(TOK.NUMBER, "20130", (20130, None, None))]),
        (
            "874 e.Kr.",
            [Tok(TOK.YEAR, "874 e.Kr", 874), Tok(TOK.PUNCTUATION, ".", None)],
        ),
        (
            "2013 f.Kr.",
            [Tok(TOK.YEAR, "2013 f.Kr", -2013), Tok(TOK.PUNCTUATION, ".", None)],
        ),
        ("árið 2013", [Tok(TOK.YEAR, "árið 2013", 2013)]),
        ("árinu 874", [Tok(TOK.YEAR, "árinu 874", 874)]),
        ("ársins 2013", [Tok(TOK.YEAR, "ársins 2013", 2013)]),
        (
            "ársins 320 f.Kr.",
            [Tok(TOK.YEAR, "ársins 320 f.Kr", -320), Tok(TOK.PUNCTUATION, ".", None)],
        ),
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
            ]
        ),
        ("2,013.45", [Tok(TOK.NUMBER, "2,013.45", (2013.45, None, None))]),
        (
            "2,0134.45",
            [
                Tok(TOK.NUMBER, "2", (2, None, None)),
                Tok(TOK.PUNCTUATION, ",", None),
                Tok(TOK.NUMBER, "0134.45", (134.45, None, None)),
            ]
        ),
        ("1/2", [Tok(TOK.NUMBER, "1/2", (0.5, None, None))]),
        ("1/20", [Tok(TOK.DATEREL, "1/20", (0, 1, 20))]),
        (
            "1/37",
            [
                Tok(TOK.NUMBER, "1", (1, None, None)),
                Tok(TOK.PUNCTUATION, "/", None),
                Tok(TOK.NUMBER, "37", (37, None, None)),
            ]
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
        (
            "750 þús.kr.",
            [
                Tok(TOK.AMOUNT, "750 þús.kr", (750e3, "ISK", None, None)),
                Tok(TOK.PUNCTUATION, ".", None),
            ],
        ),
        (
            "750 þús. kr.",
            [
                Tok(TOK.AMOUNT, "750 þús. kr", (750e3, "ISK", None, None)),
                Tok(TOK.PUNCTUATION, ".", None),
            ],
        ),
        (
            "750 þús. ISK.",
            [
                Tok(TOK.AMOUNT, "750 þús. ISK", (750e3, "ISK", None, None)),
                Tok(TOK.PUNCTUATION, ".", None),
            ],
        ),
        (
            "2,7 mrð. USD.",
            [
                Tok(TOK.AMOUNT, "2,7 mrð. USD", (2.7e9, "USD", None, None)),
                Tok(TOK.PUNCTUATION, ".", None),
            ],
        ),
        (
            "m.kr.",
            [
                Tok(
                    TOK.WORD,
                    "m.kr",
                    [("milljónir króna", 0, "kvk", "skst", "m.kr.", "-")],
                ),
                Tok(TOK.PUNCTUATION, ".", None),
            ],
        ),
        (
            "ma.kr.",
            [
                Tok(
                    TOK.WORD,
                    "ma.kr",
                    [("milljarðar króna", 0, "kk", "skst", "ma.kr.", "-")],
                ),
                Tok(TOK.PUNCTUATION, ".", None),
            ],
        ),
        (
            "30,7 mö.kr.",
            [
                Tok(TOK.AMOUNT, "30,7 mö.kr", (30.7e9, "ISK", None, None)),
                Tok(TOK.PUNCTUATION, ".", None),
            ],
        ),
        ("t.d.", TOK.WORD, [("til dæmis", 0, "ao", "frasi", "t.d.", "-")]),
        ("hr.", TOK.WORD, [("herra", 0, "kk", "skst", "hr.", "-")]),
        (
            "dags. 10/7",
            [
                Tok(TOK.WORD, "dags.", [("dagsetja", 0, "so", "skst", "dags.", "-")]),
                Tok(TOK.DATEREL, "10/7", (0, 7, 10)),
            ],
        ),
        ("Hr.", TOK.WORD, [("herra", 0, "kk", "skst", "hr.", "-")]),
        (
            "nk.",
            [
                Tok(TOK.WORD, "nk", [("næstkomandi", 0, "lo", "skst", "nk.", "-")]),
                Tok(TOK.PUNCTUATION, ".", None),
            ],
        ),
        (
            "sl.",
            [
                Tok(TOK.WORD, "sl", [("síðastliðinn", 0, "lo", "skst", "sl.", "-")]),
                Tok(TOK.PUNCTUATION, ".", None),
            ],
        ),
        (
            "o.s.frv.",
            [
                Tok(
                    TOK.WORD,
                    "o.s.frv",
                    [("og svo framvegis", 0, "ao", "frasi", "o.s.frv.", "-")],
                ),
                Tok(TOK.PUNCTUATION, ".", None),
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
        ("9000000", TOK.NUMBER),
        ("1234567", TOK.NUMBER),
        ("525-4764", [Tok(TOK.TELNO, "525-4764", "525-4764")]),
        ("4204200", [Tok(TOK.TELNO, "4204200", "420-4200")]),
        ("699 2422", [Tok(TOK.TELNO, "699 2422", "699-2422")]),
        ("12,3%", TOK.PERCENT),
        ("12,3 %", [Tok(TOK.PERCENT, "12,3%", (12.3, None, None))]),
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

        ("fake@news.is", TOK.EMAIL),
        ("jon.jonsson.99@netfang.is", TOK.EMAIL),
        ("valid@my-domain.reallylongtld", TOK.EMAIL),
        ("7a", [Tok(TOK.NUMWLETTER, "7a", (7, "a"))]),
        ("33B", [Tok(TOK.NUMWLETTER, "33B", (33, "B"))]),
        ("1129c", [Tok(TOK.NUMWLETTER, "1129c", (1129, "c"))]),
        ("7l", [Tok(TOK.MEASUREMENT, "7 l", ("m³", 0.007))]),
        ("17 ltr", [Tok(TOK.MEASUREMENT, "17 ltr", ("m³", 17.0e-3))]),
        ("150m", [Tok(TOK.MEASUREMENT, "150 m", ("m", 150))]),
        ("220V", [Tok(TOK.MEASUREMENT, "220 V", ("V", 220))]),
        ("11A", [Tok(TOK.MEASUREMENT, "11 A", ("A", 11))]),
        ("100 mm", [Tok(TOK.MEASUREMENT, "100 mm", ("m", 0.1))]),
        ("30,7°C", [Tok(TOK.MEASUREMENT, "30,7 °C", ("K", 273.15 + 30.7))]),
        ("30,7 °C", [Tok(TOK.MEASUREMENT, "30,7 °C", ("K", 273.15 + 30.7))]),
        ("30,7° C", [Tok(TOK.MEASUREMENT, "30,7 °C", ("K", 273.15 + 30.7))]),
        ("30,7 ° C", [Tok(TOK.MEASUREMENT, "30,7 °C", ("K", 273.15 + 30.7))]),
        ("32°F", [Tok(TOK.MEASUREMENT, "32 °F", ("K", 273.15))]),
        ("32 °F", [Tok(TOK.MEASUREMENT, "32 °F", ("K", 273.15))]),
        ("32° F", [Tok(TOK.MEASUREMENT, "32 °F", ("K", 273.15))]),
        ("32 ° F", [Tok(TOK.MEASUREMENT, "32 °F", ("K", 273.15))]),
        ("180°", [Tok(TOK.MEASUREMENT, "180°", ("°", 180))]),
        ("180 °", [Tok(TOK.MEASUREMENT, "180°", ("°", 180))]),
        ("6.500 kg", [Tok(TOK.MEASUREMENT, "6.500 kg", ("g", 6.5e6))]),
        ("690 MW", [Tok(TOK.MEASUREMENT, "690 MW", ("W", 690e6))]),
        ("1800 MWst", [Tok(TOK.MEASUREMENT, "1800 MWst", ("J", 6480e9))]),
        ("1976kWst", [Tok(TOK.MEASUREMENT, "1976 kWst", ("J", 7113.6e6))]),
    ]

    TEST_CASES_KLUDGY_MODIFY = [
        ("1sti", [Tok(TOK.WORD, "fyrsti", None)]),
        ("4ðu", [Tok(TOK.WORD, "fjórðu", None)]),
        ("2svar", [Tok(TOK.WORD, "tvisvar", None)]),
        ("4ra", [Tok(TOK.WORD, "fjögurra", None)]),
    ]

    TEST_CASES_KLUDGY_TRANSLATE = [
        ("1sti", [Tok(TOK.ORDINAL, "1sti", 1)]),
        ("4ðu", [Tok(TOK.ORDINAL, "4ðu", 4)]),
        ("2svar", [Tok(TOK.WORD, "2svar", None)]),
        ("4ra", [Tok(TOK.WORD, "4ra", None)]),
    ]

    TEST_CASES_CONVERT_TELNOS = [
        ("525-4764", TOK.TELNO),
        ("4204200", [Tok(TOK.TELNO, "4204200", "420-4200")]),
        ("699 2422", [Tok(TOK.TELNO, "699 2422", "699-2422")]),
        ("699 2012", [Tok(TOK.TELNO, "699 2012", "699-2012")]),
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

    def run_test(test_cases, **options):
        for test_case in test_cases:
            if len(test_case) == 3:
                txt, kind, val = test_case
                c = [Tok(kind, txt, val)]
            elif isinstance(test_case[1], list):
                txt = test_case[0]
                c = test_case[1]
            else:
                txt, kind = test_case
                c = [Tok(kind, txt, None)]
            l = list(t.tokenize(txt, **options))
            assert len(l) == len(c) + 2, repr(l)
            assert l[0].kind == TOK.S_BEGIN, repr(l[0])
            assert l[-1].kind == TOK.S_END, repr(l[-1])
            for tok, check in zip(l[1:-1], c):
                assert tok.kind == check.kind, (
                    tok.txt
                    + ": "
                    + repr(TOK.descr[tok.kind])
                    + " "
                    + repr(TOK.descr[check.kind])
                )
                assert tok.txt == check.txt, tok.txt + ": " + check.txt
                if check.val is not None:
                    assert tok.val == check.val, repr(tok.val) + ": " + repr(check.val)

    run_test(TEST_CASES)
    run_test(
        TEST_CASES_KLUDGY_MODIFY,
        handle_kludgy_ordinals=t.KLUDGY_ORDINALS_MODIFY
    )
    run_test(
        TEST_CASES_KLUDGY_TRANSLATE,
        handle_kludgy_ordinals=t.KLUDGY_ORDINALS_TRANSLATE
    )
    run_test(TEST_CASES_CONVERT_TELNOS)
    run_test(
        TEST_CASES_CONVERT_NUMBERS,
        convert_numbers=True
    )


def test_sentences():

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
        "X": TOK.UNKNOWN,
    }

    def test_sentence(text, expected):

        exp = expected.split()
        s = t.tokenize(text)

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
        "B W      W   W     W   W "
        "W    O  W   O     W     W    W   N P Y   W    DA            P E",
    )

    test_sentence(
        "  Góðan daginn! Ég á 10.000 kr. í vasanum, €100 og $40.Gengi USD er 103,45. "
        "Í dag er 10. júlí. Klukkan er 15:40 núna.Ég fer kl. 13 niður á Hlemm o.s.frv. ",
        "B W     W     P E B W W A       W W      P A    W  A  P E B W W   W  N     P E "
        "B W W W  DR      P E B W   W  T     W   P E B W W T     W     W W     W      P E",
    )

    test_sentence(
        "Jæja, bjór í Bretlandi kominn upp í £4.29 (ISK 652).  Dýrt!     Í Japan er hann bara ¥600.",
        "B W P W    W W         W      W   W A    P A   P P E  B W P E B W W     W  W    W    A   P E",
    )

    test_sentence(
        "Almennt verð er krónur 9.900,- en kr. 8.000,- fyrir félagsmenn. Maður borgar 99 kr. 10 sinnum. "
        "USD900 fyrir Bandaríkjamenn en 700 EUR fyrir Þjóðverja. Ég hef spilað RISK 100 sinnum.",
        "B W     W    W  A          P P W  A       P P W     W        P E B  W W      A      N  W   P E "
        "B A    W     W              W  A       W     W      P E B W W  W      W    N   W    P E"
    )

    # '\u00AD': soft hyphen
    # '\u200B': zero-width space
    # '\uFEFF': zero-width non-breaking space
    test_sentence(
        "Lands\u00ADbank\u00ADinn er í 98\u200B,2 pró\u00ADsent eigu\u200B íslenska rík\uFEFFis\u00ADins.",
        "B W                      W  W PC                       W          W        W                  P E",
    )

    test_sentence(
        "Málið um BSRB gekk marg-ítrekað til stjórnskipunar- og eftirlitsnefndar í 10. sinn "
        "skv. XVII. kafla þann 24. september 2015 nk. Ál-verið notar 60 MWst á ári.",
        "B W   W  W    W    W            W   W                                   W O   W "
        "W    O     W     W    DA                 W P E B W P W W    ME      W W  P E",
    )

    test_sentence(
        "Ég er t.d. með tölvupóstfangið fake@news.com, vefföngin "
        "http://greynir.is og https://greynir.is, og síma 6638999. Hann gaf mér 1000 kr. Ég keypti mér 1/2 kaffi. "
        "Það er hægt að ná í mig í s 623 7892, eða vinnusíma, 7227979 eða eitthvað.",
        "B W W W    W   W               M            P W "
        "U                 W  U             P W  W    TEL    P E B W W  W   A      P E B W W   W   N   W    P E "
        "B W W  W    W  W  W W   W W        TEL     P W   W        P  TEL     W   W P E"
    )

    test_sentence(
        "Þetta voru 300 1000 kílóa pokar, og 4000 500 kílóa pokar. "
        "Einnig 932 800 kílóa pokar, svo og 177 4455 millilítra skammtar.",
        "B W   W    N   N    W     W    P W  N    N   W     W    P E "
        "B W    N   N   W     W    P W   W  N   N    W          W       P"
    )

    test_sentence(
        "Skoðaðu vörunúmerin 000-1224 eða 121-2233. Hafðu síðan samband í síma 692 2073. "
        "Þeir voru 313 2012 en 916 árið 2013.",
        "B W     W           N  P N   W   N  P N P E B W  W     W       W W    TEL P E "
        "B W  W    N   Y    W  N    Y P E"
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
        "W    DA                           W  W     W        P E",
    )

    test_sentence(
        "1.030 hPa lægð gengur yfir landið árið 2019 e.Kr. Jógúrtin inniheldur 80 kcal.",
        "B ME      W    W      W    W      Y             P E B W    W          ME     P E",
    )

    test_sentence(
        "Maður var lagður inn á deild 33C eftir handtöku á Bárugötu 14a þann nítjánda júlí 2016.",
        "B W   W   W      W   W W     NL  W     W        W W        NL  W    DA                P E",
    )

    test_sentence(
        "Þessir 10Milljón vírar með 20A straum kostuðu 3000ISK og voru geymdir á Hagamel á 2hæð.",
        "B W    N         W     W   ME  W      W       A       W  W    W       W W       W N W P E",
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
        "B    W W ME    W  W     W  N P N W       W  W    W P E B W       W N P E B W W  N P W    N P E",
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
        "B W    W       W         W           W   W      W                                                  W    DA         P E",
    )

    test_sentence(
        "#MeToo-byltingin er til staðar á Íslandsmóti #1. #12stig í Eurovision en #égerekkiaðfílaþað! #ruv50.",
        "B HT  P W        W  W   W      W W         O P E B HT    W W          W  HT              P E B HT P E",
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
        "B W   W         W   W W    W  W  W      W W P E B W  W    W W   W  W    W W P E B W W P E",
    )

    test_sentence(
        "Ég vildi [...] fara út. [...] Hann sá mig.",
        "B W W    P     W    W P P     E B W W W  P E",
    )


def test_unicode():
    """ Test composite Unicode characters, where a glyph has two code points """
    # Mask away Python 2/3 difference
    if sys.version_info >= (3, 0):
        unicode_chr = lambda c: chr(c)
    else:
        unicode_chr = lambda c: unichr(c)
    ACUTE = unicode_chr(769)
    UMLAUT = unicode_chr(776)
    sent = (
        "Ko" + UMLAUT + "rfuboltamaðurinn og KR-ingurinn Kristo" + ACUTE + "fer Acox "
        "heldur a" + ACUTE + " vit ævinty" + ACUTE + "ranna."
    )
    tokens = list(t.tokenize(sent))
    assert tokens[1].txt == "Körfuboltamaðurinn"
    assert tokens[6].txt == "Kristófer"
    assert tokens[9].txt == "á"
    assert tokens[11].txt == "ævintýranna"


def test_correction():
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
            """Hann sagði: Þú ert ‚fífl‘! Hringdu í 7771234."""
        ),
        (
            """Hann sagði: Þú ert (´fífl´)! Ég mótmælti því.""",
            """Hann sagði: Þú ert (´fífl‘)! Ég mótmælti því.""",  # !!!
        ),
        (
            """Hann "gaf" mér 10,780.65 dollara.""",
            """Hann „gaf“ mér 10,780.65 dollara."""
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
            """Hann „gaf“ mér 10.780,65 dollara."""
        ),
        (
            """Hann "gaf" mér €10,780.65.""",
            """Hann „gaf“ mér €10.780,65."""
        ),
        (
            """Hann "gaf" mér €10.780,65.""",
            """Hann „gaf“ mér €10.780,65.""",
        ),
    ]
    for sent, correct in SENT:
        s = t.tokenize(sent)
        txt = t.correct_spaces(" ".join(token.txt for token in s if token.txt))
        assert txt == correct
    for sent, correct in SENT_KLUDGY_ORDINALS_MODIFY:
        s = t.tokenize(sent, handle_kludgy_ordinals=t.KLUDGY_ORDINALS_MODIFY)
        txt = t.correct_spaces(" ".join(token.txt for token in s if token.txt))
        assert txt == correct
    for sent, correct in SENT_KLUDGY_ORDINALS_TRANSLATE:
        s = t.tokenize(sent, handle_kludgy_ordinals=t.KLUDGY_ORDINALS_TRANSLATE)
        txt = t.correct_spaces(" ".join(token.txt for token in s if token.txt))
        assert txt == correct
    for sent, correct in SENT_CONVERT_NUMBERS:
        s = t.tokenize(sent, convert_numbers=True)
        txt = t.correct_spaces(" ".join(token.txt for token in s if token.txt))
        assert txt == correct


def test_correct_spaces():
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
    assert s == "Það á að geyma mjólkina við 20±3° C"


def test_abbrev():
    tokens = list(t.tokenize("Ég las fréttina um IBM t.d. á Mbl."))
    assert tokens == [
        Tok(kind=TOK.S_BEGIN, txt=None, val=(0, None)),
        Tok(kind=TOK.WORD, txt="Ég", val=None),
        Tok(kind=TOK.WORD, txt="las", val=None),
        Tok(kind=TOK.WORD, txt="fréttina", val=None),
        Tok(kind=TOK.WORD, txt="um", val=None),
        Tok(
            kind=TOK.WORD,
            txt="IBM",
            val=[("International Business Machines", 0, "hk", "skst", "IBM", "-")],
        ),
        Tok(
            kind=TOK.WORD,
            txt="t.d.",
            val=[("til dæmis", 0, "ao", "frasi", "t.d.", "-")],
        ),
        Tok(kind=TOK.WORD, txt="á", val=None),
        Tok(
            kind=TOK.WORD,
            txt="Mbl",
            val=[("Morgunblaðið", 0, "hk", "skst", "Mbl.", "-")],
        ),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=3),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]


def test_overlap():
    # Make sure that there is no overlap between the punctuation sets
    assert not(
        set(t.definitions.LEFT_PUNCTUATION)
        & set(t.definitions.RIGHT_PUNCTUATION)
        & set(t.definitions.CENTER_PUNCTUATION)
        & set(t.definitions.NONE_PUNCTUATION)
    )


if __name__ == "__main__":

    test_single_tokens()
    test_sentences()
    test_correct_spaces()
    test_correction()
    test_abbrev()
    test_overlap()
