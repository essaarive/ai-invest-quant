"""Run the built-in ETF rotation demo through the standard CLI."""

from __future__ import annotations

import sys

from ai_invest_quant.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["run-demo", *sys.argv[1:]]))
