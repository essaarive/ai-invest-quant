import pandas as pd
import pytest

from ai_invest_quant.assets.watchlist import load_watchlist, save_watchlist, validate_watchlist


def make_watchlist() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "510300",
                "name": "沪深300ETF",
                "market": "CN",
                "asset_type": "ETF",
                "currency": "CNY",
                "data_path": "data/raw/510300.csv",
            }
        ]
    )


def test_load_watchlist_reads_standard_watchlist(tmp_path):
    path = tmp_path / "watchlist.csv"
    make_watchlist().to_csv(path, index=False)

    result = load_watchlist(path)

    assert result.loc[0, "symbol"] == "510300"


def test_validate_watchlist_accepts_valid_data():
    validate_watchlist(make_watchlist())


def test_missing_required_column_raises_error():
    df = make_watchlist().drop(columns=["data_path"])

    with pytest.raises(ValueError, match="Missing required watchlist columns: data_path"):
        validate_watchlist(df)


def test_empty_symbol_raises_error():
    df = make_watchlist()
    df.loc[0, "symbol"] = ""

    with pytest.raises(ValueError, match="symbol.*cannot be empty"):
        validate_watchlist(df)


def test_invalid_market_raises_error():
    df = make_watchlist()
    df.loc[0, "market"] = "EU"

    with pytest.raises(ValueError, match="Invalid market values: EU"):
        validate_watchlist(df)


def test_invalid_asset_type_raises_error():
    df = make_watchlist()
    df.loc[0, "asset_type"] = "BOND"

    with pytest.raises(ValueError, match="Invalid asset_type values: BOND"):
        validate_watchlist(df)


def test_save_watchlist_creates_parent_directory(tmp_path):
    output_path = tmp_path / "nested" / "watchlist.csv"

    save_watchlist(make_watchlist(), output_path)

    assert output_path.exists()
    saved = pd.read_csv(output_path)
    assert str(saved.loc[0, "symbol"]) == "510300"
