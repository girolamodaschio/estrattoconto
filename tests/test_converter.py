"""Tests for converter module."""

import unittest
from pathlib import Path

from estrattoconto import extract_table, extract_data_tables


class TestConverter(unittest.TestCase):
    """Test cases for PDF extraction and table conversion."""

    def test_extract_table_returns_tuple(self):
        """Test that extract_table returns a tuple of 4 DataFrames."""
        # Note: This test will fail if the fixture PDF is not present
        filepath = Path(f"./fixture/centroveneto.pdf")

        if not filepath.exists():
            self.skipTest("Test fixture not available (./fixture/centroveneto.pdf)")

        extraction = extract_table(str(filepath))
        self.assertIsInstance(extraction, tuple)
        self.assertEqual(len(extraction), 4)

    def test_extract_table_dataframes_not_empty(self):
        """Test that extracted DataFrames contain data."""
        filepath = Path("./fixture/centroveneto.pdf")

        if not filepath.exists():
            self.skipTest("Test fixture not available (./fixture/centroveneto.pdf)")

        book_balance, account_info, balance_summary, transactions = extract_table(str(filepath))

        # At least the transaction table should have data
        self.assertFalse(transactions.empty, "Transaction table should not be empty")


if __name__ == "__main__":
    unittest.main()
