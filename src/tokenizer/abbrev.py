# -*- encoding: utf-8 -*-
"""

    Abbreviations module for tokenization of Icelandic text

    Copyright(C) 2018 Miðeind ehf.
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

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from threading import Lock


class ConfigError(Exception):
    pass


class Abbreviations:

    """ Wrapper around dictionary of abbreviations, initialized from the config file """

    # Dictionary of abbreviations and their meanings
    DICT = {}
    MEANINGS = set()  # All abbreviation meanings
    # Single-word abbreviations, i.e. those with only one dot at the end
    SINGLES = set()
    # Potential sentence finishers, i.e. those with a dot at the end, marked with an asterisk
    # in the config file
    FINISHERS = set()
    # Abbreviations that should not be seen as such at the end of sentences, marked with
    # an exclamation mark in the config file
    NOT_FINISHERS = set()
    # Abbreviations that should not be seen as such at the end of sentences, but
    # are allowed in front of person names; marked with a hat ^ in the config file
    NAME_FINISHERS = set()

    # Ensure that only one thread initializes the abbreviations
    _lock = Lock()

    @staticmethod
    def add(abbrev, meaning, gender, fl=None):
        """ Add an abbreviation to the dictionary. Called from the config file handler. """
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
                    "Only abbreviations ending with periods can be marked as not-finishers"
                )
        elif abbrev.endswith("^"):
            # This abbreviation can be followed by a name; in other aspects it is like a not-finisher
            # (Example: 'próf.')
            name_finisher = True
            abbrev = abbrev[0:-1]
            if not abbrev.endswith("."):
                raise ConfigError(
                    "Only abbreviations ending with periods can be marked as name finishers"
                )
        if abbrev.endswith("!") or abbrev.endswith("*") or abbrev.endswith("^"):
            raise ConfigError(
                "!, * and ^ modifiers are mutually exclusive on abbreviations"
            )
        # Append the abbreviation and its meaning in tuple form
        if abbrev in Abbreviations.DICT:
            raise ConfigError(
                "Abbreviation '{0}' is defined more than once".format(abbrev)
            )
        Abbreviations.DICT[abbrev] = (
            meaning,
            0,
            gender,
            "skst" if fl is None else fl,
            abbrev,
            "-",
        )
        Abbreviations.MEANINGS.add(meaning)
        if abbrev[-1] == "." and "." not in abbrev[0:-1]:
            # Only one dot, at the end
            Abbreviations.SINGLES.add(abbrev[0:-1])  # Lookup is without the dot
        if finisher:
            Abbreviations.FINISHERS.add(abbrev)
        if not_finisher or name_finisher:
            # Both name finishers and not-finishers are added to the NOT_FINISHERS set
            Abbreviations.NOT_FINISHERS.add(abbrev)
        if name_finisher:
            Abbreviations.NAME_FINISHERS.add(abbrev)

    @staticmethod
    def has_meaning(abbrev):
        return abbrev in Abbreviations.DICT

    @staticmethod
    def has_abbreviation(meaning):
        return meaning in Abbreviations.MEANINGS

    @staticmethod
    def get_meaning(abbrev):
        """ Lookup meaning of abbreviation, if available """
        return (
            None if abbrev not in Abbreviations.DICT else Abbreviations.DICT[abbrev][0]
        )

    @staticmethod
    def _handle_abbreviations(s):
        """ Handle abbreviations in the settings section """
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
    def initialize():
        """ Read the abbreviations config file """
        with Abbreviations._lock:
            if len(Abbreviations.DICT):
                # Already initialized
                return
            from pkg_resources import resource_stream

            with resource_stream(__name__, "Abbrev.conf") as config:
                for b in config:
                    # We get lines as binary strings
                    s = b.decode("utf-8")
                    # Ignore comments
                    ix = s.find("#")
                    if ix >= 0:
                        s = s[0:ix]
                    s = s.strip()
                    if not s:
                        # Blank line: ignore
                        continue
                    if s[0] == "[":
                        # Section header (we are expecting [abbreviations])
                        if s != "[abbreviations]":
                            raise ConfigError("Wrong section header")
                        continue
                    Abbreviations._handle_abbreviations(s)
