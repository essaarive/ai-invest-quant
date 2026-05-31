import math

import pandas as pd

from ai_invest_quant.report.markdown_report import (
    format_date,
    format_number,
    format_percentage,
    generate_markdown_report,
)


def make_summary() -> dict:
    return {
        "total_return": 0.1234,
        "annual_return": 0.2345,
        "max_drawdown": -0.1111,
        "annual_volatility": 0.0987,
        "sharpe_ratio": 1.23456,
        "calmar_ratio": math.nan,
        "total_turnover_by_amount": 0.4567,
        "rebalance_win_rate": 0.5,
        "start_date": pd.Timestamp("2024-01-01"),
        "end_date": pd.Timestamp("2024-01-10"),
        "trading_days": 9,
    }


def test_generate_markdown_report_returns_string_and_contains_title():
    report = generate_markdown_report(make_summary())

    assert isinstance(report, str)
    assert "# ETF Rotation Backtest Report" in report


def test_report_contains_core_performance_fields_and_percentage_format():
    report = generate_markdown_report(make_summary())

    assert "Total Return" in report
    assert "Annual Return" in report
    assert "Max Drawdown" in report
    assert "Annual Volatility" in report
    assert "Sharpe Ratio" in report
    assert "Calmar Ratio" in report
    assert "Total Turnover by Amount" in report
    assert "Rebalance Win Rate" in report
    assert "12.34%" in report


def test_report_contains_benchmark_section_when_enabled():
    summary = make_summary() | {
        "benchmark_total_return": 0.1,
        "benchmark_max_drawdown": -0.05,
        "excess_total_return": 0.0234,
    }

    report = generate_markdown_report(summary, benchmark_symbol="ETF_A")

    assert "## Benchmark" in report
    assert "Benchmark Symbol: ETF_A" in report
    assert "Benchmark Total Return: 10.00%" in report
    assert "Benchmark Max Drawdown: -5.00%" in report
    assert "Excess Total Return: 2.34%" in report


def test_report_contains_out_of_sample_section_when_enabled():
    summary = make_summary() | {
        "split_date": pd.Timestamp("2024-01-08"),
        "in_sample_total_return": 0.12,
        "in_sample_max_drawdown": -0.03,
        "in_sample_sharpe_ratio": 1.1,
        "out_of_sample_total_return": 0.04,
        "out_of_sample_max_drawdown": -0.02,
        "out_of_sample_sharpe_ratio": 0.8,
    }

    report = generate_markdown_report(summary)

    assert "## Out-of-Sample Evaluation" in report
    assert "Split Date: 2024-01-08" in report
    assert "In-Sample Total Return: 12.00%" in report
    assert "Out-of-Sample Total Return: 4.00%" in report


def test_format_helpers_handle_nan_none_numbers_and_dates():
    assert format_percentage(math.nan) == "N/A"
    assert format_number(None) == "N/A"
    assert format_number(1.234567) == "1.2346"
    assert format_date(pd.Timestamp("2024-01-02")) == "2024-01-02"


def test_output_path_writes_file(tmp_path):
    path = tmp_path / "report.md"

    report = generate_markdown_report(make_summary(), output_path=path)

    assert path.read_text(encoding="utf-8") == report


def test_nav_with_risk_mode_shows_latest_mode():
    nav = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=3),
            "equity": [1000, 990, 980],
            "nav": [1.0, 0.99, 0.98],
            "risk_mode": ["normal", "defensive", "defensive"],
            "drawdown": [0.0, -0.01, -0.02],
        }
    )

    report = generate_markdown_report(make_summary(), nav_df=nav)

    assert "Latest Risk Mode: defensive" in report
    assert "Latest Drawdown: -2.00%" in report
    assert "Defensive Days: 2" in report


def test_nav_without_risk_mode_says_risk_manager_not_enabled():
    nav = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=2),
            "equity": [1000, 1010],
            "nav": [1.0, 1.01],
        }
    )

    report = generate_markdown_report(make_summary(), nav_df=nav)

    assert "Risk Manager not enabled" in report


def test_empty_positions_trades_and_signals_show_empty_messages():
    report = generate_markdown_report(
        make_summary(),
        positions_df=pd.DataFrame(),
        trades_df=pd.DataFrame(),
        signals_df=pd.DataFrame(),
    )

    assert "No current positions" in report
    assert "No trades" in report
    assert "No signals" in report


def test_report_contains_fixed_risk_disclaimer():
    report = generate_markdown_report(make_summary())

    assert "This report is generated from historical backtest data." in report
    assert "Backtest performance does not guarantee future results." in report
    assert "Transaction costs and slippage assumptions may differ from live trading." in report
    assert "This system does not provide financial advice." in report
    assert "No real orders are placed by this report." in report


def test_recent_trades_shows_at_most_ten_rows():
    trades = pd.DataFrame(
        {
            "trade_date": pd.date_range("2024-01-01", periods=12),
            "symbol": [f"ETF{index:02d}" for index in range(12)],
            "side": ["buy"] * 12,
            "quantity": [1.0] * 12,
            "price": [100.0] * 12,
            "trade_amount": [100.0] * 12,
            "fee": [0.1] * 12,
        }
    )

    report = generate_markdown_report(make_summary(), trades_df=trades)

    assert "ETF00" not in report
    assert "ETF01" not in report
    assert "ETF02" in report
    assert "ETF11" in report


def test_latest_positions_shows_at_most_ten_rows_sorted_by_weight():
    positions = pd.DataFrame(
        {
            "date": [pd.Timestamp("2024-01-10")] * 12,
            "symbol": [f"ETF{index:02d}" for index in range(12)],
            "quantity": [1.0] * 12,
            "close": [100.0] * 12,
            "market_value": [100.0] * 12,
            "weight": [index / 100 for index in range(12)],
        }
    )

    report = generate_markdown_report(make_summary(), positions_df=positions)

    assert "ETF00" not in report
    assert "ETF01" not in report
    assert "ETF02" in report
    assert "ETF11" in report


def test_recent_signals_shows_at_most_ten_rows():
    signals = pd.DataFrame(
        {
            "signal_date": pd.date_range("2024-01-01", periods=12),
            "execute_date": pd.date_range("2024-01-02", periods=12),
            "symbol": [f"ETF{index:02d}" for index in range(12)],
            "target_weight": [0.1] * 12,
        }
    )

    report = generate_markdown_report(make_summary(), signals_df=signals)

    assert "ETF00" not in report
    assert "ETF01" not in report
    assert "ETF02" in report
    assert "ETF11" in report
