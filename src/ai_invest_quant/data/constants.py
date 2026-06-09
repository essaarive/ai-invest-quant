"""Shared column constants for standardized market data."""

# Tuples keep the standard schema definitions immutable across modules.
BASE_PRICE_COLUMNS = (
    "date",
    "symbol",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
)

OHLC_COLUMNS = (
    "open",
    "high",
    "low",
    "close",
)

VOLUME_AMOUNT_COLUMNS = (
    "volume",
    "amount",
)

PRICE_NUMERIC_COLUMNS = (
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
)
