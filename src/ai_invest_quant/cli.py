"""Command-line interface for AI Invest Quant."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ai_invest_quant.config.experiment_config import (
    DEFAULT_EXPERIMENT_CONFIG,
    load_experiment_config,
    validate_experiment_config,
)
from ai_invest_quant.pipeline.run_etf_rotation_demo import run_etf_rotation_demo
from ai_invest_quant.pipeline.sensitivity import run_parameter_sensitivity
from ai_invest_quant.report.markdown_report import format_number, format_percentage

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLE_CSV = PROJECT_ROOT / "data" / "samples" / "sample_etf_prices.csv"
DEFAULT_OUTPUT_DIR = "outputs/demo"
DEFAULT_SENSITIVITY_OUTPUT_DIR = "outputs/sensitivity"
DEFAULT_RUN_DEMO_CONFIG = DEFAULT_EXPERIMENT_CONFIG | {
    "csv_path": str(DEFAULT_SAMPLE_CSV),
    "output_dir": DEFAULT_OUTPUT_DIR,
}


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "command_func"):
        parser.print_help()
        return 0

    try:
        args.command_func(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Invest Quant command-line tools.")
    subparsers = parser.add_subparsers(dest="command")

    run_demo_parser = subparsers.add_parser("run-demo", help="Run the built-in ETF rotation demo.")
    run_demo_parser.add_argument("--config", default=None, help="Experiment JSON config path.")
    run_demo_parser.add_argument("--csv-path", default=None, help="Input CSV path.")
    run_demo_parser.add_argument("--output-dir", default=None, help="Output directory.")
    run_demo_parser.add_argument("--initial-cash", type=float, default=None, help="Initial cash.")
    run_demo_parser.add_argument(
        "--rebalance-interval", type=int, default=None, help="Rebalance interval in trading days."
    )
    run_demo_parser.add_argument(
        "--top-n", type=int, default=None, help="Number of symbols to select."
    )
    run_demo_parser.add_argument(
        "--target-exposure", type=float, default=None, help="Target ETF exposure."
    )
    run_demo_parser.add_argument("--fee-rate", type=float, default=None, help="Trade fee rate.")
    run_demo_parser.add_argument("--slippage", type=float, default=None, help="Trade slippage.")
    run_demo_parser.add_argument(
        "--benchmark-symbol", default=None, help="Benchmark symbol to compare against."
    )
    run_demo_parser.add_argument(
        "--out-of-sample-ratio",
        type=float,
        default=None,
        help="Final-date ratio used for out-of-sample evaluation.",
    )

    risk_group = run_demo_parser.add_mutually_exclusive_group()
    risk_group.add_argument(
        "--use-risk-manager",
        dest="use_risk_manager",
        action="store_true",
        help="Enable risk manager.",
    )
    risk_group.add_argument(
        "--no-risk-manager",
        dest="use_risk_manager",
        action="store_false",
        help="Disable risk manager.",
    )
    auto_run_group = run_demo_parser.add_mutually_exclusive_group()
    auto_run_group.add_argument(
        "--auto-run-dir",
        dest="auto_run_dir",
        action="store_true",
        help="Write outputs to output_dir/runs/YYYYMMDD_HHMMSS.",
    )
    auto_run_group.add_argument(
        "--no-auto-run-dir",
        dest="auto_run_dir",
        action="store_false",
        help="Write outputs directly to output_dir.",
    )
    run_demo_parser.set_defaults(
        use_risk_manager=None, auto_run_dir=None, command_func=run_demo_command
    )

    sensitivity_parser = subparsers.add_parser(
        "run-sensitivity",
        help="Run lightweight ETF rotation parameter sensitivity analysis.",
    )
    sensitivity_parser.add_argument(
        "--csv-path", default=str(DEFAULT_SAMPLE_CSV), help="Input CSV path."
    )
    sensitivity_parser.add_argument(
        "--output-dir", default=DEFAULT_SENSITIVITY_OUTPUT_DIR, help="Output directory."
    )
    sensitivity_parser.add_argument(
        "--top-n-values", default="1,2,3", help="Comma-separated positive integers."
    )
    sensitivity_parser.add_argument(
        "--target-exposure-values",
        default="0.5,0.8",
        help="Comma-separated exposure values in [0, 1].",
    )
    sensitivity_parser.add_argument(
        "--rebalance-interval-values",
        default="5,10",
        help="Comma-separated positive integer rebalance intervals.",
    )
    sensitivity_parser.add_argument("--initial-cash", type=float, default=1_000_000)
    sensitivity_parser.add_argument("--fee-rate", type=float, default=0.001)
    sensitivity_parser.add_argument("--slippage", type=float, default=0.0005)
    sensitivity_parser.add_argument("--benchmark-symbol", default=None)
    sensitivity_parser.add_argument("--out-of-sample-ratio", type=float, default=0.3)
    sensitivity_risk_group = sensitivity_parser.add_mutually_exclusive_group()
    sensitivity_risk_group.add_argument(
        "--use-risk-manager",
        dest="use_risk_manager",
        action="store_true",
        help="Enable risk manager.",
    )
    sensitivity_risk_group.add_argument(
        "--no-risk-manager",
        dest="use_risk_manager",
        action="store_false",
        help="Disable risk manager.",
    )
    sensitivity_parser.set_defaults(use_risk_manager=True, command_func=run_sensitivity_command)

    return parser


def run_demo_command(args: argparse.Namespace) -> None:
    """Validate arguments, run the demo, and print output paths and metrics."""
    run_config = _build_run_demo_config(args)
    _validate_run_demo_config(run_config)
    result = run_etf_rotation_demo(
        csv_path=run_config["csv_path"],
        output_dir=run_config["output_dir"],
        initial_cash=run_config["initial_cash"],
        rebalance_interval=run_config["rebalance_interval"],
        top_n=run_config["top_n"],
        target_exposure=run_config["target_exposure"],
        fee_rate=run_config["fee_rate"],
        slippage=run_config["slippage"],
        use_risk_manager=run_config["use_risk_manager"],
        auto_run_dir=run_config["auto_run_dir"],
        benchmark_symbol=run_config["benchmark_symbol"],
        out_of_sample_ratio=run_config["out_of_sample_ratio"],
    )

    summary = result["summary"]
    output_paths = result["output_paths"]
    print("Demo completed")
    print(f"nav.csv: {output_paths['nav']}")
    print(f"trades.csv: {output_paths['trades']}")
    print(f"positions.csv: {output_paths['positions']}")
    print(f"signals.csv: {output_paths['signals']}")
    if "benchmark_nav" in output_paths:
        print(f"benchmark_nav.csv: {output_paths['benchmark_nav']}")
    if "strategy_vs_benchmark" in output_paths:
        print(f"strategy_vs_benchmark.csv: {output_paths['strategy_vs_benchmark']}")
    print(f"report.md: {output_paths['report']}")
    print(f"Total Return: {format_percentage(summary.get('total_return'))}")
    print(f"Max Drawdown: {format_percentage(summary.get('max_drawdown'))}")
    print(f"Sharpe Ratio: {format_number(summary.get('sharpe_ratio'))}")
    if "benchmark_total_return" in summary:
        print(f"Benchmark Total Return: {format_percentage(summary.get('benchmark_total_return'))}")
        print(f"Benchmark Max Drawdown: {format_percentage(summary.get('benchmark_max_drawdown'))}")
        print(f"Excess Total Return: {format_percentage(summary.get('excess_total_return'))}")


def run_sensitivity_command(args: argparse.Namespace) -> None:
    """Validate arguments, run parameter sensitivity, and print summary location."""
    csv_path = _resolve_csv_path(args.csv_path)
    _validate_sensitivity_args(args, csv_path)
    result = run_parameter_sensitivity(
        csv_path=csv_path,
        output_dir=args.output_dir,
        top_n_values=parse_int_list(args.top_n_values),
        target_exposure_values=parse_float_list(args.target_exposure_values),
        rebalance_interval_values=parse_int_list(args.rebalance_interval_values),
        initial_cash=args.initial_cash,
        fee_rate=args.fee_rate,
        slippage=args.slippage,
        use_risk_manager=args.use_risk_manager,
        benchmark_symbol=args.benchmark_symbol,
        out_of_sample_ratio=args.out_of_sample_ratio,
    )

    print("Sensitivity analysis completed.")
    print(f"Summary: {result['summary_path']}")
    print(f"Runs: {len(result['runs'])}")


def parse_int_list(value: str) -> list[int]:
    """Parse comma-separated positive integers."""
    if not value or not value.strip():
        raise ValueError("Expected comma-separated positive integers")
    try:
        values = [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as exc:
        raise ValueError("Expected comma-separated positive integers") from exc
    if not values or any(item <= 0 for item in values):
        raise ValueError("Expected comma-separated positive integers")
    return values


def parse_float_list(value: str) -> list[float]:
    """Parse comma-separated floats."""
    if not value or not value.strip():
        raise ValueError("Expected comma-separated numeric values")
    try:
        values = [float(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as exc:
        raise ValueError("Expected comma-separated numeric values") from exc
    if not values:
        raise ValueError("Expected comma-separated numeric values")
    return values


def _build_run_demo_config(args: argparse.Namespace) -> dict[str, object]:
    config = dict(DEFAULT_RUN_DEMO_CONFIG)
    if args.config is not None:
        config.update(load_experiment_config(args.config))

    cli_values = {
        "csv_path": args.csv_path,
        "output_dir": args.output_dir,
        "initial_cash": args.initial_cash,
        "rebalance_interval": args.rebalance_interval,
        "top_n": args.top_n,
        "target_exposure": args.target_exposure,
        "fee_rate": args.fee_rate,
        "slippage": args.slippage,
        "use_risk_manager": args.use_risk_manager,
        "auto_run_dir": args.auto_run_dir,
        "benchmark_symbol": args.benchmark_symbol,
        "out_of_sample_ratio": args.out_of_sample_ratio,
    }
    config.update({key: value for key, value in cli_values.items() if value is not None})
    config = validate_experiment_config(config)
    config["csv_path"] = str(_resolve_csv_path(config["csv_path"]))
    return config


def _resolve_csv_path(csv_path: str) -> Path:
    path = Path(csv_path)
    if path.exists() or path.is_absolute():
        return path

    project_path = PROJECT_ROOT / path
    if project_path.exists():
        return project_path

    return path


def _validate_run_demo_config(config: dict[str, object]) -> None:
    csv_path = Path(str(config["csv_path"]))
    if not csv_path.exists():
        raise ValueError(f"csv_path does not exist: {csv_path}")
    if config["initial_cash"] <= 0:
        raise ValueError("initial_cash must be > 0")
    if config["rebalance_interval"] <= 0:
        raise ValueError("rebalance_interval must be > 0")
    if config["top_n"] <= 0:
        raise ValueError("top_n must be > 0")
    if config["target_exposure"] < 0 or config["target_exposure"] > 1:
        raise ValueError("target_exposure must be >= 0 and <= 1")
    if config["fee_rate"] < 0:
        raise ValueError("fee_rate must be >= 0")
    if config["slippage"] < 0:
        raise ValueError("slippage must be >= 0")
    if config["out_of_sample_ratio"] < 0 or config["out_of_sample_ratio"] >= 1:
        raise ValueError("out_of_sample_ratio must be >= 0 and < 1")


def _validate_sensitivity_args(args: argparse.Namespace, csv_path: Path) -> None:
    if not csv_path.exists():
        raise ValueError(f"csv_path does not exist: {csv_path}")
    if args.initial_cash <= 0:
        raise ValueError("initial_cash must be > 0")
    if args.fee_rate < 0:
        raise ValueError("fee_rate must be >= 0")
    if args.slippage < 0:
        raise ValueError("slippage must be >= 0")
    if args.out_of_sample_ratio < 0 or args.out_of_sample_ratio >= 1:
        raise ValueError("out_of_sample_ratio must be >= 0 and < 1")

    top_n_values = parse_int_list(args.top_n_values)
    target_exposure_values = parse_float_list(args.target_exposure_values)
    rebalance_interval_values = parse_int_list(args.rebalance_interval_values)
    if any(value < 0 or value > 1 for value in target_exposure_values):
        raise ValueError("target_exposure_values must be >= 0 and <= 1")
    if any(value <= 0 for value in top_n_values):
        raise ValueError("top_n_values must be positive integers")
    if any(value <= 0 for value in rebalance_interval_values):
        raise ValueError("rebalance_interval_values must be positive integers")


if __name__ == "__main__":
    raise SystemExit(main())
