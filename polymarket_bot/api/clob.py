from __future__ import annotations

from datetime import datetime, timezone

import requests

from polymarket_bot.models import PricePoint

DATA_API_URL = "https://data-api.polymarket.com/trades"
PAGE_SIZE = 10000


def fetch_price_history(condition_id: str) -> list[PricePoint]:
    """Fetch trade prices for a market from the Data API.

    The CLOB /prices-history endpoint does not retain data for resolved markets.
    Instead, we use the public Data API /trades endpoint which returns individual
    trades with prices, filterable by condition ID.
    """
    points: list[PricePoint] = []
    offset = 0

    while True:
        params = {
            "market": condition_id,
            "limit": PAGE_SIZE,
            "offset": offset,
        }
        resp = requests.get(DATA_API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if not data:
            break

        for trade in data:
            outcome = trade.get("outcome", "")
            if outcome != "Yes":
                continue
            try:
                ts_raw = trade.get("timestamp", 0)
                price = float(trade.get("price", 0))
                if isinstance(ts_raw, (int, float)):
                    ts = datetime.fromtimestamp(ts_raw, tz=timezone.utc)
                else:
                    ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
                points.append(PricePoint(timestamp=ts, price=price))
            except (ValueError, TypeError):
                continue

        if len(data) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    points.sort(key=lambda p: p.timestamp)
    return points
