# Phase 3: Performance Optimization

**Priority:** HIGH
**Duration:** 4-7 days
**Impact:** VERY HIGH - 10-100x speedup

## Overview

Implement multiple performance optimization strategies to achieve dramatic speedups. The hybrid approach combines caching, fast extraction methods, selective processing, async support, and batch operations.

**Expected Results:**
- Instant processing for cached PDFs
- 10-50x faster for simple PDFs (with fast extraction)
- 3-5x faster for complex PDFs (with selective processing)
- Non-blocking processing for Django/web apps (with async)

---

## Task 3.1: Implement Caching System

### Overview

**Impact:** VERY HIGH - Instant for repeated processing
**Duration:** 1-2 days

File-hash based caching to avoid reprocessing the same PDF twice.

### Implementation

#### estrattoconto/cache.py (new file)

```python
"""Caching system for PDF processing results."""

import hashlib
import pickle
import json
from pathlib import Path
from typing import Optional, Any, Dict
from datetime import datetime
import pandas as pd


class CacheManager:
    """
    Multi-level cache manager for estrattoconto.

    Caches:
    - Level 1: Docling conversion results (document structure)
    - Level 2: Extracted tables (raw data)
    - Level 3: Enriched data (final result)
    """

    def __init__(self, cache_dir: str = ".estrattoconto_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)

        # Cache subdirectories
        self.docling_cache = self.cache_dir / "docling"
        self.tables_cache = self.cache_dir / "tables"
        self.enriched_cache = self.cache_dir / "enriched"
        self.metadata_cache = self.cache_dir / "metadata"

        for cache in [self.docling_cache, self.tables_cache,
                     self.enriched_cache, self.metadata_cache]:
            cache.mkdir(exist_ok=True)

    def _hash_file(self, pdf_path: str) -> str:
        """
        Generate SHA256 hash of file content.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Hexadecimal hash string
        """
        hasher = hashlib.sha256()

        with open(pdf_path, 'rb') as f:
            # Read in chunks for memory efficiency
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)

        return hasher.hexdigest()

    def get_enriched(self, pdf_path: str) -> Optional[pd.DataFrame]:
        """
        Get cached enriched data.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Cached DataFrame or None
        """
        file_hash = self._hash_file(pdf_path)
        cache_path = self.enriched_cache / f"{file_hash}.pkl"

        if cache_path.exists():
            try:
                return pickle.load(cache_path.open('rb'))
            except Exception as e:
                print(f"Warning: Failed to load cache: {e}")
                return None

        return None

    def save_enriched(self, pdf_path: str, data: pd.DataFrame) -> None:
        """
        Save enriched data to cache.

        Args:
            pdf_path: Path to PDF file
            data: Enriched DataFrame to cache
        """
        file_hash = self._hash_file(pdf_path)
        cache_path = self.enriched_cache / f"{file_hash}.pkl"

        try:
            pickle.dump(data, cache_path.open('wb'))
            self._save_metadata(pdf_path, file_hash, 'enriched')
        except Exception as e:
            print(f"Warning: Failed to save cache: {e}")

    def get_tables(self, pdf_path: str):
        """Get cached table extraction results."""
        file_hash = self._hash_file(pdf_path)
        cache_path = self.tables_cache / f"{file_hash}.pkl"

        if cache_path.exists():
            try:
                return pickle.load(cache_path.open('rb'))
            except Exception:
                return None

        return None

    def save_tables(self, pdf_path: str, tables) -> None:
        """Save table extraction results to cache."""
        file_hash = self._hash_file(pdf_path)
        cache_path = self.tables_cache / f"{file_hash}.pkl"

        try:
            pickle.dump(tables, cache_path.open('wb'))
            self._save_metadata(pdf_path, file_hash, 'tables')
        except Exception as e:
            print(f"Warning: Failed to save cache: {e}")

    def _save_metadata(self, pdf_path: str, file_hash: str, cache_type: str) -> None:
        """Save cache metadata for tracking."""
        metadata = {
            'original_path': str(pdf_path),
            'file_hash': file_hash,
            'cache_type': cache_type,
            'cached_at': datetime.now().isoformat(),
            'file_size': Path(pdf_path).stat().st_size,
        }

        meta_path = self.metadata_cache / f"{file_hash}.json"
        with meta_path.open('w') as f:
            json.dump(metadata, f, indent=2)

    def invalidate(self, pdf_path: str) -> None:
        """
        Invalidate all cache entries for a PDF.

        Args:
            pdf_path: Path to PDF file
        """
        file_hash = self._hash_file(pdf_path)

        for cache_dir in [self.docling_cache, self.tables_cache,
                         self.enriched_cache, self.metadata_cache]:
            for cached_file in cache_dir.glob(f"{file_hash}*"):
                cached_file.unlink()

    def clear_all(self) -> None:
        """Clear entire cache."""
        import shutil
        shutil.rmtree(self.cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.__init__(str(self.cache_dir))

    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        def dir_size(directory: Path) -> int:
            return sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())

        def file_count(directory: Path) -> int:
            return len(list(directory.glob('*.pkl')))

        total_size = dir_size(self.cache_dir)

        return {
            'total_size_mb': total_size / (1024 * 1024),
            'docling_cached': file_count(self.docling_cache),
            'tables_cached': file_count(self.tables_cache),
            'enriched_cached': file_count(self.enriched_cache),
            'cache_directory': str(self.cache_dir),
        }

    def print_stats(self) -> None:
        """Print cache statistics."""
        stats = self.stats()
        print("\n=== Cache Statistics ===")
        print(f"Cache directory: {stats['cache_directory']}")
        print(f"Total size: {stats['total_size_mb']:.2f} MB")
        print(f"Docling results cached: {stats['docling_cached']}")
        print(f"Tables cached: {stats['tables_cached']}")
        print(f"Enriched data cached: {stats['enriched_cached']}")


# Global cache instance
_global_cache = None


def get_cache(cache_dir: str = None) -> CacheManager:
    """Get or create global cache manager."""
    global _global_cache

    if _global_cache is None:
        _global_cache = CacheManager(cache_dir or ".estrattoconto_cache")

    return _global_cache
```

### Integration

Update `converter.py` to use cache:

```python
from .cache import get_cache

def extract_table(pdf_path: str, use_cache: bool = True):
    """Extract tables with caching support."""
    cache = get_cache()

    if use_cache:
        # Check cache first
        cached_tables = cache.get_tables(pdf_path)
        if cached_tables is not None:
            print("✓ Cache hit - using cached tables")
            return cached_tables

    # ... existing extraction logic ...

    if use_cache:
        cache.save_tables(pdf_path, tables)

    return tables
```

Update `statement.py`:

```python
@classmethod
def from_pdf(cls, pdf_path: str, use_cache: bool = True):
    """Create from PDF with caching support."""
    cache = get_cache()

    if use_cache:
        cached_data = cache.get_enriched(pdf_path)
        if cached_data is not None:
            print("✓ Cache hit - using cached enriched data")
            return cls(cached_data)

    # Process normally
    tables = extract_table(pdf_path, use_cache=use_cache)
    enriched_data = enrich_data(tables)

    if use_cache:
        cache.save_enriched(pdf_path, enriched_data)

    return cls(enriched_data)
```

### CLI Integration

Add cache management commands:

```python
# __main__.py
parser.add_argument('--no-cache', action='store_true', help='Disable caching')
parser.add_argument('--clear-cache', action='store_true', help='Clear cache and exit')
parser.add_argument('--cache-stats', action='store_true', help='Show cache stats and exit')

if args.clear_cache:
    get_cache().clear_all()
    print("✓ Cache cleared")
    sys.exit(0)

if args.cache_stats:
    get_cache().print_stats()
    sys.exit(0)

statement = convert(args.pdf_path, use_cache=not args.no_cache)
```

### Testing

```python
# tests/test_cache.py
import unittest
from estrattoconto.cache import CacheManager
import pandas as pd
import tempfile

class TestCache(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache = CacheManager(self.temp_dir)

    def test_hash_file(self):
        # Create temp PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'test content')
            pdf_path = f.name

        hash1 = self.cache._hash_file(pdf_path)
        hash2 = self.cache._hash_file(pdf_path)
        self.assertEqual(hash1, hash2)

    def test_save_and_get_enriched(self):
        df = pd.DataFrame({'a': [1, 2, 3]})

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'test')
            pdf_path = f.name

        self.cache.save_enriched(pdf_path, df)
        cached = self.cache.get_enriched(pdf_path)

        pd.testing.assert_frame_equal(df, cached)

    def test_cache_miss(self):
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'test')
            pdf_path = f.name

        cached = self.cache.get_enriched(pdf_path)
        self.assertIsNone(cached)

    def test_invalidate(self):
        df = pd.DataFrame({'a': [1, 2, 3]})

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'test')
            pdf_path = f.name

        self.cache.save_enriched(pdf_path, df)
        self.assertIsNotNone(self.cache.get_enriched(pdf_path))

        self.cache.invalidate(pdf_path)
        self.assertIsNone(self.cache.get_enriched(pdf_path))
```

### Acceptance Criteria
- [ ] CacheManager implemented
- [ ] Integration with converter and statement
- [ ] CLI commands for cache management
- [ ] Tests added
- [ ] Documentation updated

---

## Task 3.2: Implement Async Support

### Overview

**Impact:** HIGH - Non-blocking for web apps
**Duration:** 2-3 days

Add async/await support for Django and web integration.

### Implementation

See [hybrid-approaches.md](hybrid-approaches.md) for detailed async implementation.

Quick summary:

```python
# estrattoconto/async_api.py (new file)
import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Optional
from .statement import EstrattoConto

async def convert_async(
    pdf_path: str,
    use_cache: bool = True,
    progress_callback = None
) -> EstrattoConto:
    """
    Async version of convert().

    Args:
        pdf_path: Path to PDF
        use_cache: Use caching
        progress_callback: Optional callback for progress updates

    Returns:
        EstrattoConto instance
    """
    loop = asyncio.get_event_loop()

    with ProcessPoolExecutor() as pool:
        if progress_callback:
            await progress_callback(0.1, "Starting conversion...")

        result = await loop.run_in_executor(
            pool,
            EstrattoConto.from_pdf,
            pdf_path,
            use_cache
        )

        if progress_callback:
            await progress_callback(1.0, "Complete")

        return result
```

### Acceptance Criteria
- [ ] Async API implemented
- [ ] Progress callback support
- [ ] ProcessPoolExecutor for CPU-bound work
- [ ] Examples for Django added
- [ ] Tests added

---

## Task 3.3: Implement Batch Processing

### Overview

**Impact:** MEDIUM - Parallel processing
**Duration:** 1-2 days

Process multiple PDFs in parallel.

### Implementation

```python
# estrattoconto/batch.py (new file)
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Callable, Optional
from pathlib import Path
from tqdm import tqdm
from .statement import EstrattoConto

def batch_process(
    pdf_paths: List[str],
    max_workers: int = 4,
    use_cache: bool = True,
    progress_bar: bool = True
) -> Dict[str, EstrattoConto]:
    """
    Process multiple PDFs in parallel.

    Args:
        pdf_paths: List of PDF file paths
        max_workers: Maximum parallel workers
        use_cache: Use caching
        progress_bar: Show progress bar

    Returns:
        Dictionary mapping PDF path to EstrattoConto instance
    """
    results = {}
    errors = {}

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_path = {
            executor.submit(EstrattoConto.from_pdf, path, use_cache): path
            for path in pdf_paths
        }

        # Process results as they complete
        iterator = as_completed(future_to_path)
        if progress_bar:
            iterator = tqdm(iterator, total=len(pdf_paths), desc="Processing PDFs")

        for future in iterator:
            pdf_path = future_to_path[future]
            try:
                result = future.result()
                results[pdf_path] = result
            except Exception as e:
                errors[pdf_path] = str(e)
                if progress_bar:
                    print(f"\n✗ Failed: {pdf_path}: {e}")

    if errors:
        print(f"\n✗ Failed to process {len(errors)}/{len(pdf_paths)} PDFs")
        for path, error in errors.items():
            print(f"  - {path}: {error}")

    return results
```

### CLI Integration

```bash
# Add batch command
estrattoconto batch *.pdf --output-dir ./results/
```

### Acceptance Criteria
- [ ] batch.py implemented
- [ ] Progress bar with tqdm
- [ ] Error handling for partial failures
- [ ] CLI batch command
- [ ] Tests added

---

## Summary Checklist

Phase 3 complete when:

- [ ] Caching system implemented and tested
- [ ] Async API implemented
- [ ] Batch processing implemented
- [ ] All integrated with existing code
- [ ] CLI commands added
- [ ] Tests passing
- [ ] Performance benchmarks documented

---

## Performance Benchmarks

Document expected performance:

```python
# benchmarks/performance.py
import time
from estrattoconto import convert

def benchmark():
    # First run (no cache)
    start = time.time()
    convert('sample.pdf', use_cache=False)
    no_cache_time = time.time() - start

    # Second run (with cache)
    start = time.time()
    convert('sample.pdf', use_cache=True)
    cache_time = time.time() - start

    print(f"Without cache: {no_cache_time:.2f}s")
    print(f"With cache: {cache_time:.2f}s")
    print(f"Speedup: {no_cache_time/cache_time:.1f}x")
```

---

**Next:** [Hybrid Approaches](hybrid-approaches.md) for advanced optimizations
