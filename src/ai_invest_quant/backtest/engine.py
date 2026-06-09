"""Basic portfolio backtest execution engine."""

from __future__ import annotations

import pandas as pd

from ai_invest_quant.backtest.broker import execute_trade
from ai_invest_quant.data.constants import OHLC_COLUMNS
from ai_invest_quant.portfolio.portfolio import Portfolio

PRICE_COLUMNS = ("date", "symbol", OHLC_COLUMNS[0], OHLC_COLUMNS[3])
SIGNAL_COLUMNS = ("signal_date", "execute_date", "symbol", "target_weight")


def run_backtest(
    price_df: pd.DataFrame,
    signals_df: pd.DataFrame,
    initial_cash: float = 1_000_000,
    fee_rate: float = 0.001,
    slippage: float = 0.0005,
    risk_manager=None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run a simple long-only rebalance simulation."""
    prices = _prepare_prices(price_df)
    signals = _prepare_signals(signals_df)
    portfolio = Portfolio(cash=initial_cash)

    nav_rows: list[dict[str, object]] = []
    trade_rows: list[dict[str, object]] = []
    position_rows: list[dict[str, object]] = []

    trading_dates = pd.Index(prices["date"].drop_duplicates().sort_values())
    signals_by_execute_date = {
        execute_date: group.reset_index(drop=True)
        for execute_date, group in signals.groupby("execute_date", sort=False)
    }

    peak_equity = 0.0

    for current_date in trading_dates:
        daily_prices = prices[prices["date"] == current_date]
        open_map = dict(zip(daily_prices["symbol"], daily_prices["open"], strict=True))
        close_map = dict(zip(daily_prices["symbol"], daily_prices["close"], strict=True))

        if current_date in signals_by_execute_date:
            target_weights = _target_weights_from_signals(signals_by_execute_date[current_date])
            if risk_manager is not None:
                target_weights = risk_manager.apply_limits(target_weights)

            trade_rows.extend(
                _rebalance(
                    portfolio=portfolio,
                    target_weights=target_weights,
                    open_map=open_map,
                    trade_date=current_date,
                    fee_rate=fee_rate,
                    slippage=slippage,
                )
            )

        positions_value = portfolio.total_position_value(close_map)
        equity = portfolio.cash + positions_value
        peak_equity = max(peak_equity, equity)
        drawdown = equity / peak_equity - 1 if peak_equity else 0.0
        if risk_manager is not None:
            risk_manager.update_state(equity)
            risk_mode = risk_manager.mode
            drawdown = risk_manager.current_drawdown
        else:
            risk_mode = None

        nav_rows.append(
            {
                "date": current_date,
                "cash": portfolio.cash,
                "positions_value": positions_value,
                "equity": equity,
                "nav": equity / initial_cash,
                "risk_mode": risk_mode,
                "drawdown": drawdown,
            }
        )

        for symbol, quantity in sorted(portfolio.positions.items()):
            close = _require_price(close_map, symbol, "close")
            market_value = quantity * close
            position_rows.append(
                {
                    "date": current_date,
                    "symbol": symbol,
                    "quantity": quantity,
                    "close": close,
                    "market_value": market_value,
                    "weight": market_value / equity if equity else 0.0,
                }
            )

    return (
        pd.DataFrame(
            nav_rows,
            columns=["date", "cash", "positions_value", "equity", "nav", "risk_mode", "drawdown"],
        ),
        pd.DataFrame(
            trade_rows,
            columns=[
                "trade_date",
                "symbol",
                "side",
                "quantity",
                "price",
                "trade_amount",
                "fee",
                "cash_after",
                "position_after",
            ],
        ),
        pd.DataFrame(
            position_rows,
            columns=["date", "symbol", "quantity", "close", "market_value", "weight"],
        ),
    )


def _prepare_prices(price_df: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in PRICE_COLUMNS if column not in price_df.columns]
    if missing:
        raise ValueError(f"Missing required price columns: {', '.join(missing)}")

    prices = price_df.copy()
    prices["date"] = pd.to_datetime(prices["date"], errors="raise")
    prices["open"] = pd.to_numeric(prices["open"], errors="raise")
    prices["close"] = pd.to_numeric(prices["close"], errors="raise")
    return prices.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)


def _prepare_signals(signals_df: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in SIGNAL_COLUMNS if column not in signals_df.columns]
    if missing:
        raise ValueError(f"Missing required signal columns: {', '.join(missing)}")

    signals = signals_df.copy()
    signals["signal_date"] = pd.to_datetime(signals["signal_date"], errors="raise")
    signals["execute_date"] = pd.to_datetime(signals["execute_date"], errors="raise")
    try:
        signals["target_weight"] = pd.to_numeric(signals["target_weight"], errors="raise")
    except Exception as exc:
        raise ValueError("target_weight must be numeric") from exc

    if ((signals["target_weight"] < 0) | (signals["target_weight"] > 1)).any():
        raise ValueError("target_weight must be >= 0 and <= 1")

    if signals.duplicated(["execute_date", "symbol"]).any():
        raise ValueError("duplicate execute_date + symbol signals are not allowed")

    for _execute_date, group in signals.groupby("execute_date", sort=False):
        has_cash = (group["symbol"] == Portfolio.CASH_SYMBOL).any()
        etf_group = group[group["symbol"] != Portfolio.CASH_SYMBOL]

        if has_cash and not etf_group.empty:
            raise ValueError("CASH and ETF signals cannot appear on the same execute_date")

        if etf_group["target_weight"].sum() > 1:
            raise ValueError("ETF target_weight sum cannot exceed 1 for the same execute_date")

        if has_cash and len(group) == 1 and float(group.iloc[0]["target_weight"]) != 1.0:
            raise ValueError("CASH signal target_weight must be 1.0")

    return signals.sort_values(["execute_date", "symbol"], kind="mergesort").reset_index(drop=True)


def _target_weights_from_signals(signals: pd.DataFrame) -> dict[str, float]:
    return {
        row.symbol: float(row.target_weight)
        for row in signals.itertuples(index=False)
        if row.symbol != Portfolio.CASH_SYMBOL
    }


def _rebalance(
    portfolio: Portfolio,
    target_weights: dict[str, float],
    open_map: dict[str, float],
    trade_date: pd.Timestamp,
    fee_rate: float,
    slippage: float,
) -> list[dict[str, object]]:
    symbols = set(portfolio.positions) | set(target_weights)
    equity_before_trade = portfolio.total_equity(open_map)
    target_quantities = {
        symbol: (equity_before_trade * target_weights.get(symbol, 0.0))
        / _require_price(open_map, symbol, "open")
        for symbol in symbols
    }

    trades: list[dict[str, object]] = []

    for symbol in sorted(symbols):
        current_quantity = portfolio.get_position(symbol)
        target_quantity = target_quantities[symbol]
        sell_quantity = current_quantity - target_quantity
        if sell_quantity > Portfolio.POSITION_TOLERANCE:
            trades.append(
                execute_trade(
                    portfolio=portfolio,
                    symbol=symbol,
                    side="sell",
                    quantity=sell_quantity,
                    open_price=_require_price(open_map, symbol, "open"),
                    fee_rate=fee_rate,
                    slippage=slippage,
                    trade_date=trade_date,
                )
            )

    for symbol in sorted(symbols):
        current_quantity = portfolio.get_position(symbol)
        target_quantity = target_quantities[symbol]
        buy_quantity = target_quantity - current_quantity
        if buy_quantity <= Portfolio.POSITION_TOLERANCE:
            continue

        open_price = _require_price(open_map, symbol, "open")
        buy_price = open_price * (1 + slippage)
        max_affordable_quantity = portfolio.cash / (buy_price * (1 + fee_rate))
        executable_quantity = min(buy_quantity, max_affordable_quantity)
        if executable_quantity <= Portfolio.POSITION_TOLERANCE:
            continue

        trades.append(
            execute_trade(
                portfolio=portfolio,
                symbol=symbol,
                side="buy",
                quantity=executable_quantity,
                open_price=open_price,
                fee_rate=fee_rate,
                slippage=slippage,
                trade_date=trade_date,
            )
        )

    return trades


def _require_price(price_map: dict[str, float], symbol: str, price_name: str) -> float:
    if symbol not in price_map:
        raise ValueError(f"Missing {price_name} price for symbol: {symbol}")
    price = float(price_map[symbol])
    if price <= 0:
        raise ValueError(f"{price_name} price must be > 0 for symbol: {symbol}")
    return price
