# -*- encoding: utf-8 -*-
"""

    Type annotation stubs for Abbreviations

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
    Optional,
    Set,
    List,
    Dict,
    Tuple,
    Sequence,
)

Meaning = Tuple[str, int, str, str, str, str]
MeaningList = Sequence[Meaning]

class ConfigError(Exception):
    ...

class Abbreviations:

    DICT: Dict[str, MeaningList] = ...
    WRONGDICT: Dict[str, MeaningList] = ...
    NAME_FINISHERS: Set[str] = ...
    WRONGDOTS: Dict[str, List[str]] = ...
    @staticmethod
    def initialize() -> None: ...
    @staticmethod
    def has_abbreviation(meaning: str) -> bool: ...
    @staticmethod
    def get_meaning(abbrev: str) -> Optional[MeaningList]: ...
