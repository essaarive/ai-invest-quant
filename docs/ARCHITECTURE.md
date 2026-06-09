# Architecture

Current architecture status: V0.3.2 Research Workbench.

## High-Level Architecture

AI Invest Quant is organized as a local research pipeline. Each module owns one part of the workflow:

- Asset Layer: manage watchlists and asset metadata for local real-data workflows
- Data Layer: adapt external ETF CSV columns, standardize multiple CSV files, load, validate, clean, sort, and deduplicate local market data
- Data Quality Layer: inspect standardized OHLCV data before analysis
- Indicators: calculate moving averages and returns
- Strategy: standardize strategy metadata/interfaces and generate ETF rotation target-weight signals
- Backtest Engine: execute signals on historical prices and produce NAV, trades, and positions
- Risk Manager: apply position caps, exposure caps, and drawdown-based defensive mode
- Performance: calculate strategy metrics, benchmark comparison, and out-of-sample evaluation
- Report: generate Markdown reports, metadata, run index, historical loading, and run comparison helpers
- Pipeline: run the full ETF rotation workflow end to end, parameter sensitivity analysis, and walk-forward testing
- CLI: expose local demo execution and `run-sensitivity` through `ai-invest-quant`
- Dashboard: provide a local Streamlit interface for running, loading, comparing, and downloading experiments
- Experiment Management: preserve config snapshots, metadata, timestamped run directories, and `runs/index.csv`

## Data Flow

```text
raw CSV files
-> watchlist / asset metadata
-> multi CSV standardization
-> standardized CSV
-> data quality report
-> data adapter
-> loader / validator / cleaner
-> indicators
-> strategy signals
-> backtest engine
-> nav / trades / positions
-> metrics / benchmark / OOS
-> report / metadata / index / sensitivity summary / walk-forward summary
-> CLI / Dashboard
```

## Core Modules

- `src/ai_invest_quant/assets/`: Watchlist loading, validation, and saving
- `src/ai_invest_quant/data/`: ETF CSV data adapter, multi CSV standardization, standardized OHLCV quality checks, CSV loading, field validation, numeric conversion, date parsing, sorting, and deduplication
- `src/ai_invest_quant/indicators/`: moving averages and return indicators
- `src/ai_invest_quant/strategies/`: Strategy Protocol, StrategyMetadata, ETFRotationStrategy wrapper, and ETF rotation signal generation
- `src/ai_invest_quant/backtest/`: historical execution engine
- `src/ai_invest_quant/portfolio/`: portfolio and broker-style accounting helpers
- `src/ai_invest_quant/risk/`: risk manager and target-weight clipping
- `src/ai_invest_quant/performance/`: performance metrics, benchmark comparison, and out-of-sample evaluation
- `src/ai_invest_quant/report/`: Markdown report, metadata, run index, historical loading, and run comparison
- `src/ai_invest_quant/pipeline/`: end-to-end ETF rotation demo runner, sensitivity pipeline, and walk-forward pipeline
- `src/ai_invest_quant/config/`: JSON experiment config loading, validation, and saving
- `dashboard/`: local Streamlit Dashboard

## Backtest Assumptions

- Signals are generated using signal date data only.
- Execution occurs on the next trading day open.
- Sell orders are processed before buy orders.
- No short selling is modeled.
- No hidden leverage is introduced.
- Fees and slippage are modeled.
- Remaining unallocated capital is kept as cash.
- Benchmark is used only for historical comparison.

## Asset Layer

The asset layer supports a local real-data workflow:

- `watchlist.csv` records `symbol`, `name`, `market`, `asset_type`, `currency`, and `data_path`.
- Watchlist validation checks required fields and allowed market / asset type values.
- Multi CSV standardization reads each watchlist row, standardizes its raw CSV, merges prices,
  and writes `asset_metadata.csv`.
- The standardized prices file still uses `date,symbol,open,high,low,close,volume,amount`.

## Data Quality Layer

The data quality layer checks standardized OHLCV data before analysis:

- `quality_report.py` generates one report row per symbol.
- It checks duplicate dates, missing values, non-positive prices, invalid high/low ranges,
  negative volume, and negative amount.
- It can write `data_quality_report.csv` for audit and review.
- The report is a basic quality gate and does not change the standardized OHLCV format.

## Strategy Layer

The strategy layer is intentionally lightweight:

- `StrategyMetadata` stores strategy name, version, and description.
- `Strategy Protocol` defines the expected `generate_signals(price_df)` method.
- `ETFRotationStrategy` wraps the existing ETF rotation function for future class-based usage.
- The existing function-based API remains compatible for pipelines and tests.

## Risk Assumptions

- Single-position weight caps can be applied.
- Total exposure caps can be applied.
- Defensive mode is based on equity drawdown.
- Risk limits are applied at rebalance.
- Risk controls are not a guarantee against loss.

## Experiment Management

Experiment management is local and file-based:

- JSON config files store reproducible run parameters.
- `metadata.json` stores version, run time, config snapshot, summary metrics, and output paths.
- `auto_run_dir` creates timestamped run directories under `runs/`.
- `runs/index.csv` records historical experiment summaries.
- Historical loading reads previous run outputs without rerunning backtests.
- Run comparison reads local historical outputs and compares metrics, configs, and normalized NAV.
