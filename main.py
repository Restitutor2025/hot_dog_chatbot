#
#  main.py
#  hot_dog_chatbot
#
#  Created by Codex on 2026-05-07.
#  Updated by Codex on 2026-05-07.
#
#  Codex Update Log:
#  - 2026-05-07: Added the root launcher for .venv setup and API server startup.
#
#  God_Zero Update Log:
#  - 2026-05-07: No direct launcher changes; session memory runs inside the chatbot router.
#

from app.bootstrap import run_dev_server


if __name__ == "__main__":
    run_dev_server()
