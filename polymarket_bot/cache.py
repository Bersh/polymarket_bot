from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from polymarket_bot.models import Market, PricePoint

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
MARKETS_DIR = CACHE_DIR / "markets"
PRICES_DIR = CACHE_DIR / "prices"


# ── Market list cache (keyed by query params) ──────────────────────


def _markets_cache_path(start_date: str, end_date: str, min_volume: float) -> Path:
    raw = f"{start_date}_{end_date}_{min_volume}"
    key = hashlib.md5(raw.encode()).hexdigest()
    return MARKETS_DIR / f"{key}.json"


def save_markets(
    start_date: str,
    end_date: str,
    min_volume: float,
    markets: list[Market],
) -> None:
    MARKETS_DIR.mkdir(parents=True, exist_ok=True)
    data = [_serialize_market(m) for m in markets]
    path = _markets_cache_path(start_date, end_date, min_volume)
    path.write_text(json.dumps(data), encoding="utf-8")


def load_markets(
    start_date: str,
    end_date: str,
    min_volume: float,
) -> list[Market] | None:
    path = _markets_cache_path(start_date, end_date, min_volume)
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [_deserialize_market(m) for m in raw]


# ── Price history cache (keyed by condition_id) ─────────────────────


def _prices_cache_path(condition_id: str) -> Path:
    return PRICES_DIR / f"{condition_id}.json"


def save_prices(condition_id: str, points: list[PricePoint]) -> None:
    PRICES_DIR.mkdir(parents=True, exist_ok=True)
    data = [_serialize_price_point(p) for p in points]
    path = _prices_cache_path(condition_id)
    path.write_text(json.dumps(data), encoding="utf-8")


def load_prices(condition_id: str) -> list[PricePoint] | None:
    path = _prices_cache_path(condition_id)
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [_deserialize_price_point(p) for p in raw]


# ── Serialization helpers ───────────────────────────────────────────


def _serialize_market(m: Market) -> dict:
    return {
        "id": m.id,
        "question": m.question,
        "slug": m.slug,
        "end_date": m.end_date.isoformat(),
        "volume": m.volume,
        "outcome_prices": m.outcome_prices,
        "clob_token_ids": m.clob_token_ids,
        "outcomes": m.outcomes,
        "condition_id": m.condition_id,
    }


def _deserialize_market(d: dict) -> Market:
    return Market(
        id=d["id"],
        question=d["question"],
        slug=d["slug"],
        end_date=datetime.fromisoformat(d["end_date"]),
        volume=d["volume"],
        outcome_prices=d["outcome_prices"],
        clob_token_ids=d["clob_token_ids"],
        outcomes=d["outcomes"],
        condition_id=d["condition_id"],
    )


def _serialize_price_point(p: PricePoint) -> dict:
    return {"timestamp": p.timestamp.isoformat(), "price": p.price}


def _deserialize_price_point(d: dict) -> PricePoint:
    return PricePoint(
        timestamp=datetime.fromisoformat(d["timestamp"]),
        price=d["price"],
    )
