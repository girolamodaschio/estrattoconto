# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

estrattoconto is a Python package for extracting and enriching transaction data from Italian bank statement PDFs (estratto conto). The project uses the `docling` library for document conversion and provides both an object-oriented Python API and CLI interface.

The package is structured as a modern Python project using Poetry for dependency management and packaging.

## Architecture

### Design Pattern: Object-Oriented API

The package provides a **primary object-oriented API** through the `EstrattoConto` class, with a legacy functional API for backward compatibility.

**Primary API Pattern:**
```python
import estrattoconto
statement = estrattoconto.convert('statement.pdf')  # Returns EstrattoConto object
statement.to_csv('output.csv')
payers = statement.extract_payers()
```

**Legacy Functional API:**
```python
from estrattoconto import extract_table, enrich_data
tables = extract_table('statement.pdf')
enriched_df = enrich_data(tables)
```

### Core Pipeline

The extraction pipeline consists of four main stages:

1. **PDF Conversion** (src/estrattoconto/converter.py): Uses `docling.DocumentConverter` to convert PDF documents into structured document objects with tables
2. **Document Type Detection** (src/estrattoconto/converter.py:10-24): Automatically identifies the bank type by scanning document text for known bank identifiers
3. **Table Extraction** (src/estrattoconto/converter.py:46-73): Extracts four specific table types from the converted document based on detected bank type
4. **Data Enrichment** (src/estrattoconto/enrichment.py): Extracts semantic information from raw transaction data and adds classification flags
5. **Object Wrapping** (src/estrattoconto/statement.py): Wraps enriched DataFrame in `EstrattoConto` class with query and export methods

### Package Structure

```
src/estrattoconto/
├── __init__.py         # Public API exports (convert(), EstrattoConto, legacy functions)
├── __version__.py      # Version information (0.1.0)
├── __main__.py         # CLI entry point
├── config.py           # Bank constants (CENTROVENETO, UNSUPPORTED)
├── converter.py        # PDF extraction and table conversion (functional)
├── enrichment.py       # Data enrichment and classification (functional)
├── utils.py            # Currency conversion utilities
└── statement.py        # EstrattoConto class (object-oriented API) ⭐ NEW
```

### EstrattoConto Class (src/estrattoconto/statement.py)

The main user-facing class that wraps enriched transaction data:

**Factory Method:**
- `EstrattoConto.from_pdf(pdf_path)` - Create from PDF

**Export Methods:**
- `to_csv(output_path)` - Export to CSV
- `to_json(output_path)` - Export to JSON
- `to_excel(output_path)` - Export to Excel

**Query Methods:**
- `extract_payers()` - Get list of unique payers
- `extract_payees()` - Get list of unique payees

**Filter Methods:**
- `get_bills()` - Filter direct debits (S.D.D.)
- `get_incoming_transfers()` - Filter incoming wire transfers
- `get_outgoing_transfers()` - Filter outgoing wire transfers
- `get_fees()` - Filter bank fees
- `filter_by_date(start, end)` - Date range filtering

**Utility Methods:**
- `get_dataframe()` - Access underlying pandas DataFrame
- `summary()` - Get statistics dictionary
- `__len__()` - Count transactions
- `__repr__()` - String representation

### Data Flow

```
PDF file → DocumentConverter → extract_document_type() →
extract_table() → 4 DataFrames (book_balance, account_info, balance_summary, transactions) →
postprocess_extraction() → enrich_data() → Enriched DataFrame →
EstrattoConto wrapper → User interacts with methods
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

### Enrichment Process (src/estrattoconto/enrichment.py)

The enrichment pipeline transforms raw transaction data into a structured, classified dataset:

1. **Column Selection & Cleaning**: Keeps only essential columns (DATA MOV., VALUTA, DARE, AVERE, DESCRIZIONE OPERAZIONE) and drops NaN rows

2. **Entity Extraction**: Uses regex patterns on DESCRIZIONE OPERAZIONE field to extract:
   - `payer`: Extracted from "Ordinante: ... Causale" pattern
   - `payee`: Extracted from "ADDEBITO CRED. ... ID.MANDATO" pattern
   - `id_mandato`: Extracted from "ID.MANDATO ... RIF./SDD" pattern

3. **Currency Conversion** (src/estrattoconto/utils.py): The `clean_and_convert_currency()` function handles Italian currency format:
   - Removes € symbol and spaces
   - Converts thousands separator (.) to nothing
   - Converts decimal separator (,) to period (.)
   - Strips +/- signs
   - Converts to numeric float
   - Applied to both DARE (debit) and AVERE (credit) columns

4. **Amount Normalization**: Combines DARE_Numeric and AVERE_Numeric into single `amount` column

5. **Transaction Classification**: Adds boolean flags based on text patterns:
   - `is_bill`: Contains "S.D.D." (direct debit)
   - `is_incoming_transfer`: Contains "BONIFICO A VS. FAVORE"
   - `is_outcoming_transfer`: Contains "BONIFICO coordinate benef"
   - `is_bank_fee`: Contains "CANONE"

6. **Metadata Addition**: Enriches with contextual data from other tables (account, period)

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
poetry run pytest tests/test_statement.py
poetry run pytest tests/test_converter.py

# Run specific test function
poetry run pytest tests/test_statement.py::TestEstrattoConto::test_extract_payers
```

Note: Tests reference `tests/fixture/centroveneto.pdf` which is not committed to the repository (PDFs are gitignored for security).

### Code Quality

```bash
# Format code with black
poetry run black src/ tests/ examples/

# Lint with ruff
poetry run ruff check src/ tests/ examples/

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

### Running Examples

```bash
# Run the basic usage example
poetry run python examples/basic_usage.py

# After installing package
python examples/basic_usage.py
```

### Building and Publishing

```bash
# Build package (creates wheel and sdist in dist/)
poetry build

# Install package locally for testing
pip install dist/estrattoconto-0.1.0-py3-none-any.whl

```

The project uses GitHub Actions to run pylint on every push (Python 3.13+).

## Key Implementation Details

### Adding Support for New Banks

To add a new bank format:

1. Add bank identifier constant to `src/estrattoconto/config.py` (e.g., `NEWBANK = "BANK NAME"`)
2. Update `extract_document_type()` (src/estrattoconto/converter.py:10-24) to detect the new bank's identifier in document text
3. Update the conditional in `extract_table()` (src/estrattoconto/converter.py:54-73) to handle the new bank's table structure
4. Update `enrich_data()` (src/estrattoconto/enrichment.py) with bank-specific regex patterns for that bank's transaction description format
5. Add tests in `tests/test_converter.py` and `tests/test_statement.py` for the new bank
6. Test with fixture PDF from that bank

### Adding New Methods to EstrattoConto Class

When adding new query or filter methods to the `EstrattoConto` class:

1. Add the method to `src/estrattoconto/statement.py`
2. Follow the existing pattern: methods that filter return `pd.DataFrame`, methods that extract return `List[str]`
3. Add comprehensive tests in `tests/test_statement.py`
4. Update docstrings with examples
5. Consider if the method should be exposed in `__init__.py`

### Italian Currency Format Handling

The codebase is specifically designed for Italian banking formats:
- **Thousands separator**: Period (.) - e.g., 1.000 = one thousand
- **Decimal separator**: Comma (,) - e.g., 1.234,56 = 1234.56
- **Currency symbol**: € (euro)
- **Sign notation**: Prefix +/- before amount

The `clean_and_convert_currency()` function (src/estrattoconto/utils.py) must be applied to all monetary columns before numeric operations.

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

2. **No SQL Export Implementation**: Django integration is pending. Users can export to CSV/JSON/Excel using the `EstrattoConto` methods.

3. **Empty Dare/Avere Filtering** (src/estrattoconto/enrichment.py): The code sets DARE/AVERE to empty string when they don't contain "€", but this logic may need refinement as the currency symbol should always be present in valid monetary columns.

## Project Structure

```
estrattoconto/
├── src/estrattoconto/          # Main package
├── tests/                      # Test suite
├── examples/                   # Usage examples
│   ├── basic_usage.py          # Demonstrates OO API
│   └── README.md               # Examples documentation
├── pyproject.toml              # Poetry configuration
├── README.md                   # User-facing documentation
└── CLAUDE.md                   # This file
```
