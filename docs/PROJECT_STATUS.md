# Project Status

## Project Name

AI Invest Quant

## Current Version

V0.3.1 Research Workbench

## Current Status

AI Invest Quant is a local ETF rotation quantitative research workbench. It is designed for historical backtesting, experiment management, benchmark comparison, out-of-sample evaluation, parameter sensitivity analysis, and local visual inspection through a Streamlit Dashboard.

The project is intended for research, learning, and reproducible strategy experiments. It is not an automatic trading system.

## Supported Features

- Local CSV data loading
- ETF CSV data adapter
- Data validation and cleaning
- Trend and return indicators
- ETF rotation signal generation
- Backtest engine
- Portfolio and broker simulation
- Risk manager
- Performance metrics
- Markdown report
- Streamlit Dashboard
- English / 中文 Dashboard labels
- Enhanced Chinese Dashboard display labels and localized table columns
- CSV upload
- Output downloads
- JSON experiment config
- CLI config support
- `metadata.json`
- Auto run directory
- `runs/index.csv`
- Historical run loading
- Historical run comparison
- Benchmark comparison
- Out-of-sample evaluation
- Parameter sensitivity analysis
- Walk-forward testing
- CLI `run-sensitivity` support
- CLI `run-walk-forward` support

## Not Supported

- Live trading
- Broker connection
- Automatic order placement
- Real-time data feed
- Crypto trading
- User accounts
- Cloud deployment
- Investment advice

## Latest Test Result

250 passed

## Development Quality Checks

- `pytest`
- `ruff check`
- `ruff format`
- CI enabled with GitHub Actions
- CI runs `ruff check` and `pytest`

## GitHub Presentation Status

- README optimized for project showcase
- Dashboard screenshots added
- Documentation links are available from the GitHub project front page

## Current Recommended Use

- Local historical backtesting
- ETF strategy research
- Parameter comparison across historical runs
- Risk mode and drawdown observation
- Benchmark comparison
- Out-of-sample robustness checks

This project should not be used as an automatic trading system.
