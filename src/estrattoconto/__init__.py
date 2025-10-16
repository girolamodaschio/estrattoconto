"""
py-estrattoconto: Italian bank statement PDF extractor and enricher.

This package provides tools to extract transaction data from Italian bank
statement PDFs and enrich them with semantic information and classifications.
"""

from .__version__ import __version__
from .converter import extract_table, extract_document_type, extract_data_tables
from .enrichment import enrich_data, postprocess_extraction
from .utils import clean_and_convert_currency
from .config import CENTROVENETO, UNSUPPORTED

__all__ = [
    "__version__",
    "extract_table",
    "extract_document_type",
    "extract_data_tables",
    "enrich_data",
    "postprocess_extraction",
    "clean_and_convert_currency",
    "CENTROVENETO",
    "UNSUPPORTED",
]
