# =============================================================================
# File: app/main.py
# Updated: 2026-04-29
# Purpose: FastAPI entry point for the dog shopping chatbot API.
# =============================================================================

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.chatbot.router import router as chatbot_router


load_dotenv()

app = FastAPI(
    title="Dog Shopping Chatbot API",
    description="Button-based and Ollama-backed chatbot API for a dog shopping app.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "validation error",
            "data": {"errors": jsonable_encoder(exc.errors())},
        },
    )


@app.get("/health")
def health() -> dict:
    return {
        "success": True,
        "message": "server is healthy",
        "data": {"status": "ok"},
    }


app.include_router(chatbot_router)
