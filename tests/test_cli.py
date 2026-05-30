import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CSV = PROJECT_ROOT / "data" / "samples" / "sample_etf_prices.csv"


def run_cli(args, tmp_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "ai_invest_quant.cli", *args],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
    )


def assert_demo_outputs_exist(output_dir: Path) -> None:
    assert (output_dir / "nav.csv").exists()
    assert (output_dir / "trades.csv").exists()
    assert (output_dir / "positions.csv").exists()
    assert (output_dir / "signals.csv").exists()
    assert (output_dir / "report.md").exists()


def test_cli_help_runs(tmp_path):
    result = run_cli(["--help"], tmp_path)

    assert result.returncode == 0
    assert "run-demo" in result.stdout


def test_run_demo_help_runs(tmp_path):
    result = run_cli(["run-demo", "--help"], tmp_path)

    assert result.returncode == 0
    assert "--csv-path" in result.stdout


def test_default_run_demo_succeeds(tmp_path):
    result = run_cli(["run-demo"], tmp_path)

    assert result.returncode == 0
    assert "Demo completed" in result.stdout
    assert_demo_outputs_exist(tmp_path / "outputs" / "demo")


def test_custom_output_dir_succeeds(tmp_path):
    output_dir = tmp_path / "custom_demo"

    result = run_cli(["run-demo", "--output-dir", str(output_dir)], tmp_path)

    assert result.returncode == 0
    assert_demo_outputs_exist(output_dir)


def test_no_risk_manager_succeeds(tmp_path):
    output_dir = tmp_path / "no_risk_demo"

    result = run_cli(["run-demo", "--output-dir", str(output_dir), "--no-risk-manager"], tmp_path)

    assert result.returncode == 0
    assert "Demo completed" in result.stdout
    assert_demo_outputs_exist(output_dir)


def test_success_output_contains_key_lines(tmp_path):
    output_dir = tmp_path / "printed_demo"

    result = run_cli(["run-demo", "--output-dir", str(output_dir)], tmp_path)

    assert result.returncode == 0
    assert "Demo completed" in result.stdout
    assert "report.md" in result.stdout
    assert "Total Return" in result.stdout
    assert "Max Drawdown" in result.stdout
    assert "Sharpe Ratio" in result.stdout


def test_missing_csv_path_returns_non_zero(tmp_path):
    result = run_cli(["run-demo", "--csv-path", str(tmp_path / "missing.csv")], tmp_path)

    assert result.returncode != 0
    assert "csv_path does not exist" in result.stderr


def test_invalid_initial_cash_returns_non_zero(tmp_path):
    result = run_cli(["run-demo", "--initial-cash", "0"], tmp_path)

    assert result.returncode != 0
    assert "initial_cash must be > 0" in result.stderr


def test_invalid_target_exposure_returns_non_zero(tmp_path):
    result = run_cli(["run-demo", "--target-exposure", "1.1"], tmp_path)

    assert result.returncode != 0
    assert "target_exposure must be >= 0 and <= 1" in result.stderr


def test_custom_parameters_succeed(tmp_path):
    output_dir = tmp_path / "params_demo"

    result = run_cli(
        [
            "run-demo",
            "--csv-path",
            str(SAMPLE_CSV),
            "--output-dir",
            str(output_dir),
            "--initial-cash",
            "1000000",
            "--rebalance-interval",
            "5",
            "--top-n",
            "3",
            "--target-exposure",
            "0.8",
            "--fee-rate",
            "0.001",
            "--slippage",
            "0.0005",
            "--no-risk-manager",
        ],
        tmp_path,
    )

    assert result.returncode == 0
    assert_demo_outputs_exist(output_dir)
