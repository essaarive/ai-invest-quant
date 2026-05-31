import pandas as pd

from ai_invest_quant.data.cleaner import clean_market_data


def test_cleaner_parses_dates_sorts_deduplicates_and_resets_index():
    df = pd.DataFrame(
        {
            "date": ["2024-01-03", "2024-01-01", "2024-01-02", "2024-01-02"],
            "symbol": ["BBB", "AAA", "AAA", "AAA"],
            "open": [30.0, 10.0, 11.0, 99.0],
            "high": [31.0, 11.0, 12.0, 100.0],
            "low": [29.0, 9.0, 10.0, 98.0],
            "close": [30.5, 10.5, 11.5, 99.5],
            "volume": [3000, 1000, 1100, 9999],
            "amount": [91500.0, 10500.0, 12650.0, 995000.0],
        },
        index=[10, 11, 12, 13],
    )

    cleaned = clean_market_data(df)

    assert pd.api.types.is_datetime64_any_dtype(cleaned["date"])
    assert cleaned[["symbol", "date"]].values.tolist() == [
        ["AAA", pd.Timestamp("2024-01-01")],
        ["AAA", pd.Timestamp("2024-01-02")],
        ["BBB", pd.Timestamp("2024-01-03")],
    ]
    assert cleaned.loc[1, "close"] == 99.5
    assert cleaned.index.tolist() == [0, 1, 2]
