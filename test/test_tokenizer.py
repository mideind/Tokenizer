"""

    test.py

    Tester for tokenizer.py

    Copyright(C) 2017 by Miðeind ehf.

"""

import tokenizer as t

TOK = t.TOK

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

print("Start of test")

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

s = t.tokenize("Góðan daginn! Ég á 10.000 kr. í vasanum, €100 og $40. Gengi USD er 103,45. "
	"Í dag er 10. júlí. Klukkan er 15:40 núna. Ég fer kl. 13 niður á Hlemm o.s.frv. ")

for tok in s:
    print(tok)

s = t.tokenize("Málið um BSRB gekk marg-ítrekað til stjórnskipunar- og eftirlitsnefndar í 10. sinn "
	"skv. XVII. kafla þann 24. september 2015. Ál-verið notar 60 MWst á ári.")

for tok in s:
    print(tok)

s = t.tokenize("Ég er t.d. með tölvupóstfangið fake@news.com, veffangið "
	"http://greynir.is, og síma 6638999. Hann gaf mér 1000 kr. Ég keypti mér 1/2 kaffi.")

for tok in s:
    print(tok)

