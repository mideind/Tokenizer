#!/usr/bin/env python3

import timeit
from collections import deque
import argparse
from tokenizer import tokenize


def run_tok(file_path: str) -> None:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            deque(tokenize(f), maxlen=0)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return

def main() -> None:
    parser = argparse.ArgumentParser(description="Tokenize a file and measure execution time.")
    parser.add_argument("file", nargs="?", default="out1mb.txt", help="Path to the input file (default: out1mb.txt)")
    args = parser.parse_args()

    # Pass the file path to run_tok via timeit
    setup_code = (
        "from __main__ import run_tok\n"
        f"file_path = '{args.file}'"
    )
    execution_time = timeit.timeit(
        "run_tok(file_path)", setup=setup_code, number=1
    )
    print(f"Execution time: {execution_time:.6f} seconds")


if __name__ == "__main__":
    main()
