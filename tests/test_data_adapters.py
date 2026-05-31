import pandas as pd
import pytest

from ai_invest_quant.data.adapters import (
    STANDARD_COLUMNS,
    standardize_price_columns,
    standardize_price_csv,
)


def test_standard_english_columns_are_detected():
    df = pd.DataFrame(
        {
            "date": ["2024-01-01"],
            "symbol": ["ETF_A"],
            "open": [10],
            "high": [11],
            "low": [9],
            "close": [10.5],
            "volume": [1000],
            "amount": [10500],
        }
    )

    result = standardize_price_columns(df)

    assert result.columns.tolist() == STANDARD_COLUMNS
    assert result.loc[0, "symbol"] == "ETF_A"


def test_case_variant_english_columns_are_detected():
    df = pd.DataFrame(
        {
            "Date": ["2024-01-01"],
            "Ticker": ["ETF_A"],
            "Open": [10],
            "High": [11],
            "Low": [9],
            "Adj Close": [10.5],
            "Volume": [1000],
            "Turnover": [10500],
        }
    )

    result = standardize_price_columns(df)

    assert result.columns.tolist() == STANDARD_COLUMNS
    assert result.loc[0, "close"] == 10.5


def test_chinese_columns_are_detected():
    df = pd.DataFrame(
        {
            "日期": ["2024-01-01"],
            "证券代码": ["ETF_A"],
            "开盘价": [10],
            "最高价": [11],
            "最低价": [9],
            "收盘价": [10.5],
            "成交量": [1000],
            "成交金额": [10500],
        }
    )

    result = standardize_price_columns(df)

    assert result.columns.tolist() == STANDARD_COLUMNS
    assert result.loc[0, "amount"] == 10500


def test_column_mapping_overrides_auto_detection():
    df = pd.DataFrame(
        {
            "date": ["wrong"],
            "trade_dt": ["2024-01-01"],
            "sec_code": ["ETF_A"],
            "open_px": [10],
            "high_px": [11],
            "low_px": [9],
            "close_px": [10.5],
            "vol": [1000],
            "amt": [10500],
        }
    )
    mapping = {
        "trade_dt": "date",
        "sec_code": "symbol",
        "open_px": "open",
        "high_px": "high",
        "low_px": "low",
        "close_px": "close",
        "vol": "volume",
        "amt": "amount",
    }

    result = standardize_price_columns(df, column_mapping=mapping)

    assert result.loc[0, "date"] == "2024-01-01"
    assert result.columns.tolist() == STANDARD_COLUMNS


def test_default_symbol_fills_missing_symbol():
    df = pd.DataFrame(
        {
            "date": ["2024-01-01"],
            "open": [10],
            "high": [11],
            "low": [9],
            "close": [10.5],
            "volume": [1000],
            "amount": [10500],
        }
    )

    result = standardize_price_columns(df, default_symbol="ETF_A")

    assert result.loc[0, "symbol"] == "ETF_A"


def test_missing_symbol_without_default_symbol_raises_error():
    df = pd.DataFrame(
        {
            "date": ["2024-01-01"],
            "open": [10],
            "high": [11],
            "low": [9],
            "close": [10.5],
            "volume": [1000],
            "amount": [10500],
        }
    )

    with pytest.raises(ValueError, match="symbol"):
        standardize_price_columns(df)


def test_missing_required_field_raises_error():
    df = pd.DataFrame(
        {
            "date": ["2024-01-01"],
            "symbol": ["ETF_A"],
            "open": [10],
            "high": [11],
            "low": [9],
            "volume": [1000],
            "amount": [10500],
        }
    )

    with pytest.raises(ValueError, match="close"):
        standardize_price_columns(df)


def test_standardize_price_csv_reads_and_saves_standard_csv(tmp_path):
    input_path = tmp_path / "raw.csv"
    output_path = tmp_path / "processed" / "prices.csv"
    pd.DataFrame(
        {
            "Date": ["2024-01-01"],
            "Ticker": ["ETF_A"],
            "Open": [10],
            "High": [11],
            "Low": [9],
            "Close": [10.5],
            "Volume": [1000],
            "Amount": [10500],
        }
    ).to_csv(input_path, index=False)

    result = standardize_price_csv(input_path, output_path=output_path)

    assert output_path.exists()
    assert result.columns.tolist() == STANDARD_COLUMNS
    saved = pd.read_csv(output_path)
    assert saved.columns.tolist() == STANDARD_COLUMNS


def test_standardize_price_columns_does_not_modify_original_dataframe():
    df = pd.DataFrame(
        {
            "Date": ["2024-01-01"],
            "Ticker": ["ETF_A"],
            "Open": [10],
            "High": [11],
            "Low": [9],
            "Close": [10.5],
            "Volume": [1000],
            "Amount": [10500],
        }
    )
    original_columns = df.columns.tolist()

    standardize_price_columns(df)

    assert df.columns.tolist() == original_columns
