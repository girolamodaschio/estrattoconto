"""Utility functions for data processing."""

import pandas as pd


def clean_and_convert_currency(series: pd.Series) -> pd.Series:
    """
    Clean Italian currency strings and convert to numeric floats.

    Handles Italian banking format:
    - Thousands separator: . (period)
    - Decimal separator: , (comma)
    - Currency symbol: € (euro)
    - Sign notation: +/- prefix

    Examples:
        '+ 4.858,52 €' -> 4858.52
        '- 1.234,00 €' -> 1234.00

    Args:
        series: Pandas Series containing currency strings

    Returns:
        Pandas Series with numeric float values

    Steps:
        1. Convert to string type
        2. Remove non-numeric characters (except +, -, comma, period)
        3. Remove € symbol and spaces
        4. Remove thousands separator (.)
        5. Replace decimal separator (,) with period (.)
        6. Remove +/- signs
        7. Convert to numeric (coerce errors to NaN)
    """
    series = series.astype(str)
    cleaned_series = series.str.replace(r'[^\d\+\-\,\.\s]', '', regex=True)
    cleaned_series = cleaned_series.str.replace('€', '', regex=False).str.strip()
    cleaned_series = cleaned_series.str.replace('.', '', regex=False)
    cleaned_series = cleaned_series.str.replace(',', '.', regex=False)
    cleaned_series = cleaned_series.str.replace('+', '', regex=False)
    cleaned_series = cleaned_series.str.replace('-', '', regex=False)
    return pd.to_numeric(cleaned_series, errors="coerce")
