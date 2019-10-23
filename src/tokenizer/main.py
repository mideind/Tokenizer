#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""

    Tokenizer for Icelandic text

    Copyright (C) 2019 Miðeind ehf.
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
    of this module is registered as a console_script entry point in setup.py.

"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import sys
import argparse
import json

from . import TOK, tokenize_without_annotation


parser = argparse.ArgumentParser(description="Tokenizes Icelandic text")

parser.add_argument(
    'infile',
    nargs='?',
    type=argparse.FileType('r', encoding="utf-8"),
    default=sys.stdin,
    help="UTF-8 text file to tokenize",
)
parser.add_argument(
    'outfile',
    nargs='?',
    type=argparse.FileType('w', encoding="utf-8"),
    default=sys.stdout,
    help="UTF-8 output text file"
)

parser.add_argument(
    "--moses",
    help="Use Moses-compatible token splitting", action="store_true"
)

group = parser.add_mutually_exclusive_group()
group.add_argument(
    "--csv",
    help="Output one token per line in CSV format", action="store_true"
)
group.add_argument(
    "--json",
    help="Output one token per line in JSON format", action="store_true"
)


def quote(s):
    """ Return the string s within double quotes, and with any contained
        backslashes and double quotes escaped with a backslash """
    return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\""


def main():

    args = parser.parse_args()
    options = dict()

    def gen(f):
        for line in f:
            yield line

    def val(t, quote_word=False):
        if t.val is None:
            return None
        if t.kind == TOK.WORD:
            # Get the full expansion of an abbreviation
            if quote_word:
                return quote(t.val[0][0])
            return t.val[0][0]
        if t.kind == TOK.PERCENT or t.kind == TOK.NUMBER:
            return t.val[0]
        if t.kind == TOK.S_BEGIN:
            return None
        return t.val

    curr_line = []

    for t in tokenize_without_annotation(gen(args.infile), **options):
        if args.csv:
            if t.txt:
                print(
                    "{0},{1},{2}"
                    .format(t.kind, quote(t.txt), val(t, quote_word=True) or ""),
                    file=args.outfile
                )
        elif args.json:
            d = dict(k=t.kind)
            if t.txt is not None:
                d["t"] = t.txt
            v = val(t)
            if v is not None:
                d["v"] = v
            print(
                json.dumps(
                    d, ensure_ascii=False, separators=(',', ':')
                ),
                file=args.outfile
            )
        else:
            if t.kind in TOK.END:
                print(" ".join(curr_line), file=args.outfile)
                curr_line = []
            elif t.txt:
                curr_line.append(t.txt)

    if curr_line:
        print(" ".join(curr_line), file=args.outfile)


if __name__ == "__main__":
    main()
