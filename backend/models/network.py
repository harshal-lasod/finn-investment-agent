"""
FINN - Pydantic Data Models: Network Graph
File: backend/models/network.py
"""
from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class NodeRole(str, Enum):
    INVESTOR = "investor"
    EXECUTIVE = "executive"
    FOUNDER = "founder"
    BOARD_MEMBER = "board_member"
    DOMAIN_EXPERT = "domain_expert"
    ALUMNUS = "alumnus"


class NetworkPerson(BaseModel):
    """A person node in the investor's network graph."""
    id: str = Field(..., description="Unique person identifier, e.g. p_001")
    name: str = Field(..., description="Full Name")
    current_role: str = Field(..., description="Current job title")
    current_company: str = Field(..., description="Current employer")
    closeness_score: int = Field(..., ge=1, le=5, description="1 (Distant) to 5 (Core Circle)")
    role_type: NodeRole
    past_companies: list[str] = Field(default_factory=list)
    alma_maters: list[str] = Field(default_factory=list)
    expertise_tags: list[str] = Field(default_factory=list)
    last_interaction_date: Optional[str] = None


class NetworkEdge(BaseModel):
    """An edge (relationship) between two nodes in the graph."""
    source_id: str
    target_id: str
    relationship_type: str = Field(..., description="KNOWS, WORKED_AT, STUDIED_AT, COLLEAGUE_OF")
    weight: float = Field(default=1.0)
    context_notes: Optional[str] = None


class NetworkGraph(BaseModel):
    """Full network graph for visualization."""
    nodes: list[NetworkPerson]
    edges: list[NetworkEdge]


class NetworkQueryResult(BaseModel):
    """A person surfaced by a network query with relevance context."""
    person: NetworkPerson
    relevance_reason: str = Field(..., description="Why this person is relevant to the query")
    path_from_investor: list[str] = Field(..., description="e.g. ['You', 'Vikram Malhotra', 'Target Person']")
    degree: int = Field(..., ge=1, le=3)
    suggested_icebreaker: str = Field(..., description="Grounding context to initiate conversation")


class DiligenceProfile(BaseModel):
    """Executive diligence dossier."""
    person: NetworkPerson
    shortest_path_from_investor: list[str]
    degrees_of_separation: int
    common_alumni: list[str]
    common_past_employers: list[str]
    talking_points: list[str]
