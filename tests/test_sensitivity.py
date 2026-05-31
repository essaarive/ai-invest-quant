from pathlib import Path

import pandas as pd

from ai_invest_quant.pipeline.sensitivity import run_parameter_sensitivity
from tests.test_pipeline_demo import make_demo_csv


def test_run_parameter_sensitivity_generates_summary_and_runs(tmp_path):
    csv_path = tmp_path / "prices.csv"
    output_dir = tmp_path / "sensitivity"
    make_demo_csv(csv_path)

    result = run_parameter_sensitivity(
        csv_path=csv_path,
        output_dir=output_dir,
        top_n_values=[1, 2],
        target_exposure_values=[0.5],
        rebalance_interval_values=[5],
    )

    summary = result["summary"]
    assert len(summary) == 2
    assert Path(result["summary_path"]).exists()
    assert (output_dir / "sensitivity_summary.csv").exists()
    assert {"top_n", "target_exposure", "rebalance_interval"}.issubset(summary.columns)
    assert {"total_return", "max_drawdown", "sharpe_ratio"}.issubset(summary.columns)
    assert summary["actual_output_dir"].notna().all()
    for actual_output_dir in summary["actual_output_dir"]:
        assert Path(actual_output_dir).parent == output_dir / "runs"
        assert Path(actual_output_dir).exists()


def test_run_parameter_sensitivity_includes_benchmark_and_oos_metrics(tmp_path):
    csv_path = tmp_path / "prices.csv"
    output_dir = tmp_path / "sensitivity"
    make_demo_csv(csv_path)

    result = run_parameter_sensitivity(
        csv_path=csv_path,
        output_dir=output_dir,
        top_n_values=[1],
        target_exposure_values=[0.5],
        rebalance_interval_values=[5],
        benchmark_symbol="ETF_A",
        out_of_sample_ratio=0.3,
    )

    summary = result["summary"]
    row = summary.iloc[0]
    assert "benchmark_total_return" in summary.columns
    assert "benchmark_max_drawdown" in summary.columns
    assert "excess_total_return" in summary.columns
    assert "in_sample_total_return" in summary.columns
    assert "out_of_sample_total_return" in summary.columns
    assert "out_of_sample_max_drawdown" in summary.columns
    assert "out_of_sample_sharpe_ratio" in summary.columns
    assert pd.notna(row["benchmark_total_return"])
    assert pd.notna(row["out_of_sample_total_return"])
