# type: ignore

"""
    Test helper functions from definitions.py
    Copyright (C) 2025 Miðeind ehf.
"""

from tokenizer.definitions import valid_ssn, roman_to_int


def test_valid_ssn():
    # Test valid Icelandic SSNs (kennitölur)
    assert valid_ssn("311281-5189")
    assert valid_ssn("101275-5239")
    assert valid_ssn("500101-2880")
    assert valid_ssn("700269-1169")
    assert valid_ssn("010130-7789")
    assert valid_ssn("140543-3229")
    assert valid_ssn("120375-3509")
    assert valid_ssn("650376-0649")

    # Test invalid formats - wrong length
    assert not valid_ssn("01010-1019")
    assert not valid_ssn("0101011019")
    assert not valid_ssn("010101-10199")
    assert not valid_ssn("")
    assert not valid_ssn(None)

    # Test invalid formats - no hyphen
    assert not valid_ssn("0101011019")
    assert not valid_ssn("010101+1019")
    assert not valid_ssn("010101 1019")

    # Test invalid formats - hyphen in wrong position
    assert not valid_ssn("01010-11019")
    assert not valid_ssn("0101011-019")

    # Test checksum failures
    assert not valid_ssn("010101-0000")
    assert not valid_ssn("010101-1018")
    assert not valid_ssn("310354-2268")

    # Test invalid format - non-digit characters
    assert not valid_ssn("01010A-1019")
    assert not valid_ssn("010101-10B9")

    # Test completely malformed inputs
    assert not valid_ssn("abcde-fghi")
    assert not valid_ssn("12345")
    assert not valid_ssn("not-a-ssn")


def test_roman_to_int():
    # Test basic single numerals
    assert roman_to_int("I") == 1
    assert roman_to_int("V") == 5
    assert roman_to_int("X") == 10
    assert roman_to_int("L") == 50
    assert roman_to_int("C") == 100
    assert roman_to_int("D") == 500
    assert roman_to_int("M") == 1000

    # Test subtractive notation
    assert roman_to_int("IV") == 4
    assert roman_to_int("IX") == 9
    assert roman_to_int("XL") == 40
    assert roman_to_int("XC") == 90
    assert roman_to_int("CD") == 400
    assert roman_to_int("CM") == 900

    # Test additive notation and combinations
    assert roman_to_int("II") == 2
    assert roman_to_int("III") == 3
    assert roman_to_int("VI") == 6
    assert roman_to_int("VII") == 7
    assert roman_to_int("VIII") == 8
    assert roman_to_int("XI") == 11
    assert roman_to_int("XV") == 15
    assert roman_to_int("XVI") == 16

    # Test various complex numbers
    assert roman_to_int("XXIV") == 24
    assert roman_to_int("XLII") == 42
    assert roman_to_int("XCIX") == 99
    assert roman_to_int("CDXLIV") == 444
    assert roman_to_int("MCMXCIX") == 1999
    assert roman_to_int("MMXXIII") == 2023
    assert roman_to_int("MMMCMXCIX") == 3999
