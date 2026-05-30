import pandas as pd
import pytest

from ai_invest_quant.strategies.etf_rotation import generate_etf_rotation_signals


def make_rows(dates, symbols, return_20d=None, ma60=90.0, close=100.0):
    rows = []
    return_20d = return_20d or {symbol: 0.1 for symbol in symbols}
    for date in dates:
        for symbol in symbols:
            rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "open": close,
                    "high": close + 1,
                    "low": close - 1,
                    "close": close,
                    "volume": 1000,
                    "amount": 100000,
                    "ma60": ma60,
                    "return_20d": return_20d[symbol],
                }
            )
    return pd.DataFrame(rows)


def test_signal_dates_every_five_trading_days_and_execute_next_day():
    dates = pd.date_range("2024-01-01", periods=11)
    df = make_rows(dates, ["ETF_A"])

    result = generate_etf_rotation_signals(df)

    assert result["signal_date"].tolist() == [dates[0], dates[5]]
    assert result["execute_date"].tolist() == [dates[1], dates[6]]
    assert (result["signal_date"] != result["execute_date"]).all()


def test_result_index_is_continuous_from_zero():
    dates = pd.date_range("2024-01-01", periods=11)
    df = make_rows(dates, ["ETF_A", "ETF_B", "ETF_C"])

    result = generate_etf_rotation_signals(df)

    assert result.index.tolist() == list(range(len(result)))


def test_close_less_than_or_equal_to_ma60_is_not_selected():
    date = pd.Timestamp("2024-01-01")
    df = make_rows([date, date + pd.Timedelta(days=1)], ["GOOD", "BAD"])
    df.loc[(df["date"] == date) & (df["symbol"] == "BAD"), "close"] = 90.0

    result = generate_etf_rotation_signals(df)

    assert result["symbol"].tolist() == ["GOOD"]


def test_empty_ma60_or_return_20d_is_not_selected():
    date = pd.Timestamp("2024-01-01")
    df = make_rows([date, date + pd.Timedelta(days=1)], ["GOOD", "NO_MA", "NO_RETURN"])
    df.loc[(df["date"] == date) & (df["symbol"] == "NO_MA"), "ma60"] = pd.NA
    df.loc[(df["date"] == date) & (df["symbol"] == "NO_RETURN"), "return_20d"] = pd.NA

    result = generate_etf_rotation_signals(df)

    assert result["symbol"].tolist() == ["GOOD"]


def test_selects_top_three_by_return_20d_descending():
    dates = pd.date_range("2024-01-01", periods=2)
    df = make_rows(
        dates,
        ["ETF_A", "ETF_B", "ETF_C", "ETF_D"],
        return_20d={"ETF_A": 0.4, "ETF_B": 0.1, "ETF_C": 0.3, "ETF_D": 0.2},
    )

    result = generate_etf_rotation_signals(df)

    assert result["symbol"].tolist() == ["ETF_A", "ETF_C", "ETF_D"]
    assert result["rank"].tolist() == [1, 2, 3]


def test_three_symbols_get_equal_target_exposure_weight():
    dates = pd.date_range("2024-01-01", periods=2)
    df = make_rows(dates, ["ETF_A", "ETF_B", "ETF_C"])

    result = generate_etf_rotation_signals(df)

    assert result["target_weight"].tolist() == [0.8 / 3, 0.8 / 3, 0.8 / 3]
    assert "CASH" not in result["symbol"].tolist()


def test_two_symbols_get_half_target_exposure_weight():
    dates = pd.date_range("2024-01-01", periods=2)
    df = make_rows(dates, ["ETF_A", "ETF_B"])

    result = generate_etf_rotation_signals(df)

    assert result["target_weight"].tolist() == [0.8 / 2, 0.8 / 2]


def test_one_symbol_gets_full_target_exposure_weight():
    dates = pd.date_range("2024-01-01", periods=2)
    df = make_rows(dates, ["ETF_A"])

    result = generate_etf_rotation_signals(df)

    assert result.loc[0, "symbol"] == "ETF_A"
    assert result.loc[0, "target_weight"] == 0.8


def test_no_eligible_symbol_outputs_cash_signal():
    dates = pd.date_range("2024-01-01", periods=2)
    df = make_rows(dates, ["ETF_A", "ETF_B"], ma60=100.0, close=90.0)

    result = generate_etf_rotation_signals(df)

    assert result.loc[0, "symbol"] == "CASH"
    assert result.loc[0, "target_weight"] == 1.0
    assert result.loc[0, "rank"] is None
    assert result.loc[0, "reason"] == "no_eligible_symbol"


@pytest.mark.parametrize("target_exposure", [-0.01, 1.01])
def test_invalid_target_exposure_raises_error(target_exposure):
    dates = pd.date_range("2024-01-01", periods=2)
    df = make_rows(dates, ["ETF_A"])

    with pytest.raises(ValueError, match="target_exposure.*>= 0.*<= 1"):
        generate_etf_rotation_signals(df, target_exposure=target_exposure)


def test_execute_date_values_do_not_affect_signal_date_selection():
    dates = pd.date_range("2024-01-01", periods=2)
    df = make_rows(
        dates,
        ["ETF_A", "ETF_B"],
        return_20d={"ETF_A": 0.1, "ETF_B": 0.2},
    )
    baseline = generate_etf_rotation_signals(df)

    changed = df.copy()
    execute_date = dates[1]
    changed.loc[(changed["date"] == execute_date) & (changed["symbol"] == "ETF_A"), "return_20d"] = 99.0
    changed.loc[(changed["date"] == execute_date) & (changed["symbol"] == "ETF_A"), "close"] = 1_000_000.0
    changed.loc[(changed["date"] == execute_date) & (changed["symbol"] == "ETF_B"), "return_20d"] = -99.0
    changed.loc[(changed["date"] == execute_date) & (changed["symbol"] == "ETF_B"), "close"] = 1.0
    updated = generate_etf_rotation_signals(changed)

    pd.testing.assert_frame_equal(baseline, updated)
