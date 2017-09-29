---------
Tokenizer
---------

Tokenizer tokenizes Icelandic text. It converts Python text strings
to streams of token objects, where each token object is a separate word, punctuation sign,
number/amount, date, e-mail, URL/URI, etc. The tokenizer takes care of corner cases such
as abbreviations and dates in the middle of sentences.

Tokenizer is derived from a corresponding module in the `Greynir project <https://greynir.is>`_
(GitHub repository `here <https://github.com/vthorsteinsson/Reynir>`_), by the same author.
Note that Tokenizer is licensed under the MIT license while Greynir is licensed under GPLv3.

To install::

	pip install tokenizer

To use::

	from tokenizer import tokenize, TOK

	text = "Málinu var vísað til stjórnskipunar- og eftirlitsnefndar "
		"skv. 3. gr. XVII. kafla laga nr. 10/2007 þann 3. janúar 2010."

	for token in tokenize(text):

		print("{0}: '{1}' {2}".format(
			TOK.descr[token.kind],
			token.txt or "-",
			token.val or "")
		)

Output::

	BEGIN SENT: '-' (0, None)
	WORD: 'Málinu'
	WORD: 'var'
	WORD: 'vísað'
	WORD: 'til'
	WORD: 'stjórnskipunar- og eftirlitsnefndar'
	WORD: 'skv.' samkvæmt
	ORDINAL: '3.' 3
	WORD: 'gr.' grein
	ORDINAL: 'XVII.' 17
	WORD: 'kafla'
	WORD: 'laga'
	WORD: 'nr.' númer
	NUMBER: '10' (10, None, None)
	PUNCTUATION: '/' 4
	YEAR: '2007' 2007
	WORD: 'þann'
	DATE: '3. janúar 2010' (2010, 1, 3)
	PUNCTUATION: '.' 3
	END SENT: '-'

Note the following:

	- Sentences are delimited by ``TOK.S_BEGIN`` and ``TOK.S_END`` tokens.
	- Composite words, such as *stjórnskipunar- og eftirlitsnefndar*, are coalesced into one token.
	- Known abbreviations are recognized and their full meaning is available in the ``token.val`` field.
	- Ordinal numbers (*3., XVII.*) are recognized and their value (*3, 17*) is available in the ``token.val`` field.
	- Numbers, both integer and real, are recognized and their value is available in the ``token.val`` field.
	- Dates, years and times are recognized and the respective year, month, day, hour, minute and second
	  values are included in a tuple in ``token.val``.
	- Punctuation is annotated in ``token.val`` depending on its whitespace requirements::

		TP_LEFT = 1   # Whitespace to the left
		TP_CENTER = 2 # Whitespace to the left and right
		TP_RIGHT = 3  # Whitespace to the right
		TP_NONE = 4   # No whitespace


Documentation
-------------

To tokenize a text string, call ``tokenizer.tokenize(text)``. This function returns a
Python *generator* of token objects. Typically, it is used in a ``for`` loop::

	for token in tokenizer.tokenize(mystring):
		kind, txt, val = token
		if kind == tokenizer.TOK.EMAIL:
			# Do something with e-mail tokens
		else:
			# Do something else

Alternatively, create a token list from the returned generator::

	token_list = list(tokenizer.tokenize(mystring))

Each token object is a simple named tuple with three
components: ``(kind, txt, val)``.

The ``kind`` field contains one of the following integer constants (defined within the ``TOK``
class)::

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

    S_BEGIN = 11001 # Sentence begin
    S_END = 11002 # Sentence end

To obtain a descriptive text for a token kind, use ``TOK.descr[token.kind]`` (see example above).

The ``txt`` field contains the original source text for the token. Note that in the case of
abbreviations that end a sentence, the final period '.' is a separate token, and it is thus
omitted from the of the abbreviation token's ``txt`` field.

The ``val`` field contains auxiliary information, corresponding to the token kind.


