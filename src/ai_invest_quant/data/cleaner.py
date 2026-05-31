"""Cleaning helpers for validated market data."""

from __future__ import annotations

import pandas as pd

NUMERIC_COLUMNS = ("open", "high", "low", "close", "volume", "amount")


def clean_market_data(df: pd.DataFrame) -> pd.DataFrame:
    """Parse dates, convert numeric fields, sort, deduplicate, and reset index."""
    cleaned = df.copy()
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="raise")
    for column in NUMERIC_COLUMNS:
        try:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="raise")
        except Exception as exc:
            raise ValueError(f"Column '{column}' must be convertible to numeric") from exc

    cleaned = cleaned.sort_values(["symbol", "date"], ascending=True, kind="mergesort")
    cleaned = cleaned.drop_duplicates(["symbol", "date"], keep="last")
    return cleaned.reset_index(drop=True)
