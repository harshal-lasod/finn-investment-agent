"""Deterministic, explicitly synthetic data used to keep the submission demo reliable."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from backend.models.market import MarketData, PortfolioStock
from backend.models.network import NetworkPerson

DATA_DIR = Path(__file__).resolve().parents[1] / "storage"
DATA_NOTICE = (
    "Illustrative demo data only. Prices, filings, financials, people, and guidance "
    "are synthetic and are not verified market data or investment advice."
)
_FIRST_NAMES = [
    "Aarav", "Aditi", "Akash", "Ananya", "Arjun", "Dev", "Ira", "Kabir", "Kavya",
    "Mira", "Neel", "Nisha", "Rohan", "Sana", "Vikram", "Zoya", "Ishan", "Leela",
    "Manav", "Tara",
]
_LAST_NAMES = [
    "Mehta", "Rao", "Kapoor", "Shah", "Iyer", "Desai", "Malhotra", "Sen", "Nair",
    "Khanna", "Joshi", "Bose", "Kulkarni", "Sethi", "Menon", "Roy", "Bhat", "Dutta",
]
_EXPERTISE = [
    ["Consumer retail", "Store economics", "Quick commerce"],
    ["Electronics manufacturing", "Supply chain", "Capital allocation"],
    ["Specialty chemicals", "Process engineering", "R&D"],
    ["Banking", "Credit", "Digital lending"],
    ["Automotive", "EVs", "Component sourcing"],
    ["Information technology", "Cloud", "Enterprise software"],
    ["Pharmaceuticals", "Regulatory affairs", "R&D"],
    ["Industrials", "EPC", "Project execution"],
]
_COMPANIES = [
    "Trent", "Dixon Technologies", "Deepak Nitrite", "HDFC Bank", "Tata Motors",
    "TCS", "Sun Pharma", "Larsen & Toubro", "Reliance Industries", "Kaynes Technology",
]
_SCHOOLS = ["IIM Ahmedabad", "IIT Bombay", "IIM Bangalore", "Delhi University", "IIT Madras"]


def load_portfolio() -> list[dict[str, Any]]:
    with (DATA_DIR / "portfolio_seed.json").open(encoding="utf-8") as seed:
        return json.load(seed)


def load_people() -> list[NetworkPerson]:
    """Create 50 repeatable fictional contacts with overlapping expertise clusters."""
    people: list[NetworkPerson] = []
    for index in range(50):
        first = _FIRST_NAMES[index % len(_FIRST_NAMES)]
        last = _LAST_NAMES[(index * 7 + index // len(_FIRST_NAMES)) % len(_LAST_NAMES)]
        expertise = _EXPERTISE[index % len(_EXPERTISE)]
        closeness = [5, 4, 3, 2, 1][index % 5]
        role = ["executive", "founder", "domain_expert", "investor", "board_member"][index % 5]
        people.append(NetworkPerson(
            id=f"p_{index + 1:03d}",
            name=f"{first} {last}",
            current_role=f"Synthetic {role.replace('_', ' ').title()}",
            current_company=_COMPANIES[index % len(_COMPANIES)],
            closeness_score=closeness,
            role_type=role,
            past_companies=[_COMPANIES[(index + 3) % len(_COMPANIES)]],
            alma_maters=[_SCHOOLS[index % len(_SCHOOLS)]],
            expertise_tags=expertise,
            last_interaction_date=(datetime.now(timezone.utc) - timedelta(days=7 + index)).date().isoformat(),
        ))
    return people


def stock_quote(stock: dict[str, Any]) -> MarketData:
    price = float(stock["price"])
    change_pct = float(stock["change_pct"])
    previous_close = price / (1 + change_pct / 100) if change_pct > -100 else price
    avg_volume = 1_000_000 + int(stock["market_cap_cr"]) % 500_000
    volume_multiple = float(stock["volume_multiple"])
    volume = int(avg_volume * volume_multiple)
    return MarketData(
        current_price=price,
        change_absolute=round(price - previous_close, 2),
        change_percent=change_pct,
        day_volume=volume,
        volume_20d_avg=float(avg_volume),
        volume_multiple=volume_multiple,
        pe_ratio=float(stock["pe_ratio"]),
        market_cap_cr=float(stock["market_cap_cr"]),
        high_52w=round(price * 1.18, 2),
        low_52w=round(price * 0.72, 2),
        last_updated=datetime.now(timezone.utc),
    )


def portfolio_stocks() -> list[PortfolioStock]:
    return [
        PortfolioStock(
            ticker=item["ticker"],
            company_name=item["company_name"],
            sector=item["sector"],
            market_cap_category=item["market_cap_category"],
            market_data=stock_quote(item),
            active_alert_count=int(
                float(item["volume_multiple"]) > 2
                or abs(float(item["change_pct"])) >= 4
            ),
            has_recent_material_filing=item["ticker"] in {"TRENT", "TATAMOTORS", "KAYNES"},
        )
        for item in load_portfolio()
    ]


def resolve_stock(ticker: str) -> dict[str, Any]:
    normalized = ticker.upper().removesuffix(".NS").strip()
    if not normalized or len(normalized) > 20 or not normalized.replace("-", "").isalnum():
        raise ValueError("Ticker must be a valid NSE symbol.")
    for stock in load_portfolio():
        if stock["ticker"] == normalized:
            return stock
    return {
        "ticker": normalized,
        "company_name": f"{normalized} (unverified ticker)",
        "sector": "Unclassified",
        "market_cap_category": "Unclassified",
        "price": 0.0,
        "change_pct": 0.0,
        "volume_multiple": 0.0,
        "pe_ratio": 0.0,
        "market_cap_cr": 0.0,
    }
