import numpy as np
import pandas as pd

from ai_invest_quant.indicators.returns import add_daily_return, add_period_return


def make_prices(symbol: str, start: int, periods: int) -> pd.DataFrame:
    close = np.arange(start, start + periods, dtype=float)
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=periods),
            "symbol": symbol,
            "close": close,
        }
    )


def test_daily_return_first_row_per_symbol_is_empty_and_independent():
    df = pd.concat([make_prices("BBB", 101, 30), make_prices("AAA", 1, 30)], ignore_index=True)
    result = add_daily_return(df)

    assert result.index.tolist() == list(range(len(result)))

    aaa = result[result["symbol"] == "AAA"].reset_index(drop=True)
    bbb = result[result["symbol"] == "BBB"].reset_index(drop=True)

    assert pd.isna(aaa.loc[0, "return_1d"])
    assert pd.isna(bbb.loc[0, "return_1d"])
    assert aaa.loc[1, "return_1d"] == 2 / 1 - 1
    assert bbb.loc[1, "return_1d"] == 102 / 101 - 1


def test_period_return_window_twenty_and_independent_by_symbol():
    df = pd.concat([make_prices("BBB", 101, 30), make_prices("AAA", 1, 30)], ignore_index=True)
    result = add_period_return(df, window=20)

    assert result.index.tolist() == list(range(len(result)))

    aaa = result[result["symbol"] == "AAA"].reset_index(drop=True)
    bbb = result[result["symbol"] == "BBB"].reset_index(drop=True)

    assert aaa.loc[:19, "return_20d"].isna().all()
    assert aaa.loc[20, "return_20d"] == 21 / 1 - 1
    assert bbb.loc[20, "return_20d"] == 121 / 101 - 1


def test_returns_do_not_use_future_data():
    df = make_prices("AAA", 1, 30)
    baseline = add_period_return(add_daily_return(df), window=20)

    changed = df.copy()
    changed.loc[29, "close"] = 1_000_000.0
    updated = add_period_return(add_daily_return(changed), window=20)

    pd.testing.assert_series_equal(
        baseline.loc[:20, "return_1d"],
        updated.loc[:20, "return_1d"],
        check_names=False,
    )
    pd.testing.assert_series_equal(
        baseline.loc[:20, "return_20d"],
        updated.loc[:20, "return_20d"],
        check_names=False,
    )


def test_return_indicators_do_not_mutate_input():
    df = make_prices("AAA", 1, 30)
    add_daily_return(df)
    add_period_return(df)
    assert "return_1d" not in df.columns
    assert "return_20d" not in df.columns
