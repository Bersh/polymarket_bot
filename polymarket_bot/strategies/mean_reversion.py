from __future__ import annotations

import math

from polymarket_bot.models import Market, PricePoint, Trade
from polymarket_bot.strategies.base import Strategy, StrategyConfig

# TODO very good strategy
class MeanReversionStrategy(Strategy):
    """Buy the dip — enter when price deviates sharply from its rolling mean.

    Computes a rolling mean and standard deviation of Yes prices.
    When the current price drops more than `z_threshold` standard deviations
    below the mean, buy Yes (oversold). When it rises above, buy No (overbought).

    Rationale: prediction markets overreact to short-term noise. Prices
    that diverge sharply from their recent average tend to snap back,
    especially in higher-volume markets where consensus is stronger.
    """

    def __init__(
        self,
        config: StrategyConfig,
        window: int = 25,
        z_threshold: float = 2.0,
    ) -> None:
        super().__init__(config)
        self.window = window
        self.z_threshold = z_threshold

    @property
    def name(self) -> str:
        return "mean_reversion"

    def _rolling_stats(
        self, prices: list[float], window: int
    ) -> tuple[float, float] | None:
        if len(prices) < window:
            return None
        recent = prices[-window:]
        mean = sum(recent) / window
        variance = sum((p - mean) ** 2 for p in recent) / window
        std = math.sqrt(variance)
        return mean, std

    def evaluate(
        self,
        market: Market,
        price_history: list[PricePoint],
    ) -> Trade | None:
        prices_so_far: list[float] = []

        for point in price_history:
            if self.config.start_date and point.timestamp < self.config.start_date:
                prices_so_far.append(point.price)
                continue
            if self.config.end_date and point.timestamp > self.config.end_date:
                break

            prices_so_far.append(point.price)

            stats = self._rolling_stats(prices_so_far, self.window)
            if stats is None:
                continue

            mean, std = stats
            if std < 0.01:
                # Flat market, no meaningful deviation
                continue

            z_score = (point.price - mean) / std

            # Oversold: price dropped well below average → buy Yes
            if z_score <= -self.z_threshold:
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

            # Overbought: price spiked well above average → buy No
            if z_score >= self.z_threshold:
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
