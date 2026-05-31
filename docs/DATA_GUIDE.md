# Data Guide

## Standard CSV Format

AI Invest Quant uses one standard price schema:

```text
date,symbol,open,high,low,close,volume,amount
```

## Date Format

Recommended date format:

```text
YYYY-MM-DD
```

## Example CSV

```csv
date,symbol,open,high,low,close,volume,amount
2024-01-01,ETF_A,10.00,10.50,9.80,10.20,100000,1020000
2024-01-02,ETF_A,10.20,10.80,10.10,10.60,120000,1272000
```

## Chinese Data Source Example

Many Chinese ETF CSV exports can be mapped automatically when they use common columns:

```csv
日期,代码,开盘,最高,最低,收盘,成交量,成交额
2024-01-01,ETF_A,10.00,10.50,9.80,10.20,100000,1020000
```

## English Data Source Example

Common English columns are also supported:

```csv
Date,Ticker,Open,High,Low,Close,Volume,Amount
2024-01-01,ETF_A,10.00,10.50,9.80,10.20,100000,1020000
```

## Using The Data Adapter

```python
from ai_invest_quant.data.adapters import standardize_price_csv

standardize_price_csv(
    input_path="raw.csv",
    output_path="data/processed/etf_prices.csv",
    default_symbol="ETF_A",
)
```

For custom exports, pass a manual mapping. The key is the original column name, and the value is
the standard target column:

```python
standardize_price_csv(
    input_path="raw.csv",
    output_path="data/processed/etf_prices.csv",
    column_mapping={
        "trade_dt": "date",
        "sec_code": "symbol",
        "open_px": "open",
        "high_px": "high",
        "low_px": "low",
        "close_px": "close",
        "vol": "volume",
        "amt": "amount",
    },
)
```

## Important Notes

- This project does not automatically download market data.
- Users need to prepare valid local CSV data.
- Data quality directly affects backtest results.
- This project does not provide investment advice.
