"""Out-of-sample evaluation helpers for completed backtest NAV."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from ai_invest_quant.performance.metrics import (
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_total_return,
)


def split_nav_in_out_sample(
    nav_df: pd.DataFrame, out_of_sample_ratio: float = 0.3
) -> dict[str, Any]:
    """Split NAV into in-sample and out-of-sample periods by date."""
    ratio = _validate_ratio(out_of_sample_ratio)
    nav = _prepare_nav(nav_df)

    if ratio == 0:
        return {
            "in_sample_nav": nav,
            "out_of_sample_nav": nav.iloc[0:0].copy(),
            "split_date": None,
        }

    if len(nav) < 2:
        raise ValueError("nav_df has too few rows for out-of-sample split")

    out_sample_count = max(1, math.ceil(len(nav) * ratio))
    split_index = len(nav) - out_sample_count
    if split_index <= 0:
        raise ValueError("nav_df has too few rows for the requested out_of_sample_ratio")

    in_sample_nav = nav.iloc[:split_index].reset_index(drop=True)
    out_of_sample_nav = nav.iloc[split_index:].reset_index(drop=True)
    return {
        "in_sample_nav": in_sample_nav,
        "out_of_sample_nav": out_of_sample_nav,
        "split_date": out_of_sample_nav["date"].iloc[0],
    }


def calculate_oos_summary(nav_df: pd.DataFrame, out_of_sample_ratio: float = 0.3) -> dict[str, Any]:
    """Calculate in-sample and out-of-sample summary metrics from NAV."""
    split = split_nav_in_out_sample(nav_df, out_of_sample_ratio=out_of_sample_ratio)
    if split["out_of_sample_nav"].empty:
        return {}

    in_sample_nav = split["in_sample_nav"]
    out_of_sample_nav = split["out_of_sample_nav"]
    return {
        "in_sample_total_return": calculate_total_return(in_sample_nav),
        "in_sample_max_drawdown": calculate_max_drawdown(in_sample_nav),
        "in_sample_sharpe_ratio": calculate_sharpe_ratio(in_sample_nav),
        "out_of_sample_total_return": calculate_total_return(out_of_sample_nav),
        "out_of_sample_max_drawdown": calculate_max_drawdown(out_of_sample_nav),
        "out_of_sample_sharpe_ratio": calculate_sharpe_ratio(out_of_sample_nav),
        "split_date": split["split_date"],
    }


def _prepare_nav(nav_df: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in ["date", "equity"] if column not in nav_df.columns]
    if missing:
        raise ValueError(f"Missing required nav columns: {', '.join(missing)}")
    if nav_df.empty:
        raise ValueError("nav_df cannot be empty")

    nav = nav_df.copy()
    nav["date"] = pd.to_datetime(nav["date"], errors="raise")
    nav["equity"] = pd.to_numeric(nav["equity"], errors="raise")
    if "nav" not in nav.columns:
        if nav["equity"].iloc[0] <= 0:
            raise ValueError("initial equity must be > 0")
        nav["nav"] = nav["equity"] / nav["equity"].iloc[0]
    else:
        nav["nav"] = pd.to_numeric(nav["nav"], errors="raise")
    return nav.sort_values("date", kind="mergesort").reset_index(drop=True)


def _validate_ratio(out_of_sample_ratio: float) -> float:
    try:
        ratio = float(out_of_sample_ratio)
    except (TypeError, ValueError) as exc:
        raise ValueError("out_of_sample_ratio must be >= 0 and < 1") from exc
    if ratio < 0 or ratio >= 1:
        raise ValueError("out_of_sample_ratio must be >= 0 and < 1")
    return ratio
