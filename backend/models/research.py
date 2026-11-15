"""
FINN - Pydantic Data Models: Research
File: backend/models/research.py
"""
from __future__ import annotations
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class BusinessSnapshot(BaseModel):
    """Business operating model and competitive moats."""
    segment_revenue_mix: dict[str, float] = Field(..., description="Segment name -> % contribution")
    core_operating_model: str = Field(..., description="Brief factual description of business model")
    key_moats: list[str] = Field(default_factory=list, description="Primary structural moats")


class FinancialSnapshot(BaseModel):
    """Trailing 12-month P&L and valuation metrics."""
    ttm_revenue_cr: float = Field(..., description="Trailing 12-month revenue in ₹ Cr")
    ttm_ebitda_margin_pct: float = Field(..., description="EBITDA margin %")
    ttm_pat_cr: float = Field(..., description="Trailing 12-month PAT in ₹ Cr")
    roce_pct: float = Field(..., description="Return on Capital Employed %")
    pe_multiple: float = Field(..., description="P/E ratio")
    ev_ebitda_multiple: float = Field(..., description="EV/EBITDA multiple")


class TrajectoryMetrics(BaseModel):
    """Historical growth and margin trend."""
    cagr_revenue_3y: float = Field(..., description="3-Year Revenue CAGR %")
    cagr_revenue_5y: float = Field(..., description="5-Year Revenue CAGR %")
    cagr_pat_5y: float = Field(..., description="5-Year PAT CAGR %")
    margin_trend_summary: str = Field(..., description="Margin expansion or compression trend")


class BalanceSheetHealth(BaseModel):
    """Debt and working capital metrics."""
    gross_debt_cr: float = Field(..., description="Total debt in ₹ Cr")
    net_debt_cr: float = Field(..., description="Net debt in ₹ Cr")
    debt_to_equity: float = Field(..., description="D/E ratio")
    working_capital_days: int = Field(..., description="Working capital cycle in days")


class CashFlowQuality(BaseModel):
    """Cash flow conversion quality metrics."""
    cfo_cr: float = Field(..., description="Cash flow from operations in ₹ Cr")
    pat_cr: float = Field(..., description="Reported PAT in ₹ Cr")
    cfo_to_pat_ratio: float = Field(..., description="CFO / PAT conversion (Ideal > 0.8)")
    free_cash_flow_cr: float = Field(..., description="FCF = CFO - Capex in ₹ Cr")
    fcf_yield_pct: float = Field(..., description="FCF Yield %")


class ResearchReport(BaseModel):
    """Full 8-module primary-grounded research report."""
    ticker: str
    company_name: str
    sector: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    business_snapshot: BusinessSnapshot
    financial_snapshot: FinancialSnapshot
    trajectory: TrajectoryMetrics
    balance_sheet: BalanceSheetHealth
    cash_quality: CashFlowQuality
    narrative_audit: list = Field(default_factory=list)  # list[NarrativeEntry] - avoid circular import
    forward_guidance: list[str] = Field(default_factory=list)
    bull_bear_thesis: dict = Field(default_factory=dict)  # BullBearThesis - avoid circular import
