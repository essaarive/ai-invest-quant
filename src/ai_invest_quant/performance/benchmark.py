"""Benchmark NAV helpers for local historical backtests."""

from __future__ import annotations

import pandas as pd


def build_benchmark_nav(price_df: pd.DataFrame, benchmark_symbol: str, initial_nav: float = 1.0) -> pd.DataFrame:
    """Build normalized benchmark NAV from one symbol's close prices."""
    required_columns = {"date", "symbol", "close"}
    missing = required_columns - set(price_df.columns)
    if missing:
        raise ValueError(f"price_df missing required columns: {', '.join(sorted(missing))}")
    if not isinstance(benchmark_symbol, str) or not benchmark_symbol.strip():
        raise ValueError("benchmark_symbol must be a non-empty string")
    if initial_nav <= 0:
        raise ValueError("initial_nav must be > 0")

    benchmark = price_df[price_df["symbol"] == benchmark_symbol].copy()
    if benchmark.empty:
        raise ValueError(f"benchmark_symbol not found: {benchmark_symbol}")

    benchmark["date"] = pd.to_datetime(benchmark["date"], errors="raise")
    benchmark["close"] = pd.to_numeric(benchmark["close"], errors="raise")
    if benchmark["close"].isna().any() or (benchmark["close"] <= 0).any():
        raise ValueError("Benchmark close must be numeric and > 0")

    benchmark = benchmark.sort_values("date").reset_index(drop=True)
    first_close = benchmark["close"].iloc[0]
    return pd.DataFrame(
        {
            "date": benchmark["date"],
            "benchmark_symbol": benchmark_symbol,
            "benchmark_nav": benchmark["close"] / first_close * initial_nav,
        }
    )


def calculate_benchmark_summary(benchmark_nav_df: pd.DataFrame) -> dict[str, float]:
    """Calculate lightweight benchmark summary metrics."""
    if "benchmark_nav" not in benchmark_nav_df.columns:
        raise ValueError("benchmark_nav_df must contain benchmark_nav")
    benchmark_nav = pd.to_numeric(benchmark_nav_df["benchmark_nav"], errors="raise")
    if benchmark_nav.empty or benchmark_nav.iloc[0] <= 0:
        raise ValueError("benchmark_nav must start with a value > 0")

    running_max = benchmark_nav.cummax()
    drawdown = benchmark_nav / running_max - 1
    return {
        "benchmark_total_return": benchmark_nav.iloc[-1] / benchmark_nav.iloc[0] - 1,
        "benchmark_max_drawdown": drawdown.min(),
    }


def merge_strategy_benchmark_nav(nav_df: pd.DataFrame, benchmark_nav_df: pd.DataFrame) -> pd.DataFrame:
    """Merge strategy NAV and benchmark NAV by date for charting."""
    if "date" not in nav_df.columns or "equity" not in nav_df.columns:
        raise ValueError("nav_df must contain date and equity")
    if "date" not in benchmark_nav_df.columns or "benchmark_nav" not in benchmark_nav_df.columns:
        raise ValueError("benchmark_nav_df must contain date and benchmark_nav")

    strategy = nav_df[["date", "equity"]].copy()
    strategy["date"] = pd.to_datetime(strategy["date"], errors="raise")
    strategy["equity"] = pd.to_numeric(strategy["equity"], errors="raise")
    if strategy.empty or strategy["equity"].iloc[0] <= 0:
        raise ValueError("strategy equity must start with a value > 0")
    strategy["strategy_nav"] = strategy["equity"] / strategy["equity"].iloc[0]

    benchmark = benchmark_nav_df[["date", "benchmark_nav"]].copy()
    benchmark["date"] = pd.to_datetime(benchmark["date"], errors="raise")
    benchmark["benchmark_nav"] = pd.to_numeric(benchmark["benchmark_nav"], errors="raise")

    merged = strategy[["date", "strategy_nav"]].merge(benchmark, on="date", how="inner")
    return merged.sort_values("date").reset_index(drop=True)
