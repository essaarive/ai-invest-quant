"""Helpers for comparing completed historical backtest runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

METRIC_COLUMNS = [
    "total_return",
    "annual_return",
    "max_drawdown",
    "annual_volatility",
    "sharpe_ratio",
    "calmar_ratio",
    "rebalance_win_rate",
]

CONFIG_COLUMNS = [
    "initial_cash",
    "rebalance_interval",
    "top_n",
    "target_exposure",
    "fee_rate",
    "slippage",
    "use_risk_manager",
    "auto_run_dir",
]


def load_runs_for_comparison(
    selected_rows: pd.DataFrame | Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Load metrics, configs, and normalized NAV series for selected historical runs.

    This function only reads local run output files and never reruns a backtest.
    Missing per-run files are recorded in ``missing_files`` and do not stop the
    remaining runs from loading.
    """
    rows = _to_dataframe(selected_rows)
    if rows.empty:
        return {
            "metrics": pd.DataFrame(columns=["run_id", *METRIC_COLUMNS]),
            "configs": pd.DataFrame(columns=["run_id", *CONFIG_COLUMNS]),
            "nav_comparison": pd.DataFrame(),
            "missing_files": [],
        }

    metric_rows: list[dict[str, Any]] = []
    config_rows: list[dict[str, Any]] = []
    nav_series: list[pd.Series] = []
    missing_files: list[str] = []

    for row in rows.to_dict(orient="records"):
        metadata = _load_metadata(row)
        run_id = _run_id(row, metadata)
        metric_rows.append(
            _comparison_row(run_id, METRIC_COLUMNS, row, metadata.get("summary", {}))
        )
        config_rows.append(_comparison_row(run_id, CONFIG_COLUMNS, row, metadata.get("config", {})))

        nav = _load_normalized_nav(row, metadata, run_id, missing_files)
        if nav is not None:
            nav_series.append(nav)

    nav_comparison = pd.concat(nav_series, axis=1) if nav_series else pd.DataFrame()
    return {
        "metrics": pd.DataFrame(metric_rows, columns=["run_id", *METRIC_COLUMNS]),
        "configs": pd.DataFrame(config_rows, columns=["run_id", *CONFIG_COLUMNS]),
        "nav_comparison": nav_comparison,
        "missing_files": missing_files,
    }


def _to_dataframe(selected_rows: pd.DataFrame | Iterable[dict[str, Any]]) -> pd.DataFrame:
    if isinstance(selected_rows, pd.DataFrame):
        return selected_rows.reset_index(drop=True)
    return pd.DataFrame(list(selected_rows))


def _load_metadata(row: dict[str, Any]) -> dict[str, Any]:
    metadata_path = _valid_path(row.get("metadata_path"))
    if metadata_path is None:
        actual_output_dir = _valid_path(row.get("actual_output_dir"))
        if actual_output_dir is not None:
            metadata_path = actual_output_dir / "metadata.json"

    if metadata_path is None or not metadata_path.exists():
        return {}

    try:
        with metadata_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _load_normalized_nav(
    row: dict[str, Any],
    metadata: dict[str, Any],
    run_id: str,
    missing_files: list[str],
) -> pd.Series | None:
    nav_path = _nav_path(row, metadata)
    if nav_path is None or not nav_path.exists():
        missing_files.append(f"Missing nav.csv for run {run_id}")
        return None

    try:
        nav = pd.read_csv(nav_path)
    except Exception:
        missing_files.append(f"Missing nav.csv for run {run_id}")
        return None

    if nav.empty or "date" not in nav.columns or "equity" not in nav.columns:
        missing_files.append(f"Missing nav.csv for run {run_id}")
        return None

    nav = nav[["date", "equity"]].copy()
    nav["date"] = pd.to_datetime(nav["date"], errors="coerce")
    nav["equity"] = pd.to_numeric(nav["equity"], errors="coerce")
    nav = nav.dropna(subset=["date", "equity"]).sort_values("date")
    if nav.empty or nav["equity"].iloc[0] <= 0:
        missing_files.append(f"Missing nav.csv for run {run_id}")
        return None

    normalized = nav["equity"] / nav["equity"].iloc[0]
    normalized.index = nav["date"]
    normalized.name = run_id
    return normalized


def _nav_path(row: dict[str, Any], metadata: dict[str, Any]) -> Path | None:
    output_paths = metadata.get("output_paths", {})
    path = _valid_path(output_paths.get("nav"))
    if path is not None:
        return path

    actual_output_dir = _valid_path(
        row.get("actual_output_dir") or metadata.get("actual_output_dir")
    )
    if actual_output_dir is None:
        return None
    return actual_output_dir / "nav.csv"


def _comparison_row(
    run_id: str,
    columns: list[str],
    row: dict[str, Any],
    fallback: dict[str, Any],
) -> dict[str, Any]:
    values = {"run_id": run_id}
    for column in columns:
        values[column] = _first_valid(row.get(column), fallback.get(column))
    return values


def _run_id(row: dict[str, Any], metadata: dict[str, Any]) -> str:
    run_id = _first_valid(row.get("run_id"), None)
    if run_id is not None:
        return str(run_id)

    actual_output_dir = _first_valid(
        row.get("actual_output_dir"), metadata.get("actual_output_dir")
    )
    if actual_output_dir is not None:
        return Path(str(actual_output_dir)).name
    return "unknown"


def _first_valid(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        try:
            if pd.isna(value):
                continue
        except (TypeError, ValueError):
            pass
        return value
    return None


def _valid_path(value: Any) -> Path | None:
    value = _first_valid(value)
    if value is None:
        return None
    return Path(str(value))
