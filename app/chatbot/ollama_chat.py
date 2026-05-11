#
#  ollama_chat.py
#  hot_dog_chatbot
#
#  Created by Codex on 2026-04-29.
#  Updated by Codex on 2026-05-07.
#  Updated by God_Zero on 2026-05-07.
#
#  Codex Update Log:
#  - 2026-04-29: Added local Ollama chat generation without CSV, RAG, or vector indexes.
#  - 2026-05-07: Preserved the Ollama defaults and wired history into direct-message chat.
#
#  God_Zero Update Log:
#  - 2026-05-07: God_Zero님 added session history messages to support continuous conversations.
#

import os
from functools import lru_cache

from llama_index.core import Settings
from llama_index.core.llms import ChatMessage
from llama_index.llms.ollama import Ollama
from pydantic import BaseModel

from app.chatbot.memory import ChatHistoryMessage
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


def generate_chat_response(
    message: str,
    history: list[ChatHistoryMessage] | None = None,
    product_context: str | None = None,
) -> str:
    llm = get_llm()
    chat_messages = [ChatMessage(role="system", content=SYSTEM_PROMPT)]
    chat_messages.extend(
        ChatMessage(role=history_message.role, content=history_message.content)
        for history_message in history or []
    )
    if product_context:
        chat_messages.append(ChatMessage(role="system", content=product_context))
    chat_messages.append(ChatMessage(role="user", content=message))

    response = llm.chat(
        messages=chat_messages,
    )

    content = getattr(getattr(response, "message", None), "content", None)
    if content is None:
        content = str(response)
    return content.strip()
