"""
estrattoconto: Italian bank statement PDF extractor and enricher.

This package provides tools to extract transaction data from Italian bank
statement PDFs and enrich them with semantic information and classifications.

Main API (Object-Oriented):
    import estrattoconto
    statement = estrattoconto.convert('bank_statement.pdf')
    statement.to_csv('output.csv')

Legacy API (Functional):
    from estrattoconto import extract_table, enrich_data
    tables = extract_table('bank_statement.pdf')
    enriched = enrich_data(tables)
"""

from .__version__ import __version__
from .statement import EstrattoConto

# Functional API (backward compatibility)
from .converter import extract_table, extract_document_type, extract_data_tables
from .enrichment import enrich_data, postprocess_extraction
from .utils import clean_and_convert_currency
from .config import CENTROVENETO, UNSUPPORTED


# Main convenience function for object-oriented API
def convert(pdf_path: str) -> EstrattoConto:
    """
    Convert a PDF bank statement to an EstrattoConto object.

    This is the main entry point for the object-oriented API.

    Args:
        pdf_path: Path to the PDF bank statement file

    Returns:
        EstrattoConto object with enriched transaction data

    Example:
        >>> import estrattoconto
        >>> statement = estrattoconto.convert('bank_statement.pdf')
        >>> statement.to_csv('transactions.csv')
        >>> payers = statement.extract_payers()
    """
    return EstrattoConto.from_pdf(pdf_path)


__all__ = [
    # Version
    "__version__",
    # Object-Oriented API (Primary)
    "EstrattoConto",
    "convert",
    # Functional API (Legacy/Advanced)
    "extract_table",
    "extract_document_type",
    "extract_data_tables",
    "enrich_data",
    "postprocess_extraction",
    "clean_and_convert_currency",
    # Constants
    "CENTROVENETO",
    "UNSUPPORTED",
]
