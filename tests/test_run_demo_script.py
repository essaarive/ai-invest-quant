import os
import subprocess
import sys
from pathlib import Path

from ai_invest_quant.data.loader import load_csv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CSV = PROJECT_ROOT / "data" / "samples" / "sample_etf_prices.csv"
RUN_DEMO_SCRIPT = PROJECT_ROOT / "scripts" / "run_demo.py"


def test_sample_csv_exists_and_can_be_loaded():
    assert SAMPLE_CSV.exists()

    df = load_csv(SAMPLE_CSV)

    assert df["symbol"].nunique() >= 4
    assert df["date"].nunique() >= 130
    assert {"ETF_A", "ETF_B", "ETF_C", "ETF_D"}.issubset(set(df["symbol"]))


def test_run_demo_script_exists():
    assert RUN_DEMO_SCRIPT.exists()


def test_run_demo_script_can_run_with_custom_output_dir(tmp_path):
    output_dir = tmp_path / "demo_outputs"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")

    result = subprocess.run(
        [sys.executable, str(RUN_DEMO_SCRIPT), "--output-dir", str(output_dir)],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "Demo completed" in result.stdout
    assert "report.md" in result.stdout
    assert (output_dir / "report.md").exists()
    assert (output_dir / "nav.csv").exists()
    assert (output_dir / "trades.csv").exists()
    assert (output_dir / "positions.csv").exists()
    assert (output_dir / "signals.csv").exists()
    assert (output_dir / "report.md").stat().st_size > 0
    assert (output_dir / "nav.csv").stat().st_size > 0
    assert (output_dir / "positions.csv").stat().st_size > 0
    assert (output_dir / "signals.csv").stat().st_size > 0
