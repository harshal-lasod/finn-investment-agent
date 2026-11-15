"""Local search for exchange-listed equity symbols."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

SYMBOLS_PATH = Path(__file__).resolve().parents[1] / "data" / "exchange_symbols.json"


@lru_cache(maxsize=1)
def load_symbols() -> tuple[dict[str, str], ...]:
    if not SYMBOLS_PATH.exists():
        return ()
    with SYMBOLS_PATH.open(encoding="utf-8") as symbols_file:
        rows: list[dict[str, Any]] = json.load(symbols_file)
    return tuple(
        {
            "symbol": str(row["symbol"]).strip().upper(),
            "name": str(row["name"]).strip(),
            "exchange": str(row["exchange"]).strip().upper(),
            "isin": str(row.get("isin") or "").strip(),
            "series": str(row.get("series") or "").strip().upper(),
        }
        for row in rows
        if row.get("symbol") and row.get("name") and row.get("exchange")
    )


def search_symbols(query: str, limit: int = 10) -> list[dict[str, str]]:
    needle = query.strip().casefold()
    if not needle:
        return []

    def rank(row: dict[str, str]) -> tuple[int, str, str]:
        symbol = row["symbol"].casefold()
        name = row["name"].casefold()
        if symbol == needle:
            priority = 0
        elif symbol.startswith(needle):
            priority = 1
        elif any(word.startswith(needle) for word in name.split()):
            priority = 2
        elif needle in name:
            priority = 3
        else:
            priority = 4
        return priority, symbol, row["exchange"]

    matches = [
        row for row in load_symbols()
        if needle in row["symbol"].casefold() or needle in row["name"].casefold()
    ]
    return sorted(matches, key=rank)[:limit]
