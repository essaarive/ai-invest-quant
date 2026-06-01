from pathlib import Path

import pandas as pd
import pytest

from ai_invest_quant.pipeline.walk_forward import run_walk_forward_test
from tests.test_pipeline_demo import make_demo_csv


def test_run_walk_forward_test_generates_summary_and_runs(tmp_path):
    csv_path = tmp_path / "prices.csv"
    output_dir = tmp_path / "walk_forward"
    make_demo_csv(csv_path)

    result = run_walk_forward_test(
        csv_path=csv_path,
        output_dir=output_dir,
        train_window_days=30,
        test_window_days=70,
        step_days=70,
    )

    summary = result["summary"]
    assert len(summary) == 1
    assert Path(result["summary_path"]).exists()
    assert (output_dir / "walk_forward_summary.csv").exists()
    assert {"window_id", "train_start", "train_end", "test_start", "test_end"}.issubset(
        summary.columns
    )
    assert {"total_return", "max_drawdown", "sharpe_ratio"}.issubset(summary.columns)
    assert summary["actual_output_dir"].notna().all()
    assert Path(summary.loc[0, "actual_output_dir"]).parent == output_dir / "runs"


def test_run_walk_forward_test_includes_benchmark_metrics(tmp_path):
    csv_path = tmp_path / "prices.csv"
    output_dir = tmp_path / "walk_forward"
    make_demo_csv(csv_path)

    result = run_walk_forward_test(
        csv_path=csv_path,
        output_dir=output_dir,
        train_window_days=30,
        test_window_days=70,
        step_days=70,
        benchmark_symbol="ETF_A",
    )

    summary = result["summary"]
    assert "benchmark_total_return" in summary.columns
    assert "benchmark_max_drawdown" in summary.columns
    assert "excess_total_return" in summary.columns
    assert pd.notna(summary.loc[0, "benchmark_total_return"])


def test_run_walk_forward_test_rejects_too_little_data(tmp_path):
    csv_path = tmp_path / "prices.csv"
    output_dir = tmp_path / "walk_forward"
    make_demo_csv(csv_path)

    with pytest.raises(ValueError, match="Not enough data"):
        run_walk_forward_test(
            csv_path=csv_path,
            output_dir=output_dir,
            train_window_days=120,
            test_window_days=60,
            step_days=60,
        )


@pytest.mark.parametrize(
    ("field", "kwargs"),
    [
        ("train_window_days", {"train_window_days": 0}),
        ("test_window_days", {"test_window_days": 0}),
        ("step_days", {"step_days": 0}),
    ],
)
def test_run_walk_forward_test_rejects_non_positive_windows(tmp_path, field, kwargs):
    csv_path = tmp_path / "prices.csv"
    output_dir = tmp_path / "walk_forward"
    make_demo_csv(csv_path)

    with pytest.raises(ValueError, match=f"{field} must be a positive integer"):
        run_walk_forward_test(csv_path=csv_path, output_dir=output_dir, **kwargs)
