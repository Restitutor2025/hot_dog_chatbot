#
#  schemas.py
#  hot_dog_chatbot
#
#  Created by Codex on 2026-04-29.
#  Updated by Codex on 2026-05-07.
#  Updated by God_Zero on 2026-05-07.
#
#  Codex Update Log:
#  - 2026-04-29: Added base request and response schemas for the chatbot API.
#  - 2026-05-07: Preserved existing schemas while adding session-aware response data.
#
#  God_Zero Update Log:
#  - 2026-05-07: God_Zero님 added optional session_id support for RAM-based conversation memory.
#

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
    session_id: str | None = None
    user_seq: int | None = Field(default=None, ge=1)
    user_id: str | None = Field(default=None, min_length=1)
    buy_seq: int | None = Field(default=None, ge=1)
    deliver_seq: int | None = Field(default=None, ge=1)
    product_seq: int | None = Field(default=None, ge=1)


class SelectData(BaseModel):
    selected: str
    answer: str
    next_step: str
    options: list[str]


class MessageData(BaseModel):
    answer: str
    session_id: str
    model: str
    base_url: str
