from pathlib import Path

from ai_invest_quant.report.run_index import append_run_index, load_run_index


def make_metadata(run_id: str, run_time: str, base_dir: Path) -> dict:
    actual_output_dir = base_dir / run_id
    return {
        "run_time": run_time,
        "actual_output_dir": str(actual_output_dir),
        "strategy_name": "ETF Rotation Strategy",
        "config": {
            "csv_path": "prices.csv",
            "initial_cash": 1_000_000,
            "rebalance_interval": 5,
            "top_n": 3,
            "target_exposure": 0.8,
            "fee_rate": 0.001,
            "slippage": 0.0005,
            "use_risk_manager": True,
        },
        "summary": {
            "total_return": 0.1,
            "annual_return": 0.2,
            "max_drawdown": -0.05,
            "annual_volatility": 0.12,
            "sharpe_ratio": 1.5,
            "calmar_ratio": 4.0,
            "rebalance_win_rate": 0.6,
        },
        "output_paths": {
            "metadata": str(actual_output_dir / "metadata.json"),
            "report": str(actual_output_dir / "report.md"),
        },
    }


def test_append_run_index_creates_index_csv(tmp_path):
    index_path = tmp_path / "runs" / "index.csv"

    append_run_index(index_path, make_metadata("20260531_031530", "2026-05-31T03:15:30", tmp_path))

    index = load_run_index(index_path)
    assert index_path.exists()
    assert len(index) == 1
    assert index.loc[0, "run_id"] == "20260531_031530"


def test_append_run_index_adds_new_run(tmp_path):
    index_path = tmp_path / "runs" / "index.csv"

    append_run_index(index_path, make_metadata("20260531_031530", "2026-05-31T03:15:30", tmp_path))
    append_run_index(index_path, make_metadata("20260531_031531", "2026-05-31T03:15:31", tmp_path))

    index = load_run_index(index_path)
    assert len(index) == 2


def test_append_run_index_does_not_duplicate_actual_output_dir(tmp_path):
    index_path = tmp_path / "runs" / "index.csv"
    metadata = make_metadata("20260531_031530", "2026-05-31T03:15:30", tmp_path)

    append_run_index(index_path, metadata)
    append_run_index(index_path, metadata)

    index = load_run_index(index_path)
    assert len(index) == 1


def test_load_run_index_missing_file_returns_empty_dataframe(tmp_path):
    index = load_run_index(tmp_path / "missing.csv")

    assert index.empty


def test_load_run_index_sorts_by_run_time_descending(tmp_path):
    index_path = tmp_path / "runs" / "index.csv"
    append_run_index(index_path, make_metadata("older", "2026-05-31T03:15:30", tmp_path))
    append_run_index(index_path, make_metadata("newer", "2026-05-31T03:15:31", tmp_path))

    index = load_run_index(index_path)

    assert index["run_id"].tolist() == ["newer", "older"]
