"""Validation helpers for market data inputs."""

from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = (
    "date",
    "symbol",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
)

PRICE_COLUMNS = ("open", "high", "low", "close")
NON_NEGATIVE_COLUMNS = ("volume", "amount")


def validate_market_data(df: pd.DataFrame) -> None:
    """Validate required market data fields and values.

    Raises:
        ValueError: If required columns are missing or values are invalid.
    """
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    _validate_date(df["date"])
    _validate_symbol(df["symbol"])

    numeric_columns: dict[str, pd.Series] = {}
    for column in PRICE_COLUMNS + NON_NEGATIVE_COLUMNS:
        numeric_columns[column] = _to_numeric(df[column], column)

    for column in PRICE_COLUMNS:
        invalid = numeric_columns[column].isna() | (numeric_columns[column] <= 0)
        if invalid.any():
            raise ValueError(f"Column '{column}' must be numeric and > 0")

    for column in NON_NEGATIVE_COLUMNS:
        invalid = numeric_columns[column].isna() | (numeric_columns[column] < 0)
        if invalid.any():
            raise ValueError(f"Column '{column}' must be numeric and >= 0")

    high = numeric_columns["high"]
    low = numeric_columns["low"]
    open_ = numeric_columns["open"]
    close = numeric_columns["close"]

    if (high < open_).any() or (high < close).any() or (high < low).any():
        raise ValueError("Column 'high' must be >= open, close, and low")

    if (low > open_).any() or (low > close).any() or (low > high).any():
        raise ValueError("Column 'low' must be <= open, close, and high")


def _validate_date(series: pd.Series) -> None:
    invalid_empty = series.isna() | series.astype("string").str.strip().eq("")
    if invalid_empty.any():
        raise ValueError("Column 'date' cannot be empty")

    try:
        pd.to_datetime(series, errors="raise")
    except Exception as exc:
        raise ValueError("Column 'date' must be parseable as dates") from exc


def _validate_symbol(series: pd.Series) -> None:
    invalid = series.isna() | series.astype("string").str.strip().eq("")
    if invalid.any():
        raise ValueError("Column 'symbol' cannot be empty")


def _to_numeric(series: pd.Series, column: str) -> pd.Series:
    try:
        return pd.to_numeric(series, errors="raise")
    except Exception as exc:
        raise ValueError(f"Column '{column}' must be numeric") from exc

