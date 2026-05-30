import os
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CSV = PROJECT_ROOT / "data" / "samples" / "sample_etf_prices.csv"
DEMO_CONFIG = PROJECT_ROOT / "configs" / "demo_config.json"


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
    assert "--config" in result.stdout
    assert "--csv-path" in result.stdout


def test_default_run_demo_succeeds(tmp_path):
    result = run_cli(["run-demo"], tmp_path)

    assert result.returncode == 0
    assert "Demo completed" in result.stdout
    assert_demo_outputs_exist(tmp_path / "outputs" / "demo")


def test_run_demo_with_config_succeeds(tmp_path):
    result = run_cli(["run-demo", "--config", str(DEMO_CONFIG)], tmp_path)

    assert result.returncode == 0
    assert "Demo completed" in result.stdout
    assert_demo_outputs_exist(tmp_path / "outputs" / "dashboard_demo")


def test_config_output_dir_can_be_overridden(tmp_path):
    output_dir = tmp_path / "config_override_output"

    result = run_cli(
        ["run-demo", "--config", str(DEMO_CONFIG), "--output-dir", str(output_dir)],
        tmp_path,
    )

    assert result.returncode == 0
    assert_demo_outputs_exist(output_dir)


def test_config_top_n_can_be_overridden(tmp_path):
    output_dir = tmp_path / "top_n_override"

    result = run_cli(
        ["run-demo", "--config", str(DEMO_CONFIG), "--output-dir", str(output_dir), "--top-n", "2"],
        tmp_path,
    )

    assert result.returncode == 0
    signals = pd.read_csv(output_dir / "signals.csv")
    etf_signals = signals[signals["symbol"] != "CASH"]
    max_symbols_per_execute_date = etf_signals.groupby("execute_date")["symbol"].nunique().max()
    assert max_symbols_per_execute_date <= 2


def test_no_risk_manager_overrides_config_true(tmp_path):
    output_dir = tmp_path / "no_risk_override"

    result = run_cli(
        ["run-demo", "--config", str(DEMO_CONFIG), "--output-dir", str(output_dir), "--no-risk-manager"],
        tmp_path,
    )

    assert result.returncode == 0
    nav = pd.read_csv(output_dir / "nav.csv")
    assert nav["risk_mode"].isna().all()


def test_use_risk_manager_overrides_config_false(tmp_path):
    output_dir = tmp_path / "use_risk_override"
    config_path = tmp_path / "config_no_risk.json"
    config = json.loads(DEMO_CONFIG.read_text(encoding="utf-8"))
    config["use_risk_manager"] = False
    config_path.write_text(json.dumps(config), encoding="utf-8")

    result = run_cli(
        ["run-demo", "--config", str(config_path), "--output-dir", str(output_dir), "--use-risk-manager"],
        tmp_path,
    )

    assert result.returncode == 0
    nav = pd.read_csv(output_dir / "nav.csv")
    assert nav["risk_mode"].notna().any()


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


def test_missing_config_path_returns_non_zero(tmp_path):
    result = run_cli(["run-demo", "--config", str(tmp_path / "missing_config.json")], tmp_path)

    assert result.returncode != 0
    assert "Experiment config not found" in result.stderr


def test_invalid_config_returns_non_zero(tmp_path):
    config_path = tmp_path / "invalid_config.json"
    config = json.loads(DEMO_CONFIG.read_text(encoding="utf-8"))
    config["target_exposure"] = 1.5
    config_path.write_text(json.dumps(config), encoding="utf-8")

    result = run_cli(["run-demo", "--config", str(config_path)], tmp_path)

    assert result.returncode != 0
    assert "target_exposure must be >= 0 and <= 1" in result.stderr


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
