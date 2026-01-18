# Multi-Bank Integration - Implementation Roadmap

## Overview

This document provides the step-by-step implementation plan for adding multi-bank support to `estrattoconto`, including concrete code examples and mockup generation using docling.

---

## Phase 1: Core Provider Infrastructure

### Step 1.1: Create Provider Package Structure

```bash
mkdir -p estrattoconto/providers
touch estrattoconto/providers/__init__.py
touch estrattoconto/providers/base.py
touch estrattoconto/providers/registry.py
touch estrattoconto/providers/centroveneto.py
touch estrattoconto/providers/mock.py
```

**Package Structure:**
```
estrattoconto/providers/
├── __init__.py           # Public exports
├── base.py               # Abstract base class & data models
├── registry.py           # Provider factory & registry
├── centroveneto.py       # Existing bank (refactored)
├── mock.py               # Mock provider for testing
├── intesa.py            # Intesa SanPaolo (future)
└── unicredit.py         # UniCredit (future)
```

### Step 1.2: Implement Base Classes

**File**: `estrattoconto/providers/__init__.py`

```python
"""
Multi-bank provider system for estrattoconto.

This package implements a provider pattern for supporting multiple
Italian bank statement formats.
"""

from .base import BankProvider, BankTables, EnrichmentPatterns
from .registry import ProviderRegistry
from .centroveneto import CentroVenetoProvider
from .mock import MockBankProvider

# Auto-register all providers
ProviderRegistry.register(CentroVenetoProvider)
ProviderRegistry.register(MockBankProvider)

__all__ = [
    'BankProvider',
    'BankTables',
    'EnrichmentPatterns',
    'ProviderRegistry',
    'CentroVenetoProvider',
    'MockBankProvider',
]
```

**Key Implementation Details:**

1. **BankTables Dataclass**: Standardizes the 4 DataFrame structure
2. **EnrichmentPatterns Dataclass**: Encapsulates bank-specific regex patterns
3. **BankProvider ABC**: Defines the interface all providers must implement
4. **ProviderRegistry**: Singleton pattern for provider management

### Step 1.3: Update Converter Module

**File**: `estrattoconto/converter.py` (changes)

```python
from typing import Tuple, Optional
import pandas as pd
from docling.document_converter import DocumentConverter

# New imports
from .providers import ProviderRegistry, BankProvider
from .providers.centroveneto import CentroVenetoProvider

# Auto-register built-in providers
ProviderRegistry.register(CentroVenetoProvider)

def extract_document_type(docling_doc) -> str:
    """
    Detect bank type from document.

    .. deprecated:: 0.2.0
        Use :func:`detect_provider` instead.

    Args:
        docling_doc: Docling document object

    Returns:
        Bank identifier or "UNSUPPORTED"
    """
    import warnings
    warnings.warn(
        "extract_document_type is deprecated, use detect_provider instead",
        DeprecationWarning,
        stacklevel=2
    )
    provider = ProviderRegistry.detect_provider(docling_doc)
    return provider.name if provider else "UNSUPPORTED"

def detect_provider(docling_doc) -> Optional[BankProvider]:
    """
    Detect and return appropriate bank provider for document.

    Args:
        docling_doc: Docling document object

    Returns:
        BankProvider instance or None if unsupported

    Example:
        >>> from docling.document_converter import DocumentConverter
        >>> converter = DocumentConverter()
        >>> result = converter.convert('statement.pdf')
        >>> provider = detect_provider(result.document)
        >>> if provider:
        ...     print(f"Detected: {provider.display_name}")
    """
    return ProviderRegistry.detect_provider(docling_doc)

def extract_table(
    doc_path: str,
    provider: Optional[BankProvider] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Extract tables from bank statement PDF.

    Args:
        doc_path: Path to PDF file
        provider: Optional specific provider to use (auto-detected if None)

    Returns:
        Tuple of (book_balance, account_info, balance_summary, transactions)

    Raises:
        ValueError: If no provider can handle the document
        FileNotFoundError: If doc_path doesn't exist

    Example:
        >>> # Automatic detection
        >>> tables = extract_table('statement.pdf')
        >>>
        >>> # Explicit provider
        >>> from estrattoconto.providers import CentroVenetoProvider
        >>> provider = CentroVenetoProvider()
        >>> tables = extract_table('statement.pdf', provider=provider)
    """
    # Convert PDF to docling document
    converter = DocumentConverter()
    result = converter.convert(doc_path)
    docling_doc = result.document

    # Detect provider if not specified
    if provider is None:
        provider = ProviderRegistry.detect_provider(docling_doc)
        if provider is None:
            supported = ', '.join(ProviderRegistry.list_providers())
            raise ValueError(
                f"Unsupported bank statement format. "
                f"Supported banks: {supported}"
            )

    # Extract using provider
    tables = provider.extract_tables(docling_doc)

    # Return as tuple for backward compatibility
    return (
        tables.book_balance,
        tables.account_information,
        tables.balance_summary,
        tables.transactions
    )
```

### Step 1.4: Update Enrichment Module

**File**: `estrattoconto/enrichment.py` (changes)

```python
import pandas as pd
from typing import Tuple

from .providers import BankProvider
from .utils import clean_and_convert_currency

def enrich_data(
    extracted_data: Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
    provider: BankProvider
) -> pd.DataFrame:
    """
    Enrich transaction data using provider-specific patterns.

    Args:
        extracted_data: Tuple of (book_balance, account_info, balance_summary, transactions)
        provider: Bank provider with enrichment patterns

    Returns:
        Enriched DataFrame with extracted entities and classifications

    Example:
        >>> from estrattoconto import extract_table, enrich_data
        >>> from estrattoconto.providers import detect_provider
        >>> from docling.document_converter import DocumentConverter
        >>>
        >>> # Extract with provider
        >>> converter = DocumentConverter()
        >>> result = converter.convert('statement.pdf')
        >>> provider = detect_provider(result.document)
        >>> tables = extract_table('statement.pdf', provider)
        >>> enriched = enrich_data(tables, provider)
    """
    book_balance, account_information, balance_summary, data_table = extracted_data

    # Postprocess using provider column mapping
    data_table = postprocess_extraction(data_table, provider)

    # Get provider-specific patterns
    patterns = provider.get_enrichment_patterns()

    # Enrichment pipeline
    data_table = _extract_entities(data_table, patterns, provider)
    data_table = _convert_currency(data_table, provider)
    data_table = _classify_transactions(data_table, patterns, provider)
    data_table = _add_metadata(data_table, account_information, book_balance, provider)

    return data_table

def postprocess_extraction(
    data_table: pd.DataFrame,
    provider: BankProvider
) -> pd.DataFrame:
    """
    Standardize column names and clean data using provider mapping.

    Args:
        data_table: Raw transaction DataFrame
        provider: Bank provider with column mapping

    Returns:
        Cleaned DataFrame with standardized columns
    """
    mapping = provider.get_column_mapping()

    # Select only columns that exist in mapping
    existing_cols = [col for col in mapping.values() if col in data_table.columns]

    if not existing_cols:
        raise ValueError(
            f"No expected columns found in data. "
            f"Expected: {list(mapping.values())}, "
            f"Found: {list(data_table.columns)}"
        )

    data_table = data_table[existing_cols].copy()

    # Remove completely empty rows
    data_table = data_table.dropna(how='all')

    # Clean currency columns
    debit_col = mapping.get('debit')
    credit_col = mapping.get('credit')

    for col in [debit_col, credit_col]:
        if col and col in data_table.columns:
            # Set empty cells if no euro symbol present
            data_table[col] = data_table[col].apply(
                lambda x: x if isinstance(x, str) and '€' in x else ''
            )

    return data_table

def _extract_entities(
    df: pd.DataFrame,
    patterns,
    provider: BankProvider
) -> pd.DataFrame:
    """Extract entities (payer, payee, mandate ID) using regex patterns"""
    mapping = provider.get_column_mapping()
    desc_col = mapping.get('description', 'DESCRIZIONE OPERAZIONE')

    if desc_col not in df.columns:
        return df

    # Extract payer
    if patterns.payer_pattern:
        df['payer'] = df[desc_col].str.extract(patterns.payer_pattern, expand=False)

    # Extract payee
    if patterns.payee_pattern:
        df['payee'] = df[desc_col].str.extract(patterns.payee_pattern, expand=False)

    # Extract mandate ID
    if patterns.mandate_id_pattern:
        df['id_mandato'] = df[desc_col].str.extract(
            patterns.mandate_id_pattern,
            expand=False
        )

    return df

def _convert_currency(
    df: pd.DataFrame,
    provider: BankProvider
) -> pd.DataFrame:
    """Convert Italian currency format to numeric"""
    mapping = provider.get_column_mapping()
    debit_col = mapping.get('debit', 'DARE')
    credit_col = mapping.get('credit', 'AVERE')

    # Convert DARE and AVERE
    if debit_col in df.columns:
        df['DARE_Numeric'] = clean_and_convert_currency(df[debit_col])

    if credit_col in df.columns:
        df['AVERE_Numeric'] = clean_and_convert_currency(df[credit_col])

    # Create unified amount column
    df['amount'] = df.get('AVERE_Numeric', 0) - df.get('DARE_Numeric', 0).abs()

    return df

def _classify_transactions(
    df: pd.DataFrame,
    patterns,
    provider: BankProvider
) -> pd.DataFrame:
    """Classify transactions using regex patterns"""
    mapping = provider.get_column_mapping()
    desc_col = mapping.get('description', 'DESCRIZIONE OPERAZIONE')

    if desc_col not in df.columns:
        return df

    # Bill detection (S.D.D.)
    if patterns.bill_pattern:
        df['is_bill'] = df[desc_col].str.contains(
            patterns.bill_pattern,
            na=False
        )

    # Incoming transfer
    if patterns.incoming_transfer_pattern:
        df['is_incoming_transfer'] = df[desc_col].str.contains(
            patterns.incoming_transfer_pattern,
            na=False
        )

    # Outgoing transfer
    if patterns.outgoing_transfer_pattern:
        df['is_outcoming_transfer'] = df[desc_col].str.contains(
            patterns.outgoing_transfer_pattern,
            na=False
        )

    # Bank fees
    if patterns.bank_fee_pattern:
        df['is_bank_fee'] = df[desc_col].str.contains(
            patterns.bank_fee_pattern,
            na=False
        )

    return df

def _add_metadata(
    df: pd.DataFrame,
    account_information: pd.DataFrame,
    book_balance: pd.DataFrame,
    provider: BankProvider
) -> pd.DataFrame:
    """Add account and period metadata to each transaction"""
    # Extract account number (first IBAN-like value)
    account = None
    for col in account_information.columns:
        for val in account_information[col]:
            if isinstance(val, str) and ('IT' in val or 'IBAN' in val.upper()):
                account = val
                break
        if account:
            break

    # Extract period (date range)
    period = None
    for col in book_balance.columns:
        for val in book_balance[col]:
            if isinstance(val, str) and '-' in val and '/' in val:
                period = val
                break
        if period:
            break

    df['related_account'] = account
    df['period'] = period

    return df
```

### Step 1.5: Update Statement Class

**File**: `estrattoconto/statement.py` (changes)

```python
from pathlib import Path
import pandas as pd
from typing import Optional

from .converter import extract_table, detect_provider
from .enrichment import enrich_data
from .providers import BankProvider

class EstrattoConto:
    """
    Object-oriented interface for bank statement analysis.

    Supports multiple Italian bank formats through the provider system.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        provider: Optional[BankProvider] = None
    ):
        """
        Initialize with enriched transaction data.

        Args:
            data: Enriched DataFrame with transaction data
            provider: Bank provider used for extraction (optional)

        Note:
            Use :meth:`from_pdf` class method to create instances from PDFs.
        """
        self._data = data.copy()
        self._provider = provider

    @classmethod
    def from_pdf(
        cls,
        pdf_path: str | Path,
        provider: Optional[BankProvider] = None
    ) -> 'EstrattoConto':
        """
        Create EstrattoConto instance from PDF bank statement.

        Args:
            pdf_path: Path to PDF file
            provider: Optional specific provider (auto-detected if None)

        Returns:
            EstrattoConto instance with enriched data

        Raises:
            ValueError: If no provider can handle the document
            FileNotFoundError: If pdf_path doesn't exist

        Example:
            >>> # Automatic bank detection
            >>> statement = EstrattoConto.from_pdf('statement.pdf')
            >>> print(f"Bank: {statement.provider_name}")
            >>>
            >>> # Explicit provider
            >>> from estrattoconto.providers import CentroVenetoProvider
            >>> provider = CentroVenetoProvider()
            >>> statement = EstrattoConto.from_pdf('statement.pdf', provider)
        """
        # Convert to Path object
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Detect provider if not provided
        if provider is None:
            from docling.document_converter import DocumentConverter
            converter = DocumentConverter()
            result = converter.convert(str(pdf_path))
            provider = detect_provider(result.document)

            if provider is None:
                from .providers import ProviderRegistry
                supported = ', '.join(ProviderRegistry.list_providers())
                raise ValueError(
                    f"Unsupported bank statement format. "
                    f"Supported banks: {supported}"
                )

        # Extract and enrich data
        extracted_data = extract_table(str(pdf_path), provider)
        enriched_data = enrich_data(extracted_data, provider)

        return cls(enriched_data, provider)

    @property
    def provider_name(self) -> Optional[str]:
        """Get the name of the bank provider used"""
        return self._provider.name if self._provider else None

    @property
    def provider_display_name(self) -> Optional[str]:
        """Get the display name of the bank"""
        return self._provider.display_name if self._provider else None

    # ... rest of existing methods unchanged ...

    def summary(self) -> dict:
        """
        Get summary statistics for the statement.

        Returns:
            Dictionary with summary information including provider details

        Example:
            >>> statement = EstrattoConto.from_pdf('statement.pdf')
            >>> summary = statement.summary()
            >>> print(f"Bank: {summary['bank']}")
            >>> print(f"Total transactions: {summary['total_transactions']}")
        """
        summary_dict = {
            'bank': self.provider_display_name,
            'bank_code': self.provider_name,
            'total_transactions': len(self._data),
            'period': self._data['period'].iloc[0] if 'period' in self._data else None,
            'account': self._data['related_account'].iloc[0] if 'related_account' in self._data else None,
        }

        # Add transaction counts by type
        if 'is_bill' in self._data:
            summary_dict['bills'] = self._data['is_bill'].sum()
        if 'is_incoming_transfer' in self._data:
            summary_dict['incoming_transfers'] = self._data['is_incoming_transfer'].sum()
        if 'is_outcoming_transfer' in self._data:
            summary_dict['outgoing_transfers'] = self._data['is_outcoming_transfer'].sum()
        if 'is_bank_fee' in self._data:
            summary_dict['bank_fees'] = self._data['is_bank_fee'].sum()

        # Add amount totals
        if 'DARE_Numeric' in self._data:
            summary_dict['total_debit'] = self._data['DARE_Numeric'].sum()
        if 'AVERE_Numeric' in self._data:
            summary_dict['total_credit'] = self._data['AVERE_Numeric'].sum()

        return summary_dict

    def __repr__(self) -> str:
        """String representation"""
        bank = self.provider_display_name or "Unknown Bank"
        return f"<EstrattoConto bank='{bank}' transactions={len(self._data)}>"
```

---

## Phase 2: Mockup Generation with Docling

### Strategy for Mock Data Generation

**Goal**: Create realistic bank statement PDFs that can be parsed by docling for testing without real customer data.

### Step 2.1: Install Dependencies

```bash
# Add to pyproject.toml [tool.poetry.dev-dependencies]
reportlab = "^4.0.0"
faker = "^20.0.0"  # For generating realistic names/data
```

### Step 2.2: Create Advanced Mock Generator

**File**: `tests/mock_generators/advanced_mock.py`

```python
"""
Advanced mock bank statement generator with realistic data.
Uses Faker for realistic names and patterns.
"""
from datetime import datetime, timedelta
import random
from typing import List, Dict, Tuple
import pandas as pd
from faker import Faker

class BankStatementMockGenerator:
    """Generate realistic bank statement mock data"""

    def __init__(self, locale: str = 'it_IT'):
        """
        Initialize generator.

        Args:
            locale: Faker locale (default: it_IT for Italian names)
        """
        self.faker = Faker(locale)
        random.seed(42)  # Reproducible

    def generate_transactions(
        self,
        num_transactions: int,
        start_date: datetime,
        end_date: datetime,
        opening_balance: float = 10000.0
    ) -> Tuple[pd.DataFrame, float, float]:
        """
        Generate realistic transaction data with running balance.

        Args:
            num_transactions: Number of transactions to generate
            start_date: Start date for transactions
            end_date: End date for transactions
            opening_balance: Starting balance

        Returns:
            Tuple of (transactions_df, opening_balance, closing_balance)
        """
        transactions = []
        current_balance = opening_balance
        delta = end_date - start_date

        # Transaction templates with realistic patterns
        templates = [
            {
                'type': 'bill',
                'weight': 15,
                'generator': self._generate_bill,
            },
            {
                'type': 'incoming_transfer',
                'weight': 10,
                'generator': self._generate_incoming_transfer,
            },
            {
                'type': 'outgoing_transfer',
                'weight': 20,
                'generator': self._generate_outgoing_transfer,
            },
            {
                'type': 'card_payment',
                'weight': 30,
                'generator': self._generate_card_payment,
            },
            {
                'type': 'atm_withdrawal',
                'weight': 15,
                'generator': self._generate_atm_withdrawal,
            },
            {
                'type': 'bank_fee',
                'weight': 10,
                'generator': self._generate_bank_fee,
            },
        ]

        # Weighted random selection
        weights = [t['weight'] for t in templates]

        for i in range(num_transactions):
            # Random date within period
            random_days = random.randint(0, delta.days)
            txn_date = start_date + timedelta(days=random_days)

            # Select transaction type
            template = random.choices(templates, weights=weights)[0]

            # Generate transaction
            txn = template['generator'](txn_date)
            transactions.append(txn)

        # Sort by date
        transactions.sort(key=lambda x: datetime.strptime(x['DATA MOV.'], '%d/%m/%Y'))

        # Convert to DataFrame
        df = pd.DataFrame(transactions)

        # Calculate closing balance
        closing_balance = current_balance
        if 'DARE' in df.columns:
            closing_balance -= df['DARE'].apply(self._parse_amount).sum()
        if 'AVERE' in df.columns:
            closing_balance += df['AVERE'].apply(self._parse_amount).sum()

        return df, opening_balance, closing_balance

    def _generate_bill(self, date: datetime) -> Dict[str, str]:
        """Generate S.D.D. direct debit bill"""
        companies = [
            'ENEL ENERGIA SPA',
            'ENI GAS E LUCE',
            'TIM SPA',
            'VODAFONE ITALIA',
            'A2A ENERGIA',
            'ACQUE VERONESI',
            'HERA SPA',
        ]
        company = random.choice(companies)
        amount = round(random.uniform(30, 200), 2)
        mandate_id = f"IT{random.randint(10000, 99999)}"

        return {
            'DATA MOV.': date.strftime('%d/%m/%Y'),
            'VALUTA': date.strftime('%d/%m/%Y'),
            'DARE': self._format_amount(amount),
            'AVERE': '',
            'DESCRIZIONE OPERAZIONE': f'S.D.D. ADDEBITO CRED. {company} ID.MANDATO {mandate_id} RIF. {date.strftime("%Y%m")}'
        }

    def _generate_incoming_transfer(self, date: datetime) -> Dict[str, str]:
        """Generate incoming wire transfer"""
        sender = self.faker.name()
        amount = round(random.uniform(100, 5000), 2)
        reasons = [
            'Rimborso',
            'Pagamento fattura',
            'Regalo',
            'Affitto',
            'Stipendio',
            'Consulenza',
        ]
        reason = random.choice(reasons)

        return {
            'DATA MOV.': date.strftime('%d/%m/%Y'),
            'VALUTA': date.strftime('%d/%m/%Y'),
            'DARE': '',
            'AVERE': self._format_amount(amount),
            'DESCRIZIONE OPERAZIONE': f'BONIFICO A VS. FAVORE Ordinante: {sender.upper()} Causale: {reason}'
        }

    def _generate_outgoing_transfer(self, date: datetime) -> Dict[str, str]:
        """Generate outgoing wire transfer"""
        recipient = self.faker.name()
        amount = round(random.uniform(50, 2000), 2)
        reasons = [
            'Pagamento',
            'Affitto',
            'Spesa',
            'Regalo',
            'Consulenza',
        ]
        reason = random.choice(reasons)

        return {
            'DATA MOV.': date.strftime('%d/%m/%Y'),
            'VALUTA': date.strftime('%d/%m/%Y'),
            'DARE': self._format_amount(amount),
            'AVERE': '',
            'DESCRIZIONE OPERAZIONE': f'BONIFICO coordinate benef {recipient.upper()} Causale: {reason}'
        }

    def _generate_card_payment(self, date: datetime) -> Dict[str, str]:
        """Generate card payment"""
        merchants = [
            'ESSELUNGA',
            'CONAD',
            'AMAZON EU',
            'IKEA ITALIA',
            'DECATHLON',
            'H&M',
            'ZARA',
            'MEDIAWORLD',
        ]
        merchant = random.choice(merchants)
        amount = round(random.uniform(5, 300), 2)

        return {
            'DATA MOV.': date.strftime('%d/%m/%Y'),
            'VALUTA': (date + timedelta(days=1)).strftime('%d/%m/%Y'),
            'DARE': self._format_amount(amount),
            'AVERE': '',
            'DESCRIZIONE OPERAZIONE': f'PAGAMENTO CARTA DI CREDITO {merchant} {date.strftime("%d/%m/%Y")}'
        }

    def _generate_atm_withdrawal(self, date: datetime) -> Dict[str, str]:
        """Generate ATM withdrawal"""
        amounts = [20, 50, 100, 150, 200]
        amount = random.choice(amounts)

        return {
            'DATA MOV.': date.strftime('%d/%m/%Y'),
            'VALUTA': date.strftime('%d/%m/%Y'),
            'DARE': self._format_amount(amount),
            'AVERE': '',
            'DESCRIZIONE OPERAZIONE': f'PRELIEVO ATM FILIALE {random.randint(1, 50):03d}'
        }

    def _generate_bank_fee(self, date: datetime) -> Dict[str, str]:
        """Generate bank fee"""
        fees = [
            ('CANONE MENSILE CONTO CORRENTE', 8.50),
            ('COMMISSIONI GESTIONE CONTO', 2.00),
            ('SPESE TENUTA CONTO', 5.00),
            ('IMPOSTA DI BOLLO', 34.20),
        ]
        description, amount = random.choice(fees)

        return {
            'DATA MOV.': date.strftime('%d/%m/%Y'),
            'VALUTA': date.strftime('%d/%m/%Y'),
            'DARE': self._format_amount(amount),
            'AVERE': '',
            'DESCRIZIONE OPERAZIONE': description
        }

    @staticmethod
    def _format_amount(amount: float) -> str:
        """Format amount in Italian banking format"""
        # Format: + 1.234,56 € or - 1.234,56 €
        formatted = f"{amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"+ {formatted} €" if amount > 0 else f"- {formatted} €"

    @staticmethod
    def _parse_amount(amount_str: str) -> float:
        """Parse Italian banking format to float"""
        if not isinstance(amount_str, str) or amount_str == '':
            return 0.0
        # Remove symbols and convert
        clean = amount_str.replace('€', '').replace('+', '').replace(' ', '').strip()
        clean = clean.replace('.', '').replace(',', '.')
        return abs(float(clean))
```

### Step 2.3: Create Docling-Compatible PDF Generator

**File**: `tests/mock_generators/pdf_generator.py`

```python
"""
Generate PDF bank statements compatible with docling parsing.
Uses ReportLab to create structured tables that docling can extract.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from typing import Dict
import pandas as pd

class DoclingCompatiblePDFGenerator:
    """
    Generate PDFs optimized for docling table extraction.

    Docling works best with:
    - Clear table borders
    - Consistent cell padding
    - No merged cells in data tables
    - Clear text hierarchy
    """

    def __init__(self, bank_name: str, bank_logo_text: str):
        self.bank_name = bank_name
        self.bank_logo_text = bank_logo_text
        self.styles = getSampleStyleSheet()

        # Custom styles
        self.title_style = ParagraphStyle(
            'BankTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#003366'),
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        )

        self.header_style = ParagraphStyle(
            'SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#003366'),
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )

    def generate_statement(
        self,
        output_path: str,
        account_info: Dict[str, str],
        transactions: pd.DataFrame,
        period: str,
        opening_balance: str,
        closing_balance: str,
        total_credit: str = '',
        total_debit: str = ''
    ):
        """
        Generate bank statement PDF compatible with docling.

        Args:
            output_path: Output PDF path
            account_info: Dict with account information
            transactions: DataFrame with transaction data
            period: Statement period
            opening_balance: Opening balance (Italian format)
            closing_balance: Closing balance (Italian format)
            total_credit: Total credits (optional)
            total_debit: Total debits (optional)
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            topMargin=2*cm,
            bottomMargin=2*cm,
            leftMargin=2*cm,
            rightMargin=2*cm
        )

        story = []

        # Bank logo/name (important for detection)
        title = Paragraph(self.bank_logo_text, self.title_style)
        story.append(title)
        story.append(Spacer(1, 1*cm))

        # Document title
        doc_title = Paragraph(
            f"<b>ESTRATTO CONTO</b><br/><font size=12>{period}</font>",
            self.header_style
        )
        story.append(doc_title)
        story.append(Spacer(1, 0.5*cm))

        # Table 0: Book balance (period information)
        story.append(Paragraph("<b>Periodo di riferimento</b>", self.styles['Heading3']))
        story.append(Spacer(1, 0.3*cm))

        book_balance_data = [
            ['Periodo', period],
        ]
        book_balance_table = self._create_simple_table(book_balance_data)
        story.append(book_balance_table)
        story.append(Spacer(1, 0.8*cm))

        # Table 1: Account information
        story.append(Paragraph("<b>Informazioni conto</b>", self.styles['Heading3']))
        story.append(Spacer(1, 0.3*cm))

        account_data = [[k, v] for k, v in account_info.items()]
        account_table = self._create_simple_table(account_data)
        story.append(account_table)
        story.append(Spacer(1, 0.8*cm))

        # Tables 2 to n-1: Transaction data (split if needed)
        story.append(Paragraph("<b>Movimenti del conto</b>", self.styles['Heading3']))
        story.append(Spacer(1, 0.3*cm))

        # Split transactions into multiple tables if many rows (to match real bank behavior)
        max_rows_per_table = 25
        for i in range(0, len(transactions), max_rows_per_table):
            chunk = transactions.iloc[i:i+max_rows_per_table]
            txn_table = self._create_transaction_table(chunk)
            story.append(txn_table)
            story.append(Spacer(1, 0.5*cm))

        # Table n: Balance summary
        story.append(Paragraph("<b>Riepilogo saldi</b>", self.styles['Heading3']))
        story.append(Spacer(1, 0.3*cm))

        balance_data = [
            ['Saldo iniziale', opening_balance],
            ['Saldo finale', closing_balance],
        ]
        if total_credit:
            balance_data.append(['Totale accrediti', total_credit])
        if total_debit:
            balance_data.append(['Totale addebiti', total_debit])

        balance_table = self._create_simple_table(balance_data)
        story.append(balance_table)

        # Build PDF
        doc.build(story)

    def _create_simple_table(self, data: list) -> Table:
        """Create a simple 2-column table for metadata"""
        table = Table(data, colWidths=[6*cm, 10*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8E8E8')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return table

    def _create_transaction_table(self, transactions: pd.DataFrame) -> Table:
        """Create transaction table with header row"""
        # Convert DataFrame to table data
        header = transactions.columns.tolist()
        rows = transactions.values.tolist()
        data = [header] + rows

        # Column widths
        col_widths = [2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 7*cm]

        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (3, -1), 'CENTER'),  # Date and amount columns
            ('ALIGN', (4, 1), (4, -1), 'LEFT'),    # Description column

            # All cells
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),

            # Alternating row colors for readability
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ]))

        return table
```

### Step 2.4: Create CLI Command for Mock Generation

**File**: `estrattoconto/cli.py` (add commands)

```python
import click
from pathlib import Path

# ... existing imports ...

@click.group()
def mock():
    """Generate mock bank statement data for testing"""
    pass

@mock.command('generate')
@click.option('--bank', default='CENTROVENETO', help='Bank type to generate')
@click.option('--transactions', '-n', default=30, help='Number of transactions')
@click.option('--output', '-o', required=True, help='Output PDF path')
@click.option('--start-date', default='01/01/2025', help='Period start (DD/MM/YYYY)')
@click.option('--end-date', default='31/01/2025', help='Period end (DD/MM/YYYY)')
def generate_mock(bank: str, transactions: int, output: str, start_date: str, end_date: str):
    """
    Generate a mock bank statement PDF.

    Example:
        estrattoconto mock generate --bank CENTROVENETO -n 50 -o mock.pdf
    """
    try:
        from datetime import datetime
        from tests.mock_generators.advanced_mock import BankStatementMockGenerator
        from tests.mock_generators.pdf_generator import DoclingCompatiblePDFGenerator

        # Parse dates
        start = datetime.strptime(start_date, '%d/%m/%Y')
        end = datetime.strptime(end_date, '%d/%m/%Y')

        # Generate transaction data
        click.echo(f"Generating {transactions} transactions for {bank}...")
        mock_gen = BankStatementMockGenerator(locale='it_IT')
        txn_df, opening, closing = mock_gen.generate_transactions(
            num_transactions=transactions,
            start_date=start,
            end_date=end
        )

        # Bank-specific configuration
        bank_configs = {
            'CENTROVENETO': {
                'name': 'CENTROVENETO',
                'logo': 'BANCA VENETO CENTRALE',
                'iban': 'IT60X0542811101000000123456'
            },
            'INTESA': {
                'name': 'INTESA',
                'logo': 'INTESA SANPAOLO',
                'iban': 'IT40S0306909606100000012345'
            },
            'UNICREDIT': {
                'name': 'UNICREDIT',
                'logo': 'UNICREDIT BANCA',
                'iban': 'IT10X0200805319000400123456'
            }
        }

        config = bank_configs.get(bank, bank_configs['CENTROVENETO'])

        # Generate PDF
        click.echo("Generating PDF...")
        pdf_gen = DoclingCompatiblePDFGenerator(
            bank_name=config['name'],
            bank_logo_text=config['logo']
        )

        account_info = {
            'IBAN': config['iban'],
            'Intestatario': 'MARIO ROSSI',
            'Filiale': 'TREVISO 001'
        }

        pdf_gen.generate_statement(
            output_path=output,
            account_info=account_info,
            transactions=txn_df,
            period=f"{start_date} - {end_date}",
            opening_balance=mock_gen._format_amount(opening),
            closing_balance=mock_gen._format_amount(closing)
        )

        click.echo(f"✓ Mock PDF generated: {output}")
        click.echo(f"  Bank: {config['logo']}")
        click.echo(f"  Transactions: {len(txn_df)}")
        click.echo(f"  Opening balance: {mock_gen._format_amount(opening)}")
        click.echo(f"  Closing balance: {mock_gen._format_amount(closing)}")

    except ImportError as e:
        click.echo(f"Error: Missing dependency: {e}", err=True)
        click.echo("Install with: pip install reportlab faker", err=True)
    except Exception as e:
        click.echo(f"Error generating mock: {e}", err=True)
        raise

@mock.command('test')
@click.argument('pdf_path')
def test_mock(pdf_path: str):
    """
    Test parsing a mock PDF with estrattoconto.

    Example:
        estrattoconto mock test mock.pdf
    """
    try:
        from estrattoconto import convert

        click.echo(f"Testing mock PDF: {pdf_path}")
        statement = convert(pdf_path)

        click.echo(f"\n✓ Successfully parsed!")
        click.echo(f"  Bank: {statement.provider_display_name}")
        click.echo(f"  Transactions: {len(statement)}")

        summary = statement.summary()
        for key, value in summary.items():
            click.echo(f"  {key}: {value}")

    except Exception as e:
        click.echo(f"✗ Error parsing mock: {e}", err=True)
        raise

# Add mock group to main CLI
cli.add_command(mock)
```

### Usage Examples

```bash
# Generate mock CENTROVENETO statement with 50 transactions
estrattoconto mock generate --bank CENTROVENETO -n 50 -o test_centro.pdf

# Generate mock INTESA statement
estrattoconto mock generate --bank INTESA -n 30 -o test_intesa.pdf

# Test parsing the generated mock
estrattoconto mock test test_centro.pdf

# Convert and analyze
estrattoconto extract test_centro.pdf --output transactions.csv
```

---

## Phase 3: Adding New Bank Providers

### Template for New Provider

**File**: `estrattoconto/providers/template.py`

```python
"""
Provider template for adding new banks.

Copy this file and replace:
- BANKNAME with actual bank code (e.g., INTESA)
- Bank Display Name with full name
- Detection string
- Table structure logic
- Regex patterns
- Column mappings
"""
import re
from typing import Dict
from docling_core.types.doc import DoclingDocument, TableItem
import pandas as pd

from .base import BankProvider, BankTables, EnrichmentPatterns

class BankNameProvider(BankProvider):
    """Provider for [Bank Display Name] statements"""

    @property
    def name(self) -> str:
        return "BANKNAME"  # TODO: Change to bank code

    @property
    def display_name(self) -> str:
        return "Bank Display Name"  # TODO: Change to full bank name

    def detect(self, docling_doc: DoclingDocument) -> bool:
        """
        Detect [BANKNAME] by scanning for bank identifier.

        TODO: Update detection string to match bank's PDF header
        """
        for text in docling_doc.texts:
            if "BANK IDENTIFIER STRING" in text.text.upper():
                return True
        return False

    def extract_tables(self, docling_doc: DoclingDocument) -> BankTables:
        """
        Extract tables following [BANKNAME] structure.

        TODO: Analyze sample PDF to determine table structure:
        - Which table contains account info?
        - Which tables contain transactions?
        - Which table contains balance summary?
        """
        tables = [item for item in docling_doc.tables if isinstance(item, TableItem)]

        if len(tables) < 2:
            raise ValueError(f"Expected at least 2 tables, found {len(tables)}")

        # TODO: Adjust indices based on actual bank structure
        book_balance = self._table_to_df(tables[0])
        account_info = self._table_to_df(tables[1])
        balance_summary = self._table_to_df(tables[-1])

        # TODO: Identify which tables contain transactions
        transaction_dfs = [self._table_to_df(t) for t in tables[2:-1]]
        transactions = pd.concat(transaction_dfs, ignore_index=True) if transaction_dfs else pd.DataFrame()

        return BankTables(
            book_balance=book_balance,
            account_information=account_info,
            balance_summary=balance_summary,
            transactions=transactions
        )

    def get_enrichment_patterns(self) -> EnrichmentPatterns:
        """
        Return [BANKNAME]-specific regex patterns.

        TODO: Analyze transaction descriptions to create patterns for:
        - Payer extraction (from incoming transfers)
        - Payee extraction (from direct debits)
        - Mandate ID extraction (from direct debits)
        - Bill detection (keywords)
        - Transfer detection (keywords)
        - Bank fee detection (keywords)
        """
        return EnrichmentPatterns(
            payer_pattern=re.compile(r'TODO: Pattern for payer', re.IGNORECASE),
            payee_pattern=re.compile(r'TODO: Pattern for payee', re.IGNORECASE),
            mandate_id_pattern=re.compile(r'TODO: Pattern for mandate ID', re.IGNORECASE),
            bill_pattern=re.compile(r'TODO: Keywords for bills', re.IGNORECASE),
            incoming_transfer_pattern=re.compile(r'TODO: Keywords for incoming transfer', re.IGNORECASE),
            outgoing_transfer_pattern=re.compile(r'TODO: Keywords for outgoing transfer', re.IGNORECASE),
            bank_fee_pattern=re.compile(r'TODO: Keywords for bank fees', re.IGNORECASE)
        )

    def get_column_mapping(self) -> Dict[str, str]:
        """
        Return [BANKNAME] column name mapping.

        TODO: Update column names to match bank's actual PDF column headers
        """
        return {
            'movement_date': 'TODO: Column name for movement date',
            'value_date': 'TODO: Column name for value date',
            'debit': 'TODO: Column name for debit',
            'credit': 'TODO: Column name for credit',
            'description': 'TODO: Column name for description'
        }

    @staticmethod
    def _table_to_df(table: TableItem) -> pd.DataFrame:
        """Convert TableItem to DataFrame"""
        return table.export_to_dataframe()
```

### Checklist for Adding New Bank

- [ ] Obtain sample PDF (anonymized)
- [ ] Analyze PDF structure with docling
- [ ] Identify detection string
- [ ] Map table indices
- [ ] Identify column names
- [ ] Extract transaction description patterns
- [ ] Create provider class
- [ ] Register provider
- [ ] Write unit tests
- [ ] Generate mock PDF
- [ ] Update documentation

---

## Testing Roadmap

### Test Structure

```
tests/
├── fixtures/
│   ├── centroveneto.pdf (gitignored)
│   ├── intesa.pdf (gitignored)
│   ├── mock_centroveneto.pdf
│   └── mock_intesa.pdf
├── mock_generators/
│   ├── __init__.py
│   ├── advanced_mock.py
│   └── pdf_generator.py
├── test_providers.py          # Provider system tests
├── test_centroveneto.py       # CENTROVENETO-specific tests
├── test_intesa.py             # Intesa-specific tests (future)
├── test_mock_generation.py    # Mock generator tests
└── test_integration.py        # End-to-end tests
```

### Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=estrattoconto --cov-report=html

# Test specific provider
pytest tests/test_centroveneto.py

# Test mock generation
pytest tests/test_mock_generation.py

# Test with real PDFs (requires fixtures)
pytest tests/test_integration.py
```

---

## Documentation Roadmap

1. **API Reference** - Auto-generate with Sphinx
2. **Provider Guide** - How to add new banks
3. **Mockup Guide** - How to generate test data
4. **Migration Guide** - Upgrading from v0.1.x
5. **Examples** - Usage examples for each bank

---

## Deployment Checklist

### Version 0.2.0 - Multi-Bank Support

- [ ] Phase 1 implementation complete
- [ ] Phase 2 mock generation working
- [ ] At least 2 banks supported
- [ ] All tests passing (>90% coverage)
- [ ] Documentation updated
- [ ] CHANGELOG.md written
- [ ] Examples updated
- [ ] PyPI package published

---

*Document Version: 1.0*
*Last Updated: 2026-01-18*
