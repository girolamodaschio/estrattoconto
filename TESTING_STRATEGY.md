# Testing Strategy for Multi-Bank Integration

## 🎯 Overview

This document outlines the comprehensive testing strategy for the multi-bank integration feature. It covers unit tests, integration tests, mock data generation, and validation approaches.

---

## 🧪 Testing Philosophy

### Core Principles

1. **Test at Multiple Levels**: Unit, integration, and end-to-end tests
2. **Mock-First Development**: Use generated mocks before real PDFs
3. **Isolation**: Each provider tested independently
4. **Automation**: All tests runnable in CI/CD
5. **No Sensitive Data**: Use mocks for automated testing

### Testing Pyramid

```
                    ┌──────────────────┐
                    │   E2E Tests      │  ← Real PDFs (manual)
                    │   ~5 tests       │     Gitignored
                    └──────────────────┘
                ┌──────────────────────────┐
                │  Integration Tests       │  ← Mock PDFs (automated)
                │  ~20 tests               │     Committed to repo
                └──────────────────────────┘
            ┌──────────────────────────────────┐
            │   Unit Tests                     │  ← Pure Python (automated)
            │   ~100 tests                     │     Fast, isolated
            └──────────────────────────────────┘
```

---

## 🏗️ Test Structure

### Directory Layout

```
tests/
├── fixtures/                          # Test data
│   ├── mock_pdfs/                    # Generated mock PDFs (committed)
│   │   ├── centroveneto_30txn.pdf
│   │   ├── intesa_50txn.pdf
│   │   └── unicredit_20txn.pdf
│   ├── real_pdfs/                    # Real PDFs (gitignored)
│   │   ├── .gitignore
│   │   └── README.md (instructions)
│   └── expected_outputs/             # Known-good outputs for comparison
│       ├── centroveneto_expected.csv
│       └── intesa_expected.csv
│
├── mock_generators/                  # Mock data generation
│   ├── __init__.py
│   ├── advanced_mock.py             # Transaction data generator
│   ├── pdf_generator.py             # PDF creation
│   └── test_generators.py           # Test the generators themselves
│
├── unit/                             # Fast, isolated tests
│   ├── __init__.py
│   ├── test_provider_base.py       # Abstract base class tests
│   ├── test_registry.py            # ProviderRegistry tests
│   ├── test_centroveneto.py        # CENTROVENETO provider tests
│   ├── test_intesa.py              # Intesa provider tests
│   ├── test_mock_provider.py       # Mock provider tests
│   ├── test_enrichment.py          # Enrichment logic tests
│   └── test_utils.py               # Utility functions tests
│
├── integration/                      # Multi-component tests
│   ├── __init__.py
│   ├── test_mock_pdf_parsing.py    # Parse generated mock PDFs
│   ├── test_provider_detection.py  # Test auto-detection
│   ├── test_full_pipeline.py       # End-to-end with mocks
│   └── test_backward_compat.py     # Ensure existing API works
│
├── e2e/                              # Real PDF tests (manual/optional)
│   ├── __init__.py
│   ├── test_real_centroveneto.py   # Real CENTROVENETO PDFs
│   ├── test_real_intesa.py         # Real Intesa PDFs
│   └── README.md                    # Instructions for running
│
├── conftest.py                       # Pytest fixtures
└── test_config.py                    # Test configuration
```

---

## 📝 Test Categories

### 1. Unit Tests (Fast, Isolated)

**Purpose**: Test individual components in isolation
**Run Frequency**: Every commit (pre-commit hook)
**Duration**: <5 seconds

#### 1.1 Provider Base Tests

**File**: `tests/unit/test_provider_base.py`

```python
"""Test BankProvider abstract base class and data models"""
import pytest
from estrattoconto.providers.base import BankProvider, BankTables, EnrichmentPatterns
import pandas as pd

def test_bank_tables_dataclass():
    """Test BankTables dataclass creation"""
    tables = BankTables(
        book_balance=pd.DataFrame({'col': [1]}),
        account_information=pd.DataFrame({'col': [2]}),
        balance_summary=pd.DataFrame({'col': [3]}),
        transactions=pd.DataFrame({'col': [4]})
    )
    assert isinstance(tables.book_balance, pd.DataFrame)
    assert len(tables.transactions) == 1

def test_enrichment_patterns_dataclass():
    """Test EnrichmentPatterns with optional patterns"""
    import re
    patterns = EnrichmentPatterns(
        payer_pattern=re.compile(r'Payer:\s*(\w+)'),
        bill_pattern=re.compile(r'BILL')
    )
    assert patterns.payer_pattern is not None
    assert patterns.payee_pattern is None  # Optional

def test_bank_provider_is_abstract():
    """Test that BankProvider cannot be instantiated directly"""
    with pytest.raises(TypeError):
        BankProvider()

def test_bank_provider_requires_all_methods():
    """Test that concrete provider must implement all abstract methods"""
    class IncompleteProvider(BankProvider):
        @property
        def name(self):
            return "TEST"

    with pytest.raises(TypeError):
        IncompleteProvider()
```

#### 1.2 Registry Tests

**File**: `tests/unit/test_registry.py`

```python
"""Test ProviderRegistry factory and registration"""
import pytest
from estrattoconto.providers import ProviderRegistry, BankProvider
from estrattoconto.providers.mock import MockBankProvider

def test_register_provider():
    """Test provider registration"""
    initial_count = len(ProviderRegistry.list_providers())

    # Create a test provider
    class TestProvider(BankProvider):
        @property
        def name(self):
            return "TESTBANK"

        @property
        def display_name(self):
            return "Test Bank"

        def detect(self, docling_doc):
            return False

        def extract_tables(self, docling_doc):
            pass

        def get_enrichment_patterns(self):
            pass

        def get_column_mapping(self):
            return {}

    ProviderRegistry.register(TestProvider)
    assert len(ProviderRegistry.list_providers()) == initial_count + 1
    assert "TESTBANK" in ProviderRegistry.list_providers()

def test_get_provider_by_name():
    """Test retrieving provider by name"""
    ProviderRegistry.register(MockBankProvider)
    provider = ProviderRegistry.get_provider("MOCKBANK")
    assert provider is not None
    assert provider.name == "MOCKBANK"

def test_get_nonexistent_provider():
    """Test retrieving non-existent provider returns None"""
    provider = ProviderRegistry.get_provider("NONEXISTENT")
    assert provider is None

def test_detect_provider_returns_none_for_unknown():
    """Test detection returns None for unsupported documents"""
    # Create a mock docling document with no matching text
    class MockDoc:
        texts = [type('obj', (object,), {'text': 'UNKNOWN BANK'})]

    provider = ProviderRegistry.detect_provider(MockDoc())
    assert provider is None
```

#### 1.3 Provider-Specific Tests

**File**: `tests/unit/test_centroveneto.py`

```python
"""Test CentroVenetoProvider implementation"""
import pytest
import re
from estrattoconto.providers.centroveneto import CentroVenetoProvider

@pytest.fixture
def provider():
    return CentroVenetoProvider()

def test_centroveneto_name(provider):
    """Test provider name"""
    assert provider.name == "CENTROVENETO"
    assert provider.display_name == "Banca del Veneto Centrale"

def test_centroveneto_detection_positive(provider):
    """Test detection with CENTROVENETO document"""
    class MockDoc:
        texts = [
            type('obj', (object,), {'text': 'Some header text'}),
            type('obj', (object,), {'text': 'BANCA VENETO CENTRALE'}),
            type('obj', (object,), {'text': 'More content'}),
        ]

    assert provider.detect(MockDoc()) is True

def test_centroveneto_detection_negative(provider):
    """Test detection with non-CENTROVENETO document"""
    class MockDoc:
        texts = [
            type('obj', (object,), {'text': 'INTESA SANPAOLO'}),
            type('obj', (object,), {'text': 'Some other bank'}),
        ]

    assert provider.detect(MockDoc()) is False

def test_centroveneto_detection_case_insensitive(provider):
    """Test detection is case insensitive"""
    class MockDoc:
        texts = [
            type('obj', (object,), {'text': 'banca veneto centrale'}),
        ]

    assert provider.detect(MockDoc()) is True

def test_centroveneto_enrichment_patterns(provider):
    """Test regex patterns for entity extraction"""
    patterns = provider.get_enrichment_patterns()

    # Test payer pattern
    text = "BONIFICO Ordinante: MARIO ROSSI Causale: Payment"
    match = patterns.payer_pattern.search(text)
    assert match is not None
    assert match.group(1) == "MARIO ROSSI"

    # Test payee pattern
    text = "ADDEBITO CRED. ENEL ENERGIA SPA ID.MANDATO IT12345"
    match = patterns.payee_pattern.search(text)
    assert match is not None
    assert "ENEL ENERGIA SPA" in match.group(1)

    # Test mandate ID pattern
    text = "ID.MANDATO IT12345 RIF. 202501"
    match = patterns.mandate_id_pattern.search(text)
    assert match is not None
    assert "IT12345" in match.group(1)

def test_centroveneto_column_mapping(provider):
    """Test column name mapping"""
    mapping = provider.get_column_mapping()

    assert mapping['movement_date'] == 'DATA MOV.'
    assert mapping['value_date'] == 'VALUTA'
    assert mapping['debit'] == 'DARE'
    assert mapping['credit'] == 'AVERE'
    assert mapping['description'] == 'DESCRIZIONE OPERAZIONE'

def test_centroveneto_bill_detection(provider):
    """Test bill detection pattern"""
    patterns = provider.get_enrichment_patterns()

    assert patterns.bill_pattern.search("S.D.D. ADDEBITO") is not None
    assert patterns.bill_pattern.search("s.d.d. transaction") is not None
    assert patterns.bill_pattern.search("Regular transfer") is None

def test_centroveneto_transfer_detection(provider):
    """Test transfer detection patterns"""
    patterns = provider.get_enrichment_patterns()

    # Incoming transfer
    assert patterns.incoming_transfer_pattern.search("BONIFICO A VS. FAVORE") is not None

    # Outgoing transfer
    assert patterns.outgoing_transfer_pattern.search("BONIFICO coordinate benef") is not None

    # Not a transfer
    assert patterns.incoming_transfer_pattern.search("Regular payment") is None

def test_centroveneto_fee_detection(provider):
    """Test bank fee detection"""
    patterns = provider.get_enrichment_patterns()

    assert patterns.bank_fee_pattern.search("CANONE MENSILE") is not None
    assert patterns.bank_fee_pattern.search("COMMISSIONI GESTIONE") is not None
    assert patterns.bank_fee_pattern.search("Regular transaction") is None
```

#### 1.4 Enrichment Tests

**File**: `tests/unit/test_enrichment.py`

```python
"""Test data enrichment logic"""
import pytest
import pandas as pd
from estrattoconto.enrichment import enrich_data, postprocess_extraction
from estrattoconto.providers.centroveneto import CentroVenetoProvider

@pytest.fixture
def provider():
    return CentroVenetoProvider()

@pytest.fixture
def sample_transactions():
    return pd.DataFrame({
        'DATA MOV.': ['01/01/2025', '02/01/2025'],
        'VALUTA': ['01/01/2025', '02/01/2025'],
        'DARE': ['- 50,00 €', ''],
        'AVERE': ['', '+ 100,00 €'],
        'DESCRIZIONE OPERAZIONE': [
            'S.D.D. ADDEBITO CRED. ENEL SPA ID.MANDATO IT123 RIF. 2025',
            'BONIFICO A VS. FAVORE Ordinante: MARIO ROSSI Causale: Payment'
        ]
    })

def test_postprocess_extraction(provider, sample_transactions):
    """Test column selection and cleaning"""
    result = postprocess_extraction(sample_transactions, provider)

    # Should have same columns
    expected_cols = ['DATA MOV.', 'VALUTA', 'DARE', 'AVERE', 'DESCRIZIONE OPERAZIONE']
    assert list(result.columns) == expected_cols

    # Should remove NaN rows if any
    assert len(result) <= len(sample_transactions)

def test_currency_conversion(provider, sample_transactions):
    """Test Italian currency format conversion"""
    book_balance = pd.DataFrame({'Period': ['01/01/2025 - 31/01/2025']})
    account_info = pd.DataFrame({'IBAN': ['IT123']})
    balance_summary = pd.DataFrame({'Balance': ['+ 1.000,00 €']})

    extracted_data = (book_balance, account_info, balance_summary, sample_transactions)
    result = enrich_data(extracted_data, provider)

    # Check numeric columns created
    assert 'DARE_Numeric' in result.columns
    assert 'AVERE_Numeric' in result.columns
    assert 'amount' in result.columns

    # Check values
    assert result.iloc[0]['DARE_Numeric'] == pytest.approx(50.0)
    assert result.iloc[1]['AVERE_Numeric'] == pytest.approx(100.0)

def test_entity_extraction(provider, sample_transactions):
    """Test payer/payee extraction"""
    book_balance = pd.DataFrame({'Period': ['01/01/2025 - 31/01/2025']})
    account_info = pd.DataFrame({'IBAN': ['IT123']})
    balance_summary = pd.DataFrame({'Balance': ['+ 1.000,00 €']})

    extracted_data = (book_balance, account_info, balance_summary, sample_transactions)
    result = enrich_data(extracted_data, provider)

    # Check entities extracted
    assert 'payer' in result.columns
    assert 'payee' in result.columns
    assert 'id_mandato' in result.columns

    # Check values
    assert result.iloc[1]['payer'] == 'MARIO ROSSI'
    assert 'ENEL' in str(result.iloc[0]['payee'])
    assert 'IT123' in str(result.iloc[0]['id_mandato'])

def test_transaction_classification(provider, sample_transactions):
    """Test transaction type classification"""
    book_balance = pd.DataFrame({'Period': ['01/01/2025 - 31/01/2025']})
    account_info = pd.DataFrame({'IBAN': ['IT123']})
    balance_summary = pd.DataFrame({'Balance': ['+ 1.000,00 €']})

    extracted_data = (book_balance, account_info, balance_summary, sample_transactions)
    result = enrich_data(extracted_data, provider)

    # Check classification flags
    assert 'is_bill' in result.columns
    assert 'is_incoming_transfer' in result.columns
    assert 'is_outcoming_transfer' in result.columns
    assert 'is_bank_fee' in result.columns

    # Check values
    assert result.iloc[0]['is_bill'] is True
    assert result.iloc[1]['is_incoming_transfer'] is True

def test_metadata_addition(provider, sample_transactions):
    """Test account and period metadata"""
    book_balance = pd.DataFrame({'Period': ['01/01/2025 - 31/01/2025']})
    account_info = pd.DataFrame({'IBAN': ['IT60X0542811101000000123456']})
    balance_summary = pd.DataFrame({'Balance': ['+ 1.000,00 €']})

    extracted_data = (book_balance, account_info, balance_summary, sample_transactions)
    result = enrich_data(extracted_data, provider)

    # Check metadata columns
    assert 'related_account' in result.columns
    assert 'period' in result.columns

    # Check values
    assert result['related_account'].iloc[0] == 'IT60X0542811101000000123456'
    assert result['period'].iloc[0] == '01/01/2025 - 31/01/2025'
```

---

### 2. Integration Tests (Mock PDFs)

**Purpose**: Test full pipeline with generated mock PDFs
**Run Frequency**: Every push (CI/CD)
**Duration**: 10-30 seconds

#### 2.1 Mock PDF Parsing Tests

**File**: `tests/integration/test_mock_pdf_parsing.py`

```python
"""Test parsing of generated mock PDFs"""
import pytest
from pathlib import Path
from estrattoconto import convert
from estrattoconto.providers import ProviderRegistry

# Mock PDFs should be pre-generated and committed
MOCK_PDF_DIR = Path(__file__).parent.parent / 'fixtures' / 'mock_pdfs'

def test_parse_mock_centroveneto():
    """Test parsing mock CENTROVENETO PDF"""
    pdf_path = MOCK_PDF_DIR / 'centroveneto_30txn.pdf'

    # Skip if mock not generated yet
    if not pdf_path.exists():
        pytest.skip(f"Mock PDF not found: {pdf_path}")

    statement = convert(str(pdf_path))

    # Verify detection
    assert statement.provider_name == "CENTROVENETO"
    assert statement.provider_display_name == "Banca del Veneto Centrale"

    # Verify transaction count
    assert len(statement) == 30  # Known from generation

    # Verify columns exist
    df = statement.get_dataframe()
    expected_cols = ['DATA MOV.', 'VALUTA', 'DARE', 'AVERE', 'DESCRIZIONE OPERAZIONE']
    for col in expected_cols:
        assert col in df.columns

    # Verify enrichment
    assert 'amount' in df.columns
    assert 'is_bill' in df.columns

def test_parse_mock_intesa():
    """Test parsing mock INTESA PDF"""
    pdf_path = MOCK_PDF_DIR / 'intesa_50txn.pdf'

    if not pdf_path.exists():
        pytest.skip(f"Mock PDF not found: {pdf_path}")

    statement = convert(str(pdf_path))
    assert statement.provider_name == "INTESA"
    assert len(statement) == 50

def test_mock_pdf_export_csv():
    """Test exporting mock PDF to CSV"""
    pdf_path = MOCK_PDF_DIR / 'centroveneto_30txn.pdf'

    if not pdf_path.exists():
        pytest.skip(f"Mock PDF not found: {pdf_path}")

    statement = convert(str(pdf_path))

    # Export to temp CSV
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        csv_path = f.name

    statement.to_csv(csv_path)

    # Verify CSV created and readable
    import pandas as pd
    df = pd.read_csv(csv_path)
    assert len(df) == 30

    # Cleanup
    Path(csv_path).unlink()

def test_mock_pdf_filtering():
    """Test filtering methods with mock PDF"""
    pdf_path = MOCK_PDF_DIR / 'centroveneto_30txn.pdf'

    if not pdf_path.exists():
        pytest.skip(f"Mock PDF not found: {pdf_path}")

    statement = convert(str(pdf_path))

    # Test filtering
    bills = statement.get_bills()
    incoming = statement.get_incoming_transfers()
    outgoing = statement.get_outgoing_transfers()
    fees = statement.get_fees()

    # Verify filtering returns subsets
    assert len(bills) <= len(statement)
    assert len(incoming) <= len(statement)
    assert len(outgoing) <= len(statement)
    assert len(fees) <= len(statement)
```

#### 2.2 Provider Detection Tests

**File**: `tests/integration/test_provider_detection.py`

```python
"""Test automatic provider detection"""
import pytest
from pathlib import Path
from docling.document_converter import DocumentConverter
from estrattoconto.providers import ProviderRegistry
from estrattoconto import convert

MOCK_PDF_DIR = Path(__file__).parent.parent / 'fixtures' / 'mock_pdfs'

def test_auto_detect_centroveneto():
    """Test automatic detection of CENTROVENETO"""
    pdf_path = MOCK_PDF_DIR / 'centroveneto_30txn.pdf'

    if not pdf_path.exists():
        pytest.skip(f"Mock PDF not found: {pdf_path}")

    converter = DocumentConverter()
    result = converter.convert(str(pdf_path))

    provider = ProviderRegistry.detect_provider(result.document)
    assert provider is not None
    assert provider.name == "CENTROVENETO"

def test_auto_detect_intesa():
    """Test automatic detection of INTESA"""
    pdf_path = MOCK_PDF_DIR / 'intesa_50txn.pdf'

    if not pdf_path.exists():
        pytest.skip(f"Mock PDF not found: {pdf_path}")

    converter = DocumentConverter()
    result = converter.convert(str(pdf_path))

    provider = ProviderRegistry.detect_provider(result.document)
    assert provider is not None
    assert provider.name == "INTESA"

def test_detect_unsupported_bank():
    """Test detection of unsupported bank returns None"""
    # This would require a mock PDF from an unsupported bank
    # For now, we'll test with a text-only PDF
    pass  # TODO: Create unsupported bank mock
```

---

### 3. End-to-End Tests (Real PDFs)

**Purpose**: Validate with real bank statement PDFs
**Run Frequency**: Manual (optional, requires real PDFs)
**Duration**: Variable

#### 3.1 Real PDF Tests

**File**: `tests/e2e/test_real_centroveneto.py`

```python
"""
Test with real CENTROVENETO PDFs.

NOTE: Real PDFs must be placed in tests/fixtures/real_pdfs/
These files are gitignored for security.
"""
import pytest
from pathlib import Path
from estrattoconto import convert

REAL_PDF_DIR = Path(__file__).parent.parent / 'fixtures' / 'real_pdfs'

@pytest.mark.skipif(
    not (REAL_PDF_DIR / 'centroveneto.pdf').exists(),
    reason="Real PDF not available (gitignored)"
)
def test_real_centroveneto_pdf():
    """Test parsing real CENTROVENETO PDF"""
    pdf_path = REAL_PDF_DIR / 'centroveneto.pdf'

    statement = convert(str(pdf_path))

    # Verify detection
    assert statement.provider_name == "CENTROVENETO"

    # Verify data structure
    df = statement.get_dataframe()
    assert len(df) > 0
    assert 'DATA MOV.' in df.columns
    assert 'amount' in df.columns

    # Print summary for manual verification
    print("\nReal PDF Summary:")
    print(statement.summary())
```

**File**: `tests/fixtures/real_pdfs/README.md`

```markdown
# Real Bank Statement PDFs

Place real (anonymized) bank statement PDFs here for end-to-end testing.

## Security Note

**IMPORTANT**: This directory is gitignored. Never commit real bank statements
with sensitive customer information.

## File Naming Convention

- `centroveneto.pdf` - CENTROVENETO sample
- `intesa.pdf` - Intesa SanPaolo sample
- `unicredit.pdf` - UniCredit sample

## Anonymization Checklist

Before placing a PDF here, ensure:
- [ ] All account numbers replaced/removed
- [ ] All personal names replaced with "MARIO ROSSI" etc.
- [ ] All addresses removed
- [ ] All phone numbers removed
- [ ] Keep transaction descriptions (non-personal)
- [ ] Keep bank name (for detection)
- [ ] Keep table structure (for parsing)

## Running E2E Tests

```bash
# Run only if real PDFs are available
pytest tests/e2e/ -v

# Skip E2E tests (default in CI)
pytest -m "not e2e"
```
\`\`\`

---

### 4. Mock Generator Tests

**Purpose**: Test the mock generation tools themselves
**Run Frequency**: Every commit
**Duration**: <5 seconds

**File**: `tests/mock_generators/test_generators.py`

```python
"""Test mock data generators"""
import pytest
from datetime import datetime
from tests.mock_generators.advanced_mock import BankStatementMockGenerator

def test_mock_generator_creates_data():
    """Test basic mock generation"""
    gen = BankStatementMockGenerator(locale='it_IT')

    df, opening, closing = gen.generate_transactions(
        num_transactions=10,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31)
    )

    # Verify transaction count
    assert len(df) == 10

    # Verify columns
    expected_cols = ['DATA MOV.', 'VALUTA', 'DARE', 'AVERE', 'DESCRIZIONE OPERAZIONE']
    for col in expected_cols:
        assert col in df.columns

    # Verify balances are numeric
    assert isinstance(opening, (int, float))
    assert isinstance(closing, (int, float))

def test_mock_generator_date_range():
    """Test transactions are within date range"""
    gen = BankStatementMockGenerator()

    start = datetime(2025, 1, 1)
    end = datetime(2025, 1, 31)

    df, _, _ = gen.generate_transactions(
        num_transactions=20,
        start_date=start,
        end_date=end
    )

    # Parse dates and verify range
    dates = pd.to_datetime(df['DATA MOV.'], format='%d/%m/%Y')
    assert dates.min() >= pd.Timestamp(start)
    assert dates.max() <= pd.Timestamp(end)

def test_mock_generator_realistic_amounts():
    """Test amounts are realistic"""
    gen = BankStatementMockGenerator()

    df, _, _ = gen.generate_transactions(num_transactions=50)

    # Check DARE and AVERE formats
    dare_values = df['DARE'][df['DARE'] != '']
    avere_values = df['AVERE'][df['AVERE'] != '']

    for val in dare_values:
        assert '€' in val
        assert '-' in val or '+' in val

    for val in avere_values:
        assert '€' in val
        assert '+' in val

def test_mock_generator_italian_names():
    """Test uses Italian locale for names"""
    gen = BankStatementMockGenerator(locale='it_IT')

    df, _, _ = gen.generate_transactions(num_transactions=20)

    # Check for Italian naming patterns in descriptions
    descriptions = df['DESCRIZIONE OPERAZIONE'].tolist()

    # Should have at least some transactions with names
    has_names = any('Ordinante:' in d or 'benef' in d for d in descriptions)
    assert has_names
```

---

## 🔄 Test Execution Workflow

### Local Development

```bash
# 1. Run fast unit tests during development
pytest tests/unit/ -v

# 2. Run integration tests before commit
pytest tests/integration/ -v

# 3. Generate coverage report
pytest --cov=estrattoconto --cov-report=html
open htmlcov/index.html

# 4. Run specific test file
pytest tests/unit/test_centroveneto.py -v

# 5. Run tests matching pattern
pytest -k "test_enrichment" -v
```

### Pre-Commit (Git Hook)

```bash
# .git/hooks/pre-commit
#!/bin/bash
set -e

echo "Running tests..."
pytest tests/unit/ tests/mock_generators/ -q

echo "Running linter..."
ruff check estrattoconto/

echo "Running formatter check..."
black --check estrattoconto/

echo "✅ All checks passed"
```

### CI/CD Pipeline (.github/workflows/test.yml)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install --with dev

      - name: Generate mock PDFs
        run: |
          poetry run python tests/mock_generators/generate_all.py

      - name: Run unit tests
        run: |
          poetry run pytest tests/unit/ -v --cov=estrattoconto

      - name: Run integration tests
        run: |
          poetry run pytest tests/integration/ -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 📊 Coverage Goals

### Target Coverage

- **Overall**: >90%
- **Core modules**: >95%
  - `providers/base.py`: 100%
  - `providers/registry.py`: 100%
  - `enrichment.py`: >95%
- **Providers**: >85%
  - Each provider: >85%
- **Utils**: >90%

### Coverage Monitoring

```bash
# Generate coverage report
pytest --cov=estrattoconto --cov-report=html --cov-report=term

# Check coverage threshold
pytest --cov=estrattoconto --cov-fail-under=90
```

---

## 🎯 Testing Checklist

### For Each New Bank Provider

- [ ] Unit tests for provider class
  - [ ] Test `detect()` with positive cases
  - [ ] Test `detect()` with negative cases
  - [ ] Test `extract_tables()` structure
  - [ ] Test `get_enrichment_patterns()` regex
  - [ ] Test `get_column_mapping()` completeness
- [ ] Integration tests
  - [ ] Generate mock PDF
  - [ ] Test full parsing pipeline
  - [ ] Test export to CSV/JSON/Excel
  - [ ] Test filtering methods
- [ ] E2E tests (optional)
  - [ ] Test with real anonymized PDF
  - [ ] Verify output against known results
- [ ] Documentation
  - [ ] Provider README with examples
  - [ ] Update SUPPORTED_BANKS.md

---

## 🚨 Common Test Scenarios

### Scenario 1: Empty Transaction Description

```python
def test_empty_description_handling():
    """Test handling of transactions with empty descriptions"""
    df = pd.DataFrame({
        'DESCRIZIONE OPERAZIONE': ['', None, 'Valid description']
    })
    # Should not crash, should handle gracefully
```

### Scenario 2: Malformed Currency

```python
def test_malformed_currency_handling():
    """Test handling of malformed currency strings"""
    from estrattoconto.utils import clean_and_convert_currency

    series = pd.Series(['123', 'invalid', '+ 1.000,00 €', ''])
    result = clean_and_convert_currency(series)

    # Should convert valid, return NaN for invalid
    assert not result.isna().all()
```

### Scenario 3: Missing Tables

```python
def test_missing_tables_error():
    """Test error when PDF has insufficient tables"""
    # Mock document with only 1 table
    with pytest.raises(ValueError, match="Expected at least 2 tables"):
        provider.extract_tables(mock_doc_with_one_table)
```

---

## 📝 Test Data Management

### Mock PDF Generation Script

**File**: `tests/mock_generators/generate_all.py`

```python
"""
Generate all mock PDFs for testing.
Run this to create fixtures before running integration tests.
"""
from datetime import datetime
from pathlib import Path
from advanced_mock import BankStatementMockGenerator
from pdf_generator import DoclingCompatiblePDFGenerator

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'mock_pdfs'
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

def generate_centroveneto_mock():
    """Generate CENTROVENETO mock with 30 transactions"""
    print("Generating CENTROVENETO mock (30 txn)...")

    gen = BankStatementMockGenerator(locale='it_IT')
    df, opening, closing = gen.generate_transactions(
        num_transactions=30,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31)
    )

    pdf_gen = DoclingCompatiblePDFGenerator(
        bank_name='CENTROVENETO',
        bank_logo_text='BANCA VENETO CENTRALE'
    )

    pdf_gen.generate_statement(
        output_path=str(FIXTURES_DIR / 'centroveneto_30txn.pdf'),
        account_info={'IBAN': 'IT60X0542811101000000123456'},
        transactions=df,
        period='01/01/2025 - 31/01/2025',
        opening_balance=gen._format_amount(opening),
        closing_balance=gen._format_amount(closing)
    )
    print("✓ Generated centroveneto_30txn.pdf")

def generate_intesa_mock():
    """Generate INTESA mock with 50 transactions"""
    print("Generating INTESA mock (50 txn)...")
    # Similar to above
    print("✓ Generated intesa_50txn.pdf")

if __name__ == '__main__':
    generate_centroveneto_mock()
    # generate_intesa_mock()  # Uncomment when Intesa provider ready
    print("\n✅ All mock PDFs generated successfully")
```

---

## ✅ Success Metrics

### Definition of Done (for testing)

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Coverage >90%
- [ ] Mock PDFs generated and committed
- [ ] Real PDF tests documented (optional)
- [ ] CI/CD pipeline green
- [ ] No regressions in existing functionality

---

## 📚 Testing Tools & Dependencies

```toml
[tool.poetry.dev-dependencies]
# Testing
pytest = "^8.0.0"
pytest-cov = "^5.0.0"
pytest-mock = "^3.12.0"

# Mock generation
reportlab = "^4.0.0"
faker = "^20.0.0"

# Code quality
black = "^24.0.0"
ruff = "^0.4.0"
mypy = "^1.9.0"
```

---

**Document Version**: 1.0
**Created**: 2026-01-18
**Status**: Complete ✅
