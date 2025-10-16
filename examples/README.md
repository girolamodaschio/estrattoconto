# Examples

This directory contains example scripts demonstrating how to use the estrattoconto package.

## Available Examples

### basic_usage.py

Demonstrates the core object-oriented API:
- Converting a PDF to an EstrattoConto object
- Extracting payers and payees
- Filtering by transaction type (bills, transfers, fees)
- Getting summary statistics
- Exporting to various formats

**Run it:**
```bash
python examples/basic_usage.py
```

**With Poetry:**
```bash
poetry run python examples/basic_usage.py
```

## Requirements

Make sure you have a test PDF file at `tests/fixture/centroveneto.pdf` or modify the path in the examples.

## Creating Your Own Examples

Feel free to create additional examples for specific use cases:
- `advanced_filtering.py` - Complex query patterns
- `batch_processing.py` - Processing multiple PDFs
- `data_analysis.py` - Analyzing transaction patterns
- `export_formats.py` - Different export options

All examples should follow the same pattern:
1. Import estrattoconto
2. Load/convert data
3. Demonstrate specific features
4. Include comments explaining each step
