import pandas as pd
import pytest

from ai_invest_quant.performance.benchmark import (
    build_benchmark_nav,
    calculate_benchmark_summary,
    merge_strategy_benchmark_nav,
)


def price_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-01", "2024-01-03", "2024-01-01"],
            "symbol": ["ETF_A", "ETF_A", "ETF_A", "ETF_B"],
            "close": [110.0, 100.0, 105.0, 200.0],
        }
    )


def test_build_benchmark_nav_generates_normalized_nav():
    benchmark = build_benchmark_nav(price_df(), "ETF_A")

    assert list(benchmark.columns) == ["date", "benchmark_symbol", "benchmark_nav"]
    assert benchmark["benchmark_symbol"].unique().tolist() == ["ETF_A"]
    assert benchmark["benchmark_nav"].iloc[0] == 1.0
    assert benchmark["benchmark_nav"].iloc[-1] == 1.05


def test_build_benchmark_nav_missing_symbol_raises_error():
    with pytest.raises(ValueError, match="benchmark_symbol not found"):
        build_benchmark_nav(price_df(), "MISSING")


def test_build_benchmark_nav_rejects_non_positive_close():
    prices = price_df()
    prices.loc[0, "close"] = 0

    with pytest.raises(ValueError, match="close.*> 0"):
        build_benchmark_nav(prices, "ETF_A")


def test_calculate_benchmark_summary_returns_core_metrics():
    benchmark = pd.DataFrame({"benchmark_nav": [1.0, 1.1, 1.05]})

    summary = calculate_benchmark_summary(benchmark)

    assert summary["benchmark_total_return"] == pytest.approx(0.05)
    assert summary["benchmark_max_drawdown"] == pytest.approx(1.05 / 1.1 - 1)


def test_merge_strategy_benchmark_nav_outputs_strategy_and_benchmark_nav():
    nav = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "equity": [1000.0, 1020.0, 1010.0],
        }
    )
    benchmark = build_benchmark_nav(price_df(), "ETF_A")

    merged = merge_strategy_benchmark_nav(nav, benchmark)

    assert list(merged.columns) == ["date", "strategy_nav", "benchmark_nav"]
    assert merged["strategy_nav"].iloc[0] == 1.0
    assert merged["benchmark_nav"].iloc[0] == 1.0
