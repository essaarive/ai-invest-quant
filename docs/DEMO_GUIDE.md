# Demo Guide

This guide shows how to run and inspect the local historical ETF rotation demo.

## Run CLI Demo

```bash
pip install -e ".[dev]"
ai-invest-quant run-demo
```

The default demo uses:

```text
data/samples/sample_etf_prices.csv
```

and writes outputs to:

```text
outputs/demo/
```

## Run Dashboard

```bash
streamlit run dashboard/app.py
```

The Dashboard is local-only. It does not connect to brokers and does not place orders.

## Use CSV Upload

Use `Upload ETF price CSV` in the sidebar to run the demo pipeline against your own local CSV.

The CSV must contain:

```text
date,symbol,open,high,low,close,volume,amount
```

Uploaded files still go through the same validation and cleaning pipeline.

## Enable Benchmark

From the CLI:

```bash
ai-invest-quant run-demo --benchmark-symbol ETF_A
```

From the Dashboard, set `Benchmark symbol` in the sidebar.

Benchmark comparison is for historical reference only and does not imply future performance.

## Enable Out-of-Sample Evaluation

From the CLI:

```bash
ai-invest-quant run-demo --out-of-sample-ratio 0.3
```

From the Dashboard, set `Out-of-sample ratio` in the sidebar.

This evaluates the last 30% of trading dates as the out-of-sample period. It does not change strategy logic.

## Use auto_run_dir

```bash
ai-invest-quant run-demo --output-dir outputs --auto-run-dir
```

This creates timestamped experiment directories:

```text
outputs/runs/YYYYMMDD_HHMMSS/
```

## Load Historical Run

In the Dashboard:

1. Set `Output Directory` to the base directory that contains `runs/index.csv`.
2. Use `Select historical run`.
3. Click `Load Historical Run`.

Loading a historical run reads existing output files and does not rerun the backtest.

## Compare Historical Runs

In the Dashboard:

1. Open `Compare Historical Runs`.
2. Use `Select runs to compare`.
3. Select 2 to 5 historical runs.
4. Click `Compare Selected Runs`.

The comparison shows metrics, config values, and normalized NAV curves.

## Download Outputs

After a run completes, the Dashboard can download:

- `nav.csv`
- `trades.csv`
- `positions.csv`
- `signals.csv`
- `report.md`
- `metadata.json`
- `benchmark_nav.csv`
- `strategy_vs_benchmark.csv`
