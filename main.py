from src.estrattoconto import extract_table, enrich_data


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