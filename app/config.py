import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    BASE_PATH = os.getenv("BASE_PATH", "/file_upload").rstrip("/") or ""
    UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_DIR", "data/uploads")
    DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "data/app.db")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100")) * 1024 * 1024
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
