"""
FINN - Pydantic Data Models: Common
File: backend/models/common.py
"""
from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None
    path: Optional[str] = None
