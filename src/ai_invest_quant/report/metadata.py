"""Experiment metadata generation for backtest outputs."""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ai_invest_quant import __version__

SUMMARY_KEYS = (
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
    "in_sample_max_drawdown",
    "in_sample_sharpe_ratio",
    "out_of_sample_total_return",
    "out_of_sample_max_drawdown",
    "out_of_sample_sharpe_ratio",
    "split_date",
)


def build_metadata(
    config: dict[str, Any],
    summary: dict[str, Any],
    output_paths: dict[str, str],
    actual_output_dir: str | None = None,
    strategy_name: str = "ETF Rotation Strategy",
    run_time: str | None = None,
) -> dict[str, Any]:
    """Build JSON-serializable experiment metadata."""
    metadata = {
        "project": "ai-invest-quant",
        "version": __version__,
        "strategy_name": strategy_name,
        "run_time": run_time or datetime.now().isoformat(timespec="seconds"),
        "actual_output_dir": actual_output_dir,
        "config": config,
        "summary": {key: summary.get(key) for key in SUMMARY_KEYS},
        "output_paths": output_paths,
    }
    return _json_safe(metadata)


def write_metadata(
    path: str | Path,
    config: dict[str, Any],
    summary: dict[str, Any],
    output_paths: dict[str, str],
    actual_output_dir: str | None = None,
    strategy_name: str = "ETF Rotation Strategy",
) -> dict[str, Any]:
    """Write experiment metadata JSON and return the metadata dict."""
    metadata = build_metadata(
        config=config,
        summary=summary,
        output_paths=output_paths,
        actual_output_dir=actual_output_dir,
        strategy_name=strategy_name,
    )
    metadata_path = Path(path)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, allow_nan=False)
        file.write("\n")
    return metadata


def _json_safe(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if hasattr(value, "item"):
        return _json_safe(value.item())

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value

    return value
