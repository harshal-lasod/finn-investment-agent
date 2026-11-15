"""
FINN - Pydantic Data Models: Narrative vs Numbers
File: backend/models/narrative.py
"""
from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field


class DeliveryStatus(str, Enum):
    DELIVERED = "delivered"
    MISSED = "missed"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"


class NarrativeEntry(BaseModel):
    """Single quarter management guidance vs actual result."""
    quarter: str = Field(..., description="Quarter audited, e.g. Q2 FY25")
    guidance_given: str = Field(..., description="Verbatim/faithful management forward commitment")
    source_concall: str = Field(..., description="Concall citation, e.g. Q1 FY25 Concall p.12")
    actual_reported: str = Field(..., description="Audited reported metric for that quarter")
    delivery_status: DeliveryStatus
    analysis_notes: str = Field(..., description="Objective assessment of beat or miss")


class GuidanceAudit(BaseModel):
    """Full guidance audit result for a ticker."""
    ticker: str
    management_credibility_score: float = Field(..., ge=0.0, le=10.0)
    credibility_summary: str
    quarters_audited: int
    entries: list[NarrativeEntry]
    forward_guidance_commitments: list[str]


class BullBearThesis(BaseModel):
    """Structural bull and bear thesis."""
    bull_points: list[str] = Field(..., min_length=3, max_length=5, description="Structural tailwinds")
    bear_points: list[str] = Field(..., min_length=3, max_length=5, description="Structural risks")
