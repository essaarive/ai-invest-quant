"""Local Streamlit dashboard for the ETF rotation demo."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from ai_invest_quant.config.experiment_config import (
    DEFAULT_EXPERIMENT_CONFIG,
    load_experiment_config,
    save_experiment_config,
)
from ai_invest_quant.pipeline.run_etf_rotation_demo import run_etf_rotation_demo
from ai_invest_quant.pipeline.sensitivity import run_parameter_sensitivity
from ai_invest_quant.report.markdown_report import format_number, format_percentage
from ai_invest_quant.report.run_compare import load_runs_for_comparison
from ai_invest_quant.report.run_index import load_run_index
from ai_invest_quant.report.run_loader import load_historical_run

DEFAULT_CSV_PATH = "data/samples/sample_etf_prices.csv"
DEFAULT_OUTPUT_DIR = "outputs/dashboard_demo"
DEFAULT_CONFIG_PATH = "configs/demo_config.json"


def main() -> None:
    st.set_page_config(page_title="AI Invest Quant Dashboard", layout="wide")
    st.title("AI Invest Quant Dashboard")

    with st.sidebar:
        config = st.session_state.setdefault("experiment_config", dict(DEFAULT_EXPERIMENT_CONFIG))
        st.header("Experiment Config")
        config_path = st.text_input("Config JSON Path", value=DEFAULT_CONFIG_PATH)
        config_columns = st.columns(2)
        if config_columns[0].button("Load Config"):
            try:
                config = load_experiment_config(config_path)
                st.session_state["experiment_config"] = config
                st.success(f"Loaded config: {config_path}")
            except (FileNotFoundError, ValueError) as exc:
                st.error(str(exc))

        st.header("Backtest Parameters")
        csv_path = st.text_input("CSV Path", value=config.get("csv_path", DEFAULT_CSV_PATH))
        uploaded_csv = st.file_uploader("Upload ETF price CSV", type=["csv"])
        output_dir = st.text_input(
            "Output Directory", value=config.get("output_dir", DEFAULT_OUTPUT_DIR)
        )
        initial_cash = st.number_input(
            "Initial Cash",
            min_value=1.0,
            value=float(config.get("initial_cash", 1_000_000)),
            step=10_000.0,
        )
        rebalance_interval = st.number_input(
            "Rebalance Interval",
            min_value=1,
            value=int(config.get("rebalance_interval", 5)),
            step=1,
        )
        top_n = st.number_input("Top N", min_value=1, value=int(config.get("top_n", 3)), step=1)
        target_exposure = st.slider(
            "Target Exposure",
            min_value=0.0,
            max_value=1.0,
            value=float(config.get("target_exposure", 0.8)),
            step=0.05,
        )
        fee_rate = st.number_input(
            "Fee Rate",
            min_value=0.0,
            value=float(config.get("fee_rate", 0.001)),
            step=0.0001,
            format="%.4f",
        )
        slippage = st.number_input(
            "Slippage",
            min_value=0.0,
            value=float(config.get("slippage", 0.0005)),
            step=0.0001,
            format="%.4f",
        )
        use_risk_manager = st.checkbox(
            "Use Risk Manager", value=bool(config.get("use_risk_manager", True))
        )
        auto_run_dir = st.checkbox(
            "Use auto run directory", value=bool(config.get("auto_run_dir", False))
        )
        benchmark_symbol = st.text_input(
            "Benchmark symbol", value=config.get("benchmark_symbol") or ""
        )
        out_of_sample_ratio = st.number_input(
            "Out-of-sample ratio",
            min_value=0.0,
            max_value=0.99,
            value=float(config.get("out_of_sample_ratio", 0.3)),
            step=0.05,
            format="%.2f",
        )
        current_config = _build_experiment_config(
            csv_path=csv_path,
            output_dir=output_dir,
            initial_cash=initial_cash,
            rebalance_interval=int(rebalance_interval),
            top_n=int(top_n),
            target_exposure=target_exposure,
            fee_rate=fee_rate,
            slippage=slippage,
            use_risk_manager=use_risk_manager,
            auto_run_dir=auto_run_dir,
            benchmark_symbol=benchmark_symbol.strip() or None,
            out_of_sample_ratio=out_of_sample_ratio,
        )
        if config_columns[1].button("Save Config"):
            try:
                save_experiment_config(current_config, config_path)
                st.session_state["experiment_config"] = current_config
                st.success(f"Saved config: {config_path}")
            except ValueError as exc:
                st.error(str(exc))

        run_button = st.button("Run Backtest", type="primary")

    if run_button:
        selected_csv_path = _resolve_csv_path(csv_path, uploaded_csv, output_dir)
        if selected_csv_path is None:
            return

        _run_dashboard_backtest(
            csv_path=selected_csv_path,
            output_dir=output_dir,
            initial_cash=initial_cash,
            rebalance_interval=int(rebalance_interval),
            top_n=int(top_n),
            target_exposure=target_exposure,
            fee_rate=fee_rate,
            slippage=slippage,
            use_risk_manager=use_risk_manager,
            auto_run_dir=auto_run_dir,
            benchmark_symbol=benchmark_symbol.strip() or None,
            out_of_sample_ratio=out_of_sample_ratio,
        )

    run_index_path = str(Path(output_dir) / "runs" / "index.csv")
    _render_run_history(run_index_path)
    _render_parameter_sensitivity(
        csv_path=csv_path,
        uploaded_csv=uploaded_csv,
        output_dir=output_dir,
        initial_cash=initial_cash,
        fee_rate=fee_rate,
        slippage=slippage,
        use_risk_manager=use_risk_manager,
        benchmark_symbol=benchmark_symbol.strip() or None,
        out_of_sample_ratio=out_of_sample_ratio,
    )

    result = st.session_state.get("dashboard_result")
    if result is None:
        st.info("Set parameters in the sidebar and click Run Backtest.")
        return

    _render_summary(result["summary"])
    st.caption(f"Actual output directory: {result['actual_output_dir']}")
    _render_charts(result["nav"], result.get("strategy_vs_benchmark"))
    _render_tables(result["positions"], result["trades"], result["signals"])
    _render_report(result["report"], result["output_paths"]["report"])
    _render_downloads(result["output_paths"])
    _render_risk_disclaimer()


def _resolve_csv_path(csv_path: str, uploaded_csv, output_dir: str) -> str | None:
    if uploaded_csv is None:
        return csv_path

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    uploaded_path = output_root / "uploaded_etf_prices.csv"
    uploaded_path.write_bytes(uploaded_csv.getbuffer())
    st.info(f"Using uploaded CSV: {uploaded_path}")
    return str(uploaded_path)


def _build_experiment_config(
    csv_path: str,
    output_dir: str,
    initial_cash: float,
    rebalance_interval: int,
    top_n: int,
    target_exposure: float,
    fee_rate: float,
    slippage: float,
    use_risk_manager: bool,
    auto_run_dir: bool,
    benchmark_symbol: str | None,
    out_of_sample_ratio: float,
) -> dict[str, object]:
    return {
        "csv_path": csv_path,
        "output_dir": output_dir,
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


def _run_dashboard_backtest(**kwargs) -> None:
    csv_path = Path(kwargs["csv_path"])
    if not csv_path.exists():
        st.error(f"CSV file not found: {csv_path}")
        return

    with st.spinner("Running backtest..."):
        st.session_state["dashboard_result"] = run_etf_rotation_demo(**kwargs)

    st.success("Backtest completed")


def _render_parameter_sensitivity(
    csv_path: str,
    uploaded_csv,
    output_dir: str,
    initial_cash: float,
    fee_rate: float,
    slippage: float,
    use_risk_manager: bool,
    benchmark_symbol: str | None,
    out_of_sample_ratio: float,
) -> None:
    st.subheader("Parameter Sensitivity")
    top_n_text = st.text_input("Top N values", value="1,2,3")
    exposure_text = st.text_input("Target exposure values", value="0.5,0.8")
    interval_text = st.text_input("Rebalance interval values", value="5,10")
    if st.button("Run Parameter Sensitivity"):
        try:
            top_n_values = _parse_int_list(top_n_text)
            target_exposure_values = _parse_float_list(exposure_text)
            rebalance_interval_values = _parse_int_list(interval_text)
            selected_csv_path = _resolve_csv_path(csv_path, uploaded_csv, output_dir)
            if selected_csv_path is None:
                return

            with st.spinner("Running parameter sensitivity..."):
                result = run_parameter_sensitivity(
                    csv_path=selected_csv_path,
                    output_dir=str(Path(output_dir) / "sensitivity"),
                    top_n_values=top_n_values,
                    target_exposure_values=target_exposure_values,
                    rebalance_interval_values=rebalance_interval_values,
                    initial_cash=initial_cash,
                    fee_rate=fee_rate,
                    slippage=slippage,
                    use_risk_manager=use_risk_manager,
                    benchmark_symbol=benchmark_symbol,
                    out_of_sample_ratio=out_of_sample_ratio,
                )
            st.session_state["sensitivity_result"] = result
            st.success("Parameter sensitivity completed")
        except ValueError as exc:
            st.error(str(exc))

    sensitivity_result = st.session_state.get("sensitivity_result")
    if sensitivity_result is None:
        return

    st.subheader("Sensitivity Summary")
    st.dataframe(sensitivity_result["summary"], use_container_width=True)
    summary_path = Path(sensitivity_result["summary_path"])
    if summary_path.exists():
        st.download_button(
            label="Download sensitivity_summary.csv",
            data=summary_path.read_bytes(),
            file_name="sensitivity_summary.csv",
            mime="text/csv",
        )


def _parse_int_list(value: str) -> list[int]:
    try:
        values = [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as exc:
        raise ValueError("Expected comma-separated integer values") from exc
    if not values:
        raise ValueError("Expected at least one integer value")
    return values


def _parse_float_list(value: str) -> list[float]:
    try:
        values = [float(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as exc:
        raise ValueError("Expected comma-separated numeric values") from exc
    if not values:
        raise ValueError("Expected at least one numeric value")
    return values


def _render_summary(summary: dict) -> None:
    st.subheader("Core Performance Metrics")
    columns = st.columns(4)
    metrics = [
        ("Total Return", format_percentage(summary.get("total_return"))),
        ("Annual Return", format_percentage(summary.get("annual_return"))),
        ("Max Drawdown", format_percentage(summary.get("max_drawdown"))),
        ("Annual Volatility", format_percentage(summary.get("annual_volatility"))),
        ("Sharpe Ratio", format_number(summary.get("sharpe_ratio"))),
        ("Calmar Ratio", format_number(summary.get("calmar_ratio"))),
        ("Rebalance Win Rate", format_percentage(summary.get("rebalance_win_rate"))),
    ]
    if "benchmark_total_return" in summary:
        metrics.extend(
            [
                (
                    "Benchmark Total Return",
                    format_percentage(summary.get("benchmark_total_return")),
                ),
                (
                    "Benchmark Max Drawdown",
                    format_percentage(summary.get("benchmark_max_drawdown")),
                ),
                ("Excess Total Return", format_percentage(summary.get("excess_total_return"))),
            ]
        )
    for index, (label, value) in enumerate(metrics):
        columns[index % len(columns)].metric(label, value)

    if "out_of_sample_total_return" in summary:
        st.subheader("Out-of-Sample Evaluation")
        oos_columns = st.columns(4)
        oos_metrics = [
            ("Split Date", str(summary.get("split_date"))[:10]),
            ("In-Sample Total Return", format_percentage(summary.get("in_sample_total_return"))),
            ("In-Sample Max Drawdown", format_percentage(summary.get("in_sample_max_drawdown"))),
            ("In-Sample Sharpe Ratio", format_number(summary.get("in_sample_sharpe_ratio"))),
            (
                "Out-of-Sample Total Return",
                format_percentage(summary.get("out_of_sample_total_return")),
            ),
            (
                "Out-of-Sample Max Drawdown",
                format_percentage(summary.get("out_of_sample_max_drawdown")),
            ),
            (
                "Out-of-Sample Sharpe Ratio",
                format_number(summary.get("out_of_sample_sharpe_ratio")),
            ),
        ]
        for index, (label, value) in enumerate(oos_metrics):
            oos_columns[index % len(oos_columns)].metric(label, value)


def _render_charts(nav: pd.DataFrame, strategy_vs_benchmark: pd.DataFrame | None = None) -> None:
    st.subheader("NAV")
    nav_chart = nav[["date", "nav"]].copy()
    nav_chart["date"] = pd.to_datetime(nav_chart["date"])
    st.line_chart(nav_chart.set_index("date")["nav"])

    st.subheader("Drawdown")
    if "drawdown" in nav.columns:
        drawdown_chart = nav[["date", "drawdown"]].copy()
        drawdown_chart["date"] = pd.to_datetime(drawdown_chart["date"])
        st.line_chart(drawdown_chart.set_index("date")["drawdown"])
    else:
        st.info("Drawdown data is not available.")

    st.subheader("Strategy vs Benchmark")
    if strategy_vs_benchmark is None or strategy_vs_benchmark.empty:
        st.info("Benchmark is not enabled.")
    else:
        comparison = strategy_vs_benchmark[["date", "strategy_nav", "benchmark_nav"]].copy()
        comparison["date"] = pd.to_datetime(comparison["date"])
        st.line_chart(comparison.set_index("date"))


def _render_tables(positions: pd.DataFrame, trades: pd.DataFrame, signals: pd.DataFrame) -> None:
    st.subheader("Latest Positions")
    if positions.empty:
        st.write("No current positions")
    else:
        latest_date = pd.to_datetime(positions["date"]).max()
        latest_positions = positions[pd.to_datetime(positions["date"]) == latest_date]
        st.dataframe(
            latest_positions.sort_values("weight", ascending=False).head(10),
            use_container_width=True,
        )

    st.subheader("Recent Trades")
    if trades.empty:
        st.write("No trades")
    else:
        st.dataframe(trades.tail(10), use_container_width=True)

    st.subheader("Recent Signals")
    if signals.empty:
        st.write("No signals")
    else:
        st.dataframe(signals.tail(10), use_container_width=True)


def _render_report(report: str, report_path: str) -> None:
    st.subheader("Markdown Report")
    st.caption(f"report.md path: {report_path}")
    st.markdown(report)


def _render_downloads(output_paths: dict[str, str]) -> None:
    st.subheader("Download Outputs")
    downloads = [
        ("nav", "nav.csv", "text/csv"),
        ("trades", "trades.csv", "text/csv"),
        ("positions", "positions.csv", "text/csv"),
        ("signals", "signals.csv", "text/csv"),
        ("report", "report.md", "text/markdown"),
        ("metadata", "metadata.json", "application/json"),
        ("benchmark_nav", "benchmark_nav.csv", "text/csv"),
        ("strategy_vs_benchmark", "strategy_vs_benchmark.csv", "text/csv"),
    ]
    for key, file_name, mime in downloads:
        if key not in output_paths:
            continue
        path = Path(output_paths[key])
        if not path.exists():
            st.info(f"{file_name} is not available.")
            continue
        st.download_button(
            label=f"Download {file_name}",
            data=path.read_bytes(),
            file_name=file_name,
            mime=mime,
        )


def _render_run_history(run_index_path: str | None) -> None:
    st.subheader("Run History")
    if not run_index_path:
        st.info("No run history yet.")
        return

    index = load_run_index(run_index_path)
    if index.empty:
        st.info("No run history yet.")
        return

    columns = [
        "run_time",
        "run_id",
        "total_return",
        "max_drawdown",
        "sharpe_ratio",
        "actual_output_dir",
    ]
    st.dataframe(index[columns].head(20), use_container_width=True)
    options = [
        f"{row.run_time} | {row.run_id} | {row.actual_output_dir}"
        for row in index.itertuples(index=False)
    ]
    selected = st.selectbox("Select historical run", options=options)
    if st.button("Load Historical Run"):
        actual_output_dir = selected.split(" | ", maxsplit=2)[-1]
        historical_result = load_historical_run(actual_output_dir)
        st.session_state["dashboard_result"] = historical_result
        if historical_result["missing_files"]:
            st.warning(
                "Missing historical output files: " + ", ".join(historical_result["missing_files"])
            )
        else:
            st.success(f"Loaded historical run: {actual_output_dir}")

    _render_run_comparison(index)


def _render_run_comparison(index: pd.DataFrame) -> None:
    st.subheader("Compare Historical Runs")
    option_map = {
        _format_run_comparison_option(row): position
        for position, row in enumerate(index.itertuples(index=False))
    }
    selected_options = st.multiselect("Select runs to compare", options=list(option_map))
    if not st.button("Compare Selected Runs"):
        return

    if len(selected_options) < 2:
        st.info("Please select at least 2 runs to compare.")
        return
    if len(selected_options) > 5:
        st.info("Please select no more than 5 runs to compare.")
        return

    selected_positions = [option_map[option] for option in selected_options]
    comparison = load_runs_for_comparison(index.iloc[selected_positions])
    if comparison["missing_files"]:
        st.warning("\n".join(comparison["missing_files"]))

    st.subheader("Metrics Comparison")
    st.dataframe(comparison["metrics"], use_container_width=True)

    st.subheader("Config Comparison")
    st.dataframe(comparison["configs"], use_container_width=True)

    st.subheader("NAV Comparison")
    if comparison["nav_comparison"].empty:
        st.info("No NAV comparison data is available.")
    else:
        st.line_chart(comparison["nav_comparison"])


def _format_run_comparison_option(row) -> str:
    return (
        f"{row.run_time} | {row.run_id} | "
        f"{format_percentage(row.total_return)} | "
        f"{format_percentage(row.max_drawdown)} | "
        f"{format_number(row.sharpe_ratio)}"
    )


def _render_risk_disclaimer() -> None:
    st.subheader("Risk Disclaimer")
    st.markdown(
        "- This Dashboard is for local historical backtest visualization only.\n"
        "- It does not connect to real brokers.\n"
        "- It does not place real orders.\n"
        "- It does not provide financial advice."
    )


if __name__ == "__main__":
    main()
