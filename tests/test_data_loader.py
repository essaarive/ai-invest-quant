import pandas as pd

from ai_invest_quant.data.loader import load_csv


def test_valid_csv_loads_to_clean_dataframe(tmp_path):
    path = tmp_path / "prices.csv"
    pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-01"],
            "symbol": ["AAA", "AAA"],
            "open": [11.0, 10.0],
            "high": [12.0, 11.0],
            "low": [10.0, 9.0],
            "close": [11.5, 10.5],
            "volume": [1200, 1000],
            "amount": [13800.0, 10500.0],
        }
    ).to_csv(path, index=False)

    df = load_csv(path)

    assert isinstance(df, pd.DataFrame)
    assert df["date"].tolist() == [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-02")]
    assert df["close"].tolist() == [10.5, 11.5]
    for column in ["open", "high", "low", "close", "volume", "amount"]:
        assert pd.api.types.is_numeric_dtype(df[column])
