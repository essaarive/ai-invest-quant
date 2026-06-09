"""Utilities for standardizing and merging multiple local price CSV files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ai_invest_quant.assets.watchlist import WATCHLIST_COLUMNS, load_watchlist
from ai_invest_quant.data.adapters import STANDARD_COLUMNS, standardize_price_csv


def standardize_many_price_csvs(
    watchlist_path: str | Path,
    output_path: str | Path,
    metadata_output_path: str | Path | None = None,
) -> dict[str, object]:
    """Standardize many local CSV files listed in a watchlist and merge them."""
    watchlist = load_watchlist(watchlist_path)
    if watchlist.empty:
        raise ValueError("watchlist cannot be empty")

    standardized_frames = []
    for row in watchlist.itertuples(index=False):
        data_path = Path(row.data_path)
        if not data_path.exists():
            raise FileNotFoundError(f"Price CSV not found for symbol {row.symbol}: {data_path}")
        standardized_frames.append(
            standardize_price_csv(data_path, default_symbol=str(row.symbol))
        )

    prices = pd.concat(standardized_frames, ignore_index=True)
    prices["date"] = pd.to_datetime(prices["date"], errors="raise")
    prices = prices.sort_values(["symbol", "date"], ascending=True, kind="mergesort")
    prices = prices[STANDARD_COLUMNS].reset_index(drop=True)

    metadata = watchlist[WATCHLIST_COLUMNS].copy().reset_index(drop=True)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    prices.to_csv(output, index=False)

    metadata_output = None
    if metadata_output_path is not None:
        metadata_output = Path(metadata_output_path)
        metadata_output.parent.mkdir(parents=True, exist_ok=True)
        metadata.to_csv(metadata_output, index=False)

    return {
        "prices": prices,
        "metadata": metadata,
        "output_path": str(output),
        "metadata_output_path": str(metadata_output) if metadata_output is not None else None,
    }
