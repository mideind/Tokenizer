"""
Test the command line interface (CLI) of the tokenizer.
Copyright (C) 2025 Miðeind ehf.
"""
# ruff: noqa: E501 # Allow long lines in test files

from io import StringIO
import sys
from unittest.mock import patch

from pytest import CaptureFixture, MonkeyPatch

from tokenizer.main import main
from tokenizer import __version__ as tokenizer_version


CLT_NAME = "tokenize"


def run_cli(c: CaptureFixture[str], m: MonkeyPatch, args: list[str], standard_input: str = "") -> str:
    """Run the command line interface (CLI) main function with
    the given arguments and standard input."""

    # Feed the provided string into standard input
    old_stdin = sys.stdin
    input = StringIO(standard_input)
    m.setattr(sys, "stdin", input)

    # Run the main function with the provided arguments
    # We patch sys.argv to simulate command line arguments
    try:
        with patch.object(sys, "argv", [CLT_NAME] + args):
            main()
    # Capture the command line script exiting
    except SystemExit as e:
        assert e.code == 0, f"Expected exit code 0 from CLT, got {e.code}"

    # Capture the output
    output = c.readouterr()

    # Restore the original standard input
    m.setattr(sys, "stdin", old_stdin)

    # Return the output string
    return output.out.strip()


def test_cli(capsys: CaptureFixture[str], monkeypatch: MonkeyPatch) -> None:
    """Test the command line interface (CLI) of the tokenizer."""
    c = capsys  # Capture output
    m = monkeypatch  # Monkeypatch for testing

    # Version and help
    assert run_cli(c, m, ["--version"]).endswith(tokenizer_version)
    assert "usage:" in run_cli(c, m, ["--help"])

    # Basic tokenization
    assert (
        run_cli(c, m, ["-", "-"], "Hann Jón,sem kom kl.14:00 í dag, fór seinna.")
        == "Hann Jón , sem kom kl. 14:00 í dag , fór seinna ."
    )

    # JSON output
    expected_json_out = """
{"k":"BEGIN SENT","t":""}
{"k":"WORD","t":"Þetta","o":"Þetta","s":[0,1,2,3,4]}
{"k":"WORD","t":"var","o":" var","s":[1,2,3]}
{"k":"DATEREL","t":"14. mars","v":[0,3,14],"o":" 14. mars","s":[1,2,3,4,5,6,7,8]}
{"k":"WORD","t":"og","o":" og","s":[1,2]}
{"k":"NUMBER","t":"11","v":11,"o":" 11","s":[1,2]}
{"k":"WORD","t":"manns","o":" manns","s":[1,2,3,4,5]}
{"k":"WORD","t":"viðstaddir","o":" viðstaddir","s":[1,2,3,4,5,6,7,8,9,10]}
{"k":"PUNCTUATION","t":".","v":".","o":".","s":[0]}
{"k":"END SENT","t":""}
"""
    r = run_cli(
        c, m, ["-", "-", "--json"], "Þetta var 14. mars og 11 manns viðstaddir."
    )
    assert r.strip() == expected_json_out.strip()

    # CSV output
    expected_csv_out = """
6,"Þetta","","Þetta","0-1-2-3-4"
6,"var",""," var","1-2-3"
19,"14. mars","0|3|14"," 14. mars","1-2-3-4-5-6-7-8"
6,"og",""," og","1-2"
5,"11",11," 11","1-2"
6,"manns",""," manns","1-2-3-4-5"
6,"viðstaddir",""," viðstaddir","1-2-3-4-5-6-7-8-9-10"
1,".",".",".","0"
0,"","","",""
"""

    r = run_cli(c, m, ["-", "-", "--csv"], "Þetta var 14. mars og 11 manns viðstaddir.")
    assert r.strip() == expected_csv_out.strip()

    # Normalize punctuation, quote marks, and dashes
    # --normalize flag
    t = "'Þetta gengur ekki,' sagði hann, \"Við vitum ekkert - ekki einu sinni nafnið.\""
    r = run_cli(c, m, ["-", "-"], t)
    assert (
        r
        == "' Þetta gengur ekki , ' sagði hann , \" Við vitum ekkert - ekki einu sinni nafnið . \""
    )
    r = run_cli(c, m, ["-", "-", "--normalize"], t)
    assert (
        r
        == "‚ Þetta gengur ekki , ‘ sagði hann , „ Við vitum ekkert - ekki einu sinni nafnið . “"
    )

    # Once sentence per line
    # --one_sent_per_line flag
    t = "Þetta er setning\nÞetta er önnur setning\nÞetta er þriðja setningin"
    r = run_cli(c, m, ["-", "-"], t)
    assert r == "Þetta er setning Þetta er önnur setning Þetta er þriðja setningin"
    r = run_cli(c, m, ["-", "-", "--one_sent_per_line"], t)
    assert r == "Þetta er setning\nÞetta er önnur setning\nÞetta er þriðja setningin"

    # Output original token text (sentence splitter only)
    # --original flag
    t = "Við gerðum afar lítið þann dag. En síðar í vikunni var tekin vinnutörn."
    r = run_cli(c, m, ["-", "-"], t)
    assert (
        r
        == "Við gerðum afar lítið þann dag .\nEn síðar í vikunni var tekin vinnutörn ."
    )
    r = run_cli(c, m, ["-", "-", "--original"], t)
    assert (
        r == "Við gerðum afar lítið þann dag.\n En síðar í vikunni var tekin vinnutörn."
    )

    # Normalize temperature degrees
    # --convert_measurements
    t = "Það var 25° C í sumarbústaðunum, en bara 15° C í bænum."
    r = run_cli(c, m, ["-", "-"], t)
    assert r == "Það var 25° C í sumarbústaðunum , en bara 15° C í bænum ."
    r = run_cli(c, m, ["-", "-", "--convert_measurements"], t)
    assert r == "Það var 25 °C í sumarbústaðunum , en bara 15 °C í bænum ."

    # Numbers combined into one token with percentage word forms
    # --coalesce_percent
    t = "Þetta var 70 prósent rétt hjá honum"
    expected_json_out = """
{"k":"BEGIN SENT","t":""}
{"k":"WORD","t":"Þetta","o":"Þetta","s":[0,1,2,3,4]}
{"k":"WORD","t":"var","o":" var","s":[1,2,3]}
{"k":"NUMBER","t":"70","v":70,"o":" 70","s":[1,2]}
{"k":"WORD","t":"prósent","o":" prósent","s":[1,2,3,4,5,6,7]}
{"k":"WORD","t":"rétt","o":" rétt","s":[1,2,3,4]}
{"k":"WORD","t":"hjá","o":" hjá","s":[1,2,3]}
{"k":"WORD","t":"honum","o":" honum","s":[1,2,3,4,5]}
{"k":"END SENT","t":""}
"""
    r = run_cli(c, m, ["-", "-", "--json"], t)
    assert r.strip() == expected_json_out.strip()

    expected_json_out = """
{"k":"BEGIN SENT","t":""}
{"k":"WORD","t":"Þetta","o":"Þetta","s":[0,1,2,3,4]}
{"k":"WORD","t":"var","o":" var","s":[1,2,3]}
{"k":"PERCENT","t":"70 prósent","v":70,"o":" 70 prósent","s":[1,2,3,4,5,6,7,8,9,10]}
{"k":"WORD","t":"rétt","o":" rétt","s":[1,2,3,4]}
{"k":"WORD","t":"hjá","o":" hjá","s":[1,2,3]}
{"k":"WORD","t":"honum","o":" honum","s":[1,2,3,4,5]}
{"k":"END SENT","t":""}
"""
    t = "Þetta var 70 prósent rétt hjá honum"
    r = run_cli(c, m, ["-", "-", "--json", "--coalesce_percent"], t)
    assert r.strip() == expected_json_out.strip()

    # Do not replace composite glyphs using Unicode COMBINING codes
    # --keep_composite_glyphs
    comp = "a" + chr(769)  # 'a' with combining acute accent
    t = f"Ég á heima {comp} Íslandi."
    r = run_cli(c, m, ["-", "-"], t)
    assert r == "Ég á heima á Íslandi ."
    # TODO: Broken
    # r = run_cli(c, m, ["-", "-", "--keep_composite_glyphs"], t)
    # assert r == t

    # Replace HTML escape codes
    # --replace_html_escapes flag
    t = "Hann &aacute; ekki s&eacute;ns &iacute; &thorn;etta"
    r = run_cli(c, m, ["-", "-"], t)
    assert r == "Hann & aacute ; ekki s & eacute ; ns & iacute ; & thorn ; etta"
    r = run_cli(c, m, ["-", "-", "--replace_html_escapes"], t)
    assert r == "Hann á ekki séns í þetta"

    # Change English decimal separator to Icelandic
    # --convert_numbers flag
    t = "Hann fékk 7.5 í meðaleinkunn en bara 3.3 í íþróttum, og hlaut 2,000.5 USD fyrir."
    r = run_cli(c, m, ["-", "-"], t)
    assert (
        r
        == "Hann fékk 7.5 í meðaleinkunn en bara 3.3 í íþróttum , og hlaut 2,000.5 USD fyrir ."
    )
    r = run_cli(c, m, ["-", "-", "--convert_numbers"], t)
    assert (
        r
        == "Hann fékk 7,5 í meðaleinkunn en bara 3,3 í íþróttum , og hlaut 2.000,5 USD fyrir ."
    )

    # Handle kludgy ordinals
    # --handle_kludgy_ordinals flag
    t = "Hann var 1sti maðurinn til að heimsækja tunglið."
    r = run_cli(c, m, ["-", "-", "--handle_kludgy_ordinals", "1"], t)
    assert r == "Hann var fyrsti maðurinn til að heimsækja tunglið ."
    # TODO: Broken functionality, needs to be fixed
    # r = run_cli(c, m, ["-", "-", "--handle_kludgy_ordinals", "2"], t)
    # assert r == "Hann var 1. maðurinn til að heimsækja tunglið ."

    # TODO: Add more tests for the CLI to achieve 100% coverage
