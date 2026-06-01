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
The sidebar starts with `Language`. English is the default, and 中文 labels can be enabled to make the Dashboard easier to understand for local research.

![Dashboard overview](assets/dashboard_overview.png)

## Use CSV Upload

Use `Upload ETF price CSV` in the sidebar to run the demo pipeline against your own local CSV.

The CSV must contain:

```text
date,symbol,open,high,low,close,volume,amount
```

Uploaded files still go through the same validation and cleaning pipeline.

## Use Data Adapter

Use the ETF CSV data adapter when source files use common Chinese or English column names:

```python
from ai_invest_quant.data.adapters import standardize_price_csv

standardize_price_csv(
    input_path="raw.csv",
    output_path="data/processed/etf_prices.csv",
    default_symbol="ETF_A",
)
```

See [Data Guide](DATA_GUIDE.md) for supported mappings.

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

![Run history](assets/run_history.png)

## Compare Historical Runs

In the Dashboard:

1. Open `Compare Historical Runs`.
2. Use `Select runs to compare`.
3. Select 2 to 5 historical runs.
4. Click `Compare Selected Runs`.

The comparison shows metrics, config values, and normalized NAV curves.

![Historical run comparison](assets/comparison_view.png)

## Run Parameter Sensitivity

From the CLI:

```bash
ai-invest-quant run-sensitivity \
  --top-n-values 1,2,3 \
  --target-exposure-values 0.5,0.8 \
  --rebalance-interval-values 5,10 \
  --benchmark-symbol ETF_A
```

In the Dashboard:

1. Open `Parameter Sensitivity`.
2. Set `Top N values`, such as `1,2,3`.
3. Set `Target exposure values`, such as `0.5,0.8`.
4. Set `Rebalance interval values`, such as `5,10`.
5. Click `Run Parameter Sensitivity`.
6. Review the `Sensitivity Summary` table.
7. Download `sensitivity_summary.csv`.

Each parameter combination is saved as a separate timestamped historical experiment. The summary is
for research stability checks only and is not an investment recommendation.

## Run Walk-forward Testing

In the Dashboard:

1. Open `Walk-forward Testing`.
2. Set `Train window days`.
3. Set `Test window days`.
4. Set `Step days`.
5. Click `Run Walk-forward Test`.
6. Review the `Walk-forward Summary` table.
7. Download `walk_forward_summary.csv`.

Walk-forward testing uses rolling train/test windows. The training window is recorded as structure,
and each test window runs as a separate historical backtest. This is for research only and is not an
investment recommendation.

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
