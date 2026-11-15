"""HTTP endpoints for FINN's Push, Pull, and Network demo flows."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.config import settings
from backend.services.demo_data import DATA_NOTICE, load_portfolio, portfolio_stocks, resolve_stock
from backend.models.market import MarketData
from backend.services.market_data import YAHOO_SOURCE, market_data_service
from backend.services.local_cache import persistent_response_cache
from backend.services.network_graph import network_service
from backend.services.research_engine import build_narrative, build_research
from backend.services.symbol_directory import search_symbols

router = APIRouter()


@router.get("/symbols/search")
def symbol_search(
    q: str = Query(min_length=1, max_length=80),
    limit: int = Query(default=10, ge=1, le=20),
) -> dict[str, list[dict[str, str]]]:
    return {"symbols": search_symbols(q, limit)}


def _market_data_notice(live_count: int) -> str:
    if live_count:
        return (
            f"{live_count} latest daily bar quote(s) and technical indicators use {YAHOO_SOURCE}. "
            "Any remaining quotes, announcements, and contact data are synthetic; unsupported fundamental modules are not estimated."
        )
    if settings.ENABLE_LIVE_DATA:
        return f"Yahoo Finance did not return usable history; demo seed values are shown. {DATA_NOTICE}"
    return DATA_NOTICE


async def _fetch_live_portfolio() -> dict[str, dict[str, Any]]:
    if not settings.ENABLE_LIVE_DATA:
        return {}
    stocks = load_portfolio()
    semaphore = asyncio.Semaphore(5)

    async def fetch(stock: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
        async with semaphore:
            return stock["ticker"], await market_data_service.get_live_snapshot(stock["ticker"])

    snapshots = await asyncio.gather(*(fetch(stock) for stock in stocks))
    return {ticker: snapshot for ticker, snapshot in snapshots if snapshot is not None}


class NetworkQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    company_focus: str | None = None
    sector_focus: str | None = None
    max_results: int = Field(default=5, ge=1, le=20)


class CopilotMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1, max_length=4_000)
    timestamp: datetime | None = None


class CopilotChatRequest(BaseModel):
    messages: list[CopilotMessage] = Field(min_length=1, max_length=30)
    active_ticker: str | None = None
    active_tab: str | None = None


def _announcements() -> tuple[list[dict[str, Any]], dict[str, str], datetime]:
    now = datetime.now(timezone.utc)
    companies = {item["ticker"]: item["company_name"] for item in load_portfolio()}
    return [
        {
            "id": "demo-results-trent", "ticker": "TRENT", "title": "Illustrative quarterly results scenario",
            "hours_ago": 5, "category": "financial_results", "material": True, "score": 0.91,
            "summary": "Synthetic example only: a results filing would be reviewed against audited statements.",
            "metric_headline": "Illustrative scenario · not actual results",
        },
        {
            "id": "demo-management-kaynes", "ticker": "KAYNES", "title": "Illustrative leadership update scenario",
            "hours_ago": 19, "category": "management_change", "material": True, "score": 0.82,
            "summary": "Synthetic scenario showing how a management-change filing could be connected to the network.",
            "network_connection_id": "p_002", "network_context_text": "Synthetic contact; verify any connection independently.",
        },
        {
            "id": "demo-expansion-lt", "ticker": "LT", "title": "Illustrative capacity expansion scenario",
            "hours_ago": 44, "category": "capex_or_expansion", "material": True, "score": 0.76,
            "summary": "Synthetic example only: review the official filing for investment amount and timeline.",
        },
        {
            "id": "demo-admin-itc", "ticker": "ITC", "title": "Illustrative share-certificate service request",
            "hours_ago": 11, "category": "routine_administrative", "material": False, "score": 0.12,
            "summary": "Synthetic routine-filing example included to demonstrate noise filtering.",
        },
        {
            "id": "demo-admin-infy", "ticker": "INFY", "title": "Illustrative investor-meeting schedule",
            "hours_ago": 137, "category": "routine_administrative", "material": False, "score": 0.08,
            "summary": "Synthetic routine-filing example included to demonstrate the 7-day digest.",
        },
        {
            "id": "demo-regulatory-sbin", "ticker": "SBIN", "title": "Illustrative regulatory update scenario",
            "hours_ago": 155, "category": "regulatory_or_legal", "material": True, "score": 0.70,
            "summary": "Synthetic example only: no actual regulatory filing is represented.",
        },
    ], companies, now


def _announcement_models() -> tuple[list[dict[str, Any]], datetime]:
    raw, companies, now = _announcements()
    return ([{
        "id": item["id"],
        "ticker": item["ticker"],
        "company_name": companies[item["ticker"]],
        "timestamp": now - timedelta(hours=item["hours_ago"]),
        "title": item["title"],
        "category": item["category"],
        "is_material": item["material"],
        "materiality_score": item["score"],
        "summary": item["summary"],
        "network_connection_id": item.get("network_connection_id"),
        "network_context_text": item.get("network_context_text"),
        "metric_headline": item.get("metric_headline"),
    } for item in raw], now)


@router.get("/portfolio")
@persistent_response_cache("portfolio", settings.PORTFOLIO_CACHE_TTL_SECONDS)
async def get_portfolio() -> dict[str, Any]:
    snapshots = await _fetch_live_portfolio()
    stocks = []
    for stock in portfolio_stocks():
        snapshot = snapshots.get(stock.ticker)
        if snapshot is not None:
            stock = stock.model_copy(update={"market_data": MarketData.model_validate(snapshot["quote"])})
        item = stock.model_dump(mode="json")
        item["market_data_source"] = YAHOO_SOURCE if snapshot else "Synthetic demo seed"
        item["quote_date"] = snapshot["quote_date"] if snapshot else None
        stocks.append(item)
    return {
        "total_count": len(stocks),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "stocks": stocks,
        "is_stale": len(snapshots) < len(stocks),
        "data_notice": _market_data_notice(len(snapshots)),
    }


@router.get("/portfolio/alerts")
@persistent_response_cache("alerts", settings.ALERTS_CACHE_TTL_SECONDS)
async def get_alerts() -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    snapshots = await _fetch_live_portfolio()
    stocks = {item["ticker"]: item for item in load_portfolio()}
    alerts = []
    for stock in stocks.values():
        snapshot = snapshots.get(stock["ticker"])
        if snapshot:
            quote = MarketData.model_validate(snapshot["quote"])
            change = quote.change_percent
            multiple = quote.volume_multiple
        else:
            change = float(stock["change_pct"])
            multiple = float(stock["volume_multiple"])
        if multiple > settings.ALERT_VOLUME_MULTIPLE_THRESHOLD:
            alerts.append({
                "id": f"volume-{stock['ticker'].lower()}",
                "ticker": stock["ticker"], "company_name": stock["company_name"],
                "alert_type": "volume_spike", "severity": "MEDIUM",
                "headline": f"{stock['ticker']} volume is above the configured threshold",
                "trigger_value": f"{multiple:.1f}x 20d average",
                "timestamp": now.isoformat(), "is_dismissed": False,
                "data_source": YAHOO_SOURCE if snapshot else "Synthetic demo seed",
            })
        if abs(change) >= settings.ALERT_PRICE_CHANGE_PCT_THRESHOLD:
            alerts.append({
                "id": f"price-{stock['ticker'].lower()}",
                "ticker": stock["ticker"], "company_name": stock["company_name"],
                "alert_type": "price_shock", "severity": "HIGH",
                "headline": f"{stock['ticker']} price move exceeds the configured threshold",
                "trigger_value": f"{change:+.1f}%",
                "timestamp": now.isoformat(), "is_dismissed": False,
                "data_source": YAHOO_SOURCE if snapshot else "Synthetic demo seed",
            })
    return {
        "count": len(alerts),
        "generated_at": now.isoformat(),
        "alerts": alerts,
        "data_notice": _market_data_notice(len(snapshots)),
    }


@router.get("/portfolio/{ticker}/digest")
@persistent_response_cache("digest", settings.DIGEST_CACHE_TTL_SECONDS)
async def get_digest(
    ticker: str,
    window: Literal["24h", "7d"] = Query(default="24h"),
) -> dict[str, Any]:
    normalized = ticker.upper()
    if normalized != "ALL":
        try:
            resolve_stock(normalized)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    announcements, now = _announcement_models()
    cutoff = now - timedelta(hours=24 if window == "24h" else 168)
    selected = [
        item for item in announcements
        if (normalized == "ALL" or item["ticker"] == normalized) and item["timestamp"] >= cutoff
    ]
    material = [item for item in selected if item["is_material"]]
    routine = [item for item in selected if not item["is_material"]]
    return {
        "ticker": normalized,
        "window": window,
        "generated_at": now.isoformat(),
        "total_announcements": len(selected),
        "material_count": len(material),
        "routine_count": len(routine),
        "material_announcements": material,
        "routine_announcements": routine,
        "data_notice": DATA_NOTICE,
    }


@router.get("/research/{ticker}")
@persistent_response_cache("research", settings.RESEARCH_RESPONSE_CACHE_TTL_SECONDS)
async def get_research(ticker: str) -> dict[str, Any]:
    try:
        report = build_research(ticker)
        symbol = report["ticker"].upper().removesuffix(".NS")
        yahoo_base = f"https://finance.yahoo.com/quote/{symbol}.NS/"
        nse_filings = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"
        source_urls = {
            "quote": f"{yahoo_base}",
            "financials": f"{yahoo_base}financials/",
            "balance_sheet": f"{yahoo_base}balance-sheet/",
            "cash_flow": f"{yahoo_base}cash-flow/",
        }
        if settings.ENABLE_LIVE_DATA:
            snapshot = await market_data_service.get_live_snapshot(report["ticker"])
            if snapshot is not None:
                report["live_data"] = snapshot
                source_urls.update(snapshot.get("source_urls", {}))
                report["source_status"] = "live_yahoo_finance"
                report["data_notice"] = (
                    "Latest daily bar and technical indicators are from Yahoo Finance via yfinance (unofficial and may be delayed or partial). "
                    "Company-analysis modules remain unavailable unless supported by filings; the narrative audit requires verified transcripts."
                )
                statement_data = snapshot.get("fundamentals", {})
                module_status = report["report"]["module_status"]
                if statement_data.get("income_statement"):
                    module_status["financial_snapshot"] = "Yahoo annual statements available; not primary-source verified"
                if statement_data.get("balance_sheet"):
                    module_status["balance_sheet"] = "Yahoo annual statements available; verify against filings"
                if statement_data.get("cash_flow"):
                    module_status["cash_quality"] = "Yahoo annual statements available; verify against filings"
            else:
                report["live_data_error"] = market_data_service.last_error(report["ticker"])
        report["report"]["module_sources"] = {
            "business_snapshot": [{"label": "NSE corporate filings", "url": nse_filings}],
            "financial_snapshot": [{"label": "Yahoo annual financials", "url": source_urls["financials"]}],
            "trajectory": [{"label": "Yahoo financials", "url": source_urls["financials"]}],
            "balance_sheet": [{"label": "Yahoo balance sheet", "url": source_urls["balance_sheet"]}],
            "cash_quality": [{"label": "Yahoo cash flow", "url": source_urls["cash_flow"]}],
            "narrative_audit": [{"label": "NSE corporate filings", "url": nse_filings}],
            "forward_guidance": [{"label": "NSE corporate filings", "url": nse_filings}],
            "bull_bear_thesis": [{"label": "NSE corporate filings", "url": nse_filings}],
        }
        return report
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/research/{ticker}/narrative")
@persistent_response_cache("narrative", settings.NARRATIVE_CACHE_TTL_SECONDS)
async def get_narrative(ticker: str) -> dict[str, Any]:
    try:
        return build_narrative(ticker)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/network/query")
@persistent_response_cache("network-query", settings.NETWORK_CACHE_TTL_SECONDS)
async def query_network(request: NetworkQueryRequest) -> dict[str, Any]:
    results = network_service.query(
        request.query, request.company_focus, request.sector_focus, request.max_results
    )
    return {
        "query": request.query,
        "resolved_focus": {
            "company": request.company_focus,
            "sector": request.sector_focus,
            "mode": "synthetic keyword matching",
        },
        "results": results,
        "data_notice": DATA_NOTICE,
    }


@router.get("/network/graph")
@persistent_response_cache("network-graph", settings.NETWORK_CACHE_TTL_SECONDS)
async def get_network_graph(
    center_node: str = "INVESTOR_ROOT",
    depth: int = Query(default=2, ge=1, le=3),
) -> dict[str, Any]:
    return {**network_service.snapshot(center_node, depth), "data_notice": DATA_NOTICE}


@router.get("/network/diligence/{person_id}")
@persistent_response_cache("network-diligence", settings.NETWORK_CACHE_TTL_SECONDS)
async def get_diligence(person_id: str) -> dict[str, Any]:
    result = network_service.diligence(person_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Person not found in network graph")
    return {**result, "data_notice": DATA_NOTICE}


@router.post("/copilot/chat")
@persistent_response_cache("copilot", settings.COPILOT_CACHE_TTL_SECONDS)
async def copilot_chat(request: CopilotChatRequest) -> dict[str, Any]:
    user_message = next((message.content for message in reversed(request.messages) if message.role == "user"), "")
    if not user_message:
        raise HTTPException(status_code=422, detail="At least one user message is required.")
    leads = network_service.query(user_message, request.active_ticker, max_results=3)
    response_text = (
        "This demo uses synthetic portfolio, filing, financial, and contact data. "
        "I can show the relevant demo records, but I cannot verify company facts or provide an investment recommendation. "
        "Check the linked primary filings and audited statements before drawing conclusions."
    )
    if leads and any(word in user_message.lower() for word in ("who", "call", "network", "contact")):
        response_text += " Potential synthetic network matches: " + ", ".join(
            result["person"]["name"] for result in leads
        ) + "."
    response_text += f" Context: {request.active_tab or 'general'}."
    return {
        "response": {
            "role": "assistant", "content": response_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "referenced_sources": ["FINN synthetic demo seed"],
        "suggested_followups": [
            "Show the network matches for this theme.",
            "Open the research page and check the source status.",
        ],
        "network_leads": [result["person"] for result in leads],
        "action_links": [],
        "data_notice": DATA_NOTICE,
    }
