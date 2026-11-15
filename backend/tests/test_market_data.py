from datetime import datetime

import pandas as pd

from backend.services.market_data import MarketDataService
from backend.services import market_data


def test_deterministic_market_metrics() -> None:
    assert MarketDataService.compute_volume_multiple(3_000, 1_000) == 3.0
    assert MarketDataService.compute_volume_multiple(1, 0) == 1.0
    assert MarketDataService.compute_price_change_pct(105, 100) == 5.0
    assert MarketDataService.compute_price_change_pct(10, 0) == 0.0


def test_technical_indicators_are_computed_from_history() -> None:
    close = [float(value) for value in range(1, 221)]
    history = pd.DataFrame({
        "Close": close,
        "High": [value + 1 for value in close],
        "Low": [value - 1 for value in close],
        "Volume": [1000] * len(close),
    }, index=pd.date_range("2026-01-01", periods=len(close)))
    indicators = MarketDataService.calculate_technicals(history)
    assert indicators["sma_20"] == 210.5
    assert indicators["sma_50"] == 195.5
    assert indicators["sma_200"] == 120.5
    assert indicators["rsi_14"] == 100
    assert indicators["latest_close"] == 220
    assert indicators["atr_14"] == 2


def test_yahoo_snapshot_parser_maps_bars_and_statements(monkeypatch) -> None:
    close = [float(value) for value in range(1, 221)]
    history = pd.DataFrame({
        "Close": close,
        "High": [value + 1 for value in close],
        "Low": [value - 1 for value in close],
        "Volume": [1000] * len(close),
    }, index=pd.date_range("2026-01-01", periods=len(close)))
    period = datetime(2026, 3, 31)

    class FakeTicker:
        def get_info(self):
            return {"currency": "INR", "financialCurrency": "INR", "trailingPE": 20, "marketCap": 1_000_000_000}

        income_stmt = pd.DataFrame(
            {"2026-03-31": [500.0, 100.0, 120.0, 70.0]},
            index=["Total Revenue", "Operating Income", "EBITDA", "Net Income"],
        )
        balance_sheet = pd.DataFrame(
            {"2026-03-31": [900.0, 100.0]},
            index=["Total Assets", "Total Debt"],
        )
        cashflow = pd.DataFrame(
            {"2026-03-31": [80.0, -20.0]},
            index=["Operating Cash Flow", "Capital Expenditure"],
        )

        def history(self, **kwargs):
            return history

    import yfinance

    monkeypatch.setattr(yfinance, "Ticker", lambda _: FakeTicker())
    snapshot = MarketDataService._fetch_snapshot("DEMO")
    assert snapshot is not None
    assert snapshot["quote"]["current_price"] == 220
    assert snapshot["technicals"]["sma_20"] == 210.5
    assert len(snapshot["price_history"]) == 220
    assert snapshot["price_history"][-1]["close"] == 220
    assert snapshot["currency"] == "INR"
    assert snapshot["financial_currency"] == "INR"
    assert snapshot["quote"]["market_cap_cr"] == 100
    assert snapshot["fundamentals"]["income_statement"]["revenue"] == 500
    assert snapshot["fundamentals"]["income_statement"]["period"] == period.date().isoformat()


def test_live_snapshot_persists_statements_with_long_ttl(monkeypatch) -> None:
    service = MarketDataService()
    persisted = []
    snapshot = {
        "ticker": "DEMO",
        "fundamentals": {"income_statement": {"revenue": 123}},
    }

    async def no_cache(_key):
        return None

    async def record_cache(key, value, ttl):
        persisted.append((key, value, ttl))

    def fake_fetch(_ticker, _cached_fundamentals):
        return snapshot

    monkeypatch.setattr(market_data, "get_local_cache", no_cache)
    monkeypatch.setattr(market_data, "set_local_cache", record_cache)
    monkeypatch.setattr(service, "_fetch_snapshot", fake_fetch)

    import asyncio

    result = asyncio.run(service.get_live_snapshot("DEMO"))
    assert result == snapshot
    fundamentals_entry = next(item for item in persisted if item[0] == "yahoo_fundamentals:DEMO")
    assert fundamentals_entry[1] == snapshot["fundamentals"]
    assert fundamentals_entry[2] == 30 * 24 * 60 * 60
