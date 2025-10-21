"""Tests for enrichment module."""

import unittest
import pandas as pd

from estrattoconto import postprocess_extraction


class TestEnrichment(unittest.TestCase):
    """Test cases for data enrichment and classification."""

    def test_postprocess_extraction_filters_columns(self):
        """Test that postprocess_extraction keeps only essential columns."""
        # Create a test DataFrame with extra columns
        df = pd.DataFrame({
            'DATA MOV.': ['01/01/2025', '02/01/2025'],
            'VALUTA': ['01/01/2025', '02/01/2025'],
            'DARE': ['100,00 €', ''],
            'AVERE': ['', '200,00 €'],
            'DESCRIZIONE OPERAZIONE': ['Test 1', 'Test 2'],
            'EXTRA_COLUMN': ['Extra 1', 'Extra 2'],
        })

        result = postprocess_extraction(df)

        expected_columns = ['DATA MOV.', 'VALUTA', 'DARE', 'AVERE', 'DESCRIZIONE OPERAZIONE']
        self.assertListEqual(list(result.columns), expected_columns)
        self.assertNotIn('EXTRA_COLUMN', result.columns)

    def test_postprocess_extraction_removes_nan(self):
        """Test that postprocess_extraction removes rows with NaN values."""
        df = pd.DataFrame({
            'DATA MOV.': ['01/01/2025', None, '03/01/2025'],
            'VALUTA': ['01/01/2025', '02/01/2025', '03/01/2025'],
            'DARE': ['100,00 €', '200,00 €', '300,00 €'],
            'AVERE': ['', '', ''],
            'DESCRIZIONE OPERAZIONE': ['Test 1', 'Test 2', 'Test 3'],
        })

        result = postprocess_extraction(df)

        # Should have removed the row with None
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()
