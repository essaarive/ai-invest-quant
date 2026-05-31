"""Simple portfolio state for cash and long-only positions."""

from __future__ import annotations


class Portfolio:
    """Maintain cash and long-only symbol quantities."""

    CASH_SYMBOL = "CASH"
    CASH_TOLERANCE = 1e-8
    POSITION_TOLERANCE = 1e-12

    def __init__(self, cash: float = 0.0, positions: dict[str, float] | None = None) -> None:
        self.positions: dict[str, float] = {}
        self._cash = 0.0
        self.cash = cash

        for symbol, quantity in (positions or {}).items():
            self.set_position(symbol, quantity)

    @property
    def cash(self) -> float:
        return self._cash

    @cash.setter
    def cash(self, value: float) -> None:
        value = float(value)
        if value < -self.CASH_TOLERANCE:
            raise ValueError("cash cannot be negative")
        self._cash = 0.0 if value < 0 else value

    def get_position(self, symbol: str) -> float:
        return self.positions.get(symbol, 0.0)

    def set_position(self, symbol: str, quantity: float) -> None:
        if symbol == self.CASH_SYMBOL:
            return

        quantity = float(quantity)
        if quantity < -self.POSITION_TOLERANCE:
            raise ValueError("position quantity cannot be negative")

        if abs(quantity) <= self.POSITION_TOLERANCE:
            self.positions.pop(symbol, None)
            return

        self.positions[symbol] = quantity

    def update_position(self, symbol: str, delta_quantity: float) -> None:
        if symbol == self.CASH_SYMBOL:
            return

        new_quantity = self.get_position(symbol) + float(delta_quantity)
        self.set_position(symbol, new_quantity)

    def position_value(self, symbol: str, price: float) -> float:
        return self.get_position(symbol) * float(price)

    def total_position_value(self, price_map: dict[str, float]) -> float:
        total = 0.0
        for symbol, quantity in self.positions.items():
            if symbol not in price_map:
                raise ValueError(f"Missing price for symbol: {symbol}")
            total += quantity * float(price_map[symbol])
        return total

    def total_equity(self, price_map: dict[str, float]) -> float:
        return self.cash + self.total_position_value(price_map)
