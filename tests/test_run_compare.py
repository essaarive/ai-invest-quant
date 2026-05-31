import json
from pathlib import Path

import pandas as pd

from ai_invest_quant.report.run_compare import load_runs_for_comparison


def write_run(
    run_dir: Path,
    *,
    total_return: float,
    annual_return: float,
    max_drawdown: float,
    sharpe_ratio: float,
    top_n: int,
    with_nav: bool = True,
) -> dict:
    run_dir.mkdir(parents=True)
    if with_nav:
        pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "equity": [1000.0, 1020.0, 1010.0],
            }
        ).to_csv(run_dir / "nav.csv", index=False)

    metadata = {
        "run_time": f"2026-05-31T03:{top_n:02d}:00",
        "actual_output_dir": str(run_dir),
        "config": {
            "initial_cash": 1_000_000,
            "rebalance_interval": 5,
            "top_n": top_n,
            "target_exposure": 0.8,
            "fee_rate": 0.001,
            "slippage": 0.0005,
            "use_risk_manager": True,
            "auto_run_dir": True,
        },
        "summary": {
            "total_return": total_return,
            "annual_return": annual_return,
            "max_drawdown": max_drawdown,
            "annual_volatility": 0.12,
            "sharpe_ratio": sharpe_ratio,
            "calmar_ratio": 1.5,
            "rebalance_win_rate": 0.6,
        },
        "output_paths": {
            "nav": str(run_dir / "nav.csv"),
            "metadata": str(run_dir / "metadata.json"),
        },
    }
    (run_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    return {
        "run_time": metadata["run_time"],
        "run_id": run_dir.name,
        "actual_output_dir": str(run_dir),
        "total_return": total_return,
        "annual_return": annual_return,
        "max_drawdown": max_drawdown,
        "annual_volatility": 0.12,
        "sharpe_ratio": sharpe_ratio,
        "calmar_ratio": 1.5,
        "rebalance_win_rate": 0.6,
        "initial_cash": 1_000_000,
        "rebalance_interval": 5,
        "top_n": top_n,
        "target_exposure": 0.8,
        "fee_rate": 0.001,
        "slippage": 0.0005,
        "use_risk_manager": True,
        "metadata_path": str(run_dir / "metadata.json"),
    }


def test_load_runs_for_comparison_loads_metrics_and_configs(tmp_path):
    rows = [
        write_run(
            tmp_path / "runs" / "20260531_031530",
            total_return=0.1,
            annual_return=0.2,
            max_drawdown=-0.05,
            sharpe_ratio=1.2,
            top_n=3,
        ),
        write_run(
            tmp_path / "runs" / "20260531_031531",
            total_return=0.2,
            annual_return=0.3,
            max_drawdown=-0.08,
            sharpe_ratio=1.5,
            top_n=2,
        ),
    ]

    result = load_runs_for_comparison(pd.DataFrame(rows))

    assert list(result["metrics"]["run_id"]) == ["20260531_031530", "20260531_031531"]
    assert list(result["metrics"]["total_return"]) == [0.1, 0.2]
    assert list(result["configs"]["top_n"]) == [3, 2]
    assert list(result["configs"]["auto_run_dir"]) == [True, True]


def test_load_runs_for_comparison_generates_normalized_nav(tmp_path):
    rows = [
        write_run(
            tmp_path / "runs" / "20260531_031530",
            total_return=0.1,
            annual_return=0.2,
            max_drawdown=-0.05,
            sharpe_ratio=1.2,
            top_n=3,
        ),
        write_run(
            tmp_path / "runs" / "20260531_031531",
            total_return=0.2,
            annual_return=0.3,
            max_drawdown=-0.08,
            sharpe_ratio=1.5,
            top_n=2,
        ),
    ]

    result = load_runs_for_comparison(rows)
    nav_comparison = result["nav_comparison"]

    assert list(nav_comparison.columns) == ["20260531_031530", "20260531_031531"]
    assert nav_comparison.iloc[0]["20260531_031530"] == 1.0
    assert nav_comparison.iloc[0]["20260531_031531"] == 1.0


def test_load_runs_for_comparison_missing_nav_does_not_crash(tmp_path):
    rows = [
        write_run(
            tmp_path / "runs" / "20260531_031530",
            total_return=0.1,
            annual_return=0.2,
            max_drawdown=-0.05,
            sharpe_ratio=1.2,
            top_n=3,
        ),
        write_run(
            tmp_path / "runs" / "20260531_031531",
            total_return=0.2,
            annual_return=0.3,
            max_drawdown=-0.08,
            sharpe_ratio=1.5,
            top_n=2,
            with_nav=False,
        ),
    ]

    result = load_runs_for_comparison(pd.DataFrame(rows))

    assert "Missing nav.csv for run 20260531_031531" in result["missing_files"]
    assert list(result["nav_comparison"].columns) == ["20260531_031530"]
