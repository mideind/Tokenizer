---------
Tokenizer
---------

Tokenizer tokenizes Icelandic text. It converts Python text strings
to streams of token objects, where each token object is a separate word, punctuation sign,
number/amount, date, e-mail, URL/URI, etc. The tokenizer takes care of corner cases such
as abbreviations and dates in the middle of sentences.

To use::

	from tokenizer import tokenize, TOK

	for t in tokenize(
		"Málinu var vísað til stjórnskipunar- og eftirlitsnefndar "
		"skv. 3. gr. XVII. kafla laga nr. 10/2007 þann 3. janúar 2010."):

		print("{0}: '{1}' {2}".format(
			TOK.descr[t.kind],
			t.txt,
			t.val or "")
		)

Output::

	[TBD]


Documentation
-------------

Each token object is a simple named tuple with three
components: (kind, txt, val).

The kind field contains one of the following integer constants::

