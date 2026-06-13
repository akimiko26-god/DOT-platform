"""Запись сессий и аудит действий."""

import hashlib
from datetime import datetime

from fastapi import Request

from app.models import AuditLog, UserSession


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()[:64]


def record_session(db, user_id: int, token: str, request: Request | None = None) -> None:
    ip = ""
    ua = ""
    if request:
        ip = request.client.host if request.client else ""
        ua = (request.headers.get("user-agent") or "")[:512]
    th = _token_hash(token)
    row = (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id, UserSession.token_hash == th, UserSession.is_active == True)
        .first()
    )
    if row:
        row.last_seen_at = datetime.utcnow()
        if ip:
            row.ip_address = ip
    else:
        db.add(
            UserSession(
                user_id=user_id,
                token_hash=th,
                ip_address=ip,
                user_agent=ua,
            )
        )


def touch_session(db, user_id: int, token: str | None = None) -> None:
    q = db.query(UserSession).filter(UserSession.user_id == user_id, UserSession.is_active == True)
    if token:
        q = q.filter(UserSession.token_hash == _token_hash(token))
    row = q.order_by(UserSession.last_seen_at.desc()).first()
    if row:
        row.last_seen_at = datetime.utcnow()


def audit(db, user_id: int | None, action: str, entity_type: str = "", entity_id: int | None = None, details: str = "") -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details[:2000],
        )
    )
