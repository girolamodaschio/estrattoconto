"""PDF extraction and table conversion module with performance optimizations."""

import logging
import multiprocessing
from typing import Union, Optional
import pandas as pd
from docling.document_converter import DocumentConverter, ConversionResult, PdfFormatOption
from docling.datamodel.document import TableItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice
from docling.backend.docling_parse_v2_backend import DoclingParseV2DocumentBackend

from .config import CENTROVENETO, UNSUPPORTED

# Configure logging
logger = logging.getLogger(__name__)

# Singleton instance for DocumentConverter to avoid expensive reinitialization
_converter_instance: Optional[DocumentConverter] = None


def get_converter() -> DocumentConverter:
    """
    Get or create a singleton DocumentConverter instance with optimized configuration.

    Performance optimizations:
    - DoclingParseV2DocumentBackend: 10x faster PDF loading
    - do_ocr=False: Digital bank statements don't need OCR (3-5x speedup)
    - TableFormerMode.FAST: Faster table extraction for structured tables
    - Multi-threading: Utilizes all CPU cores for parallel processing
    - Singleton pattern: Avoids expensive model reinitialization

    Returns:
        Configured DocumentConverter instance
    """
    global _converter_instance

    if _converter_instance is None:
        # Configure pipeline options for optimal performance with bank statements
        pipeline_options = PdfPipelineOptions(
            do_ocr=False,  # Bank statements are digital PDFs, no OCR needed
            do_table_structure=True,  # We need table extraction
            do_code_enrichment=False,  # No code blocks in bank statements
            do_picture_classification=False,  # No picture analysis needed
        )

        # Use FAST mode for table extraction (bank tables are well-structured)
        pipeline_options.table_structure_options.mode = TableFormerMode.FAST

        # Configure accelerator for multi-threaded processing
        pipeline_options.accelerator_options = AcceleratorOptions(
            num_threads=multiprocessing.cpu_count(),
            device=AcceleratorDevice.AUTO
        )

        # Create converter with optimized configuration
        _converter_instance = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=DoclingParseV2DocumentBackend  # 10x faster than default
                )
            }
        )

        logger.info("Initialized optimized DocumentConverter with DoclingParseV2DocumentBackend")

    return _converter_instance


def extract_document_type(docling_doc: ConversionResult) -> str:
    """
    Extract document type by scanning document text for bank identifiers.

    Args:
        docling_doc: Converted document from docling

    Returns:
        Bank type identifier string (e.g., CENTROVENETO) or UNSUPPORTED
    """
    # Check all text elements for bank identifier
    for t in docling_doc.document.texts:
        if str(t.text).__contains__(CENTROVENETO):
            return CENTROVENETO

    # Only return UNSUPPORTED if no match found in any text
    return UNSUPPORTED


def extract_data_tables(converted_file_tables: Union[TableItem, list[TableItem]]) -> pd.DataFrame:
    """
    Convert docling TableItem(s) to pandas DataFrame with optimized concatenation.

    Args:
        converted_file_tables: Single TableItem or list of TableItems

    Returns:
        Concatenated DataFrame from all tables
    """
    if isinstance(converted_file_tables, list):
        # Optimized: collect all DataFrames first, then concat once (O(n) instead of O(n²))
        dfs = [el.export_to_dataframe() for el in converted_file_tables]
        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    else:
        return converted_file_tables.export_to_dataframe()


def extract_table(source: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Extract and parse tables from bank statement PDF with optimized performance.

    Performance improvements:
    - Uses singleton DocumentConverter (avoids reinitialization)
    - DoclingParseV2DocumentBackend for 10x faster PDF loading
    - Disabled OCR for digital PDFs (3-5x speedup)
    - Fast table extraction mode
    - Multi-threaded processing

    Args:
        source: File path to PDF document

    Returns:
        Tuple of 4 DataFrames:
            - book_balance_df: Period and balance information
            - account_information_df: Account details
            - balance_summary_df: Summary of balances
            - data_tables_df: Transaction data

    Note:
        Returns empty DataFrames if document type is unsupported.
    """
    converter = get_converter()
    result = converter.convert(source)
    used_tables = result.document.tables
    document_type = extract_document_type(result)

    if document_type in [CENTROVENETO]:
        logger.info(f"Supported document type: {document_type}")
        book_balance = used_tables[0]
        account_information = used_tables[1]
        balance_summary = used_tables[len(used_tables)-1]
        data_tables = used_tables[2:len(used_tables)-1]

        book_balance_df = extract_data_tables(book_balance)
        account_information_df = extract_data_tables(account_information)
        balance_summary_df = extract_data_tables(balance_summary)
        data_tables_df = extract_data_tables(data_tables)

        return book_balance_df, account_information_df, balance_summary_df, data_tables_df
    else:
        logger.warning("Unsupported document type")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
