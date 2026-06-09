# Real Data Guide

This guide explains the local real-data workflow for preparing ETF, stock, index, fund,
and crypto research CSV files for AI Invest Quant.

The project does not download market data automatically. Users prepare raw CSV files locally,
then standardize them into the existing backtest schema.

## Workflow

```text
raw CSV files
-> watchlist.csv
-> standardize_many_price_csvs
-> prices.csv
-> asset_metadata.csv
-> Dashboard / CLI analysis
```

## watchlist.csv

The watchlist records each asset and the raw CSV path to standardize.

```csv
symbol,name,market,asset_type,currency,data_path
510300,沪深300ETF,CN,ETF,CNY,data/raw/510300.csv
SPY,SPDR S&P 500 ETF,US,ETF,USD,data/raw/SPY.csv
BTCUSDT,Bitcoin,CRYPTO,CRYPTO,USDT,data/raw/BTCUSDT.csv
```

Required fields:

```text
symbol,name,market,asset_type,currency,data_path
```

`name` may be empty, but the column must exist. `symbol`, `market`, `asset_type`,
`currency`, and `data_path` cannot be empty.

Supported `market` values:

- CN
- HK
- US
- CRYPTO

Supported `asset_type` values:

- ETF
- STOCK
- CRYPTO
- INDEX
- FUND

## Raw Price CSV Fields

Raw CSV files may use common English or Chinese field names. The workflow reuses the existing
data adapter to standardize fields into:

```text
date,symbol,open,high,low,close,volume,amount
```

Recommended date format:

```text
YYYY-MM-DD
```

If a raw CSV does not contain a symbol column, the watchlist `symbol` is used as the default
symbol for that file.

## Python Example

```python
from ai_invest_quant.data.multi_csv import standardize_many_price_csvs

standardize_many_price_csvs(
    watchlist_path="data/watchlist.csv",
    output_path="data/processed/prices.csv",
    metadata_output_path="data/processed/asset_metadata.csv",
)
```

Outputs:

- `prices.csv`: standardized market data with `date,symbol,open,high,low,close,volume,amount`
- `asset_metadata.csv`: asset metadata with `symbol,name,market,asset_type,currency,data_path`

## Data Quality Report

After `standardize_many_price_csvs`, run a basic data quality check before analysis:

```python
from ai_invest_quant.data.quality_report import generate_data_quality_report

quality_report = generate_data_quality_report(
    price_df=result["prices"],
    output_path="data/processed/data_quality_report.csv",
)
```

Output file:

```text
data/processed/data_quality_report.csv
```

The report focuses on:

- `duplicate_date_count`
- `missing_value_count`
- `zero_or_negative_price_count`
- `high_low_error_count`
- `negative_volume_count`
- `negative_amount_count`
- `is_passed`
- `issues`

The data quality report can catch basic structural and OHLCV errors, but it cannot guarantee
that data is accurate. Adjustments, suspensions, dividends, splits, and exchange-specific
rules still need to be confirmed by the user.

## CLI / Dashboard Usage

After standardizing real data, run the existing local historical analysis tools:

```bash
ai-invest-quant run-demo \
  --csv-path data/processed/prices.csv \
  --benchmark-symbol 510300
```

The Dashboard can also use `data/processed/prices.csv` as the CSV path.

## Risks And Limits

- This project does not automatically download market data.
- Users need to prepare legal, clean, local data.
- Data quality directly affects backtest results.
- Multi-market assets have different trading rules.
- The current backtest still uses a unified OHLCV schema.
- A-share price limits, suspensions, and T+1 settlement are not fully modeled.
- Hong Kong board lots, stamp duties, and trading fees are not fully modeled.
- US dividends, splits, and adjustments depend on user-provided data quality.
- Crypto 24/7 trading, funding rates, derivatives, and leverage are not supported.
- This workflow is for local historical research only and does not provide investment advice.
