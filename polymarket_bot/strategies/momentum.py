from __future__ import annotations

from polymarket_bot.models import Market, PricePoint, Trade
from polymarket_bot.strategies.base import Strategy, StrategyConfig


class MomentumStrategy(Strategy):
    """Trend-following via moving average crossover.

    Computes a fast and slow simple moving average of Yes prices.
    When the fast MA crosses above the slow MA, buy Yes (uptrend).
    When the fast MA crosses below the slow MA, buy No (downtrend).

    Rationale: information flows gradually into prediction markets,
    so sustained directional moves tend to continue toward resolution.
    """

    def __init__(
        self,
        config: StrategyConfig,
        fast_window: int = 10,
        slow_window: int = 30,
        min_trend_strength: float = 0.03,
    ) -> None:
        super().__init__(config)
        self.fast_window = fast_window
        self.slow_window = slow_window
        # Minimum gap between fast and slow MA to confirm trend
        self.min_trend_strength = min_trend_strength

    @property
    def name(self) -> str:
        return "momentum"

    def _sma(self, prices: list[float], window: int) -> float | None:
        if len(prices) < window:
            return None
        return sum(prices[-window:]) / window

    def evaluate(
        self,
        market: Market,
        price_history: list[PricePoint],
    ) -> Trade | None:
        prices_so_far: list[float] = []
        prev_fast: float | None = None
        prev_slow: float | None = None

        for point in price_history:
            if self.config.start_date and point.timestamp < self.config.start_date:
                prices_so_far.append(point.price)
                continue
            if self.config.end_date and point.timestamp > self.config.end_date:
                break

            prices_so_far.append(point.price)

            fast_ma = self._sma(prices_so_far, self.fast_window)
            slow_ma = self._sma(prices_so_far, self.slow_window)

            if fast_ma is None or slow_ma is None:
                prev_fast, prev_slow = fast_ma, slow_ma
                continue

            # Detect crossover (fast crosses above slow → bullish)
            if (
                prev_fast is not None
                and prev_slow is not None
                and prev_fast <= prev_slow
                and fast_ma > slow_ma
                and (fast_ma - slow_ma) >= self.min_trend_strength
            ):
                # Buy Yes — trend is up
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

            # Fast crosses below slow → bearish, buy No
            if (
                prev_fast is not None
                and prev_slow is not None
                and prev_fast >= prev_slow
                and fast_ma < slow_ma
                and (slow_ma - fast_ma) >= self.min_trend_strength
            ):
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

            prev_fast, prev_slow = fast_ma, slow_ma

        return None
