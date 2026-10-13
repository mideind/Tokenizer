"""
Regression test for the large test set.
Copyright (C) 2026 Miðeind ehf.

The shallow tokenization of test/toktest_large.txt by the tokenize command
must match test/toktest_large_gold_acceptable.txt exactly. When a change
in tokenization is intended, regenerate the gold file and review its diff:

    tokenize test/toktest_large.txt test/toktest_large_gold_acceptable.txt

test/Overview.txt refers to line numbers in the gold file; see the note
at its end on how those line ranges were computed.
"""

import difflib
from pathlib import Path
import sys
from unittest.mock import patch

from pytest import CaptureFixture

from tokenizer.main import main

TEST_DIR = Path(__file__).parent
INPUT = TEST_DIR / "toktest_large.txt"
GOLD = TEST_DIR / "toktest_large_gold_acceptable.txt"


def test_large_gold(capsys: CaptureFixture[str]) -> None:
    # Explicit "-" so that argparse resolves sys.stdout at call time,
    # after capsys has replaced it
    with patch.object(sys, "argv", ["tokenize", str(INPUT), "-"]):
        main()
    output = capsys.readouterr().out.splitlines()
    gold = GOLD.read_text(encoding="utf-8").splitlines()
    if output != gold:
        diff = list(
            difflib.unified_diff(gold, output, "gold", "output", n=1, lineterm="")
        )
        changed = sum(1 for d in diff if d.startswith("-") and d != "--- gold")
        raise AssertionError(
            f"Output differs from {GOLD.name} on {changed} lines; first hunks:\n"
            + "\n".join(diff[:40])
        )
