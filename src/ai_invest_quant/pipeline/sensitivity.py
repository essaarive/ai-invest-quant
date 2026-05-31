"""Lightweight parameter sensitivity runner for ETF rotation experiments."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ai_invest_quant.pipeline.run_etf_rotation_demo import run_etf_rotation_demo

SENSITIVITY_COLUMNS = [
    "run_id",
    "actual_output_dir",
    "top_n",
    "target_exposure",
    "rebalance_interval",
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
    "in_sample_total_return",
    "out_of_sample_total_return",
    "out_of_sample_max_drawdown",
    "out_of_sample_sharpe_ratio",
]


def run_parameter_sensitivity(
    csv_path,
    output_dir="outputs/sensitivity",
    top_n_values=None,
    target_exposure_values=None,
    rebalance_interval_values=None,
    initial_cash=1_000_000,
    fee_rate=0.001,
    slippage=0.0005,
    use_risk_manager=True,
    benchmark_symbol=None,
    out_of_sample_ratio=0.3,
) -> dict[str, object]:
    """Run multiple ETF rotation parameter combinations and summarize results."""
    top_n_values = top_n_values or [1, 2, 3]
    target_exposure_values = target_exposure_values or [0.5, 0.8]
    rebalance_interval_values = rebalance_interval_values or [5, 10]

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    runs: list[dict[str, object]] = []
    for top_n in top_n_values:
        for target_exposure in target_exposure_values:
            for rebalance_interval in rebalance_interval_values:
                result = run_etf_rotation_demo(
                    csv_path=csv_path,
                    output_dir=output_root,
                    initial_cash=initial_cash,
                    rebalance_interval=int(rebalance_interval),
                    top_n=int(top_n),
                    target_exposure=float(target_exposure),
                    fee_rate=fee_rate,
                    slippage=slippage,
                    use_risk_manager=use_risk_manager,
                    auto_run_dir=True,
                    benchmark_symbol=benchmark_symbol,
                    out_of_sample_ratio=out_of_sample_ratio,
                )
                runs.append(result)
                rows.append(
                    _build_summary_row(
                        result=result,
                        top_n=int(top_n),
                        target_exposure=float(target_exposure),
                        rebalance_interval=int(rebalance_interval),
                    )
                )

    summary = pd.DataFrame(rows).reindex(columns=SENSITIVITY_COLUMNS)
    summary_path = output_root / "sensitivity_summary.csv"
    summary.to_csv(summary_path, index=False)
    return {
        "summary": summary,
        "summary_path": str(summary_path),
        "runs": runs,
    }


def _build_summary_row(
    result: dict[str, object],
    top_n: int,
    target_exposure: float,
    rebalance_interval: int,
) -> dict[str, object]:
    actual_output_dir = str(result["actual_output_dir"])
    summary = result["summary"]
    if not isinstance(summary, dict):
        raise ValueError("run result summary must be a dict")

    row = {
        "run_id": Path(actual_output_dir).name,
        "actual_output_dir": actual_output_dir,
        "top_n": top_n,
        "target_exposure": target_exposure,
        "rebalance_interval": rebalance_interval,
    }
    for key in SENSITIVITY_COLUMNS:
        if key not in row:
            row[key] = summary.get(key)
    return row
