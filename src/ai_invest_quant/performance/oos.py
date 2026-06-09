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
from ai_invest_quant.performance.utils import prepare_nav_dataframe


def split_nav_in_out_sample(
    nav_df: pd.DataFrame, out_of_sample_ratio: float = 0.3
) -> dict[str, Any]:
    """Split NAV into in-sample and out-of-sample periods by date."""
    ratio = _validate_ratio(out_of_sample_ratio)
    nav = prepare_nav_dataframe(nav_df)

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


def _validate_ratio(out_of_sample_ratio: float) -> float:
    try:
        ratio = float(out_of_sample_ratio)
    except (TypeError, ValueError) as exc:
        raise ValueError("out_of_sample_ratio must be >= 0 and < 1") from exc
    if ratio < 0 or ratio >= 1:
        raise ValueError("out_of_sample_ratio must be >= 0 and < 1")
    return ratio
