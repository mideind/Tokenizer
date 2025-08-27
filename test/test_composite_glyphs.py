"""
Test suite for composite glyph handling in the tokenizer.

Tests the --keep_composite_glyphs flag and replace_composite_glyphs option
to ensure combining Unicode characters are handled correctly.

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
"""

from tokenizer import TOK, tokenize, split_into_sentences


def test_composite_glyphs_default():
    """Test that composite glyphs are replaced by default."""
    # Test combining acute accent (U+0301)
    text = "Ha\u0301kon"  # "a" + combining acute + "kon" = "Hákon"
    tokens = list(tokenize(text))
    # Filter out sentence boundary tokens
    word_tokens = [t for t in tokens if t.kind == TOK.WORD]
    
    assert len(word_tokens) == 1
    assert word_tokens[0].txt == "Hákon"
    
    # Test combining diaeresis (U+0308)
    text = "o\u0308"  # "o" + combining diaeresis = "ö"
    tokens = list(tokenize(text))
    word_tokens = [t for t in tokens if t.kind == TOK.WORD]
    
    assert len(word_tokens) == 1
    assert word_tokens[0].txt == "ö"


def test_composite_glyphs_keep():
    """Test that composite glyphs are kept separate when replace_composite_glyphs=False."""
    # Test combining acute accent (U+0301)
    text = "Ha\u0301kon"  # "a" + combining acute + "kon"
    tokens = list(tokenize(text, replace_composite_glyphs=False))
    # Filter out sentence boundary tokens
    content_tokens = [t for t in tokens if t.txt]
    
    assert len(content_tokens) == 3
    assert content_tokens[0].txt == "Ha"
    assert content_tokens[0].kind == TOK.WORD
    assert content_tokens[1].txt == "\u0301"  # Combining acute accent
    assert content_tokens[1].kind == TOK.UNKNOWN
    assert content_tokens[2].txt == "kon"
    assert content_tokens[2].kind == TOK.WORD
    
    # Test combining diaeresis (U+0308)
    text = "o\u0308"  # "o" + combining diaeresis
    tokens = list(tokenize(text, replace_composite_glyphs=False))
    content_tokens = [t for t in tokens if t.txt]
    
    assert len(content_tokens) == 2
    assert content_tokens[0].txt == "o"
    assert content_tokens[0].kind == TOK.WORD
    assert content_tokens[1].txt == "\u0308"  # Combining diaeresis
    assert content_tokens[1].kind == TOK.UNKNOWN


def test_multiple_composite_glyphs():
    """Test text with multiple composite glyphs."""
    # "Ágúst" with combining characters
    text = "A\u0301gu\u0301st"  # A + acute, u + acute
    
    # Test with replacement (default)
    tokens = list(tokenize(text))
    word_tokens = [t for t in tokens if t.kind == TOK.WORD]
    assert len(word_tokens) == 1
    assert word_tokens[0].txt == "Ágúst"
    
    # Test without replacement
    tokens = list(tokenize(text, replace_composite_glyphs=False))
    content_tokens = [t for t in tokens if t.txt]
    assert len(content_tokens) == 5
    assert content_tokens[0].txt == "A"
    assert content_tokens[1].txt == "\u0301"
    assert content_tokens[2].txt == "gu"
    assert content_tokens[3].txt == "\u0301"
    assert content_tokens[4].txt == "st"


def test_icelandic_vowels_with_combining():
    """Test all Icelandic vowels with combining accents and umlauts."""
    test_cases = [
        ("a\u0301", "á"),  # a + acute
        ("e\u0301", "é"),  # e + acute
        ("i\u0301", "í"),  # i + acute
        ("o\u0301", "ó"),  # o + acute
        ("u\u0301", "ú"),  # u + acute
        ("y\u0301", "ý"),  # y + acute
        ("o\u0308", "ö"),  # o + umlaut
        ("A\u0301", "Á"),  # A + acute (uppercase)
        ("E\u0301", "É"),  # E + acute (uppercase)
        ("I\u0301", "Í"),  # I + acute (uppercase)
        ("O\u0301", "Ó"),  # O + acute (uppercase)
        ("U\u0301", "Ú"),  # U + acute (uppercase)
        ("Y\u0301", "Ý"),  # Y + acute (uppercase)
        ("O\u0308", "Ö"),  # O + umlaut (uppercase)
    ]
    
    for combining_form, expected in test_cases:
        # Test with replacement (default)
        tokens = list(tokenize(combining_form))
        word_tokens = [t for t in tokens if t.kind == TOK.WORD]
        assert len(word_tokens) == 1
        assert word_tokens[0].txt == expected
        
        # Test without replacement
        tokens = list(tokenize(combining_form, replace_composite_glyphs=False))
        content_tokens = [t for t in tokens if t.txt]
        assert len(content_tokens) == 2
        # First token is the base character
        assert content_tokens[0].txt == combining_form[0]
        # Second token is the combining character
        assert content_tokens[1].txt in ["\u0301", "\u0308"]


def test_sentence_splitting_with_composite():
    """Test that sentence splitting works correctly with composite glyphs."""
    text = "A\u0301gu\u0301st er ma\u0301nu\u0308dur."  # "Ágúst er mánüdur." (u + umlaut = ü, not ú)
    
    # Test with replacement (default)
    sentences = list(split_into_sentences(text))
    assert len(sentences) == 1
    assert sentences[0] == "Ágúst er mánüdur ."  # u + umlaut becomes ü
    
    # Test without replacement
    sentences = list(split_into_sentences(text, replace_composite_glyphs=False))
    assert len(sentences) == 1
    # The combining characters are kept as separate tokens
    expected = "A ́ gu ́ st er ma ́ nu ̈ dur ."
    assert sentences[0] == expected


def test_mixed_text():
    """Test text with both regular and composite characters."""
    text = "Þo\u0301r og O\u0308rn"  # "Þór og Örn"
    
    # Test with replacement
    tokens = list(tokenize(text))
    word_tokens = [t for t in tokens if t.kind == TOK.WORD]
    assert len(word_tokens) == 3
    assert word_tokens[0].txt == "Þór"
    assert word_tokens[1].txt == "og"
    assert word_tokens[2].txt == "Örn"
    
    # Test without replacement
    tokens = list(tokenize(text, replace_composite_glyphs=False))
    content_tokens = [t for t in tokens if t.txt and t.kind in (TOK.WORD, TOK.UNKNOWN)]
    assert len(content_tokens) == 7  # More tokens due to the way combining chars split
    assert content_tokens[0].txt == "Þo"
    assert content_tokens[1].txt == "\u0301"  # Combining acute accent
    assert content_tokens[2].txt == "r"
    assert content_tokens[3].txt == "og"
    assert content_tokens[4].txt == "O"  # O as a separate token (matches abbreviation)
    assert content_tokens[5].txt == "\u0308"  # Combining diaeresis
    assert content_tokens[6].txt == "rn"


def test_zero_width_characters():
    """Test that zero-width characters are handled correctly."""
    # Test soft hyphen (U+00AD), zero-width space (U+200B), zero-width NBSP (U+FEFF)
    text = "test\u00ADing zero\u200Bwidth BOM\uFEFFtest"
    
    # Zero-width characters should always be removed regardless of replace_composite_glyphs
    
    # With replace_composite_glyphs=True (default)
    tokens = list(tokenize(text))
    word_tokens = [t for t in tokens if t.kind == TOK.WORD]
    assert len(word_tokens) == 3
    assert word_tokens[0].txt == "testing"  # soft hyphen removed
    assert word_tokens[1].txt == "zerowidth"  # zero-width space removed
    assert word_tokens[2].txt == "BOMtest"  # zero-width NBSP removed
    
    # With replace_composite_glyphs=False - zero-width chars should still be removed
    tokens = list(tokenize(text, replace_composite_glyphs=False))
    word_tokens = [t for t in tokens if t.kind == TOK.WORD]
    assert len(word_tokens) == 3  # Zero-width characters are always removed
    assert word_tokens[0].txt == "testing"
    assert word_tokens[1].txt == "zerowidth"
    assert word_tokens[2].txt == "BOMtest"


def test_original_preserved():
    """Test that original text is preserved in tokens."""
    text = "Ha\u0301kon"
    
    # With replacement
    tokens = list(tokenize(text))
    word_tokens = [t for t in tokens if t.kind == TOK.WORD]
    assert word_tokens[0].txt == "Hákon"
    assert word_tokens[0].original == "Ha\u0301kon"
    
    # Without replacement
    tokens = list(tokenize(text, replace_composite_glyphs=False))
    content_tokens = [t for t in tokens if t.txt]
    assert content_tokens[0].original == "Ha"
    assert content_tokens[1].original == "\u0301"
    assert content_tokens[2].original == "kon"