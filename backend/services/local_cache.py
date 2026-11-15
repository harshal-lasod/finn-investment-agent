"""SQLite-backed TTL cache for API responses and source data."""
from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

from fastapi.encoders import jsonable_encoder

from backend.database import get_db

T = TypeVar("T")


async def get_local_cache(key: str) -> Any | None:
    now = time.time()
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT payload_json, expires_at FROM local_response_cache WHERE cache_key = ?",
            (key,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        if row["expires_at"] <= now:
            await db.execute("DELETE FROM local_response_cache WHERE cache_key = ?", (key,))
            await db.commit()
            return None
        return json.loads(row["payload_json"])


async def set_local_cache(key: str, value: Any, ttl_seconds: int) -> None:
    if ttl_seconds <= 0:
        return
    now = time.time()
    payload = json.dumps(jsonable_encoder(value), separators=(",", ":"), ensure_ascii=False)
    async with get_db() as db:
        await db.execute("DELETE FROM local_response_cache WHERE expires_at <= ?", (now,))
        await db.execute(
            """
            INSERT INTO local_response_cache (cache_key, payload_json, cached_at, expires_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                payload_json = excluded.payload_json,
                cached_at = excluded.cached_at,
                expires_at = excluded.expires_at
            """,
            (key, payload, now, now + ttl_seconds),
        )
        await db.commit()


def persistent_response_cache(
    namespace: str, ttl_seconds: int
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Cache an async endpoint's JSON response locally for a configured TTL."""
    def decorate(endpoint: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(endpoint)
        async def wrapped(*args: Any, **kwargs: Any) -> T:
            if ttl_seconds <= 0:
                return await endpoint(*args, **kwargs)
            request_data = json.dumps(
                jsonable_encoder({"args": args, "kwargs": kwargs}),
                sort_keys=True,
                separators=(",", ":"),
            )
            digest = hashlib.sha256(request_data.encode("utf-8")).hexdigest()
            key = f"api:{namespace}:{digest}"
            cached = await get_local_cache(key)
            if cached is not None:
                return cached
            result = await endpoint(*args, **kwargs)
            await set_local_cache(key, result, ttl_seconds)
            return result

        return wrapped

    return decorate
