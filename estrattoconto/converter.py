"""PDF extraction and table conversion module."""

from typing import Union
import pandas as pd
from docling.document_converter import DocumentConverter, ConversionResult
from docling.datamodel.document import TableItem

from .config import CENTROVENETO, UNSUPPORTED


def extract_document_type(docling_doc: ConversionResult) -> str:
    """
    Extract document type by scanning document text for bank identifiers.

    Args:
        docling_doc: Converted document from docling

    Returns:
        Bank type identifier string (e.g., CENTROVENETO) or UNSUPPORTED

    Note:
        Currently has a bug - returns UNSUPPORTED on first non-match
        instead of checking all text elements.
    """
    for t in docling_doc.document.texts:
        if str(t.text).__contains__(CENTROVENETO):
            return CENTROVENETO
        else:
            return UNSUPPORTED
    return UNSUPPORTED


def extract_data_tables(converted_file_tables: Union[TableItem, list[TableItem]]) -> pd.DataFrame:
    """
    Convert docling TableItem(s) to pandas DataFrame.

    Args:
        converted_file_tables: Single TableItem or list of TableItems

    Returns:
        Concatenated DataFrame from all tables
    """
    if isinstance(converted_file_tables, list):
        df = pd.DataFrame()
        for el in converted_file_tables:
            out_df = el.export_to_dataframe()
            df = pd.concat([df, out_df], ignore_index=True)
        return df
    else:
        df = converted_file_tables.export_to_dataframe()
    return df


def extract_table(source: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Extract and parse tables from bank statement PDF.

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
    converter = DocumentConverter()
    result = converter.convert(source)
    used_tables = result.document.tables
    document_type = extract_document_type(result)

    if document_type in [CENTROVENETO]:
        print(f"Supported document type {document_type}")
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
        print("Unsupported document type")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
