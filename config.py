"""Application configuration and constants."""
from pathlib import Path

# HuggingFace model
REPO_ID = "Qwen/Qwen2.5-Coder-3B-Instruct-GGUF"
MODEL_FILENAME = "qwen2.5-coder-3b-instruct-q4_k_m.gguf"

# Paths
LOCAL_DIR = Path("./models")
MODEL_PATH = LOCAL_DIR / MODEL_FILENAME

# Ensure model directory exists
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

# Database
DB_NAME = "prompt_database.db"
