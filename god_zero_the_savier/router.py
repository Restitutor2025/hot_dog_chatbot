# =============================================================================
# File: app/chatbot/router.py
# Updated: 2026-05-07
# Purpose: FastAPI routes for button selections and free-text Ollama chat.
# =============================================================================

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.chatbot.memory import append_exchange, clear_history, get_history, normalize_session_id
from app.chatbot.ollama_chat import generate_chat_response, get_ollama_settings
from app.chatbot.options import (
    ALL_SELECTABLE_OPTIONS,
    CATEGORY_OPTIONS,
    MAIN_OPTIONS,
    MAIN_SELECTIONS,
    MAIN_STEP,
    OPTION_RESPONSES,
)
from app.chatbot.schemas import MessageRequest, SelectRequest


router = APIRouter(prefix="/chat", tags=["chatbot"])


def api_response(success: bool, message: str, data: dict | None = None) -> dict:
    return {"success": success, "message": message, "data": data}


def error_response(status_code: int, message: str, data: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=api_response(False, message, data),
    )


@router.get("/options")
def get_main_options():
    return api_response(
        True,
        "main options loaded",
        {"step": MAIN_STEP, "options": MAIN_OPTIONS},
    )


@router.get("/options/{category}")
def get_category_options(category: str):
    normalized_category = category.strip().lower()
    options = CATEGORY_OPTIONS.get(normalized_category)
    if options is None:
        return error_response(
            400,
            "invalid category",
            {"category": category, "available_categories": list(CATEGORY_OPTIONS.keys())},
        )

    return api_response(
        True,
        f"{normalized_category} options loaded",
        {"step": normalized_category, "options": options},
    )


@router.post("/select")
def select_option(request: SelectRequest):
    selected = request.selected.strip()
    if not selected:
        return error_response(400, "selected is required", {"available_options": ALL_SELECTABLE_OPTIONS})

    if selected in MAIN_SELECTIONS:
        selection = MAIN_SELECTIONS[selected]
        return api_response(
            True,
            "selection handled",
            {
                "selected": selected,
                "answer": selection["answer"],
                "next_step": selection["next_step"],
                "options": selection["options"],
            },
        )

    answer = OPTION_RESPONSES.get(selected)
    if answer is None:
        return error_response(
            400,
            "unsupported selection",
            {"selected": selected, "available_options": ALL_SELECTABLE_OPTIONS},
        )

    return api_response(
        True,
        "selection handled",
        {
            "selected": selected,
            "answer": answer,
            "next_step": MAIN_STEP,
            "options": MAIN_OPTIONS,
        },
    )


@router.post("/message")
def chat_message(request: MessageRequest):
    message = request.message.strip()
    if not message:
        return error_response(400, "message is required", None)

    session_id = normalize_session_id(request.session_id)
    history = get_history(session_id)
    settings = get_ollama_settings()
    try:
        answer = generate_chat_response(message, history)
    except Exception as exc:
        return error_response(
            503,
            "ollama request failed",
            {
                "error": str(exc),
                "base_url": settings.base_url,
                "model": settings.model,
            },
        )

    append_exchange(session_id, message, answer)
    return api_response(
        True,
        "chat response generated",
        {
            "answer": answer,
            "session_id": session_id,
            "model": settings.model,
            "base_url": settings.base_url,
        },
    )


@router.delete("/sessions/{session_id}")
def delete_chat_session(session_id: str):
    normalized_session_id = session_id.strip()
    if not normalized_session_id:
        return error_response(400, "session_id is required", None)

    deleted = clear_history(normalized_session_id)
    return api_response(
        True,
        "session cleared" if deleted else "session was already empty",
        {"session_id": normalized_session_id},
    )
