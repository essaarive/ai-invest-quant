"""End-to-end ETF rotation demo runner."""

from __future__ import annotations

from pathlib import Path

from ai_invest_quant.backtest.engine import run_backtest
from ai_invest_quant.data.loader import load_csv
from ai_invest_quant.indicators.returns import add_daily_return, add_period_return
from ai_invest_quant.indicators.trend import add_moving_average
from ai_invest_quant.performance.benchmark import (
    build_benchmark_nav,
    calculate_benchmark_summary,
    merge_strategy_benchmark_nav,
)
from ai_invest_quant.performance.metrics import calculate_performance_summary
from ai_invest_quant.performance.oos import calculate_oos_summary
from ai_invest_quant.report.markdown_report import generate_markdown_report
from ai_invest_quant.report.metadata import write_metadata
from ai_invest_quant.report.run_index import append_run_index
from ai_invest_quant.risk.risk_manager import RiskManager
from ai_invest_quant.strategies.etf_rotation import generate_etf_rotation_signals
from ai_invest_quant.utils.run_id import create_run_directory


def run_etf_rotation_demo(
    csv_path,
    output_dir="outputs",
    initial_cash=1_000_000,
    rebalance_interval=5,
    top_n=3,
    target_exposure=0.8,
    fee_rate=0.001,
    slippage=0.0005,
    use_risk_manager=True,
    auto_run_dir=False,
    benchmark_symbol=None,
    out_of_sample_ratio=0.3,
) -> dict[str, object]:
    """Run the full ETF rotation demo pipeline from local CSV to report."""
    out_of_sample_ratio = float(out_of_sample_ratio)
    output_root = create_run_directory(output_dir) if auto_run_dir else Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    actual_output_dir = str(output_root)

    data = load_csv(csv_path)
    data = add_moving_average(data, windows=(20, 60, 120))
    data = add_daily_return(data)
    data = add_period_return(data, window=20)

    signals = generate_etf_rotation_signals(
        data,
        rebalance_interval=rebalance_interval,
        top_n=top_n,
        target_exposure=target_exposure,
    )

    risk_manager = RiskManager() if use_risk_manager else None
    nav, trades, positions = run_backtest(
        price_df=data,
        signals_df=signals,
        initial_cash=initial_cash,
        fee_rate=fee_rate,
        slippage=slippage,
        risk_manager=risk_manager,
    )

    summary = calculate_performance_summary(nav, trades_df=trades, signals_df=signals)
    if out_of_sample_ratio > 0:
        summary.update(calculate_oos_summary(nav, out_of_sample_ratio=out_of_sample_ratio))

    output_paths = {
        "nav": str(output_root / "nav.csv"),
        "trades": str(output_root / "trades.csv"),
        "positions": str(output_root / "positions.csv"),
        "signals": str(output_root / "signals.csv"),
        "report": str(output_root / "report.md"),
        "metadata": str(output_root / "metadata.json"),
    }
    benchmark_nav = None
    strategy_vs_benchmark = None
    if benchmark_symbol is not None:
        benchmark_nav = build_benchmark_nav(data, benchmark_symbol)
        benchmark_summary = calculate_benchmark_summary(benchmark_nav)
        summary.update(benchmark_summary)
        summary["excess_total_return"] = (
            summary["total_return"] - benchmark_summary["benchmark_total_return"]
        )
        strategy_vs_benchmark = merge_strategy_benchmark_nav(nav, benchmark_nav)
        output_paths["benchmark_nav"] = str(output_root / "benchmark_nav.csv")
        output_paths["strategy_vs_benchmark"] = str(output_root / "strategy_vs_benchmark.csv")

    if auto_run_dir:
        output_paths["run_index"] = str(Path(output_dir) / "runs" / "index.csv")

    nav.to_csv(output_paths["nav"], index=False)
    trades.to_csv(output_paths["trades"], index=False)
    positions.to_csv(output_paths["positions"], index=False)
    signals.to_csv(output_paths["signals"], index=False)
    if benchmark_nav is not None and strategy_vs_benchmark is not None:
        benchmark_nav.to_csv(output_paths["benchmark_nav"], index=False)
        strategy_vs_benchmark.to_csv(output_paths["strategy_vs_benchmark"], index=False)

    report = generate_markdown_report(
        summary=summary,
        nav_df=nav,
        trades_df=trades,
        positions_df=positions,
        signals_df=signals,
        benchmark_symbol=benchmark_symbol,
        output_path=output_paths["report"],
    )
    config_snapshot = {
        "csv_path": str(csv_path),
        "output_dir": str(output_dir),
        "initial_cash": initial_cash,
        "rebalance_interval": rebalance_interval,
        "top_n": top_n,
        "target_exposure": target_exposure,
        "fee_rate": fee_rate,
        "slippage": slippage,
        "use_risk_manager": use_risk_manager,
        "auto_run_dir": auto_run_dir,
        "benchmark_symbol": benchmark_symbol,
        "out_of_sample_ratio": out_of_sample_ratio,
    }
    metadata = write_metadata(
        path=output_paths["metadata"],
        config=config_snapshot,
        summary=summary,
        output_paths=output_paths,
        actual_output_dir=actual_output_dir,
    )
    if auto_run_dir:
        append_run_index(output_paths["run_index"], metadata)

    result = {
        "nav": nav,
        "trades": trades,
        "positions": positions,
        "signals": signals,
        "summary": summary,
        "report": report,
        "output_paths": output_paths,
        "actual_output_dir": actual_output_dir,
    }
    if benchmark_symbol is not None:
        result["benchmark_nav"] = benchmark_nav
        result["strategy_vs_benchmark"] = strategy_vs_benchmark
    return result
