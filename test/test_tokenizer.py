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
        ("kl. 13:45", [Tok(TOK.TIME, "kl. 13:45", (13, 45, 0))]),
        ("klukkan 13:45", [Tok(TOK.TIME, "klukkan 13:45", (13, 45, 0))]),
        ("Klukkan 13:45", [Tok(TOK.TIME, "Klukkan 13:45", (13, 45, 0))]),
        ("hálftólf", [Tok(TOK.TIME, "hálftólf", (11, 30, 0))]),
        ("kl. hálfátta", [Tok(TOK.TIME, "kl. hálfátta", (7, 30, 0))]),
        ("klukkan þrjú", [Tok(TOK.TIME, "klukkan þrjú", (3, 00, 0))]),
        ("17/6", [Tok(TOK.DATEREL, "17/6", (0, 6, 17))]),
        ("3. maí", [Tok(TOK.DATEREL, "3. maí", (0, 5, 3))]),
        ("Ágúst", TOK.WORD), # Not month name if capitalized
        ("13. ágúst", [Tok(TOK.DATEREL, "13. ágúst", (0, 8, 13))]),
        ("nóvember 1918", [Tok(TOK.DATEREL, "nóvember 1918", (1918, 11, 0))]),
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
        ("2013", [Tok(TOK.YEAR, "2013", 2013)]),
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
        ("2,013.45", [Tok(TOK.NUMBER, "2.013,45", (2013.45, None, None))]),
        ("1/2", [Tok(TOK.NUMBER, "1/2", (0.5, None, None))]),
        ("1/4", [Tok(TOK.NUMBER, "1/4", (0.25, None, None))]),
        ("¼", [Tok(TOK.NUMBER, "¼", (0.25, None, None))]),
        ("2⅞", [Tok(TOK.NUMBER, "2⅞", (2.875, None, None))]),
        ("33⅗", [Tok(TOK.NUMBER, "33⅗", (33.6, None, None))]),
        ("1sti", [Tok(TOK.WORD, "fyrsti", None)]),
        ("4ðu", [Tok(TOK.WORD, "fjórðu", None)]),
        ("2svar", [Tok(TOK.WORD, "tvisvar", None)]),
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
        ("mbl.is", TOK.WORD),
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
        ("123-4444", TOK.TELNO),
        ("1234444", [Tok(TOK.TELNO, "123-4444", None)]),
        ("12,3%", TOK.PERCENT),
        ("12,3 %", [Tok(TOK.PERCENT, "12,3%", (12.3, None, None))]),
        ("http://www.greynir.is", TOK.URL),
        ("https://www.greynir.is", TOK.URL),
        ("www.greynir.is", TOK.URL),
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
        ("$472,64", TOK.AMOUNT),
        ("€472,64", TOK.AMOUNT),
        ("$1.472,64", TOK.AMOUNT),
        ("€3.472,64", TOK.AMOUNT),
        ("£1.922", TOK.AMOUNT),
        ("¥212,11", TOK.AMOUNT),
        ("$1,472.64", [Tok(TOK.AMOUNT, "$1.472,64", (1472.64, "USD", None, None))]),
        ("€3,472.64", [Tok(TOK.AMOUNT, "€3.472,64", (3472.64, "EUR", None, None))]),
        ("£5,199.99", [Tok(TOK.AMOUNT, "£5.199,99", (5199.99, "GBP", None, None))]),
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

    for test_case in TEST_CASES:
        if len(test_case) == 3:
            txt, kind, val = test_case
            c = [Tok(kind, txt, val)]
        elif isinstance(test_case[1], list):
            txt = test_case[0]
            c = test_case[1]
        else:
            txt, kind = test_case
            c = [Tok(kind, txt, None)]
        l = list(t.tokenize(txt))
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
        "X": TOK.UNKNOWN,
    }

    def test_sentence(text, expected):

        exp = expected.split()
        s = t.tokenize(text)

        for token, e in zip(s, exp):
            assert e in KIND
            ekind = KIND[e]
            assert token.kind == ekind

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
        "B W P W    W W         W      W   W A    P W N P P E  B W P E B W W     W  W    W    A   P E",
    )

    # '\u00AD': soft hyphen
    # '\u200B': zero-width space
    # '\uFEFF': zero-width non-breaking space
    test_sentence(
        "Lands\u00ADbank\u00ADinn er í 98\u200B,2 pró\u00ADsent eigu\u200B íslenska rík\uFEFFis\u00ADins.",
        "B W                      W  W PC                       W          W        W                  P E"
    )

    test_sentence(
        "Málið um BSRB gekk marg-ítrekað til stjórnskipunar- og eftirlitsnefndar í 10. sinn "
        "skv. XVII. kafla þann 24. september 2015 nk. Ál-verið notar 60 MWst á ári.",
        "B W   W  W    W    W            W   W                                   W O   W "
        "W    O     W     W    DA                 W P E B W P W W    ME      W W  P E",
    )

    test_sentence(
        "Ég er t.d. með tölvupóstfangið fake@news.com, vefföngin "
        "http://greynir.is og www.greynir.is, og síma 6638999. Hann gaf mér 1000 kr. Ég keypti mér 1/2 kaffi.",
        "B W W W    W   W               M            P W "
        "U                 W  U             P W  W    TEL    P E B W W  W   A      P E B W W   W   N   W    P E",
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
        "Ágúst bjó á hæð númer 13. Ágúst kunni vel við það, enda var 12. ágúst. ÞAÐ VAR 12. ÁGÚST!",
        "B   W W   W W   W    N P E B W     W     W   W   W P  W    W   DR  P E B W W   DR      P E",
    )

    test_sentence(
        "Þórdís Kolbrún Reykfjörð Gylfadóttir var skipuð dómsmála-, ferðamála- og iðnaðarráðherra þann 12. mars 2019.",
        "B W    W       W         W           W   W      W                                        W    DA           P E"
    )

    test_sentence(
        "Þórdís Kolbrún Reykfjörð Gylfadóttir var skipuð viðskipta- dómsmála- ferðamála- og iðnaðarráðherra þann 12. mars 2019.",
        "B W    W       W         W           W   W      W                                       W    DA           P E"
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
            """Hann sagði: ‚Þú ert fífl‘! Farðu í þriðja sinn.""",
        ),
        (
            """Hann sagði: Þú ert ´fífl´! Hringdu í 7771234.""",
            """Hann sagði: Þú ert ‚fífl‘! Hringdu í 777-1234.""",
        ),
        (
            """Hann sagði: Þú ert (´fífl´)! Ég mótmælti því.""",
            """Hann sagði: Þú ert (´fífl‘)! Ég mótmælti því.""",  # !!!
        ),
        (
            """Hann "gaf" mér 10,780.65 dollara.""",
            """Hann „gaf“ mér 10.780,65 dollara.""",
        ),
    ]
    for sent, correct in SENT:
        s = t.tokenize(sent)
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
    tokens = list(t.tokenize("Ég las fréttina um IBM t.d. á mbl.is."))
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
            txt="mbl.is",
            val=[("mbl.is", 0, "hk", "skst", "mbl.is", "-")],
        ),
        Tok(kind=TOK.PUNCTUATION, txt=".", val=3),
        Tok(kind=TOK.S_END, txt=None, val=None),
    ]


if __name__ == "__main__":

    test_single_tokens()
    test_sentences()
    test_correct_spaces()
    test_correction()
    test_abbrev()
