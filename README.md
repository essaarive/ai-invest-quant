# AI Invest Quant

AI Invest Quant is an MVP for researching AI-assisted investment quant workflows. It focuses on local CSV data, ETF rotation signals, backtesting, risk controls, performance metrics, and Markdown reports.

## Quick Start

Run the built-in ETF rotation demo with the bundled sample data:

```bash
pip install -e ".[dev]"
ai-invest-quant run-demo
```

By default, demo outputs are written to:

```text
outputs/demo/
```

Use a custom output directory:

```bash
ai-invest-quant run-demo --output-dir /tmp/ai_invest_quant_demo
```

## Supported Features

- Local CSV loading, validation, cleaning, sorting, and symbol/date deduplication
- MA20 / MA60 / MA120 trend indicators
- Daily and 20-trading-day returns
- ETF rotation target-weight signals
- Basic open-price backtest execution with fees and slippage
- Portfolio accounting and trade records
- Optional risk manager with position, exposure, and drawdown mode controls
- Performance summary metrics
- Markdown backtest report generation
- End-to-end ETF rotation demo pipeline
- Local Streamlit Dashboard for demo backtest visualization

## Not Supported

This project does not support live trading, real broker connections, automatic order placement, external data pulling, Crypto, user login, or cloud deployment.

## CSV Data Format

Input CSV files must contain:

```text
date,symbol,open,high,low,close,volume,amount
```

Example:

```csv
date,symbol,open,high,low,close,volume,amount
2024-01-01,ETF_A,79.7502,80.3095,79.2717,79.9100,100000,7991000.0000
2024-01-01,ETF_B,82.3153,82.8104,81.8214,82.4100,105000,8653050.0000
```

Rules:

- `date` must be parseable by pandas.
- `symbol` cannot be empty.
- `open`, `high`, `low`, and `close` must be numeric and greater than 0.
- `volume` and `amount` must be numeric and greater than or equal to 0.
- `high` must be greater than or equal to `open`, `close`, and `low`.
- `low` must be less than or equal to `open`, `close`, and `high`.

## Install

Development install:

```bash
pip install -e ".[dev]"
```

Legacy dependency-only install:

```bash
pip install -r requirements.txt
```

## Run Tests

```bash
PYTHONPATH=src python3 -m pytest
```

## Run Demo Pipeline

Use the bundled sample data:

```bash
ai-invest-quant run-demo
```

This uses:

```text
data/samples/sample_etf_prices.csv
```

and writes to:

```text
outputs/demo/
```

The script accepts a custom output directory:

```bash
PYTHONPATH=src python3 scripts/run_demo.py --output-dir /tmp/ai_invest_quant_demo
```

## CLI Usage

View help:

```bash
ai-invest-quant --help
```

Legacy module form:

```bash
PYTHONPATH=src python3 -m ai_invest_quant.cli --help
```

Run the default demo:

```bash
ai-invest-quant run-demo
```

Legacy module form:

```bash
PYTHONPATH=src python3 -m ai_invest_quant.cli run-demo
```

Run with explicit parameters:

```bash
ai-invest-quant run-demo \
  --csv-path data/samples/sample_etf_prices.csv \
  --output-dir outputs/demo \
  --initial-cash 1000000 \
  --rebalance-interval 5 \
  --top-n 3 \
  --target-exposure 0.8 \
  --fee-rate 0.001 \
  --slippage 0.0005 \
  --no-risk-manager
```

Run from a local experiment config:

```bash
ai-invest-quant run-demo --config configs/demo_config.json
```

Override config values from the CLI:

```bash
ai-invest-quant run-demo \
  --config configs/demo_config.json \
  --top-n 2 \
  --output-dir outputs/config_test
```

Parameter priority is:

```text
CLI arguments > config file > defaults
```

The `ai-invest-quant` CLI only runs local historical backtests. It does not connect to real brokers, does not place orders, and does not provide investment advice.

## Dashboard

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run the local Streamlit Dashboard:

```bash
streamlit run dashboard/app.py
```

The Dashboard lets you configure the bundled demo backtest, run it locally, and view:

- Core performance metrics
- NAV curve
- Drawdown curve
- Latest positions
- Recent trades
- Recent signals
- Generated Markdown report
- CSV upload for your own ETF price data
- Buttons to download output files
- Local JSON experiment config save/load for reproducible runs

By default, Dashboard outputs are written to:

```text
outputs/dashboard_demo/
```

The default Dashboard experiment config is:

```text
configs/demo_config.json
```

The config is a local JSON file containing run parameters:

```json
{
  "csv_path": "data/samples/sample_etf_prices.csv",
  "output_dir": "outputs/dashboard_demo",
  "initial_cash": 1000000,
  "rebalance_interval": 5,
  "top_n": 3,
  "target_exposure": 0.8,
  "fee_rate": 0.001,
  "slippage": 0.0005,
  "use_risk_manager": true
}
```

Use `Load Config` in the sidebar to load parameters from a JSON file. Use `Save Config` to save the current Dashboard parameters for later reproduction.

The same config can be used by the CLI:

```bash
ai-invest-quant run-demo --config configs/demo_config.json
```

Experiment config files only store local historical backtest parameters. They should not contain broker credentials or secrets. They do not enable real trading, automatic order placement, or financial advice.

You can use the default sample CSV or upload your own ETF CSV from the sidebar. Uploaded CSV files still go through the same local data validation pipeline and must contain:

```text
date,symbol,open,high,low,close,volume,amount
```

After a run completes, the Dashboard provides download output files buttons for:

- `nav.csv`
- `trades.csv`
- `positions.csv`
- `signals.csv`
- `report.md`

The Dashboard only displays local historical backtest results. It does not connect to real brokers, does not download external data, does not place orders, and does not provide investment advice.

The lower-level Python pipeline can also be called directly:

```bash
PYTHONPATH=src python3 -c "from ai_invest_quant.pipeline.run_etf_rotation_demo import run_etf_rotation_demo; run_etf_rotation_demo('path/to/prices.csv')"
```

You can also choose an output directory:

```bash
PYTHONPATH=src python3 -c "from ai_invest_quant.pipeline.run_etf_rotation_demo import run_etf_rotation_demo; run_etf_rotation_demo('path/to/prices.csv', output_dir='outputs/demo')"
```

## Output Files

The demo pipeline writes:

- `nav.csv`: daily cash, positions value, equity, NAV, risk mode, and drawdown
- `trades.csv`: executed trades
- `positions.csv`: daily position snapshots
- `signals.csv`: ETF rotation target-weight signals
- `report.md`: Markdown backtest report

## Risk Disclaimer

This project is for historical research and backtesting only. It does not provide financial advice, does not guarantee future results, does not connect to real brokers, and does not place real orders.
