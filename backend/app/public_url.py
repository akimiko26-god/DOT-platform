import os

from fastapi import Request

from app.config import settings


def _render_external_url() -> str | None:
    url = os.getenv("RENDER_EXTERNAL_URL", "").strip()
    if url:
        return url.rstrip("/")
    host = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
    if host:
        return f"https://{host}"
    return None


def public_frontend_url(request: Request | None = None) -> str:
    deployed = _render_external_url()
    if deployed:
        return deployed
    if request is not None:
        forwarded = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
        host = forwarded.split(",")[0].strip()
        if host and "localhost" not in host and "127.0.0.1" not in host:
            proto = request.headers.get("x-forwarded-proto", request.url.scheme)
            return f"{proto}://{host}".rstrip("/")
    return settings.frontend_url.rstrip("/")
