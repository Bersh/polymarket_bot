from __future__ import annotations

import json
from datetime import datetime

import requests

from polymarket_bot.models import Market

GAMMA_API_URL = "https://gamma-api.polymarket.com/markets"
PAGE_SIZE = 100


def fetch_resolved_markets(
    start_date: str,
    end_date: str,
    min_volume: float = 1000,
) -> list[Market]:
    """Fetch all resolved binary markets in the given date range."""
    markets: list[Market] = []
    offset = 0

    while True:
        params = {
            "closed": "true",
            "end_date_min": start_date,
            "end_date_max": end_date,
            "limit": PAGE_SIZE,
            "offset": offset,
        }
        resp = requests.get(GAMMA_API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if not data:
            break

        for raw in data:
            market = _parse_market(raw)
            if market is None:
                continue
            if market.volume < min_volume:
                continue
            markets.append(market)

        if len(data) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    return markets


def _parse_market(raw: dict) -> Market | None:
    """Parse a raw Gamma API market dict into a Market, or None if invalid."""
    try:
        outcomes = json.loads(raw.get("outcomes", "[]"))
        outcome_prices = json.loads(raw.get("outcomePrices", "[]"))
        clob_token_ids = json.loads(raw.get("clobTokenIds", "[]"))
    except (json.JSONDecodeError, TypeError):
        return None

    # Only binary Yes/No markets
    if outcomes != ["Yes", "No"]:
        return None

    if len(outcome_prices) != 2 or len(clob_token_ids) != 2:
        return None

    # Must be fully resolved (one outcome = 1, other = 0)
    try:
        prices = [float(p) for p in outcome_prices]
    except (ValueError, TypeError):
        return None

    if sorted(prices) != [0.0, 1.0]:
        return None

    end_date_str = raw.get("endDate", "")
    if not end_date_str:
        return None

    try:
        end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
    except ValueError:
        return None

    volume = float(raw.get("volume", 0) or 0)

    return Market(
        id=raw.get("id", ""),
        question=raw.get("question", ""),
        slug=raw.get("slug", ""),
        end_date=end_date,
        volume=volume,
        outcome_prices=prices,
        clob_token_ids=clob_token_ids,
        outcomes=outcomes,
        condition_id=raw.get("conditionId", ""),
    )
