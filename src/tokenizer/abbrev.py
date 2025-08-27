"""

Abbreviations module for tokenization of Icelandic text

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


This module reads the definition of abbreviations from the file
Abbrev.conf, assumed to be located in the same directory (or installation
resource library) as this Python source file.

"""

from typing import Dict, Generic, Iterator, List, Optional, Set, TypeVar

from threading import Lock
from collections import defaultdict
import importlib.resources as importlib_resources

from .definitions import BIN_Tuple


class ConfigError(Exception):
    pass


_T = TypeVar("_T")


class OrderedSet(Generic[_T]):
    """Shim class to provide an ordered set API on top
    of a dictionary. This is necessary to make abbreviation
    lookups predictable and repeatable, which they would not be
    if a standard Python set() was used."""

    def __init__(self) -> None:
        # Insertions are ordered in Python 3.7+ dicts
        self._dict: Dict[_T, None] = {}

    def add(self, item: _T) -> None:
        """Add an item at the end of the ordered set"""
        # For plain dicts in Python 3.7+, direct assignment works:
        # * If item is new, it is added at the end.
        # * If item already exists, its value is updated (to None again),
        #   and the order remains unchanged.
        self._dict[item] = None

    def __contains__(self, item: _T) -> bool:
        return item in self._dict

    def __iter__(self) -> Iterator[_T]:
        return self._dict.__iter__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({list(self._dict.keys())})"


class Abbreviations:
    """Wrapper around dictionary of abbreviations,
    initialized from the config file"""

    # Dictionary of abbreviations and their meanings
    DICT: Dict[str, OrderedSet[BIN_Tuple]] = defaultdict(OrderedSet)
    # Wrong versions of abbreviations
    WRONGDICT: Dict[str, OrderedSet[BIN_Tuple]] = defaultdict(OrderedSet)
    # All abbreviation meanings
    MEANINGS: Set[str] = set()
    # Single-word abbreviations, i.e. those with only one dot at the end
    SINGLES: Set[str] = set()
    # Set of abbreviations without periods, e.g. "td", "osfrv"
    WRONGSINGLES: Set[str] = set()
    # Potential sentence finishers, i.e. those with a dot at the end,
    # marked with an asterisk in the config file
    FINISHERS: Set[str] = set()
    # Abbreviations that should not be seen as such at the end of sentences,
    # marked with an exclamation mark in the config file
    NOT_FINISHERS: Set[str] = set()
    # Abbreviations that should not be seen as such at the end of sentences, but
    # are allowed in front of person names; marked with a hat ^ in the config file
    NAME_FINISHERS: Set[str] = set()
    # Wrong versions of abbreviations with possible corrections
    # wrong version : [correction1, correction2, ...]
    WRONGDOTS: Dict[str, List[str]] = defaultdict(list)
    # Word forms that should never be interpreted as abbreviations
    NOT_ABBREVIATIONS: Set[str] = set()

    # Ensure that only one thread initializes the abbreviations
    _lock = Lock()

    @staticmethod
    def add(abbrev: str, meaning: str, gender: str, fl: Optional[str] = None) -> None:
        """Add an abbreviation to the dictionary.
        Called from the config file handler."""
        # Check for sentence finishers
        finisher = False
        not_finisher = False
        name_finisher = False
        if abbrev.endswith("*"):
            # This abbreviation is explicitly allowed to finish a sentence
            finisher = True
            abbrev = abbrev[0:-1]
            if not abbrev.endswith("."):
                raise ConfigError(
                    "Only abbreviations ending with periods can be sentence finishers"
                )
        elif abbrev.endswith("!"):
            # A not-finisher cannot finish a sentence, because it is also a valid word
            # (Example: 'dags.', 'mín.', 'sek.')
            not_finisher = True
            abbrev = abbrev[0:-1]
            if not abbrev.endswith("."):
                raise ConfigError(
                    "Only abbreviations ending with periods "
                    "can be marked as not-finishers"
                )
        elif abbrev.endswith("^"):
            # This abbreviation is only to be interpreted as an abbreviation
            # if it is followed by a name (example: 'próf.' for 'prófessor').
            # This logic is not fully present in Tokenizer as information
            # about person names is needed to make it work. The full implementation,
            # using the NAME_FINISHERS set, is found in bintokenizer.py in
            # GreynirEngine.
            name_finisher = True
            abbrev = abbrev[0:-1]
            if not abbrev.endswith("."):
                raise ConfigError(
                    "Only abbreviations ending with periods "
                    "can be marked as name finishers"
                )
        if abbrev.endswith("!") or abbrev.endswith("*") or abbrev.endswith("^"):
            raise ConfigError(
                "!, * and ^ modifiers are mutually exclusive on abbreviations"
            )
        # Append the abbreviation and its meaning in tuple form
        # Multiple meanings are supported for each abbreviation
        Abbreviations.DICT[abbrev].add(
            BIN_Tuple(
                meaning,
                0,
                gender,
                "skst" if fl is None else fl,
                abbrev,
                "-",
            )
        )
        Abbreviations.MEANINGS.add(meaning)
        # Adding wrong versions of abbreviations
        if abbrev[-1] == "." and "." not in abbrev[0:-1]:
            # Only one dot, at the end
            # Lookup is without the dot
            wabbrev = abbrev[0:-1]
            Abbreviations.SINGLES.add(wabbrev)
            if finisher:
                Abbreviations.FINISHERS.add(wabbrev)
            Abbreviations.WRONGDOTS[wabbrev].append(abbrev)
            if len(wabbrev) > 1:
                # We don't add single letters (such as Í and Á)
                # as abbreviations, even though they are listed as such
                # in the form 'Í.' and 'Á.' for use within person names
                Abbreviations.WRONGDICT[wabbrev].add(
                    BIN_Tuple(
                        meaning,
                        0,
                        gender,
                        "skst" if fl is None else fl,
                        wabbrev,
                        "-",
                    )
                )

        elif "." in abbrev:
            # Only multiple dots, checked single dots above
            # Want to see versions with each one deleted,
            # and one where all are deleted
            indices = [pos for pos, char in enumerate(abbrev) if char == "."]
            for i in indices:
                # Removing one dot at a time
                wabbrev = abbrev[:i] + abbrev[i + 1 :]
                Abbreviations.WRONGDOTS[wabbrev].append(abbrev)
                Abbreviations.WRONGDICT[wabbrev].add(
                    BIN_Tuple(
                        meaning,
                        0,
                        gender,
                        "skst" if fl is None else fl,
                        wabbrev,
                        "-",
                    )
                )
            if len(indices) > 2:
                # 3 or 4 dots currently in vocabulary
                # Not all cases with 4 dots are handled.
                i1 = indices[0]
                i2 = indices[1]
                i3 = indices[2]
                wabbrevs: List[str] = []
                # 1 and 2 removed
                wabbrevs.append(abbrev[:i1] + abbrev[i1 + 1 : i2] + abbrev[i2 + 1 :])
                # 1 and 3 removed
                wabbrevs.append(abbrev[:i1] + abbrev[i1 + 1 : i3] + abbrev[i3 + 1 :])
                # 2 and 3 removed
                wabbrevs.append(abbrev[:i2] + abbrev[i2 + 1 : i3] + abbrev[i3 + 1 :])
                for wabbrev in wabbrevs:
                    Abbreviations.WRONGDOTS[wabbrev].append(abbrev)
                    Abbreviations.WRONGDICT[wabbrev].add(
                        BIN_Tuple(
                            meaning,
                            0,
                            gender,
                            "skst" if fl is None else fl,
                            wabbrev,
                            "-",
                        )
                    )
            # Removing all dots
            wabbrev = abbrev.replace(".", "")
            Abbreviations.WRONGSINGLES.add(wabbrev)
            Abbreviations.WRONGDOTS[wabbrev].append(abbrev)
            Abbreviations.WRONGDICT[wabbrev].add(
                BIN_Tuple(
                    meaning,
                    0,
                    gender,
                    "skst" if fl is None else fl,
                    wabbrev,
                    "-",
                )
            )
        if finisher:
            Abbreviations.FINISHERS.add(abbrev)
        if not_finisher:
            Abbreviations.NOT_FINISHERS.add(abbrev)
        if name_finisher:
            Abbreviations.NAME_FINISHERS.add(abbrev)

    @staticmethod
    def has_meaning(abbrev: str) -> bool:
        return abbrev in Abbreviations.DICT or abbrev in Abbreviations.WRONGDICT

    @staticmethod
    def has_abbreviation(meaning: str) -> bool:
        return meaning in Abbreviations.MEANINGS

    @staticmethod
    def get_meaning(abbrev: str) -> Optional[list[BIN_Tuple]]:
        """Look up meaning(s) of abbreviation, if available."""
        m = Abbreviations.DICT.get(abbrev)
        if not m:
            m = Abbreviations.WRONGDICT.get(abbrev)
        return list(m) if m else None

    @staticmethod
    def _handle_abbreviations(s: str) -> None:
        """Handle abbreviations in the settings section"""
        # Format: abbrev[*] = "meaning" gender (kk|kvk|hk)
        # An asterisk after an abbreviation ending with a period
        # indicates that the abbreviation may finish a sentence
        a = s.split("=", 1)  # maxsplit=1
        if len(a) != 2:
            raise ConfigError(
                "Wrong format for abbreviation: should be abbreviation = meaning"
            )
        abbrev = a[0].strip()
        if not abbrev:
            raise ConfigError(
                "Missing abbreviation. Format should be abbreviation = meaning."
            )
        m = a[1].strip().split('"')
        par = ""
        if len(m) >= 3:
            # Something follows the last quote
            par = m[-1].strip()
        gender = "hk"  # Default gender is neutral
        fl = None  # Default word category is None
        if par:
            p = par.split()
            if len(p) >= 1:
                gender = p[0].strip()
            if len(p) >= 2:
                fl = p[1].strip()
        Abbreviations.add(abbrev, m[1], gender, fl)

    @staticmethod
    def _handle_not_abbreviations(s: str) -> None:
        """Handle not_abbreviations in the settings section"""
        if len(s) < 3 or s[0] != '"' or s[-1] != '"':
            raise ConfigError("not_abbreviations should be enclosed in double quotes")
        Abbreviations.NOT_ABBREVIATIONS.add(s[1:-1])

    @staticmethod
    def initialize() -> None:
        """Read the abbreviations config file"""
        with Abbreviations._lock:
            if len(Abbreviations.DICT):
                # Already initialized
                return

            section = None

            p = importlib_resources.files("tokenizer").joinpath("Abbrev.conf")
            config = p.read_text(encoding="utf-8")

            for s in config.split("\n"):
                # Ignore comments
                ix = s.find("#")
                if ix >= 0:
                    s = s[0:ix]
                s = s.strip()
                if not s:
                    # Blank line: ignore
                    continue
                if s[0] == "[":
                    # Section header (we expect [abbreviations]/[not_abbreviations])
                    if s not in {"[abbreviations]", "[not_abbreviations]"}:
                        raise ConfigError("Wrong section header")
                    section = s
                    continue
                if section == "[abbreviations]":
                    Abbreviations._handle_abbreviations(s)
                elif section == "[not_abbreviations]":
                    Abbreviations._handle_not_abbreviations(s)
                else:
                    raise ConfigError("Content outside section")

            # Remove not_abbreviations from WRONGDICT
            for abbr in Abbreviations.NOT_ABBREVIATIONS:
                if abbr in Abbreviations.WRONGDICT:
                    del Abbreviations.WRONGDICT[abbr]
            Abbreviations.NOT_ABBREVIATIONS = set()
