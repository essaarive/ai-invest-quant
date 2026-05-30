from pathlib import Path

import pandas as pd

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
    assert set(result) == {"nav", "trades", "positions", "signals", "summary", "report", "output_paths"}
    assert output_dir.exists()
    assert "# ETF Rotation Backtest Report" in result["report"]
    assert "risk_mode" in result["nav"].columns
    assert "drawdown" in result["nav"].columns

    for key in ["nav", "trades", "positions", "signals", "report"]:
        path = Path(result["output_paths"][key])
        assert path.exists()
        if key != "trades" or not result["trades"].empty:
            assert path.stat().st_size > 0

    assert not result["nav"].empty
    assert not result["signals"].empty
    assert not result["positions"].empty


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
