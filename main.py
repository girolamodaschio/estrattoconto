from src.config import CENTROVENETO
import pandas as pd
from docling.document_converter import DocumentConverter



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
    """takes a pdf file from ls, extract """
    converter = DocumentConverter()
    result = converter.convert(source)
    used_tables = result.document.tables
    document_type = CENTROVENETO #fixme add a document type extractor
    if document_type in [CENTROVENETO]:
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
        print("Unsupported")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def extract_bill(df):
    """typically this is between MANDATO and SSD"""
    return ""

def extract_payee(df):
    """when there is the word BONIFICO Coordinate benef: output is between è  A fav: e ID.MSG"""
    return ""

def extract_timeframe(df):
    """this is used to extract what's below the Periodo. Such as 01/07/2025 - 31/07/2025 """
    return ""
def sql_export(df: pd.DataFrame) -> None:
    """this function will export the df as will be used by my awesome django application"""
    return ""


def enrich_data(data_tables_df):
    bill = extract_bill(data_tables_df)
    payee = extract_payee(data_tables_df)
    timeframe = extract_timeframe(data_tables_df)





def main():
    """
    this function will:
    read a pdf
    convert to dataframe
    classify the expense
    enrich it
    """
    pass


if __name__ == "__main__":
    extract_table('tests/fixture/centroveneto.pdf')