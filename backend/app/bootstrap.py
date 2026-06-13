"""Создание системного супер-админа и демо-данных при старте."""

from app.auth import hash_password
from app.config import settings
from app.models import User

SUPERADMIN_EMAIL = "superadmin@dot.kz"
SUPERADMIN_PASSWORD = "DotSuper2026!"


def ensure_superadmin(db) -> None:
    email = (settings.admin_email or SUPERADMIN_EMAIL).strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user:
        if not user.is_admin:
            user.is_admin = True
        if not user.is_active:
            user.is_active = True
        db.commit()
        return
    db.add(
        User(
            email=email,
            hashed_password=hash_password(SUPERADMIN_PASSWORD),
            full_name="Супер-администратор",
            is_admin=True,
            is_active=True,
        )
    )
    db.commit()


def ensure_demo_data(db) -> None:
    from app.seed_demo import seed_demo_data

    seed_demo_data(db)
