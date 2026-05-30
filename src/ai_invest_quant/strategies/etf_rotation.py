"""ETF rotation strategy signal generation."""

from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = (
    "date",
    "symbol",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
    "ma60",
    "return_20d",
)


def generate_etf_rotation_signals(
    df: pd.DataFrame,
    rebalance_interval: int = 5,
    top_n: int = 3,
    target_exposure: float = 0.8,
) -> pd.DataFrame:
    """Generate ETF rotation target-weight signals.

    The strategy layer only outputs ETF target weights. If total ETF weight is
    below 1, the remaining exposure is left for a later portfolio/backtest layer
    to treat as cash. A row with symbol="CASH" and target_weight=1.0 is emitted
    only when no ETF is eligible for a signal date. CASH is not a real tradable
    symbol.

    Signals are calculated from the signal_date snapshot only. execute_date is
    the next market trading day and is not used for ranking or filtering.
    """
    _validate_inputs(df, rebalance_interval, top_n, target_exposure)

    data = df.copy()
    data["date"] = pd.to_datetime(data["date"], errors="raise")
    data = data.sort_values(["date", "symbol"], ascending=True, kind="mergesort")

    trading_dates = pd.Index(data["date"].drop_duplicates().sort_values())
    rows: list[dict[str, object]] = []

    for date_index in range(0, len(trading_dates), rebalance_interval):
        signal_date = trading_dates[date_index]
        if date_index + 1 >= len(trading_dates):
            continue

        execute_date = trading_dates[date_index + 1]
        snapshot = data[data["date"] == signal_date]
        selected = _select_symbols(snapshot, top_n)

        if selected.empty:
            rows.append(
                {
                    "signal_date": signal_date,
                    "execute_date": execute_date,
                    "symbol": "CASH",
                    "target_weight": 1.0,
                    "rank": None,
                    "close": pd.NA,
                    "ma60": pd.NA,
                    "return_20d": pd.NA,
                    "reason": "no_eligible_symbol",
                }
            )
            continue

        target_weight = target_exposure / len(selected)
        for rank, (_, item) in enumerate(selected.iterrows(), start=1):
            rows.append(
                {
                    "signal_date": signal_date,
                    "execute_date": execute_date,
                    "symbol": item["symbol"],
                    "target_weight": target_weight,
                    "rank": rank,
                    "close": item["close"],
                    "ma60": item["ma60"],
                    "return_20d": item["return_20d"],
                    "reason": "selected",
                }
            )

    return pd.DataFrame(
        rows,
        columns=[
            "signal_date",
            "execute_date",
            "symbol",
            "target_weight",
            "rank",
            "close",
            "ma60",
            "return_20d",
            "reason",
        ],
    ).reset_index(drop=True)


def _validate_inputs(
    df: pd.DataFrame,
    rebalance_interval: int,
    top_n: int,
    target_exposure: float,
) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    if rebalance_interval <= 0:
        raise ValueError("rebalance_interval must be > 0")

    if top_n <= 0:
        raise ValueError("top_n must be > 0")

    if target_exposure < 0 or target_exposure > 1:
        raise ValueError("target_exposure must be >= 0 and <= 1")


def _select_symbols(snapshot: pd.DataFrame, top_n: int) -> pd.DataFrame:
    eligible = snapshot[
        snapshot["ma60"].notna()
        & snapshot["return_20d"].notna()
        & (snapshot["close"] > snapshot["ma60"])
    ]
    return eligible.sort_values(
        ["return_20d", "symbol"],
        ascending=[False, True],
        kind="mergesort",
    ).head(top_n)
