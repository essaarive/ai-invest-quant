"""Risk manager for target-weight clipping and drawdown state."""

from __future__ import annotations


class RiskManager:
    """Manage exposure limits and normal/defensive mode state."""

    NORMAL = "normal"
    DEFENSIVE = "defensive"
    CASH_SYMBOL = "CASH"

    def __init__(
        self,
        max_position_weight: float = 0.30,
        normal_max_exposure: float = 0.80,
        defensive_max_exposure: float = 0.30,
        defensive_drawdown: float = -0.12,
        recovery_drawdown: float = -0.06,
    ) -> None:
        self.max_position_weight = float(max_position_weight)
        self.normal_max_exposure = float(normal_max_exposure)
        self.defensive_max_exposure = float(defensive_max_exposure)
        self.defensive_drawdown = float(defensive_drawdown)
        self.recovery_drawdown = float(recovery_drawdown)
        self._validate_parameters()

        self.mode = self.NORMAL
        self.peak_equity = 0.0
        self.current_drawdown = 0.0

    def update_state(self, equity: float) -> None:
        """Update peak equity, current drawdown, and risk mode after close."""
        equity = float(equity)
        if equity <= 0:
            raise ValueError("equity must be > 0")

        self.peak_equity = max(self.peak_equity, equity)
        self.current_drawdown = equity / self.peak_equity - 1

        if self.mode == self.NORMAL and self.current_drawdown <= self.defensive_drawdown:
            self.mode = self.DEFENSIVE
        elif self.mode == self.DEFENSIVE and self.current_drawdown > self.recovery_drawdown:
            self.mode = self.NORMAL

    def apply_limits(self, target_weights: dict[str, float]) -> dict[str, float]:
        """Clip target weights by single-position and total-exposure limits."""
        clipped: dict[str, float] = {}
        for symbol, weight in target_weights.items():
            if symbol == self.CASH_SYMBOL:
                continue

            weight = float(weight)
            if weight < 0 or weight > 1:
                raise ValueError("target weight must be >= 0 and <= 1")

            clipped[symbol] = min(weight, self.max_position_weight)

        max_exposure = (
            self.defensive_max_exposure if self.mode == self.DEFENSIVE else self.normal_max_exposure
        )
        total_weight = sum(clipped.values())
        if total_weight > max_exposure and total_weight > 0:
            scale = max_exposure / total_weight
            clipped = {symbol: weight * scale for symbol, weight in clipped.items()}

        return clipped

    def _validate_parameters(self) -> None:
        for name in ("max_position_weight", "normal_max_exposure", "defensive_max_exposure"):
            value = getattr(self, name)
            if value < 0 or value > 1:
                raise ValueError(f"{name} must be >= 0 and <= 1")

        if self.defensive_max_exposure > self.normal_max_exposure:
            raise ValueError("defensive_max_exposure must be <= normal_max_exposure")

        if self.defensive_drawdown >= 0:
            raise ValueError("defensive_drawdown must be < 0")

        if self.recovery_drawdown >= 0:
            raise ValueError("recovery_drawdown must be < 0")

        if self.recovery_drawdown <= self.defensive_drawdown:
            raise ValueError("recovery_drawdown must be > defensive_drawdown")
