# type: ignore

"""

    test_detokenize.py

    Tests for Tokenizer module

    Copyright (C) 2016-2025 by Miðeind ehf.
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

import tokenizer as t


def test_detokenize() -> None:

    options = {"normalize": True}

    def should_be_equal(s: str) -> None:
        toklist = t.tokenize(s, **options)
        assert s == t.detokenize(toklist, **options)

    def should_be(s1: str, s2: str) -> None:
        toklist = t.tokenize(s1, **options)
        assert s2 == t.detokenize(toklist, **options)

    should_be_equal("Jón átti 1.234,56 kr. í vasanum t.a.m. og 12. gr. átti ekki við.")
    should_be_equal("o.s.frv.")
    should_be_equal("http://www.malfong.is")
    should_be_equal("Páll skoðaði t.d. http://www.malfong.is.")
    should_be_equal("Páll var með netfangið palli@einn.i.heiminum.is.")
    should_be_equal("Páll var með „netfangið“ palli@einn.i.heiminum.is.")
    should_be_equal("Páll var m.a. [palli@einn.i.heiminum.is] þann 10. 12. 1998.")
    should_be_equal("Páll var m.a. [palli@einn.i.heiminum.is] þann 10.12.1998.")
    should_be_equal("Páll veiddi 74 cm. lax í Norðurá þann 1.3.")

    should_be(
        'Páll var með "netfangið" palli@einn.i.heiminum.is.',
        "Páll var með „netfangið“ palli@einn.i.heiminum.is.",
    )

    # !!! BUG
    # should_be(
    #    "Páll var með \"netfangið\", þ.e.a.s. (\"þetta\").",
    #    "Páll var með „netfangið“, þ.e.a.s. („þetta“).",
    # )

    options = {"normalize": False}

    should_be_equal("Páll var með „netfangið“, þ.e.a.s. („þetta“).")
    should_be_equal('Páll var með "netfangið" palli@einn.i.heiminum.is.')
    should_be_equal('Páll var með "netfangið", þ.e.a.s. ("þetta").')
