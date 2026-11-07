import os
from pathlib import Path
from dotenv import load_dotenv

# Load Backend/.env if it exists
_env_file = Path(__file__).resolve().parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file)

def _get_bool(key: str, default: bool) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in ("true", "1", "yes", "y", "t", "on")

def _get_float(key: str, default: float) -> float:
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return float(val.strip())
    except ValueError:
        return default

def _get_int(key: str, default: int) -> int:
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val.strip())
    except ValueError:
        return default

class Config:
    # --- Google Gemini ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    GEMINI_ENABLED: bool = _get_bool("GEMINI_ENABLED", True)
    GEMINI_TIMEOUT: float = _get_float("GEMINI_TIMEOUT", 15.0)

    # --- Groq ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    GROQ_ENABLED: bool = _get_bool("GROQ_ENABLED", True)
    GROQ_TIMEOUT: float = _get_float("GROQ_TIMEOUT", 15.0)

    # --- OpenRouter ---
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "").strip()
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct").strip()
    OPENROUTER_ENABLED: bool = _get_bool("OPENROUTER_ENABLED", True)
    OPENROUTER_TIMEOUT: float = _get_float("OPENROUTER_TIMEOUT", 15.0)

    # --- Concurrent Racing & Reliability Settings ---
    PROVIDER_MAX_RETRIES: int = _get_int("PROVIDER_MAX_RETRIES", 1)
    PROVIDER_COOLDOWN_SECONDS: float = _get_float("PROVIDER_COOLDOWN_SECONDS", 60.0)
    PROVIDER_CONCURRENCY_LIMIT: int = _get_int("PROVIDER_CONCURRENCY_LIMIT", 3)
    PROVIDER_OVERALL_TIMEOUT: float = _get_float("PROVIDER_OVERALL_TIMEOUT", 30.0)

    # --- Firebase ---
    FIREBASE_SERVICE_ACCOUNT_PATH: str = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_PATH",
        r"D:\PythonProject\QuizWise-Secrets\serviceAccountKey.json"
    ).strip()

config = Config()

