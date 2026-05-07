# =============================================================================
# File: main.py
# Updated: 2026-05-07
# Purpose: Root launcher that prepares .venv and starts the chatbot API server.
# =============================================================================

from app.bootstrap import run_dev_server


if __name__ == "__main__":
    run_dev_server()
