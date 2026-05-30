"""Trend indicators."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def add_moving_average(
    df: pd.DataFrame,
    windows: Iterable[int] = (20, 60, 120),
) -> pd.DataFrame:
    """Add moving-average columns calculated independently by symbol."""
    result = df.copy()
    result = result.sort_values(["symbol", "date"], ascending=True, kind="mergesort")
    result = result.reset_index(drop=True)

    grouped_close = result.groupby("symbol", sort=False)["close"]
    for window in windows:
        result[f"ma{window}"] = grouped_close.transform(
            lambda series: series.rolling(window=window, min_periods=window).mean()
        )

    return result
