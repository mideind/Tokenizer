# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tokenizer is a Python (>= 3.9) library for tokenizing Icelandic text. It converts input text into streams of tokens (words, punctuation, numbers, dates, etc.) and segments them into sentences. The project supports both shallow tokenization (space-separated strings) and deep tokenization (structured token objects with type annotations and metadata).

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
python -m pytest                    # Run all tests
python -m pytest test/test_tokenizer.py  # Run specific test file
python -m pytest -v test/test_tokenizer.py::test_single_tokens  # Run specific test
```

### Linting and Type Checking
```bash
ruff check src/tokenizer            # Code linting (configured in pyproject.toml)
ruff format src/tokenizer           # Code formatting
mypy src/tokenizer                  # Type checking (config in mypy.ini)
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
```bash
tokenize test/toktest_large.txt test/toktest_large_out.txt
diff test/toktest_large_out.txt test/toktest_large_gold_acceptable.txt
```

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
- **mypy.ini**: Type checker configuration (currently set for Python 3.6/PyPy)
- **Abbrev.conf**: Icelandic abbreviation dictionary

## Testing Structure

- **test_tokenizer.py**: Main tokenization logic tests
- **test_cli.py**: Command-line interface tests
- **test_abbrev.py**: Abbreviation handling tests
- **test_detokenize.py**: Detokenization tests
- **toktest_large.txt**: Comprehensive test dataset (13,075 lines)

## Type Checking

- The project uses type annotations in all code and tries to avoid Any types
- Python 3.9 is supported so type annotations should adhere to 3.9-compatible syntax
- Note: mypy.ini currently targets Python 3.6 for PyPy compatibility

## Development Environment

- For running Python code in this project, activate the virtualenv via `source ~/github/Greynir/pypy/bin/activate` (from CLAUDE.local.md)