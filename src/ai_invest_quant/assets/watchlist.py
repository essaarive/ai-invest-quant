"""Watchlist loading, validation, and saving helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

WATCHLIST_COLUMNS = ["symbol", "name", "market", "asset_type", "currency", "data_path"]
REQUIRED_NON_EMPTY_COLUMNS = ["symbol", "market", "asset_type", "currency", "data_path"]
ALLOWED_MARKETS = {"CN", "HK", "US", "CRYPTO"}
ALLOWED_ASSET_TYPES = {"ETF", "STOCK", "CRYPTO", "INDEX", "FUND"}


def load_watchlist(path: str | Path) -> pd.DataFrame:
    """Load and validate a watchlist CSV."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    validate_watchlist(df)
    return df


def validate_watchlist(df: pd.DataFrame) -> None:
    """Validate the standard watchlist schema and controlled fields."""
    missing = [column for column in WATCHLIST_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required watchlist columns: {', '.join(missing)}")

    for column in REQUIRED_NON_EMPTY_COLUMNS:
        if df[column].isna().any() or df[column].astype(str).str.strip().eq("").any():
            raise ValueError(f"Watchlist column '{column}' cannot be empty")

    invalid_markets = sorted(set(df["market"].astype(str)) - ALLOWED_MARKETS)
    if invalid_markets:
        raise ValueError(f"Invalid market values: {', '.join(invalid_markets)}")

    invalid_asset_types = sorted(set(df["asset_type"].astype(str)) - ALLOWED_ASSET_TYPES)
    if invalid_asset_types:
        raise ValueError(f"Invalid asset_type values: {', '.join(invalid_asset_types)}")


def save_watchlist(df: pd.DataFrame, path: str | Path) -> None:
    """Validate and save a watchlist CSV."""
    validate_watchlist(df)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
