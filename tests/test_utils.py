"""Tests for utility functions."""

import unittest
import pandas as pd
import numpy as np

from src.estrattoconto import clean_and_convert_currency

class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""

    def test_clean_and_convert_currency_basic(self):
        """Test basic currency conversion from Italian format."""
        series = pd.Series(['+ 4.858,52 €', '- 1.234,00 €'])
        result = clean_and_convert_currency(series)

        self.assertAlmostEqual(result.iloc[0], 4858.52)
        self.assertAlmostEqual(result.iloc[1], 1234.00)

    def test_clean_and_convert_currency_removes_symbols(self):
        """Test that currency symbols and signs are removed."""
        series = pd.Series(['+ 100,50 €', '- 200,75 €'])
        result = clean_and_convert_currency(series)

        self.assertAlmostEqual(result.iloc[0], 100.50)
        self.assertAlmostEqual(result.iloc[1], 200.75)

    def test_clean_and_convert_currency_handles_thousands(self):
        """Test that thousands separator (.) is correctly handled."""
        series = pd.Series(['1.234.567,89 €'])
        result = clean_and_convert_currency(series)

        self.assertAlmostEqual(result.iloc[0], 1234567.89)

    def test_clean_and_convert_currency_handles_invalid(self):
        """Test that invalid strings are converted to NaN."""
        series = pd.Series(['invalid', 'also invalid'])
        result = clean_and_convert_currency(series)

        self.assertTrue(pd.isna(result.iloc[0]))
        self.assertTrue(pd.isna(result.iloc[1]))

    def test_clean_and_convert_currency_handles_empty(self):
        """Test that empty strings are converted to NaN."""
        series = pd.Series(['', '  '])
        result = clean_and_convert_currency(series)

        self.assertTrue(pd.isna(result.iloc[0]))
        self.assertTrue(pd.isna(result.iloc[1]))


if __name__ == "__main__":
    unittest.main()
