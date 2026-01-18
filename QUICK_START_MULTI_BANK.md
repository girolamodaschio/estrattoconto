# Quick Start: Multi-Bank Integration

## 🎯 Executive Summary

Transform `estrattoconto` from a single-bank tool (CENTROVENETO) into a multi-provider platform supporting all major Italian banks through a clean provider pattern architecture.

**Timeline**: 4-5 weeks | **Impact**: Universal Italian bank statement processing

---

## 📊 Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                    estrattoconto Public API                      │
│                                                                  │
│  EstrattoConto.from_pdf('statement.pdf')                        │
│       ↓                                                          │
│  Auto-detects bank via ProviderRegistry                         │
│       ↓                                                          │
│  ┌──────────────────────────────────────────────┐              │
│  │        BankProvider (Abstract)                │              │
│  │  - detect(doc) → bool                        │              │
│  │  - extract_tables(doc) → BankTables          │              │
│  │  - get_enrichment_patterns() → Patterns      │              │
│  │  - get_column_mapping() → Dict               │              │
│  └──────────────┬───────────────────────────────┘              │
│                 │                                                │
│     ┌───────────┴───────────┬─────────────┬──────────────┐    │
│     ▼                        ▼             ▼              ▼    │
│  CentroVeneto            Intesa      UniCredit        Mock     │
│  Provider                Provider     Provider      Provider   │
│                                                                  │
│  ✅ Done                 🚧 TODO      🚧 TODO        ✅ Done   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
**Goal**: Build provider system without breaking existing code

#### Tasks:
1. ✅ Create `providers/` package structure
2. ✅ Define `BankProvider` abstract base class
3. ✅ Implement `ProviderRegistry` factory
4. ✅ Refactor CENTROVENETO into provider
5. ✅ Update `converter.py` to use providers
6. ✅ Update `enrichment.py` to use provider patterns
7. ✅ Verify backward compatibility

#### Deliverables:
- `estrattoconto/providers/base.py` - Base classes
- `estrattoconto/providers/registry.py` - Factory pattern
- `estrattoconto/providers/centroveneto.py` - Migrated provider
- All existing tests passing

---

### Phase 2: Mock Generation (Week 2)
**Goal**: Create realistic test data using docling-compatible PDFs

#### Tasks:
1. ✅ Install dependencies (reportlab, faker)
2. ✅ Create `MockBankProvider` for generating data
3. ✅ Create `BankStatementMockGenerator` with realistic transactions
4. ✅ Create `DoclingCompatiblePDFGenerator` for PDF creation
5. ✅ Add CLI commands: `estrattoconto mock generate`
6. ✅ Generate test PDFs for each bank

#### Deliverables:
- `estrattoconto/providers/mock.py` - Mock provider
- `tests/mock_generators/advanced_mock.py` - Data generator
- `tests/mock_generators/pdf_generator.py` - PDF generator
- CLI commands for mock generation

#### Usage Example:
```bash
# Generate mock CENTROVENETO statement
estrattoconto mock generate --bank CENTROVENETO -n 50 -o test.pdf

# Test parsing
estrattoconto mock test test.pdf

# Convert to CSV
estrattoconto extract test.pdf --output transactions.csv
```

---

### Phase 3: Real Bank Support (Weeks 3-4)
**Goal**: Add 2+ additional Italian banks

#### Priority Banks:
1. **Intesa SanPaolo** (largest Italian bank)
2. **UniCredit** (major international bank)
3. BancoBPM
4. Poste Italiane
5. Fineco Bank

#### Tasks per Bank:
1. 📄 Collect sample PDF (anonymized)
2. 🔍 Analyze with docling to identify structure
3. 🏗️ Create provider class from template
4. ✍️ Extract regex patterns from descriptions
5. 🧪 Write unit tests
6. 📝 Generate mock PDF
7. ✅ Verify end-to-end parsing

#### Template Workflow:
```bash
# 1. Analyze sample PDF structure
python -c "
from docling.document_converter import DocumentConverter
conv = DocumentConverter()
result = conv.convert('intesa_sample.pdf')
print(f'Tables found: {len(result.document.tables)}')
for i, table in enumerate(result.document.tables):
    df = table.export_to_dataframe()
    print(f'Table {i}: {df.shape} - Columns: {list(df.columns)}')
"

# 2. Copy template
cp estrattoconto/providers/template.py estrattoconto/providers/intesa.py

# 3. Fill in TODOs in intesa.py

# 4. Register provider
# In estrattoconto/providers/__init__.py:
# from .intesa import IntesaProvider
# ProviderRegistry.register(IntesaProvider)

# 5. Test
pytest tests/test_intesa.py
```

---

## 🔍 Key Components

### 1. BankProvider Interface

**Purpose**: Define contract all bank providers must implement

**Methods**:
```python
class BankProvider(ABC):
    @abstractmethod
    def name(self) -> str:
        """Bank code (e.g., 'CENTROVENETO')"""

    @abstractmethod
    def display_name(self) -> str:
        """Human name (e.g., 'Banca del Veneto Centrale')"""

    @abstractmethod
    def detect(self, docling_doc) -> bool:
        """Return True if this provider handles the document"""

    @abstractmethod
    def extract_tables(self, docling_doc) -> BankTables:
        """Extract structured data from PDF"""

    @abstractmethod
    def get_enrichment_patterns(self) -> EnrichmentPatterns:
        """Return regex patterns for entity extraction"""

    @abstractmethod
    def get_column_mapping(self) -> Dict[str, str]:
        """Map bank columns to standard names"""
```

### 2. ProviderRegistry

**Purpose**: Factory pattern for provider detection and instantiation

**Usage**:
```python
from estrattoconto.providers import ProviderRegistry

# Auto-detect provider
provider = ProviderRegistry.detect_provider(docling_doc)

# List all providers
banks = ProviderRegistry.list_providers()
# ['CENTROVENETO', 'INTESA', 'UNICREDIT', 'MOCKBANK']

# Get specific provider
provider = ProviderRegistry.get_provider('INTESA')
```

### 3. Mock Generators

**Purpose**: Create realistic test data without real customer PDFs

**Components**:
- `MockBankProvider`: In-memory data generation
- `BankStatementMockGenerator`: Realistic transaction creation using Faker
- `DoclingCompatiblePDFGenerator`: PDF creation optimized for docling parsing

**Features**:
- ✅ Realistic Italian names (via Faker it_IT locale)
- ✅ Multiple transaction types (bills, transfers, fees, card payments)
- ✅ Proper Italian currency format (1.234,56 €)
- ✅ Docling-compatible table structures
- ✅ Reproducible (seeded random)

---

## 📝 Development Workflow

### Adding a New Bank: Step-by-Step

#### Step 1: Gather Requirements
```bash
# Collect sample PDF (remove sensitive data)
# Preferred: 1-2 pages, 10-20 transactions
```

#### Step 2: Analyze Structure
```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert('bank_sample.pdf')
doc = result.document

# Check detection string
for text in doc.texts:
    print(text.text)

# Analyze tables
for i, table in enumerate(doc.tables):
    df = table.export_to_dataframe()
    print(f"\nTable {i}:")
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {list(df.columns)}")
    print(df.head())
```

#### Step 3: Create Provider
```bash
# Copy template
cp estrattoconto/providers/template.py estrattoconto/providers/bankname.py

# Edit provider file:
# 1. Update class name: BankNameProvider
# 2. Set name property: "BANKNAME"
# 3. Set display_name: "Bank Display Name"
# 4. Update detect() with bank identifier string
# 5. Update extract_tables() with correct table indices
# 6. Create regex patterns for enrichment
# 7. Map column names
```

#### Step 4: Register Provider
```python
# In estrattoconto/providers/__init__.py
from .bankname import BankNameProvider

ProviderRegistry.register(BankNameProvider)

__all__ = [
    # ...
    'BankNameProvider',
]
```

#### Step 5: Write Tests
```python
# tests/test_bankname.py
import pytest
from estrattoconto.providers import BankNameProvider

def test_bankname_detection():
    """Test provider detects bank correctly"""
    provider = BankNameProvider()
    # Load fixture and test detection
    ...

def test_bankname_extraction():
    """Test table extraction"""
    ...

def test_bankname_enrichment():
    """Test pattern matching"""
    ...
```

#### Step 6: Generate Mock
```bash
# Create mock PDF for testing
estrattoconto mock generate --bank BANKNAME -n 30 -o test_bankname.pdf

# Test end-to-end
estrattoconto mock test test_bankname.pdf
```

#### Step 7: Document
```markdown
# Update docs/MULTI_BANK_SUPPORT.md
## Supported Banks
- ✅ Banca del Veneto Centrale (CENTROVENETO)
- ✅ Bank Name (BANKNAME)  # Add new entry
```

---

## 🧪 Testing Strategy

### Test Pyramid

```
            ┌─────────────────┐
            │  E2E Tests      │  ← Real PDFs (gitignored)
            │  (Integration)  │
            └─────────────────┘
           ┌───────────────────┐
           │  Mock PDF Tests   │  ← Generated PDFs
           │  (Functional)     │
           └───────────────────┘
         ┌─────────────────────────┐
         │  Provider Unit Tests    │  ← Isolated components
         │  (Unit)                 │
         └─────────────────────────┘
```

### Test Files

```
tests/
├── test_providers.py           # Provider system tests
├── test_centroveneto.py        # CENTROVENETO-specific
├── test_intesa.py              # Intesa-specific
├── test_mock_generation.py     # Mock generators
└── test_integration.py         # End-to-end with real PDFs
```

### Coverage Goals

- **Unit tests**: >90% coverage
- **Integration tests**: All supported banks
- **Mock tests**: All providers have mock PDFs

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=estrattoconto --cov-report=html

# Specific provider
pytest tests/test_intesa.py -v

# Only unit tests (fast)
pytest tests/test_providers.py tests/test_mock_generation.py

# Only integration tests (requires PDFs)
pytest tests/test_integration.py
```

---

## 🎨 Using Docling for Mockups

### Why Docling for Mocks?

1. **Consistency**: Mock PDFs parsed exactly like real ones
2. **Validation**: Ensures provider logic works before getting real PDFs
3. **CI/CD**: Can test without sensitive data
4. **Documentation**: Provides reference examples

### Mock PDF Best Practices

#### ✅ DO:
- Use clear table borders
- Keep consistent cell padding
- Include bank name in header (for detection)
- Use realistic transaction descriptions
- Follow real bank's table structure
- Generate multiple variations

#### ❌ DON'T:
- Merge cells in data tables
- Use complex layouts
- Include images or logos (text is fine)
- Create PDFs with unusual encodings

### Example: Creating High-Quality Mock

```python
from tests.mock_generators.advanced_mock import BankStatementMockGenerator
from tests.mock_generators.pdf_generator import DoclingCompatiblePDFGenerator
from datetime import datetime

# Generate realistic data
mock_gen = BankStatementMockGenerator(locale='it_IT')
txn_df, opening, closing = mock_gen.generate_transactions(
    num_transactions=50,
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31),
    opening_balance=10000.0
)

# Create docling-optimized PDF
pdf_gen = DoclingCompatiblePDFGenerator(
    bank_name='INTESA',
    bank_logo_text='INTESA SANPAOLO'
)

pdf_gen.generate_statement(
    output_path='test_intesa.pdf',
    account_info={
        'IBAN': 'IT40S0306909606100000012345',
        'Intestatario': 'MARIO ROSSI',
        'Filiale': 'MILANO 001'
    },
    transactions=txn_df,
    period='01/01/2025 - 31/01/2025',
    opening_balance=mock_gen._format_amount(opening),
    closing_balance=mock_gen._format_amount(closing)
)

# Test parsing
from estrattoconto import convert
statement = convert('test_intesa.pdf')
assert statement.provider_name == 'INTESA'
```

---

## 📚 Documentation Deliverables

### User Documentation
- ✅ `MULTI_BANK_STRATEGY.md` - Overall strategy
- ✅ `IMPLEMENTATION_ROADMAP.md` - Detailed implementation guide
- ✅ `QUICK_START_MULTI_BANK.md` - This document
- 🚧 `docs/MULTI_BANK_SUPPORT.md` - User guide for multi-bank features
- 🚧 `docs/SUPPORTED_BANKS.md` - List of supported banks with details

### Developer Documentation
- 🚧 `docs/PROVIDER_DEVELOPMENT.md` - How to add new banks
- 🚧 `docs/MOCK_GENERATION.md` - Mock data generation guide
- 🚧 `docs/API_REFERENCE.md` - Auto-generated API docs

### Migration Guide
- 🚧 `docs/MIGRATION_0.1_TO_0.2.md` - Upgrading guide for users

---

## ✅ Success Criteria

### Phase 1 Complete When:
- [ ] Provider infrastructure works
- [ ] CENTROVENETO migrated
- [ ] All existing tests pass
- [ ] Backward compatibility verified
- [ ] Zero breaking changes to public API

### Phase 2 Complete When:
- [ ] MockBankProvider generates valid data
- [ ] PDF generator creates docling-parseable files
- [ ] CLI commands work: `estrattoconto mock generate`
- [ ] Mock PDFs can be parsed end-to-end

### Phase 3 Complete When:
- [ ] ≥2 additional banks supported (Intesa + UniCredit)
- [ ] Each bank has mock PDF fixture
- [ ] Integration tests pass for all banks
- [ ] Documentation complete
- [ ] Ready for v0.2.0 release

### Release Readiness (v0.2.0):
- [ ] All phases complete
- [ ] Test coverage >90%
- [ ] Documentation complete
- [ ] CHANGELOG.md written
- [ ] Migration guide published
- [ ] Examples updated
- [ ] PyPI package ready

---

## 🚦 Getting Started Right Now

### For Developers:

```bash
# 1. Create feature branch
git checkout -b feature/multi-bank-support

# 2. Create provider package
mkdir -p estrattoconto/providers
touch estrattoconto/providers/__init__.py

# 3. Copy base files from IMPLEMENTATION_ROADMAP.md
# (base.py, registry.py, centroveneto.py)

# 4. Run tests to ensure nothing broke
pytest

# 5. Commit progress
git add .
git commit -m "feat: add provider infrastructure skeleton"
```

### For Project Managers:

1. **Approve strategy** (this document + MULTI_BANK_STRATEGY.md)
2. **Prioritize banks** (which banks to support first?)
3. **Gather PDFs** (anonymized samples from priority banks)
4. **Allocate resources** (4-5 weeks development time)
5. **Review timeline** (adjust based on team capacity)

### For QA/Testing:

1. **Review test strategy** (Testing Strategy section)
2. **Prepare test data** (collect diverse statement samples)
3. **Plan acceptance tests** (define success criteria per bank)
4. **Set up CI/CD** (automated testing with mock PDFs)

---

## 💡 Design Principles

1. **Backward Compatibility**: Existing code must not break
2. **Open/Closed**: Easy to add banks, hard to break existing ones
3. **Testability**: Mock generation for testing without real data
4. **Documentation**: Each bank has clear provider guide
5. **User Experience**: Automatic detection, no manual configuration

---

## 📞 Next Steps & Questions

### Immediate Actions:
1. ✅ Review and approve this strategy
2. ⏳ Choose which banks to support first
3. ⏳ Collect sample PDFs (anonymized)
4. ⏳ Start Phase 1 implementation

### Open Questions:
1. **Priority Banks**: Intesa + UniCredit, or different banks?
2. **Timeline**: Is 4-5 weeks acceptable?
3. **Breaking Changes**: OK for v0.2.0, or must be v1.0.0?
4. **Resources**: Solo developer or team effort?

---

## 📖 Reference Documents

- **Strategy Overview**: [`MULTI_BANK_STRATEGY.md`](MULTI_BANK_STRATEGY.md)
- **Implementation Details**: [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md)
- **Current Codebase**: See `estrattoconto/` package

---

**Document Version**: 1.0
**Created**: 2026-01-18
**Author**: Claude (estrattoconto contributor)
**Status**: Ready for Review ✅

---

*Let's make estrattoconto the universal Italian bank statement processor!* 🇮🇹 🏦 📊
