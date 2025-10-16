# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

py-estrattoconto is a Python package for extracting and enriching transaction data from Italian bank statement PDFs (estratto conto). The project uses the `docling` library for document conversion and provides both a Python API and CLI interface.

The package is structured as a modern Python project using Poetry for dependency management and packaging.

## Architecture

### Core Pipeline

The extraction pipeline consists of four main stages:

1. **PDF Conversion** (src/estrattoconto/converter.py:47-49): Uses `docling.DocumentConverter` to convert PDF documents into structured document objects with tables
2. **Document Type Detection** (src/estrattoconto/converter.py:10-24): Automatically identifies the bank type by scanning document text for known bank identifiers
3. **Table Extraction** (src/estrattoconto/converter.py:46-73): Extracts four specific table types from the converted document based on detected bank type
4. **Data Enrichment** (src/estrattoconto/enrichment.py:30-108): Extracts semantic information from raw transaction data and adds classification flags

### Package Structure

```
src/estrattoconto/
├── __init__.py         # Public API exports
├── __version__.py      # Version information
├── __main__.py         # CLI entry point
├── config.py           # Bank constants (CENTROVENETO, UNSUPPORTED)
├── converter.py        # PDF extraction and table conversion
├── enrichment.py       # Data enrichment and classification
└── utils.py            # Currency conversion utilities
```

### Bank-Specific Parsing

The codebase uses an automatic bank type detection system (src/estrattoconto/converter.py:10-24):
- Scans document text using `extract_document_type()` to find bank identifier strings
- Currently supports: CENTROVENETO ("BANCA VENETO CENTRALE")
- Returns UNSUPPORTED for unrecognized document types

For CENTROVENETO statements, the table structure is:
- Table 0: Book balance (period information)
- Table 1: Account information
- Tables 2 to n-1: Transaction data tables
- Table n (last): Balance summary

### Data Flow

```
PDF file → DocumentConverter → extract_document_type() →
extract_table() → 4 DataFrames (book_balance, account_info, balance_summary, transactions) →
postprocess_extraction() → enrich_data() → Final enriched DataFrame
```

### Enrichment Process (src/estrattoconto/enrichment.py:30-108)

The enrichment pipeline transforms raw transaction data into a structured, classified dataset:

1. **Column Selection & Cleaning** (src/estrattoconto/enrichment.py:6-28): Keeps only essential columns (DATA MOV., VALUTA, DARE, AVERE, DESCRIZIONE OPERAZIONE) and drops NaN rows

2. **Entity Extraction**: Uses regex patterns on DESCRIZIONE OPERAZIONE field to extract:
   - `payer`: Extracted from "Ordinante: ... Causale" pattern
   - `payee`: Extracted from "ADDEBITO CRED. ... ID.MANDATO" pattern
   - `id_mandato`: Extracted from "ID.MANDATO ... RIF./SDD" pattern

3. **Currency Conversion** (src/estrattoconto/utils.py:6-47): The `clean_and_convert_currency()` function handles Italian currency format:
   - Removes € symbol and spaces
   - Converts thousands separator (.) to nothing
   - Converts decimal separator (,) to period (.)
   - Strips +/- signs
   - Converts to numeric float
   - Applied to both DARE (debit) and AVERE (credit) columns

4. **Amount Normalization**: Combines DARE_Numeric and AVERE_Numeric into single `amount` column using `combine_first()`

5. **Transaction Classification**: Adds boolean flags based on text patterns:
   - `is_bill`: Contains "S.D.D." (direct debit)
   - `is_incoming_transfer`: Contains "BONIFICO A VS. FAVORE"
   - `is_outcoming_transfer`: Contains "BONIFICO coordinate benef"
   - `is_bank_fee`: Contains "CANONE"

6. **Metadata Addition**: Enriches with contextual data from other tables:
   - `related_account`: From account_information table (extracted_tables[1])
   - `period`: From book_balance table (extracted_tables[0])

## Development Commands

### Initial Setup

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies (including dev dependencies)
poetry install

# Activate virtual environment
poetry shell
```

### Running Tests

```bash
# Run all tests with pytest
poetry run pytest

# Run with coverage report
poetry run pytest --cov=estrattoconto --cov-report=term-missing

# Run specific test file
poetry run pytest tests/test_converter.py

# Run specific test function
poetry run pytest tests/test_utils.py::TestUtils::test_clean_and_convert_currency_basic
```

Note: Tests reference `tests/fixture/centroveneto.pdf` which is not committed to the repository (PDFs are gitignored for security).

### Code Quality

```bash
# Format code with black
poetry run black src/ tests/

# Lint with ruff
poetry run ruff check src/ tests/

# Lint with pylint (used in CI)
poetry run pylint src/estrattoconto
poetry run pylint $(git ls-files '*.py')

# Type checking with mypy
poetry run mypy src/estrattoconto
```

### Using the CLI

```bash
# Run CLI in development mode
poetry run estrattoconto extract path/to/statement.pdf

# Save output to CSV
poetry run estrattoconto extract path/to/statement.pdf --output transactions.csv

# Get help
poetry run estrattoconto --help
poetry run estrattoconto extract --help
```

### Building and Publishing

```bash
# Build package (creates wheel and sdist in dist/)
poetry build

# Install package locally for testing
pip install dist/estrattoconto-0.1.0-py3-none-any.whl

# Publish to PyPI (requires authentication)
poetry publish

# Publish to Test PyPI first
poetry publish --repository testpypi
```

The project uses GitHub Actions to run pylint on every push (Python 3.13+).

## Key Implementation Details

### Adding Support for New Banks

To add a new bank format:

1. Add bank identifier constant to `src/estrattoconto/config.py` (e.g., `NEWBANK = "BANK NAME"`)
2. Update `extract_document_type()` (src/estrattoconto/converter.py:10-24) to detect the new bank's identifier in document text
3. Update the conditional in `extract_table()` (src/estrattoconto/converter.py:54-73) to handle the new bank's table structure
4. Update `enrich_data()` (src/estrattoconto/enrichment.py) with bank-specific regex patterns for that bank's transaction description format
5. Add tests in `tests/test_converter.py` for the new bank
6. Test with fixture PDF from that bank

### Italian Currency Format Handling

The codebase is specifically designed for Italian banking formats:
- **Thousands separator**: Period (.) - e.g., 1.000 = one thousand
- **Decimal separator**: Comma (,) - e.g., 1.234,56 = 1234.56
- **Currency symbol**: € (euro)
- **Sign notation**: Prefix +/- before amount

The `clean_and_convert_currency()` function (src/estrattoconto/utils.py:6-47) must be applied to all monetary columns before numeric operations.

### Regex Pattern Matching for Transaction Classification

All transaction enrichment relies on pattern matching within the `DESCRIZIONE OPERAZIONE` (operation description) field. When adding new transaction types:

1. Identify the text pattern that uniquely identifies that transaction type
2. Add extraction regex using `str.extract()` for entity extraction (returns matched group)
3. Add classification regex using `str.contains()` for boolean flags (returns True/False)
4. Use `case=False, na=False` parameters to handle missing/null values safely

## Python Version

Target: Python 3.10+ (supports 3.10, 3.11, 3.12, 3.13)

CI runs tests on Python 3.13 (as specified in GitHub Actions workflow)

## Dependencies

Managed via Poetry in `pyproject.toml`:

**Runtime dependencies:**
- pandas ^2.0.0 (DataFrame operations)
- numpy ^1.24.0 (numeric operations)
- docling ^2.0.0 (PDF document conversion library)

**Development dependencies:**
- pytest ^8.0.0 (testing framework)
- pytest-cov ^5.0.0 (coverage reports)
- pylint ^3.0.0 (linting)
- black ^24.0.0 (code formatting)
- ruff ^0.4.0 (fast linting)
- mypy ^1.9.0 (type checking)
- pandas-stubs ^2.0.0 (type stubs for pandas)

## Current Limitations & Known Issues

1. **Bug in extract_document_type()** (src/estrattoconto/converter.py:10-24): The function returns UNSUPPORTED on the first iteration when the bank identifier is NOT found, instead of continuing to check all text elements. This should loop through all texts before returning UNSUPPORTED.

2. **No SQL Export Implementation**: Django integration is pending. Users can export to CSV using the CLI or save DataFrames manually.

3. **Empty Dare/Avere Filtering** (src/estrattoconto/enrichment.py:73-76): The code sets DARE/AVERE to empty string when they don't contain "€", but this logic may need refinement as the currency symbol should always be present in valid monetary columns.

4. **Old main.py**: The original `main.py` file still exists but is now obsolete. The package code is in `src/estrattoconto/`. Consider removing or updating `main.py` to avoid confusion.
