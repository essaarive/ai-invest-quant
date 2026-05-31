"""Basic open-price trade execution with fees and slippage."""

from __future__ import annotations

from ai_invest_quant.portfolio.portfolio import Portfolio


def execute_trade(
    portfolio: Portfolio,
    symbol: str,
    side: str,
    quantity: float,
    open_price: float,
    fee_rate: float = 0.001,
    slippage: float = 0.0005,
    trade_date=None,
) -> dict[str, object]:
    """Execute a long-only buy or sell against a Portfolio."""
    quantity = float(quantity)
    open_price = float(open_price)

    if side not in {"buy", "sell"}:
        raise ValueError("side must be 'buy' or 'sell'")
    if quantity <= 0:
        raise ValueError("quantity must be > 0")
    if open_price <= 0:
        raise ValueError("open_price must be > 0")
    if symbol == Portfolio.CASH_SYMBOL:
        raise ValueError("CASH is not a tradable symbol")

    if side == "buy":
        price = open_price * (1 + slippage)
        trade_amount = quantity * price
        fee = trade_amount * fee_rate
        total_cost = trade_amount + fee
        if total_cost > portfolio.cash + Portfolio.CASH_TOLERANCE:
            raise ValueError("insufficient cash for buy")

        portfolio.cash = portfolio.cash - total_cost
        portfolio.update_position(symbol, quantity)
    else:
        current_quantity = portfolio.get_position(symbol)
        if quantity > current_quantity + Portfolio.POSITION_TOLERANCE:
            raise ValueError("cannot sell more than current position")

        price = open_price * (1 - slippage)
        trade_amount = quantity * price
        fee = trade_amount * fee_rate
        net_proceeds = trade_amount - fee
        portfolio.update_position(symbol, -quantity)
        portfolio.cash = portfolio.cash + net_proceeds

    return {
        "trade_date": trade_date,
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "price": price,
        "trade_amount": trade_amount,
        "fee": fee,
        "cash_after": portfolio.cash,
        "position_after": portfolio.get_position(symbol),
    }
