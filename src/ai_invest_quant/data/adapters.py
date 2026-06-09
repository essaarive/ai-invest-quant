"""Adapters for standardizing external ETF price CSV columns."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ai_invest_quant.data.constants import BASE_PRICE_COLUMNS

STANDARD_COLUMNS = list(BASE_PRICE_COLUMNS)

COLUMN_ALIASES = {
    "date": ["date", "Date", "datetime", "trade_date", "日期", "交易日期"],
    "symbol": [
        "symbol",
        "Symbol",
        "ticker",
        "Ticker",
        "code",
        "Code",
        "代码",
        "证券代码",
        "标的代码",
    ],
    "open": ["open", "Open", "开盘", "开盘价"],
    "high": ["high", "High", "最高", "最高价"],
    "low": ["low", "Low", "最低", "最低价"],
    "close": ["close", "Close", "adj_close", "Adj Close", "收盘", "收盘价", "复权收盘价"],
    "volume": ["volume", "Volume", "vol", "成交量", "成交股数"],
    "amount": ["amount", "Amount", "turnover", "Turnover", "成交额", "成交金额"],
}


def standardize_price_columns(
    df: pd.DataFrame,
    column_mapping: dict[str, str] | None = None,
    default_symbol: str | None = None,
) -> pd.DataFrame:
    """Convert external price columns into the project standard market data schema."""
    result = pd.DataFrame(index=df.index)
    resolved_mapping = _resolve_column_mapping(df, column_mapping=column_mapping)

    for source_column, target_column in resolved_mapping.items():
        result[target_column] = df[source_column]

    if "symbol" not in result.columns and default_symbol is not None:
        result["symbol"] = default_symbol

    missing = [column for column in STANDARD_COLUMNS if column not in result.columns]
    if missing:
        raise ValueError(f"Missing required standardized columns: {', '.join(missing)}")

    return result[STANDARD_COLUMNS].reset_index(drop=True)


def standardize_price_csv(
    input_path: str | Path,
    output_path: str | Path | None = None,
    column_mapping: dict[str, str] | None = None,
    default_symbol: str | None = None,
) -> pd.DataFrame:
    """Read an external CSV, standardize price columns, optionally save, and return it."""
    raw = pd.read_csv(input_path)
    standardized = standardize_price_columns(
        raw,
        column_mapping=column_mapping,
        default_symbol=default_symbol,
    )

    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        standardized.to_csv(path, index=False)

    return standardized


def _resolve_column_mapping(
    df: pd.DataFrame,
    column_mapping: dict[str, str] | None = None,
) -> dict[str, str]:
    resolved: dict[str, str] = {}
    used_targets: set[str] = set()

    if column_mapping:
        for source_column, target_column in column_mapping.items():
            if target_column not in STANDARD_COLUMNS:
                raise ValueError(f"Unsupported target column in column_mapping: {target_column}")
            if source_column not in df.columns:
                raise ValueError(f"Mapped source column not found: {source_column}")
            resolved[source_column] = target_column
            used_targets.add(target_column)

    for target_column, aliases in COLUMN_ALIASES.items():
        if target_column in used_targets:
            continue
        for alias in aliases:
            if alias in df.columns and alias not in resolved:
                resolved[alias] = target_column
                used_targets.add(target_column)
                break

    return resolved
