# -*- encoding: utf-8 -*-
"""

    test_tokenizer.py

    Tests for Tokenizer module

    Copyright(C) 2017 by Miðeind ehf.
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
from __future__ import print_function
from __future__ import unicode_literals

import tokenizer as t

TOK = t.TOK
Tok = t.Tok

def test_single_tokens():

    TEST_CASES = [
        (".", TOK.PUNCTUATION),
        (",", TOK.PUNCTUATION),
        ("!", TOK.PUNCTUATION),
        ('"', TOK.PUNCTUATION),
        ("13:45", [ Tok(TOK.TIME, "13:45", (13,45,0)) ]),
        ("17/6", [ Tok(TOK.DATE, "17/6", (0, 6, 17)) ]),
        ("17/6/2013", [ Tok(TOK.DATE, "17/6/2013", (2013, 6, 17)) ]),
        ("2013", [ Tok(TOK.YEAR, "2013", 2013) ]),
        ("213", [ Tok(TOK.NUMBER, "213", (213, None, None)) ]),
        ("2.013", [ Tok(TOK.NUMBER, "2.013", (2013, None, None)) ]),
        ("2,013", [ Tok(TOK.NUMBER, "2,013", (2.013, None, None)) ]),
        ("2.013,45", [ Tok(TOK.NUMBER, "2.013,45", (2013.45, None, None)) ]),
        ("þjóðhátíð", TOK.WORD),
        ("Þjóðhátíð", TOK.WORD),
        ("marg-ítrekað", TOK.WORD),
        ("750 þús.kr.",
            [
                Tok(TOK.NUMBER, "750", (750, None, None)),
                Tok(TOK.WORD, "þús.kr", [ ('þúsundir króna', 0, 'kvk', 'skst', 'þús.kr.', '-') ]),
                Tok(TOK.PUNCTUATION, ".", None)
            ]
        ),
        ("m.kr.",
            [
                Tok(TOK.WORD, "m.kr", [ ('milljónir króna', 0, 'kvk', 'skst', 'm.kr.', '-') ]),
                Tok(TOK.PUNCTUATION, ".", None)
            ]
        ),
        ("ma.kr.",
            [
                Tok(TOK.WORD, "ma.kr", [ ('milljarðar króna', 0, 'kk', 'skst', 'ma.kr.', '-') ]),
                Tok(TOK.PUNCTUATION, ".", None)
            ]
        ),
        ("t.d.", TOK.WORD, [ ('til dæmis', 0, 'ao', 'frasi', 't.d.', '-') ]),
        ("hr.", TOK.WORD, [ ('herra', 0, 'kk', 'skst', 'hr.', '-') ]),
        ("Hr.", TOK.WORD, [ ('herra', 0, 'kk', 'skst', 'hr.', '-') ]),
        ("o.s.frv.",
            [
                Tok(TOK.WORD, "o.s.frv", [ ('og svo framvegis', 0, 'ao', 'frasi', 'o.s.frv.', '-') ]),
                Tok(TOK.PUNCTUATION, ".", None)
            ]
        ),
        ("BSRB", TOK.WORD),
        ("stjórnskipunar- og eftirlitsnefnd", TOK.WORD),
        ("1234444", TOK.TELNO),
        ("12,3%", TOK.PERCENT),
        ("12,3 %", [ Tok(TOK.PERCENT, "12,3%", (12.3, None, None)) ]),
        ("http://www.greynir.is", TOK.URL),
        ("19/3/1977 14:56:10",
            [ Tok(TOK.TIMESTAMP, "19/3/1977 14:56:10", (1977,3,19,14,56,10)) ]
        ),
        ("$472,64", TOK.AMOUNT),
        ("€472,64", TOK.AMOUNT),
        ("fake@news.is", TOK.EMAIL)
    ]

    for test_case in TEST_CASES:
        if len(test_case) == 3:
            txt, kind, val = test_case
            c = [ Tok(kind, txt, val) ]
        elif isinstance(test_case[1], list):
            txt = test_case[0]
            c = test_case[1]
        else:
            txt, kind = test_case
            c = [ Tok(kind, txt, None) ]
        l = list(t.tokenize(txt))
        assert len(l) == len(c) + 2, repr(l)
        assert l[0].kind == TOK.S_BEGIN, repr(l[0])
        assert l[-1].kind == TOK.S_END, repr(l[-1])
        for tok, check in zip(l[1:-1], c):
            assert tok.kind == check.kind, tok.txt + ": " + repr(TOK.descr[tok.kind]) + " " + repr(TOK.descr[check.kind])
            assert tok.txt == check.txt, tok.txt + ": " + check.txt
            if check.val is not None:
                assert tok.val == check.val, repr(tok.val) + ": " + repr(check.val)

def test_sentences():

    KIND = {
        "B" : TOK.S_BEGIN,
        "E" : TOK.S_END,
        "W" : TOK.WORD,
        "P" : TOK.PUNCTUATION,
        "T" : TOK.TIME,
        "D" : TOK.DATE,
        "Y" : TOK.YEAR,
        "N" : TOK.NUMBER,
        "TEL" : TOK.TELNO,
        "PC" : TOK.PERCENT,
        "U" : TOK.URL,
        "O" : TOK.ORDINAL,
        "TS" : TOK.TIMESTAMP,
        "C" : TOK.CURRENCY,
        "A" : TOK.AMOUNT,
        "M" : TOK.EMAIL,
        "X" : TOK.UNKNOWN
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
        "W    O  W   O     W     W    W   N P Y   W    D             P E")

    test_sentence(
        "  Góðan daginn! Ég á 10.000 kr. í vasanum, €100 og $40. Gengi USD er 103,45. "
        "Í dag er 10. júlí. Klukkan er 15:40 núna. Ég fer kl. 13 niður á Hlemm o.s.frv. ",
        "B W     W     P E B W W N   W   W W      P A    W  A  P E B W W   W  N     P E "
        "B W W W  D       P E B W   W  T     W   P E B W W T     W     W W     W      P E")

    test_sentence(
        "Málið um BSRB gekk marg-ítrekað til stjórnskipunar- og eftirlitsnefndar í 10. sinn "
        "skv. XVII. kafla þann 24. september 2015. Ál-verið notar 60 MWst á ári.",
        "B W   W  W    W    W            W   W                                   W O   W "
        "W    O     W     W    D                 P E B W P W W    N  W    W W  P E")

    test_sentence(
        "Ég er t.d. með tölvupóstfangið fake@news.com, veffangið "
        "http://greynir.is, og síma 6638999. Hann gaf mér 1000 kr. Ég keypti mér 1/2 kaffi.",
        "B W W W    W   W               M            P W "
        "U                P W  W    TEL    P E B W W  W   N    W P E B W W   W   N   W    P E")

    test_sentence(
        "Hann starfaði við stofnunina árin 1944-50.",
        "B W  W        W   W          W    Y   P N P")


def test_correct_spaces():
    s = t.correct_spaces("Frétt \n  dagsins:Jón\t ,Friðgeir og Páll ! 100,8  /  2  =   50.4")
    assert s == 'Frétt dagsins: Jón, Friðgeir og Páll! 100,8/2 = 50.4'
    s = t.correct_spaces("Hitinn    var\n-7,4 \t gráður en   álverðið var  \n $10,348.55.")
    assert s == 'Hitinn var -7,4 gráður en álverðið var $10,348.55.'
    s = t.correct_spaces("\n Breytingin var   +4,10 þingmenn \t  en dollarinn er nú á €1,3455  .")
    assert s == 'Breytingin var +4,10 þingmenn en dollarinn er nú á €1,3455.'
    s = t.correct_spaces("Jón- sem var formaður — mótmælti málinu.")
    assert s == 'Jón-sem var formaður — mótmælti málinu.'


if __name__ == "__main__":

    test_single_tokens()
    test_sentences()
    test_correct_spaces()
