"""Tests for the EstrattoConto class (object-oriented API)."""

import unittest
from pathlib import Path
import pandas as pd
import tempfile

from estrattoconto import EstrattoConto, convert


class TestEstrattoConto(unittest.TestCase):
    """Test cases for the EstrattoConto class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock enriched DataFrame for testing
        self.mock_data = pd.DataFrame({
            'DATA MOV.': ['01/01/2025', '02/01/2025', '03/01/2025', '04/01/2025'],
            'VALUTA': ['01/01/2025', '02/01/2025', '03/01/2025', '04/01/2025'],
            'DARE': ['100,00 €', '', '50,00 €', ''],
            'AVERE': ['', '200,00 €', '', '25,00 €'],
            'DESCRIZIONE OPERAZIONE': [
                'S.D.D. ADDEBITO CRED. Utility Company ID.MANDATO MAN123 SDD',
                'BONIFICO A VS. FAVORE Ordinante: John Doe Causale: Payment',
                'BONIFICO coordinate benef ABC123',
                'CANONE Monthly fee'
            ],
            'payer': [None, 'John Doe', None, None],
            'payee': ['Utility Company', None, None, None],
            'id_mandato': ['MAN123', None, None, None],
            'DARE_Numeric': [100.0, None, 50.0, None],
            'AVERE_Numeric': [None, 200.0, None, 25.0],
            'amount': [100.0, 200.0, 50.0, 25.0],
            'is_bill': [True, False, False, False],
            'is_incoming_transfer': [False, True, False, False],
            'is_outcoming_transfer': [False, False, True, False],
            'is_bank_fee': [False, False, False, True],
            'related_account': ['IT123456', 'IT123456', 'IT123456', 'IT123456'],
            'period': ['01/01/2025 - 31/01/2025'] * 4,
        })

        self.statement = EstrattoConto(data=self.mock_data)

    def test_init(self):
        """Test EstrattoConto initialization."""
        self.assertIsInstance(self.statement, EstrattoConto)
        self.assertIsInstance(self.statement.data, pd.DataFrame)
        self.assertEqual(len(self.statement.data), 4)

    def test_len(self):
        """Test __len__ method."""
        self.assertEqual(len(self.statement), 4)

    def test_repr(self):
        """Test string representation."""
        repr_str = repr(self.statement)
        self.assertIn('EstrattoConto', repr_str)
        self.assertIn('transactions=4', repr_str)
        self.assertIn('IT123456', repr_str)

    def test_extract_payers(self):
        """Test extracting unique payer names."""
        payers = self.statement.extract_payers()
        self.assertIsInstance(payers, list)
        self.assertEqual(len(payers), 1)
        self.assertIn('John Doe', payers)

    def test_extract_payees(self):
        """Test extracting unique payee names."""
        payees = self.statement.extract_payees()
        self.assertIsInstance(payees, list)
        self.assertEqual(len(payees), 1)
        self.assertIn('Utility Company', payees)

    def test_get_bills(self):
        """Test filtering bill transactions."""
        bills = self.statement.get_bills()
        self.assertIsInstance(bills, pd.DataFrame)
        self.assertEqual(len(bills), 1)
        self.assertTrue(bills['is_bill'].all())

    def test_get_incoming_transfers(self):
        """Test filtering incoming transfer transactions."""
        incoming = self.statement.get_incoming_transfers()
        self.assertIsInstance(incoming, pd.DataFrame)
        self.assertEqual(len(incoming), 1)
        self.assertTrue(incoming['is_incoming_transfer'].all())

    def test_get_outgoing_transfers(self):
        """Test filtering outgoing transfer transactions."""
        outgoing = self.statement.get_outgoing_transfers()
        self.assertIsInstance(outgoing, pd.DataFrame)
        self.assertEqual(len(outgoing), 1)
        self.assertTrue(outgoing['is_outcoming_transfer'].all())

    def test_get_fees(self):
        """Test filtering fee transactions."""
        fees = self.statement.get_fees()
        self.assertIsInstance(fees, pd.DataFrame)
        self.assertEqual(len(fees), 1)
        self.assertTrue(fees['is_bank_fee'].all())

    def test_get_dataframe(self):
        """Test getting the underlying DataFrame."""
        df = self.statement.get_dataframe()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 4)
        # Ensure it's a copy
        self.assertFalse(df is self.statement.data)

    def test_summary(self):
        """Test statement summary."""
        summary = self.statement.summary()
        self.assertIsInstance(summary, dict)
        self.assertEqual(summary['total_transactions'], 4)
        self.assertEqual(summary['total_bills'], 1)
        self.assertEqual(summary['total_incoming_transfers'], 1)
        self.assertEqual(summary['total_outgoing_transfers'], 1)
        self.assertEqual(summary['total_fees'], 1)
        self.assertEqual(summary['account'], 'IT123456')
        self.assertEqual(summary['period'], '01/01/2025 - 31/01/2025')

    def test_to_csv(self):
        """Test CSV export."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name

        try:
            self.statement.to_csv(csv_path)
            self.assertTrue(Path(csv_path).exists())

            # Read back and verify
            df_loaded = pd.read_csv(csv_path)
            self.assertEqual(len(df_loaded), 4)
        finally:
            Path(csv_path).unlink(missing_ok=True)

    def test_to_json(self):
        """Test JSON export."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name

        try:
            self.statement.to_json(json_path)
            self.assertTrue(Path(json_path).exists())

            # Read back and verify
            df_loaded = pd.read_json(json_path)
            self.assertEqual(len(df_loaded), 4)
        finally:
            Path(json_path).unlink(missing_ok=True)

    def test_filter_by_date(self):
        """Test date range filtering."""
        filtered = self.statement.filter_by_date('01/01/2025', '02/01/2025')
        self.assertIsInstance(filtered, pd.DataFrame)
        self.assertEqual(len(filtered), 2)

    def test_filter_by_date_start_only(self):
        """Test filtering with start date only."""
        filtered = self.statement.filter_by_date(start_date='03/01/2025')
        self.assertIsInstance(filtered, pd.DataFrame)
        self.assertEqual(len(filtered), 2)

    def test_filter_by_date_end_only(self):
        """Test filtering with end date only."""
        filtered = self.statement.filter_by_date(end_date='02/01/2025')
        self.assertIsInstance(filtered, pd.DataFrame)
        self.assertEqual(len(filtered), 2)


class TestConvertFunction(unittest.TestCase):
    """Test cases for the convert() convenience function."""

    def test_convert_function_exists(self):
        """Test that convert function is accessible."""
        self.assertTrue(callable(convert))

    def test_from_pdf_integration(self):
        """Test creating EstrattoConto from PDF (integration test)."""
        filepath = Path("tests/fixture/centroveneto.pdf")

        if not filepath.exists():
            self.skipTest("Test fixture not available (tests/fixture/centroveneto.pdf)")

        statement = convert(str(filepath))
        self.assertIsInstance(statement, EstrattoConto)
        self.assertFalse(statement.data.empty)
        self.assertGreater(len(statement), 0)


if __name__ == "__main__":
    unittest.main()
