# Hybrid Approaches: Making Docling Faster

**Goal:** Achieve 10-100x speedup by avoiding docling when possible

## Overview

Docling is powerful but slow because it performs sophisticated layout analysis and table structure recognition. The hybrid approach uses fast methods (pdfplumber, templates) for 80% of cases and falls back to docling only when necessary.

**Key Insight:** Not all PDFs need docling's heavy machinery. Bank statements are semi-structured with predictable layouts.

---

## Approach 1: Fast Preprocessing + Selective Docling

**Speedup:** 10-50x for simple PDFs
**Implementation Complexity:** Medium
**Accuracy:** 95-100%

### Strategy

1. Try fast extraction with pdfplumber first
2. Validate the results
3. Fall back to docling if validation fails

### Implementation

#### estrattoconto/extractors/__init__.py

```python
"""Extraction engine that chooses optimal method."""

from .fast import FastExtractor
from .docling import DoclingExtractor
from .hybrid import HybridExtractor

__all__ = ['HybridExtractor', 'FastExtractor', 'DoclingExtractor']
```

#### estrattoconto/extractors/fast.py

```python
"""Fast extraction using pdfplumber."""

import pdfplumber
import pandas as pd
from typing import Tuple, Optional
from ..providers.base import BankTables


class FastExtractor:
    """Fast PDF extraction using pdfplumber."""

    def extract(self, pdf_path: str) -> Tuple[Optional[BankTables], bool]:
        """
        Try fast extraction.

        Returns:
            (BankTables, success) tuple
            success=True if extraction worked and validated
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                all_tables = []

                for page in pdf.pages:
                    # Extract tables (much faster than docling)
                    tables = page.extract_tables()

                    for table in tables:
                        if table and len(table) > 1:
                            df = pd.DataFrame(table[1:], columns=table[0])
                            all_tables.append(df)

                if not all_tables:
                    return None, False

                # Combine all tables
                combined_df = pd.concat(all_tables, ignore_index=True)

                # Validate
                if self._validate_extraction(combined_df):
                    # Convert to BankTables format
                    tables = self._to_bank_tables(combined_df)
                    return tables, True

                return None, False

        except Exception as e:
            print(f"Fast extraction failed: {e}")
            return None, False

    def _validate_extraction(self, df: pd.DataFrame) -> bool:
        """
        Validate that fast extraction produced good results.

        This is crucial - bad fast extraction is worse than slow correct extraction.
        """
        # Check 1: Must have expected columns
        expected_cols = ['DATA MOV.', 'VALUTA', 'DARE', 'AVERE', 'DESCRIZIONE OPERAZIONE']
        if not all(col in df.columns for col in expected_cols):
            return False

        # Check 2: Must have some data
        if len(df) < 3:
            return False

        # Check 3: Amount columns should contain currency or numbers
        dare_valid = df['DARE'].astype(str).str.contains('€|\\d').sum()
        if dare_valid < len(df) * 0.3:  # At least 30% valid
            return False

        # Check 4: Dates should be parseable
        try:
            dates = pd.to_datetime(
                df['DATA MOV.'].head(5),
                format='%d/%m/%Y',
                errors='coerce'
            )
            if dates.isna().all():
                return False
        except:
            return False

        return True

    def _to_bank_tables(self, df: pd.DataFrame) -> BankTables:
        """
        Convert combined DataFrame to BankTables format.

        Note: Fast extraction doesn't separate tables like docling does.
        We create minimal BankTables with all data in transactions.
        """
        return BankTables(
            book_balance=pd.DataFrame(),  # Empty for fast extraction
            account_info=pd.DataFrame(),
            balance_summary=pd.DataFrame(),
            transactions=df
        )
```

#### estrattoconto/extractors/docling.py

```python
"""Standard docling extraction."""

from docling.document_converter import DocumentConverter
from ..providers.base import BankTables


class DoclingExtractor:
    """Standard docling extraction (slow but accurate)."""

    def __init__(self):
        self.converter = DocumentConverter()

    def extract(self, pdf_path: str) -> BankTables:
        """Extract using docling."""
        result = self.converter.convert(pdf_path)

        # Use provider system to extract tables
        from ..providers import detect_provider
        provider = detect_provider(result)

        if provider is None:
            raise ValueError("No provider found for document")

        return provider.extract_tables(result)
```

#### estrattoconto/extractors/hybrid.py

```python
"""Hybrid extractor that tries fast then falls back to docling."""

import time
from typing import Tuple
from .fast import FastExtractor
from .docling import DoclingExtractor
from ..providers.base import BankTables


class HybridExtractor:
    """
    Intelligent extractor that chooses the best method.

    Decision tree:
    1. Try fast extraction (pdfplumber)
    2. If validation passes → use fast result
    3. If validation fails → fall back to docling
    """

    def __init__(self):
        self.fast_extractor = FastExtractor()
        self.docling_extractor = DoclingExtractor()

        self.stats = {
            'fast': 0,
            'docling': 0,
            'fast_time': 0.0,
            'docling_time': 0.0,
        }

    def extract(self, pdf_path: str) -> Tuple[BankTables, str, float]:
        """
        Extract with best method.

        Returns:
            (BankTables, method_used, elapsed_time)
        """
        # Try fast extraction
        start_time = time.time()
        tables, success = self.fast_extractor.extract(pdf_path)
        fast_time = time.time() - start_time

        if success:
            self.stats['fast'] += 1
            self.stats['fast_time'] += fast_time
            print(f"✓ Fast extraction succeeded ({fast_time:.2f}s)")
            return tables, 'fast', fast_time

        # Fall back to docling
        print("⚠ Fast extraction failed, falling back to docling...")
        start_time = time.time()
        tables = self.docling_extractor.extract(pdf_path)
        docling_time = time.time() - start_time

        self.stats['docling'] += 1
        self.stats['docling_time'] += docling_time
        print(f"✓ Docling extraction succeeded ({docling_time:.2f}s)")

        return tables, 'docling', docling_time

    def print_stats(self):
        """Print extraction statistics."""
        total = self.stats['fast'] + self.stats['docling']
        if total == 0:
            print("No extractions yet")
            return

        fast_pct = (self.stats['fast'] / total) * 100
        avg_fast = self.stats['fast_time'] / max(self.stats['fast'], 1)
        avg_docling = self.stats['docling_time'] / max(self.stats['docling'], 1)

        print("\n=== Extraction Statistics ===")
        print(f"Fast extractions: {self.stats['fast']} ({fast_pct:.1f}%)")
        print(f"  Average time: {avg_fast:.2f}s")
        print(f"Docling extractions: {self.stats['docling']} ({100-fast_pct:.1f}%)")
        print(f"  Average time: {avg_docling:.2f}s")

        if self.stats['fast'] > 0:
            speedup = avg_docling / avg_fast
            print(f"Fast extraction speedup: {speedup:.1f}x")
```

### Integration

Update `converter.py`:

```python
from .extractors import HybridExtractor

_hybrid_extractor = HybridExtractor()

def extract_table(pdf_path: str, use_hybrid: bool = True):
    """Extract tables using hybrid approach."""
    if use_hybrid:
        tables, method, elapsed = _hybrid_extractor.extract(pdf_path)
        return tables
    else:
        # Use standard docling
        from .extractors import DoclingExtractor
        return DoclingExtractor().extract(pdf_path)
```

### Testing

```python
# tests/test_hybrid.py
import unittest
from estrattoconto.extractors import HybridExtractor

class TestHybrid(unittest.TestCase):
    def test_fast_extraction_fallback(self):
        extractor = HybridExtractor()

        # Should try fast, fall back to docling for complex PDF
        tables, method, time = extractor.extract('complex.pdf')

        self.assertIn(method, ['fast', 'docling'])
        self.assertIsNotNone(tables)
        self.assertGreater(time, 0)
```

### Acceptance Criteria
- [ ] FastExtractor implemented
- [ ] DoclingExtractor wrapped
- [ ] HybridExtractor with fallback logic
- [ ] Validation functions comprehensive
- [ ] Integration with converter
- [ ] Tests added
- [ ] Statistics tracking

---

## Approach 2: Template-Based Extraction

**Speedup:** 50-100x
**Implementation Complexity:** High (requires templates)
**Accuracy:** 98-100%

### Strategy

For known bank formats, use predefined coordinate-based extraction. Bypass docling's layout analysis entirely.

### Implementation

#### estrattoconto/extractors/template.py

```python
"""Template-based extraction using coordinates."""

import pdfplumber
import pandas as pd
from typing import Dict, Optional, Tuple
from ..providers.base import BankTables


class TemplateExtractor:
    """Extract using predefined templates (very fast)."""

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict:
        """
        Load coordinate templates for known banks.

        Templates define exact pixel coordinates for table regions.
        """
        return {
            'CENTROVENETO': {
                'identifier': 'BANCA VENETO CENTRALE',
                'transaction_region': {
                    'x0': 50,   # left edge
                    'y0': 150,  # top edge
                    'x1': 550,  # right edge
                    'y1': 750,  # bottom edge
                },
                'columns': {
                    'DATA MOV.': (50, 110),
                    'VALUTA': (110, 150),
                    'DESCRIZIONE OPERAZIONE': (150, 350),
                    'DARE': (350, 420),
                    'AVERE': (420, 490),
                },
                'skip_pages': [0, -1],  # First and last pages
            },
            # Add more banks...
        }

    def can_extract(self, pdf_path: str) -> Tuple[bool, Optional[str]]:
        """
        Check if template extraction is available for this PDF.

        Returns:
            (can_extract, bank_name) tuple
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                first_page_text = pdf.pages[0].extract_text()

                for bank, template in self.templates.items():
                    if template['identifier'] in first_page_text:
                        return True, bank

            return False, None
        except:
            return False, None

    def extract(self, pdf_path: str, bank_name: str = None) -> Optional[BankTables]:
        """
        Extract using template.

        Args:
            pdf_path: Path to PDF
            bank_name: Optional bank name (auto-detect if None)

        Returns:
            BankTables or None if failed
        """
        if bank_name is None:
            can_extract, bank_name = self.can_extract(pdf_path)
            if not can_extract:
                return None

        template = self.templates.get(bank_name)
        if template is None:
            return None

        try:
            return self._extract_with_template(pdf_path, template)
        except Exception as e:
            print(f"Template extraction failed: {e}")
            return None

    def _extract_with_template(self, pdf_path: str, template: Dict) -> BankTables:
        """Extract using predefined coordinates."""
        all_rows = []

        with pdfplumber.open(pdf_path) as pdf:
            pages_to_process = [
                i for i in range(len(pdf.pages))
                if i not in template.get('skip_pages', [])
            ]

            for page_idx in pages_to_process:
                page = pdf.pages[page_idx]

                # Crop to transaction region
                bbox = template['transaction_region']
                crop = page.within_bbox((bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1']))

                # Extract with column hints
                table_settings = {
                    "vertical_strategy": "explicit",
                    "horizontal_strategy": "explicit",
                    "explicit_vertical_lines": self._get_column_lines(template),
                    "intersection_tolerance": 5
                }

                table = crop.extract_table(table_settings)

                if table:
                    all_rows.extend(table)

        # Convert to DataFrame
        if all_rows and len(all_rows) > 1:
            df = pd.DataFrame(all_rows[1:], columns=all_rows[0])

            return BankTables(
                book_balance=pd.DataFrame(),
                account_info=pd.DataFrame(),
                balance_summary=pd.DataFrame(),
                transactions=df
            )

        return None

    def _get_column_lines(self, template: Dict) -> list:
        """Get vertical line positions for columns."""
        bbox = template['transaction_region']
        columns = template['columns']

        lines = [bbox['x0']]  # Left edge

        for col_name, (x0, x1) in columns.items():
            lines.extend([x0, x1])

        lines.append(bbox['x1'])  # Right edge

        return sorted(set(lines))  # Remove duplicates and sort

    def learn_template_interactive(self, pdf_path: str) -> Dict:
        """
        Interactive tool to create templates.

        Opens PDF and allows user to mark regions.
        """
        # TODO: Implement interactive template creation
        # Could use matplotlib or a web interface
        raise NotImplementedError("Interactive template learning not yet implemented")
```

### Enhanced Hybrid with Templates

```python
# Update extractors/hybrid.py
class EnhancedHybridExtractor:
    """Hybrid with template support."""

    def __init__(self):
        self.template_extractor = TemplateExtractor()
        self.fast_extractor = FastExtractor()
        self.docling_extractor = DoclingExtractor()

    def extract(self, pdf_path: str) -> Tuple[BankTables, str, float]:
        """
        Extract with best method.

        Priority:
        1. Template (if available) - fastest
        2. Fast extraction (pdfplumber) - fast
        3. Docling - slow but reliable
        """
        # Try template first
        can_use_template, bank_name = self.template_extractor.can_extract(pdf_path)

        if can_use_template:
            start = time.time()
            tables = self.template_extractor.extract(pdf_path, bank_name)
            elapsed = time.time() - start

            if tables is not None:
                print(f"✓ Template extraction ({elapsed:.2f}s)")
                return tables, 'template', elapsed

        # Try fast extraction
        start = time.time()
        tables, success = self.fast_extractor.extract(pdf_path)
        elapsed = time.time() - start

        if success:
            print(f"✓ Fast extraction ({elapsed:.2f}s)")
            return tables, 'fast', elapsed

        # Fall back to docling
        start = time.time()
        tables = self.docling_extractor.extract(pdf_path)
        elapsed = time.time() - start

        print(f"✓ Docling extraction ({elapsed:.2f}s)")
        return tables, 'docling', elapsed
```

### Acceptance Criteria
- [ ] TemplateExtractor implemented
- [ ] Template format defined
- [ ] At least 1 template created (CENTROVENETO)
- [ ] Integration with enhanced hybrid
- [ ] Template learning tool (optional)
- [ ] Tests added

---

## Approach 3: Page-Level Selective Processing

**Speedup:** 3-5x
**Implementation Complexity:** Medium
**Accuracy:** 100%

### Strategy

Quickly classify page types, then only process transaction pages with docling.

### Implementation

#### estrattoconto/extractors/selective.py

```python
"""Selective page processing."""

import pdfplumber
from typing import List
from docling.document_converter import DocumentConverter


class SelectiveProcessor:
    """Process only relevant pages."""

    def classify_pages(self, pdf_path: str) -> List[str]:
        """
        Classify each page type without heavy processing.

        Returns:
            List of page types: ['header', 'transactions', 'summary']
        """
        page_types = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""

                # Simple heuristics
                if page_num == 0 and "ESTRATTO CONTO" in text:
                    page_types.append('header')
                elif "SALDO CONTABILE" in text and page_num == len(pdf.pages) - 1:
                    page_types.append('summary')
                elif self._looks_like_transactions(page, text):
                    page_types.append('transactions')
                else:
                    page_types.append('other')

        return page_types

    def _looks_like_transactions(self, page, text: str) -> bool:
        """Quick check if page has transaction table."""
        # Check for table-like structures
        tables = page.find_tables()
        if not tables:
            return False

        # Check for transaction keywords
        keywords = ['DATA MOV.', 'VALUTA', 'DARE', 'AVERE']
        return sum(kw in text for kw in keywords) >= 3

    def extract_selective(self, pdf_path: str) -> BankTables:
        """
        Extract by processing only transaction pages.

        This requires docling to support page-level processing.
        """
        # Classify pages
        page_types = self.classify_pages(pdf_path)
        transaction_pages = [
            i for i, ptype in enumerate(page_types)
            if ptype == 'transactions'
        ]

        print(f"Processing {len(transaction_pages)}/{len(page_types)} pages")

        # Process only transaction pages
        # Note: This requires splitting PDF or docling page support
        # Implementation depends on docling API

        # Placeholder: Process full document but skip analysis on non-transaction pages
        converter = DocumentConverter()
        result = converter.convert(pdf_path)

        # Extract tables only from relevant pages
        # This is a simplified version - actual implementation needs refinement

        from ..providers import detect_provider
        provider = detect_provider(result)

        if provider:
            return provider.extract_tables(result)

        raise ValueError("No provider found")
```

### Acceptance Criteria
- [ ] Page classification implemented
- [ ] Selective processing logic
- [ ] Integration with hybrid system
- [ ] Performance benchmarks
- [ ] Tests added

---

## Performance Comparison

### Benchmark Results (Expected)

| Method | Speed | Accuracy | Use Case |
|--------|-------|----------|----------|
| Pure docling | 8-12s | 100% | Complex/unknown PDFs |
| + Caching | 0.01s | 100% | Repeat processing |
| + Fast (pdfplumber) | 0.5-1s | 95-98% | Clean simple PDFs |
| + Template | 0.1-0.3s | 99-100% | Known formats |
| + Selective | 3-5s | 100% | Multi-page statements |
| **Enhanced Hybrid** | **0.1-8s** | **98-100%** | **Best overall** |

### Expected Distribution

With enhanced hybrid:
- 20% via templates (0.1-0.3s)
- 50% via fast extraction (0.5-1s)
- 20% via selective docling (3-5s)
- 10% via full docling (8-12s)

**Average speedup: 20-30x**

---

## Implementation Priority

### Phase 1 (Week 1)
- [ ] Fast extraction with pdfplumber
- [ ] Basic hybrid with fallback
- [ ] Integration and testing

### Phase 2 (Week 2)
- [ ] Template system design
- [ ] Create CENTROVENETO template
- [ ] Enhanced hybrid

### Phase 3 (Week 3)
- [ ] Page-level classification
- [ ] Selective processing
- [ ] Performance benchmarking

---

## Configuration

Allow users to configure extraction preferences:

```python
# estrattoconto/config.py
EXTRACTION_CONFIG = {
    'prefer_speed': True,  # Use fast methods when possible
    'prefer_accuracy': False,  # Always use docling
    'use_templates': True,  # Enable template extraction
    'use_cache': True,  # Enable caching
    'min_confidence': 0.95,  # Minimum validation confidence
}
```

---

## Testing Strategy

```python
# tests/test_performance.py
import time
import unittest

class TestPerformance(unittest.TestCase):
    def test_extraction_speed(self):
        """Benchmark extraction methods."""
        pdf = 'tests/fixture/sample.pdf'

        # Docling baseline
        start = time.time()
        # ... extract with docling
        docling_time = time.time() - start

        # Hybrid
        start = time.time()
        # ... extract with hybrid
        hybrid_time = time.time() - start

        speedup = docling_time / hybrid_time
        print(f"Speedup: {speedup:.1f}x")

        self.assertGreater(speedup, 2.0)  # At least 2x faster
```

---

**Next:** Integrate with [Phase 3 Performance](phase-3-performance.md)
