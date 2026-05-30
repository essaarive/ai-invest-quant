"""Command-line interface for AI Invest Quant."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ai_invest_quant.pipeline.run_etf_rotation_demo import run_etf_rotation_demo
from ai_invest_quant.report.markdown_report import format_number, format_percentage


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLE_CSV = PROJECT_ROOT / "data" / "samples" / "sample_etf_prices.csv"
DEFAULT_OUTPUT_DIR = "outputs/demo"


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "command_func"):
        parser.print_help()
        return 0

    try:
        args.command_func(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Invest Quant command-line tools.")
    subparsers = parser.add_subparsers(dest="command")

    run_demo_parser = subparsers.add_parser("run-demo", help="Run the built-in ETF rotation demo.")
    run_demo_parser.add_argument("--csv-path", default=str(DEFAULT_SAMPLE_CSV), help="Input CSV path.")
    run_demo_parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory.")
    run_demo_parser.add_argument("--initial-cash", type=float, default=1_000_000, help="Initial cash.")
    run_demo_parser.add_argument("--rebalance-interval", type=int, default=5, help="Rebalance interval in trading days.")
    run_demo_parser.add_argument("--top-n", type=int, default=3, help="Number of symbols to select.")
    run_demo_parser.add_argument("--target-exposure", type=float, default=0.8, help="Target ETF exposure.")
    run_demo_parser.add_argument("--fee-rate", type=float, default=0.001, help="Trade fee rate.")
    run_demo_parser.add_argument("--slippage", type=float, default=0.0005, help="Trade slippage.")

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
    run_demo_parser.set_defaults(use_risk_manager=True, command_func=run_demo_command)

    return parser


def run_demo_command(args: argparse.Namespace) -> None:
    """Validate arguments, run the demo, and print output paths and metrics."""
    _validate_run_demo_args(args)
    result = run_etf_rotation_demo(
        csv_path=args.csv_path,
        output_dir=args.output_dir,
        initial_cash=args.initial_cash,
        rebalance_interval=args.rebalance_interval,
        top_n=args.top_n,
        target_exposure=args.target_exposure,
        fee_rate=args.fee_rate,
        slippage=args.slippage,
        use_risk_manager=args.use_risk_manager,
    )

    summary = result["summary"]
    output_paths = result["output_paths"]
    print("Demo completed")
    print(f"nav.csv: {output_paths['nav']}")
    print(f"trades.csv: {output_paths['trades']}")
    print(f"positions.csv: {output_paths['positions']}")
    print(f"signals.csv: {output_paths['signals']}")
    print(f"report.md: {output_paths['report']}")
    print(f"Total Return: {format_percentage(summary.get('total_return'))}")
    print(f"Max Drawdown: {format_percentage(summary.get('max_drawdown'))}")
    print(f"Sharpe Ratio: {format_number(summary.get('sharpe_ratio'))}")


def _validate_run_demo_args(args: argparse.Namespace) -> None:
    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        raise ValueError(f"csv_path does not exist: {csv_path}")
    if args.initial_cash <= 0:
        raise ValueError("initial_cash must be > 0")
    if args.rebalance_interval <= 0:
        raise ValueError("rebalance_interval must be > 0")
    if args.top_n <= 0:
        raise ValueError("top_n must be > 0")
    if args.target_exposure < 0 or args.target_exposure > 1:
        raise ValueError("target_exposure must be >= 0 and <= 1")
    if args.fee_rate < 0:
        raise ValueError("fee_rate must be >= 0")
    if args.slippage < 0:
        raise ValueError("slippage must be >= 0")


if __name__ == "__main__":
    raise SystemExit(main())

