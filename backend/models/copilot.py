"""
FINN - Pydantic Data Models: Copilot
File: backend/models/copilot.py
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field

from models.network import NetworkPerson


class CopilotMessage(BaseModel):
    """A single message in a copilot conversation."""
    role: str = Field(..., description="'user' or 'assistant' or 'system'")
    content: str = Field(..., description="Message text")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CopilotContext(BaseModel):
    """Active screen context for the copilot."""
    active_ticker: Optional[str] = None
    active_tab: Optional[str] = None  # "push" | "research" | "network"


class CopilotChatRequest(BaseModel):
    """Request body for POST /api/copilot/chat."""
    messages: list[CopilotMessage]
    active_ticker: Optional[str] = None
    active_tab: Optional[str] = None


class CopilotChatResponse(BaseModel):
    """Standardized response from the copilot."""
    response: CopilotMessage
    referenced_sources: list[str] = Field(default_factory=list)
    suggested_followups: list[str] = Field(default_factory=list)
    network_leads: list[NetworkPerson] = Field(default_factory=list)
    action_links: list[dict[str, str]] = Field(default_factory=list)
