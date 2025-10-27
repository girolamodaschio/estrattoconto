# estrattoconto


deploy as docker image to fix pytorch issues on mac intel. image should receive a pdf encoded in base64 and return appropriate json structure
evaluate using docling serve instead of building docling straightaway

A Python library for extracting and enriching transaction data from Italian bank statement PDFs (estratto conto).

## Features

- **PDF Extraction**: Converts bank statement PDFs into structured DataFrames using docling
- **Automatic Bank Detection**: Identifies bank type by scanning document content
- **Transaction Enrichment**: Extracts entities (payer, payee, mandate IDs) from transaction descriptions
- **Transaction Classification**: Automatically categorizes transactions (bills, transfers, fees)
- **Currency Conversion**: Handles Italian currency format (1.234,56 → 1234.56)
- **CLI Support**: Command-line interface for quick extractions

Currently supports:
- Banca del Veneto Centrale (CENTROVENETO)

## Installation

### From source

```bash
git clone https://github.com/girolamodaschio/estrattoconto.git
cd estrattoconto
poetry install
```

## Usage

### Command Line Interface

Extract transactions from a bank statement PDF:

```bash
estrattoconto extract path/to/statement.pdf
```

Save output to CSV:

```bash
estrattoconto extract path/to/statement.pdf --output transactions.csv
```

### Python API (Object-Oriented)

The recommended way to use estrattoconto is through the object-oriented API:

```python
import estrattoconto

# Convert PDF to EstrattoConto object
statement = estrattoconto.convert('bank_statement.pdf')

# Export to various formats
statement.to_csv('transactions.csv')
statement.to_json('transactions.json')
statement.to_excel('transactions.xlsx')

# Query transaction data
payers = statement.extract_payers()
payees = statement.extract_payees()

# Filter by transaction type
bills = statement.get_bills()
incoming_transfers = statement.get_incoming_transfers()
outgoing_transfers = statement.get_outgoing_transfers()
fees = statement.get_fees()

# Filter by date range
january_transactions = statement.filter_by_date('01/01/2025', '31/01/2025')

# Get summary statistics
summary = statement.summary()
print(f"Total transactions: {summary['total_transactions']}")
print(f"Total bills: {summary['total_bills']}")

# Access underlying DataFrame if needed
df = statement.get_dataframe()
```

### Legacy API (Functional)

For advanced use cases, the functional API is still available:

```python
from estrattoconto import extract_table, enrich_data

# Extract tables from PDF
book_balance, account_info, balance_summary, transactions = extract_table('statement.pdf')

# Enrich transaction data
enriched_df = enrich_data((book_balance, account_info, balance_summary, transactions))

# Access enriched data
print(enriched_df[['DATA MOV.', 'amount', 'payer', 'payee', 'is_bill']])
```

### Enriched Data Columns

The enriched DataFrame includes:

- **Original columns**: DATA MOV., VALUTA, DARE, AVERE, DESCRIZIONE OPERAZIONE
- **Extracted entities**: payer, payee, id_mandato
- **Numeric amounts**: DARE_Numeric, AVERE_Numeric, amount (combined)
- **Classification flags**: is_bill, is_incoming_transfer, is_outcoming_transfer, is_bank_fee
- **Metadata**: related_account, period

### Examples

For complete working examples, see the [examples/](examples/) directory:

```bash
# Run the basic usage example
python examples/basic_usage.py

# Or with Poetry
poetry run python examples/basic_usage.py
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/girolamodaschio/estrattoconto.git
cd estrattoconto

# Install dependencies (including dev dependencies)
poetry install

# Activate virtual environment
poetry shell
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=estrattoconto

# Run specific test file
poetry run pytest tests/test_converter.py
```

### Code Quality

```bash
# Format code
poetry run black src/ tests/

# Lint code
poetry run ruff check src/ tests/
poetry run pylint src/estrattoconto

# Type checking
poetry run mypy src/estrattoconto
```

### Running Linting (CI)

```bash
poetry run pylint $(git ls-files '*.py')
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Adding Support for New Banks

See [CLAUDE.md](CLAUDE.md) for detailed instructions on adding support for additional bank formats.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Requirements

- Python 3.10+
- pandas
- numpy
- docling

## Roadmap

- [ ] Support for additional Italian banks
- [ ] Export to SQL/Django ORM models
- [ ] Transaction categorization using ML
- [ ] Web interface for PDF upload
- [ ] Batch processing support

## Acknowledgments

Built with [docling](https://github.com/DS4SD/docling) for PDF document conversion.
