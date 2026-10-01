"""Application configuration and constants."""
import sys
from pathlib import Path


def _get_app_dir() -> Path:
    """Return the directory where the app lives (exe folder or project folder)."""
    if getattr(sys, "frozen", False):
        # Running as a .exe – put models/ and db next to the executable
        return Path(sys.executable).parent
    return Path(__file__).parent.resolve()


def _get_resource_path(relative: str) -> Path:
    """Return path to a bundled resource (works in dev AND frozen mode)."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)  # temp extraction folder
    else:
        base = Path(__file__).parent.resolve()
    return base / relative


# --- Runtime dir (models, db live here, next to the .exe) ---
APP_DIR = _get_app_dir()

# --- Bundled resources (icon lives inside the .exe) ---
def resource_path(name: str) -> Path:
    return _get_resource_path(name)


# --- HuggingFace model ---
#REPO_ID        = "Qwen/Qwen2.5-Coder-3B-Instruct-GGUF"
#MODEL_FILENAME = "qwen2.5-coder-3b-instruct-q4_k_m.gguf"

REPO_ID = "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
MODEL_FILENAME = "qwen2.5-coder-7b-instruct-q4_k_m.gguf"

# --- Paths ---
MODELS_DIR = APP_DIR / "models"
MODEL_PATH = MODELS_DIR / MODEL_FILENAME
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# --- Database ---
DB_NAME = str(APP_DIR / "prompt_database.db")
