# Multi-Bank Integration Strategy

## Executive Summary

This document outlines the strategy to transform `estrattoconto` from a single-bank solution (CENTROVENETO) into a multi-provider architecture supporting multiple Italian bank statement formats.

## Current State Analysis

### What Works Well
- ✅ Clean separation between extraction (`converter.py`), enrichment (`enrichment.py`), and API (`statement.py`)
- ✅ Well-designed OO API with `EstrattoConto` class
- ✅ Robust currency conversion for Italian format
- ✅ docling integration for PDF parsing
- ✅ Comprehensive test suite structure

### Current Limitations
- ❌ **Hardcoded bank detection**: Only checks for "BANCA VENETO CENTRALE" string
- ❌ **Fixed table structure assumptions**: Assumes specific table order (Table 0 = balance, Table 1 = account, etc.)
- ❌ **Single regex pattern set**: Enrichment patterns only work for CENTROVENETO format
- ❌ **No provider abstraction**: Bank-specific logic scattered across modules
- ❌ **Bug in detection**: Returns UNSUPPORTED on first non-match instead of checking all text

---

## Proposed Architecture: Provider Pattern

### Core Concept

Implement a **Provider Pattern** where each bank has a dedicated provider class implementing a common interface. This allows:
- Easy addition of new banks without modifying existing code
- Encapsulation of bank-specific logic
- Testable design with mock providers
- Consistent API regardless of underlying bank

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     estrattoconto                            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │          EstrattoConto (Public API)                 │    │
│  │  - from_pdf(path) → Delegates to ProviderRegistry  │    │
│  │  - All existing methods remain unchanged            │    │
│  └────────────────────┬───────────────────────────────┘    │
│                       │                                      │
│  ┌────────────────────▼───────────────────────────────┐    │
│  │          ProviderRegistry (Factory)                 │    │
│  │  - detect_provider(docling_doc) → BankProvider     │    │
│  │  - register_provider(provider_class)                │    │
│  │  - list_providers() → List[str]                     │    │
│  └────────────────────┬───────────────────────────────┘    │
│                       │                                      │
│                       │ Creates appropriate provider         │
│                       ▼                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         BankProvider (Abstract Base Class)           │  │
│  │  + name: str                                         │  │
│  │  + detect(docling_doc) → bool                       │  │
│  │  + extract_tables(docling_doc) → BankTables         │  │
│  │  + get_enrichment_patterns() → EnrichmentPatterns   │  │
│  │  + get_column_mapping() → Dict[str, str]            │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │ Implementations                   │
│         ┌───────────────┴────────────────┬──────────────┐  │
│         ▼                                 ▼              ▼  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │CentroVeneto │  │   Intesa    │  │   UniCredit │  ...  │
│  │  Provider   │  │  Provider   │  │   Provider  │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Core Provider Infrastructure (Week 1)

#### 1.1 Create Base Provider Interface

**File**: `estrattoconto/providers/__init__.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Pattern
import pandas as pd

@dataclass
class BankTables:
    """Standardized container for extracted bank data"""
    book_balance: pd.DataFrame
    account_information: pd.DataFrame
    balance_summary: pd.DataFrame
    transactions: pd.DataFrame

@dataclass
class EnrichmentPatterns:
    """Bank-specific regex patterns for entity extraction"""
    payer_pattern: Pattern | None = None
    payee_pattern: Pattern | None = None
    mandate_id_pattern: Pattern | None = None
    bill_pattern: Pattern | None = None
    incoming_transfer_pattern: Pattern | None = None
    outgoing_transfer_pattern: Pattern | None = None
    bank_fee_pattern: Pattern | None = None

class BankProvider(ABC):
    """Abstract base class for bank statement providers"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'CENTROVENETO')"""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable bank name (e.g., 'Banca del Veneto Centrale')"""
        pass

    @abstractmethod
    def detect(self, docling_doc) -> bool:
        """
        Detect if this provider can handle the given document.

        Args:
            docling_doc: Docling document object

        Returns:
            True if this provider can parse the document
        """
        pass

    @abstractmethod
    def extract_tables(self, docling_doc) -> BankTables:
        """
        Extract and structure tables from the document.

        Args:
            docling_doc: Docling document object

        Returns:
            BankTables with standardized structure
        """
        pass

    @abstractmethod
    def get_enrichment_patterns(self) -> EnrichmentPatterns:
        """
        Get bank-specific regex patterns for data enrichment.

        Returns:
            EnrichmentPatterns object with compiled regex patterns
        """
        pass

    @abstractmethod
    def get_column_mapping(self) -> Dict[str, str]:
        """
        Get mapping from bank-specific column names to standard names.

        Returns:
            Dict mapping bank columns to standard columns:
            - 'movement_date': Movement date column
            - 'value_date': Value date column
            - 'debit': Debit amount column
            - 'credit': Credit amount column
            - 'description': Transaction description column
        """
        pass
```

#### 1.2 Create Provider Registry

**File**: `estrattoconto/providers/registry.py`

```python
from typing import Dict, List, Type, Optional
from .base import BankProvider

class ProviderRegistry:
    """Factory and registry for bank providers"""

    _providers: Dict[str, Type[BankProvider]] = {}

    @classmethod
    def register(cls, provider_class: Type[BankProvider]) -> None:
        """Register a new provider"""
        # Instantiate to get name
        instance = provider_class()
        cls._providers[instance.name] = provider_class

    @classmethod
    def detect_provider(cls, docling_doc) -> Optional[BankProvider]:
        """
        Detect and return appropriate provider for document.

        Args:
            docling_doc: Docling document object

        Returns:
            BankProvider instance or None if no provider detected
        """
        for provider_class in cls._providers.values():
            provider = provider_class()
            if provider.detect(docling_doc):
                return provider
        return None

    @classmethod
    def get_provider(cls, name: str) -> Optional[BankProvider]:
        """Get provider by name"""
        provider_class = cls._providers.get(name)
        return provider_class() if provider_class else None

    @classmethod
    def list_providers(cls) -> List[str]:
        """List all registered provider names"""
        return list(cls._providers.keys())
```

#### 1.3 Migrate CENTROVENETO to Provider

**File**: `estrattoconto/providers/centroveneto.py`

```python
import re
from typing import Dict
from docling_core.types.doc import DoclingDocument, TableItem
import pandas as pd

from .base import BankProvider, BankTables, EnrichmentPatterns

class CentroVenetoProvider(BankProvider):
    """Provider for Banca del Veneto Centrale statements"""

    @property
    def name(self) -> str:
        return "CENTROVENETO"

    @property
    def display_name(self) -> str:
        return "Banca del Veneto Centrale"

    def detect(self, docling_doc: DoclingDocument) -> bool:
        """Detect CENTROVENETO by scanning for bank name"""
        # Fixed bug: check ALL texts before returning False
        for text in docling_doc.texts:
            if "BANCA VENETO CENTRALE" in text.text.upper():
                return True
        return False

    def extract_tables(self, docling_doc: DoclingDocument) -> BankTables:
        """
        Extract tables following CENTROVENETO structure:
        - Table 0: Book balance (period info)
        - Table 1: Account information
        - Tables 2 to n-1: Transaction data
        - Table n: Balance summary
        """
        tables = [item for item in docling_doc.tables if isinstance(item, TableItem)]

        if len(tables) < 2:
            raise ValueError(f"Expected at least 2 tables, found {len(tables)}")

        # Extract specific tables
        book_balance = self._table_to_df(tables[0])
        account_info = self._table_to_df(tables[1])
        balance_summary = self._table_to_df(tables[-1])

        # Combine transaction tables (all middle tables)
        transaction_dfs = [self._table_to_df(t) for t in tables[2:-1]]
        transactions = pd.concat(transaction_dfs, ignore_index=True) if transaction_dfs else pd.DataFrame()

        return BankTables(
            book_balance=book_balance,
            account_information=account_info,
            balance_summary=balance_summary,
            transactions=transactions
        )

    def get_enrichment_patterns(self) -> EnrichmentPatterns:
        """Return CENTROVENETO-specific regex patterns"""
        return EnrichmentPatterns(
            payer_pattern=re.compile(r'Ordinante:\s*(.*?)\s*Causale', re.IGNORECASE),
            payee_pattern=re.compile(r'ADDEBITO CRED\.\s*(.*?)\s*ID\.MANDATO', re.IGNORECASE),
            mandate_id_pattern=re.compile(r'ID\.MANDATO\s*(.*?)\s*(?:RIF\.|\sSDD)', re.IGNORECASE),
            bill_pattern=re.compile(r'S\.D\.D\.', re.IGNORECASE),
            incoming_transfer_pattern=re.compile(r'BONIFICO A VS\. FAVORE', re.IGNORECASE),
            outgoing_transfer_pattern=re.compile(r'BONIFICO coordinate benef', re.IGNORECASE),
            bank_fee_pattern=re.compile(r'CANONE|COMMISSIONI', re.IGNORECASE)
        )

    def get_column_mapping(self) -> Dict[str, str]:
        """Return CENTROVENETO column name mapping"""
        return {
            'movement_date': 'DATA MOV.',
            'value_date': 'VALUTA',
            'debit': 'DARE',
            'credit': 'AVERE',
            'description': 'DESCRIZIONE OPERAZIONE'
        }

    @staticmethod
    def _table_to_df(table: TableItem) -> pd.DataFrame:
        """Convert TableItem to DataFrame"""
        return table.export_to_dataframe()
```

#### 1.4 Update Converter to Use Providers

**File**: `estrattoconto/converter.py` (refactored)

```python
from typing import Tuple
import pandas as pd
from docling.document_converter import DocumentConverter

from .providers import ProviderRegistry, BankProvider
from .providers.centroveneto import CentroVenetoProvider

# Auto-register providers
ProviderRegistry.register(CentroVenetoProvider)

def extract_document_type(docling_doc) -> str:
    """Detect bank type (deprecated - use detect_provider)"""
    provider = ProviderRegistry.detect_provider(docling_doc)
    return provider.name if provider else "UNSUPPORTED"

def detect_provider(docling_doc) -> BankProvider | None:
    """Detect and return appropriate bank provider"""
    return ProviderRegistry.detect_provider(docling_doc)

def extract_table(
    doc_path: str,
    provider: BankProvider | None = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Extract tables from bank statement PDF.

    Args:
        doc_path: Path to PDF file
        provider: Optional specific provider to use (auto-detected if None)

    Returns:
        Tuple of (book_balance, account_info, balance_summary, transactions)
    """
    converter = DocumentConverter()
    result = converter.convert(doc_path)
    docling_doc = result.document

    # Detect provider if not specified
    if provider is None:
        provider = ProviderRegistry.detect_provider(docling_doc)
        if provider is None:
            raise ValueError(f"Unsupported bank statement format")

    # Extract using provider
    tables = provider.extract_tables(docling_doc)

    return (
        tables.book_balance,
        tables.account_information,
        tables.balance_summary,
        tables.transactions
    )
```

#### 1.5 Update Enrichment to Use Provider Patterns

**File**: `estrattoconto/enrichment.py` (refactored)

```python
import pandas as pd
from .providers import BankProvider, EnrichmentPatterns

def enrich_data(
    extracted_data: tuple,
    provider: BankProvider
) -> pd.DataFrame:
    """
    Enrich transaction data using provider-specific patterns.

    Args:
        extracted_data: Tuple of (book_balance, account_info, balance_summary, transactions)
        provider: Bank provider with enrichment patterns

    Returns:
        Enriched DataFrame with extracted entities and classifications
    """
    book_balance, account_information, balance_summary, data_table = extracted_data

    # Postprocess (standardize column names using provider mapping)
    data_table = postprocess_extraction(data_table, provider)

    # Get provider-specific patterns
    patterns = provider.get_enrichment_patterns()

    # Extract entities using provider patterns
    data_table = _extract_entities(data_table, patterns)

    # Convert currency
    data_table = _convert_currency(data_table)

    # Classify transactions using provider patterns
    data_table = _classify_transactions(data_table, patterns)

    # Add metadata
    data_table = _add_metadata(data_table, account_information, book_balance)

    return data_table

def postprocess_extraction(
    data_table: pd.DataFrame,
    provider: BankProvider
) -> pd.DataFrame:
    """Standardize column names and clean data"""
    mapping = provider.get_column_mapping()

    # Create reverse mapping for renaming
    reverse_mapping = {v: k for k, v in mapping.items()}

    # Select only mapped columns that exist
    existing_cols = [col for col in mapping.values() if col in data_table.columns]
    data_table = data_table[existing_cols].copy()

    # Optionally rename to standard names (keeping original for backward compatibility)
    # data_table = data_table.rename(columns=reverse_mapping)

    # Remove empty rows
    data_table = data_table.dropna(how='all')

    return data_table

def _extract_entities(df: pd.DataFrame, patterns: EnrichmentPatterns) -> pd.DataFrame:
    """Extract entities using regex patterns"""
    desc_col = 'DESCRIZIONE OPERAZIONE'  # Use standardized name from provider

    if patterns.payer_pattern:
        df['payer'] = df[desc_col].str.extract(patterns.payer_pattern, expand=False)

    if patterns.payee_pattern:
        df['payee'] = df[desc_col].str.extract(patterns.payee_pattern, expand=False)

    if patterns.mandate_id_pattern:
        df['id_mandato'] = df[desc_col].str.extract(patterns.mandate_id_pattern, expand=False)

    return df

def _classify_transactions(df: pd.DataFrame, patterns: EnrichmentPatterns) -> pd.DataFrame:
    """Classify transactions using regex patterns"""
    desc_col = 'DESCRIZIONE OPERAZIONE'

    if patterns.bill_pattern:
        df['is_bill'] = df[desc_col].str.contains(patterns.bill_pattern, na=False)

    if patterns.incoming_transfer_pattern:
        df['is_incoming_transfer'] = df[desc_col].str.contains(patterns.incoming_transfer_pattern, na=False)

    if patterns.outgoing_transfer_pattern:
        df['is_outcoming_transfer'] = df[desc_col].str.contains(patterns.outgoing_transfer_pattern, na=False)

    if patterns.bank_fee_pattern:
        df['is_bank_fee'] = df[desc_col].str.contains(patterns.bank_fee_pattern, na=False)

    return df

# Keep existing _convert_currency and _add_metadata functions unchanged
```

---

### Phase 2: Mockup Generation with Docling (Week 2)

#### 2.1 Create Mock Provider for Testing

**File**: `estrattoconto/providers/mock.py`

```python
"""
Mock provider for testing multi-bank support.
Generates synthetic bank statements for development.
"""
import re
from typing import Dict
import pandas as pd
from datetime import datetime, timedelta
from .base import BankProvider, BankTables, EnrichmentPatterns

class MockBankProvider(BankProvider):
    """
    Mock provider that generates synthetic bank statement data.
    Useful for testing without real PDFs.
    """

    def __init__(self, bank_name: str = "MOCKBANK"):
        self._bank_name = bank_name

    @property
    def name(self) -> str:
        return self._bank_name

    @property
    def display_name(self) -> str:
        return f"Mock Bank ({self._bank_name})"

    def detect(self, docling_doc) -> bool:
        """Always returns False - must be explicitly instantiated"""
        return False

    def extract_tables(self, docling_doc) -> BankTables:
        """Generate mock transaction data"""
        return self.generate_mock_data()

    def generate_mock_data(
        self,
        account_number: str = "IT60X0542811101000000123456",
        period_start: str = "01/01/2025",
        period_end: str = "31/01/2025",
        num_transactions: int = 50
    ) -> BankTables:
        """
        Generate synthetic bank statement data.

        Args:
            account_number: IBAN
            period_start: Start date (DD/MM/YYYY)
            period_end: End date (DD/MM/YYYY)
            num_transactions: Number of transactions to generate

        Returns:
            BankTables with synthetic data
        """
        # Book balance
        book_balance = pd.DataFrame({
            'Period': [f"{period_start} - {period_end}"],
            'Account': [account_number]
        })

        # Account information
        account_info = pd.DataFrame({
            'IBAN': [account_number],
            'Account Holder': ['MOCK CUSTOMER'],
            'Branch': ['Mock Branch 001']
        })

        # Balance summary
        balance_summary = pd.DataFrame({
            'Opening Balance': ['+ 10.000,00 €'],
            'Closing Balance': ['+ 9.500,00 €'],
            'Total Credits': ['+ 5.000,00 €'],
            'Total Debits': ['- 5.500,00 €']
        })

        # Generate transactions
        transactions = self._generate_transactions(num_transactions, period_start, period_end)

        return BankTables(
            book_balance=book_balance,
            account_information=account_info,
            balance_summary=balance_summary,
            transactions=transactions
        )

    def _generate_transactions(self, count: int, start_date: str, end_date: str) -> pd.DataFrame:
        """Generate synthetic transaction data"""
        import random

        # Parse dates
        start = datetime.strptime(start_date, "%d/%m/%Y")
        end = datetime.strptime(end_date, "%d/%m/%Y")
        delta = end - start

        transactions = []

        transaction_types = [
            ('bill', 'ADDEBITO CRED. ACME UTILITIES SPA ID.MANDATO IT12345 RIF. 2025-001', 'debit'),
            ('incoming', 'BONIFICO A VS. FAVORE Ordinante: JOHN DOE Causale: Payment invoice', 'credit'),
            ('outgoing', 'BONIFICO coordinate benef JANE SMITH Causale: Monthly rent', 'debit'),
            ('fee', 'CANONE MENSILE CONTO CORRENTE', 'debit'),
            ('fee', 'COMMISSIONI GESTIONE CONTO', 'debit'),
        ]

        for i in range(count):
            # Random date within period
            random_days = random.randint(0, delta.days)
            txn_date = start + timedelta(days=random_days)
            date_str = txn_date.strftime("%d/%m/%Y")

            # Random transaction type
            txn_type, description, direction = random.choice(transaction_types)

            # Random amount
            amount = round(random.uniform(10, 500), 2)
            amount_str = f"{'+ ' if direction == 'credit' else '- '}{amount:,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.')

            transactions.append({
                'DATA MOV.': date_str,
                'VALUTA': date_str,
                'DARE': amount_str if direction == 'debit' else '',
                'AVERE': amount_str if direction == 'credit' else '',
                'DESCRIZIONE OPERAZIONE': description
            })

        return pd.DataFrame(transactions)

    def get_enrichment_patterns(self) -> EnrichmentPatterns:
        """Use same patterns as CENTROVENETO for mock data"""
        return EnrichmentPatterns(
            payer_pattern=re.compile(r'Ordinante:\s*(.*?)\s*Causale', re.IGNORECASE),
            payee_pattern=re.compile(r'ADDEBITO CRED\.\s*(.*?)\s*ID\.MANDATO', re.IGNORECASE),
            mandate_id_pattern=re.compile(r'ID\.MANDATO\s*(.*?)\s*(?:RIF\.|\sSDD)', re.IGNORECASE),
            bill_pattern=re.compile(r'S\.D\.D\.|ADDEBITO CRED\.', re.IGNORECASE),
            incoming_transfer_pattern=re.compile(r'BONIFICO A VS\. FAVORE', re.IGNORECASE),
            outgoing_transfer_pattern=re.compile(r'BONIFICO coordinate benef', re.IGNORECASE),
            bank_fee_pattern=re.compile(r'CANONE|COMMISSIONI', re.IGNORECASE)
        )

    def get_column_mapping(self) -> Dict[str, str]:
        """Use same column names as CENTROVENETO"""
        return {
            'movement_date': 'DATA MOV.',
            'value_date': 'VALUTA',
            'debit': 'DARE',
            'credit': 'AVERE',
            'description': 'DESCRIZIONE OPERAZIONE'
        }
```

#### 2.2 Create Docling PDF Generator for Mocks

**File**: `tests/mock_generators/pdf_generator.py`

```python
"""
Generate mock PDF bank statements using ReportLab.
These PDFs are designed to be parseable by Docling.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from typing import List, Dict
import pandas as pd

class MockPDFGenerator:
    """Generate mock bank statement PDFs for testing"""

    def __init__(self, bank_name: str, logo_text: str | None = None):
        self.bank_name = bank_name
        self.logo_text = logo_text or bank_name

    def generate_statement(
        self,
        output_path: str,
        account_info: Dict[str, str],
        transactions: pd.DataFrame,
        period: str,
        opening_balance: str,
        closing_balance: str
    ):
        """
        Generate a mock bank statement PDF.

        Args:
            output_path: Path to save PDF
            account_info: Dict with account details (IBAN, holder, etc.)
            transactions: DataFrame with transaction data
            period: Statement period string
            opening_balance: Opening balance string
            closing_balance: Closing balance string
        """
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#003366'),
            spaceAfter=30,
        )

        # Bank logo/name
        title = Paragraph(self.logo_text, title_style)
        story.append(title)
        story.append(Spacer(1, 0.5*cm))

        # Statement header
        header = Paragraph(f"<b>ESTRATTO CONTO</b><br/>{period}", styles['Heading2'])
        story.append(header)
        story.append(Spacer(1, 0.5*cm))

        # Account information table
        account_data = [[k, v] for k, v in account_info.items()]
        account_table = Table(account_data, colWidths=[5*cm, 10*cm])
        account_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(account_table)
        story.append(Spacer(1, 1*cm))

        # Balance summary
        balance_data = [
            ['Opening Balance', opening_balance],
            ['Closing Balance', closing_balance]
        ]
        balance_table = Table(balance_data, colWidths=[7*cm, 5*cm])
        balance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(balance_table)
        story.append(Spacer(1, 1*cm))

        # Transaction table
        txn_header = Paragraph("<b>Movimenti del conto</b>", styles['Heading3'])
        story.append(txn_header)
        story.append(Spacer(1, 0.5*cm))

        # Convert DataFrame to table data
        txn_data = [transactions.columns.tolist()] + transactions.values.tolist()

        # Calculate column widths
        col_widths = [2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 8*cm]

        txn_table = Table(txn_data, colWidths=col_widths, repeatRows=1)
        txn_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(txn_table)

        # Build PDF
        doc.build(story)

# Usage example
def generate_centroveneto_mock():
    """Generate a mock CENTROVENETO statement"""
    generator = MockPDFGenerator(
        bank_name="CENTROVENETO",
        logo_text="BANCA VENETO CENTRALE"
    )

    account_info = {
        'IBAN': 'IT60X0542811101000000123456',
        'Intestatario': 'MARIO ROSSI',
        'Filiale': 'TREVISO 001'
    }

    # Generate mock transactions
    from estrattoconto.providers.mock import MockBankProvider
    mock_provider = MockBankProvider("CENTROVENETO")
    tables = mock_provider.generate_mock_data(num_transactions=30)

    generator.generate_statement(
        output_path='tests/fixtures/mock_centroveneto.pdf',
        account_info=account_info,
        transactions=tables.transactions,
        period='01/01/2025 - 31/01/2025',
        opening_balance='+ 10.000,00 €',
        closing_balance='+ 9.500,00 €'
    )
```

#### 2.3 Create CLI Command for Mock Generation

**File**: `estrattoconto/cli_mock.py`

```python
"""CLI commands for generating mock data"""
import click
from pathlib import Path
from .providers.mock import MockBankProvider

@click.group()
def mock():
    """Generate mock bank statement data for testing"""
    pass

@mock.command()
@click.option('--bank', default='MOCKBANK', help='Bank name for mock data')
@click.option('--transactions', default=50, help='Number of transactions to generate')
@click.option('--output', required=True, help='Output CSV file')
def generate_csv(bank: str, transactions: int, output: str):
    """Generate mock transaction data as CSV"""
    provider = MockBankProvider(bank)
    tables = provider.generate_mock_data(num_transactions=transactions)

    tables.transactions.to_csv(output, index=False)
    click.echo(f"✓ Generated {len(tables.transactions)} transactions to {output}")

@mock.command()
@click.option('--bank', default='CENTROVENETO', help='Bank to generate PDF for')
@click.option('--transactions', default=30, help='Number of transactions')
@click.option('--output', required=True, help='Output PDF file')
def generate_pdf(bank: str, transactions: int, output: str):
    """Generate mock bank statement PDF"""
    # Import here to avoid dependency on reportlab if not used
    try:
        from tests.mock_generators.pdf_generator import MockPDFGenerator, generate_centroveneto_mock
    except ImportError:
        click.echo("Error: reportlab not installed. Install with: pip install reportlab", err=True)
        return

    if bank == 'CENTROVENETO':
        generate_centroveneto_mock()
        click.echo(f"✓ Generated CENTROVENETO mock PDF to {output}")
    else:
        click.echo(f"Error: PDF generation for {bank} not yet implemented", err=True)
```

---

### Phase 3: Add Support for Real Banks (Week 3-4)

#### 3.1 Intesa SanPaolo Provider

**Research Required**: Obtain sample Intesa SanPaolo statement to identify:
- Bank name detection string
- Table structure
- Column names
- Transaction description patterns

**File**: `estrattoconto/providers/intesa.py`

```python
"""Provider for Intesa SanPaolo bank statements"""
import re
from typing import Dict
from .base import BankProvider, BankTables, EnrichmentPatterns
# Implementation follows same pattern as CentroVenetoProvider
```

#### 3.2 UniCredit Provider

**File**: `estrattoconto/providers/unicredit.py`

Similar structure to Intesa provider.

#### 3.3 Other Major Italian Banks

Planned providers:
- BancoBPM
- Monte dei Paschi di Siena (MPS)
- Banca Mediolanum
- Fineco Bank
- Poste Italiane

---

## Testing Strategy

### Unit Tests

**File**: `tests/test_providers.py`

```python
"""Test provider detection and data extraction"""
import pytest
from estrattoconto.providers import ProviderRegistry
from estrattoconto.providers.centroveneto import CentroVenetoProvider
from estrattoconto.providers.mock import MockBankProvider

def test_provider_registration():
    """Test provider can be registered and retrieved"""
    ProviderRegistry.register(MockBankProvider)
    assert 'MOCKBANK' in ProviderRegistry.list_providers()

def test_centroveneto_detection():
    """Test CENTROVENETO is detected from document"""
    # Load fixture PDF
    from docling.document_converter import DocumentConverter
    converter = DocumentConverter()
    result = converter.convert('tests/fixtures/centroveneto.pdf')

    provider = ProviderRegistry.detect_provider(result.document)
    assert provider is not None
    assert provider.name == 'CENTROVENETO'

def test_mock_provider_generation():
    """Test mock provider generates valid data"""
    provider = MockBankProvider('TEST')
    tables = provider.generate_mock_data(num_transactions=10)

    assert len(tables.transactions) == 10
    assert 'DATA MOV.' in tables.transactions.columns
    assert 'DESCRIZIONE OPERAZIONE' in tables.transactions.columns

def test_enrichment_with_provider_patterns():
    """Test enrichment uses provider-specific patterns"""
    provider = CentroVenetoProvider()
    patterns = provider.get_enrichment_patterns()

    # Test payer extraction
    test_desc = "BONIFICO Ordinante: JOHN DOE Causale: Payment"
    match = patterns.payer_pattern.search(test_desc)
    assert match.group(1) == "JOHN DOE"
```

### Integration Tests

**File**: `tests/test_integration_multibank.py`

```python
"""Integration tests for multi-bank support"""
import pytest
from estrattoconto import convert
from estrattoconto.providers.mock import MockBankProvider

def test_convert_with_mock_data():
    """Test full pipeline with mock data"""
    # Generate mock PDF (requires reportlab)
    # Convert using estrattoconto
    # Verify enriched output
    pass

def test_convert_centroveneto_real_pdf():
    """Test real CENTROVENETO PDF processing"""
    statement = convert('tests/fixtures/centroveneto.pdf')
    assert statement is not None
    assert len(statement) > 0
```

---

## Documentation Updates

### User Documentation

**File**: `docs/MULTI_BANK_SUPPORT.md`

```markdown
# Multi-Bank Support

estrattoconto supports multiple Italian bank statement formats.

## Supported Banks

- ✅ Banca del Veneto Centrale (CENTROVENETO)
- 🚧 Intesa SanPaolo (Coming soon)
- 🚧 UniCredit (Coming soon)

## Usage

The library automatically detects the bank type:

\`\`\`python
import estrattoconto

# Automatic detection
statement = estrattoconto.convert('statement.pdf')
\`\`\`

## Adding Support for New Banks

See [CONTRIBUTING.md](CONTRIBUTING.md) for instructions on adding new bank providers.
\`\`\`

### Developer Documentation

**File**: `docs/PROVIDER_DEVELOPMENT.md`

Complete guide on creating new providers with examples and templates.

---

## Migration Path

### Backward Compatibility

All existing code continues to work:
- ✅ `estrattoconto.convert()` auto-detects provider
- ✅ Legacy functional API (`extract_table`, `enrich_data`) maintained
- ✅ Existing column names preserved
- ✅ All `EstrattoConto` methods unchanged

### Deprecation Notices

- `extract_document_type()` → Deprecated in favor of `detect_provider()`
- Will add warnings in version 0.2.0, remove in version 1.0.0

---

## Success Criteria

### Phase 1 (Core Infrastructure)
- [ ] `BankProvider` abstract base class implemented
- [ ] `ProviderRegistry` factory working
- [ ] `CentroVenetoProvider` migrated and tested
- [ ] All existing tests passing
- [ ] Backward compatibility verified

### Phase 2 (Mockups)
- [ ] `MockBankProvider` generating valid data
- [ ] PDF generator creating docling-parseable files
- [ ] CLI commands for mock generation
- [ ] Mock-based tests written

### Phase 3 (Real Banks)
- [ ] At least 2 additional banks supported (Intesa, UniCredit)
- [ ] Integration tests for each bank
- [ ] Documentation complete
- [ ] Example statements collected (with sensitive data removed)

---

## Timeline Summary

| Phase | Duration | Deliverables |
|---|---|---|
| **Phase 1** | 1 week | Provider infrastructure, CENTROVENETO migration |
| **Phase 2** | 1 week | Mock generators, test framework |
| **Phase 3** | 2-3 weeks | 2+ new bank providers, documentation |

**Total**: 4-5 weeks for full multi-bank support

---

## Next Steps

1. **Approve this plan** - Review and provide feedback
2. **Set up development branch** - Create feature branch for provider system
3. **Implement Phase 1** - Build core infrastructure
4. **Create mockups** - Generate test data with docling
5. **Add real banks** - Implement Intesa and UniCredit providers
6. **Release v0.2.0** - Multi-bank support release

---

## Questions for Stakeholders

1. **Priority banks**: Which banks should we support first after CENTROVENETO?
2. **PDF samples**: Can you provide sample statements (anonymized) for testing?
3. **Breaking changes**: Are breaking changes acceptable for v0.2.0, or strict backward compatibility required?
4. **Timeline**: Is 4-5 weeks acceptable, or do we need to accelerate?

---

*Document Version: 1.0*
*Last Updated: 2026-01-18*
*Author: Claude (estrattoconto contributor)*
