"""
Example usage of the estrattoconto package.

This demonstrates the object-oriented API for extracting and working with
Italian bank statement data.
"""

import estrattoconto


def main():
    """
    Demonstrate the estrattoconto object-oriented API.

    This function will:
    1. Read a PDF bank statement
    2. Convert it to an EstrattoConto object
    3. Demonstrate various query and export methods
    """
    # Convert PDF to EstrattoConto object
    statement = estrattoconto.convert('tests/fixture/centroveneto.pdf')

    # Print statement summary
    print(statement)
    print("\nStatement Summary:")
    summary = statement.summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Query methods
    print("\n--- Extracting Information ---")
    payers = statement.extract_payers()
    print(f"Unique payers: {payers}")

    payees = statement.extract_payees()
    print(f"Unique payees: {payees}")

    # Filter by transaction type
    print("\n--- Filtering by Transaction Type ---")
    bills = statement.get_bills()
    print(f"Total bills (S.D.D.): {len(bills)}")

    incoming = statement.get_incoming_transfers()
    print(f"Total incoming transfers: {len(incoming)}")

    outgoing = statement.get_outgoing_transfers()
    print(f"Total outgoing transfers: {len(outgoing)}")

    fees = statement.get_fees()
    print(f"Total bank fees: {len(fees)}")

    # Export to various formats (uncomment to use)
    # statement.to_csv('output.csv')
    # statement.to_json('output.json')
    # statement.to_excel('output.xlsx')

    print("\n--- Complete! ---")


if __name__ == "__main__":
    main()
