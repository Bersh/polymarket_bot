from __future__ import annotations

import math

from polymarket_bot.models import Market, PricePoint, Trade
from polymarket_bot.strategies.base import Strategy, StrategyConfig


class VolatilityBreakoutStrategy(Strategy):
    """Enter when price breaks out of a low-volatility consolidation range.

    Tracks rolling volatility (standard deviation). When volatility over the
    lookback window is below `calm_threshold` (market in consensus) and the
    current price moves beyond the recent range by `breakout_multiple` times
    the std dev, enter in the direction of the breakout.

    Rationale: after periods of stability, a decisive price move typically
    signals new high-quality information. The market is re-pricing and
    the breakout direction tends to predict resolution.
    """

    def __init__(
        self,
        config: StrategyConfig,
        lookback: int = 20,
        calm_threshold: float = 0.03,
        breakout_multiple: float = 3.0,
    ) -> None:
        super().__init__(config)
        self.lookback = lookback
        # Max std dev to consider the market "calm"
        self.calm_threshold = calm_threshold
        # How many std devs the price must move to trigger
        self.breakout_multiple = breakout_multiple

    @property
    def name(self) -> str:
        return "volatility_breakout"

    def evaluate(
        self,
        market: Market,
        price_history: list[PricePoint],
    ) -> Trade | None:
        prices_so_far: list[float] = []
        was_calm = False
        calm_mean: float = 0.0
        calm_std: float = 0.0

        for point in price_history:
            if self.config.start_date and point.timestamp < self.config.start_date:
                prices_so_far.append(point.price)
                continue
            if self.config.end_date and point.timestamp > self.config.end_date:
                break

            prices_so_far.append(point.price)

            if len(prices_so_far) < self.lookback:
                continue

            window = prices_so_far[-self.lookback :]
            mean = sum(window) / self.lookback
            variance = sum((p - mean) ** 2 for p in window) / self.lookback
            std = math.sqrt(variance)

            if std <= self.calm_threshold:
                # Market is calm — remember this state for breakout detection
                was_calm = True
                calm_mean = mean
                calm_std = max(std, 0.005)  # floor to avoid division issues
                continue

            # If we were just in a calm period and now volatility increased,
            # check if current price broke out
            if was_calm:
                deviation = point.price - calm_mean

                if deviation > calm_std * self.breakout_multiple:
                    # Upside breakout → buy Yes
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

                if deviation < -(calm_std * self.breakout_multiple):
                    # Downside breakout → buy No
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

                # Volatility rose but no clear directional breakout — reset
                was_calm = False

        return None
