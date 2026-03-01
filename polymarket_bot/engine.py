from __future__ import annotations

import sys
from datetime import datetime

from polymarket_bot.api.clob import fetch_price_history
from polymarket_bot.api.gamma import fetch_resolved_markets
from polymarket_bot.models import BacktestResult
from polymarket_bot.strategies.base import Strategy


def run_backtest(
    strategy: Strategy,
    start_date: str,
    end_date: str,
    min_volume: float = 1000,
    verbose: bool = False,
) -> BacktestResult:
    """Run a backtest over resolved markets in the given date range."""
    result = BacktestResult()

    if verbose:
        print(f"Fetching resolved markets from {start_date} to {end_date}...")

    markets = fetch_resolved_markets(start_date, end_date, min_volume)
    result.markets_scanned = len(markets)

    if verbose:
        print(f"Found {len(markets)} resolved markets (min volume: ${min_volume:,.0f})")

    for i, market in enumerate(markets):
        if verbose:
            progress = f"[{i + 1}/{len(markets)}]"
            print(f"  {progress} {market.question[:70]}...", end=" ", flush=True)

        # Fetch Yes trade prices via Data API (by condition ID)
        try:
            price_history = fetch_price_history(market.condition_id)
        except Exception as e:
            if verbose:
                print(f"ERROR fetching prices: {e}", file=sys.stderr)
            continue

        if not price_history:
            if verbose:
                print("no price data")
            continue

        trade = strategy.evaluate(market, price_history)
        if trade:
            result.trades.append(trade)
            if verbose:
                status = "WIN" if trade.won else "LOSS"
                print(f"{status} (${trade.profit:+.2f})")
        elif verbose:
            print("no signal")

    return result
