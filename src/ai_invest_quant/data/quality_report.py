"""Data quality checks for standardized OHLCV market data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ai_invest_quant.data.constants import BASE_PRICE_COLUMNS, OHLC_COLUMNS, PRICE_NUMERIC_COLUMNS

REQUIRED_COLUMNS = BASE_PRICE_COLUMNS
PRICE_COLUMNS = OHLC_COLUMNS


def generate_data_quality_report(
    price_df: pd.DataFrame,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    """Generate a per-symbol data quality report for standardized OHLCV data."""
    _validate_input(price_df)

    data = price_df[list(REQUIRED_COLUMNS)].copy()
    data["date"] = pd.to_datetime(data["date"], errors="raise")

    rows = []
    for symbol, group in data.groupby("symbol", sort=True):
        rows.append(_build_symbol_report(str(symbol), group))

    report = pd.DataFrame(
        rows,
        columns=[
            "symbol",
            "start_date",
            "end_date",
            "row_count",
            "unique_date_count",
            "duplicate_date_count",
            "missing_value_count",
            "missing_open_count",
            "missing_high_count",
            "missing_low_count",
            "missing_close_count",
            "missing_volume_count",
            "missing_amount_count",
            "zero_or_negative_price_count",
            "high_low_error_count",
            "negative_volume_count",
            "negative_amount_count",
            "is_passed",
            "issues",
        ],
    )

    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        report.to_csv(path, index=False)

    return report


def _validate_input(price_df: pd.DataFrame) -> None:
    if price_df.empty:
        raise ValueError("price_df cannot be empty")

    missing = [column for column in REQUIRED_COLUMNS if column not in price_df.columns]
    if missing:
        raise ValueError(f"Missing required price columns: {', '.join(missing)}")


def _build_symbol_report(symbol: str, group: pd.DataFrame) -> dict[str, object]:
    numeric = group.copy()
    for column in PRICE_NUMERIC_COLUMNS:
        numeric[column] = pd.to_numeric(numeric[column], errors="coerce")

    missing_counts = {
        column: int(_missing_mask(group[column]).sum())
        for column in PRICE_NUMERIC_COLUMNS
    }
    duplicate_date_count = int(group["date"].duplicated().sum())
    zero_or_negative_price_count = int((numeric[list(PRICE_COLUMNS)].le(0)).any(axis=1).sum())
    high_low_error_count = int((numeric["high"] < numeric["low"]).sum())
    negative_volume_count = int((numeric["volume"] < 0).sum())
    negative_amount_count = int((numeric["amount"] < 0).sum())

    issues = _collect_issues(
        duplicate_date_count=duplicate_date_count,
        missing_counts=missing_counts,
        zero_or_negative_price_count=zero_or_negative_price_count,
        high_low_error_count=high_low_error_count,
        negative_volume_count=negative_volume_count,
        negative_amount_count=negative_amount_count,
    )
    is_passed = _is_passed(
        duplicate_date_count=duplicate_date_count,
        missing_counts=missing_counts,
        zero_or_negative_price_count=zero_or_negative_price_count,
        high_low_error_count=high_low_error_count,
        negative_volume_count=negative_volume_count,
        negative_amount_count=negative_amount_count,
    )

    return {
        "symbol": symbol,
        "start_date": group["date"].min().strftime("%Y-%m-%d"),
        "end_date": group["date"].max().strftime("%Y-%m-%d"),
        "row_count": int(len(group)),
        "unique_date_count": int(group["date"].nunique()),
        "duplicate_date_count": duplicate_date_count,
        "missing_value_count": int(_missing_mask(group[list(REQUIRED_COLUMNS)]).sum().sum()),
        "missing_open_count": missing_counts["open"],
        "missing_high_count": missing_counts["high"],
        "missing_low_count": missing_counts["low"],
        "missing_close_count": missing_counts["close"],
        "missing_volume_count": missing_counts["volume"],
        "missing_amount_count": missing_counts["amount"],
        "zero_or_negative_price_count": zero_or_negative_price_count,
        "high_low_error_count": high_low_error_count,
        "negative_volume_count": negative_volume_count,
        "negative_amount_count": negative_amount_count,
        "is_passed": is_passed,
        "issues": "; ".join(issues),
    }


def _missing_mask(values: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    if isinstance(values, pd.Series):
        return values.isna() | values.astype(str).str.strip().eq("")
    return values.isna() | values.astype(str).apply(lambda column: column.str.strip().eq(""))


def _collect_issues(
    duplicate_date_count: int,
    missing_counts: dict[str, int],
    zero_or_negative_price_count: int,
    high_low_error_count: int,
    negative_volume_count: int,
    negative_amount_count: int,
) -> list[str]:
    issues = []
    if duplicate_date_count > 0:
        issues.append("duplicate dates found")
    for column, count in missing_counts.items():
        if count > 0:
            issues.append(f"missing {column} values")
    if zero_or_negative_price_count > 0:
        issues.append("zero or negative price values found")
    if high_low_error_count > 0:
        issues.append("high lower than low found")
    if negative_volume_count > 0:
        issues.append("negative volume found")
    if negative_amount_count > 0:
        issues.append("negative amount found")
    return issues


def _is_passed(
    duplicate_date_count: int,
    missing_counts: dict[str, int],
    zero_or_negative_price_count: int,
    high_low_error_count: int,
    negative_volume_count: int,
    negative_amount_count: int,
) -> bool:
    return not (
        duplicate_date_count > 0
        or any(missing_counts[column] > 0 for column in PRICE_COLUMNS)
        or zero_or_negative_price_count > 0
        or high_low_error_count > 0
        or negative_volume_count > 0
        or negative_amount_count > 0
    )
