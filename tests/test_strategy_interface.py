from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from ai_invest_quant.strategies.base import Strategy, StrategyMetadata
from ai_invest_quant.strategies.etf_rotation import (
    ETFRotationStrategy,
    generate_etf_rotation_signals,
)


def make_strategy_input() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=6)
    rows = []
    returns = {"ETF_A": 0.3, "ETF_B": 0.2, "ETF_C": 0.1}
    for date in dates:
        for symbol, return_20d in returns.items():
            rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.0,
                    "volume": 1000,
                    "amount": 100000,
                    "ma60": 90.0,
                    "return_20d": return_20d,
                }
            )
    return pd.DataFrame(rows)


def test_strategy_metadata_can_be_created():
    metadata = StrategyMetadata(
        name="Example Strategy",
        version="0.1.0",
        description="Example strategy metadata.",
    )

    assert metadata.name == "Example Strategy"
    assert metadata.version == "0.1.0"
    assert metadata.description == "Example strategy metadata."


def test_strategy_metadata_is_frozen():
    metadata = StrategyMetadata(
        name="Example Strategy",
        version="0.1.0",
        description="Example strategy metadata.",
    )

    with pytest.raises(FrozenInstanceError):
        metadata.name = "Changed"


def test_etf_rotation_strategy_has_metadata():
    strategy = ETFRotationStrategy()

    assert strategy.metadata.name == "ETF Rotation Strategy"
    assert strategy.metadata.version == "1.0.0"


def test_etf_rotation_strategy_generate_signals_returns_dataframe():
    strategy = ETFRotationStrategy()

    result = strategy.generate_signals(make_strategy_input())

    assert isinstance(result, pd.DataFrame)
    assert not result.empty


def test_etf_rotation_strategy_matches_function_output():
    df = make_strategy_input()
    strategy = ETFRotationStrategy(rebalance_interval=5, top_n=2, target_exposure=0.6)

    class_result = strategy.generate_signals(df)
    function_result = generate_etf_rotation_signals(
        df,
        rebalance_interval=5,
        top_n=2,
        target_exposure=0.6,
    )

    pd.testing.assert_frame_equal(class_result, function_result)


def test_etf_rotation_strategy_satisfies_strategy_protocol():
    def run_strategy(strategy: Strategy, price_df: pd.DataFrame) -> pd.DataFrame:
        return strategy.generate_signals(price_df)

    result = run_strategy(ETFRotationStrategy(), make_strategy_input())

    assert isinstance(result, pd.DataFrame)
    assert result["symbol"].tolist()[:3] == ["ETF_A", "ETF_B", "ETF_C"]
