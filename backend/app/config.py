import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent


def _default_frontend_url() -> str:
    url = os.getenv("RENDER_EXTERNAL_URL", "").strip()
    if url:
        return url.rstrip("/")
    host = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
    if host:
        return f"https://{host}"
    return "http://localhost:5173"


class Settings(BaseSettings):
    database_url: str = "sqlite:///./dot_local.db"
    secret_key: str = "change-me-in-production-use-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    frontend_url: str = _default_frontend_url()
    api_public_url: str = _default_frontend_url()
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    mail_from: str = "noreply@dot.kz"
    reset_token_expire_hours: int = 24
    admin_email: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    seed_demo: bool = False

    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
