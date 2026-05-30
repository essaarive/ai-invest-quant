"""Return indicators."""

from __future__ import annotations

import pandas as pd


def add_daily_return(df: pd.DataFrame) -> pd.DataFrame:
    """Add one-trading-day returns calculated independently by symbol."""
    result = df.copy()
    result = result.sort_values(["symbol", "date"], ascending=True, kind="mergesort")
    result = result.reset_index(drop=True)
    result["return_1d"] = result.groupby("symbol", sort=False)["close"].pct_change(1)
    return result


def add_period_return(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Add N-trading-day returns calculated independently by symbol."""
    result = df.copy()
    result = result.sort_values(["symbol", "date"], ascending=True, kind="mergesort")
    result = result.reset_index(drop=True)
    result[f"return_{window}d"] = result.groupby("symbol", sort=False)["close"].pct_change(window)
    return result
