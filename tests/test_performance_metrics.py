import math

import numpy as np
import pandas as pd
import pytest

from ai_invest_quant.performance.metrics import (
    calculate_annual_return,
    calculate_annual_volatility,
    calculate_calmar_ratio,
    calculate_max_drawdown,
    calculate_performance_summary,
    calculate_rebalance_win_rate,
    calculate_sharpe_ratio,
    calculate_total_return,
    calculate_turnover,
)


def make_nav(values: list[float]) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=len(values))
    return pd.DataFrame(
        {
            "date": dates,
            "cash": 0.0,
            "positions_value": np.array(values) * 1000,
            "equity": np.array(values) * 1000,
            "nav": values,
            "risk_mode": None,
            "drawdown": 0.0,
        }
    )


def test_missing_nav_column_raises_error():
    nav = make_nav([1.0, 1.1]).drop(columns=["nav"])

    with pytest.raises(ValueError, match="Missing required nav columns: nav"):
        calculate_total_return(nav)


def test_empty_nav_raises_error():
    nav = make_nav([1.0]).iloc[:0]

    with pytest.raises(ValueError, match="nav_df cannot be empty"):
        calculate_total_return(nav)


def test_initial_nav_must_be_positive():
    nav = make_nav([0.0, 1.0])

    with pytest.raises(ValueError, match="initial nav must be > 0"):
        calculate_total_return(nav)


@pytest.mark.parametrize("value", [0.0, -0.1])
def test_middle_nav_must_be_positive(value):
    nav = make_nav([1.0, value, 1.1])

    with pytest.raises(ValueError, match="nav values must be > 0"):
        calculate_total_return(nav)


@pytest.mark.parametrize("value", [0.0, -100.0])
def test_middle_equity_must_be_positive(value):
    nav = make_nav([1.0, 1.05, 1.1])
    nav.loc[1, "equity"] = value

    with pytest.raises(ValueError, match="equity values must be > 0"):
        calculate_total_return(nav)


def test_total_return_from_one_to_one_point_two_is_twenty_percent():
    nav = make_nav([1.0, 1.2])

    assert calculate_total_return(nav) == pytest.approx(0.2)


def test_annual_return_with_multiple_days():
    nav = make_nav([1.0, 1.1, 1.2])

    expected = (1.2 / 1.0) ** (252 / 2) - 1
    assert calculate_annual_return(nav) == pytest.approx(expected)


def test_annual_return_with_one_day_returns_zero():
    nav = make_nav([1.0])

    assert calculate_annual_return(nav) == 0.0


def test_max_drawdown_is_min_drawdown():
    nav = make_nav([1.0, 1.1, 1.05, 0.95, 1.0])

    assert calculate_max_drawdown(nav) == pytest.approx(0.95 / 1.1 - 1)


def test_annual_volatility_constant_nav_returns_zero():
    nav = make_nav([1.0, 1.0, 1.0])

    assert calculate_annual_volatility(nav) == 0.0


def test_sharpe_ratio_constant_nav_returns_zero():
    nav = make_nav([1.0, 1.0, 1.0])

    assert calculate_sharpe_ratio(nav) == 0.0


def test_sharpe_ratio_with_volatile_data_returns_number():
    nav = make_nav([1.0, 1.02, 0.99, 1.05])

    result = calculate_sharpe_ratio(nav)

    assert isinstance(result, float)
    assert not math.isnan(result)


def test_calmar_ratio_returns_nan_when_max_drawdown_is_zero():
    nav = make_nav([1.0, 1.1, 1.2])

    assert math.isnan(calculate_calmar_ratio(nav))


def test_turnover_empty_trades_returns_zero():
    nav = make_nav([1.0, 1.1])
    trades = pd.DataFrame(columns=["trade_date", "trade_amount"])

    assert calculate_turnover(trades, nav) == 0.0


def test_turnover_uses_sum_trade_amount_over_average_equity():
    nav = make_nav([1.0, 1.2])
    trades = pd.DataFrame(
        {
            "trade_date": [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-02")],
            "trade_amount": [100.0, 200.0],
        }
    )

    assert calculate_turnover(trades, nav) == pytest.approx(300 / 1100)


def test_rebalance_win_rate_counts_positive_and_negative_periods():
    nav = make_nav([1.0, 1.1, 1.2, 1.15, 1.1])
    signals = pd.DataFrame(
        {
            "execute_date": [
                pd.Timestamp("2024-01-01"),
                pd.Timestamp("2024-01-03"),
                pd.Timestamp("2024-01-05"),
            ]
        }
    )

    assert calculate_rebalance_win_rate(nav, signals) == pytest.approx(0.5)


def test_rebalance_win_rate_no_valid_period_returns_nan():
    nav = make_nav([1.0, 1.1])
    signals = pd.DataFrame({"execute_date": [pd.Timestamp("2024-01-01")]})

    assert math.isnan(calculate_rebalance_win_rate(nav, signals))


def test_performance_summary_contains_core_fields_and_dates():
    nav = make_nav([1.0, 1.1, 1.2])
    trades = pd.DataFrame({"trade_date": [pd.Timestamp("2024-01-02")], "trade_amount": [100.0]})
    signals = pd.DataFrame(
        {
            "execute_date": [
                pd.Timestamp("2024-01-01"),
                pd.Timestamp("2024-01-03"),
            ]
        }
    )

    summary = calculate_performance_summary(nav, trades_df=trades, signals_df=signals)

    assert isinstance(summary, dict)
    assert set(summary) == {
        "total_return",
        "annual_return",
        "max_drawdown",
        "annual_volatility",
        "sharpe_ratio",
        "calmar_ratio",
        "total_turnover_by_amount",
        "rebalance_win_rate",
        "start_date",
        "end_date",
        "trading_days",
    }
    assert summary["start_date"] == pd.Timestamp("2024-01-01")
    assert summary["end_date"] == pd.Timestamp("2024-01-03")
    assert summary["trading_days"] == 2
