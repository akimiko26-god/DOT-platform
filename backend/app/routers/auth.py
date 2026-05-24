import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.presence import touch_last_seen
from app.config import settings
from app.public_url import public_frontend_url
from app.database import get_db
from app.email_service import send_reset_email
from app.models import Company, CompanyMember, PasswordResetToken, User
from app.permissions import is_owner, user_company_ids
from app.schemas import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserMeOut,
    UserOut,
    UserProfileUpdate,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _membership_perms(company: Company, member: CompanyMember | None, user: User) -> dict:
    if user.is_admin or is_owner(user, company):
        return {
            "leads": True,
            "crm": True,
            "catalog": True,
            "qr": True,
            "settings": True,
            "employees": True,
            "role": "owner",
        }
    if not member:
        return {}
    return {
        "leads": member.perm_leads,
        "crm": member.perm_crm,
        "catalog": member.perm_catalog,
        "qr": member.perm_qr,
        "settings": member.perm_settings,
        "employees": member.perm_employees,
        "role": member.role,
    }


@router.post("/register", response_model=UserOut)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    is_first = db.query(User).count() == 0
    make_admin = is_first or (
        settings.admin_email and data.email.lower() == settings.admin_email.lower()
    )
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        is_admin=make_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    if not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    touch_last_seen(user)
    db.commit()
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token)


@router.post("/ping")
def ping(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    touch_last_seen(user)
    db.commit()
    return {"ok": True}


@router.patch("/me", response_model=UserMeOut)
def update_me(
    data: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.email and data.email != user.email:
        if db.query(User).filter(User.email == data.email, User.id != user.id).first():
            raise HTTPException(status_code=400, detail="Email уже занят")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return me(user, db)


@router.get("/me", response_model=UserMeOut)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    touch_last_seen(user)
    db.commit()
    ids = user_company_ids(user, db)
    companies = db.query(Company).filter(Company.id.in_(ids)).all() if ids else []
    memberships = (
        db.query(CompanyMember).filter(CompanyMember.user_id == user.id).all()
    )
    member_by_company = {m.company_id: m for m in memberships}
    access = []
    for c in companies:
        m = member_by_company.get(c.id)
        access.append(
            {
                "company_id": c.id,
                "company_name": c.name,
                "slug": c.slug,
                "permissions": _membership_perms(c, m, user),
            }
        )
    return UserMeOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone or "",
        avatar_url=user.avatar_url or "",
        job_title=user.job_title or "",
        department=user.department or "",
        is_admin=user.is_admin,
        is_active=user.is_active,
        companies_access=access,
    )


@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    email = data.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user:
        return {"message": "Если этот email зарегистрирован, вы получите письмо со ссылкой"}
    try:
        token = secrets.token_urlsafe(32)
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=datetime.utcnow()
                + timedelta(hours=settings.reset_token_expire_hours),
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Ошибка базы данных. Перезапустите backend (создастся таблица сброса пароля)",
        )
    link = f"{public_frontend_url(request)}/reset-password?token={token}"
    result = send_reset_email(user.email, link)
    resp = {
        "message": result.get("message") or "Если email зарегистрирован, проверьте почту",
        "email_sent": result.get("mode") == "smtp",
    }
    if result.get("dev_reset_link"):
        resp["dev_reset_link"] = result["dev_reset_link"]
    if result.get("error"):
        resp["smtp_error"] = result["error"]
    return resp


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    row = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token == data.token,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.utcnow(),
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=400, detail="Ссылка недействительна или устарела")
    user = db.query(User).filter(User.id == row.user_id).first()
    user.hashed_password = hash_password(data.new_password)
    row.used = True
    db.commit()
    return {"message": "Пароль обновлён"}
