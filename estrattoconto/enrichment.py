"""Data enrichment and classification module."""

import pandas as pd

from .utils import clean_and_convert_currency


def postprocess_extraction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter and clean extracted transaction data.

    Args:
        df: Raw DataFrame from table extraction

    Returns:
        DataFrame with only essential columns and NaN rows removed

    Essential columns:
        - DATA MOV.: Movement date
        - VALUTA: Value date
        - DARE: Debit amount
        - AVERE: Credit amount
        - DESCRIZIONE OPERAZIONE: Operation description
    """
    columns_to_keep = ['DATA MOV.', 'VALUTA', 'DARE', 'AVERE', 'DESCRIZIONE OPERAZIONE']
    df = df.loc[:, columns_to_keep]
    df = df.dropna()
    return df


def enrich_data(extracted_tables: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]) -> pd.DataFrame:
    """
    Enrich transaction data with extracted entities, classifications, and metadata.

    Performs the following enrichment steps:
    1. Column selection and cleaning
    2. Entity extraction (payer, payee, id_mandato)
    3. Currency conversion for Italian format
    4. Amount normalization
    5. Transaction classification flags
    6. Metadata addition (account, period)

    Args:
        extracted_tables: Tuple of 4 DataFrames from extract_table():
            [0] book_balance: Period information
            [1] account_information: Account details
            [2] balance_summary: Balance summary
            [3] data_tables: Transaction data

    Returns:
        Enriched DataFrame with additional columns:
            - payer: Extracted from wire transfers
            - payee: Extracted from direct debits
            - id_mandato: Mandate ID from direct debits
            - DARE_Numeric: Numeric debit amount
            - AVERE_Numeric: Numeric credit amount
            - amount: Combined amount (debit or credit)
            - is_bill: Boolean flag for direct debits (S.D.D.)
            - is_incoming_transfer: Boolean flag for incoming wire transfers
            - is_outcoming_transfer: Boolean flag for outgoing wire transfers
            - is_bank_fee: Boolean flag for bank fees (CANONE)
            - related_account: Account number
            - period: Statement period
    """
    data_table = extracted_tables[3]
    data_table = postprocess_extraction(data_table)

    # Entity extraction using regex patterns on DESCRIZIONE OPERAZIONE
    data_table['payer'] = data_table['DESCRIZIONE OPERAZIONE'].str.extract(
        r'Ordinante:\s*(.*?)\s*Causale', expand=False
    )
    data_table['payee'] = data_table['DESCRIZIONE OPERAZIONE'].str.extract(
        r'ADDEBITO CRED\.\s*(.*?)\s*ID\.MANDATO', expand=False
    )
    data_table['id_mandato'] = data_table['DESCRIZIONE OPERAZIONE'].str.extract(
        r'ID\.MANDATO\s*(.*?)\s*(?:RIF\.|\sSDD)', expand=False
    )

    # Filter empty AVERE/DARE columns (only keep rows with € symbol)
    av_mask = data_table['AVERE'].astype(str).str.contains('€', na=False)
    data_table.loc[~av_mask, 'AVERE'] = ""
    av_mask = data_table['DARE'].astype(str).str.contains('€', na=False)
    data_table.loc[~av_mask, 'DARE'] = ""

    # Convert Italian currency format to numeric
    data_table['DARE'] = clean_and_convert_currency(data_table['DARE'])
    data_table['AVERE'] = clean_and_convert_currency(data_table['AVERE'])

    # Transaction classification flags
    data_table['is_bill'] = data_table['DESCRIZIONE OPERAZIONE'].str.contains(
        'S.D.D.', case=False, na=False
    )
    data_table['is_incoming_transfer'] = data_table['DESCRIZIONE OPERAZIONE'].str.contains(
        'BONIFICO A VS. FAVORE', case=False, na=False
    )
    data_table['is_outcoming_transfer'] = data_table['DESCRIZIONE OPERAZIONE'].str.contains(
        'BONIFICO coordinate benef', case=False, na=False
    )
    data_table['is_bank_fee'] = data_table['DESCRIZIONE OPERAZIONE'].str.contains(
        'CANONE|COMMISSIONI', case=False, na=False
    )

    # Add metadata from other tables
    data_table['related_account'] = extracted_tables[1].iloc[1].values[1]
    data_table['period'] = extracted_tables[0].iloc[0].values[-1]

    return data_table
