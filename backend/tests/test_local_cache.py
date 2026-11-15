import asyncio

from backend.database import init_db
from backend.services.local_cache import (
    get_local_cache,
    persistent_response_cache,
    set_local_cache,
)


def test_persistent_response_cache_reuses_sqlite_value() -> None:
    calls = 0

    @persistent_response_cache("test-endpoint", 60)
    async def endpoint(value: str) -> dict[str, str]:
        nonlocal calls
        calls += 1
        return {"value": value}

    async def run() -> None:
        await init_db()
        assert await endpoint("cached") == {"value": "cached"}
        assert await endpoint("cached") == {"value": "cached"}
        await set_local_cache("expired", {"value": "old"}, -1)
        assert await get_local_cache("expired") is None

    asyncio.run(run())
    assert calls == 1


def test_local_cache_removes_expired_values() -> None:
    async def run() -> None:
        await init_db()
        await set_local_cache("expires-now", {"value": "old"}, 60)
        from backend.database import get_db

        async with get_db() as db:
            await db.execute(
                "UPDATE local_response_cache SET expires_at = 0 WHERE cache_key = ?",
                ("expires-now",),
            )
            await db.commit()
        assert await get_local_cache("expires-now") is None

    asyncio.run(run())
