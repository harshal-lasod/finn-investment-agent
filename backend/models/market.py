"""
FINN - Pydantic Data Models: Market & Portfolio
File: backend/models/market.py
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class MarketData(BaseModel):
    """Real-time market data for a stock."""
    model_config = ConfigDict(frozen=True)

    current_price: float = Field(..., description="Last traded price in INR")
    change_absolute: float = Field(..., description="Day change in INR")
    change_percent: float = Field(..., description="Day change percentage")
    day_volume: int = Field(..., description="Current day trading volume")
    volume_20d_avg: float = Field(..., description="20-day moving average volume")
    volume_multiple: float = Field(..., description="Current volume / 20-day avg volume")
    pe_ratio: Optional[float] = Field(None, description="Price to Earnings ratio")
    market_cap_cr: float = Field(..., description="Market capitalization in INR Crores")
    high_52w: float = Field(..., description="52-week high price in INR")
    low_52w: float = Field(..., description="52-week low price in INR")
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of last update"
    )


class MetricChange(BaseModel):
    """Represents a metric with its period-over-period change."""
    value: float
    change_pct: float
    period: str = Field(..., description="e.g. 'YoY', 'QoQ'")


class PortfolioStock(BaseModel):
    """A stock in the portfolio with enriched market data."""
    ticker: str = Field(..., description="NSE ticker symbol, e.g. TRENT")
    company_name: str = Field(..., description="Full legal company name")
    sector: str = Field(..., description="Industry sector, e.g. Retail, Chemicals")
    market_cap_category: str = Field(..., description="Large Cap, Mid Cap, Small Cap")
    market_data: MarketData
    active_alert_count: int = Field(default=0, ge=0)
    has_recent_material_filing: bool = Field(default=False)


class PortfolioResponse(BaseModel):
    """Response for GET /api/portfolio."""
    total_count: int
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    stocks: list[PortfolioStock]
    is_stale: bool = Field(default=False, description="True if serving cached/seed data")
