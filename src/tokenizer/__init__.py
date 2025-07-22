"""

Copyright(C) 2016-2025 Miðeind ehf.
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

import importlib.metadata

from .definitions import (
    TP_LEFT,
    TP_CENTER,
    TP_RIGHT,
    TP_NONE,
    TP_WORD,
    EN_DASH,
    EM_DASH,
    KLUDGY_ORDINALS_PASS_THROUGH,
    KLUDGY_ORDINALS_MODIFY,
    KLUDGY_ORDINALS_TRANSLATE,
    BIN_Tuple,
    BIN_TupleList,
)
from .tokenizer import (
    TOK,
    Tok,
    tokenize,
    tokenize_without_annotation,
    split_into_sentences,
    parse_tokens,
    correct_spaces,
    detokenize,
    mark_paragraphs,
    paragraphs,
    normalized_text,
    normalized_text_from_tokens,
    text_from_tokens,
    calculate_indexes,
    generate_raw_tokens,
    TokenStream,
)
from .abbrev import Abbreviations, ConfigError

__author__ = "Miðeind ehf."
__copyright__ = "(C) 2016-2025 Miðeind ehf."
__version__ = importlib.metadata.version(__name__)

__all__ = (
    "__author__",
    "__copyright__",
    "__version__",
    "Abbreviations",
    "BIN_Tuple",
    "BIN_TupleList",
    "calculate_indexes",
    "ConfigError",
    "correct_spaces",
    "detokenize",
    "EM_DASH",
    "EN_DASH",
    "generate_raw_tokens",
    "KLUDGY_ORDINALS_MODIFY",
    "KLUDGY_ORDINALS_PASS_THROUGH",
    "KLUDGY_ORDINALS_TRANSLATE",
    "mark_paragraphs",
    "normalized_text_from_tokens",
    "normalized_text",
    "paragraphs",
    "parse_tokens",
    "split_into_sentences",
    "text_from_tokens",
    "Tok",
    "TOK",
    "tokenize_without_annotation",
    "tokenize",
    "TokenStream",
    "TP_CENTER",
    "TP_LEFT",
    "TP_NONE",
    "TP_RIGHT",
    "TP_WORD",
)
