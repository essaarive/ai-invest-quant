import json
import math

from ai_invest_quant import __version__
from ai_invest_quant.report.metadata import build_metadata, write_metadata


def test_build_metadata_contains_required_fields_and_sanitizes_nan_inf():
    metadata = build_metadata(
        config={"csv_path": "prices.csv"},
        summary={
            "total_return": 0.1,
            "annual_return": math.nan,
            "max_drawdown": -0.2,
            "annual_volatility": math.inf,
            "sharpe_ratio": 1.2,
            "calmar_ratio": -math.inf,
            "rebalance_win_rate": 0.5,
            "benchmark_total_return": 0.08,
            "benchmark_max_drawdown": -0.1,
            "excess_total_return": 0.02,
            "in_sample_total_return": 0.12,
            "in_sample_max_drawdown": -0.03,
            "in_sample_sharpe_ratio": 1.1,
            "out_of_sample_total_return": 0.04,
            "out_of_sample_max_drawdown": -0.02,
            "out_of_sample_sharpe_ratio": 0.8,
            "split_date": "2024-04-01",
        },
        output_paths={"nav": "nav.csv"},
        run_time="2026-01-01T00:00:00",
    )

    assert metadata["project"] == "ai-invest-quant"
    assert metadata["version"] == __version__
    assert metadata["strategy_name"] == "ETF Rotation Strategy"
    assert metadata["run_time"] == "2026-01-01T00:00:00"
    assert metadata["summary"]["annual_return"] is None
    assert metadata["summary"]["annual_volatility"] is None
    assert metadata["summary"]["calmar_ratio"] is None
    assert metadata["summary"]["benchmark_total_return"] == 0.08
    assert metadata["summary"]["benchmark_max_drawdown"] == -0.1
    assert metadata["summary"]["excess_total_return"] == 0.02
    assert metadata["summary"]["out_of_sample_total_return"] == 0.04
    assert metadata["summary"]["split_date"] == "2024-04-01"


def test_write_metadata_outputs_valid_json(tmp_path):
    path = tmp_path / "metadata.json"

    write_metadata(
        path=path,
        config={"csv_path": "prices.csv"},
        summary={"total_return": math.nan},
        output_paths={"metadata": str(path)},
    )

    with path.open("r", encoding="utf-8") as file:
        loaded = json.load(file)

    assert loaded["summary"]["total_return"] is None
