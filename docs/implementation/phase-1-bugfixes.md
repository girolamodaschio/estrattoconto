# Phase 1: Foundation & Bug Fixes

**Priority:** CRITICAL
**Duration:** 1-2 days
**Impact:** HIGH - Stability and reliability

## Overview

This phase focuses on fixing critical bugs and stabilizing the current functionality before building new features. These fixes are essential for a reliable foundation.

---

## Task 1.1: Fix extract_document_type() Loop Bug

### Problem
**File:** `estrattoconto/converter.py:25-29`

Current code returns `UNSUPPORTED` on the first non-match instead of checking all text elements:

```python
def extract_document_type(converted_result):
    for el in converted_result.document.texts:
        if CENTROVENETO in el.text:
            return CENTROVENETO
        return UNSUPPORTED  # BUG: Returns too early!
```

### Solution

```python
def extract_document_type(converted_result):
    """
    Detect bank type by scanning all document text elements.

    Args:
        converted_result: ConversionResult from docling

    Returns:
        Bank identifier string or UNSUPPORTED
    """
    for el in converted_result.document.texts:
        if CENTROVENETO in el.text:
            return CENTROVENETO

    # Only return UNSUPPORTED after checking all elements
    return UNSUPPORTED
```

### Testing
Add test case in `tests/test_converter.py`:

```python
def test_extract_document_type_checks_all_elements(self):
    """Test that all text elements are checked before returning UNSUPPORTED."""
    # Create mock result with bank identifier in second element
    mock_result = Mock()
    mock_result.document.texts = [
        Mock(text="Some random text"),
        Mock(text="BANCA VENETO CENTRALE Account Statement"),
        Mock(text="More text")
    ]

    result = extract_document_type(mock_result)
    self.assertEqual(result, CENTROVENETO)
```

### Acceptance Criteria
- [ ] Loop continues through all text elements
- [ ] Returns UNSUPPORTED only after checking everything
- [ ] Test added and passing
- [ ] No regression in existing functionality

---

## Task 1.2: Add Missing Dependencies

### Problem
**File:** `pyproject.toml`

Critical dependencies are missing from the project configuration:
- `pandas` (used throughout but not declared)
- `numpy` (implicit dependency via pandas)
- `openpyxl` (required for Excel export in statement.py:156)

### Solution

Update `pyproject.toml` dependencies section:

```toml
[tool.poetry.dependencies]
python = "^3.10"
docling = "^2.58.0"
pandas = "^2.0.0"
numpy = "^1.24.0"
openpyxl = "^3.1.0"  # Required for Excel export
```

### Testing

```bash
# Remove current environment
poetry env remove python

# Reinstall from clean state
poetry install

# Test imports
poetry run python -c "import pandas; import numpy; import openpyxl; print('All imports successful')"

# Test Excel export
poetry run pytest tests/test_statement.py::TestEstrattoConto::test_to_excel -v
```

### Acceptance Criteria
- [ ] All dependencies explicitly declared in pyproject.toml
- [ ] Clean install works without errors
- [ ] Excel export functionality works
- [ ] All tests pass after fresh install

---

## Task 1.3: Add CLI Entry Point

### Problem
**File:** `pyproject.toml`

No entry point defined for the CLI, making it harder to use after installation.

### Solution

Add to `pyproject.toml`:

```toml
[tool.poetry.scripts]
estrattoconto = "estrattoconto.__main__:main"
```

### Testing

```bash
# Install package
poetry install

# Test CLI works
poetry run estrattoconto --help
poetry run estrattoconto extract tests/fixture/sample.pdf

# Test after pip install (in fresh venv)
pip install -e .
estrattoconto --help
```

### Acceptance Criteria
- [ ] CLI accessible via `estrattoconto` command
- [ ] Works with `poetry run estrattoconto`
- [ ] Works after `pip install -e .`
- [ ] Help text displays correctly

---

## Task 1.4: Create Missing amount Column

### Problem
**File:** `estrattoconto/enrichment.py`

The `amount` column is mentioned in README.md:87 but never created in the enrichment process.

### Current State

```python
# enrichment.py only creates:
# - DARE_Numeric
# - AVERE_Numeric
# But NOT amount column
```

### Solution

Add amount column creation in `enrich_data()`:

```python
def enrich_data(tables: tuple) -> pd.DataFrame:
    """
    Enrich transaction data with extracted entities and classifications.

    ...existing docstring...

    Columns added:
        ...existing columns...
        amount: Combined amount (AVERE_Numeric - DARE_Numeric)
    """
    # ... existing code ...

    # After creating DARE_Numeric and AVERE_Numeric
    enriched_table['DARE_Numeric'] = clean_and_convert_currency(enriched_table['DARE'])
    enriched_table['AVERE_Numeric'] = clean_and_convert_currency(enriched_table['AVERE'])

    # Create combined amount column
    # Convention: positive for credits (AVERE), negative for debits (DARE)
    enriched_table['amount'] = (
        enriched_table['AVERE_Numeric'].fillna(0) -
        enriched_table['DARE_Numeric'].fillna(0)
    )

    # ... rest of existing code ...

    return enriched_table
```

### Testing

Add test in `tests/test_enrichment.py`:

```python
def test_amount_column_created(self):
    """Test that amount column is created correctly."""
    # Create mock tables
    mock_tables = self._create_mock_tables()

    # Enrich
    result = enrich_data(mock_tables)

    # Check amount column exists
    self.assertIn('amount', result.columns)

    # Check calculation is correct
    # Positive for credits, negative for debits
    credit_row = result[result['AVERE_Numeric'] > 0].iloc[0]
    self.assertEqual(credit_row['amount'], credit_row['AVERE_Numeric'])

    debit_row = result[result['DARE_Numeric'] > 0].iloc[0]
    self.assertEqual(debit_row['amount'], -debit_row['DARE_Numeric'])
```

### Acceptance Criteria
- [ ] `amount` column created in enriched data
- [ ] Positive values for credits (AVERE)
- [ ] Negative values for debits (DARE)
- [ ] Test added and passing
- [ ] Update README.md if column list needs correction

---

## Task 1.5: Improve Error Handling

### Problem
Limited error handling throughout the codebase. Functions can fail with cryptic errors.

### Solution

Add comprehensive error handling in key functions:

#### converter.py

```python
from pathlib import Path

def extract_table(pdf_path: str) -> tuple:
    """
    Extract tables from PDF bank statement.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Tuple of (book_balance, account_info, balance_summary, transactions)

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If file is not a valid PDF
        RuntimeError: If docling conversion fails
    """
    # Validate file exists
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Validate file is PDF
    if pdf_file.suffix.lower() != '.pdf':
        raise ValueError(f"File must be a PDF, got: {pdf_file.suffix}")

    # Convert with error handling
    try:
        converter = DocumentConverter()
        converted_result: ConversionResult = converter.convert(source=pdf_path)
    except Exception as e:
        raise RuntimeError(f"Failed to convert PDF with docling: {e}") from e

    # Detect document type
    document_type = extract_document_type(converted_result)

    if document_type == UNSUPPORTED:
        raise ValueError(
            f"Unsupported document type. Currently supported banks: {CENTROVENETO}. "
            "Please check if this is a valid bank statement PDF."
        )

    # ... rest of existing code ...
```

#### enrichment.py

```python
def enrich_data(tables: tuple) -> pd.DataFrame:
    """
    Enrich transaction data.

    Args:
        tables: Tuple of (book_balance, account_info, balance_summary, transactions)

    Returns:
        Enriched DataFrame

    Raises:
        ValueError: If tables tuple is invalid
        TypeError: If tables is not a tuple
    """
    if not isinstance(tables, tuple):
        raise TypeError(f"Expected tuple, got {type(tables)}")

    if len(tables) != 4:
        raise ValueError(f"Expected 4 tables, got {len(tables)}")

    book_balance, account_info, balance_summary, transactions = tables

    if transactions.empty:
        raise ValueError("No transactions found in PDF")

    # ... rest of existing code ...
```

#### statement.py

```python
class EstrattoConto:
    @classmethod
    def from_pdf(cls, pdf_path: str) -> 'EstrattoConto':
        """
        Create EstrattoConto from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            EstrattoConto instance

        Raises:
            FileNotFoundError: If PDF doesn't exist
            ValueError: If PDF is invalid or unsupported
            RuntimeError: If processing fails
        """
        try:
            tables = extract_table(pdf_path)
            enriched_data = enrich_data(tables)
            return cls(enriched_data)
        except (FileNotFoundError, ValueError, RuntimeError) as e:
            # Re-raise with context
            raise type(e)(f"Failed to process PDF '{pdf_path}': {e}") from e
        except Exception as e:
            # Catch unexpected errors
            raise RuntimeError(
                f"Unexpected error processing PDF '{pdf_path}': {e}"
            ) from e
```

#### __main__.py (CLI)

```python
def main():
    # ... existing argparse setup ...

    try:
        # Validate file exists
        if not Path(args.pdf_path).exists():
            print(f"Error: File not found: {args.pdf_path}", file=sys.stderr)
            sys.exit(1)

        # Process PDF
        statement = convert(args.pdf_path, enrich=not args.no_enrich)

        # Output
        if args.output:
            statement.to_csv(args.output)
            print(f"✓ Extracted {len(statement)} transactions to {args.output}")
        else:
            print(statement.get_dataframe().to_string())

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(4)
```

### Testing

Add error handling tests:

```python
# tests/test_converter.py
def test_extract_table_file_not_found(self):
    with self.assertRaises(FileNotFoundError):
        extract_table("nonexistent.pdf")

def test_extract_table_invalid_file_type(self):
    with self.assertRaises(ValueError):
        extract_table("README.md")

# tests/test_enrichment.py
def test_enrich_data_invalid_input(self):
    with self.assertRaises(TypeError):
        enrich_data("not a tuple")

    with self.assertRaises(ValueError):
        enrich_data((pd.DataFrame(), pd.DataFrame()))  # Only 2 tables

# tests/test_statement.py
def test_from_pdf_invalid_file(self):
    with self.assertRaises(FileNotFoundError):
        EstrattoConto.from_pdf("nonexistent.pdf")
```

### Acceptance Criteria
- [ ] All functions have appropriate error handling
- [ ] Clear, helpful error messages
- [ ] Different exception types for different errors
- [ ] CLI returns appropriate exit codes
- [ ] Tests for error conditions added
- [ ] No regression in existing functionality

---

## Task 1.6: Add Input Validation

### Problem
No validation of extracted data quality or structure.

### Solution

Add validation utilities:

```python
# estrattoconto/validation.py (new file)
"""Data validation utilities."""

import pandas as pd
from typing import List, Dict, Optional

class ValidationError(Exception):
    """Raised when data validation fails."""
    pass

def validate_transaction_data(df: pd.DataFrame) -> List[str]:
    """
    Validate extracted transaction data.

    Args:
        df: DataFrame with transaction data

    Returns:
        List of validation warnings (empty if all good)

    Raises:
        ValidationError: If data is critically invalid
    """
    warnings = []

    # Check required columns
    required_cols = ['DATA MOV.', 'VALUTA', 'DARE', 'AVERE', 'DESCRIZIONE OPERAZIONE']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        raise ValidationError(f"Missing required columns: {missing_cols}")

    # Check data quality
    if len(df) == 0:
        raise ValidationError("No transactions found")

    # Check date column has dates
    try:
        pd.to_datetime(df['DATA MOV.'], format='%d/%m/%Y', errors='coerce')
    except:
        warnings.append("Date column (DATA MOV.) may contain invalid dates")

    # Check amount columns
    if df['DARE'].isna().all() and df['AVERE'].isna().all():
        warnings.append("Both DARE and AVERE columns are empty")

    # Check description column
    if df['DESCRIZIONE OPERAZIONE'].isna().all():
        warnings.append("Description column is empty")

    # Check for suspicious patterns
    if len(df) < 3:
        warnings.append(f"Very few transactions found: {len(df)}")

    return warnings

def validate_enriched_data(df: pd.DataFrame) -> List[str]:
    """
    Validate enriched transaction data.

    Args:
        df: Enriched DataFrame

    Returns:
        List of validation warnings
    """
    warnings = []

    # Check enrichment columns exist
    enrichment_cols = ['payer', 'payee', 'is_bill', 'is_incoming_transfer',
                      'is_outcoming_transfer', 'is_bank_fee', 'amount']
    missing_cols = [col for col in enrichment_cols if col not in df.columns]

    if missing_cols:
        warnings.append(f"Missing enrichment columns: {missing_cols}")

    # Check if enrichment actually worked
    if 'payer' in df.columns and df['payer'].notna().sum() == 0:
        warnings.append("No payers extracted - check regex patterns")

    if 'payee' in df.columns and df['payee'].notna().sum() == 0:
        warnings.append("No payees extracted - check regex patterns")

    return warnings
```

Use validation in converter:

```python
from estrattoconto.validation import validate_transaction_data, validate_enriched_data

def extract_table(pdf_path: str) -> tuple:
    # ... existing code ...

    # Validate extracted data
    try:
        warnings = validate_transaction_data(transactions)
        for warning in warnings:
            import warnings as warn_module
            warn_module.warn(warning)
    except ValidationError as e:
        raise ValueError(f"Extracted data validation failed: {e}")

    return book_balance, account_info, balance_summary, transactions

def enrich_data(tables: tuple) -> pd.DataFrame:
    # ... existing code ...

    # Validate enriched data
    warnings = validate_enriched_data(enriched_table)
    for warning in warnings:
        import warnings as warn_module
        warn_module.warn(warning)

    return enriched_table
```

### Testing

```python
# tests/test_validation.py (new file)
import unittest
from estrattoconto.validation import validate_transaction_data, ValidationError

class TestValidation(unittest.TestCase):
    def test_validate_missing_columns(self):
        df = pd.DataFrame({'wrong': [1, 2, 3]})
        with self.assertRaises(ValidationError):
            validate_transaction_data(df)

    def test_validate_empty_dataframe(self):
        df = pd.DataFrame(columns=['DATA MOV.', 'VALUTA', 'DARE', 'AVERE', 'DESCRIZIONE OPERAZIONE'])
        with self.assertRaises(ValidationError):
            validate_transaction_data(df)

    def test_validate_warnings(self):
        df = pd.DataFrame({
            'DATA MOV.': ['01/01/2025'],
            'VALUTA': ['01/01/2025'],
            'DARE': [None],
            'AVERE': [None],
            'DESCRIZIONE OPERAZIONE': ['Test']
        })
        warnings = validate_transaction_data(df)
        self.assertIn("Both DARE and AVERE columns are empty", warnings)
```

### Acceptance Criteria
- [ ] validation.py module created
- [ ] Validation functions implemented
- [ ] Integrated into extraction pipeline
- [ ] Tests added
- [ ] Warnings displayed to users
- [ ] Critical issues raise exceptions

---

## Summary Checklist

Phase 1 is complete when:

- [ ] All bugs fixed and tested
- [ ] All dependencies declared in pyproject.toml
- [ ] CLI entry point configured
- [ ] Error handling comprehensive
- [ ] Input validation implemented
- [ ] All tests passing
- [ ] Code coverage maintained or improved
- [ ] Documentation updated

---

## Commands for Testing

```bash
# Install fresh environment
poetry env remove python
poetry install

# Run all tests
poetry run pytest -v

# Run specific tests
poetry run pytest tests/test_converter.py -v
poetry run pytest tests/test_enrichment.py -v

# Check coverage
poetry run pytest --cov=estrattoconto --cov-report=html

# Lint
poetry run pylint estrattoconto

# Type check
poetry run mypy estrattoconto

# Test CLI
poetry run estrattoconto --help
poetry run estrattoconto extract tests/fixture/sample.pdf
```

---

**Next Phase:** [Phase 2: Multi-Provider Architecture](phase-2-providers.md)
