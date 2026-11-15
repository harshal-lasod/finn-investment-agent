"""Primary-source-aware research response; missing facts stay unavailable."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.services.demo_data import DATA_NOTICE, resolve_stock
from backend.services.network_graph import network_service


def build_research(ticker: str) -> dict[str, Any]:
    stock = resolve_stock(ticker)
    code = stock["ticker"]
    overlay = network_service.query(
        f"{stock['sector']} {code}", company_focus=code, sector_focus=stock["sector"], max_results=3
    )
    return {
        "ticker": code,
        "company_name": stock["company_name"],
        "sector": stock["sector"],
        "report": {
            "ticker": code,
            "company_name": stock["company_name"],
            "sector": stock["sector"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "business_snapshot": None,
            "financial_snapshot": None,
            "trajectory": None,
            "balance_sheet": None,
            "cash_quality": None,
            "narrative_audit": [],
            "forward_guidance": [],
            "bull_bear_thesis": None,
            "module_status": {
                "business_snapshot": "primary_source_unavailable",
                "financial_snapshot": "annual_statement_data_unavailable",
                "trajectory": "multi_year_statement_data_unavailable",
                "balance_sheet": "verified_balance_sheet_unavailable",
                "cash_quality": "verified_cash_flow_unavailable",
                "narrative_audit": "no_verified_transcripts",
                "forward_guidance": "no_verified_transcripts",
                "bull_bear_thesis": "not_generated_without_verified_company_context",
            },
        },
        "network_overlay": [item["person"] for item in overlay],
        "cached": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_status": "sources_unavailable",
        "data_notice": DATA_NOTICE,
    }


def build_narrative(ticker: str) -> dict[str, Any]:
    stock = resolve_stock(ticker)
    return {
        "ticker": stock["ticker"],
        "management_credibility_score": 0.0,
        "credibility_summary": "No verified transcripts or audited results are loaded; no credibility assessment is possible.",
        "quarters_audited": 0,
        "entries": [],
        "forward_guidance_commitments": [],
        "source_status": "no_transcripts_found",
        "data_notice": DATA_NOTICE,
    }
