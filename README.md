# polymarket_bot

Backtesting simulator for Polymarket trading strategies. Crawls historical trade data from Polymarket APIs and evaluates strategies over configurable date ranges.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
python -m polymarket_bot --start 2024-06-01 --end 2024-12-31 --verbose
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--start` | (required) | Start date `YYYY-MM-DD` |
| `--end` | (required) | End date `YYYY-MM-DD` |
| `--bet` | 10 | Bet amount in USD |
| `--min-volume` | 1000 | Minimum market volume filter |
| `--strategy` | `low_odds_contra` | Strategy to run |
| `--verbose` | off | Per-market progress + trade log |

### Examples

```bash
# Quick test — narrow window
python -m polymarket_bot --start 2024-11-01 --end 2024-12-31 --verbose

# Wider range, larger bets, higher volume filter
python -m polymarket_bot --start 2024-01-01 --end 2024-12-31 --bet 25 --min-volume 5000 --verbose
```

## Strategy: low_odds_contra

Buys "No" shares when a market's "Yes" price is between 10–15%. Rationale: events with low implied probability usually resolve "No", yielding small but frequent profits.

- Entry: first time Yes price is in [0.10, 0.15] within the backtest window
- Position: `$bet / no_price` shares (e.g. $10 / $0.87 = 11.49 shares)
- If No wins: profit = shares × $1 − $bet
- If Yes wins: loss = −$bet
- One trade per market max
