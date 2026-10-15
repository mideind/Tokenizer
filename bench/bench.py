#!/usr/bin/env python3
"""
Tokenizer performance bench.

Times a handful of realistic workloads over the test corpus and prints a
digest of the full token output for each, so that an optimization can be
checked for identical results as well as for speed.

    python bench/bench.py                       # time all workloads
    python bench/bench.py -w tokenize -n 10     # one workload, 10 runs
    python bench/bench.py --save base.json      # record timings + digests
    python bench/bench.py --compare base.json   # diff against a recording
    python bench/bench.py --loop tokenize -s 20 # busy loop for a profiler

Profile with the CPython 3.15 sampling profiler, see bench/profile.sh.
"""

import argparse
from collections import deque
from collections.abc import Callable, Iterable, Iterator
import gc
import hashlib
import json
from pathlib import Path
import sys
import time

from tokenizer import Tok, split_into_sentences, tokenize
from tokenizer.abbrev import Abbreviations

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FILES = [
    ROOT / "test" / "toktest_large.txt",
    ROOT / "test" / "Overview.txt",
]


def load_lines(files: list[Path], repeat: int) -> list[str]:
    lines: list[str] = []
    for f in files:
        lines.extend(f.read_text(encoding="utf-8").splitlines(keepends=True))
    return lines * repeat


def tok_record(t: Tok) -> str:
    return repr((t.kind, t.txt, t.val, t.original, t.origin_spans))


# Each workload maps the input lines to an iterator of strings that
# fully describe its output; timing consumes the iterator unhashed,
# digesting hashes it.
Workload = Callable[[list[str]], Iterator[str]]


def w_tokenize(lines: list[str]) -> Iterator[str]:
    return map(tok_record, tokenize(lines))


def w_tokenize_noann(lines: list[str]) -> Iterator[str]:
    return map(tok_record, tokenize(lines, with_annotation=False))


def w_tokenize_text(lines: list[str]) -> Iterator[str]:
    # A single string rather than a line iterator
    return map(tok_record, tokenize("".join(lines)))


def w_sentences(lines: list[str]) -> Iterator[str]:
    return split_into_sentences(lines)


def w_sentences_original(lines: list[str]) -> Iterator[str]:
    return split_into_sentences(lines, original=True)


# For timing we skip tok_record() so that only tokenizer work is measured
TIMED: dict[str, Callable[[list[str]], Iterable[object]]] = {
    "tokenize": lambda lines: tokenize(lines),
    "tokenize_noann": lambda lines: tokenize(lines, with_annotation=False),
    "tokenize_text": lambda lines: tokenize("".join(lines)),
    "sentences": lambda lines: split_into_sentences(lines),
    "sentences_original": lambda lines: split_into_sentences(lines, original=True),
}
DIGESTED: dict[str, Workload] = {
    "tokenize": w_tokenize,
    "tokenize_noann": w_tokenize_noann,
    "tokenize_text": w_tokenize_text,
    "sentences": w_sentences,
    "sentences_original": w_sentences_original,
}


def time_once(name: str, lines: list[str]) -> float:
    fn = TIMED[name]
    gc.collect()
    t0 = time.perf_counter()
    deque(fn(lines), maxlen=0)
    return time.perf_counter() - t0


def digest(name: str, lines: list[str]) -> tuple[str, int]:
    h = hashlib.sha256()
    n = 0
    for rec in DIGESTED[name](lines):
        h.update(rec.encode("utf-8"))
        h.update(b"\n")
        n += 1
    return h.hexdigest()[:16], n


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("-w", "--workload", action="append", choices=list(TIMED))
    ap.add_argument(
        "-n", "--runs", type=int, default=5, help="timed runs (min is reported)"
    )
    ap.add_argument(
        "-r", "--repeat", type=int, default=1, help="repeat the corpus N times"
    )
    ap.add_argument("-f", "--file", action="append", type=Path, help="input file(s)")
    ap.add_argument("--no-digest", action="store_true", help="skip the output digest")
    ap.add_argument("--save", type=Path, help="save results as JSON")
    ap.add_argument("--compare", type=Path, help="compare with saved JSON")
    ap.add_argument(
        "--loop",
        choices=list(TIMED),
        help="run one workload repeatedly (for attaching or running a profiler)",
    )
    ap.add_argument(
        "-s", "--seconds", type=float, default=15.0, help="duration for --loop"
    )
    args = ap.parse_args()

    files = args.file or DEFAULT_FILES
    lines = load_lines(files, args.repeat)
    nbytes = sum(len(s.encode("utf-8")) for s in lines)
    Abbreviations.initialize()  # Keep the one-time setup out of the timings

    if args.loop:
        deadline = time.perf_counter() + args.seconds
        runs = 0
        while time.perf_counter() < deadline:
            deque(TIMED[args.loop](lines), maxlen=0)
            runs += 1
        print(f"{args.loop}: {runs} runs in {args.seconds:.0f} s", file=sys.stderr)
        return

    names = args.workload or list(TIMED)
    base = json.loads(args.compare.read_text()) if args.compare else {}
    results: dict[str, dict[str, object]] = {}
    print(
        f"Python {sys.version.split()[0]}  "
        f"input {nbytes / 1e6:.2f} MB, {len(lines)} lines, {args.runs} runs (min)"
    )
    for name in names:
        times = [time_once(name, lines) for _ in range(args.runs)]
        best = min(times)
        res: dict[str, object] = {
            "best": best,
            "median": sorted(times)[len(times) // 2],
        }
        line = f"{name:<20} {best * 1000:9.1f} ms  {nbytes / best / 1e6:6.2f} MB/s"
        if not args.no_digest:
            dg, n = digest(name, lines)
            res.update(digest=dg, records=n)
            line += f"  {n:7} recs  {dg}"
        if name in base:
            b = base[name]
            line += f"  {(float(b['best']) / best - 1) * 100:+6.1f}% speed"
            if not args.no_digest and "digest" in b:
                line += "  same" if b["digest"] == res["digest"] else "  OUTPUT DIFFERS"
        print(line, flush=True)
        results[name] = res

    if args.save:
        args.save.write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
