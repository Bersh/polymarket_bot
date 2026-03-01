from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from polymarket_bot.models import Market, PricePoint, Trade


@dataclass
class StrategyConfig:
    bet_amount: float = 10.0
    start_date: datetime | None = None
    end_date: datetime | None = None


class Strategy(ABC):
    def __init__(self, config: StrategyConfig) -> None:
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def evaluate(
        self,
        market: Market,
        price_history: list[PricePoint],
    ) -> Trade | None:
        """Evaluate whether to take a trade on this market.

        Returns a Trade if the strategy triggers, None otherwise.
        """
        ...
