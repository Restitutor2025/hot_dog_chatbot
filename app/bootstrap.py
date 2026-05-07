# =============================================================================
# File: app/bootstrap.py
# Updated: 2026-05-07
# Purpose: Prepare .venv, ensure the Ollama model, and launch the API server.
# =============================================================================

from __future__ import annotations

import hashlib
import os
import subprocess
import venv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"
REQUIREMENTS_MARKER = VENV_DIR / ".requirements.sha256"
DEFAULT_OLLAMA_MODEL = "gemma3:4b"


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _requirements_hash() -> str:
    return hashlib.sha256(REQUIREMENTS_PATH.read_bytes()).hexdigest()


def _create_venv_if_needed() -> None:
    python_path = _venv_python()
    if python_path.exists():
        return

    print(f"[bootstrap] creating virtual environment: {VENV_DIR}")
    venv.create(VENV_DIR, with_pip=True)


def _install_requirements_if_needed() -> None:
    if not REQUIREMENTS_PATH.exists():
        raise FileNotFoundError(f"requirements.txt not found: {REQUIREMENTS_PATH}")

    current_hash = _requirements_hash()
    if REQUIREMENTS_MARKER.exists() and REQUIREMENTS_MARKER.read_text(encoding="utf-8") == current_hash:
        return

    python_path = _venv_python()
    print("[bootstrap] installing requirements")
    subprocess.check_call(
        [str(python_path), "-m", "pip", "install", "-r", str(REQUIREMENTS_PATH)],
        cwd=PROJECT_ROOT,
    )
    REQUIREMENTS_MARKER.write_text(current_hash, encoding="utf-8")


def ensure_venv() -> Path:
    _create_venv_if_needed()
    _install_requirements_if_needed()
    return _venv_python()


def _ollama_env() -> dict[str, str]:
    env = os.environ.copy()
    base_url = env.get("OLLAMA_BASE_URL")
    if base_url and not env.get("OLLAMA_HOST"):
        env["OLLAMA_HOST"] = base_url
    return env


def _ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)


def _is_ollama_model_installed(model: str) -> bool:
    result = subprocess.run(
        ["ollama", "list"],
        cwd=PROJECT_ROOT,
        env=_ollama_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip())

    installed_models = {
        line.split()[0]
        for line in result.stdout.splitlines()[1:]
        if line.strip()
    }
    return model in installed_models


def ensure_ollama_model() -> None:
    model = _ollama_model()
    try:
        if _is_ollama_model_installed(model):
            print(f"[bootstrap] ollama model already installed: {model}")
            return

        print(f"[bootstrap] pulling ollama model: {model}")
        subprocess.check_call(["ollama", "pull", model], cwd=PROJECT_ROOT, env=_ollama_env())
    except FileNotFoundError:
        print("[bootstrap] warning: ollama command not found. Install Ollama to use /chat/message.")
    except Exception as exc:
        print(f"[bootstrap] warning: could not prepare ollama model '{model}': {exc}")


def run_dev_server() -> None:
    python_path = ensure_venv()
    ensure_ollama_model()
    command = [str(python_path), "-m", "uvicorn", "app.main:app", "--reload"]
    print("[bootstrap] starting server: uvicorn app.main:app --reload")
    subprocess.check_call(command, cwd=PROJECT_ROOT)
