import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/jansahayak"
)

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2"
)

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "jansahayak-secret-key"
)

UPLOAD_FOLDER = "documents"

MAX_FILE_SIZE = 10 * 1024 * 1024
