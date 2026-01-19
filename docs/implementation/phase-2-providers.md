# Phase 2: Multi-Provider Architecture

**Priority:** HIGH
**Duration:** 3-5 days
**Impact:** VERY HIGH - Enables extensibility

## Overview

Transform estrattoconto from a single-bank tool to a multi-provider system where new banks can be added without modifying core code. This phase establishes the foundation for scaling to support all major Italian banks.

---

## Architecture Design

### Current Problem

All bank-specific logic is hardcoded throughout the codebase:
- Bank detection in `converter.py`
- Table structure assumptions in `converter.py`
- Regex patterns in `enrichment.py`
- No abstraction layer

Adding a new bank requires modifying multiple files and understanding the entire codebase.

### Solution: Provider Pattern

Implement the Provider pattern with:
1. **Abstract base class** defining the interface
2. **Provider registry** for automatic discovery
3. **Individual providers** for each bank
4. **Configuration system** for provider settings

---

## Task 2.1: Create Provider Base Class

### File Structure

```
estrattoconto/
├── providers/
│   ├── __init__.py           # Registry and exports
│   ├── base.py               # Abstract base class
│   ├── centroveneto.py       # CENTROVENETO provider
│   └── README.md             # Provider development guide
```

### Implementation

#### estrattoconto/providers/base.py

```python
"""Base class for bank statement providers."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import pandas as pd
from docling.document_converter import ConversionResult


@dataclass
class BankTables:
    """Container for extracted bank statement tables."""
    book_balance: pd.DataFrame
    account_info: pd.DataFrame
    balance_summary: pd.DataFrame
    transactions: pd.DataFrame

    def __repr__(self) -> str:
        return (
            f"BankTables("
            f"book_balance={len(self.book_balance)} rows, "
            f"account_info={len(self.account_info)} rows, "
            f"balance_summary={len(self.balance_summary)} rows, "
            f"transactions={len(self.transactions)} rows)"
        )


@dataclass
class ProviderMetadata:
    """Metadata about a provider."""
    name: str
    bank_name: str
    version: str
    description: str
    supported_formats: List[str]
    author: str
    confidence_threshold: float = 0.8

    def __repr__(self) -> str:
        return f"ProviderMetadata(name={self.name}, bank={self.bank_name}, version={self.version})"


class BankStatementProvider(ABC):
    """
    Abstract base class for bank statement providers.

    Each provider handles a specific bank's statement format.
    Providers are responsible for:
    1. Detecting if they can handle a document
    2. Extracting tables from the document
    3. Enriching transaction data with bank-specific logic
    """

    @property
    @abstractmethod
    def metadata(self) -> ProviderMetadata:
        """
        Provider metadata.

        Returns:
            ProviderMetadata with name, version, etc.
        """
        pass

    @abstractmethod
    def detect(self, document: ConversionResult) -> float:
        """
        Detect if this provider can handle the document.

        Args:
            document: Converted document from docling

        Returns:
            Confidence score (0.0 to 1.0)
            - 0.0: Cannot handle
            - 0.5: Uncertain
            - 1.0: Definitely can handle

        Example:
            >>> provider = CentroVenetoProvider()
            >>> confidence = provider.detect(converted_doc)
            >>> if confidence > 0.8:
            >>>     print("High confidence this is CENTROVENETO")
        """
        pass

    @abstractmethod
    def extract_tables(self, document: ConversionResult) -> BankTables:
        """
        Extract tables from document.

        Args:
            document: Converted document from docling

        Returns:
            BankTables with extracted data

        Raises:
            ValueError: If document structure is unexpected
            RuntimeError: If extraction fails
        """
        pass

    @abstractmethod
    def enrich_data(self, tables: BankTables) -> pd.DataFrame:
        """
        Enrich transaction data with bank-specific logic.

        Expected enrichment columns:
        - payer: Entity making payment
        - payee: Entity receiving payment
        - id_mandato: Mandate ID (for SEPA Direct Debit)
        - is_bill: Boolean flag for bill payments
        - is_incoming_transfer: Boolean flag for incoming transfers
        - is_outcoming_transfer: Boolean flag for outgoing transfers
        - is_bank_fee: Boolean flag for bank fees
        - amount: Combined numeric amount (AVERE - DARE)
        - DARE_Numeric: Numeric debit amount
        - AVERE_Numeric: Numeric credit amount

        Args:
            tables: Extracted tables

        Returns:
            Enriched DataFrame with additional columns

        Raises:
            ValueError: If tables are invalid
        """
        pass

    def validate_tables(self, tables: BankTables) -> List[str]:
        """
        Validate extracted tables (optional override).

        Args:
            tables: Extracted tables to validate

        Returns:
            List of validation warnings (empty if all good)
        """
        warnings = []

        if tables.transactions.empty:
            warnings.append("No transactions found")

        return warnings

    def get_config_schema(self) -> Dict[str, Any]:
        """
        Get configuration schema for this provider (optional override).

        Returns:
            JSON schema for provider configuration
        """
        return {}
```

### Acceptance Criteria
- [ ] base.py created with abstract base class
- [ ] BankTables dataclass defined
- [ ] ProviderMetadata dataclass defined
- [ ] All abstract methods documented with examples
- [ ] Type hints for all methods

---

## Task 2.2: Create Provider Registry

### Implementation

#### estrattoconto/providers/__init__.py

```python
"""Provider registry and exports."""

from typing import Optional, List, Type, Dict
from docling.document_converter import ConversionResult
from .base import BankStatementProvider, BankTables, ProviderMetadata


class ProviderRegistry:
    """
    Registry for bank statement providers.

    Manages provider discovery, registration, and selection.
    """

    def __init__(self):
        self._providers: List[BankStatementProvider] = []
        self._provider_cache: Dict[str, BankStatementProvider] = {}

    def register(self, provider: BankStatementProvider) -> None:
        """
        Register a provider.

        Args:
            provider: Provider instance to register
        """
        if not isinstance(provider, BankStatementProvider):
            raise TypeError(f"Expected BankStatementProvider, got {type(provider)}")

        self._providers.append(provider)
        print(f"✓ Registered provider: {provider.metadata.name}")

    def detect_provider(
        self,
        document: ConversionResult,
        min_confidence: float = 0.8
    ) -> Optional[BankStatementProvider]:
        """
        Automatically detect which provider can handle the document.

        Args:
            document: Converted document from docling
            min_confidence: Minimum confidence threshold (0.0 to 1.0)

        Returns:
            Provider with highest confidence, or None if no match

        Example:
            >>> registry = ProviderRegistry()
            >>> registry.register(CentroVenetoProvider())
            >>> provider = registry.detect_provider(document)
            >>> if provider:
            >>>     tables = provider.extract_tables(document)
        """
        best_provider = None
        best_confidence = 0.0

        for provider in self._providers:
            confidence = provider.detect(document)

            if confidence > best_confidence:
                best_confidence = confidence
                best_provider = provider

        if best_confidence >= min_confidence:
            print(
                f"✓ Detected provider: {best_provider.metadata.name} "
                f"(confidence: {best_confidence:.2%})"
            )
            return best_provider
        else:
            print(
                f"✗ No provider found with confidence >= {min_confidence:.0%} "
                f"(best: {best_confidence:.2%})"
            )
            return None

    def get_provider_by_name(self, name: str) -> Optional[BankStatementProvider]:
        """
        Get provider by name.

        Args:
            name: Provider name

        Returns:
            Provider instance or None
        """
        for provider in self._providers:
            if provider.metadata.name == name:
                return provider
        return None

    def list_providers(self) -> List[ProviderMetadata]:
        """
        List all registered providers.

        Returns:
            List of provider metadata
        """
        return [provider.metadata for provider in self._providers]

    def clear(self) -> None:
        """Clear all registered providers."""
        self._providers.clear()
        self._provider_cache.clear()


# Global registry instance
_global_registry = ProviderRegistry()


def register_provider(provider: BankStatementProvider) -> None:
    """Register a provider with the global registry."""
    _global_registry.register(provider)


def get_registry() -> ProviderRegistry:
    """Get the global provider registry."""
    return _global_registry


def detect_provider(
    document: ConversionResult,
    min_confidence: float = 0.8
) -> Optional[BankStatementProvider]:
    """Detect provider using global registry."""
    return _global_registry.detect_provider(document, min_confidence)


# Exports
__all__ = [
    'BankStatementProvider',
    'BankTables',
    'ProviderMetadata',
    'ProviderRegistry',
    'register_provider',
    'get_registry',
    'detect_provider',
]
```

### Testing

#### tests/test_providers.py

```python
"""Tests for provider registry."""

import unittest
from unittest.mock import Mock
from estrattoconto.providers import (
    ProviderRegistry,
    BankStatementProvider,
    ProviderMetadata,
    BankTables
)


class MockProvider(BankStatementProvider):
    """Mock provider for testing."""

    def __init__(self, name: str, confidence: float):
        self._name = name
        self._confidence = confidence

    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self._name,
            bank_name="Mock Bank",
            version="1.0.0",
            description="Test provider",
            supported_formats=["PDF"],
            author="Test"
        )

    def detect(self, document) -> float:
        return self._confidence

    def extract_tables(self, document) -> BankTables:
        return BankTables(
            book_balance=Mock(),
            account_info=Mock(),
            balance_summary=Mock(),
            transactions=Mock()
        )

    def enrich_data(self, tables: BankTables):
        return Mock()


class TestProviderRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = ProviderRegistry()

    def test_register_provider(self):
        provider = MockProvider("test", 1.0)
        self.registry.register(provider)
        self.assertEqual(len(self.registry._providers), 1)

    def test_detect_provider_high_confidence(self):
        provider = MockProvider("test", 0.95)
        self.registry.register(provider)

        mock_doc = Mock()
        detected = self.registry.detect_provider(mock_doc, min_confidence=0.8)

        self.assertIsNotNone(detected)
        self.assertEqual(detected.metadata.name, "test")

    def test_detect_provider_low_confidence(self):
        provider = MockProvider("test", 0.5)
        self.registry.register(provider)

        mock_doc = Mock()
        detected = self.registry.detect_provider(mock_doc, min_confidence=0.8)

        self.assertIsNone(detected)

    def test_detect_provider_best_match(self):
        provider1 = MockProvider("low", 0.6)
        provider2 = MockProvider("high", 0.95)
        provider3 = MockProvider("medium", 0.8)

        self.registry.register(provider1)
        self.registry.register(provider2)
        self.registry.register(provider3)

        mock_doc = Mock()
        detected = self.registry.detect_provider(mock_doc, min_confidence=0.5)

        self.assertEqual(detected.metadata.name, "high")

    def test_get_provider_by_name(self):
        provider = MockProvider("test", 1.0)
        self.registry.register(provider)

        found = self.registry.get_provider_by_name("test")
        self.assertIsNotNone(found)
        self.assertEqual(found.metadata.name, "test")

    def test_list_providers(self):
        self.registry.register(MockProvider("test1", 1.0))
        self.registry.register(MockProvider("test2", 1.0))

        providers = self.registry.list_providers()
        self.assertEqual(len(providers), 2)
```

### Acceptance Criteria
- [ ] ProviderRegistry class implemented
- [ ] Global registry instance created
- [ ] Provider detection working
- [ ] Tests for registry added
- [ ] All tests passing

---

## Task 2.3: Refactor CENTROVENETO into Provider

### Implementation

#### estrattoconto/providers/centroveneto.py

```python
"""Banca Veneto Centrale provider."""

import re
import pandas as pd
from docling.document_converter import ConversionResult
from .base import BankStatementProvider, BankTables, ProviderMetadata
from ..utils import clean_and_convert_currency


class CentroVenetoProvider(BankStatementProvider):
    """Provider for Banca Veneto Centrale bank statements."""

    # Bank identifier constant
    BANK_IDENTIFIER = "BANCA VENETO CENTRALE"

    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name="centroveneto",
            bank_name="Banca Veneto Centrale",
            version="1.0.0",
            description="Extract and enrich transaction data from Banca Veneto Centrale statements",
            supported_formats=["PDF"],
            author="estrattoconto",
            confidence_threshold=0.9
        )

    def detect(self, document: ConversionResult) -> float:
        """
        Detect CENTROVENETO by searching for bank identifier in document text.

        Returns:
            1.0 if identifier found, 0.0 otherwise
        """
        for el in document.document.texts:
            if self.BANK_IDENTIFIER in el.text:
                return 1.0

        return 0.0

    def extract_tables(self, document: ConversionResult) -> BankTables:
        """
        Extract tables from CENTROVENETO statement.

        Table structure:
        - Table 0: Book balance (period information)
        - Table 1: Account information
        - Tables 2 to n-1: Transaction data
        - Table n (last): Balance summary

        Args:
            document: Converted document from docling

        Returns:
            BankTables with extracted data

        Raises:
            ValueError: If document structure is unexpected
        """
        tables = document.document.tables

        if len(tables) < 4:
            raise ValueError(
                f"Expected at least 4 tables in CENTROVENETO statement, got {len(tables)}"
            )

        # Extract specific tables
        book_balance = self._extract_dataframe(tables[0])
        account_info = self._extract_dataframe(tables[1])
        balance_summary = self._extract_dataframe(tables[-1])

        # Combine transaction tables (all tables between account info and balance)
        transaction_tables = [
            self._extract_dataframe(table)
            for table in tables[2:-1]
        ]
        transactions = pd.concat(transaction_tables, ignore_index=True)

        return BankTables(
            book_balance=book_balance,
            account_info=account_info,
            balance_summary=balance_summary,
            transactions=transactions
        )

    def _extract_dataframe(self, table_item) -> pd.DataFrame:
        """Extract DataFrame from docling TableItem."""
        return table_item.export_to_dataframe()

    def enrich_data(self, tables: BankTables) -> pd.DataFrame:
        """
        Enrich CENTROVENETO transaction data.

        Extracts:
        - payer: From "Ordinante: ... Causale" pattern
        - payee: From "ADDEBITO CRED. ... ID.MANDATO" pattern
        - id_mandato: From "ID.MANDATO ... RIF./SDD" pattern

        Classifies:
        - is_bill: Contains "S.D.D." (SEPA Direct Debit)
        - is_incoming_transfer: Contains "BONIFICO A VS. FAVORE"
        - is_outcoming_transfer: Contains "BONIFICO coordinate benef"
        - is_bank_fee: Contains "CANONE" or "COMMISSIONI"

        Args:
            tables: Extracted tables

        Returns:
            Enriched DataFrame
        """
        df = tables.transactions.copy()

        # Filter and clean
        df = self._postprocess_extraction(df)

        # Extract entities with regex
        df['payer'] = df['DESCRIZIONE OPERAZIONE'].str.extract(
            r'Ordinante:\s*(.*?)\s*Causale',
            expand=False
        )

        df['payee'] = df['DESCRIZIONE OPERAZIONE'].str.extract(
            r'ADDEBITO CRED\.\s*(.*?)\s*ID\.MANDATO',
            expand=False
        )

        df['id_mandato'] = df['DESCRIZIONE OPERAZIONE'].str.extract(
            r'ID\.MANDATO\s*(.*?)\s*RIF\./SDD',
            expand=False
        )

        # Convert currency to numeric
        df['DARE_Numeric'] = clean_and_convert_currency(df['DARE'])
        df['AVERE_Numeric'] = clean_and_convert_currency(df['AVERE'])

        # Create combined amount column
        df['amount'] = (
            df['AVERE_Numeric'].fillna(0) -
            df['DARE_Numeric'].fillna(0)
        )

        # Transaction classification
        df['is_bill'] = df['DESCRIZIONE OPERAZIONE'].str.contains(
            'S.D.D.',
            case=False,
            na=False
        )

        df['is_incoming_transfer'] = df['DESCRIZIONE OPERAZIONE'].str.contains(
            'BONIFICO A VS. FAVORE',
            case=False,
            na=False
        )

        df['is_outcoming_transfer'] = df['DESCRIZIONE OPERAZIONE'].str.contains(
            'BONIFICO coordinate benef',
            case=False,
            na=False
        )

        df['is_bank_fee'] = df['DESCRIZIONE OPERAZIONE'].str.contains(
            'CANONE|COMMISSIONI',
            case=False,
            na=False
        )

        # Add metadata
        df['related_account'] = self._extract_account_number(tables.account_info)
        df['period'] = self._extract_period(tables.book_balance)

        return df

    def _postprocess_extraction(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter and clean extracted data.

        Removes:
        - Rows without all required columns
        - Rows with all NaN values
        """
        # Filter columns
        required_cols = ['DATA MOV.', 'VALUTA', 'DARE', 'AVERE', 'DESCRIZIONE OPERAZIONE']
        available_cols = [col for col in required_cols if col in df.columns]
        df = df[available_cols]

        # Remove rows with all NaN
        df = df.dropna(how='all')

        return df

    def _extract_account_number(self, account_info: pd.DataFrame) -> str:
        """Extract account number from account info table."""
        # Implementation depends on CENTROVENETO format
        # This is a placeholder
        return "UNKNOWN"

    def _extract_period(self, book_balance: pd.DataFrame) -> str:
        """Extract statement period from book balance table."""
        # Implementation depends on CENTROVENETO format
        # This is a placeholder
        return "UNKNOWN"
```

### Acceptance Criteria
- [ ] CentroVenetoProvider class created
- [ ] All abstract methods implemented
- [ ] Regex patterns moved from enrichment.py
- [ ] Table extraction logic moved from converter.py
- [ ] Tests for provider added
- [ ] Original functionality preserved

---

## Task 2.4: Update Core to Use Providers

### Update converter.py

```python
"""PDF extraction using docling with provider system."""

from docling.document_converter import DocumentConverter, ConversionResult
import pandas as pd
from .providers import detect_provider, get_registry, BankTables
from .providers.centroveneto import CentroVenetoProvider


# Register default providers on module import
def _register_default_providers():
    """Register built-in providers."""
    registry = get_registry()
    registry.register(CentroVenetoProvider())


_register_default_providers()


def extract_table(pdf_path: str) -> BankTables:
    """
    Extract tables from PDF bank statement using provider system.

    Args:
        pdf_path: Path to PDF file

    Returns:
        BankTables with extracted data

    Raises:
        FileNotFoundError: If PDF doesn't exist
        ValueError: If no provider can handle document
        RuntimeError: If extraction fails
    """
    from pathlib import Path

    # Validate file
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if pdf_file.suffix.lower() != '.pdf':
        raise ValueError(f"File must be a PDF, got: {pdf_file.suffix}")

    # Convert with docling
    try:
        converter = DocumentConverter()
        document: ConversionResult = converter.convert(source=pdf_path)
    except Exception as e:
        raise RuntimeError(f"Failed to convert PDF with docling: {e}") from e

    # Detect provider
    provider = detect_provider(document, min_confidence=0.8)

    if provider is None:
        raise ValueError(
            "No provider found for this document. "
            "Currently supported banks: Banca Veneto Centrale. "
            "Please check if this is a valid bank statement PDF."
        )

    # Extract tables using provider
    try:
        tables = provider.extract_tables(document)
    except Exception as e:
        raise RuntimeError(
            f"Failed to extract tables using {provider.metadata.name}: {e}"
        ) from e

    return tables


# Backward compatibility
def extract_document_type(converted_result: ConversionResult) -> str:
    """
    DEPRECATED: Use provider system instead.

    Detect document type for backward compatibility.
    """
    import warnings
    warnings.warn(
        "extract_document_type() is deprecated. Use provider system instead.",
        DeprecationWarning,
        stacklevel=2
    )

    provider = detect_provider(converted_result, min_confidence=0.8)
    if provider:
        return provider.metadata.bank_name
    return "Unsupported document"
```

### Update enrichment.py

```python
"""Data enrichment using provider system."""

import pandas as pd
from .providers import BankTables, detect_provider, get_registry


def enrich_data(tables: BankTables, provider_name: str = None) -> pd.DataFrame:
    """
    Enrich transaction data using provider system.

    Args:
        tables: Extracted tables
        provider_name: Optional provider name to use

    Returns:
        Enriched DataFrame

    Raises:
        ValueError: If no provider specified and cannot determine automatically
    """
    registry = get_registry()

    if provider_name:
        # Use specified provider
        provider = registry.get_provider_by_name(provider_name)
        if provider is None:
            raise ValueError(f"Provider not found: {provider_name}")
    else:
        # This is a limitation - we need the document to auto-detect
        # For now, use the first registered provider
        providers = registry.list_providers()
        if not providers:
            raise ValueError("No providers registered")
        provider = registry.get_provider_by_name(providers[0].name)

    return provider.enrich_data(tables)


# Keep old function for backward compatibility
def postprocess_extraction(df: pd.DataFrame) -> pd.DataFrame:
    """
    DEPRECATED: Provider handles this now.

    Kept for backward compatibility.
    """
    import warnings
    warnings.warn(
        "postprocess_extraction() is deprecated. Provider handles this.",
        DeprecationWarning,
        stacklevel=2
    )
    return df
```

### Acceptance Criteria
- [ ] converter.py updated to use provider system
- [ ] enrichment.py updated to use provider system
- [ ] Backward compatibility maintained
- [ ] Deprecation warnings added
- [ ] All tests passing

---

## Task 2.5: Update Public API

### Update statement.py

```python
from .providers import BankTables

class EstrattoConto:
    @classmethod
    def from_pdf(cls, pdf_path: str, provider_name: str = None) -> 'EstrattoConto':
        """
        Create EstrattoConto from PDF file.

        Args:
            pdf_path: Path to PDF file
            provider_name: Optional provider name (auto-detect if None)

        Returns:
            EstrattoConto instance

        Raises:
            FileNotFoundError: If PDF doesn't exist
            ValueError: If PDF is invalid or no provider found
        """
        tables = extract_table(pdf_path)
        enriched_data = enrich_data(tables, provider_name=provider_name)
        return cls(enriched_data)
```

### Update __init__.py

```python
# Provider system
from .providers import (
    BankStatementProvider,
    BankTables,
    ProviderMetadata,
    register_provider,
    get_registry,
)

__all__ = [
    # ... existing exports ...
    'BankStatementProvider',
    'BankTables',
    'ProviderMetadata',
    'register_provider',
    'get_registry',
]
```

### Acceptance Criteria
- [ ] Public API updated
- [ ] Provider system accessible from main module
- [ ] Documentation updated
- [ ] Examples updated

---

## Task 2.6: Documentation

### Create Provider Development Guide

#### estrattoconto/providers/README.md

```markdown
# Provider Development Guide

Learn how to add support for a new bank to estrattoconto.

## Quick Start

1. Create a new file in `estrattoconto/providers/yourbank.py`
2. Subclass `BankStatementProvider`
3. Implement required methods
4. Register your provider

## Example: Adding Intesa Sanpaolo

\`\`\`python
# estrattoconto/providers/intesa_sanpaolo.py

from .base import BankStatementProvider, BankTables, ProviderMetadata

class IntesaSanpaoloProvider(BankStatementProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name="intesa_sanpaolo",
            bank_name="Intesa Sanpaolo",
            version="1.0.0",
            description="Extract data from Intesa Sanpaolo statements",
            supported_formats=["PDF"],
            author="Your Name"
        )

    def detect(self, document) -> float:
        # Look for bank identifier
        for el in document.document.texts:
            if "INTESA SANPAOLO" in el.text.upper():
                return 1.0
        return 0.0

    def extract_tables(self, document) -> BankTables:
        # Extract tables based on Intesa's format
        tables = document.document.tables

        return BankTables(
            book_balance=tables[0].export_to_dataframe(),
            account_info=tables[1].export_to_dataframe(),
            balance_summary=tables[-1].export_to_dataframe(),
            transactions=pd.concat([
                t.export_to_dataframe() for t in tables[2:-1]
            ])
        )

    def enrich_data(self, tables: BankTables) -> pd.DataFrame:
        # Bank-specific enrichment logic
        df = tables.transactions.copy()

        # Add your extraction patterns
        df['payer'] = df['Description'].str.extract(r'From:\s*(.*?)$')
        # ... more enrichment ...

        return df
\`\`\`

## Register Provider

\`\`\`python
from estrattoconto import register_provider
from .intesa_sanpaolo import IntesaSanpaoloProvider

register_provider(IntesaSanpaoloProvider())
\`\`\`

## Testing Your Provider

\`\`\`python
import unittest
from estrattoconto.providers import ProviderRegistry
from .intesa_sanpaolo import IntesaSanpaoloProvider

class TestIntesaSanpaoloProvider(unittest.TestCase):
    def test_detection(self):
        provider = IntesaSanpaoloProvider()
        # Test with sample document
        # ...
\`\`\`

See existing providers for more examples.
```

### Update Main README

Add section on multi-provider support and how to add banks.

### Acceptance Criteria
- [ ] Provider development guide created
- [ ] README updated
- [ ] Examples added
- [ ] API documentation updated

---

## Summary Checklist

Phase 2 is complete when:

- [ ] Provider base class implemented
- [ ] Provider registry implemented
- [ ] CENTROVENETO refactored into provider
- [ ] Core updated to use provider system
- [ ] Public API updated
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Example of adding new provider provided

---

## Commands for Testing

```bash
# Run all tests
poetry run pytest -v

# Test specific provider
poetry run pytest tests/test_providers.py -v

# Test integration
poetry run pytest tests/test_converter.py -v

# Test CLI still works
poetry run estrattoconto extract tests/fixture/sample.pdf
```

---

**Next Phase:** [Phase 3: Performance Optimization](phase-3-performance.md)
