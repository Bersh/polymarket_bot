from __future__ import annotations

import sys

from polymarket_bot.api.clob import fetch_price_history
from polymarket_bot.api.gamma import fetch_resolved_markets
from polymarket_bot import cache
from polymarket_bot.models import BacktestResult, PricePoint
from polymarket_bot.strategies.base import Strategy


def run_backtest(
    strategy: Strategy,
    start_date: str,
    end_date: str,
    min_volume: float = 1000,
    verbose: bool = False,
    use_cache: bool = True,
) -> BacktestResult:
    """Run a backtest over resolved markets in the given date range."""
    result = BacktestResult()

    # 1. Load or fetch markets
    markets = None
    if use_cache:
        markets = cache.load_markets(start_date, end_date, min_volume)
        if markets is not None:
            print(f"Loaded {len(markets)} markets from cache")

    if markets is None:
        print(f"Fetching resolved markets from {start_date} to {end_date}...")
        markets = fetch_resolved_markets(start_date, end_date, min_volume)
        print(f"Found {len(markets)} resolved markets (min volume: ${min_volume:,.0f})")
        if use_cache:
            cache.save_markets(start_date, end_date, min_volume, markets)

    result.markets_scanned = len(markets)

    # 2. Evaluate each market
    for i, market in enumerate(markets):
        progress = f"[{i + 1}/{len(markets)}]"

        # Load or fetch price history (per-market cache)
        price_history: list[PricePoint] | None = None
        from_cache = False

        if use_cache:
            price_history = cache.load_prices(market.condition_id)
            if price_history is not None:
                from_cache = True

        if price_history is None:
            if verbose:
                print(f"  {progress} fetching {market.question[:60]}...", end=" ", flush=True)
            try:
                history = fetch_price_history(market.condition_id)
            except Exception as e:
                if verbose:
                    print(f"ERROR: {e}", file=sys.stderr)
                continue

            if not history:
                if verbose:
                    print("no data")
                continue

            price_history = history
            if use_cache:
                cache.save_prices(market.condition_id, price_history)

            if verbose:
                print(f"{len(price_history)} trades")
        elif verbose:
            print(f"  {progress} {market.question[:60]}... (cached)")

        trade = strategy.evaluate(market, price_history)
        if trade:
            result.trades.append(trade)
            if verbose:
                status = "WIN" if trade.won else "LOSS"
                print(f"    → {status} (${trade.profit:+.2f})")

        # Non-verbose progress for slow API fetches
        if not verbose and not from_cache and (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(markets)} markets...")

    return result
