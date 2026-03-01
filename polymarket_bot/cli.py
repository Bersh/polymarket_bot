from __future__ import annotations

import argparse
from datetime import datetime, timezone

from polymarket_bot.engine import run_backtest
from polymarket_bot.output import print_results
from polymarket_bot.strategies.base import StrategyConfig
from polymarket_bot.strategies.low_odds_contra import LowOddsContraStrategy


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="polymarket-bot",
        description="Backtest trading strategies on Polymarket historical data",
    )
    parser.add_argument(
        "--start",
        required=True,
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        required=True,
        help="End date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--bet",
        type=float,
        default=10.0,
        help="Bet amount in USD (default: 10)",
    )
    parser.add_argument(
        "--min-volume",
        type=float,
        default=1000,
        help="Minimum market volume in USD (default: 1000)",
    )
    parser.add_argument(
        "--strategy",
        default="low_odds_contra",
        choices=["low_odds_contra"],
        help="Strategy to backtest (default: low_odds_contra)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed progress and trade log",
    )
    return parser.parse_args(argv)


def _make_strategy(args: argparse.Namespace) -> LowOddsContraStrategy:
    config = StrategyConfig(
        bet_amount=args.bet,
        start_date=datetime.strptime(args.start, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        ),
        end_date=datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc),
    )
    if args.strategy == "low_odds_contra":
        return LowOddsContraStrategy(config)
    raise ValueError(f"Unknown strategy: {args.strategy}")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    strategy = _make_strategy(args)

    print(f"Strategy: {strategy.name}")
    print(f"Period:   {args.start} to {args.end}")
    print(f"Bet size: ${args.bet:.2f}")

    result = run_backtest(
        strategy=strategy,
        start_date=args.start,
        end_date=args.end,
        min_volume=args.min_volume,
        verbose=args.verbose,
    )

    print_results(result, verbose=args.verbose)
