"""Единый аудит действий пользователей."""

import json

from app.models import User
from app.sessions import audit


def log_audit(
    db,
    user: User | None,
    action: str,
    entity_type: str = "",
    entity_id: int | None = None,
    details: str = "",
    extra: dict | None = None,
) -> None:
    parts = []
    if entity_id is not None:
        parts.append(f"ID={entity_id}")
    if details:
        parts.append(details)
    if extra:
        parts.append(json.dumps(extra, ensure_ascii=False, default=str)[:800])
    audit(
        db,
        user.id if user else None,
        action,
        entity_type,
        entity_id,
        " | ".join(parts),
    )
