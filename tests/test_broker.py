import pytest

from ai_invest_quant.backtest.broker import execute_trade
from ai_invest_quant.portfolio.portfolio import Portfolio


def test_buy_price_includes_positive_slippage_and_fee_is_deducted():
    portfolio = Portfolio(cash=2000)

    trade = execute_trade(
        portfolio,
        symbol="ETF_A",
        side="buy",
        quantity=10,
        open_price=100,
        fee_rate=0.001,
        slippage=0.0005,
        trade_date="2024-01-02",
    )

    assert trade["price"] == 100 * 1.0005
    assert trade["trade_amount"] == 10 * 100 * 1.0005
    assert trade["fee"] == trade["trade_amount"] * 0.001
    assert portfolio.cash == 2000 - trade["trade_amount"] - trade["fee"]
    assert portfolio.get_position("ETF_A") == 10


def test_sell_price_includes_negative_slippage_and_fee_is_deducted():
    portfolio = Portfolio(cash=0, positions={"ETF_A": 10})

    trade = execute_trade(
        portfolio,
        symbol="ETF_A",
        side="sell",
        quantity=4,
        open_price=100,
        fee_rate=0.001,
        slippage=0.0005,
        trade_date="2024-01-02",
    )

    assert trade["price"] == 100 * 0.9995
    assert trade["trade_amount"] == 4 * 100 * 0.9995
    assert trade["fee"] == trade["trade_amount"] * 0.001
    assert portfolio.cash == trade["trade_amount"] - trade["fee"]
    assert portfolio.get_position("ETF_A") == 6


def test_buy_does_not_allow_negative_cash():
    portfolio = Portfolio(cash=100)

    with pytest.raises(ValueError, match="insufficient cash"):
        execute_trade(portfolio, "ETF_A", "buy", 2, 100)


def test_cannot_sell_more_than_current_position():
    portfolio = Portfolio(cash=0, positions={"ETF_A": 1})

    with pytest.raises(ValueError, match="cannot sell more"):
        execute_trade(portfolio, "ETF_A", "sell", 2, 100)


@pytest.mark.parametrize("quantity", [0, -1])
def test_quantity_must_be_positive(quantity):
    portfolio = Portfolio(cash=1000)

    with pytest.raises(ValueError, match="quantity must be > 0"):
        execute_trade(portfolio, "ETF_A", "buy", quantity, 100)


@pytest.mark.parametrize("open_price", [0, -1])
def test_open_price_must_be_positive(open_price):
    portfolio = Portfolio(cash=1000)

    with pytest.raises(ValueError, match="open_price must be > 0"):
        execute_trade(portfolio, "ETF_A", "buy", 1, open_price)

