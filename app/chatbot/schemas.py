# =============================================================================
# File: app/chatbot/schemas.py
# Updated: 2026-04-29
# Purpose: Pydantic request and response schemas for chatbot endpoints.
# =============================================================================

from typing import Any

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: dict[str, Any] | None = None


class OptionData(BaseModel):
    step: str
    options: list[str]


class SelectRequest(BaseModel):
    selected: str = Field(..., min_length=1)


class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1)


class SelectData(BaseModel):
    selected: str
    answer: str
    next_step: str
    options: list[str]


class MessageData(BaseModel):
    answer: str
    model: str
    base_url: str
