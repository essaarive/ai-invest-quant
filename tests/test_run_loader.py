import json
from pathlib import Path

import pandas as pd

from ai_invest_quant.report.run_loader import load_historical_run


def write_historical_run(run_dir: Path) -> None:
    run_dir.mkdir(parents=True)
    pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "cash": [1000.0, 900.0],
            "positions_value": [0.0, 120.0],
            "equity": [1000.0, 1020.0],
            "nav": [1.0, 1.02],
            "risk_mode": ["normal", "normal"],
            "drawdown": [0.0, 0.0],
        }
    ).to_csv(run_dir / "nav.csv", index=False)
    pd.DataFrame(
        {
            "trade_date": ["2024-01-02"],
            "symbol": ["ETF_A"],
            "side": ["buy"],
            "quantity": [1.0],
            "price": [100.0],
            "trade_amount": [100.0],
            "fee": [0.1],
        }
    ).to_csv(run_dir / "trades.csv", index=False)
    pd.DataFrame(
        {
            "date": ["2024-01-02"],
            "symbol": ["ETF_A"],
            "quantity": [1.0],
            "close": [120.0],
            "market_value": [120.0],
            "weight": [0.1176],
        }
    ).to_csv(run_dir / "positions.csv", index=False)
    pd.DataFrame(
        {
            "signal_date": ["2024-01-01"],
            "execute_date": ["2024-01-02"],
            "symbol": ["ETF_A"],
            "target_weight": [0.3],
        }
    ).to_csv(run_dir / "signals.csv", index=False)
    (run_dir / "report.md").write_text("# ETF Rotation Backtest Report\n", encoding="utf-8")
    metadata = {
        "summary": {"total_return": 0.02, "sharpe_ratio": 1.2},
        "actual_output_dir": str(run_dir),
        "output_paths": {
            "nav": str(run_dir / "nav.csv"),
            "trades": str(run_dir / "trades.csv"),
            "positions": str(run_dir / "positions.csv"),
            "signals": str(run_dir / "signals.csv"),
            "report": str(run_dir / "report.md"),
            "metadata": str(run_dir / "metadata.json"),
        },
    }
    (run_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")


def test_load_historical_run_loads_all_outputs(tmp_path):
    run_dir = tmp_path / "runs" / "20260531_031530"
    write_historical_run(run_dir)
    (tmp_path / "runs" / "index.csv").write_text("run_time,run_id\n", encoding="utf-8")

    result = load_historical_run(run_dir)

    assert set(
        [
            "nav",
            "trades",
            "positions",
            "signals",
            "summary",
            "report",
            "output_paths",
            "actual_output_dir",
            "metadata",
            "missing_files",
        ]
    ).issubset(result)
    assert not result["nav"].empty
    assert not result["trades"].empty
    assert not result["positions"].empty
    assert not result["signals"].empty
    assert result["summary"]["total_return"] == 0.02
    assert "# ETF Rotation Backtest Report" in result["report"]
    assert result["output_paths"]["run_index"] == str(tmp_path / "runs" / "index.csv")
    assert result["missing_files"] == []


def test_load_historical_run_missing_files_returns_empty_outputs(tmp_path):
    run_dir = tmp_path / "runs" / "20260531_031530"
    run_dir.mkdir(parents=True)
    pd.DataFrame({"date": ["2024-01-01"], "nav": [1.0]}).to_csv(run_dir / "nav.csv", index=False)

    result = load_historical_run(run_dir)

    assert not result["nav"].empty
    assert result["trades"].empty
    assert result["positions"].empty
    assert result["signals"].empty
    assert result["report"] == ""
    assert result["metadata"] == {}
    assert result["summary"] == {}
    assert set(result["missing_files"]) == {
        "trades.csv",
        "positions.csv",
        "signals.csv",
        "report.md",
        "metadata.json",
    }


def test_load_historical_run_output_paths_point_to_run_directory(tmp_path):
    run_dir = tmp_path / "runs" / "20260531_031530"
    write_historical_run(run_dir)

    result = load_historical_run(run_dir)

    for key in ["nav", "trades", "positions", "signals", "report", "metadata"]:
        assert result["output_paths"][key] == str(run_dir / f"{key}.csv") or (
            key == "report"
            and result["output_paths"][key] == str(run_dir / "report.md")
        ) or (
            key == "metadata"
            and result["output_paths"][key] == str(run_dir / "metadata.json")
        )
