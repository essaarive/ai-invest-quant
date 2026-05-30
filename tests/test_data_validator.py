import pandas as pd
import pytest

from ai_invest_quant.data.validator import validate_market_data


def valid_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "symbol": ["AAA", "AAA"],
            "open": [10.0, 11.0],
            "high": [12.0, 12.0],
            "low": [9.0, 10.0],
            "close": [11.0, 11.5],
            "volume": [1000, 1200],
            "amount": [11000.0, 13800.0],
        }
    )


def assert_invalid(df: pd.DataFrame, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        validate_market_data(df)


def test_missing_close_raises_clear_error():
    assert_invalid(valid_df().drop(columns=["close"]), "Missing required columns: close")


def test_missing_symbol_raises_clear_error():
    assert_invalid(valid_df().drop(columns=["symbol"]), "Missing required columns: symbol")


def test_invalid_date_raises_error():
    df = valid_df()
    df.loc[0, "date"] = "not-a-date"
    assert_invalid(df, "date.*parseable")


def test_empty_symbol_raises_error():
    df = valid_df()
    df.loc[0, "symbol"] = " "
    assert_invalid(df, "symbol.*empty")


@pytest.mark.parametrize("column", ["open", "high", "low", "close"])
def test_price_columns_must_be_positive(column):
    df = valid_df()
    df.loc[0, column] = 0
    assert_invalid(df, f"{column}.*> 0")


@pytest.mark.parametrize("column", ["volume", "amount"])
def test_volume_and_amount_must_be_non_negative(column):
    df = valid_df()
    df.loc[0, column] = -1
    assert_invalid(df, f"{column}.*>= 0")


@pytest.mark.parametrize(
    ("high", "expected_message"),
    [
        (9.5, "high.*>= open"),
        (10.5, "high.*>= open"),
    ],
)
def test_high_must_not_be_below_open_or_close(high, expected_message):
    df = valid_df()
    df.loc[0, "high"] = high
    assert_invalid(df, expected_message)


@pytest.mark.parametrize(
    ("low", "expected_message"),
    [
        (10.5, "low.*<= open"),
        (11.5, "low.*<= open"),
    ],
)
def test_low_must_not_be_above_open_or_close(low, expected_message):
    df = valid_df()
    df.loc[0, "low"] = low
    assert_invalid(df, expected_message)

