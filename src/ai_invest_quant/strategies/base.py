"""Lightweight strategy interface definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pandas as pd


@dataclass(frozen=True)
class StrategyMetadata:
    """Static metadata describing a strategy implementation."""

    name: str
    version: str
    description: str


class Strategy(Protocol):
    """Protocol for strategy implementations that generate target-weight signals."""

    metadata: StrategyMetadata

    def generate_signals(self, price_df: pd.DataFrame) -> pd.DataFrame:
        """Generate strategy signals from prepared market data."""
        ...
