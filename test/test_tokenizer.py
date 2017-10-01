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

def test_single_tokens():

	TEST_CASES = [
		(".", TOK.PUNCTUATION),
		(",", TOK.PUNCTUATION),
		("!", TOK.PUNCTUATION),
		('"', TOK.PUNCTUATION),
		("13:45", TOK.TIME),
		("17/6", TOK.DATE),
		("17/6/2013", TOK.DATE),
		("2013", TOK.YEAR),
		("213", TOK.NUMBER),
		("2.013", TOK.NUMBER),
		("2,013", TOK.NUMBER),
		("2.013,00", TOK.NUMBER),
		("þjóðhátíð", TOK.WORD),
		("Þjóðhátíð", TOK.WORD),
		("marg-ítrekað", TOK.WORD),
		("t.d.", TOK.WORD, "til dæmis"),
		("hr.", TOK.WORD, "herra"),
		("Hr.", TOK.WORD, "herra"),
		("BSRB", TOK.WORD),
		("stjórnskipunar- og eftirlitsnefnd", TOK.WORD),
		("1234444", TOK.TELNO),
		("12,3%", TOK.PERCENT),
		("12,3 %", TOK.PERCENT, "12,3%"),
		("http://www.greynir.is", TOK.URL),
		("19/3/1977 14:56:10", TOK.TIMESTAMP),
		("$472,64", TOK.AMOUNT),
		("€472,64", TOK.AMOUNT),
		("fake@news.is", TOK.EMAIL)
	]

	for test_case in TEST_CASES:
		if len(test_case) == 3:
			txt, kind, lit = test_case
		else:
			txt, kind = test_case
			lit = txt
		s = t.tokenize(txt)
		l = list(s)
		assert len(l) == 3, repr(l)
		assert l[0].kind == TOK.S_BEGIN, repr(l[0])
		assert l[2].kind == TOK.S_END, repr(l[2])
		tok = l[1]
		assert tok.kind == kind, tok.txt + ": " + repr(TOK.descr[tok.kind]) + " " + repr(TOK.descr[kind])
		if tok.kind == TOK.WORD and tok.val:
			assert tok.txt == txt
			assert tok.val == lit, repr(tok.val) + " " + repr(lit)
		else:
			assert tok.txt == lit, repr(tok.txt) + " " + repr(lit)

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


if __name__ == "__main__":

	test_single_tokens()
	test_sentences()
