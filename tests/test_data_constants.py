from ai_invest_quant.data import adapters, quality_report, validator
from ai_invest_quant.data.constants import (
    BASE_PRICE_COLUMNS,
    OHLC_COLUMNS,
    PRICE_NUMERIC_COLUMNS,
)


def test_base_price_columns_are_standard_tuple():
    assert isinstance(BASE_PRICE_COLUMNS, tuple)
    assert BASE_PRICE_COLUMNS == (
        "date",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "amount",
    )


def test_ohlc_columns_are_standard_tuple():
    assert isinstance(OHLC_COLUMNS, tuple)
    assert OHLC_COLUMNS == ("open", "high", "low", "close")


def test_price_numeric_columns_include_price_volume_and_amount():
    assert PRICE_NUMERIC_COLUMNS == ("open", "high", "low", "close", "volume", "amount")


def test_modules_use_standard_price_columns():
    assert tuple(adapters.STANDARD_COLUMNS) == BASE_PRICE_COLUMNS
    assert validator.REQUIRED_COLUMNS == BASE_PRICE_COLUMNS
    assert quality_report.REQUIRED_COLUMNS == BASE_PRICE_COLUMNS
