"""Run history index helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

RUN_INDEX_COLUMNS = [
    "run_time",
    "run_id",
    "actual_output_dir",
    "strategy_name",
    "csv_path",
    "initial_cash",
    "rebalance_interval",
    "top_n",
    "target_exposure",
    "fee_rate",
    "slippage",
    "use_risk_manager",
    "total_return",
    "annual_return",
    "max_drawdown",
    "annual_volatility",
    "sharpe_ratio",
    "calmar_ratio",
    "rebalance_win_rate",
    "metadata_path",
    "report_path",
]


def append_run_index(index_path: str | Path, metadata: dict[str, Any]) -> None:
    """Append or update a run record in index.csv."""
    path = Path(index_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = load_run_index(path)
    row = _metadata_to_row(metadata)
    if not existing.empty and "actual_output_dir" in existing.columns:
        existing = existing[existing["actual_output_dir"] != row["actual_output_dir"]]

    new_row = pd.DataFrame([row])
    updated = new_row if existing.empty else pd.concat([existing, new_row], ignore_index=True)
    updated = updated.reindex(columns=RUN_INDEX_COLUMNS)
    updated.to_csv(path, index=False)


def load_run_index(index_path: str | Path) -> pd.DataFrame:
    """Load run index sorted by run_time descending."""
    path = Path(index_path)
    if not path.exists():
        return pd.DataFrame(columns=RUN_INDEX_COLUMNS)

    index = pd.read_csv(path)
    if "run_time" in index.columns:
        index = index.sort_values("run_time", ascending=False, kind="mergesort")
    return index.reset_index(drop=True)


def _metadata_to_row(metadata: dict[str, Any]) -> dict[str, Any]:
    config = metadata.get("config", {})
    summary = metadata.get("summary", {})
    output_paths = metadata.get("output_paths", {})
    actual_output_dir = metadata.get("actual_output_dir")

    return {
        "run_time": metadata.get("run_time"),
        "run_id": Path(actual_output_dir).name if actual_output_dir else None,
        "actual_output_dir": actual_output_dir,
        "strategy_name": metadata.get("strategy_name"),
        "csv_path": config.get("csv_path"),
        "initial_cash": config.get("initial_cash"),
        "rebalance_interval": config.get("rebalance_interval"),
        "top_n": config.get("top_n"),
        "target_exposure": config.get("target_exposure"),
        "fee_rate": config.get("fee_rate"),
        "slippage": config.get("slippage"),
        "use_risk_manager": config.get("use_risk_manager"),
        "total_return": summary.get("total_return"),
        "annual_return": summary.get("annual_return"),
        "max_drawdown": summary.get("max_drawdown"),
        "annual_volatility": summary.get("annual_volatility"),
        "sharpe_ratio": summary.get("sharpe_ratio"),
        "calmar_ratio": summary.get("calmar_ratio"),
        "rebalance_win_rate": summary.get("rebalance_win_rate"),
        "metadata_path": output_paths.get("metadata"),
        "report_path": output_paths.get("report"),
    }
