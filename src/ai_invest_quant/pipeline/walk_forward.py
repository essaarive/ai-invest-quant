"""Lightweight walk-forward testing pipeline for ETF rotation experiments."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ai_invest_quant.data.loader import load_csv
from ai_invest_quant.pipeline.run_etf_rotation_demo import run_etf_rotation_demo

WALK_FORWARD_COLUMNS = [
    "window_id",
    "train_start",
    "train_end",
    "test_start",
    "test_end",
    "actual_output_dir",
    "total_return",
    "annual_return",
    "max_drawdown",
    "annual_volatility",
    "sharpe_ratio",
    "calmar_ratio",
    "rebalance_win_rate",
    "benchmark_total_return",
    "benchmark_max_drawdown",
    "excess_total_return",
]


def run_walk_forward_test(
    csv_path,
    output_dir="outputs/walk_forward",
    train_window_days=120,
    test_window_days=60,
    step_days=60,
    initial_cash=1_000_000,
    rebalance_interval=5,
    top_n=3,
    target_exposure=0.8,
    fee_rate=0.001,
    slippage=0.0005,
    use_risk_manager=True,
    benchmark_symbol=None,
) -> dict[str, object]:
    """Run rolling train/test walk-forward windows and summarize test-window results."""
    train_window_days = _validate_positive_int(train_window_days, "train_window_days")
    test_window_days = _validate_positive_int(test_window_days, "test_window_days")
    step_days = _validate_positive_int(step_days, "step_days")

    data = load_csv(csv_path)
    trading_dates = pd.Index(pd.Series(data["date"].drop_duplicates()).sort_values())
    windows = _build_windows(
        trading_dates=trading_dates,
        train_window_days=train_window_days,
        test_window_days=test_window_days,
        step_days=step_days,
    )
    if not windows:
        raise ValueError("Not enough data to generate at least one walk-forward window")

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    window_data_dir = output_root / "window_data"
    window_data_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    runs: list[dict[str, object]] = []
    for window in windows:
        window_id = window["window_id"]
        test_mask = (data["date"] >= window["test_start"]) & (data["date"] <= window["test_end"])
        test_data = data[test_mask]
        test_csv_path = window_data_dir / f"{window_id}.csv"
        test_data.to_csv(test_csv_path, index=False)

        result = run_etf_rotation_demo(
            csv_path=test_csv_path,
            output_dir=output_root,
            initial_cash=initial_cash,
            rebalance_interval=rebalance_interval,
            top_n=top_n,
            target_exposure=target_exposure,
            fee_rate=fee_rate,
            slippage=slippage,
            use_risk_manager=use_risk_manager,
            auto_run_dir=True,
            benchmark_symbol=benchmark_symbol,
            out_of_sample_ratio=0,
        )
        runs.append(result)
        rows.append(_build_summary_row(window=window, result=result))

    summary = pd.DataFrame(rows).reindex(columns=WALK_FORWARD_COLUMNS)
    summary_path = output_root / "walk_forward_summary.csv"
    summary.to_csv(summary_path, index=False)
    return {
        "summary": summary,
        "summary_path": str(summary_path),
        "runs": runs,
    }


def _build_windows(
    trading_dates: pd.Index,
    train_window_days: int,
    test_window_days: int,
    step_days: int,
) -> list[dict[str, object]]:
    windows: list[dict[str, object]] = []
    start = 0
    window_number = 1
    total_required = train_window_days + test_window_days
    while start + total_required <= len(trading_dates):
        train_start_index = start
        train_end_index = start + train_window_days - 1
        test_start_index = train_end_index + 1
        test_end_index = test_start_index + test_window_days - 1
        windows.append(
            {
                "window_id": f"window_{window_number:03d}",
                "train_start": trading_dates[train_start_index],
                "train_end": trading_dates[train_end_index],
                "test_start": trading_dates[test_start_index],
                "test_end": trading_dates[test_end_index],
            }
        )
        start += step_days
        window_number += 1
    return windows


def _build_summary_row(window: dict[str, object], result: dict[str, object]) -> dict[str, object]:
    summary = result["summary"]
    if not isinstance(summary, dict):
        raise ValueError("run result summary must be a dict")

    row = {
        **window,
        "actual_output_dir": result["actual_output_dir"],
    }
    for key in WALK_FORWARD_COLUMNS:
        if key not in row:
            row[key] = summary.get(key)
    return row


def _validate_positive_int(value: int, name: str) -> int:
    try:
        normalized = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a positive integer") from exc
    if normalized <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return normalized
