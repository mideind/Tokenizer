# -*- encoding: utf-8 -*-
"""
    test the Tok class in tokenizer
    TODO
"""

import tokenizer

Tok = tokenizer.Tok
TOK = tokenizer.TOK

ACCENT = chr(769)
UMLAUT = chr(776)


def test_split_simple() -> None:
    t = Tok(TOK.RAW, "boat", None)
    l, r = t.split(2)

    assert l == Tok(TOK.RAW, "bo", None)
    assert r == Tok(TOK.RAW, "at", None)


def test_split_simple_original() -> None:
    t = Tok(TOK.RAW, "boat", None, "boat", [0, 1, 2, 3])
    l, r = t.split(2)

    assert l == Tok(TOK.RAW, "bo", None, "bo", [0, 1])
    assert r == Tok(TOK.RAW, "at", None, "at", [0, 1])


def test_split_with_substitutions() -> None:
    # original: "a&123b". replace "&123" with "x" and end up with "axb"
    t = Tok(TOK.RAW, "axb", None, "a&123b", [0, 1, 5])

    l1, r1 = t.split(1)
    assert l1 == Tok(TOK.RAW, "a", None, "a", [0])
    assert r1 == Tok(TOK.RAW, "xb", None, "&123b", [0, 4])

    l2, r2 = t.split(2)
    assert l2 == Tok(TOK.RAW, "ax", None, "a&123", [0, 1])
    assert r2 == Tok(TOK.RAW, "b", None, "b", [0])


def test_split_with_substitutions_with_whitespace_prefix() -> None:
    # original: "  a&123b". strip whitespace and replace "&123" with "x" and end up with "axb"
    t = Tok(TOK.RAW, "axb", None, "  a&123b", [2, 3, 7])

    l1, r1 = t.split(1)
    assert l1 == Tok(TOK.RAW, "a", None, "  a", [2])
    assert r1 == Tok(TOK.RAW, "xb", None, "&123b", [0, 4])

    l2, r2 = t.split(2)
    assert l2 == Tok(TOK.RAW, "ax", None, "  a&123", [2, 3])
    assert r2 == Tok(TOK.RAW, "b", None, "b", [0])


def test_split_with_whitespace_prefix() -> None:
    t = Tok(TOK.RAW, "boat", None, "   boat", [3, 4, 5, 6])
    l, r = t.split(2)

    assert l == Tok(TOK.RAW, "bo", None, "   bo", [3, 4])
    assert r == Tok(TOK.RAW, "at", None, "at", [0, 1])


def test_split_at_ends() -> None:
    t = Tok(TOK.RAW, "ab", None, "ab", [0, 1])
    l, r = t.split(0)
    assert l == Tok(TOK.RAW, "", None, "", [])
    assert r == Tok(TOK.RAW, "ab", None, "ab", [0, 1])

    t = Tok(TOK.RAW, "ab", None, "ab", [0, 1])
    l, r = t.split(2)
    assert l == Tok(TOK.RAW, "ab", None, "ab", [0, 1])
    assert r == Tok(TOK.RAW, "", None, "", [])


    t = Tok(TOK.RAW, "ab", None)
    l, r = t.split(0)
    assert l == Tok(TOK.RAW, "", None)
    assert r == Tok(TOK.RAW, "ab", None)

    t = Tok(TOK.RAW, "ab", None)
    l, r = t.split(2)
    assert l == Tok(TOK.RAW, "ab", None)
    assert r == Tok(TOK.RAW, "", None)


def test_split_with_negative_index() -> None:
    test_string = "abcde"
    t = Tok(TOK.RAW, test_string, None, test_string, list(range(len(test_string))))
    l, r = t.split(-2)
    assert l == Tok(TOK.RAW, "abc", None, "abc", [0, 1, 2])
    assert r == Tok(TOK.RAW, "de", None, "de", [0, 1])


"""
TODO: Haven't decided what's the correct behavior.
def test_split_on_empty_txt():
    t = Tok(TOK.RAW, "", None, "this got removed", [])

    l, r = t.split(0)
    assert l == Tok(TOK.RAW, "", None, "", [])
    assert r == Tok(TOK.RAW, "", None, "this got removed", [])

    l, r = t.split(1)
    assert l == Tok(TOK.RAW, "", None, "this got removed", [])
    assert r == Tok(TOK.RAW, "", None, "", [])
"""


def test_substitute() -> None:
    t = Tok(TOK.RAW, "a&123b", None, "a&123b", [0, 1, 2, 3, 4, 5])
    t.substitute((1, 5), "x")
    assert t == Tok(TOK.RAW, "axb", None, "a&123b", [0, 1, 5])

    t = Tok(TOK.RAW, "ab&123", None, "ab&123", [0, 1, 2, 3, 4, 5])
    t.substitute((2, 6), "x")
    assert t == Tok(TOK.RAW, "abx", None, "ab&123", [0, 1, 2])

    t = Tok(TOK.RAW, "&123ab", None, "&123ab", [0, 1, 2, 3, 4, 5])
    t.substitute((0, 4), "x")
    assert t == Tok(TOK.RAW, "xab", None, "&123ab", [0, 4, 5])


def test_substitute_bugfix_1() -> None:
    test_string = "xya" + ACCENT + "zu" + ACCENT + "w&aacute;o" + UMLAUT + "b"
    #              012    3         45    6         7890123456    7         8
    #              0123456789012345
    t = Tok(kind=-1, txt=test_string, val=None, original=test_string, origin_spans=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18])
    t.substitute((2, 4), "á")
    assert t == Tok(kind=-1, txt='xyázu' + ACCENT + 'w&aacute;o' + UMLAUT + 'b', val=None, original=test_string, origin_spans=[0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18])

    t.substitute((4, 6), "ú")
    assert t == Tok(kind=-1, txt='xyázúw&aacute;o' + UMLAUT + 'b', val=None, original=test_string, origin_spans=[0, 1, 2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18])

    t.substitute((14, 16), "ö")
    assert t == Tok(kind=-1, txt='xyázúw&aacute;öb', val=None, original=test_string, origin_spans=[0, 1, 2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18])
    
    # bug was here
    t.substitute((6, 14), "á")
    assert t == Tok(kind=-1, txt='xyázúwáöb', val=None, original=test_string, origin_spans=[0, 1, 2, 4, 5, 7, 8, 16, 18])


def test_multiple_substitutions() -> None:
    t = Tok(TOK.RAW, "a&123b&456&789c", None, "a&123b&456&789c", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])
    t.substitute((1, 5), "x")
    assert t == Tok(TOK.RAW, "axb&456&789c", None, "a&123b&456&789c", [0, 1, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])
    t.substitute((3, 7), "y")
    assert t == Tok(TOK.RAW, "axby&789c", None, "a&123b&456&789c", [0, 1, 5, 6, 10, 11, 12, 13, 14])
    t.substitute((4, 8), "z")
    assert t == Tok(TOK.RAW, "axbyzc", None, "a&123b&456&789c", [0, 1, 5, 6, 10, 14])


def test_substitute_without_origin_tracking() -> None:
    t = Tok(TOK.RAW, "a&123b", None)
    t.substitute((1, 5), "x")
    assert t == Tok(TOK.RAW, "axb", None)

    t = Tok(TOK.RAW, "ab&123", None)
    t.substitute((2, 6), "x")
    assert t == Tok(TOK.RAW, "abx", None)

    t = Tok(TOK.RAW, "&123ab", None)
    t.substitute((0, 4), "x")
    assert t == Tok(TOK.RAW, "xab", None)

    t = Tok(TOK.RAW, "a&123b&456c", None)
    t.substitute((1, 5), "x")
    assert t == Tok(TOK.RAW, "axb&456c", None)
    t.substitute((3, 7), "y")
    assert t == Tok(TOK.RAW, "axbyc", None)


def test_substitute_that_removes() -> None:
    t = Tok(TOK.RAW, "a&123b", None, "a&123b", [0, 1, 2, 3, 4, 5])
    t.substitute((1, 5), "")
    assert t == Tok(TOK.RAW, "ab", None, "a&123b", [0, 5])

    t = Tok(TOK.RAW, "&123ab", None, "&123ab", [0, 1, 2, 3, 4, 5])
    t.substitute((0, 4), "")
    assert t == Tok(TOK.RAW, "ab", None, "&123ab", [4, 5])

    t = Tok(TOK.RAW, "ab&123", None, "ab&123", [0, 1, 2, 3, 4, 5])
    t.substitute((2, 6), "")
    assert t == Tok(TOK.RAW, "ab", None, "ab&123", [0, 1])
    

def test_split_without_origin_tracking() -> None:
    t = Tok(TOK.RAW, "boat", None)
    l, r = t.split(2)

    assert l == Tok(TOK.RAW, "bo", None)
    assert r == Tok(TOK.RAW, "at", None)

    ###

    # original: "a&123b". replace "&123" with "x" and end up with "axb"
    t = Tok(TOK.RAW, "axb", None)

    l1, r1 = t.split(1)
    assert l1 == Tok(TOK.RAW, "a", None)
    assert r1 == Tok(TOK.RAW, "xb", None)

    l2, r2 = t.split(2)
    assert l2 == Tok(TOK.RAW, "ax", None)
    assert r2 == Tok(TOK.RAW, "b", None)

    ###

    # original: "  a&123b". strip whitespace and replace "&123" with "x" and end up with "axb"
    t = Tok(TOK.RAW, "axb", None)

    l1, r1 = t.split(1)
    assert l1 == Tok(TOK.RAW, "a", None)
    assert r1 == Tok(TOK.RAW, "xb", None)

    l2, r2 = t.split(2)
    assert l2 == Tok(TOK.RAW, "ax", None)
    assert r2 == Tok(TOK.RAW, "b", None)

    ###

    t = Tok(TOK.RAW, "boat", None)
    l, r = t.split(2)

    assert l == Tok(TOK.RAW, "bo", None)
    assert r == Tok(TOK.RAW, "at", None)


def test_html_escapes_with_origin_tracking() -> None:
    test_string = "xy&#x61;z&aacute;w&#97;b"
    tokens = list(tokenizer.generate_rough_tokens(test_string, replace_html_escapes=True))
    assert len(tokens) == 1
    assert tokens[0] == Tok(kind=TOK.RAW, txt="xyazáwab", val=None, original=test_string, origin_spans=[0, 1, 2, 8, 9, 17, 18, 23])


def test_unicode_escapes_with_origin_tracking() -> None:
    test_string = "xya" + ACCENT + "zu" + ACCENT + "wo" + UMLAUT + "b"
    tokens = list(tokenizer.generate_rough_tokens(test_string, replace_composite_glyphs=True))
    assert len(tokens) == 1
    assert tokens[0] == Tok(kind=TOK.RAW, txt="xyázúwöb", val=None, original=test_string, origin_spans=[0, 1, 2, 4, 5, 7, 8, 10])


def test_unicode_escapes_that_are_removed() -> None:
    test_string = "a\xadb\xadc"
    tokens = list(tokenizer.generate_rough_tokens(test_string, replace_composite_glyphs=True))
    assert len(tokens) == 1
    assert tokens[0] == Tok(kind=TOK.RAW, txt="abc", val=None, original=test_string, origin_spans=[0, 2, 4])


def test_html_unicode_mix() -> None:
    test_string = "xya" + ACCENT + "zu" + ACCENT + "w&aacute;o" + UMLAUT + "b"
    #              012    3         45    6         7890123456    7         8
    tokens = list(tokenizer.generate_rough_tokens(test_string, replace_composite_glyphs=True, replace_html_escapes=True))
    assert len(tokens) == 1
    assert tokens[0] == Tok(kind=TOK.RAW, txt="xyázúwáöb", val=None, original=test_string, origin_spans=[0, 1, 2, 4, 5, 7, 8, 16, 18])


def test_tok_concatenation() -> None:
    str1 = "asdf"
    tok1 = Tok(TOK.RAW, str1, None, str1, list(range(len(str1))))
    str2 = "jklæ"
    tok2 = Tok(TOK.RAW, str2, None, str2, list(range(len(str1))))
    assert tok1.concatenate(tok2) == Tok(TOK.RAW, str1+str2, None, str1+str2, list(range(len(str1+str2))))

    str1 = "abc"
    or1 = "&123&456&789"
    str2 = "xyz"
    or2 = "&xx&yy&zz"
    tok1 = Tok(TOK.RAW, str1, None, or1, [0, 4, 8])
    tok2 = Tok(TOK.RAW, str2, None, or2, [0, 2, 4])
    assert tok1.concatenate(tok2) == Tok(TOK.RAW, str1+str2, None, or1+or2, [0, 4, 8, 12, 14, 16])


def test_tok_concatenation_with_separator() -> None:
    str1 = "asdf"
    tok1 = Tok(TOK.RAW, str1, None, str1, list(range(len(str1))))
    str2 = "jklæ"
    tok2 = Tok(TOK.RAW, str2, None, str2, list(range(len(str1))))
    sep = "WOLOLO"
    assert tok1.concatenate(tok2, separator=sep) == Tok(TOK.RAW, str1+sep+str2, None, str1+str2, [0, 1, 2, 3, 4, 4, 4, 4, 4, 4, 4, 5, 6, 7])

    str1 = "abc"
    or1 = "&123&456&789"
    str2 = "xyz"
    or2 = "&xx&yy&zz"
    tok1 = Tok(TOK.RAW, str1, None, or1, [0, 4, 8])
    tok2 = Tok(TOK.RAW, str2, None, or2, [0, 2, 4])
    sep = "WOLOLO"
    assert tok1.concatenate(tok2, separator=sep) == Tok(TOK.RAW, str1+sep+str2, None, or1+or2, [0, 4, 8, 12, 12, 12, 12, 12, 12, 12, 14, 16])


def test_tok_substitute_all() -> None:
    s = "asdf"
    t = Tok(TOK.RAW, s, None, s, list(range(len(s))))
    t.substitute_all("d", "x")
    assert t == Tok(TOK.RAW, "asxf", None, s, [0, 1, 2, 3])

    s = "Þetta er lengri strengur."
    t = Tok(TOK.RAW, s, None, s, list(range(len(s))))
    t.substitute_all("e", "x")
    assert t == Tok(TOK.RAW, "Þxtta xr lxngri strxngur.", None, s, list(range(len(s))))

    s = "asdf"
    t = Tok(TOK.RAW, s, None, s, list(range(len(s))))
    t.substitute_all("d", "")
    assert t == Tok(TOK.RAW, "asf", None, s, [0, 1, 3])

    s = "Þessi verður lengri."
    #    01234567890123456789
    t = Tok(TOK.RAW, s, None, s, list(range(len(s))))
    t.substitute_all("r", "")
    assert t == Tok(TOK.RAW, "Þessi veðu lengi.", None, s, [0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 12, 13, 14, 15, 16, 18, 19])


def test_tok_substitute_longer() -> None:
    s = "asdf"
    t = Tok(TOK.RAW, s, None, s, list(range(len(s))))
    t.substitute_longer((1, 2), "xyz")
    assert t == Tok(TOK.RAW, "axyzdf", None, s, [0, 2, 2, 2, 2, 3])

    s = "asdf"
    t = Tok(TOK.RAW, s, None, s, list(range(len(s))))
    t.substitute_longer((3, 4), "xyz")
    assert t == Tok(TOK.RAW, "asdxyz", None, s, [0, 1, 2, 4, 4, 4])

    s = "asdf"
    t = Tok(TOK.RAW, s, None, s, list(range(len(s))))
    t.substitute_longer((0, 1), "xyz")
    assert t == Tok(TOK.RAW, "xyzsdf", None, s, [1, 1, 1, 1, 2, 3])
