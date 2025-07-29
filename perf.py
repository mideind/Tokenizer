#!/usr/bin/env python3

import timeit
from collections import deque

from tokenizer import tokenize


def run_tok():
    with open("out1mb.txt", "r", encoding="utf-8") as f:
        deque(tokenize(f), maxlen=0)


def main():
    execution_time = timeit.timeit(
        "run_tok()", setup="from __main__ import run_tok", number=1
    )
    print(f"Execution time: {execution_time:.6f} seconds")


if __name__ == "__main__":
    main()
