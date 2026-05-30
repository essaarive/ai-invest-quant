import numpy as np
import pandas as pd

from ai_invest_quant.indicators.trend import add_moving_average


def make_prices(symbol: str, start: int, periods: int) -> pd.DataFrame:
    close = np.arange(start, start + periods, dtype=float)
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=periods),
            "symbol": symbol,
            "close": close,
        }
    )


def test_moving_averages_are_calculated_independently_by_symbol():
    df = pd.concat([make_prices("BBB", 101, 120), make_prices("AAA", 1, 120)], ignore_index=True)
    result = add_moving_average(df)

    assert result.index.tolist() == list(range(len(result)))

    aaa = result[result["symbol"] == "AAA"].reset_index(drop=True)
    bbb = result[result["symbol"] == "BBB"].reset_index(drop=True)

    assert aaa.loc[19, "ma20"] == np.mean(np.arange(1, 21))
    assert bbb.loc[19, "ma20"] == np.mean(np.arange(101, 121))
    assert aaa.loc[:58, "ma60"].isna().all()
    assert aaa.loc[59, "ma60"] == np.mean(np.arange(1, 61))
    assert aaa.loc[119, "ma120"] == np.mean(np.arange(1, 121))


def test_moving_average_does_not_use_future_data():
    df = make_prices("AAA", 1, 80)
    baseline = add_moving_average(df)

    changed = df.copy()
    changed.loc[79, "close"] = 1_000_000.0
    updated = add_moving_average(changed)

    pd.testing.assert_series_equal(
        baseline.loc[:58, "ma20"],
        updated.loc[:58, "ma20"],
        check_names=False,
    )


def test_add_moving_average_does_not_mutate_input():
    df = make_prices("AAA", 1, 20)
    add_moving_average(df)
    assert "ma20" not in df.columns
