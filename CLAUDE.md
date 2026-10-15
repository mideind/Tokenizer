# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tokenizer is a Python (>= 3.10) library for tokenizing Icelandic text. It converts input text into streams of tokens (words, punctuation, numbers, dates, etc.) and segments them into sentences. The project supports both shallow tokenization (space-separated strings) and deep tokenization (structured token objects with type annotations and metadata).

## Core Architecture

- **`src/tokenizer/tokenizer.py`**: Main tokenization engine containing the `tokenize()` function and core logic
- **`src/tokenizer/definitions.py`**: Token type constants, data structures, and type definitions (TOK class, tuple types)
- **`src/tokenizer/main.py`**: Command-line interface implementation for the `tokenize` command
- **`src/tokenizer/abbrev.py`**: Abbreviation handling and configuration parsing
- **`src/tokenizer/Abbrev.conf`**: Dictionary of Icelandic abbreviations with their expansions
- **`src/tokenizer/__init__.py`**: Package exports and public API

## Key Functions

- `tokenize()`: Deep tokenization returning structured token objects
- `split_into_sentences()`: Shallow tokenization returning space-separated strings
- `detokenize()`: Reconstructs text from token objects
- `correct_spaces()`: Normalizes whitespace around punctuation

## Development Commands

### Testing
```bash
uv run --group test pytest                    # Run all tests
uv run --group test pytest test/test_tokenizer.py  # Run specific test file
uv run --group test pytest -v test/test_tokenizer.py::test_single_tokens  # Run specific test
```

### Linting and Type Checking
```bash
uv run --group lint ruff check src/tokenizer  # Code linting
uv run --group lint ruff format src/tokenizer # Code formatting
uv run --group type mypy src/tokenizer        # Type checking
```

### Installation
```bash
pip install -e ".[dev]"             # Development installation with test dependencies
```

### Command Line Usage
```bash
tokenize input.txt output.txt       # Basic tokenization
tokenize --json input.txt output.txt # JSON format output
tokenize --csv input.txt output.txt  # CSV format output
echo "Texti hér." | tokenize        # Pipe from stdin
```

### Large Test Set Validation
`test/test_large_gold.py` fails if the CLI output for `test/toktest_large.txt` differs
from `test/toktest_large_gold_acceptable.txt` (the current output, enforced). For an
intended tokenization change, regenerate the gold file and review its diff:
```bash
tokenize test/toktest_large.txt test/toktest_large_gold_acceptable.txt
git diff test/toktest_large_gold_acceptable.txt
```
`test/Overview.txt` cites line ranges `[input|gold]` in the gold file; they shift
when sentence splitting changes.

### Performance Bench
```bash
python bench/bench.py --save /tmp/base.json      # timings + output digests
python bench/bench.py --compare /tmp/base.json   # speed change, "same"/"OUTPUT DIFFERS"
bench/profile.sh tokenize 15                     # CPython 3.15 sampling profiler
```
Profile with `--blocking` (profile.sh does): without it the 3.15 sampler fails to
unwind ~70% of stacks in the generator pipeline and misattributes time.

## Token Types

The tokenizer recognizes 30+ token types including:
- `TOK.WORD`: Regular words and abbreviations
- `TOK.NUMBER`: Numeric values
- `TOK.DATEABS`/`TOK.DATEREL`: Absolute and relative dates
- `TOK.TIME`: Time expressions
- `TOK.AMOUNT`: Currency amounts
- `TOK.MEASUREMENT`: Values with units
- `TOK.EMAIL`, `TOK.URL`: Digital identifiers
- `TOK.S_BEGIN`/`TOK.S_END`: Sentence boundaries

## Configuration

- **pyproject.toml**: Project metadata, dependencies, ruff configuration
- **mypy.ini**: Compatibility shim; main type checker configuration is in pyproject.toml
- **Abbrev.conf**: Icelandic abbreviation dictionary

## Testing Structure

- **test_tokenizer.py**: Main tokenization logic tests
- **test_cli.py**: Command-line interface tests
- **test_abbrev.py**: Abbreviation handling tests
- **test_detokenize.py**: Detokenization tests
- **toktest_large.txt**: Comprehensive test dataset (13,075 lines)

## Type Checking

- The project uses type annotations in all code and tries to avoid Any types
- Python 3.10 is the oldest supported CPython baseline, so PEP 604 unions (`X | None`) and
  builtin generics (`list[str]`) are fine, but `typing.Self` (3.11) is not
- Tokenizer has no runtime dependencies: never import `typing_extensions` (ruff's
  autofix may try to)

## Development Environment

- For running Python code in this project, activate the virtualenv via `source ~/github/Greynir/pypy/bin/activate` (from CLAUDE.local.md)
