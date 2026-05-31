"""Load completed backtest run outputs from disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


OUTPUT_FILES = {
    "nav": "nav.csv",
    "trades": "trades.csv",
    "positions": "positions.csv",
    "signals": "signals.csv",
    "report": "report.md",
    "metadata": "metadata.json",
}

EMPTY_COLUMNS = {
    "nav": ["date", "cash", "positions_value", "equity", "nav", "risk_mode", "drawdown"],
    "trades": ["trade_date", "symbol", "side", "quantity", "price", "trade_amount", "fee"],
    "positions": ["date", "symbol", "quantity", "close", "market_value", "weight"],
    "signals": ["signal_date", "execute_date", "symbol", "target_weight"],
}


def load_historical_run(actual_output_dir: str | Path) -> dict[str, Any]:
    """Load a historical run output directory without rerunning a backtest."""
    run_dir = Path(actual_output_dir)
    output_paths = {key: str(run_dir / file_name) for key, file_name in OUTPUT_FILES.items()}
    run_index_path = run_dir.parent / "index.csv"
    if run_index_path.exists():
        output_paths["run_index"] = str(run_index_path)

    missing_files: list[str] = []
    nav = _read_csv_or_empty(output_paths["nav"], "nav", missing_files)
    trades = _read_csv_or_empty(output_paths["trades"], "trades", missing_files)
    positions = _read_csv_or_empty(output_paths["positions"], "positions", missing_files)
    signals = _read_csv_or_empty(output_paths["signals"], "signals", missing_files)
    report = _read_text_or_empty(output_paths["report"], missing_files)
    metadata = _read_metadata_or_empty(output_paths["metadata"], missing_files)

    return {
        "nav": nav,
        "trades": trades,
        "positions": positions,
        "signals": signals,
        "summary": metadata.get("summary", {}) if isinstance(metadata, dict) else {},
        "report": report,
        "output_paths": output_paths,
        "actual_output_dir": str(run_dir),
        "metadata": metadata,
        "missing_files": missing_files,
    }


def _read_csv_or_empty(path: str, key: str, missing_files: list[str]) -> pd.DataFrame:
    file_path = Path(path)
    if not file_path.exists():
        missing_files.append(file_path.name)
        return pd.DataFrame(columns=EMPTY_COLUMNS[key])
    return pd.read_csv(file_path)


def _read_text_or_empty(path: str, missing_files: list[str]) -> str:
    file_path = Path(path)
    if not file_path.exists():
        missing_files.append(file_path.name)
        return ""
    return file_path.read_text(encoding="utf-8")


def _read_metadata_or_empty(path: str, missing_files: list[str]) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        missing_files.append(file_path.name)
        return {}
    try:
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        missing_files.append(file_path.name)
        return {}

