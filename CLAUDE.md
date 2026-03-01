# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Polymarket backtesting simulator that crawls historical data from Polymarket's public REST APIs and evaluates trading strategies over configurable date ranges. Designed for eventual extension to live trading.

## Commands

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Run backtester
python -m polymarket_bot --start 2024-10-01 --end 2024-12-31 --verbose
python -m polymarket_bot --start 2024-01-01 --end 2024-12-31 --bet 25 --min-volume 5000
```

No tests or linter configured yet.

## Architecture

```
CLI (cli.py) → engine.run_backtest() → results
                 ├── api/gamma.py   → fetch resolved markets (paginated)
                 ├── api/clob.py    → fetch price history per market
                 └── strategy.evaluate(market, prices) → Trade | None
```

**Data flow:** Gamma API returns resolved binary markets → Data API returns Yes trade prices for each (by condition ID) → Strategy scans prices for entry signals and calculates P&L from resolution outcome → Results aggregated into BacktestResult.

**Adding a new strategy:** Subclass `strategies/base.py:Strategy`, implement `name` property and `evaluate()` method (returns `Trade | None`), register the choice in `cli.py`'s argparse choices and `_make_strategy()`.

## API Gotchas

- Gamma API fields `outcomes`, `outcomePrices`, `clobTokenIds` are **JSON-encoded strings** — must `json.loads()` them.
- **CLOB `/prices-history` does NOT retain data for resolved markets.** Use Data API (`data-api.polymarket.com/trades`) instead — it's public, returns trades filterable by `market` (condition ID), and works for old resolved markets.
- Data API `/trades` params: `market` (condition ID), `limit` (max 10000), `offset`. Returns trades with `price`, `timestamp`, `outcome` ("Yes"/"No").
- All read-only APIs are unauthenticated. Auth (py-clob-client + private key) only needed for future live trading.
- Resolution: `outcomePrices = ["1", "0"]` means Yes won; `["0", "1"]` means No won.

## Key Model Relationships

- `Market.condition_id` is used to fetch trades from the Data API
- `PricePoint.price` is always the Yes trade price
- No price is derived as `1 - yes_price` in strategy code
- One trade per market maximum (strategies return on first signal)
