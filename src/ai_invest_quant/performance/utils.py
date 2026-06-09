"""Shared performance data preparation helpers."""

from __future__ import annotations

import pandas as pd


def prepare_nav_dataframe(nav_df: pd.DataFrame) -> pd.DataFrame:
    """Prepare a validated, date-sorted NAV DataFrame with date, equity, and nav."""
    missing = [column for column in ("date", "equity") if column not in nav_df.columns]
    if missing:
        raise ValueError(f"Missing required nav columns: {', '.join(missing)}")

    if nav_df.empty:
        raise ValueError("nav_df cannot be empty")

    nav = nav_df.copy()
    nav["date"] = pd.to_datetime(nav["date"], errors="raise")
    nav["equity"] = _prepare_positive_numeric_column(nav["equity"], "equity")
    nav = nav.sort_values("date", kind="mergesort").reset_index(drop=True)

    if "nav" in nav.columns:
        nav["nav"] = _prepare_positive_numeric_column(nav["nav"], "nav")
    else:
        first_equity = nav["equity"].iloc[0]
        nav["nav"] = nav["equity"] / first_equity

    return nav


def _prepare_positive_numeric_column(series: pd.Series, column: str) -> pd.Series:
    if series.isna().any() or series.astype("string").str.strip().eq("").any():
        raise ValueError(f"{column} values cannot be empty")

    try:
        numeric = pd.to_numeric(series, errors="raise")
    except Exception as exc:
        raise ValueError(f"{column} values must be numeric") from exc

    if (numeric <= 0).any():
        raise ValueError(f"{column} values must be > 0")

    return numeric
