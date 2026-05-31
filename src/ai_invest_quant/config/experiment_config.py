"""Load, validate, and save local experiment JSON configuration files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_EXPERIMENT_CONFIG: dict[str, Any] = {
    "csv_path": "data/samples/sample_etf_prices.csv",
    "output_dir": "outputs/dashboard_demo",
    "initial_cash": 1_000_000,
    "rebalance_interval": 5,
    "top_n": 3,
    "target_exposure": 0.8,
    "fee_rate": 0.001,
    "slippage": 0.0005,
    "use_risk_manager": True,
    "auto_run_dir": False,
    "benchmark_symbol": None,
    "out_of_sample_ratio": 0.3,
}

REQUIRED_FIELDS = tuple(DEFAULT_EXPERIMENT_CONFIG)


def load_experiment_config(path: str | Path) -> dict[str, Any]:
    """Load and validate an experiment JSON config."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Experiment config not found: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as file:
            config = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid experiment config JSON: {config_path}") from exc

    if not isinstance(config, dict):
        raise ValueError("Experiment config must be a JSON object")

    return validate_experiment_config(config)


def save_experiment_config(config: dict[str, Any], path: str | Path) -> dict[str, Any]:
    """Validate and save an experiment JSON config."""
    validated = validate_experiment_config(config)
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as file:
        json.dump(validated, file, indent=2)
        file.write("\n")
    return validated


def validate_experiment_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate required demo pipeline parameters and return normalized values."""
    missing = [field for field in REQUIRED_FIELDS if field not in config]
    if missing:
        raise ValueError(f"Missing required experiment config fields: {', '.join(missing)}")

    if not isinstance(config["use_risk_manager"], bool):
        raise ValueError("use_risk_manager must be a bool")

    if not isinstance(config["auto_run_dir"], bool):
        raise ValueError("auto_run_dir must be a bool")

    benchmark_symbol = config["benchmark_symbol"]
    if benchmark_symbol is not None:
        if not isinstance(benchmark_symbol, str) or not benchmark_symbol.strip():
            raise ValueError("benchmark_symbol must be None or a non-empty string")
        benchmark_symbol = benchmark_symbol.strip()

    try:
        out_of_sample_ratio = float(config["out_of_sample_ratio"])
    except (TypeError, ValueError) as exc:
        raise ValueError("out_of_sample_ratio must be >= 0 and < 1") from exc

    normalized = {
        "csv_path": str(config["csv_path"]),
        "output_dir": str(config["output_dir"]),
        "initial_cash": float(config["initial_cash"]),
        "rebalance_interval": int(config["rebalance_interval"]),
        "top_n": int(config["top_n"]),
        "target_exposure": float(config["target_exposure"]),
        "fee_rate": float(config["fee_rate"]),
        "slippage": float(config["slippage"]),
        "use_risk_manager": config["use_risk_manager"],
        "auto_run_dir": config["auto_run_dir"],
        "benchmark_symbol": benchmark_symbol,
        "out_of_sample_ratio": out_of_sample_ratio,
    }

    if normalized["initial_cash"] <= 0:
        raise ValueError("initial_cash must be > 0")
    if normalized["rebalance_interval"] <= 0:
        raise ValueError("rebalance_interval must be > 0")
    if normalized["top_n"] <= 0:
        raise ValueError("top_n must be > 0")
    if normalized["target_exposure"] < 0 or normalized["target_exposure"] > 1:
        raise ValueError("target_exposure must be >= 0 and <= 1")
    if normalized["fee_rate"] < 0:
        raise ValueError("fee_rate must be >= 0")
    if normalized["slippage"] < 0:
        raise ValueError("slippage must be >= 0")
    if normalized["out_of_sample_ratio"] < 0 or normalized["out_of_sample_ratio"] >= 1:
        raise ValueError("out_of_sample_ratio must be >= 0 and < 1")

    return normalized
