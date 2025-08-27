#!/usr/bin/env python
"""

Tokenizer for Icelandic text

Copyright (C) 2016-2025 Miðeind ehf.
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


This is an executable program wrapper (main module) for the Tokenizer
package. It can be used to invoke the Tokenizer from the command line,
or via fork() or exec(), with the command 'tokenize'. The main() function
of this module is registered as a CLI command in pyproject.toml.

"""

from typing import (
    Dict,
    Iterable,
    List,
    Optional,
    TextIO,
    Iterator,
    Callable,
    Any,
    Tuple,
    Union,
    cast,
)

import sys
import argparse
import json
from functools import partial

from .definitions import AmountTuple, BIN_Tuple, NumberTuple, PunctuationTuple
from .tokenizer import TOK, Tok, tokenize
from . import __version__ as tokenizer_version


# Define the command line arguments

parser = argparse.ArgumentParser(description="Tokenizes Icelandic text")

parser.add_argument(
    "infile",
    nargs="?",
    type=argparse.FileType("r", encoding="utf-8"),
    default=sys.stdin,
    help="UTF-8 text file to tokenize",
)

parser.add_argument(
    "outfile",
    nargs="?",
    type=argparse.FileType("w", encoding="utf-8"),
    default=sys.stdout,
    help="UTF-8 output text file",
)

group = parser.add_mutually_exclusive_group()

group.add_argument(
    "--csv", help="Output one token per line in CSV format", action="store_true"
)
group.add_argument(
    "--json", help="Output one token per line in JSON format", action="store_true"
)

parser.add_argument(
    "-s",
    "--one_sent_per_line",
    action="store_true",
    help="Input contains one sentence per line",
)

parser.add_argument(
    "-m",
    "--convert_measurements",
    action="store_true",
    help="Degree signal in temperature tokens normalized (200° C -> 200 °C)",
)

parser.add_argument(
    "-p",
    "--coalesce_percent",
    action="store_true",
    help=(
        "Numbers combined into one token with percentage word forms "
        "(prósent/prósentustig/hundraðshlutar)"
    ),
)

parser.add_argument(
    "-n",
    "--normalize",
    action="store_true",
    help="Outputs normalized value of punctuation tokens instead of original text",
)

parser.add_argument(
    "-o",
    "--original",
    action="store_true",
    help="Outputs original text of tokens",
)

parser.add_argument(
    "-g",
    "--keep_composite_glyphs",
    action="store_true",
    help="Composite glyphs not replaced with a single code point",
)

parser.add_argument(
    "-e",
    "--replace_html_escapes",
    action="store_true",
    help="Escape codes from HTML replaced",
)

parser.add_argument(
    "-c",
    "--convert_numbers",
    action="store_true",
    help=(
        "English-style decimal points and thousands separators "
        "in numbers changed to Icelandic style"
    ),
)

parser.add_argument(
    "-k",
    "--handle_kludgy_ordinals",
    type=int,
    default=0,
    help=(
        "Kludgy ordinal handling defined.\n"
        "\t0: Returns the original word form.\n"
        "\t1: Ordinals returned as pure words.\n"
        "\t2: Ordinals returned as numbers."
    ),
)

parser.add_argument(
    "-v",
    "--version",
    action="version",
    version=f"%(prog)s {tokenizer_version}",
    help="Show the version number and exit",
)


def main() -> None:
    """Main function, called when the tokenize command is invoked"""

    args = parser.parse_args()
    options: Dict[str, bool] = {}

    def quote(s: str) -> str:
        """Return the string s within double quotes, and with any contained
        backslashes and double quotes escaped with a backslash"""
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

    def spanquote(lst: Iterable[int]) -> str:
        """Return the list lst as a string within double quotes"""
        return '"' + "-".join(str(x) for x in lst) + '"'

    def gen(f: TextIO) -> Iterator[str]:
        """Generate the lines of text in the input file"""
        for line in f:
            yield line

    def val(t: Tok, quote_word: bool = False) -> Any:
        """Return the value part of the token t"""
        if t.val is None:
            return None
        if t.kind == TOK.WORD:
            # Get the full expansion of an abbreviation
            mm = cast(List[BIN_Tuple], t.val)
            if quote_word:
                # Return a |-delimited list of possible meanings,
                # joined into a single string
                return quote("|".join(m[0] for m in mm))
            # Return a list of all possible meanings
            return [m[0] for m in mm]
        if t.kind in {TOK.PERCENT, TOK.NUMBER, TOK.CURRENCY}:
            return cast(NumberTuple, t.val)[0]
        if t.kind == TOK.AMOUNT:
            am = cast(AmountTuple, t.val)
            if quote_word:
                # Format as "1234.56|USD"
                return '"{0}|{1}"'.format(am[0], am[1])
            return am[0], am[1]
        if t.kind == TOK.S_BEGIN:
            return None
        if t.kind == TOK.PUNCTUATION:
            pt = cast(PunctuationTuple, t.val)
            return quote(pt[1]) if quote_word else pt[1]
        if quote_word and t.kind in {
            TOK.DATE,
            TOK.TIME,
            TOK.DATEABS,
            TOK.DATEREL,
            TOK.TIMESTAMP,
            TOK.TIMESTAMPABS,
            TOK.TIMESTAMPREL,
            TOK.TELNO,
            TOK.NUMWLETTER,
            TOK.MEASUREMENT,
        }:
            # Return a |-delimited list of numbers
            vv = cast(Tuple[Any, ...], t.val)
            return quote("|".join(str(v) for v in vv))
        if quote_word and isinstance(t.val, str):
            return quote(t.val)
        return t.val

    to_text: Callable[[Tok], str]
    if args.normalize:
        to_text = lambda t: t.punctuation if t.kind == TOK.PUNCTUATION else t.txt
    elif args.original:
        to_text = lambda t: t.original or ""
    else:
        to_text = lambda t: t.txt

    if args.convert_measurements:
        options["convert_measurements"] = True

    if args.coalesce_percent:
        options["coalesce_percent"] = True

    if args.keep_composite_glyphs:
        # True is the default in tokenizer.py
        options["replace_composite_glyphs"] = False

    if args.replace_html_escapes:
        options["replace_html_escapes"] = True

    if args.convert_numbers:
        options["convert_numbers"] = True

    if args.one_sent_per_line:
        options["one_sent_per_line"] = True

    if args.handle_kludgy_ordinals:
        options["handle_kludgy_ordinals"] = args.handle_kludgy_ordinals

    if args.original:
        options["original"] = args.original

    # Configure our JSON dump function
    json_dumps = partial(json.dumps, ensure_ascii=False, separators=(",", ":"))
    curr_sent: List[str] = []
    tsep = "" if args.original else " "  # token separator
    for t in tokenize(gen(args.infile), **options):
        if args.csv:
            # Output the tokens in CSV format, one line per token
            if t.txt:
                print(
                    "{0},{1},{2},{3},{4}".format(
                        t.kind,
                        quote(t.txt),
                        val(t, quote_word=True) or '""',
                        '""' if t.original is None else quote(t.original),
                        "[]" if t.origin_spans is None else spanquote(t.origin_spans),
                    ),
                    file=args.outfile,
                )
            elif t.kind == TOK.S_END:
                # Indicate end of sentence
                print('0,"","","",""', file=args.outfile)
        elif args.json:
            # Output the tokens in JSON format, one line per token
            d: Dict[str, Union[str, List[int]]] = {"k": TOK.descr[t.kind]}
            if cast(Optional[str], t.txt) is not None:
                d["t"] = t.txt
            v = val(t)
            if v is not None:
                d["v"] = v
            if t.original is not None:
                d["o"] = t.original
            if t.origin_spans is not None:
                d["s"] = t.origin_spans
            print(json_dumps(d), file=args.outfile)
        else:
            # Normal shallow parse, sentences separated by newline by default,
            # tokens separated by spaces
            if t.kind in TOK.END:
                # End of sentence/paragraph
                if curr_sent:
                    print(tsep.join(curr_sent), file=args.outfile)
                    curr_sent = []
            txt = to_text(t)
            if txt:
                curr_sent.append(txt)
    if curr_sent:
        print(tsep.join(curr_sent), file=args.outfile)


if __name__ == "__main__":
    main()
