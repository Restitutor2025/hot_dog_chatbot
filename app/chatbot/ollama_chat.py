# =============================================================================
# File: app/chatbot/ollama_chat.py
# Updated: 2026-04-29
# Purpose: Ollama-backed LlamaIndex chat client without RAG or vector indexing.
# =============================================================================

import os
from functools import lru_cache

from llama_index.core import Settings
from llama_index.core.llms import ChatMessage
from llama_index.llms.ollama import Ollama
from pydantic import BaseModel

from app.chatbot.options import SYSTEM_PROMPT


DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "gemma3:4b"
REQUEST_TIMEOUT = 120.0
TEMPERATURE = 0


class OllamaSettings(BaseModel):
    base_url: str
    model: str
    request_timeout: float
    temperature: int


@lru_cache(maxsize=1)
def get_ollama_settings() -> OllamaSettings:
    return OllamaSettings(
        base_url=os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
        model=os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
        request_timeout=REQUEST_TIMEOUT,
        temperature=TEMPERATURE,
    )


@lru_cache(maxsize=1)
def get_llm() -> Ollama:
    settings = get_ollama_settings()
    llm = Ollama(
        model=settings.model,
        base_url=settings.base_url,
        request_timeout=settings.request_timeout,
        temperature=settings.temperature,
    )
    Settings.llm = llm
    return llm


def generate_chat_response(message: str) -> str:
    llm = get_llm()
    response = llm.chat(
        messages=[
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(role="user", content=message),
        ]
    )

    content = getattr(getattr(response, "message", None), "content", None)
    if content is None:
        content = str(response)
    return content.strip()
