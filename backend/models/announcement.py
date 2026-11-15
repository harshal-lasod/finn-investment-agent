"""
FINN - Pydantic Data Models: Announcements
File: backend/models/announcement.py
"""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AnnouncementCategory(str, Enum):
    FINANCIAL_RESULTS = "financial_results"
    MANAGEMENT_CHANGE = "management_change"
    DEAL_OR_ACQUISITION = "deal_or_acquisition"
    CAPEX_OR_EXPANSION = "capex_or_expansion"
    REGULATORY_OR_LEGAL = "regulatory_or_legal"
    ROUTINE_ADMINISTRATIVE = "routine_administrative"
    OTHER_MATERIAL = "other_material"


class MaterialityScore(BaseModel):
    """Materiality classification result."""
    is_material: bool
    score: float = Field(..., ge=0.0, le=1.0)
    category: AnnouncementCategory


class Announcement(BaseModel):
    """Corporate exchange announcement."""
    id: str = Field(..., description="Unique announcement hash ID")
    ticker: str = Field(..., description="NSE ticker symbol")
    company_name: str = Field(..., description="Company name")
    timestamp: datetime = Field(..., description="Filing timestamp")
    title: str = Field(..., description="Official headline from exchange")
    category: AnnouncementCategory
    is_material: bool = Field(..., description="True if material, False if routine noise")
    materiality_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    summary: str = Field(..., description="Strict 1-line factual synthesis")
    source_url: Optional[str] = Field(None, description="URL to official PDF filing")

    # Enrichment fields
    network_connection_id: Optional[str] = Field(None, description="Linked NetworkPerson ID if any")
    network_context_text: Optional[str] = Field(None, description="Explanation of network connection")
    metric_headline: Optional[str] = Field(None, description="e.g. 'PAT +42% YoY' for results")
