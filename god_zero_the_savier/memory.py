# =============================================================================
# File: app/chatbot/memory.py
# Updated: 2026-05-07
# Purpose: In-memory session history store for continuous chatbot conversations.
# =============================================================================

from __future__ import annotations

from threading import Lock
from uuid import uuid4

from pydantic import BaseModel


MAX_HISTORY_MESSAGES = 20


class ChatHistoryMessage(BaseModel):
    role: str
    content: str


_sessions: dict[str, list[ChatHistoryMessage]] = {}
_lock = Lock()


def create_session_id() -> str:
    return uuid4().hex


def normalize_session_id(session_id: str | None) -> str:
    if session_id is None:
        return create_session_id()

    normalized = session_id.strip()
    if not normalized:
        return create_session_id()
    return normalized


def get_history(session_id: str) -> list[ChatHistoryMessage]:
    with _lock:
        return list(_sessions.get(session_id, []))


def append_exchange(session_id: str, user_message: str, assistant_message: str) -> None:
    with _lock:
        history = _sessions.setdefault(session_id, [])
        history.extend(
            [
                ChatHistoryMessage(role="user", content=user_message),
                ChatHistoryMessage(role="assistant", content=assistant_message),
            ]
        )
        if len(history) > MAX_HISTORY_MESSAGES:
            del history[:-MAX_HISTORY_MESSAGES]


def clear_history(session_id: str) -> bool:
    with _lock:
        return _sessions.pop(session_id, None) is not None
