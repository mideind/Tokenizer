# -*- encoding: utf-8 -*-
"""

    Type annotation stubs for Tokenizer

    Copyright (C) 2021 Miðeind ehf.
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

from typing import (
    Any,
    Optional,
    Union,
    Set,
    List,
    Dict,
    Tuple,
    Iterable,
    Iterator,
    NamedTuple,
    Sequence,
)

class Tok(NamedTuple):
    kind: int
    txt: str
    val: Any

Meaning = Tuple[str, int, str, str, str, str]
MeaningList = Sequence[Meaning]
PersonNameList = Sequence[Tuple[str, Optional[str], Optional[str]]]
Options = Union[bool, int, str]
SentenceTuple = Tuple[int, List[Tok]]
StringIterable = Union[str, Iterable[str]]

TP_LEFT: int = ...
TP_CENTER: int = ...
TP_RIGHT: int = ...
TP_NONE: int = ...
TP_WORD: int = ...

KLUDGY_ORDINALS_PASS_THROUGH: int = ...
KLUDGY_ORDINALS_MODIFY: int = ...
KLUDGY_ORDINALS_TRANSLATE: int = ...

class TOK:

    PUNCTUATION: int = ...
    TIME: int = ...
    DATE: int = ...
    YEAR: int = ...
    NUMBER: int = ...
    WORD: int = ...
    TELNO: int = ...
    PERCENT: int = ...
    URL: int = ...
    ORDINAL: int = ...
    TIMESTAMP: int = ...
    CURRENCY: int = ...
    AMOUNT: int = ...
    PERSON: int = ...
    EMAIL: int = ...
    ENTITY: int = ...
    UNKNOWN: int = ...
    DATEABS: int = ...
    DATEREL: int = ...
    TIMESTAMPABS: int = ...
    TIMESTAMPREL: int = ...
    MEASUREMENT: int = ...
    NUMWLETTER: int = ...
    DOMAIN: int = ...
    HASHTAG: int = ...
    MOLECULE: int = ...
    SSN: int = ...
    USERNAME: int = ...
    SERIALNUMBER: int = ...
    COMPANY: int = ...
    S_SPLIT: int = ...
    P_BEGIN: int = ...
    P_END: int = ...
    S_BEGIN: int = ...
    S_END: int = ...
    X_END: int = ...
    END: Set[int] = ...
    TEXT: Set[int] = ...
    TEXT_EXCL_PERSON: Set[int] = ...
    descr: Dict[int, str] = ...
    @staticmethod
    def Punctuation(w: str, normalized: Optional[str] = ...) -> Tok: ...
    @staticmethod
    def Time(w: str, h: int, m: int, s: int) -> Tok: ...
    @staticmethod
    def Date(w: str, y: int, m: int, d: int) -> Tok: ...
    @staticmethod
    def Dateabs(w: str, y: int, m: int, d: int) -> Tok: ...
    @staticmethod
    def Daterel(w: str, y: int, m: int, d: int) -> Tok: ...
    @staticmethod
    def Timestamp(w: str, y: int, mo: int, d: int, h: int, m: int, s: int) -> Tok: ...
    @staticmethod
    def Timestampabs(
        w: str, y: int, mo: int, d: int, h: int, m: int, s: int
    ) -> Tok: ...
    @staticmethod
    def Timestamprel(
        w: str, y: int, mo: int, d: int, h: int, m: int, s: int
    ) -> Tok: ...
    @staticmethod
    def Year(w: str, n: int) -> Tok: ...
    @staticmethod
    def Telno(w: str, telno: str, cc: str = ...) -> Tok: ...
    @staticmethod
    def Email(w: str) -> Tok: ...
    @staticmethod
    def Number(
        w: str,
        n: float,
        cases: Optional[List[str]] = ...,
        genders: Optional[List[str]] = ...,
    ) -> Tok: ...
    @staticmethod
    def NumberWithLetter(w: str, n: int, l: str) -> Tok: ...
    @staticmethod
    def Currency(
        w: str,
        iso: str,
        cases: Optional[List[str]] = ...,
        genders: Optional[List[str]] = ...,
    ) -> Tok: ...
    @staticmethod
    def Amount(
        w: str,
        iso: str,
        n: float,
        cases: Optional[List[str]] = ...,
        genders: Optional[List[str]] = ...,
    ) -> Tok: ...
    @staticmethod
    def Percent(
        w: str,
        n: float,
        cases: Optional[List[str]] = ...,
        genders: Optional[List[str]] = ...,
    ) -> Tok: ...
    @staticmethod
    def Ordinal(w: str, n: int) -> Tok: ...
    @staticmethod
    def Url(w: str) -> Tok: ...
    @staticmethod
    def Domain(w: str) -> Tok: ...
    @staticmethod
    def Hashtag(w: str) -> Tok: ...
    @staticmethod
    def Ssn(w: str) -> Tok: ...
    @staticmethod
    def Molecule(w: str) -> Tok: ...
    @staticmethod
    def Username(w: str, username: str) -> Tok: ...
    @staticmethod
    def SerialNumber(w: str) -> Tok: ...
    @staticmethod
    def Measurement(w: str, unit: str, val: float) -> Tok: ...
    @staticmethod
    def Word(w: str, m: Optional[MeaningList] = ...) -> Tok: ...
    @staticmethod
    def Unknown(w: str) -> Tok: ...
    @staticmethod
    def Person(w: str, m: Optional[PersonNameList] = ...) -> Tok: ...
    @staticmethod
    def Entity(w: str) -> Tok: ...
    @staticmethod
    def Company(w: str) -> Tok: ...
    @staticmethod
    def Begin_Paragraph() -> Tok: ...
    @staticmethod
    def End_Paragraph() -> Tok: ...
    @staticmethod
    def Begin_Sentence(
        num_parses: int = ..., err_index: Optional[int] = ...
    ) -> Tok: ...
    @staticmethod
    def End_Sentence() -> Tok: ...
    @staticmethod
    def End_Sentinel() -> Tok: ...
    @staticmethod
    def Split_Sentence() -> Tok: ...

def normalized_text(token: Tok) -> str: ...
def text_from_tokens(tokens: Iterable[Tok]) -> str: ...
def normalized_text_from_tokens(tokens: Iterable[Tok]) -> str: ...
def is_valid_date(y: int, m: int, d: int) -> bool: ...
def parse_digits(w: str, convert_numbers: bool) -> Tok: ...
def could_be_end_of_sentence(
    next_token: Tok, test_set: Set[int] = ..., multiplier: bool = ...
) -> bool: ...
def parse_tokens(txt: StringIterable, **options: Options) -> Iterator[Tok]: ...
def parse_particles(
    token_stream: Iterator[Tok], **options: Options
) -> Iterator[Tok]: ...
def parse_sentences(token_stream: Iterator[Tok]) -> Iterator[Tok]: ...
def match_stem_list(token: Tok, stems: Dict[str, int]) -> Optional[int]: ...
def month_for_token(token: Tok, after_ordinal: bool = ...) -> Optional[int]: ...
def parse_phrases_1(token_stream: Iterator[Tok]) -> Iterator[Tok]: ...
def parse_date_and_time(token_stream: Iterator[Tok]) -> Iterator[Tok]: ...
def parse_phrases_2(
    token_stream: Iterator[Tok], coalesce_percent: bool = ...
) -> Iterator[Tok]: ...
def tokenize(text_or_gen: StringIterable, **options: Options) -> Iterator[Tok]: ...
def tokenize_without_annotation(
    text_or_gen: StringIterable, **options: Options
) -> Iterator[Tok]: ...
def split_into_sentences(
    text_or_gen: StringIterable, **options: Options
) -> Iterator[str]: ...
def mark_paragraphs(txt: str) -> str: ...
def paragraphs(tokens: Iterable[Tok]) -> Iterator[List[SentenceTuple]]: ...

RE_SPLIT_STR: str
RE_SPLIT: str

def correct_spaces(s: str) -> str: ...
def detokenize(tokens: Iterable[Tok], normalize: bool = ...) -> str: ...
def calculate_indexes(tokens: List[Tok], last_is_end: bool = ...) -> Tuple[List[int], List[int]]: ...
def generate_rough_tokens(text_or_gen: StringIterable, replace_composite_glyphs: bool = ...,
        replace_html_escapes: bool = ..., one_sent_per_line: bool = ...) -> Iterator[Tok]: ...
