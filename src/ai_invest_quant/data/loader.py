"""CSV loader for market data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ai_invest_quant.data.cleaner import clean_market_data
from ai_invest_quant.data.validator import validate_market_data


def load_csv(path: str | Path) -> pd.DataFrame:
    """Read, validate, and clean a local CSV file."""
    df = pd.read_csv(path)
    validate_market_data(df)
    return clean_market_data(df)
