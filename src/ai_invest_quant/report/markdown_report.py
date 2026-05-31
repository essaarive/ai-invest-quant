"""Markdown backtest report generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

PERCENTAGE_FIELDS = {
    "total_return",
    "annual_return",
    "max_drawdown",
    "annual_volatility",
    "total_turnover_by_amount",
    "rebalance_win_rate",
    "benchmark_total_return",
    "benchmark_max_drawdown",
    "excess_total_return",
    "in_sample_total_return",
    "in_sample_max_drawdown",
    "out_of_sample_total_return",
    "out_of_sample_max_drawdown",
}


def generate_markdown_report(
    summary: dict,
    nav_df=None,
    trades_df=None,
    positions_df=None,
    signals_df=None,
    benchmark_symbol: str | None = None,
    strategy_name: str = "ETF Rotation Strategy",
    output_path=None,
) -> str:
    """Generate a Markdown backtest report and optionally write it to disk."""
    lines: list[str] = [
        "# ETF Rotation Backtest Report",
        "",
        "## Strategy Information",
        "",
        f"- Strategy Name: {strategy_name}",
        f"- Start Date: {format_date(summary.get('start_date'))}",
        f"- End Date: {format_date(summary.get('end_date'))}",
        f"- Trading Days: {format_number(summary.get('trading_days'))}",
        "",
        "## Core Performance Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]

    metrics = [
        ("Total Return", "total_return"),
        ("Annual Return", "annual_return"),
        ("Max Drawdown", "max_drawdown"),
        ("Annual Volatility", "annual_volatility"),
        ("Sharpe Ratio", "sharpe_ratio"),
        ("Calmar Ratio", "calmar_ratio"),
        ("Total Turnover by Amount", "total_turnover_by_amount"),
        ("Rebalance Win Rate", "rebalance_win_rate"),
    ]
    for label, key in metrics:
        formatter = format_percentage if key in PERCENTAGE_FIELDS else format_number
        lines.append(f"| {label} | {formatter(summary.get(key))} |")

    if benchmark_symbol is not None or _has_benchmark_summary(summary):
        lines.extend(["", "## Benchmark", ""])
        lines.extend(_format_benchmark_summary(summary, benchmark_symbol))

    if _has_oos_summary(summary):
        lines.extend(["", "## Out-of-Sample Evaluation", ""])
        lines.extend(_format_oos_summary(summary))

    lines.extend(["", "## Risk Status Summary", ""])
    lines.extend(_format_risk_summary(nav_df))

    lines.extend(["", "## Current Positions", ""])
    lines.extend(_format_current_positions(positions_df))

    lines.extend(["", "## Recent Trades", ""])
    lines.extend(_format_recent_trades(trades_df))

    lines.extend(["", "## Recent Signals", ""])
    lines.extend(_format_recent_signals(signals_df))

    lines.extend(
        [
            "",
            "## Risk Disclaimer",
            "",
            "- This report is generated from historical backtest data.",
            "- Backtest performance does not guarantee future results.",
            "- Transaction costs and slippage assumptions may differ from live trading.",
            "- This system does not provide financial advice.",
            "- No real orders are placed by this report.",
            "",
        ]
    )

    markdown = "\n".join(lines)
    if output_path is not None:
        Path(output_path).write_text(markdown, encoding="utf-8")

    return markdown


def format_percentage(value: Any) -> str:
    """Format a decimal number as a percentage with two decimals."""
    if _is_missing(value):
        return "N/A"
    return f"{float(value) * 100:.2f}%"


def format_number(value: Any) -> str:
    """Format a number with four decimals."""
    if _is_missing(value):
        return "N/A"
    return f"{float(value):.4f}"


def format_date(value: Any) -> str:
    """Format a date-like value as YYYY-MM-DD."""
    if _is_missing(value):
        return "N/A"
    return pd.to_datetime(value).strftime("%Y-%m-%d")


def _format_risk_summary(nav_df) -> list[str]:
    if nav_df is None or nav_df.empty or "risk_mode" not in nav_df.columns:
        return ["Risk Manager not enabled"]

    nav = nav_df.copy()
    latest = nav.iloc[-1]
    defensive_days = int((nav["risk_mode"] == "defensive").sum())
    drawdown = latest["drawdown"] if "drawdown" in nav.columns else None
    return [
        f"- Latest Risk Mode: {latest['risk_mode']}",
        f"- Latest Drawdown: {format_percentage(drawdown)}",
        f"- Defensive Days: {defensive_days}",
    ]


def _format_benchmark_summary(summary: dict, benchmark_symbol: str | None) -> list[str]:
    return [
        f"- Benchmark Symbol: {benchmark_symbol or 'N/A'}",
        f"- Benchmark Total Return: {format_percentage(summary.get('benchmark_total_return'))}",
        f"- Benchmark Max Drawdown: {format_percentage(summary.get('benchmark_max_drawdown'))}",
        f"- Excess Total Return: {format_percentage(summary.get('excess_total_return'))}",
    ]


def _has_benchmark_summary(summary: dict) -> bool:
    return any(
        key in summary
        for key in [
            "benchmark_total_return",
            "benchmark_max_drawdown",
            "excess_total_return",
        ]
    )


def _format_oos_summary(summary: dict) -> list[str]:
    out_sample_total_return = format_percentage(summary.get("out_of_sample_total_return"))
    out_sample_max_drawdown = format_percentage(summary.get("out_of_sample_max_drawdown"))
    return [
        f"- Split Date: {format_date(summary.get('split_date'))}",
        f"- In-Sample Total Return: {format_percentage(summary.get('in_sample_total_return'))}",
        f"- In-Sample Max Drawdown: {format_percentage(summary.get('in_sample_max_drawdown'))}",
        f"- In-Sample Sharpe Ratio: {format_number(summary.get('in_sample_sharpe_ratio'))}",
        f"- Out-of-Sample Total Return: {out_sample_total_return}",
        f"- Out-of-Sample Max Drawdown: {out_sample_max_drawdown}",
        f"- Out-of-Sample Sharpe Ratio: {format_number(summary.get('out_of_sample_sharpe_ratio'))}",
    ]


def _has_oos_summary(summary: dict) -> bool:
    return any(
        key in summary
        for key in [
            "in_sample_total_return",
            "out_of_sample_total_return",
            "split_date",
        ]
    )


def _format_current_positions(positions_df) -> list[str]:
    if positions_df is None or positions_df.empty:
        return ["No current positions"]

    positions = positions_df.copy()
    positions["date"] = pd.to_datetime(positions["date"], errors="raise")
    latest_date = positions["date"].max()
    latest_positions = positions[positions["date"] == latest_date]
    latest_positions = latest_positions.sort_values("weight", ascending=False).head(10)

    lines = [
        "| Symbol | Quantity | Close | Market Value | Weight |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in latest_positions.itertuples(index=False):
        lines.append(
            f"| {row.symbol} | {format_number(row.quantity)} | {format_number(row.close)} | "
            f"{format_number(row.market_value)} | {format_percentage(row.weight)} |"
        )
    return lines


def _format_recent_trades(trades_df) -> list[str]:
    if trades_df is None or trades_df.empty:
        return ["No trades"]

    trades = trades_df.copy()
    trades["trade_date"] = pd.to_datetime(trades["trade_date"], errors="raise")
    trades = trades.sort_values("trade_date", ascending=True).tail(10)

    lines = [
        "| Trade Date | Symbol | Side | Quantity | Price | Trade Amount | Fee |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in trades.itertuples(index=False):
        lines.append(
            f"| {format_date(row.trade_date)} | {row.symbol} | {row.side} | "
            f"{format_number(row.quantity)} | {format_number(row.price)} | "
            f"{format_number(row.trade_amount)} | {format_number(row.fee)} |"
        )
    return lines


def _format_recent_signals(signals_df) -> list[str]:
    if signals_df is None or signals_df.empty:
        return ["No signals"]

    signals = signals_df.copy()
    signals["execute_date"] = pd.to_datetime(signals["execute_date"], errors="raise")
    if "signal_date" in signals.columns:
        signals["signal_date"] = pd.to_datetime(signals["signal_date"], errors="raise")
    signals = signals.sort_values("execute_date", ascending=True).tail(10)

    lines = [
        "| Signal Date | Execute Date | Symbol | Target Weight |",
        "| --- | --- | --- | ---: |",
    ]
    for row in signals.itertuples(index=False):
        signal_date = getattr(row, "signal_date", None)
        lines.append(
            f"| {format_date(signal_date)} | {format_date(row.execute_date)} | {row.symbol} | "
            f"{format_percentage(row.target_weight)} |"
        )
    return lines


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except TypeError:
        return False
