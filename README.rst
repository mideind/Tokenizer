-----------------------------------------
Tokenizer: A tokenizer for Icelandic text
-----------------------------------------

.. image:: https://travis-ci.org/vthorsteinsson/Tokenizer.svg?branch=master
   :target: https://travis-ci.com/vthorsteinsson/Tokenizer

Overview
--------

Tokenization is a necessary first step in many natural language processing tasks,
such as word counting, parsing, spell checking, corpus generation, and
statistical analysis of text.

**Tokenizer** is a compact pure-Python (2 and 3) module for tokenizing Icelandic text. It converts
Python text strings to streams of token objects, where each token object is a separate
word, punctuation sign, number/amount, date, e-mail, URL/URI, etc. It also segments
the token stream into sentences, considering corner cases such as abbreviations
and dates in the middle of sentences.

The package contains a dictionary of common Icelandic abbreviations, in the file
``src/tokenizer/Abbrev.conf``.

Tokenizer is an independent spinoff from the `Greynir project <https://greynir.is>`_
(GitHub repository `here <https://github.com/vthorsteinsson/Reynir>`_), by the same authors.
Note that Tokenizer is licensed under the MIT license while Greynir is licensed under GPLv3.

You might also find the
`Reynir natural language parser for Icelandic <https://github.com/vthorsteinsson/ReynirPackage>`_
interesting. The Reynir parser uses Tokenizer on its input.

To install::

	$ pip install tokenizer

To use (for Python 3, you can omit the ``u""`` string prefix)::

	from tokenizer import tokenize, TOK

	text = (u"Málinu var vísað til stjórnskipunar- og eftirlitsnefndar "
		u"skv. 3. gr. XVII. kafla laga nr. 10/2007 þann 3. janúar 2010.")

	for token in tokenize(text):

		print(u"{0}: '{1}' {2}".format(
			TOK.descr[token.kind],
			token.txt or "-",
			token.val or ""))

Output::

	BEGIN SENT: '-' (0, None)
	WORD: 'Málinu'
	WORD: 'var'
	WORD: 'vísað'
	WORD: 'til'
	WORD: 'stjórnskipunar- og eftirlitsnefndar'
	WORD: 'skv.' [('samkvæmt', 0, 'fs', 'skst', 'skv.', '-')]
	ORDINAL: '3.' 3
	WORD: 'gr.' [('grein', 0, 'kvk', 'skst', 'gr.', '-')]
	ORDINAL: 'XVII.' 17
	WORD: 'kafla'
	WORD: 'laga'
	WORD: 'nr.' [('númer', 0, 'hk', 'skst', 'nr.', '-')]
	NUMBER: '10' (10, None, None)
	PUNCTUATION: '/' 4
	YEAR: '2007' 2007
	WORD: 'þann'
	DATEABS: '3. janúar 2010' (2010, 1, 3)
	PUNCTUATION: '.' 3
	END SENT: '-'

Note the following:

	- Sentences are delimited by ``TOK.S_BEGIN`` and ``TOK.S_END`` tokens.
	- Composite words, such as *stjórnskipunar- og eftirlitsnefndar*, are coalesced into one token.
	- Well-known abbreviations are recognized and their full expansion is available
	  in the ``token.val`` field.
	- Ordinal numbers (*3., XVII.*) are recognized and their value (*3, 17*) is available
	  in the ``token.val``  field.
	- Dates, years and times, both absolute and relative, are recognized and
	  the respective year, month, day, hour, minute and second
	  values are included as a tuple in ``token.val``.
	- Numbers, both integer and real, are recognized and their value is available
	  in the ``token.val`` field.
	- Further details of how Tokenizer processes text can be inferred from the
	  `test module <https://github.com/vthorsteinsson/Tokenizer/blob/master/test/test_tokenizer.py>`_
	  in the project's `GitHub repository <https://github.com/vthorsteinsson/Tokenizer>`_.


The ``tokenize()`` function
---------------------------

To tokenize a text string, call ``tokenizer.tokenize(text)``. This function returns a
Python *generator* of token objects. Each token object is a simple ``namedtuple`` with three
fields: ``(kind, txt, val)`` (see below).

The ``tokenizer.tokenize()`` function is typically called in a ``for`` loop::

	for token in tokenizer.tokenize(mystring):
		kind, txt, val = token
		if kind == tokenizer.TOK.WORD:
			# Do something with word tokens
			pass
		else:
			# Do something else
			pass

Alternatively, create a token list from the returned generator::

	token_list = list(tokenizer.tokenize(mystring))

In Python 2.7, you can pass either ``unicode`` strings or ``str`` byte strings to
``tokenizer.tokenize()``. In the latter case, the byte string is assumed to be
encoded in UTF-8.

The token object
----------------

Each token is represented by a ``namedtuple`` with three fields: ``(kind, txt, val)``.

The ``kind`` field
==================

The ``kind`` field contains one of the following integer constants, defined within the ``TOK``
class:

+---------------+---------+---------------------+---------------------------+
| Constant      |  Value  | Explanation         | Examples                  |
+===============+=========+=====================+===========================+
| PUNCTUATION   |    1    | Punctuation         | .                         |
+---------------+---------+---------------------+---------------------------+
| TIME          |    2    | Time (h, m, s)      | 11:35:40                  |
+---------------+---------+---------------------+---------------------------+
| DATE *        |    3    | Date (y, m, d)      | [Unused, see DATEABS and  |
|               |         |                     | DATEREL]                  |
+---------------+---------+---------------------+---------------------------+
| YEAR          |    4    | Year                | | árið 874 e.Kr.          |
|               |         |                     | | 1965                    |
|               |         |                     | | 44 f.Kr.                |
+---------------+---------+---------------------+---------------------------+
| NUMBER        |    5    | Number              | | 100                     |
|               |         |                     | | 1.965                   |
|               |         |                     | | 1.965,34                |
|               |         |                     | | 1,965.34                |
+---------------+---------+---------------------+---------------------------+
| WORD          |    6    | Word                | | kattaeftirlit           |
|               |         |                     | | hunda- og kattaeftirlit |
+---------------+---------+---------------------+---------------------------+
| TELNO         |    7    | Telephone number    | | 123444                  |
|               |         |                     | | 123-4444                |
+---------------+---------+---------------------+---------------------------+
| PERCENT       |    8    | Percentage          | 78%                       |
+---------------+---------+---------------------+---------------------------+
| URL           |    9    | URL                 | | ``https://greynir.is``  |
|               |         |                     | | ``www.greynir.is``      |
+---------------+---------+---------------------+---------------------------+
| ORDINAL       |    10   | Ordinal number      | | 30.                     |
|               |         |                     | | XVIII.                  |
+---------------+---------+---------------------+---------------------------+
| TIMESTAMP *   |    11   | Timestamp           | [Unused, see              |
|               |         |                     | TIMESTAMPABS and          |
|               |         |                     | TIMESTAMPREL]             |
+---------------+---------+---------------------+---------------------------+
| CURRENCY *    |    12   | Currency name       | [Unused]                  |
+---------------+---------+---------------------+---------------------------+
| AMOUNT        |    13   | Amount              | | €2.345,67               |
|               |         |                     | | 750 þús.kr.             |
|               |         |                     | | 2,7 mrð. USD            |
+---------------+---------+---------------------+---------------------------+
| PERSON *      |    14   | Person name         | [Unused]                  |
+---------------+---------+---------------------+---------------------------+
| EMAIL         |    15   | E-mail              | ``fake@news.is``          |
+---------------+---------+---------------------+---------------------------+
| ENTITY *      |    16   | Named entity        | [Unused]                  |
+---------------+---------+---------------------+---------------------------+
| UNKNOWN       |    17   | Unknown token       |                           |
+---------------+---------+---------------------+---------------------------+
| DATEABS       |    18   | Absolute date       | | 30. desember 1965       |
|               |         |                     | | 30/12/1965              |
|               |         |                     | | 1965-12-30              |
+---------------+---------+---------------------+---------------------------+
| DATEREL       |    19   | Relative date       | 15. mars                  |
+---------------+---------+---------------------+---------------------------+
| TIMESTAMPABS  |    20   | Absolute timestamp  | | 30. desember 1965 11:34 |
|               |         |                     | | 1965-12-30 kl. 13:00    |
+---------------+---------+---------------------+---------------------------+
| TIMESTAMPREL  |    21   | Relative timestamp  | 30. desember kl. 13:00    |
+---------------+---------+---------------------+---------------------------+
| MEASUREMENT   |    22   | Value with a        | | 690 MW                  |
|               |         | measurement unit    | | 1.010 hPa               |
|               |         |                     | | 220 m²                  |
+---------------+---------+---------------------+---------------------------+
| NUMWLETTER    |    23   | Number followed by  | | 14a                     |
|               |         | a single letter     | | 7B                      |
+---------------+---------+---------------------+---------------------------+
| S_BEGIN       |  11001  | Start of sentence   |                           |
+---------------+---------+---------------------+---------------------------+
| S_END         |  11002  | End of sentence     |                           |
+---------------+---------+---------------------+---------------------------+

(*) The token types marked with an asterisk are reserved for the Reynir package
and not currently returned by the tokenizer.

To obtain a descriptive text for a token kind, use ``TOK.descr[token.kind]`` (see example above).

The ``txt`` field
==================

The ``txt`` field contains the original source text for the token. However, in a few cases,
the tokenizer auto-corrects the original source text:

* It converts single and double quotes to the correct Icelandic ones (i.e. „these“ or ‚these‘).

* It converts kludgy ordinals (*3ja*) to proper ones (*þriðja*), and English-style
  thousand and decimal separators to Icelandic ones (*10,345.67* becomes *10.345,67*).

* Tokenizer automatically merges Unicode ``COMBINING ACUTE ACCENT`` (code point 769)
  and ``COMBINING DIAERESIS`` (code point 776) with vowels to form single code points
  for the Icelandic letters á, é, í, ó, ú, ý and ö, in both lower and upper case.

In the case of abbreviations that end a sentence, the final period '.' is a separate token,
and it is consequently omitted from the abbreviation token's ``txt`` field. A sentence ending
in *o.s.frv.* will thus end with two tokens, the next-to-last one being the tuple
``(TOK.WORD, "o.s.frv", "og svo framvegis")`` - note the omitted period in the ``txt`` field -
and the last one being ``(TOK.PUNCTUATION, ".", 3)`` (the 3 is explained below).

The ``val`` field
==================

The ``val`` field contains auxiliary information, corresponding to the token kind, as follows:

- For ``TOK.PUNCTUATION``, the ``val`` field specifies the whitespace normally found around
  the symbol in question::

	TP_LEFT = 1   # Whitespace to the left
	TP_CENTER = 2 # Whitespace to the left and right
	TP_RIGHT = 3  # Whitespace to the right
	TP_NONE = 4   # No whitespace

- For ``TOK.TIME``, the ``val`` field contains an ``(hour, minute, second)`` tuple.
- For ``TOK.DATEABS``, the ``val`` field contains a ``(year, month, day)`` tuple (all 1-based).
- For ``TOK.DATEREL``, the ``val`` field contains a ``(year, month, day)`` tuple (all 1-based),
  except that a least one of the tuple fields is missing and set to 0. Example: *þriðja júní*
  becomes ``TOK.DATEREL`` with the fields ``(0, 6, 3)`` as the year is missing.
- For ``TOK.YEAR``, the ``val`` field contains the year as an integer. A negative number
  indicates that the year is BCE (*fyrir Krist*), specified with the suffix *f.Kr.*
  (e.g. *árið 33 f.Kr.*).
- For ``TOK.NUMBER``, the ``val`` field contains a tuple ``(number, None, None)``.
  (The two empty fields are included for compatibility with Greynir.)
- For ``TOK.WORD``, the ``val`` field contains the full expansion of an abbreviation,
  as a list containing a single tuple, or ``None`` if the word is not abbreviated.
- For ``TOK.PERCENT``, the ``val`` field contains a tuple of ``(percentage, None, None)``.
- For ``TOK.ORDINAL``, the ``val`` field contains the ordinal value as an integer.
  The original ordinal may be a decimal number or a Roman numeral.
- For ``TOK.TIMESTAMP``, the ``val`` field contains a ``(year, month, day, hour, minute, second)`` tuple.
- For ``TOK.AMOUNT``, the ``val`` field contains an ``(amount, currency, None, None)`` tuple. The
  amount is a float, and the currency is an ISO currency code, e.g. *USD* for dollars ($ sign),
  *EUR* for euros (€ sign) or *ISK* for Icelandic króna (*kr.* abbreviation).
  (The two empty fields are included for compatibility with Greynir.)
- For ``TOK.MEASUREMENT``, the ``val`` field contains a ``(unit, value)`` tuple, where ``unit``
  is a base SI unit (such as ``g``, ``m``, ``m²``, ``s``, ``W``, ``Hz``, ``K`` for temperature
  in Kelvin).


The ``correct_spaces()`` function
---------------------------------

Tokenizer also contains the utility function ``tokenizer.correct_spaces(text)``. This function
returns a string after splitting it up and re-joining
it with correct whitespace around punctuation tokens. Example::

	>>> tokenizer.correct_spaces("Frétt \n  dagsins:Jón\t ,Friðgeir og Páll ! 100  /  2  =   50")
	'Frétt dagsins: Jón, Friðgeir og Páll! 100/2 = 50'


The ``Abbrev.conf`` file
------------------------

Abbreviations recognized by Tokenizer are defined in the ``Abbrev.conf`` file, found in the
``src/tokenizer/`` directory. This is a text file with abbreviations, their definitions and
explanatory comments. The file is loaded into memory during the first call to
``tokenizer.tokenize()`` within a process.


Development installation
------------------------

To install Tokenizer in development mode, where you can easily modify the source files
(assuming you have ``git`` available)::

	$ git clone https://github.com/vthorsteinsson/Tokenizer
	$ cd Tokenizer
	$ # [ Activate your virtualenv here, if you have one ]
	$ python setup.py develop

To run the built-in tests, install `pytest <https://docs.pytest.org/en/latest/>`_, ``cd`` to your
``Tokenizer`` subdirectory (and optionally activate your virtualenv), then run::

    $ python -m pytest


Changelog
---------

* Version 1.0.9: Added abbreviation 'MAST'; harmonized copyright headers
* Version 1.0.8: Bug fixes in DATEREL, MEASUREMENT and NUMWLETTER token handling;
  added kWst and MWst measurement units; blackened
* Version 1.0.7: Added NUMWLETTER token type
* Version 1.0.6: Automatic merging of Unicode ``COMBINING ACUTE ACCENT`` and
  ``COMBINING DIAERESIS`` code points with vowels
* Version 1.0.5: Date/time and amount tokens coalesced to a further extent
* Version 1.0.4: Added ``TOK.DATEABS``, ``TOK.TIMESTAMPABS``, ``TOK.MEASUREMENT``

