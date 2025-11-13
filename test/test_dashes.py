"""

test_dashes.py

Tests for dash handling in Tokenizer module

Copyright (C) 2016-2025 by Miðeind ehf.
Original author: Vilhjálmur Þorsteinsson

This software is licensed under the MIT License:

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without restriction,
    including without limitation the rights to use, copy, modify, merge,
    publish, distribute, sublicense, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

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

import pytest
import tokenizer as t

EN = t.EN_DASH
EM = t.EM_DASH

YEAR_RANGES = [
    ("1914-1918", "1914-1918"),  # Regular hyphen
    ("1914 - 1918", "1914-1918"),  # Regular hyphen
    ("1914- 1918", "1914-1918"),  # Regular hyphen
    ("1914 -1918", "1914-1918"),  # Regular hyphen - negative year converted to positive
    ("1914-  1918", "1914-1918"),  # Regular hyphen
    ("1914 -  1918", "1914-1918"),  # Regular hyphen
    (
        "1914  -1918",
        "1914-1918",
    ),  # Regular hyphen - negative year converted to positive
    (f"1914{EN}1918", f"1914{EN}1918"),  # En dash
    (f"1914 {EN}1918", f"1914{EN}1918"),  # En dash
    (f"1914{EN} 1918", f"1914{EN}1918"),  # En dash
    (f"1914 {EN} 1918", f"1914{EN}1918"),  # En dash
    (f"1914{EM}1918", f"1914 {EM} 1918"),  # Em dash
    (f"1914 {EM}1918", f"1914 {EM} 1918"),  # Em dash
    (f"1914{EM} 1918", f"1914 {EM} 1918"),  # Em dash
    (f"1914 {EM} 1918", f"1914 {EM} 1918"),  # Em dash
]

THOUGHT_PAUSES = [
    (
        "Ég elska ketti - þeir eru svo sætir!",
        "Ég elska ketti - þeir eru svo sætir!",
    ),
    (
        "Ég elska ketti  - þeir eru svo sætir!",
        "Ég elska ketti - þeir eru svo sætir!",
    ),
    (
        "Ég elska ketti -  þeir eru svo sætir!",
        "Ég elska ketti - þeir eru svo sætir!",
    ),
    (
        f"Ég elska ketti {EN} þeir eru svo sætir!",
        f"Ég elska ketti {EN} þeir eru svo sætir!",
    ),
    (
        f"Ég elska ketti {EM} þeir eru svo sætir!",
        f"Ég elska ketti {EM} þeir eru svo sætir!",
    ),
]

COMPOSITE_WORD_CONTINUATIONS = [
    (
        "Ég fór í fjölskyldu- og húsdýragarðinn",
        "Ég fór í fjölskyldu- og húsdýragarðinn",
    ),
    (
        "Ég fór í fjölskyldu - og húsdýragarðinn",
        "Ég fór í fjölskyldu - og húsdýragarðinn",
    ),
    (
        f"Ég fór í fjölskyldu{EN} og húsdýragarðinn",
        f"Ég fór í fjölskyldu{EN} og húsdýragarðinn",
    ),
    (
        f"Ég fór í fjölskyldu {EN} og húsdýragarðinn",
        f"Ég fór í fjölskyldu {EN} og húsdýragarðinn",
    ),
    (
        f"Ég fór í fjölskyldu{EM} og húsdýragarðinn",
        f"Ég fór í fjölskyldu {EM} og húsdýragarðinn",
    ),
    (
        f"Ég fór í fjölskyldu {EM} og húsdýragarðinn",
        f"Ég fór í fjölskyldu {EM} og húsdýragarðinn",
    ),
    (
        f"Ég fór í fjölskyldu {EM}og húsdýragarðinn",
        f"Ég fór í fjölskyldu {EM} og húsdýragarðinn",
    ),
    (
        "Forstjóri Barna- og fjölskyldustofu segir dæmi um að…",
        "Forstjóri Barna- og fjölskyldustofu segir dæmi um að…",
    ),
    (
        f"Forstjóri Barna{EN} og fjölskyldustofu segir dæmi um að…",
        f"Forstjóri Barna{EN} og fjölskyldustofu segir dæmi um að…",
    ),
    (
        f"Innflutningur bensín-, dísel- og rafmagnsbíla hefur aukist.",
        f"Innflutningur bensín-, dísel- og rafmagnsbíla hefur aukist.",
    ),
    (
        f"Innflutningur bensín{EN}, dísel{EN} og rafmagnsbíla hefur aukist.",
        f"Innflutningur bensín{EN}, dísel{EN} og rafmagnsbíla hefur aukist.",
    ),
]

COMPOUND_WORDS = [
    ("Austur-Skaftafellssýsla", "Austur-Skaftafellssýsla"),  # Regular hyphen
    (f"Austur{EN}Skaftafellssýsla", f"Austur{EN}Skaftafellssýsla"),  # En dash
    (f"Austur{EM}Skaftafellssýsla", f"Austur {EM} Skaftafellssýsla"),  # Em dash
]

BEGIN_DASHES = [
    ("- Byrjar á bandstriki", "-Byrjar á bandstriki"),
    (f"{EN} Byrjar á en striki", f"{EN}Byrjar á en striki"),
    (
        f"{EM} Byrjar á em striki",
        f"{EM} Byrjar á em striki",
    ),  # Should preserve space after
]

END_DASHES = [
    ("Endar á bandstriki-", "Endar á bandstriki-"),
    ("Endar á bandstriki -", "Endar á bandstriki -"),
    (f"Endar á en striki{EN}", f"Endar á en striki{EN}"),
    (f"Endar á en striki {EN}", f"Endar á en striki {EN}"),
    (
        f"Endar á em striki{EM}",
        f"Endar á em striki {EM}",
    ),  # Should preserve space before
    (
        f"Endar á em striki {EM}",
        f"Endar á em striki {EM}",
    ),  # Should preserve space before
]

MULTIPLE_DASHES_IN_SEQUENCE = [
    ("This is -- a test", "This is -- a test"),  # Multiple hyphens
    (f"This is {EN}{EN} a test", f"This is {EN}{EN} a test"),  # Multiple en dashes
    (
        f"This is {EM}{EM} a test",
        f"This is {EM}{EM} a test",
    ),  # Multiple em dashes - MUST preserve spaces
]


@pytest.mark.parametrize("test_pair", YEAR_RANGES)
def test_year_ranges_tokenize(test_pair: tuple[str, str]) -> None:
    """Test year ranges without spaces using different dash types."""
    text_in, text_out = test_pair
    # Test tokenize + detokenize preserves text
    tokens = list(t.tokenize(text_in))
    detok = t.detokenize(tokens)
    assert (
        detok == text_out
    ), f"detokenize failed for {repr(text_in)}: got {repr(detok)}"


@pytest.mark.parametrize("test_pair", YEAR_RANGES)
def test_year_ranges_correct_spaces(test_pair: tuple[str, str]) -> None:
    """Test year ranges without spaces using different dash types."""
    text_in, text_out = test_pair
    # Test split_into_sentences + correct_spaces preserves text
    sentences = list(t.split_into_sentences(text_in))
    if sentences:
        corrected = t.correct_spaces(sentences[0])
        assert (
            corrected == text_out
        ), f"correct_spaces failed for {repr(text_in)}: got {repr(corrected)}"


def test_year_ranges_normalize_to_en_dash() -> None:
    """Test that year ranges with hyphens normalize to EN_DASH when normalize=True.

    According to Icelandic spelling rules, EN_DASH is preferred between years/dates.
    """
    test_cases = [
        ("1914-1918", f"1914{EN}1918"),  # Hyphen normalized to EN_DASH
        ("1914 -1918", f"1914{EN}1918"),  # Negative year edge case
        ("1914 - 1918", f"1914{EN}1918"),  # Hyphen with spaces
        (f"1914{EN}1918", f"1914{EN}1918"),  # EN_DASH unchanged
        (f"1914 {EN}1918", f"1914{EN}1918"),  # Hyphen normalized to EN_DASH
        (f"1914 {EN} 1918", f"1914{EN}1918"),  # Hyphen normalized to EN_DASH
    ]

    for text_in, expected in test_cases:
        tokens = list(t.tokenize(text_in))
        detok = t.detokenize(tokens, normalize=True)
        assert (
            detok == expected
        ), f"normalize=True failed for {repr(text_in)}: expected {repr(expected)}, got {repr(detok)}"


@pytest.mark.parametrize("test_pair", THOUGHT_PAUSES)
def test_thought_pauses_tokenize(test_pair: tuple[str, str]) -> None:
    """Test thought pauses/parenthetical remarks with spaces using different dash types.

    Em dashes inside text should ALWAYS have spaces on both sides.
    """
    text_in, text_out = test_pair
    # Test tokenize + detokenize preserves text
    tokens = list(t.tokenize(text_in))
    detok = t.detokenize(tokens)
    assert (
        detok == text_out
    ), f"detokenize failed for {repr(text_in)}: got {repr(detok)}"


@pytest.mark.parametrize("test_pair", THOUGHT_PAUSES)
def test_thought_pauses_correct_spaces(test_pair: tuple[str, str]) -> None:
    """Test thought pauses/parenthetical remarks with spaces using different dash types.

    Em dashes inside text should ALWAYS have spaces on both sides.
    """
    text_in, text_out = test_pair
    # Test split_into_sentences + correct_spaces preserves text
    sentences = list(t.split_into_sentences(text_in))
    if sentences:
        corrected = t.correct_spaces(sentences[0])
        assert (
            corrected == text_out
        ), f"correct_spaces failed for {repr(text_in)}: got {repr(corrected)}"


@pytest.mark.parametrize("test_pair", COMPOSITE_WORD_CONTINUATIONS)
def test_composite_word_continuation_tokenize(test_pair: tuple[str, str]) -> None:
    """Test continuation of composite words using different dash types.

    Em dashes should ALWAYS preserve spaces, even in composite word continuations.
    """
    text_in, text_out = test_pair
    # Test tokenize + detokenize preserves text
    tokens = list(t.tokenize(text_in))
    detok = t.detokenize(tokens)
    assert (
        detok == text_out
    ), f"detokenize failed for {repr(text_in)}: got {repr(detok)}"


@pytest.mark.parametrize("test_pair", COMPOSITE_WORD_CONTINUATIONS)
def test_composite_word_continuation_correct_spaces(test_pair: tuple[str, str]) -> None:
    """Test continuation of composite words using different dash types.

    Em dashes should ALWAYS preserve spaces, even in composite word continuations.
    """
    text_in, text_out = test_pair
    # Test split_into_sentences + correct_spaces preserves text
    sentences = list(t.split_into_sentences(text_in, original=True))
    if sentences:
        corrected = t.correct_spaces(sentences[0])
        assert (
            corrected == text_out
        ), f"correct_spaces failed for {repr(text_in)}: got {repr(corrected)}"


@pytest.mark.parametrize("test_pair", COMPOUND_WORDS)
def test_compound_words(test_pair: tuple[str, str]) -> None:
    """Test compound words joined with dashes."""
    text_in, text_out = test_pair
    # Test tokenize + detokenize preserves text
    tokens = list(t.tokenize(text_in))
    detok = t.detokenize(tokens)
    assert (
        detok == text_out
    ), f"detokenize failed for {repr(text_in)}: got {repr(detok)}"


@pytest.mark.parametrize("test_pair", COMPOUND_WORDS)
def test_compound_words_correct_spaces(test_pair: tuple[str, str]) -> None:
    """Test compound words joined with dashes."""
    text_in, text_out = test_pair
    # Test split_into_sentences + correct_spaces preserves text
    sentences = list(t.split_into_sentences(text_in))
    if sentences:
        corrected = t.correct_spaces(sentences[0])
        assert (
            corrected == text_out
        ), f"correct_spaces failed for {repr(text_in)}: got {repr(corrected)}"


@pytest.mark.parametrize("test_pair", MULTIPLE_DASHES_IN_SEQUENCE)
def test_multiple_dashes_in_sequence_tokenize(test_pair: tuple[str, str]) -> None:
    """Test multiple dashes in sequence.

    Em dashes should ALWAYS preserve spaces, even when doubled.
    """
    text_in, text_out = test_pair
    # Test tokenize + detokenize preserves text
    tokens = list(t.tokenize(text_in))
    detok = t.detokenize(tokens)
    assert (
        detok == text_out
    ), f"detokenize failed for {repr(text_in)}: got {repr(detok)}"


@pytest.mark.parametrize("test_pair", MULTIPLE_DASHES_IN_SEQUENCE)
def test_multiple_dashes_in_sequence_correct_spaces(test_pair: tuple[str, str]) -> None:
    """Test multiple dashes in sequence."""
    text_in, text_out = test_pair
    # Test split_into_sentences + correct_spaces preserves text
    sentences = list(t.split_into_sentences(text_in, original=True))
    if sentences:
        corrected = t.correct_spaces(sentences[0])
        assert (
            corrected == text_out
        ), f"correct_spaces failed for {repr(text_in)}: got {repr(corrected)}"


@pytest.mark.parametrize("test_pair", BEGIN_DASHES)
def test_dashes_at_start_tokenize(test_pair: tuple[str, str]) -> None:
    """Test dashes at the start of text.

    Em dashes at sentence start should preserve the space after them.
    """
    text_in, text_out = test_pair
    # Test tokenize + detokenize preserves text
    tokens = list(t.tokenize(text_in))
    detok = t.detokenize(tokens)
    assert (
        detok == text_out
    ), f"detokenize failed for {repr(text_in)}: got {repr(detok)}"


@pytest.mark.parametrize("test_pair", BEGIN_DASHES)
def test_dashes_at_start_correct_spaces(test_pair: tuple[str, str]) -> None:
    """Test dashes at the start of text."""
    text_in, text_out = test_pair
    # Test split_into_sentences + correct_spaces preserves text
    sentences = list(t.split_into_sentences(text_in))
    if sentences:
        corrected = t.correct_spaces(sentences[0])
        assert (
            corrected == text_out
        ), f"correct_spaces failed for {repr(text_in)}: got {repr(corrected)}"


@pytest.mark.parametrize("test_pair", END_DASHES)
def test_dashes_at_end_tokenize(test_pair: tuple[str, str]) -> None:
    """Test dashes at the end of text.

    Em dashes at sentence end should preserve the space before them.
    """
    text_in, text_out = test_pair
    # Test tokenize + detokenize preserves text
    tokens = list(t.tokenize(text_in))
    detok = t.detokenize(tokens)
    assert (
        detok == text_out
    ), f"detokenize failed for {repr(text_in)}: got {repr(detok)}"


@pytest.mark.parametrize("test_pair", END_DASHES)
def test_dashes_at_end_correct_spaces(test_pair: tuple[str, str]) -> None:
    """Test dashes at the end of text."""
    text_in, text_out = test_pair
    # Test split_into_sentences + correct_spaces preserves text
    sentences = list(t.split_into_sentences(text_in, original=True))
    if sentences:
        corrected = t.correct_spaces(sentences[0])
        assert (
            corrected == text_out
        ), f"correct_spaces failed for {repr(text_in)}: got {repr(corrected)}"
