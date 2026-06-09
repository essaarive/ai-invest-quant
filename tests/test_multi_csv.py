import pandas as pd
import pytest

from ai_invest_quant.data.multi_csv import standardize_many_price_csvs

STANDARD_COLUMNS = ["date", "symbol", "open", "high", "low", "close", "volume", "amount"]
METADATA_COLUMNS = ["symbol", "name", "market", "asset_type", "currency", "data_path"]


def write_price_csv(path, symbol: str | None = None) -> None:
    rows = [
        {
            "Date": "2024-01-02",
            "Open": 10.0,
            "High": 11.0,
            "Low": 9.0,
            "Close": 10.5,
            "Volume": 1000,
            "Amount": 10500,
        },
        {
            "Date": "2024-01-01",
            "Open": 9.0,
            "High": 10.0,
            "Low": 8.0,
            "Close": 9.5,
            "Volume": 900,
            "Amount": 8550,
        },
    ]
    if symbol is not None:
        for row in rows:
            row["Ticker"] = symbol
    pd.DataFrame(rows).to_csv(path, index=False)


def write_watchlist(path, rows) -> None:
    pd.DataFrame(rows).to_csv(path, index=False)


def make_watchlist_rows(first_path, second_path):
    return [
        {
            "symbol": "ETF_B",
            "name": "ETF B",
            "market": "US",
            "asset_type": "ETF",
            "currency": "USD",
            "data_path": str(second_path),
        },
        {
            "symbol": "ETF_A",
            "name": "ETF A",
            "market": "US",
            "asset_type": "ETF",
            "currency": "USD",
            "data_path": str(first_path),
        },
    ]


def test_standardize_many_price_csvs_merges_two_csvs(tmp_path):
    first_csv = tmp_path / "a.csv"
    second_csv = tmp_path / "b.csv"
    write_price_csv(first_csv)
    write_price_csv(second_csv, symbol="ETF_B")
    watchlist_path = tmp_path / "watchlist.csv"
    output_path = tmp_path / "processed" / "prices.csv"
    metadata_path = tmp_path / "processed" / "asset_metadata.csv"
    write_watchlist(watchlist_path, make_watchlist_rows(first_csv, second_csv))

    result = standardize_many_price_csvs(watchlist_path, output_path, metadata_path)

    prices = result["prices"]
    metadata = result["metadata"]
    assert list(prices.columns) == STANDARD_COLUMNS
    assert list(metadata.columns) == METADATA_COLUMNS
    assert output_path.exists()
    assert metadata_path.exists()
    assert len(prices) == 4


def test_missing_symbol_in_raw_csv_uses_watchlist_symbol(tmp_path):
    price_csv = tmp_path / "a.csv"
    write_price_csv(price_csv)
    watchlist_path = tmp_path / "watchlist.csv"
    output_path = tmp_path / "prices.csv"
    write_watchlist(watchlist_path, make_watchlist_rows(price_csv, price_csv)[:1])

    result = standardize_many_price_csvs(watchlist_path, output_path)

    assert result["prices"]["symbol"].tolist() == ["ETF_B", "ETF_B"]


def test_empty_watchlist_raises_error(tmp_path):
    watchlist_path = tmp_path / "watchlist.csv"
    pd.DataFrame(columns=METADATA_COLUMNS).to_csv(watchlist_path, index=False)

    with pytest.raises(ValueError, match="watchlist cannot be empty"):
        standardize_many_price_csvs(watchlist_path, tmp_path / "prices.csv")


def test_missing_data_path_raises_error(tmp_path):
    missing_csv = tmp_path / "missing.csv"
    watchlist_path = tmp_path / "watchlist.csv"
    write_watchlist(watchlist_path, make_watchlist_rows(missing_csv, missing_csv)[:1])

    with pytest.raises(FileNotFoundError, match="Price CSV not found"):
        standardize_many_price_csvs(watchlist_path, tmp_path / "prices.csv")


def test_merged_prices_are_sorted_by_symbol_and_date(tmp_path):
    first_csv = tmp_path / "a.csv"
    second_csv = tmp_path / "b.csv"
    write_price_csv(first_csv)
    write_price_csv(second_csv)
    watchlist_path = tmp_path / "watchlist.csv"
    write_watchlist(watchlist_path, make_watchlist_rows(first_csv, second_csv))

    result = standardize_many_price_csvs(watchlist_path, tmp_path / "prices.csv")

    pairs = list(zip(result["prices"]["symbol"], result["prices"]["date"], strict=True))
    assert pairs == sorted(pairs)
