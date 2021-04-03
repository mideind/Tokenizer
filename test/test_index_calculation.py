"""
    Test the index generation of the tokenizer.
"""


import tokenizer

Tok = tokenizer.Tok
TOK = tokenizer.TOK

ACCENT = chr(769)
UMLAUT = chr(776)
EM_DASH = "\u2014"


def test_small_easy_cases():
    s = "Bara ASCII."
    #    01234567890
    #    ^   ^     ^
    toks = tokenizer.parse_tokens([s])
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
    assert char_indexes == [0, 4, 10]
    assert byte_indexes == [0, 4, 10]
    toks = tokenizer.parse_tokens([s])
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
    assert char_indexes == [0, 4, 10, 11]
    assert byte_indexes == [0, 4, 10, 11]

    s = "Á bát."
    # char:
    #    012345
    #    ^^   ^
    # byte:
    # two-byte letters:
    #    x  x
    # indexes:
    #    023467
    #    ^^   ^
    toks = tokenizer.parse_tokens([s])
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
    assert char_indexes == [0, 1, 5]
    assert byte_indexes == [0, 2, 7]
    toks = tokenizer.parse_tokens([s])
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
    assert char_indexes == [0, 1, 5, 6]
    assert byte_indexes == [0, 2, 7, 8]

    s = "endar á ö"
    #    012345678
    #    ^    ^ ^
    #          x x
    toks = tokenizer.parse_tokens([s])
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
    assert char_indexes == [0, 5, 7]
    assert byte_indexes == [0, 5, 8]
    toks = tokenizer.parse_tokens([s])
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
    assert char_indexes == [0, 5, 7, 9]
    assert byte_indexes == [0, 5, 8, 11]


def test_small_difficult_cases():
    s = ""
    toks = tokenizer.parse_tokens([s])
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
    assert char_indexes == []
    assert byte_indexes == []
    toks = tokenizer.parse_tokens([s])
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
    assert char_indexes == [0]
    assert byte_indexes == [0]

    s = " "
    toks = tokenizer.parse_tokens([s])
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
    assert char_indexes == [0]
    assert byte_indexes == [0]
    toks = tokenizer.parse_tokens([s])
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
    assert char_indexes == [0, 1]
    assert byte_indexes == [0, 1]

    # Single byte characters
    for x in ["a", "A", ".", "?", "!"]:
        s = x
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0]
        assert byte_indexes == [0]
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 1]
        assert byte_indexes == [0, 1]

        s = " " + x
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0]
        assert byte_indexes == [0]
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 2]
        assert byte_indexes == [0, 2]

        s = "  " + x
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0]
        assert byte_indexes == [0]
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 3]
        assert byte_indexes == [0, 3]

        s = "  " + x + " "
        # example:
        #   "  a "
        #    0123
        #    ^  ^
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0, 3]
        assert byte_indexes == [0, 3]
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 3, 4]
        assert byte_indexes == [0, 3, 4]

        s = " " + x + " " + x
        # example:
        #   " a a"
        #    ^ ^
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0, 2]
        assert byte_indexes == [0, 2]
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 2, 4]
        assert byte_indexes == [0, 2, 4]


    # Two byte characters
    for x in ["þ", "æ", "á"]:
        s = x
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0], s
        assert byte_indexes == [0], s
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 1], s
        assert byte_indexes == [0, 2], s

        s = " " + x
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0]
        assert byte_indexes == [0]
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 2]
        assert byte_indexes == [0, 3]

        s = "  " + x
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0]
        assert byte_indexes == [0]
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 3]
        assert byte_indexes == [0, 4]

        s = "  " + x + " "
        # example bytes:
        #   "  þ_ "
        #    01234
        #    ^   ^
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0, 3]
        assert byte_indexes == [0, 4]
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 3, 4]
        assert byte_indexes == [0, 4, 5]

        s = " " + x + " " + x
        # example bytes:
        #   " þ_ þ_"
        #    012345
        #    ^  ^
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0, 2]
        assert byte_indexes == [0, 3]
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 2, 4]
        assert byte_indexes == [0, 3, 6]


    # Two character characters
    # These strings contain two unicode code points that are rendered as one letter.
    # They are counted as two characters in python.
    # In addition the accent and umlaut characters are two bytes.
    for x in ["a"+ACCENT, "o"+UMLAUT]:
        s = x
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0], s
        assert byte_indexes == [0], s
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 2], s
        assert byte_indexes == [0, 3], s

        s = " " + x
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0]
        assert byte_indexes == [0]
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 3]
        assert byte_indexes == [0, 4]

        s = "  " + x
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0]
        assert byte_indexes == [0]
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 4]
        assert byte_indexes == [0, 5]

        s = "  " + x + " "
        # example chars:
        #   "  a´ "
        #    01234
        #    ^  ^^
        # example bytes:
        #   "  a´_ "
        #    012345
        #    ^  ^ ^
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0, 4]
        assert byte_indexes == [0, 5]
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 4, 5]
        assert byte_indexes == [0, 5, 6]

        s = " " + x + " " + x
        # example chars:
        #   " a´ a´"
        #    012345
        #    ^  ^    
        # example bytes:
        #   " a´_ a´_"
        #    01234567
        #    ^   ^  
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0, 3]
        assert byte_indexes == [0, 4]
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 3, 6]
        assert byte_indexes == [0, 4, 8]


    # The em-dash is 3 bytes
    for x in [EM_DASH]:
        s = x
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0], s
        assert byte_indexes == [0], s
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 1], s
        assert byte_indexes == [0, 3], s

        s = " " + x
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0]
        assert byte_indexes == [0]
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 2]
        assert byte_indexes == [0, 4]

        s = "  " + x
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0]
        assert byte_indexes == [0]
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 3]
        assert byte_indexes == [0, 5]

        s = "  " + x + " "
        # example chars:
        #   "  a "
        #    0123
        #    ^  ^
        # example bytes:
        #   "  a__ "
        #    012345
        #    ^    ^
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0, 3]
        assert byte_indexes == [0, 5]
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 3, 4]
        assert byte_indexes == [0, 5, 6]

        s = " " + x + " " + x
        # example chars:
        #   " a a"
        #    0123
        #    ^ ^
        # example bytes:
        #   " a__ a__"
        #    01234567
        #    ^   ^  
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
        assert char_indexes == [0, 2]
        assert byte_indexes == [0, 4]
        toks = tokenizer.parse_tokens([s])
        char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
        assert char_indexes == [0, 2, 4]
        assert byte_indexes == [0, 4, 8]


def test_larger_case():
    s = "Þessi setning er í lengra lagi og er með bæði eins og tveggja bæta stafi."
    #    0123456789012345678901234567890123456789012345678901234567890123456789012
    #    ^    ^       ^  ^ ^      ^    ^  ^  ^   ^    ^    ^  ^       ^    ^     ^
    #    x                x                     x  xx                   x
    toks = tokenizer.parse_tokens([s])
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
    assert char_indexes == [0, 5, 13, 16, 18, 25, 30, 33, 36, 40, 45, 50, 53, 61, 66, 72]
    assert byte_indexes == [0, 6, 14, 17, 20, 27, 32, 35, 38, 43, 50, 55, 58, 66, 72, 78]
    toks = tokenizer.parse_tokens([s])
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
    assert char_indexes == [0, 5, 13, 16, 18, 25, 30, 33, 36, 40, 45, 50, 53, 61, 66, 72, 73]
    assert byte_indexes == [0, 6, 14, 17, 20, 27, 32, 35, 38, 43, 50, 55, 58, 66, 72, 78, 79]


def test_iterator_cases():
    s = ["Þessi ", "setning ", "er ", "í ", "lengra ", "lagi ", "og ", "er ", "með ", "bæði ", "eins ", "og ", "tveggja ", "bæta ", "stafi."]
    # (char and byte indexes in a similar test above)
    toks = tokenizer.parse_tokens(s)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
    assert char_indexes == [0, 5, 13, 16, 18, 25, 30, 33, 36, 40, 45, 50, 53, 61, 66, 72]
    assert byte_indexes == [0, 6, 14, 17, 20, 27, 32, 35, 38, 43, 50, 55, 58, 66, 72, 78]
    toks = tokenizer.parse_tokens(s)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
    assert char_indexes == [0, 5, 13, 16, 18, 25, 30, 33, 36, 40, 45, 50, 53, 61, 66, 72, 73]
    assert byte_indexes == [0, 6, 14, 17, 20, 27, 32, 35, 38, 43, 50, 55, 58, 66, 72, 78, 79]

    s = ["Stutt setning.", "", "Önnur setning."]
    #     01234567890123        45678901234567
    #     ^    ^       ^        ^    ^       ^
    #                           x
    toks = tokenizer.parse_tokens(s)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
    assert char_indexes == [0, 5, 13, 14, 19, 27]
    assert byte_indexes == [0, 5, 13, 14, 20, 28]
    toks = tokenizer.parse_tokens(s)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
    assert char_indexes == [0, 5, 13, 14, 19, 27, 28]
    assert byte_indexes == [0, 5, 13, 14, 20, 28, 29]

    # parse_tokens does some implentation-detail-stuff here. Use tokenize instead.
    s = [" Stutt setning. ", "\n \n", "Önnur setning."]
    #     0123456789012345    6 78     90123456789012
    #     ^     ^       ^^                  ^       ^
    #                                  x
    toks = tokenizer.tokenize(s)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
    assert char_indexes == [0, 6, 14, 15, 24, 32]
    assert byte_indexes == [0, 6, 14, 15, 25, 33]
    toks = tokenizer.tokenize(s)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
    assert char_indexes == [0, 6, 14, 15, 24, 32, 33]
    assert byte_indexes == [0, 6, 14, 15, 25, 33, 34]


def test_paragraph_markers():
    s = " [[ Stutt setning. ]] [[ ]] [[ Önnur setning. ]]"
    #    012345678901234567890123456789012345678901234567
    #    ^  ^     ^       ^^  ^  ^  ^  ^     ^       ^^
    #                                   x
    toks = tokenizer.parse_tokens(s)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
    assert char_indexes == [0, 3, 9, 17, 18, 21, 24, 27, 30, 36, 44, 45]
    assert byte_indexes == [0, 3, 9, 17, 18, 21, 24, 27, 30, 37, 45, 46]
    toks = tokenizer.parse_tokens(s)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
    assert char_indexes == [0, 3, 9, 17, 18, 21, 24, 27, 30, 36, 44, 45, 48]
    assert byte_indexes == [0, 3, 9, 17, 18, 21, 24, 27, 30, 37, 45, 46, 49]

    # The tokenize functions does stuff to paragraph markers. Test that the
    # indexes are properly calculated after that.
    # Note that the text of the dropped empty paragraph markers disappears.
    s = " [[ Stutt setning. ]] [[ ]] [[ Önnur setning. ]]"
    #    012345678901234567890123456789012345678901234567
    #    ^  ^     ^       ^^           ^     ^       ^^
    #                                   x
    toks = tokenizer.tokenize(s)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
    assert char_indexes == [0, 3, 9, 17, 18, 21, 30, 36, 44, 45]
    assert byte_indexes == [0, 3, 9, 17, 18, 21, 30, 37, 45, 46]
    toks = tokenizer.tokenize(s)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
    assert char_indexes == [0, 3, 9, 17, 18, 21, 30, 36, 44, 45, 48]
    assert byte_indexes == [0, 3, 9, 17, 18, 21, 30, 37, 45, 46, 49]


def test_composite_phrases():
    s = "Orða- og tengingasetning."
    #    0123456789012345678901234
    #    ^   ^^  ^               ^
    #      x
    toks = tokenizer.parse_tokens(s)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
    assert char_indexes == [0, 4, 5, 8, 24]
    assert byte_indexes == [0, 5, 6, 9, 25]
    toks = tokenizer.parse_tokens(s)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
    assert char_indexes == [0, 4, 5, 8, 24, 25]
    assert byte_indexes == [0, 5, 6, 9, 25, 26]

    # The whole thing gets squished together into a single token.
    s = "Orða- og tengingasetning."
    #    0123456789012345678901234
    #    ^                       ^
    #      x
    toks = tokenizer.tokenize(s)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
    assert char_indexes == [0, 24]
    assert byte_indexes == [0, 25]
    toks = tokenizer.tokenize(s)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
    assert char_indexes == [0, 24, 25]
    assert byte_indexes == [0, 25, 26]


def test_lengthening_substitutions():
    s = "Þetta er 3ji báturinn!"
    #    0123456789012345678901
    #    ^    ^  ^   ^        ^
    #    x             x
    #             !             lengthening happens here (3ji->þriðji)
    toks = tokenizer.parse_tokens(s, handle_kludgy_ordinals=tokenizer.KLUDGY_ORDINALS_MODIFY)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
    assert char_indexes == [0, 5, 8, 12, 21]
    assert byte_indexes == [0, 6, 9, 13, 23]
    toks = tokenizer.parse_tokens(s, handle_kludgy_ordinals=tokenizer.KLUDGY_ORDINALS_MODIFY)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
    assert char_indexes == [0, 5, 8, 12, 21, 22]
    assert byte_indexes == [0, 6, 9, 13, 23, 24]


def test_converted_measurements():
    s = "Stillið ofninn á 12° C til að baka kökuna."
    #    012345678901234567890123456789012345678901
    #    ^      ^      ^ ^     ^   ^  ^    ^      ^
    #          x        x   x        x       x
    toks = tokenizer.tokenize(s, convert_measurements=True)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks)
    assert char_indexes == [0, 7, 14, 16, 22, 26, 29, 34, 41]
    assert byte_indexes == [0, 8, 15, 18, 25, 29, 33, 38, 46]
    toks = tokenizer.tokenize(s, convert_measurements=True)
    char_indexes, byte_indexes = tokenizer.calculate_indexes(toks, last_is_end=True)
    assert char_indexes == [0, 7, 14, 16, 22, 26, 29, 34, 41, 42]
    assert byte_indexes == [0, 8, 15, 18, 25, 29, 33, 38, 46, 47]