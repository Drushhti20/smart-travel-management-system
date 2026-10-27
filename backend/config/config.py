"""Application configuration settings for Beyond Horizons."""
import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in current folder and parent folder
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
ROOT_DIR = BACKEND_DIR.parent

if (ROOT_DIR / ".env").is_file():
    load_dotenv(ROOT_DIR / ".env")
elif (BACKEND_DIR / ".env").is_file():
    load_dotenv(BACKEND_DIR / ".env")


class Config:
    """Base application configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "beyond-horizons-dev-secret-key-3024801")
    MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
    DB_NAME = os.getenv("DB_NAME", os.getenv("MONGODB_DB", "beyond_horizons")).strip()

    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)

    # Server settings
    PORT = int(os.getenv("PORT", 5000))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    # Directory Paths
    ROOT_PATH = ROOT_DIR
    BACKEND_PATH = BACKEND_DIR
    FRONTEND_PATH = ROOT_DIR / "frontend"
    HTML_PATH = FRONTEND_PATH / "html"
    STATIC_PATH = FRONTEND_PATH
