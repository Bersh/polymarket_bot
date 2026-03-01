from __future__ import annotations

from polymarket_bot.models import BacktestResult


def print_results(result: BacktestResult, verbose: bool = False) -> None:
    """Print formatted backtest results."""
    print()
    print("=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)
    print(f"  Markets scanned:  {result.markets_scanned}")
    print(f"  Trades taken:     {len(result.trades)}")
    print(f"  Wins / Losses:    {result.wins} / {result.losses}")
    print(f"  Win rate:         {result.win_rate:.1f}%")
    print(f"  Total wagered:    ${result.total_wagered:,.2f}")
    print(f"  Total P&L:        ${result.total_profit:+,.2f}")
    print(f"  ROI:              {result.roi:+.1f}%")
    print("=" * 60)

    if verbose and result.trades:
        print()
        print("TRADE LOG")
        print("-" * 60)
        for i, trade in enumerate(result.trades, 1):
            status = "WIN " if trade.won else "LOSS"
            print(
                f"  {i:3d}. [{status}] {trade.market.question[:45]:<45s}"
                f"  Yes@{trade.entry_price_yes:.2f}  ${trade.profit:+.2f}"
            )
        print("-" * 60)
