import pytest

from ai_invest_quant.portfolio.portfolio import Portfolio


def test_initial_cash_is_set():
    portfolio = Portfolio(cash=1000)

    assert portfolio.cash == 1000


def test_update_position_changes_quantity():
    portfolio = Portfolio(cash=1000)

    portfolio.update_position("ETF_A", 10)
    portfolio.update_position("ETF_A", -3)

    assert portfolio.get_position("ETF_A") == 7


def test_total_equity_uses_cash_and_position_values():
    portfolio = Portfolio(cash=1000)
    portfolio.set_position("ETF_A", 10)
    portfolio.set_position("ETF_B", 5)

    assert portfolio.total_equity({"ETF_A": 20, "ETF_B": 30}) == 1350


def test_cash_symbol_does_not_enter_positions():
    portfolio = Portfolio(cash=1000)

    portfolio.set_position("CASH", 100)
    portfolio.update_position("CASH", 50)

    assert portfolio.positions == {}


def test_obviously_negative_cash_raises_error():
    with pytest.raises(ValueError, match="cash cannot be negative"):
        Portfolio(cash=-1)
