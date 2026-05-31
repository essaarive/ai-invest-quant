from pathlib import Path
import json
import math

import pandas as pd

from ai_invest_quant import __version__
from ai_invest_quant.pipeline.run_etf_rotation_demo import run_etf_rotation_demo


def make_demo_csv(path: Path) -> None:
    dates = pd.date_range("2024-01-01", periods=130)
    symbols = ["ETF_A", "ETF_B", "ETF_C", "ETF_D"]
    rows = []
    for day_index, date in enumerate(dates):
        for symbol_index, symbol in enumerate(symbols):
            close = 100 + day_index * (1 + symbol_index * 0.15) + symbol_index
            open_price = close - 0.2
            rows.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "symbol": symbol,
                    "open": open_price,
                    "high": close + 1.0,
                    "low": open_price - 1.0,
                    "close": close,
                    "volume": 1000 + day_index,
                    "amount": close * (1000 + day_index),
                }
            )

    pd.DataFrame(rows).to_csv(path, index=False)


def test_demo_pipeline_runs_end_to_end_and_writes_outputs(tmp_path):
    csv_path = tmp_path / "prices.csv"
    output_dir = tmp_path / "demo_outputs"
    make_demo_csv(csv_path)

    result = run_etf_rotation_demo(csv_path, output_dir=output_dir)

    assert isinstance(result, dict)
    assert set(result) == {
        "nav",
        "trades",
        "positions",
        "signals",
        "summary",
        "report",
        "output_paths",
        "actual_output_dir",
    }
    assert output_dir.exists()
    assert result["actual_output_dir"] == str(output_dir)
    assert "# ETF Rotation Backtest Report" in result["report"]
    assert "risk_mode" in result["nav"].columns
    assert "drawdown" in result["nav"].columns

    for key in ["nav", "trades", "positions", "signals", "report", "metadata"]:
        path = Path(result["output_paths"][key])
        assert path.exists()
        if key != "trades" or not result["trades"].empty:
            assert path.stat().st_size > 0

    assert not result["nav"].empty
    assert not result["signals"].empty
    assert not result["positions"].empty


def test_demo_pipeline_writes_metadata_json_with_config_summary_and_paths(tmp_path):
    csv_path = tmp_path / "prices.csv"
    output_dir = tmp_path / "metadata_outputs"
    make_demo_csv(csv_path)

    result = run_etf_rotation_demo(
        csv_path=csv_path,
        output_dir=output_dir,
        initial_cash=123456,
        rebalance_interval=4,
        top_n=2,
        target_exposure=0.6,
        fee_rate=0.002,
        slippage=0.001,
        use_risk_manager=False,
    )

    metadata_path = Path(result["output_paths"]["metadata"])
    with metadata_path.open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    assert metadata_path.exists()
    assert set(["project", "version", "strategy_name", "run_time", "config", "summary", "output_paths"]).issubset(
        metadata
    )
    assert metadata["project"] == "ai-invest-quant"
    assert metadata["version"] == __version__
    assert metadata["strategy_name"] == "ETF Rotation Strategy"
    assert metadata["config"] == {
        "csv_path": str(csv_path),
        "output_dir": str(output_dir),
        "initial_cash": 123456,
        "rebalance_interval": 4,
        "top_n": 2,
        "target_exposure": 0.6,
        "fee_rate": 0.002,
        "slippage": 0.001,
        "use_risk_manager": False,
        "auto_run_dir": False,
        "benchmark_symbol": None,
    }
    assert set(metadata["output_paths"]) == {"nav", "trades", "positions", "signals", "report", "metadata"}
    assert metadata["output_paths"]["metadata"] == str(metadata_path)
    assert metadata["actual_output_dir"] == str(output_dir)
    assert set(
        [
            "total_return",
            "annual_return",
            "max_drawdown",
            "annual_volatility",
            "sharpe_ratio",
            "calmar_ratio",
            "rebalance_win_rate",
        ]
    ).issubset(metadata["summary"])
    assert_no_nan_or_infinity(metadata)


def test_demo_pipeline_with_benchmark_writes_benchmark_outputs(tmp_path):
    csv_path = tmp_path / "prices.csv"
    output_dir = tmp_path / "benchmark_outputs"
    make_demo_csv(csv_path)

    result = run_etf_rotation_demo(csv_path, output_dir=output_dir, benchmark_symbol="ETF_A")

    assert Path(result["output_paths"]["benchmark_nav"]).exists()
    assert Path(result["output_paths"]["strategy_vs_benchmark"]).exists()
    assert not result["benchmark_nav"].empty
    assert not result["strategy_vs_benchmark"].empty
    assert "benchmark_total_return" in result["summary"]
    assert "benchmark_max_drawdown" in result["summary"]
    assert "excess_total_return" in result["summary"]

    with Path(result["output_paths"]["metadata"]).open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    assert metadata["config"]["benchmark_symbol"] == "ETF_A"
    assert "benchmark_nav" in metadata["output_paths"]
    assert "strategy_vs_benchmark" in metadata["output_paths"]


def test_demo_pipeline_runs_without_risk_manager(tmp_path):
    csv_path = tmp_path / "prices.csv"
    output_dir = tmp_path / "demo_outputs_no_risk"
    make_demo_csv(csv_path)

    result = run_etf_rotation_demo(csv_path, output_dir=output_dir, use_risk_manager=False)

    assert isinstance(result, dict)
    assert not result["nav"].empty
    assert "risk_mode" in result["nav"].columns
    assert "drawdown" in result["nav"].columns
    assert result["nav"]["risk_mode"].isna().all()
    assert Path(result["output_paths"]["report"]).exists()


def test_demo_pipeline_auto_run_dir_creates_timestamped_run_directory(tmp_path):
    csv_path = tmp_path / "prices.csv"
    output_dir = tmp_path / "auto_outputs"
    make_demo_csv(csv_path)

    result = run_etf_rotation_demo(csv_path, output_dir=output_dir, auto_run_dir=True)

    actual_output_dir = Path(result["actual_output_dir"])
    assert actual_output_dir.parent == output_dir / "runs"
    assert actual_output_dir.name[:15].count("_") == 1
    assert len(actual_output_dir.name[:15]) == 15
    assert Path(result["output_paths"]["metadata"]).parent == actual_output_dir

    with Path(result["output_paths"]["metadata"]).open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    assert metadata["config"]["output_dir"] == str(output_dir)
    assert metadata["config"]["auto_run_dir"] is True
    assert metadata["actual_output_dir"] == str(actual_output_dir)
    for path in metadata["output_paths"].values():
        if path.endswith("index.csv"):
            assert path == str(output_dir / "runs" / "index.csv")
        else:
            assert str(actual_output_dir) in path


def test_demo_pipeline_auto_run_dir_updates_run_index(tmp_path):
    csv_path = tmp_path / "prices.csv"
    output_dir = tmp_path / "indexed_outputs"
    make_demo_csv(csv_path)

    result = run_etf_rotation_demo(csv_path, output_dir=output_dir, auto_run_dir=True)
    run_index_path = Path(result["output_paths"]["run_index"])

    index = pd.read_csv(run_index_path)

    assert run_index_path == output_dir / "runs" / "index.csv"
    assert run_index_path.exists()
    assert Path(result["actual_output_dir"]).name in set(index["run_id"])
    row = index[index["actual_output_dir"] == result["actual_output_dir"]].iloc[0]
    assert row["metadata_path"] == result["output_paths"]["metadata"]


def assert_no_nan_or_infinity(value):
    if isinstance(value, dict):
        for item in value.values():
            assert_no_nan_or_infinity(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_nan_or_infinity(item)
    elif isinstance(value, float):
        assert not math.isnan(value)
        assert not math.isinf(value)
