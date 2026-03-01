from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PricePoint:
    timestamp: datetime
    price: float


@dataclass
class Market:
    id: str
    question: str
    slug: str
    end_date: datetime
    volume: float
    outcome_prices: list[float]
    clob_token_ids: list[str]
    outcomes: list[str]
    condition_id: str = ""

    @property
    def yes_won(self) -> bool:
        return self.outcome_prices[0] == 1.0

    @property
    def no_won(self) -> bool:
        return self.outcome_prices[1] == 1.0


@dataclass
class Trade:
    market: Market
    entry_price_yes: float
    entry_price_no: float
    shares: float
    bet_amount: float
    profit: float
    entry_time: datetime
    side: str = "No"

    @property
    def won(self) -> bool:
        return self.profit > 0


@dataclass
class BacktestResult:
    trades: list[Trade] = field(default_factory=list)
    markets_scanned: int = 0

    @property
    def total_profit(self) -> float:
        return sum(t.profit for t in self.trades)

    @property
    def total_wagered(self) -> float:
        return sum(t.bet_amount for t in self.trades)

    @property
    def roi(self) -> float:
        if self.total_wagered == 0:
            return 0.0
        return self.total_profit / self.total_wagered * 100

    @property
    def win_rate(self) -> float:
        if not self.trades:
            return 0.0
        return sum(1 for t in self.trades if t.won) / len(self.trades) * 100

    @property
    def wins(self) -> int:
        return sum(1 for t in self.trades if t.won)

    @property
    def losses(self) -> int:
        return sum(1 for t in self.trades if not t.won)
