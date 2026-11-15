"""
FINN - Pydantic Data Models: Alerts & Digest
File: backend/models/alert.py
"""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from models.announcement import Announcement


class AlertType(str, Enum):
    VOLUME_SPIKE = "volume_spike"
    PRICE_SHOCK = "price_shock"
    C_SUITE_CHANGE = "c_suite_change"
    EARNINGS_ANOMALY = "earnings_anomaly"
    NETWORK_INTERACTION_NUDGE = "network_interaction_nudge"


class DigestWindow(str, Enum):
    HOURS_24 = "24h"
    DAYS_7 = "7d"


class Alert(BaseModel):
    """An active anomaly alert for a portfolio stock."""
    id: str = Field(..., description="Unique alert ID")
    ticker: str
    company_name: str
    alert_type: AlertType
    severity: str = Field(..., description="HIGH, MEDIUM, LOW")
    headline: str = Field(..., description="Concise alert description")
    trigger_value: str = Field(..., description="e.g. '3.4x 20d Volume' or '-5.8% Intraday'")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    network_context: Optional[str] = None
    is_dismissed: bool = False


class AnomalyTrigger(BaseModel):
    """Trigger parameters for anomaly detection."""
    volume_multiple_threshold: float = Field(default=2.0)
    price_change_pct_threshold: float = Field(default=5.0)


class Digest(BaseModel):
    """Windowed announcement digest split into material vs routine."""
    window: DigestWindow
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    material_announcements: list[Announcement] = Field(default_factory=list)
    routine_announcements: list[Announcement] = Field(default_factory=list)
