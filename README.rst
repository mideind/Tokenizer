---------
Tokenizer
---------

Overview
--------

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

	text = ("Málinu var vísað til stjórnskipunar- og eftirlitsnefndar "
		"skv. 3. gr. XVII. kafla laga nr. 10/2007 þann 3. janúar 2010.")

	for token in tokenize(text):

		print("{0}: '{1}' {2}".format(
			TOK.descr[token.kind],
			token.txt or "-",
			token.val or ""))

Output::

	S_BEGIN: '-' (0, None)
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
	S_END: '-'

Note the following:

	- Sentences are delimited by ``TOK.S_BEGIN`` and ``TOK.S_END`` tokens.
	- Composite words, such as *stjórnskipunar- og eftirlitsnefndar*, are coalesced into one token.
	- Well-known abbreviations are recognized and their full expansion is available in the ``token.val`` field.
	- Ordinal numbers (*3., XVII.*) are recognized and their value (*3, 17*) is available in the ``token.val`` field.
	- Numbers, both integer and real, are recognized and their value is available in the ``token.val`` field.
	- Dates, years and times are recognized and the respective year, month, day, hour, minute and second
	  values are included as a tuple in ``token.val``.


The ``tokenize()`` function
---------------------------

To tokenize a text string, call ``tokenizer.tokenize(text)``. This function returns a
Python *generator* of token objects. Each token object is a simple named tuple with three
components: ``(kind, txt, val)``.

The ``tokenizer.tokenize()`` function is typically called in a ``for`` loop::

	for token in tokenizer.tokenize(mystring):
		kind, txt, val = token
		if kind == tokenizer.TOK.EMAIL:
			# Do something with e-mail tokens
		else:
			# Do something else

Alternatively, create a token list from the returned generator::

	token_list = list(tokenizer.tokenize(mystring))

Reassemble the original string, evenly spaced (for correct spacing, see below)::

	token_string = " ".join(t.txt for t in token_list)


The token object
----------------

Each token is represented by a named tuple with three fields: ``(kind, txt, val)``.

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
    CURRENCY = 12	# Not used
    AMOUNT = 13
    PERSON = 14		# Not used
    EMAIL = 15
    ENTITY = 16		# Not used
    UNKNOWN = 17

    S_BEGIN = 11001 # Sentence begin
    S_END = 11002 	# Sentence end

To obtain a descriptive text for a token kind, use ``TOK.descr[token.kind]`` (see example above).

The ``txt`` field contains the original source text for the token.

In the case of abbreviations that end a sentence, the final period '.' is a separate token,
and it is consequently omitted from the abbreviation token's ``txt`` field. A sentence ending
in *o.s.frv.* will thus end with two tokens, the next-to-last one being a ``TOK.WORD`` with
``txt = "o.s.frv"`` (note the omitted period) and the last one being a ``TOK.PUNCTUATION``
with ``txt = "."``.

The ``val`` field contains auxiliary information, corresponding to the token kind, as follows:

- For ``TOK.PUNCTUATION``, the ``val`` field specifies the whitespace normally found around
  the symbol in question::

	TP_LEFT = 1   # Whitespace to the left
	TP_CENTER = 2 # Whitespace to the left and right
	TP_RIGHT = 3  # Whitespace to the right
	TP_NONE = 4   # No whitespace

- For ``TOK.TIME``, the ``val`` field contains an ``(hour, minute, second)`` tuple.
- For ``TOK.DATE``, the ``val`` field contains a ``(year, month, day)`` tuple (all 1-based).
- For ``TOK.YEAR``, the ``val`` field contains the year as an integer.
- For ``TOK.NUMBER``, the ``val`` field contains a tuple ``(number, None, None)``.
  (The two empty fields are included for compatibility with Greynir.)
- For ``TOK.WORD``, the ``val`` field contains the full expansion of an abbreviation,
  or ``None`` if the word is not abbreviated.
- For ``TOK.PERCENT``, the ``val`` field contains a tuple of ``(percentage, None, None)``.
- For ``TOK.ORDINAL``, the ``val`` field contains the ordinal value as an integer.
- For ``TOK.TIMESTAMP``, the ``val`` field contains a ``(year, month, day, hour, minute, second)`` tuple.
- For ``TOK.AMOUNT``, the ``val`` field contains an ``(amount, currency, None, None)`` tuple. The
  amount is a float, and the currency is an ISO currency code, i.e. "USD" for dollars ($ sign) or
  "EUR" for euros (€ sign). (The two empty fields are included for compatibility with Greynir.)


The ``correct_spaces()`` function
---------------------------------

Tokenizer also contains the utility function ``tokenizer.correct_spaces(text)``. This function
returns a string after splitting it up and re-joining
it with correct whitespace around punctuation tokens. Example::

	>>> tokenizer.correct_spaces("Frétt \n  dagsins:Jón\t ,Friðgeir og Páll ! 100  /  2  =   50")
	'Frétt dagsins: Jón, Friðgeir og Páll! 100/2 = 50'

