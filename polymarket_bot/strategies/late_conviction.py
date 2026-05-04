from __future__ import annotations

from datetime import timedelta

from polymarket_bot.models import Market, PricePoint, Trade
from polymarket_bot.strategies.base import Strategy, StrategyConfig


class LateConvictionStrategy(Strategy):
    """Buy the dominant side close to market expiry.

    Only considers trades within the last `days_before_close` days before the
    market's end date. If the Yes price is above `conviction_threshold`,
    buy Yes. If below `1 - conviction_threshold`, buy No.

    Rationale: markets that are strongly priced in one direction near
    resolution rarely flip. Buying at 0.90 yields a safe 11% return.
    Lower payout per trade, but very high win rate.
    """

    def __init__(
        self,
        config: StrategyConfig,
        days_before_close: int = 5,
        conviction_threshold: float = 0.90,
    ) -> None:
        super().__init__(config)
        self.days_before_close = days_before_close
        self.conviction_threshold = conviction_threshold

    @property
    def name(self) -> str:
        return "late_conviction"

    def evaluate(
        self,
        market: Market,
        price_history: list[PricePoint],
    ) -> Trade | None:
        cutoff = market.end_date - timedelta(days=self.days_before_close)

        for point in price_history:
            if self.config.start_date and point.timestamp < self.config.start_date:
                continue
            if self.config.end_date and point.timestamp > self.config.end_date:
                continue

            # Only look at trades near market close
            if point.timestamp < cutoff:
                continue

            # Strong Yes conviction
            if point.price >= self.conviction_threshold:
                shares = self.config.bet_amount / point.price
                if market.yes_won:
                    profit = shares * 1.0 - self.config.bet_amount
                else:
                    profit = -self.config.bet_amount

                return Trade(
                    market=market,
                    entry_price_yes=point.price,
                    entry_price_no=1.0 - point.price,
                    shares=shares,
                    bet_amount=self.config.bet_amount,
                    profit=profit,
                    entry_time=point.timestamp,
                    side="Yes",
                )

            # Strong No conviction (Yes price very low)
            if point.price <= (1.0 - self.conviction_threshold):
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
