import numpy as np

from src.config import CENTROVENETO, UNSUPPORTED
import pandas as pd
from docling.document_converter import DocumentConverter


def extract_document_type(docling_doc):
    for t in docling_doc.document.texts:
        if str(t.text).__contains__(CENTROVENETO):
            return CENTROVENETO
        else:
            return UNSUPPORTED


def extract_data_tables(converted_file_tables)-> pd.DataFrame:
    if type(converted_file_tables) == list:
        df = pd.DataFrame()
        for el in converted_file_tables:
            out_df = el.export_to_dataframe()
            df = pd.concat([df, out_df])
        return df
    else:
        df = converted_file_tables.export_to_dataframe()
    return df

def extract_table(source: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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

def postprocess_extraction(df):
    columns_to_keep = ['DATA MOV.', 'VALUTA', 'DARE', 'AVERE',
       'DESCRIZIONE OPERAZIONE']

    df = df.loc[:,columns_to_keep]
    df = df.dropna()
    return df

def clean_and_convert_currency(series):
    """
    Cleans currency strings (e.g., '+ 4.858,52 €') and converts them to numeric floats.

    Steps:
    1. Handles NaN values by returning NaN.
    2. Removes the currency symbol (€) and spaces.
    3. Replaces the thousands separator (.) with nothing.
    4. Replaces the decimal separator (,) with a standard period (.).
    5. Converts the resulting string to a float.
    """
    series = series.astype(str)
    cleaned_series = series.str.replace(r'[^\d\+\-\,\.\s]', '', regex=True)
    cleaned_series = cleaned_series.str.replace('€', '', regex=False).str.strip()
    cleaned_series = cleaned_series.str.replace('.', '', regex=False)
    cleaned_series = cleaned_series.str.replace(',', '.', regex=False)
    cleaned_series = cleaned_series.str.replace('+', '', regex=False)
    cleaned_series = cleaned_series.str.replace('-', '', regex=False)
    return pd.to_numeric(cleaned_series, errors="coerce")



def enrich_data(extracted_tables):
    data_table = extracted_tables[3]
    data_table = postprocess_extraction(data_table)

    data_table['payer'] = data_table['DESCRIZIONE OPERAZIONE'].str.extract(r'Ordinante:\s*(.*?)\s*Causale', expand=False)
    data_table['payee'] = data_table['DESCRIZIONE OPERAZIONE'].str.extract(r'ADDEBITO CRED\.\s*(.*?)\s*ID\.MANDATO', expand=False)
    data_table['id_mandato'] = data_table['DESCRIZIONE OPERAZIONE'].str.extract(r'ID\.MANDATO\s*(.*?)\s*(?:RIF\.|\sSDD)', expand=False)


    av_mask = data_table['AVERE'].astype(str).str.contains('€', na=False)
    data_table.loc[~av_mask, 'AVERE'] = ""
    av_mask = data_table['DARE'].astype(str).str.contains('€', na=False)
    data_table.loc[~av_mask, 'DARE'] = ""



    data_table['DARE_Numeric'] = clean_and_convert_currency(data_table['DARE'])
    data_table['AVERE_Numeric'] = clean_and_convert_currency(data_table['AVERE'])

    data_table['amount'] = data_table['DARE_Numeric'].combine_first(data_table['AVERE_Numeric'])

    data_table['is_bill'] = data_table['DESCRIZIONE OPERAZIONE'].str.contains('S.D.D.', case=False, na=False)
    data_table['is_incoming_transfer'] = data_table['DESCRIZIONE OPERAZIONE'].str.contains('BONIFICO A VS. FAVORE', case=False, na=False)
    data_table['is_outcoming_transfer'] = data_table['DESCRIZIONE OPERAZIONE'].str.contains('BONIFICO coordinate benef', case=False, na=False)
    data_table['is_bank_fee'] = data_table['DESCRIZIONE OPERAZIONE'].str.contains('CANONE', case=False, na=False)

    data_table['related_account'] = extracted_tables[1].iloc[1].values[1]
    data_table['period'] = extracted_tables[0].iloc[0].values[-1]

    return data_table


def main():
    """
    this function will:
    read a pdf
    convert to dataframe
    classify the expense
    enrich it
    """
    extracted_tables = extract_table('tests/fixture/centroveneto.pdf')
    enriched_data_table = enrich_data(extracted_tables)
    print(0)

if __name__ == "__main__":
    main()