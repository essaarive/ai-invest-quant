"""Performance metrics for backtest outputs."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from ai_invest_quant.performance.utils import prepare_nav_dataframe

NAV_COLUMNS = ("date", "equity", "nav")
TRADES_COLUMNS = ("trade_date", "trade_amount")
SIGNALS_COLUMNS = ("execute_date",)


def calculate_total_return(nav_df: pd.DataFrame) -> float:
    """Calculate total return from the nav column."""
    nav = _prepare_nav(nav_df)
    return float(nav["nav"].iloc[-1] / nav["nav"].iloc[0] - 1)


def calculate_annual_return(nav_df: pd.DataFrame, trading_days_per_year: int = 252) -> float:
    """Calculate annualized return from the nav column."""
    nav = _prepare_nav(nav_df)
    trading_days = len(nav) - 1
    if trading_days <= 0:
        return 0.0

    return float(
        (nav["nav"].iloc[-1] / nav["nav"].iloc[0]) ** (trading_days_per_year / trading_days) - 1
    )


def calculate_max_drawdown(nav_df: pd.DataFrame) -> float:
    """Calculate maximum drawdown as a negative number."""
    nav = _prepare_nav(nav_df)
    running_max = nav["nav"].cummax()
    drawdown = nav["nav"] / running_max - 1
    return float(drawdown.min())


def calculate_annual_volatility(nav_df: pd.DataFrame, trading_days_per_year: int = 252) -> float:
    """Calculate annualized volatility from daily nav returns."""
    nav = _prepare_nav(nav_df)
    daily_return = nav["nav"].pct_change().dropna()
    if daily_return.empty:
        return 0.0

    return float(daily_return.std(ddof=0) * math.sqrt(trading_days_per_year))


def calculate_sharpe_ratio(
    nav_df: pd.DataFrame,
    risk_free_rate: float = 0.0,
    trading_days_per_year: int = 252,
) -> float:
    """Calculate annualized Sharpe ratio using an annual risk-free rate."""
    nav = _prepare_nav(nav_df)
    daily_return = nav["nav"].pct_change().dropna()
    if daily_return.empty:
        return 0.0

    daily_rf = risk_free_rate / trading_days_per_year
    excess_return = daily_return - daily_rf
    std = excess_return.std(ddof=0)
    if std == 0 or np.isnan(std):
        return 0.0

    return float(excess_return.mean() / std * math.sqrt(trading_days_per_year))


def calculate_calmar_ratio(nav_df: pd.DataFrame, trading_days_per_year: int = 252) -> float:
    """Calculate Calmar ratio as annual return divided by absolute max drawdown."""
    max_drawdown = calculate_max_drawdown(nav_df)
    if max_drawdown == 0:
        return float("nan")

    annual_return = calculate_annual_return(nav_df, trading_days_per_year=trading_days_per_year)
    return float(annual_return / abs(max_drawdown))


def calculate_turnover(trades_df: pd.DataFrame | None, nav_df: pd.DataFrame) -> float:
    """Calculate total amount turnover as trade amount over average equity."""
    nav = _prepare_nav(nav_df)
    if trades_df is None or trades_df.empty:
        return 0.0

    missing = [column for column in TRADES_COLUMNS if column not in trades_df.columns]
    if missing:
        raise ValueError(f"Missing required trades columns: {', '.join(missing)}")

    trade_amount = pd.to_numeric(trades_df["trade_amount"], errors="raise")
    average_equity = nav["equity"].mean()
    if average_equity <= 0:
        raise ValueError("average equity must be > 0")

    return float(trade_amount.sum() / average_equity)


def calculate_rebalance_win_rate(nav_df: pd.DataFrame, signals_df: pd.DataFrame) -> float:
    """Calculate the win rate across completed rebalance periods."""
    nav = _prepare_nav(nav_df)
    if signals_df is None or signals_df.empty:
        return float("nan")

    missing = [column for column in SIGNALS_COLUMNS if column not in signals_df.columns]
    if missing:
        raise ValueError(f"Missing required signals columns: {', '.join(missing)}")

    signals = signals_df.copy()
    signals["execute_date"] = pd.to_datetime(signals["execute_date"], errors="raise")
    execute_dates = signals["execute_date"].drop_duplicates().sort_values().tolist()
    if len(execute_dates) < 2:
        return float("nan")

    nav_by_date = nav.set_index("date")["nav"]
    nav_dates = pd.Index(nav["date"])
    wins = 0
    periods = 0

    for index, execute_date in enumerate(execute_dates[:-1]):
        next_execute_date = execute_dates[index + 1]
        if execute_date not in nav_by_date.index:
            continue

        period_end_candidates = nav_dates[nav_dates < next_execute_date]
        period_end_candidates = period_end_candidates[period_end_candidates >= execute_date]
        if period_end_candidates.empty:
            continue

        period_end = period_end_candidates[-1]
        if period_end == execute_date:
            continue

        period_return = nav_by_date.loc[period_end] / nav_by_date.loc[execute_date] - 1
        periods += 1
        if period_return > 0:
            wins += 1

    if periods == 0:
        return float("nan")

    return float(wins / periods)


def calculate_performance_summary(
    nav_df: pd.DataFrame,
    trades_df: pd.DataFrame | None = None,
    signals_df: pd.DataFrame | None = None,
) -> dict[str, object]:
    """Calculate a compact performance summary dict."""
    nav = _prepare_nav(nav_df)
    return {
        "total_return": calculate_total_return(nav),
        "annual_return": calculate_annual_return(nav),
        "max_drawdown": calculate_max_drawdown(nav),
        "annual_volatility": calculate_annual_volatility(nav),
        "sharpe_ratio": calculate_sharpe_ratio(nav),
        "calmar_ratio": calculate_calmar_ratio(nav),
        "total_turnover_by_amount": calculate_turnover(trades_df, nav),
        "rebalance_win_rate": (
            calculate_rebalance_win_rate(nav, signals_df)
            if signals_df is not None
            else float("nan")
        ),
        "start_date": nav["date"].iloc[0],
        "end_date": nav["date"].iloc[-1],
        "trading_days": len(nav) - 1,
    }


def _prepare_nav(nav_df: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in NAV_COLUMNS if column not in nav_df.columns]
    if missing:
        raise ValueError(f"Missing required nav columns: {', '.join(missing)}")

    if nav_df.empty:
        raise ValueError("nav_df cannot be empty")

    nav_values = pd.to_numeric(nav_df["nav"], errors="raise")
    if nav_values.iloc[0] <= 0:
        raise ValueError("initial nav must be > 0")
    if (nav_values <= 0).any():
        raise ValueError("nav values must be > 0")

    return prepare_nav_dataframe(nav_df)
