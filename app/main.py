#
#  main.py
#  hot_dog_chatbot
#
#  Created by Codex on 2026-04-29.
#  Updated by Codex on 2026-05-07.
#
#  Codex Update Log:
#  - 2026-04-29: Added the FastAPI app, CORS setup, validation handler, and health route.
#  - 2026-05-07: Added direct-run bootstrap support while preserving uvicorn imports.
#
#  God_Zero Update Log:
#  - 2026-05-07: Session memory is mounted through app.chatbot.router.
#

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if __name__ == "__main__":
    from app.bootstrap import run_dev_server

    run_dev_server()
    raise SystemExit(0)

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
