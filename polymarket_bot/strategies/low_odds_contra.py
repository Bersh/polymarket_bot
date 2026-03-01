from __future__ import annotations

from polymarket_bot.models import Market, PricePoint, Trade
from polymarket_bot.strategies.base import Strategy, StrategyConfig


class LowOddsContraStrategy(Strategy):
    """Buy 'No' when 'Yes' price is between 10-15%.

    Rationale: markets with low 'Yes' probability are likely to resolve 'No',
    so buying 'No' at $0.85-$0.90 yields a small but frequent profit.
    """

    def __init__(
        self,
        config: StrategyConfig,
        yes_min: float = 0.10,
        yes_max: float = 0.15,
    ) -> None:
        super().__init__(config)
        self.yes_min = yes_min
        self.yes_max = yes_max

    @property
    def name(self) -> str:
        return "low_odds_contra"

    def evaluate(
        self,
        market: Market,
        price_history: list[PricePoint],
    ) -> Trade | None:
        for point in price_history:
            # Only consider points within our backtest window
            if self.config.start_date and point.timestamp < self.config.start_date:
                continue
            if self.config.end_date and point.timestamp > self.config.end_date:
                continue

            if self.yes_min <= point.price <= self.yes_max:
                no_price = 1.0 - point.price
                shares = self.config.bet_amount / no_price

                if market.no_won:
                    profit = shares * 1.0 - self.config.bet_amount
                else:
                    profit = -self.config.bet_amount

                return Trade(
                    market=market,
                    entry_price_yes=point.price,
                    entry_price_no=no_price,
                    shares=shares,
                    bet_amount=self.config.bet_amount,
                    profit=profit,
                    entry_time=point.timestamp,
                    side="No",
                )

        return None
