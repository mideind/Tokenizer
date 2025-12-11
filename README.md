[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-3817/)
![Release](https://shields.io/github/v/release/mideind/Tokenizer?display_name=tag)
![PyPI](https://img.shields.io/pypi/v/tokenizer)
[![tests](https://github.com/mideind/Tokenizer/workflows/tests/badge.svg)](https://github.com/mideind/Tokenizer)

# Tokenizer: A tokenizer for Icelandic text

## Overview

Tokenization is a necessary first step in many natural language processing
tasks, such as word counting, parsing, spell checking, corpus generation, and
statistical analysis of text.

**Tokenizer** is a compact pure-Python (>=3.9) executable
program and module for tokenizing Icelandic text. It converts input text to
streams of *tokens*, where each token is a separate word, punctuation sign,
number/amount, date, e-mail, URL/URI, etc. It also segments the token stream
into sentences, considering corner cases such as abbreviations and dates in
the middle of sentences.

The package contains a dictionary of common Icelandic abbreviations,
in the file `src/tokenizer/Abbrev.conf`.

Tokenizer is an independent spinoff from the [Greynir project](https://greynir.is)
(GitHub repository [here](https://github.com/mideind/Greynir)), by the same authors.
The [Greynir natural language parser for Icelandic](https://github.com/mideind/GreynirEngine) 
uses Tokenizer on its input.

Tokenizer is licensed under the MIT license.

## Indicative performance

Time to tokenize 1 MB of a wide selection of texts from the Icelandic Gigaword Corpus
using a 64-bit 2.6 GHz Intel Core i9:

|               |  Time (sec) |
|---------------|------------:|
| CPython 3.12  |       25.27 |
| PyPy 3.11     |        8.08 |

Running tokenization with PyPy is about 3x faster than with CPython.

## Deep vs. shallow tokenization

Tokenizer can do both *deep* and *shallow* tokenization.

*Shallow* tokenization simply returns each sentence as a string (or as a line
of text in an output file), where the individual tokens are separated
by spaces.

*Deep* tokenization returns token objects that have been annotated with
the token type and further information extracted from the token, for example
a *(year, month, day)* tuple in the case of date tokens.

In shallow tokenization, tokens are in most cases kept intact, although
consecutive white space is always coalesced. The input strings
`"800 MW"`, `"21. janúar"` and `"800 7000"` thus become
two tokens each, output with a single space between them.

In deep tokenization, the same strings are represented by single token objects,
of type `TOK.MEASUREMENT`, `TOK.DATEREL` and `TOK.TELNO`, respectively.
The text associated with a single token object may contain spaces, 
although consecutive whitespace is always coalesced into a single space `" "`.

By default, the command line tool performs shallow tokenization. If you
want deep tokenization with the command line tool, use the `--json` or
`--csv` switches.

From Python code, call `split_into_sentences()` for shallow tokenization,
or `tokenize()` for deep tokenization. These functions are documented with
examples below.

## Installation

To install:

```console
$ pip install tokenizer
```

## Command line tool

After installation, the tokenizer can be invoked directly from
the command line:

```console
$ tokenize input.txt output.txt
```

Input and output files are assumed to be UTF-8 encoded. If the file names
are not given explicitly, `stdin` and `stdout` are used for input and output,
respectively.

Empty lines in the input are treated as hard sentence boundaries.

By default, the output consists of one sentence per line, where each
line ends with a single newline character (ASCII LF, `chr(10)`, `\n`).
Within each line, tokens are separated by spaces.

The following (mutually exclusive) options can be specified
on the command line:

| Option      | Description                                               |
|-------------|-----------------------------------------------------------|
| `--csv`     | Deep tokenization. Output token objects in CSV format, one per line. Each line contains: token kind (number), normalized text, value (if applicable), original text with preserved whitespace, and character span indices. Sentences are separated by lines containing `0,"","","",""`. |
| `--json`    | Deep tokenization. Output token objects in JSON format, one per line. Each JSON object contains: `k` (token kind), `t` (normalized text), `v` (value if applicable), `o` (original text with preserved whitespace), `s` (character span indices). |

Other options can be specified on the command line:

| Option                       | Description                                               |
|------------------------------|-----------------------------------------------------------|
| `-n`, `--normalize`          | Normalize punctuation: quotes output in Icelandic form („these“), ellipsis as single character (…), year ranges with en-dash (1914–1918), and em-dashes centered with spaces ( — ). This option is only applicable to shallow tokenization. |
| `-s`, `--one_sent_per_line`  | Input contains strictly one sentence per line, i.e. every newline is a sentence boundary. |
| `-o`, `--original`           | Output original token text, i.e. bypass shallow tokenization. This effectively runs the tokenizer as a sentence splitter only. |
| `-m`, `--convert_measurements` | Degree signal in tokens denoting temperature normalized (200° C -> 200 °C). |
| `-p`, `--coalesce_percent`   | Numbers combined into one token with the following token denoting percentage word forms (*prósent*, *prósentustig*, *hundraðshlutar*). |
| `-g`, `--keep_composite_glyphs` | Do not replace composite glyphs using Unicode COMBINING codes with their accented/umlaut counterparts. |
| `-e`, `--replace_html_escapes` | HTML escape codes replaced by their meaning, such as `&aacute;` -> `á`. |
| `-c`, `--convert_numbers`      | English-style decimal points and thousands separators in numbers changed to Icelandic style. |

Type `tokenize -h` or `tokenize --help` to get a short help message.

### Example

```console
$ echo "3.janúar sl. keypti   ég 64kWst rafbíl. Hann kostaði € 30.000." | tokenize
3. janúar sl. keypti ég 64kWst rafbíl .
Hann kostaði €30.000 .

$ echo "3.janúar sl. keypti   ég 64kWst rafbíl. Hann kostaði € 30.000." | tokenize --csv
19,"3. janúar","0|1|3","3.janúar","0-1-2-2-3-4-5-6-7"
6,"sl.","síðastliðinn"," sl.","1-2-3"
6,"keypti",""," keypti","1-2-3-4-5-6"
6,"ég","","   ég","3-4"
22,"64kWst","J|230400000.0"," 64kWst","1-2-3-4-5-6"
6,"rafbíl",""," rafbíl","1-2-3-4-5-6"
1,".",".",".","0"
0,"","","",""
6,"Hann",""," Hann","1-2-3-4"
6,"kostaði",""," kostaði","1-2-3-4-5-6-7"
13,"€30.000","30000|EUR"," € 30.000","1-3-4-5-6-7-8"
1,".",".",".","0"
0,"","","",""

$ echo "3.janúar sl. keypti   ég 64kWst rafbíl. Hann kostaði € 30.000." | tokenize --json
{"k":"BEGIN SENT"}
{"k":"DATEREL","t":"3. janúar","v":[0,1,3],"o":"3.janúar","s":[0,1,2,2,3,4,5,6,7]}
{"k":"WORD","t":"sl.","v":["síðastliðinn"],"o":" sl.","s":[1,2,3]}
{"k":"WORD","t":"keypti","o":" keypti","s":[1,2,3,4,5,6]}
{"k":"WORD","t":"ég","o":"   ég","s":[3,4]}
{"k":"MEASUREMENT","t":"64kWst","v":["J",230400000.0],"o":" 64kWst","s":[1,2,3,4,5,6]}
{"k":"WORD","t":"rafbíl","o":" rafbíl","s":[1,2,3,4,5,6]}
{"k":"PUNCTUATION","t":".","v":".","o":".","s":[0]}
{"k":"END SENT"}
{"k":"BEGIN SENT"}
{"k":"WORD","t":"Hann","o":" Hann","s":[1,2,3,4]}
{"k":"WORD","t":"kostaði","o":" kostaði","s":[1,2,3,4,5,6,7]}
{"k":"AMOUNT","t":"€30.000","v":[30000,"EUR"],"o":" € 30.000","s":[1,3,4,5,6,7,8]}
{"k":"PUNCTUATION","t":".","v":".","o":".","s":[0]}
{"k":"END SENT"}
```

#### CSV Output Format

When using `--csv`, each token is output as a CSV row with the following five fields:

1. **Token kind** (number): Numeric code representing the token type (e.g., 6 for WORD, 19 for DATEREL, 1 for PUNCTUATION)
2. **Normalized text**: The processed text of the token
3. **Value**: The parsed value, if applicable (e.g., date tuples, amounts, abbreviation expansions), or empty string
4. **Original text**: The original text including preserved whitespace
5. **Span indices**: Character indices mapping each character in the normalized text to its position in the original text, separated by hyphens

Sentences are separated by rows containing `0,"","","",""`.

#### JSON Output Format

When using `--json`, each token is output as a JSON object on a separate line with the following fields:

- **`k`** (kind): The token type description (e.g., "WORD", "DATEREL", "PUNCTUATION")
- **`t`** (text): The normalized/processed text of the token
- **`v`** (value): The parsed value, if applicable (e.g., date tuples, amounts, abbreviation expansions)
- **`o`** (original): The original text including preserved whitespace
- **`s`** (span): Character indices mapping each character in the normalized text to its position in the original text

## Python module

### Shallow tokenization example

An example of shallow tokenization from Python code goes something like this:

```python
from tokenizer import split_into_sentences

# A string to be tokenized, containing two sentences
s = "3.janúar sl. keypti   ég 64kWst rafbíl. Hann kostaði € 30.000."

# Obtain a generator of sentence strings
g = split_into_sentences(s)

# Loop through the sentences
for sentence in g:

    # Obtain the individual token strings
    tokens = sentence.split()

    # Print the tokens, comma-separated
    print("|".join(tokens))
```

The program outputs:

    3.|janúar|sl.|keypti|ég|64kWst|rafbíl|.
    Hann|kostaði|€30.000|.

### Deep tokenization example

To do deep tokenization from within Python code:

```python
from tokenizer import tokenize, TOK

text = ("Málinu var vísað til stjórnskipunar- og eftirlitsnefndar "
    "skv. 3. gr. XVII. kafla laga nr. 10/2007 þann 3. janúar 2010.")

for token in tokenize(text):

    print("{0}: '{1}' {2}".format(
        TOK.descr[token.kind],
        token.txt or "-",
        token.val or ""))
```

Output:

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
    PUNCTUATION: '/' (4, '/')
    YEAR: '2007' 2007
    WORD: 'þann'
    DATEABS: '3. janúar 2010' (2010, 1, 3)
    PUNCTUATION: '.' (3, '.')
    END SENT: '-'

Note the following:

- Sentences are delimited by `TOK.S_BEGIN` and `TOK.S_END` tokens.
- Composite words, such as *stjórnskipunar- og eftirlitsnefndar*,
are coalesced into one token.
- Well-known abbreviations are recognized and their full expansion
is available in the `token.val` field.
- Ordinal numbers (*3., XVII.*) are recognized and their value (*3, 17*)
is available in the `token.val`  field.
- Dates, years and times, both absolute and relative, are recognized and
the respective year, month, day, hour, minute and second
values are included as a tuple in `token.val`.
- Numbers, both integer and real, are recognized and their value
is available in the `token.val` field.
- Further details of how Tokenizer processes text can be inferred from the
[test module](https://github.com/mideind/Tokenizer/blob/master/test/test_tokenizer.py)
in the project's [GitHub repository](https://github.com/mideind/Tokenizer).

## The `tokenize()` function

To deep-tokenize a text string, call `tokenizer.tokenize(text, **options)`.
The `text` parameter can be a string, or an iterable that yields strings
(such as a text file object).

The function returns a Python *generator* of token objects.
Each token object is a simple `namedtuple` with three
fields: `(kind, txt, val)` (further documented below).

The `tokenizer.tokenize()` function is typically called in a `for` loop:

```python
import tokenizer
for token in tokenizer.tokenize(mystring):
    kind, txt, val = token
    if kind == tokenizer.TOK.WORD:
        # Do something with word tokens
        pass
    else:
        # Do something else
        pass
```

Alternatively, create a token list from the returned generator:

```python
token_list = list(tokenizer.tokenize(mystring))
```

## The `split_into_sentences()` function

To shallow-tokenize a text string, call
`tokenizer.split_into_sentences(text_or_gen, **options)`.
The `text_or_gen` parameter can be a string, or an iterable that yields
strings (such as a text file object).

This function returns a Python *generator* of strings, yielding a string
for each sentence in the input. Within a sentence, the tokens are
separated by spaces.

You can pass the option `normalize=True` to the function if you want
the normalized form of punctuation tokens. Normalization outputs
Icelandic single and double quotes („these“) instead of English-style
ones ("these"), converts three-dot ellipsis ... to single character
ellipsis …, normalizes year ranges to use en-dash (1914–1918), and
ensures em-dashes are centered with spaces ( — ).

The `tokenizer.split_into_sentences()` function is typically called
in a `for` loop:

```python
import tokenizer
with open("example.txt", "r", encoding="utf-8") as f:
    # You can pass a file object directly to split_into_sentences()
    for sentence in tokenizer.split_into_sentences(f):
        # sentence is a string of space-separated tokens
        tokens = sentence.split()
        # Now, tokens is a list of strings, one for each token
        for t in tokens:
            # Do something with the token t
            pass
```

## The `correct_spaces()` function

The `tokenizer.correct_spaces(text)` function returns a string after
splitting it up and re-joining it with correct whitespace around
punctuation tokens. Example:

```python
>>> import tokenizer
>>> tokenizer.correct_spaces(
... "Frétt \n  dagsins:Jón\t ,Friðgeir og Páll ! 100  /  2  =   50"
... )
'Frétt dagsins: Jón, Friðgeir og Páll! 100/2 = 50'
```

## The `detokenize()` function

The `tokenizer.detokenize(tokens, normalize=False)` function
takes an iterable of token objects and returns a corresponding, correctly
spaced text string, composed from the tokens' text. If the
`normalize` parameter is set to `True`,
the function uses the normalized form of any punctuation tokens, such
as proper Icelandic single and double quotes instead of English-type
quotes. Example:

```python
>>> import tokenizer
>>> toklist = list(tokenizer.tokenize("Hann sagði: \"Þú ert ágæt!\"."))
>>> tokenizer.detokenize(toklist, normalize=True)
'Hann sagði: \u201eÞú ert ágæt!\u201c.'
```

## The `normalized_text()` function

The `tokenizer.normalized_text(token)` function
returns the normalized text for a token. This means that the original
token text is returned except for certain punctuation tokens, where a
normalized form is returned instead. Specifically, English-type quotes
are converted to Icelandic ones („these“), hyphens in year ranges are
converted to en-dash (1914–1918), and consecutive identical dashes are
preserved as multi-character tokens.

## The `text_from_tokens()` function

The `tokenizer.text_from_tokens(tokens)` function
returns a concatenation of the text contents of the given token list,
with spaces between tokens. Example:

```python
>>> import tokenizer
>>> toklist = list(tokenizer.tokenize("Hann sagði: \"Þú ert ágæt!\"."))
>>> tokenizer.text_from_tokens(toklist)
'Hann sagði : " Þú ert ágæt ! " .'
```

## The `normalized_text_from_tokens()` function

The `tokenizer.normalized_text_from_tokens(tokens)` function
returns a concatenation of the normalized text contents of the given
token list, with spaces between tokens. Example (note the double quotes):

```python
>>> import tokenizer
>>> toklist = list(tokenizer.tokenize("Hann sagði: \"Þú ert ágæt!\"."))
>>> tokenizer.normalized_text_from_tokens(toklist)
'Hann sagði : „ Þú ert ágæt ! “ .'
```

## Tokenization options

You can optionally pass one or more of the following options as
keyword parameters to the `tokenize()` and `split_into_sentences()`
functions:

* `convert_numbers=[bool]`

  Setting this option to `True` causes the tokenizer to convert numbers
  and amounts with
  English-style decimal points (`.`) and thousands separators (`,`)
  to Icelandic format, where the decimal separator is a comma (`,`)
  and the thousands separator is a period (`.`). `$1,234.56` is thus
  converted to a token whose text is `$1.234,56`.

  The default value for the `convert_numbers` option is `False`.

  Note that in versions of Tokenizer prior to 1.4, `convert_numbers`
  was `True`.

* `convert_measurements=[bool]`

  Setting this option to `True` causes the tokenizer to convert
  degrees Kelvin, Celsius and Fahrenheit to a regularized form, i.e.
  `200° C` becomes `200 °C`.

  The default value for the `convert_measurements` option is `False`.

* `replace_composite_glyphs=[bool]`

  Setting this option to `False` disables the automatic replacement
  of composite Unicode glyphs with their corresponding Icelandic characters.
  By default, the tokenizer combines vowels with the Unicode
  COMBINING ACUTE ACCENT and COMBINING DIAERESIS glyphs to form single
  character code points, such as 'á' and 'ö'.

  The default value for the `replace_composite_glyphs` option is `True`.

* `replace_html_escapes=[bool]`

  Setting this option to `True` causes the tokenizer to replace common
  HTML escaped character codes, such as `&aacute;` with the character being
  escaped, such as `á`. Note that `&shy;` (soft hyphen) is replaced by
  an empty string, and `&nbsp;` is replaced by a normal space.
  The ligatures `&filig;` and `&fllig;` are replaced by `fi` and `fl`,
  respectively.

  The default value for the `replace_html_escapes` option is `False`.

## Dash and Hyphen Handling

Tokenizer distinguishes between three dash types and handles them contextually:

- **Hyphen (-)**: Regular hyphen, used e.g. in compound words
- **En-dash (–)**: Longer dash, preferred in Icelandic for year/date ranges
- **Em-dash (—)**: Longest dash, used for emphasis or parenthetical remarks

### Context-Specific Behavior

**Year ranges**: Hyphens between years are normalized to en-dash when
`normalize=True`, following Icelandic spelling rules: `1914-1918` → `1914–1918`.

**Free-standing dashes**: Hyphens and en-dashes with spaces around them
preserve those spaces: `word - word` remains `word - word`, not `word-word`.

**Composite word continuations**: Hyphens stay attached to preceding words
in patterns like `fjölskyldu- og húsdýragarðurinn`, and to succeeding words
in cases like `eldhúsborð og -stólar`.

**Em-dashes**: Treated as centered punctuation with spaces on both
sides: `word—word` → `word — word`.

**Consecutive dashes**: Multiple identical dashes (`--`, `––`, `——`) are
treated as single tokens and preserve their spacing.

### Edge Cases

The tokenizer correctly handles `1914 -1918` where `-1918` might appear to
be a negative number but is actually part of a year range.

## The token object

Each token is an instance of the class `Tok` that has three main properties:
`kind`, `txt` and `val`.

### The `kind` property

The `kind` property contains one of the following integer constants, 
defines within the `TOK` class:

| Constant      | Value   | Explanation         | Examples                  |
|---------------|---------|---------------------|---------------------------|
| PUNCTUATION   | 1       | Punctuation         | . ! ; % &                 |
| TIME          | 2       | Time (h, m, s)      | 11:35:40, kl. 7:05, klukkan 23:35 |
| DATE *        | 3       | Date (y, m, d)      | [Unused, see DATEABS and DATEREL] |
| YEAR          | 4       | Year                | árið 874 e.Kr., 1965, 44 f.Kr. |
| NUMBER        | 5       | Number              | 100, 1.965, 1.965,34, 1,965.34, 2⅞ |
| WORD          | 6       | Word                | kattaeftirlit, hunda- og kattaeftirlit |
| TELNO         | 7       | Telephone number    | 5254764, 699-4244, 410 4000 |
| PERCENT       | 8       | Percentage          | 78%                       |
| URL           | 9       | URL                 | https://greynir.is, http://tiny.cc/28695y |
| ORDINAL       | 10      | Ordinal number      | 30., XVIII.               |
| TIMESTAMP *   | 11      | Timestamp           | [Unused, see TIMESTAMPABS and TIMESTAMPREL] |
| CURRENCY *    | 12      | Currency name       | [Unused]                  |
| AMOUNT        | 13      | Amount              | €2.345,67, 750 þús.kr., 2,7 mrð. USD, kr. 9.900, EUR 200 |
| PERSON *      | 14      | Person name         | [Unused]                  |
| EMAIL         | 15      | E-mail              | `fake@news.is`          |
| ENTITY *      | 16      | Named entity        | [Unused]                  |
| UNKNOWN       | 17      | Unknown token       |                           |
| DATEABS       | 18      | Absolute date       | 30. desember 1965, 30/12/1965, 1965-12-30, 1965/12/30 |
| DATEREL       | 19      | Relative date       | 15. mars, 15/3, 15.3., mars 1911 |
| TIMESTAMPABS  | 20      | Absolute timestamp  | 30. desember 1965 11:34, 1965-12-30 kl. 13:00 |
| TIMESTAMPREL  | 21      | Relative timestamp  | 30. desember kl. 13:00  |
| MEASUREMENT   | 22      | Value with a measurement unit | 690 MW, 1.010 hPa, 220 m², 80° C |
| NUMWLETTER    | 23      | Number followed by a single letter | 14a, 7B |
| DOMAIN        | 24      | Domain name         | greynir.is, Reddit.com, www.wikipedia.org |
| HASHTAG       | 25      | Hashtag             | #MeToo, #12stig           |
| MOLECULE      | 26      | Molecular formula   | H2SO4, CO2                |
| SSN           | 27      | Social security number (*kennitala*) | 591213-1480 |
| USERNAME      | 28      | Twitter user handle | @username_123             |
| SERIALNUMBER  | 29      | Serial number       | 394-5388, 12-345-6789     |
| COMPANY *     | 30      | Company name        | [Unused]                  |
| S_BEGIN       | 11001   | Start of sentence   |                           |
| S_END         | 11002   | End of sentence     |                           |

(*) The token types marked with an asterisk are reserved for
the [GreynirEngine package](https://github.com/mideind/GreynirEngine) and
not currently returned by the tokenizer.

To obtain a descriptive text for a token kind, use
`TOK.descr[token.kind]` (see example above).

### The `txt` property

The `txt` property contains the original source text for the token, 
with the following exceptions:

* All contiguous whitespace (spaces, tabs, newlines) is coalesced
  into single spaces (`" "`) within the `txt` string. A date
  token that is parsed from a source text of `"29.  \n   janúar"`
  thus has a `txt` of `"29. janúar"`.

* Tokenizer automatically merges Unicode `COMBINING ACUTE ACCENT`
  (code point 769) and `COMBINING DIAERESIS` (code point 776)
  with vowels to form single code points for the Icelandic letters
  á, é, í, ó, ú, ý and ö, in both lower and upper case. (This behavior
  can be disabled; see the `replace_composite_glyphs` option described
  above.)

* If the `convert_numbers` option is specified (see above), English-style
  thousand and decimal separators are converted to Icelandic ones
  (*10,345.67* becomes *10.345,67*).

* If the `replace_html_escapes` option is set, Tokenizer replaces
  HTML-style escapes (`&aacute;`) with the characters
  being escaped (`á`).

### The `val` property

The `val` property contains auxiliary information, corresponding to
the token kind, as follows:

- For `TOK.PUNCTUATION`, the `val` field contains a tuple with
  two items: `(whitespace, normalform)`. The first item (`token.val[0]`)
specifies the whitespace normally found around the symbol in question,
as an integer:

    TP_LEFT = 1   # Whitespace to the left
    TP_CENTER = 2 # Whitespace to the left and right
    TP_RIGHT = 3  # Whitespace to the right
    TP_NONE = 4   # No whitespace

The second item (`token.val[1]`) contains a normalized representation of the
punctuation. For instance, various forms of single and double
quotes are represented as Icelandic ones (i.e. „these“ or ‚these‘) in
normalized form, and ellipsis ("...") are represented as the single
character "…".

- For `TOK.TIME`, the `val` field contains an
  `(hour, minute, second)` tuple.

- For `TOK.DATEABS`, the `val` field contains a
  `(year, month, day)` tuple (all 1-based).

- For `TOK.DATEREL`, the `val` field contains a
  `(year, month, day)` tuple (all 1-based),
  except that a least one of the tuple fields is missing and set to 0.
  Example: *3. júní* becomes `TOK.DATEREL` with the fields `(0, 6, 3)`
  as the year is missing.

- For `TOK.YEAR`, the `val` field contains the year as an integer.
  A negative number indicates that the year is BCE (*fyrir Krist*), 
specified with the suffix *f.Kr.* (e.g. *árið 33 f.Kr.*).

- For `TOK.NUMBER`, the `val` field contains a tuple
  `(number, None, None)`.
  (The two empty fields are included for compatibility with Greynir.)

- For `TOK.WORD`, the `val` field contains the full expansion
  of an abbreviation, as a list containing a single tuple, or `None`
  if the word is not abbreviated.

- For `TOK.PERCENT`, the `val` field contains a tuple
  of `(percentage, None, None)`.

- For `TOK.ORDINAL`, the `val` field contains the ordinal value
  as an integer. The original ordinal may be a decimal number
  or a Roman numeral.

- For `TOK.TIMESTAMP`, the `val` field contains
  a `(year, month, day, hour, minute, second)` tuple.

- For `TOK.AMOUNT`, the `val` field contains
  an `(amount, currency, None, None)` tuple. The amount is a float, and
  the currency is an ISO currency code, e.g. *USD* for dollars ($ sign),
  *EUR* for euros (€ sign) or *ISK* for Icelandic króna
  (*kr.* abbreviation). (The two empty fields are included for
  compatibility with Greynir.)

- For `TOK.MEASUREMENT`, the `val` field contains a `(unit, value)`
  tuple, where `unit` is a base SI unit (such as `g`, `m`,
  `m²`, `s`, `W`, `Hz`, `K` for temperature in Kelvin).

- For `TOK.TELNO`, the `val` field contains a tuple: `(number, cc)`
  where the first item is the phone number
  in a normalized `NNN-NNNN` format, i.e. always including a hyphen,
  and the second item is the country code, eventually prefixed by `+`.
  The country code defaults to `354` (Iceland).

## Abbreviations

Abbreviations recognized by Tokenizer are defined in the `Abbrev.conf`
file, found in the `src/tokenizer/` directory. This is a text file with
abbreviations, their definitions and explanatory comments.

When an abbreviation is encountered, it is recognized as a word token
(i.e. having its `kind` field equal to `TOK.WORD`).
Its expansion(s) are included in the token's
`val` field as a list containing tuples of the format
`(ordmynd, utg, ordfl, fl, stofn, beyging)`.
An example is *o.s.frv.*, which results in a `val` field equal to
`[('og svo framvegis', 0, 'ao', 'frasi', 'o.s.frv.', '-')]`.

The tuple format is designed to be compatible with the
[*Database of Icelandic Morphology* (*DIM*)](https://bin.arnastofnun.is/DMII/),
*Beygingarlýsing íslensks nútímamáls*, i.e. the so-called *Sigrúnarsnið*.

## Development installation

To install Tokenizer in development mode, where you can easily
modify the source files (assuming you have `git` available):

```console
$ git clone https://github.com/mideind/Tokenizer
$ cd Tokenizer
$ # [ Activate your virtualenv here, if you have one ]
$ pip install -e ".[dev]"
```

## Test suite

Tokenizer comes with a large test suite.
The file `test/test_tokenizer.py` contains built-in tests that
run under `pytest`.

To run the built-in tests, install [pytest](https://docs.pytest.org/en/latest/),
`cd` to your `Tokenizer` subdirectory (and optionally
activate your virtualenv), then run:

```console
$ python -m pytest
```

The file `test/toktest_large.txt` contains a test set of 13,075 lines.
The lines test sentence detection, token detection and token classification.
For analysis, `test/toktest_large_gold_perfect.txt` contains
the expected output of a perfect shallow tokenization, and
`test/toktest_large_gold_acceptable.txt` contains the current output of the
shallow tokenization.

The file `test/Overview.txt` (only in Icelandic) contains a description
of the test set, including line numbers for each part in both
`test/toktest_large.txt` and `test/toktest_large_gold_acceptable.txt`,
and a tag describing what is being tested in each part.

It also contains a description of a perfect shallow tokenization for each part,
acceptable tokenization and the current behaviour.
As such, the description is an analysis of which edge cases the tokenizer
can handle and which it can not.

To test the tokenizer on the large test set the following needs to be typed
in the command line:

```console
$ tokenize test/toktest_large.txt test/toktest_large_out.txt
```

To compare it to the acceptable behaviour:

```console
$ diff test/toktest_large_out.txt test/toktest_large_gold_acceptable.txt > diff.txt
```

The file `test/toktest_normal.txt` contains a running text from recent
news articles, containing no edge cases. The gold standard for that file
can be found in the file `test/toktest_normal_gold_expected.txt`.

## Changelog

* Version 3.6.0: Removed the deprecated `--handle_kludgy_ordinals` CLI flag
  and `handle_kludgy_ordinals` API option. Kludgy ordinals (e.g. `1sti`, `3ja`)
  are now always passed through unchanged as word tokens.
* Version 3.5.5: Maintenance release with modernized package metadata (PEP 517/518
  build system, enhanced PyPI discoverability with keywords and URLs), improved
  tooling configuration (ruff, mypy, pytest), and type checking improvements.
  CI updated for setuptools compatibility.
* Version 3.5.4: Improved dash and hyphen handling: free-standing hyphens
  between words now preserve spaces, year ranges normalize to en-dash (with
  `normalize=True`), em-dashes are centered with spaces, and consecutive
  identical dashes are handled as single tokens. Fixed edge case where negative
  years in ranges (e.g., "1914 -1918") were incorrectly parsed as negative
  numbers.
* Version 3.5.3: Fixed PyPI package description display (README.md reference in pyproject.toml)
* Version 3.5.2: Improved JSON output format and BIN_Tuple representation; documentation updates
* Version 3.5.1: Fixed bug in composite glyph handling
* Version 3.5.0: Better handling of colon-separated timestamps and URI schemes, modernization, and more.
* Version 3.4.5: Compatibility with Python 3.13. Now requires Python 3.9 or later.
* Version 3.4.4: Better handling of abbreviations
* Version 3.4.3: Various minor fixes. Now requires Python 3.8 or later.
* Version 3.4.2: Abbreviations and phrases added, `META_BEGIN` token added.
* Version 3.4.1: Improved performance on long input chunks.
* Version 3.4.0: Improved handling and normalization of punctuation.
* Version 3.3.2: Internal refactoring; bug fixes in paragraph handling.
* Version 3.3.1: Fixed bug where opening quotes at the start of paragraphs
  were sometimes incorrectly recognized and normalized.
* Version 3.2.0: Numbers and amounts that consist of word tokens only ('sex hundruð')
  are now returned as the original `TOK.WORD` s ('sex' and 'hundruð'), not as single
  coalesced `TOK.NUMBER` / `TOK.AMOUNT` /etc. tokens.
* Version 3.1.2: Changed paragraph markers to `[[` and `]]` (removing spaces).
* Version 3.1.1: Minor fixes; added Tok.from_token().
* Version 3.1.0: Added `-o` switch to the `tokenize` command to return original
  token text, enabling the tokenizer to run as a sentence splitter only.
* Version 3.0.0: Added tracking of character offsets for tokens within the
  original source text. Added full type annotations. Dropped Python 2.7 support.
* Version 2.5.0: Added arguments for all tokenizer options to the
  command-line tool. Type annotations enhanced.
* Version 2.4.0: Fixed bug where certain well-known word forms (*fá*, *fær*, *mín*, *sá*...)
  were being interpreted as (wrong) abbreviations. Also fixed bug where certain
  abbreviations were being recognized even in uppercase and at the end
  of a sentence, for instance *Örn.*
* Version 2.3.1: Various bug fixes; fixed type annotations for Python 2.7;
  the token kind `NUMBER WITH LETTER` is now `NUMWLETTER`.
* Version 2.3.0: Added the `replace_html_escapes` option to
  the `tokenize()` function.
* Version 2.2.0: Fixed `correct_spaces()` to handle compounds such as
  *Atvinnu-, nýsköpunar- og ferðamálaráðuneytið* and
  *bensínstöðvar, -dælur og -tankar*.
* Version 2.1.0: Changed handling of periods at end of sentences if they are
  a part of an abbreviation. Now, the period is kept attached to the abbreviation, 
  not split off into a separate period token, as before.
* Version 2.0.7: Added `TOK.COMPANY` token type; fixed a few abbreviations;
  renamed parameter `text` to `text_or_gen` in functions that accept a string
  or a string iterator.
* Version 2.0.6: Fixed handling of abbreviations such as *m.v.* (*miðað við*)
  that should not start a new sentence even if the following word is capitalized.
* Version 2.0.5: Fixed bug where single uppercase letters were erroneously
  being recognized as abbreviations, causing prepositions such as 'Í' and 'Á'
  at the beginning of sentences to be misunderstood in GreynirEngine.
* Version 2.0.4: Added imperfect abbreviations (*amk.*, *osfrv.*); recognized
  *klukkan hálf tvö* as a `TOK.TIME`.
* Version 2.0.3: Fixed bug in `detokenize()` where abbreviations, domains
  and e-mails containing periods were wrongly split.
* Version 2.0.2: Spelled-out day ordinals are no longer included as a part of
  `TOK.DATEREL` tokens. Thus, *þriðji júní* is now a `TOK.WORD`
  followed by a `TOK.DATEREL`. *3. júní* continues to be parsed as
  a single `TOK.DATEREL`.
* Version 2.0.1: Order of abbreviation meanings within the `token.val` field
  made deterministic; fixed bug in measurement unit handling.
* Version 2.0.0: Added command line tool; added `split_into_sentences()`
  and `detokenize()` functions; removed `convert_telno` option;
  splitting of coalesced tokens made more robust;
  added `TOK.SSN`, `TOK.MOLECULE`, `TOK.USERNAME` and
  `TOK.SERIALNUMBER` token kinds; abbreviations can now have multiple
  meanings.
* Version 1.4.0: Added the `**options` parameter to the
  `tokenize()` function, giving control over the handling of numbers
  and telephone numbers.
* Version 1.3.0: Added `TOK.DOMAIN` and `TOK.HASHTAG` token types; 
  improved handling of capitalized month name *Ágúst*, which is
  now recognized when following an ordinal number; improved recognition
  of telephone numbers; added abbreviations.
* Version 1.2.3: Added abbreviations; updated GitHub URLs.
* Version 1.2.2: Added support for composites with more than two parts, i.e.
  *„dómsmála-, ferðamála-, iðnaðar- og nýsköpunarráðherra“*; added support for
  `±` sign; added several abbreviations.
* Version 1.2.1: Fixed bug where the name *Ágúst* was recognized
  as a month name; Unicode nonbreaking and invisible space characters
  are now removed before tokenization.
* Version 1.2.0: Added support for Unicode fraction characters; 
  enhanced handing of degrees (°, °C, °F); fixed bug in cubic meter
  measurement unit; more abbreviations.
* Version 1.1.2: Fixed bug in liter (`l` and `ltr`) measurement units.
* Version 1.1.1: Added `mark_paragraphs()` function.
* Version 1.1.0: All abbreviations in `Abbrev.conf` are now
  returned with their meaning in a tuple in `token.val`;
  handling of 'mbl.is' fixed.
* Version 1.0.9: Added abbreviation 'MAST'; harmonized copyright headers.
* Version 1.0.8: Bug fixes in `DATEREL`, `MEASUREMENT` and `NUMWLETTER`
  token handling; added 'kWst' and 'MWst' measurement units; blackened.
* Version 1.0.7: Added `TOK.NUMWLETTER` token type.
* Version 1.0.6: Automatic merging of Unicode `COMBINING ACUTE ACCENT` and
  `COMBINING DIAERESIS` code points with vowels.
* Version 1.0.5: Date/time and amount tokens coalesced to a further extent.
* Version 1.0.4: Added `TOK.DATEABS`, `TOK.TIMESTAMPABS`,
  `TOK.MEASUREMENT`.

## MIT License

Copyright (C) 2016-2025 [Miðeind ehf.](https://mideind.is)
Original author: Vilhjálmur Þorsteinsson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
