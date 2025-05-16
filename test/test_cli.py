# type: ignore

"""
    Test the command line interface (CLI) of the tokenizer.
    Copyright (C) 2025 Miðeind ehf.
"""


from io import StringIO
import sys
from unittest.mock import patch

from tokenizer.main import main
from tokenizer import __version__ as tokenizer_version


CLT_NAME = "tokenize"


def run_cli(c, m, args: list[str], standard_input: str = "") -> str:
    """Run the command line interface (CLI) main function with
    the given arguments and standard input."""

    # Feed the provided string into standard input
    old_stdin = sys.stdin
    input = StringIO(standard_input)
    m.setattr(sys, "stdin", input)

    # Run the main function with the provided arguments
    try:
        with patch.object(sys, "argv", [CLT_NAME] + args):
            main()
    except SystemExit as e:
        assert e.code == 0, f"Expected exit code 0 from CLT, got {e.code}"

    # Capture the output
    output = c.readouterr()

    # Restore the original standard input
    m.setattr(sys, "stdin", old_stdin)

    return output.out.strip()


def test_cli(capsys, monkeypatch):
    """Test the command line interface (CLI) of the tokenizer."""
    c = capsys
    m = monkeypatch

    assert run_cli(c, m, ["--version"]).endswith(tokenizer_version)
    assert "usage:" in run_cli(c, m, ["--help"])

    assert (
        run_cli(c, m, ["-", "-"], "Hann Jón,sem kom kl.14:00 í dag, fór seinna.")
        == "Hann Jón , sem kom kl. 14:00 í dag , fór seinna ."
    )

    def clean_json(s: str) -> str:
        """Clean the JSON output by removing unnecessary whitespace."""
        return s.strip()

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
    assert clean_json(r) == clean_json(expected_json_out)

    # TODO: Add more tests for the CLI to achieve 100% coverage
