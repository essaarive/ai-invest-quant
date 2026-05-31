import pandas as pd
import pytest

from ai_invest_quant.backtest.engine import run_backtest
from ai_invest_quant.risk.risk_manager import RiskManager


def make_prices() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=5)
    rows = []
    for date in dates:
        rows.extend(
            [
                {"date": date, "symbol": "ETF_A", "open": 100.0, "close": 110.0},
                {"date": date, "symbol": "ETF_B", "open": 50.0, "close": 60.0},
            ]
        )
    return pd.DataFrame(rows)


def make_multi_symbol_prices(symbols: list[str]) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=3)
    rows = []
    for date in dates:
        for symbol in symbols:
            rows.append({"date": date, "symbol": symbol, "open": 100.0, "close": 100.0})
    return pd.DataFrame(rows)


def test_execute_date_open_is_trade_price_and_close_is_not_used_for_execution():
    prices = make_prices()
    signals = pd.DataFrame(
        {
            "signal_date": [pd.Timestamp("2024-01-01")],
            "execute_date": [pd.Timestamp("2024-01-02")],
            "symbol": ["ETF_A"],
            "target_weight": [0.5],
        }
    )

    _, trades, _ = run_backtest(prices, signals, initial_cash=1000, fee_rate=0.0, slippage=0.0)

    assert trades.loc[0, "trade_date"] == pd.Timestamp("2024-01-02")
    assert trades.loc[0, "price"] == 100.0
    assert trades.loc[0, "quantity"] == 5.0


def test_cash_signal_clears_positions_and_cash_never_enters_positions():
    prices = make_prices()
    signals = pd.DataFrame(
        [
            {
                "signal_date": pd.Timestamp("2024-01-01"),
                "execute_date": pd.Timestamp("2024-01-02"),
                "symbol": "ETF_A",
                "target_weight": 0.5,
            },
            {
                "signal_date": pd.Timestamp("2024-01-02"),
                "execute_date": pd.Timestamp("2024-01-03"),
                "symbol": "CASH",
                "target_weight": 1.0,
            },
        ]
    )

    _, trades, positions = run_backtest(
        prices, signals, initial_cash=1000, fee_rate=0.0, slippage=0.0
    )

    assert trades["side"].tolist() == ["buy", "sell"]
    assert trades.loc[1, "symbol"] == "ETF_A"
    assert "CASH" not in positions["symbol"].tolist()
    assert positions[positions["date"] >= pd.Timestamp("2024-01-03")].empty


def test_symbols_missing_from_new_target_are_sold_before_new_buys():
    prices = make_prices()
    signals = pd.DataFrame(
        [
            {
                "signal_date": pd.Timestamp("2024-01-01"),
                "execute_date": pd.Timestamp("2024-01-02"),
                "symbol": "ETF_A",
                "target_weight": 1.0,
            },
            {
                "signal_date": pd.Timestamp("2024-01-02"),
                "execute_date": pd.Timestamp("2024-01-03"),
                "symbol": "ETF_B",
                "target_weight": 1.0,
            },
        ]
    )

    _, trades, _ = run_backtest(prices, signals, initial_cash=1000, fee_rate=0.0, slippage=0.0)

    day_two_trades = trades[trades["trade_date"] == pd.Timestamp("2024-01-03")]
    assert day_two_trades["side"].tolist() == ["sell", "buy"]
    assert day_two_trades["symbol"].tolist() == ["ETF_A", "ETF_B"]


def test_buying_considers_fee_and_slippage_and_cash_is_not_negative():
    prices = make_prices()
    signals = pd.DataFrame(
        {
            "signal_date": [pd.Timestamp("2024-01-01")],
            "execute_date": [pd.Timestamp("2024-01-02")],
            "symbol": ["ETF_A"],
            "target_weight": [1.0],
        }
    )

    nav, trades, _ = run_backtest(
        prices, signals, initial_cash=1000, fee_rate=0.001, slippage=0.0005
    )

    assert trades.loc[0, "quantity"] < 10
    assert (nav["cash"] >= -1e-8).all()
    assert trades.loc[0, "cash_after"] >= 0


def test_daily_nav_uses_close_mark_to_market_and_first_day_is_initial_nav():
    prices = make_prices()
    signals = pd.DataFrame(
        {
            "signal_date": [pd.Timestamp("2024-01-01")],
            "execute_date": [pd.Timestamp("2024-01-02")],
            "symbol": ["ETF_A"],
            "target_weight": [0.5],
        }
    )

    nav, _, positions = run_backtest(prices, signals, initial_cash=1000, fee_rate=0.0, slippage=0.0)

    assert nav.loc[0, "equity"] == 1000
    assert nav.loc[0, "nav"] == 1.0
    assert nav.loc[1, "positions_value"] == 5 * 110
    assert nav.loc[1, "equity"] == 1050
    assert positions.loc[0, "market_value"] == 5 * 110
    assert positions.loc[0, "weight"] == (5 * 110) / 1050


def test_output_columns_are_complete():
    prices = make_prices()
    signals = pd.DataFrame(
        {
            "signal_date": [pd.Timestamp("2024-01-01")],
            "execute_date": [pd.Timestamp("2024-01-02")],
            "symbol": ["ETF_A"],
            "target_weight": [0.5],
        }
    )

    nav, trades, positions = run_backtest(
        prices, signals, initial_cash=1000, fee_rate=0.0, slippage=0.0
    )

    assert list(nav.columns) == [
        "date",
        "cash",
        "positions_value",
        "equity",
        "nav",
        "risk_mode",
        "drawdown",
    ]
    assert list(trades.columns) == [
        "trade_date",
        "symbol",
        "side",
        "quantity",
        "price",
        "trade_amount",
        "fee",
        "cash_after",
        "position_after",
    ]
    assert list(positions.columns) == [
        "date",
        "symbol",
        "quantity",
        "close",
        "market_value",
        "weight",
    ]


def test_changing_execute_date_close_does_not_change_trade_price_or_quantity():
    prices = make_prices()
    signals = pd.DataFrame(
        {
            "signal_date": [pd.Timestamp("2024-01-01")],
            "execute_date": [pd.Timestamp("2024-01-02")],
            "symbol": ["ETF_A"],
            "target_weight": [0.5],
        }
    )
    _, baseline_trades, _ = run_backtest(
        prices, signals, initial_cash=1000, fee_rate=0.0, slippage=0.0
    )

    changed = prices.copy()
    changed.loc[
        (changed["date"] == pd.Timestamp("2024-01-02")) & (changed["symbol"] == "ETF_A"), "close"
    ] = 1_000_000
    _, updated_trades, _ = run_backtest(
        changed, signals, initial_cash=1000, fee_rate=0.0, slippage=0.0
    )

    assert baseline_trades.loc[0, "price"] == updated_trades.loc[0, "price"]
    assert baseline_trades.loc[0, "quantity"] == updated_trades.loc[0, "quantity"]


def test_changing_future_prices_does_not_change_current_execute_trade():
    prices = make_prices()
    signals = pd.DataFrame(
        {
            "signal_date": [pd.Timestamp("2024-01-01")],
            "execute_date": [pd.Timestamp("2024-01-02")],
            "symbol": ["ETF_A"],
            "target_weight": [0.5],
        }
    )
    _, baseline_trades, _ = run_backtest(
        prices, signals, initial_cash=1000, fee_rate=0.0, slippage=0.0
    )

    changed = prices.copy()
    changed.loc[changed["date"] > pd.Timestamp("2024-01-02"), ["open", "close"]] = 1_000_000
    _, updated_trades, _ = run_backtest(
        changed, signals, initial_cash=1000, fee_rate=0.0, slippage=0.0
    )

    assert baseline_trades.loc[0, "price"] == updated_trades.loc[0, "price"]
    assert baseline_trades.loc[0, "quantity"] == updated_trades.loc[0, "quantity"]


@pytest.mark.parametrize("target_weight", [-0.1, 1.1])
def test_invalid_target_weight_bounds_raise_error(target_weight):
    prices = make_prices()
    signals = pd.DataFrame(
        {
            "signal_date": [pd.Timestamp("2024-01-01")],
            "execute_date": [pd.Timestamp("2024-01-02")],
            "symbol": ["ETF_A"],
            "target_weight": [target_weight],
        }
    )

    with pytest.raises(ValueError, match="target_weight.*>= 0.*<= 1"):
        run_backtest(prices, signals)


def test_duplicate_execute_date_and_symbol_raises_error():
    prices = make_prices()
    signals = pd.DataFrame(
        [
            {
                "signal_date": pd.Timestamp("2024-01-01"),
                "execute_date": pd.Timestamp("2024-01-02"),
                "symbol": "ETF_A",
                "target_weight": 0.4,
            },
            {
                "signal_date": pd.Timestamp("2024-01-01"),
                "execute_date": pd.Timestamp("2024-01-02"),
                "symbol": "ETF_A",
                "target_weight": 0.5,
            },
        ]
    )

    with pytest.raises(ValueError, match="duplicate execute_date \\+ symbol"):
        run_backtest(prices, signals)


def test_etf_target_weight_sum_over_one_for_same_execute_date_raises_error():
    prices = make_prices()
    signals = pd.DataFrame(
        [
            {
                "signal_date": pd.Timestamp("2024-01-01"),
                "execute_date": pd.Timestamp("2024-01-02"),
                "symbol": "ETF_A",
                "target_weight": 0.6,
            },
            {
                "signal_date": pd.Timestamp("2024-01-01"),
                "execute_date": pd.Timestamp("2024-01-02"),
                "symbol": "ETF_B",
                "target_weight": 0.5,
            },
        ]
    )

    with pytest.raises(ValueError, match="ETF target_weight sum cannot exceed 1"):
        run_backtest(prices, signals)


def test_cash_and_etf_same_execute_date_raises_error():
    prices = make_prices()
    signals = pd.DataFrame(
        [
            {
                "signal_date": pd.Timestamp("2024-01-01"),
                "execute_date": pd.Timestamp("2024-01-02"),
                "symbol": "CASH",
                "target_weight": 1.0,
            },
            {
                "signal_date": pd.Timestamp("2024-01-01"),
                "execute_date": pd.Timestamp("2024-01-02"),
                "symbol": "ETF_A",
                "target_weight": 0.5,
            },
        ]
    )

    with pytest.raises(ValueError, match="CASH and ETF signals cannot appear"):
        run_backtest(prices, signals)


def test_cash_signal_target_weight_must_be_one():
    prices = make_prices()
    signals = pd.DataFrame(
        {
            "signal_date": [pd.Timestamp("2024-01-01")],
            "execute_date": [pd.Timestamp("2024-01-02")],
            "symbol": ["CASH"],
            "target_weight": [0.5],
        }
    )

    with pytest.raises(ValueError, match="CASH signal target_weight must be 1.0"):
        run_backtest(prices, signals)


def test_risk_manager_none_keeps_original_trade_behavior():
    prices = make_prices()
    signals = pd.DataFrame(
        {
            "signal_date": [pd.Timestamp("2024-01-01")],
            "execute_date": [pd.Timestamp("2024-01-02")],
            "symbol": ["ETF_A"],
            "target_weight": [1.0],
        }
    )

    nav, trades, _ = run_backtest(
        prices,
        signals,
        initial_cash=1000,
        fee_rate=0.0,
        slippage=0.0,
        risk_manager=None,
    )

    assert trades.loc[0, "quantity"] == 10.0
    assert nav["risk_mode"].isna().all()


def test_risk_manager_limits_single_position_weight_in_backtest():
    prices = make_prices()
    signals = pd.DataFrame(
        {
            "signal_date": [pd.Timestamp("2024-01-01")],
            "execute_date": [pd.Timestamp("2024-01-02")],
            "symbol": ["ETF_A"],
            "target_weight": [0.8],
        }
    )

    _, trades, _ = run_backtest(
        prices,
        signals,
        initial_cash=1000,
        fee_rate=0.0,
        slippage=0.0,
        risk_manager=RiskManager(),
    )

    assert trades.loc[0, "trade_amount"] == 300.0
    assert trades.loc[0, "quantity"] == 3.0


def test_risk_manager_limits_total_exposure_to_eighty_percent_in_backtest():
    symbols = ["ETF_A", "ETF_B", "ETF_C", "ETF_D"]
    prices = make_multi_symbol_prices(symbols)
    signals = pd.DataFrame(
        {
            "signal_date": [pd.Timestamp("2024-01-01")] * 4,
            "execute_date": [pd.Timestamp("2024-01-02")] * 4,
            "symbol": symbols,
            "target_weight": [0.25, 0.25, 0.25, 0.25],
        }
    )

    _, trades, _ = run_backtest(
        prices,
        signals,
        initial_cash=1000,
        fee_rate=0.0,
        slippage=0.0,
        risk_manager=RiskManager(),
    )

    assert trades["trade_amount"].sum() == pytest.approx(800.0)
    assert trades["quantity"].tolist() == [2.0, 2.0, 2.0, 2.0]


def test_defensive_mode_limits_total_exposure_to_thirty_percent_in_backtest():
    symbols = ["ETF_A", "ETF_B", "ETF_C"]
    prices = make_multi_symbol_prices(symbols)
    signals = pd.DataFrame(
        {
            "signal_date": [pd.Timestamp("2024-01-01")] * 3,
            "execute_date": [pd.Timestamp("2024-01-01")] * 3,
            "symbol": symbols,
            "target_weight": [0.3, 0.3, 0.3],
        }
    )
    risk_manager = RiskManager()
    risk_manager.mode = "defensive"

    _, trades, _ = run_backtest(
        prices,
        signals,
        initial_cash=1000,
        fee_rate=0.0,
        slippage=0.0,
        risk_manager=risk_manager,
    )

    assert trades["trade_amount"].sum() == pytest.approx(300.0)
    assert trades["quantity"].tolist() == [1.0, 1.0, 1.0]


def test_daily_close_updates_risk_manager_state_and_nav_fields():
    prices = pd.DataFrame(
        [
            {"date": pd.Timestamp("2024-01-01"), "symbol": "ETF_A", "open": 100.0, "close": 100.0},
            {"date": pd.Timestamp("2024-01-02"), "symbol": "ETF_A", "open": 100.0, "close": 80.0},
            {"date": pd.Timestamp("2024-01-03"), "symbol": "ETF_A", "open": 100.0, "close": 80.0},
        ]
    )
    signals = pd.DataFrame(
        {
            "signal_date": [pd.Timestamp("2024-01-01")],
            "execute_date": [pd.Timestamp("2024-01-02")],
            "symbol": ["ETF_A"],
            "target_weight": [1.0],
        }
    )
    risk_manager = RiskManager(
        max_position_weight=1.0, normal_max_exposure=1.0, defensive_max_exposure=0.3
    )

    nav, _, _ = run_backtest(
        prices,
        signals,
        initial_cash=1000,
        fee_rate=0.0,
        slippage=0.0,
        risk_manager=risk_manager,
    )

    assert list(nav[["risk_mode", "drawdown"]].columns) == ["risk_mode", "drawdown"]
    assert risk_manager.mode == "defensive"
    assert nav.loc[1, "risk_mode"] == "defensive"
    assert nav.loc[1, "drawdown"] == pytest.approx(-0.2)
