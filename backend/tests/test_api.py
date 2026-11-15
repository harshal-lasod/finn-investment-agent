from fastapi.testclient import TestClient

from backend.config import settings
from backend.main import app
from backend.services.market_data import market_data_service


def test_portfolio_and_research_support_demo_tickers() -> None:
    with TestClient(app) as client:
        portfolio = client.get("/api/portfolio")
        assert portfolio.status_code == 200
        assert portfolio.json()["total_count"] == 20
        assert portfolio.json()["is_stale"] is True
        assert "synthetic" in portfolio.json()["data_notice"].lower()

        report = client.get("/api/research/KAYNES")
        assert report.status_code == 200
        assert report.json()["report"]["ticker"] == "KAYNES"
        assert report.json()["report"]["financial_snapshot"] is None
        assert report.json()["source_status"] == "sources_unavailable"
        assert report.json()["report"]["module_sources"]["business_snapshot"][0]["url"].startswith("https://")

        ad_hoc = client.get("/api/research/SUZLON")
        assert ad_hoc.status_code == 200
        assert ad_hoc.json()["source_status"] == "sources_unavailable"
        assert ad_hoc.json()["company_name"].startswith("SUZLON")


def test_digest_windows_and_network_diligence() -> None:
    with TestClient(app) as client:
        day_digest = client.get("/api/portfolio/ALL/digest?window=24h").json()
        week_digest = client.get("/api/portfolio/ALL/digest?window=7d").json()
        assert day_digest["material_count"] + day_digest["routine_count"] == day_digest["total_announcements"]
        assert week_digest["total_announcements"] > day_digest["total_announcements"]

        query = client.post("/api/network/query", json={"query": "specialty chemicals"}).json()
        assert query["results"]
        person_id = query["results"][0]["person"]["id"]
        dossier = client.get(f"/api/network/diligence/{person_id}")
        assert dossier.status_code == 200
        assert dossier.json()["shortest_path_from_investor"][0] == "You"
        assert client.get("/api/network/diligence/missing").status_code == 404


def test_narrative_does_not_claim_unavailable_sources() -> None:
    with TestClient(app) as client:
        narrative = client.get("/api/research/TRENT/narrative").json()
        assert narrative["source_status"] == "no_transcripts_found"
        assert narrative["quarters_audited"] == 0
        assert narrative["entries"] == []


def test_alerts_graph_and_copilot_are_demo_disclosed() -> None:
    with TestClient(app) as client:
        alerts = client.get("/api/portfolio/alerts").json()
        assert alerts["count"] > 0
        assert "synthetic" in alerts["data_notice"].lower()

        graph = client.get("/api/network/graph?depth=2").json()
        assert graph["total_nodes"] == len(graph["nodes"])
        assert graph["total_edges"] == len(graph["edges"])
        assert graph["total_nodes"] >= 50

        chat = client.post(
            "/api/copilot/chat",
            json={"messages": [{"role": "user", "content": "Who can I call about retail?"}]},
        )
        assert chat.status_code == 200
        assert chat.json()["network_leads"]
        assert "synthetic" in chat.json()["data_notice"].lower()


def test_live_yahoo_data_is_attributed_separately(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ENABLE_LIVE_DATA", True)

    async def fake_snapshot(ticker: str):
        return {
            "ticker": ticker,
            "quote": {
                "current_price": 123.0, "change_absolute": 3.0, "change_percent": 2.5,
                "day_volume": 300, "volume_20d_avg": 100.0, "volume_multiple": 3.0,
                "pe_ratio": None, "market_cap_cr": 0.0, "high_52w": 123.0, "low_52w": 90.0,
                "last_updated": "2026-11-15T00:00:00+00:00",
            },
            "quote_date": "2026-11-14",
            "technicals": {"sma_20": 120.0, "rsi_14": 61.5},
            "fundamentals": {"income_statement": {"revenue": 500.0, "period": "2026-03-31"}},
            "source": "Yahoo Finance via yfinance (unofficial; may be delayed or incomplete)",
        }

    monkeypatch.setattr(market_data_service, "get_live_snapshot", fake_snapshot)
    with TestClient(app) as client:
        research = client.get("/api/research/TRENT").json()
        assert research["source_status"] == "live_yahoo_finance"
        assert research["report"]["financial_snapshot"] is None
        assert research["live_data"]["quote"]["current_price"] == 123.0
        assert research["live_data"]["technicals"]["sma_20"] == 120.0
        assert "modules remain unavailable" in research["data_notice"]

        portfolio = client.get("/api/portfolio").json()
        trent = next(stock for stock in portfolio["stocks"] if stock["ticker"] == "TRENT")
        assert trent["market_data"]["current_price"] == 123.0
        assert trent["market_data_source"].startswith("Yahoo Finance")
