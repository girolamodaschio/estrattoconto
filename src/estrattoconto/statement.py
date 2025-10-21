"""Bank statement object-oriented API."""

from pathlib import Path
from typing import Optional, List
import pandas as pd

from .converter import extract_table
from .enrichment import enrich_data


class EstrattoConto:
    """
    Represents an Italian bank statement (estratto conto) with enriched transaction data.

    This class provides an object-oriented interface for working with bank statement data,
    including methods for querying transactions, filtering, and exporting to various formats.

    Attributes:
        data: Enriched transaction DataFrame
        book_balance: Period and balance information
        account_info: Account details
        balance_summary: Balance summary
    """

    def __init__(
        self,
        data: pd.DataFrame,
        book_balance: Optional[pd.DataFrame] = None,
        account_info: Optional[pd.DataFrame] = None,
        balance_summary: Optional[pd.DataFrame] = None,
    ):
        """
        Initialize EstrattoConto with enriched data.

        Args:
            data: Enriched transaction DataFrame
            book_balance: Optional book balance DataFrame
            account_info: Optional account information DataFrame
            balance_summary: Optional balance summary DataFrame
        """
        self.data = data
        self.book_balance = book_balance
        self.account_info = account_info
        self.balance_summary = balance_summary

    @classmethod
    def from_pdf(cls, pdf_path: str) -> "EstrattoConto":
        """
        Create an EstrattoConto object from a PDF bank statement.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            EstrattoConto object with enriched transaction data

        Example:
            >>> statement = EstrattoConto.from_pdf('bank_statement.pdf')
        """
        # Extract tables from PDF
        book_balance, account_info, balance_summary, transactions = extract_table(pdf_path)

        # Enrich the data
        enriched_data = enrich_data((book_balance, account_info, balance_summary, transactions))

        return cls(
            data=enriched_data,
            book_balance=book_balance,
            account_info=account_info,
            balance_summary=balance_summary,
        )

    def to_csv(self, output_path: str, **kwargs) -> None:
        """
        Export transactions to CSV file.

        Args:
            output_path: Path for the output CSV file
            **kwargs: Additional arguments passed to pandas.DataFrame.to_csv()

        Example:
            >>> statement.to_csv('transactions.csv')
            >>> statement.to_csv('transactions.csv', sep=';', encoding='utf-8')
        """
        self.data.to_csv(output_path, index=False, **kwargs)

    def to_json(self, output_path: str, **kwargs) -> None:
        """
        Export transactions to JSON file.

        Args:
            output_path: Path for the output JSON file
            **kwargs: Additional arguments passed to pandas.DataFrame.to_json()

        Example:
            >>> statement.to_json('transactions.json')
            >>> statement.to_json('transactions.json', orient='records', indent=2)
        """
        self.data.to_json(output_path, orient="records", **kwargs)

    def to_excel(self, output_path: str, **kwargs) -> None:
        """
        Export transactions to Excel file.

        Args:
            output_path: Path for the output Excel file
            **kwargs: Additional arguments passed to pandas.DataFrame.to_excel()

        Example:
            >>> statement.to_excel('transactions.xlsx')
        """
        self.data.to_excel(output_path, index=False, **kwargs)

    def extract_payers(self) -> List[str]:
        """
        Extract unique payer names from transactions.

        Returns:
            List of unique payer names (excluding NaN values)

        Example:
            >>> payers = statement.extract_payers()
            >>> print(payers)
            ['John Doe', 'Company XYZ']
        """
        return self.data["payer"].dropna().unique().tolist()

    def extract_payees(self) -> List[str]:
        """
        Extract unique payee names from transactions.

        Returns:
            List of unique payee names (excluding NaN values)

        Example:
            >>> payees = statement.extract_payees()
            >>> print(payees)
            ['Electric Company', 'Water Utility']
        """
        return self.data["payee"].dropna().unique().tolist()

    def get_bills(self) -> pd.DataFrame:
        """
        Filter and return only bill/direct debit transactions (S.D.D.).

        Returns:
            DataFrame containing only bill transactions

        Example:
            >>> bills = statement.get_bills()
            >>> print(f"Total bills: {len(bills)}")
        """
        return self.data[self.data["is_bill"] == True].copy()

    def get_incoming_transfers(self) -> pd.DataFrame:
        """
        Filter and return only incoming wire transfer transactions.

        Returns:
            DataFrame containing only incoming transfer transactions

        Example:
            >>> incoming = statement.get_incoming_transfers()
        """
        return self.data[self.data["is_incoming_transfer"] == True].copy()

    def get_outgoing_transfers(self) -> pd.DataFrame:
        """
        Filter and return only outgoing wire transfer transactions.

        Returns:
            DataFrame containing only outgoing transfer transactions

        Example:
            >>> outgoing = statement.get_outgoing_transfers()
        """
        return self.data[self.data["is_outcoming_transfer"] == True].copy()

    def get_fees(self) -> pd.DataFrame:
        """
        Filter and return only bank fee transactions.

        Returns:
            DataFrame containing only fee transactions

        Example:
            >>> fees = statement.get_fees()
        """
        return self.data[self.data["is_bank_fee"] == True].copy()

    def filter_by_date(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Filter transactions by date range.

        Args:
            start_date: Start date (inclusive) in format DD/MM/YYYY
            end_date: End date (inclusive) in format DD/MM/YYYY

        Returns:
            DataFrame filtered by date range

        Example:
            >>> filtered = statement.filter_by_date('01/01/2025', '31/01/2025')
        """
        df = self.data.copy()

        # Convert DATA MOV. to datetime if it's not already
        df["DATA MOV."] = pd.to_datetime(df["DATA MOV."], format="%d/%m/%Y", errors="coerce")

        if start_date:
            start = pd.to_datetime(start_date, format="%d/%m/%Y")
            df = df[df["DATA MOV."] >= start]

        if end_date:
            end = pd.to_datetime(end_date, format="%d/%m/%Y")
            df = df[df["DATA MOV."] <= end]

        return df

    def get_dataframe(self) -> pd.DataFrame:
        """
        Get the underlying enriched DataFrame.

        Returns:
            The enriched transaction DataFrame

        Example:
            >>> df = statement.get_dataframe()
            >>> print(df.columns)
        """
        return self.data.copy()

    def __repr__(self) -> str:
        """String representation of the EstrattoConto object."""
        num_transactions = len(self.data)
        period = self.data["period"].iloc[0] if "period" in self.data.columns else "Unknown"
        account = (
            self.data["related_account"].iloc[0]
            if "related_account" in self.data.columns
            else "Unknown"
        )

        return (
            f"EstrattoConto("
            f"account={account}, "
            f"period={period}, "
            f"transactions={num_transactions})"
        )

    def __len__(self) -> int:
        """Return the number of transactions."""
        return len(self.data)

    def summary(self) -> dict:
        """
        Get a summary of the statement.

        Returns:
            Dictionary with statement statistics

        Example:
            >>> summary = statement.summary()
            >>> print(summary)
        """
        return {
            "total_transactions": len(self.data),
            "total_bills": self.data["is_bill"].sum(),
            "total_incoming_transfers": self.data["is_incoming_transfer"].sum(),
            "total_outgoing_transfers": self.data["is_outcoming_transfer"].sum(),
            "total_fees": self.data["is_bank_fee"].sum(),
            "period": self.data["period"].iloc[0] if len(self.data) > 0 else None,
            "account": (
                self.data["related_account"].iloc[0] if len(self.data) > 0 else None
            ),
        }
