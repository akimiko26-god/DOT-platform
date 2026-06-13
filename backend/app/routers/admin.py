from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit_helpers import log_audit
from app.auth import get_admin_user, hash_password
from app.database import get_db
from app.models import AuditLog, Company, CompanyMember, Lead, User
from app.presence import is_user_online
from app.schemas import (
    AdminCompanyOut,
    AdminCompanyUpdate,
    AdminResetPasswordIn,
    AdminStatsOut,
    AdminUserCreate,
    AdminUserOut,
    AdminUserUpdate,
    AuditLogOut,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _user_out(db: Session, u: User) -> AdminUserOut:
    memberships = db.query(CompanyMember).filter(CompanyMember.user_id == u.id).all()
    company_ids = [m.company_id for m in memberships]
    names = []
    if company_ids:
        companies = db.query(Company).filter(Company.id.in_(company_ids)).all()
        id_to_name = {c.id: c.name for c in companies}
        names = [id_to_name.get(cid, f"#{cid}") for cid in company_ids]
    owner_ids = db.query(Company.id).filter(Company.owner_id == u.id).all()
    for row in owner_ids:
        if row.id not in company_ids:
            company_ids.append(row.id)
            c = db.query(Company).filter(Company.id == row.id).first()
            if c:
                names.append(c.name + " (владелец)")
    return AdminUserOut(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        is_admin=u.is_admin,
        is_active=u.is_active,
        is_online=is_user_online(u),
        last_seen_at=u.last_seen_at,
        created_at=u.created_at,
        company_ids=company_ids,
        company_names=names,
    )


@router.get("/stats", response_model=AdminStatsOut)
def platform_stats(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    return AdminStatsOut(
        users_total=db.query(func.count(User.id)).scalar() or 0,
        companies_total=db.query(func.count(Company.id)).scalar() or 0,
        companies_active=db.query(func.count(Company.id)).filter(Company.is_active == True).scalar() or 0,
        leads_total=db.query(func.count(Lead.id)).scalar() or 0,
    )


@router.get("/users", response_model=list[AdminUserOut])
def list_users(
    is_admin: str | None = Query(None),
    is_active: str | None = Query(None),
    company_id: int | None = Query(None),
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    q = db.query(User)
    if is_admin in ("true", "1", "yes"):
        q = q.filter(User.is_admin == True)
    elif is_admin in ("false", "0", "no"):
        q = q.filter(User.is_admin == False)
    if is_active in ("true", "1", "yes"):
        q = q.filter(User.is_active == True)
    elif is_active in ("false", "0", "no"):
        q = q.filter(User.is_active == False)
    if company_id:
        member_ids = [
            m.user_id
            for m in db.query(CompanyMember).filter(CompanyMember.company_id == company_id).all()
        ]
        owner = db.query(Company.owner_id).filter(Company.id == company_id).scalar()
        if owner and owner not in member_ids:
            member_ids.append(owner)
        q = q.filter(User.id.in_(member_ids or [-1]))
    users = q.order_by(User.id.desc()).limit(300).all()
    return [_user_out(db, u) for u in users]


@router.post("/users", response_model=AdminUserOut, status_code=201)
def create_user(
    data: AdminUserCreate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email уже занят")
    user = User(
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        is_admin=data.is_admin,
        is_active=data.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_audit(db, admin, "create", "user", user.id, user.email)
    db.commit()
    return _user_out(db, user)


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(
    user_id: int,
    data: AdminUserUpdate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.id == admin.id and data.is_admin is False:
        raise HTTPException(status_code=400, detail="Нельзя снять права с себя")
    if data.email and data.email.lower() != user.email:
        if db.query(User).filter(User.email == data.email.lower()).first():
            raise HTTPException(status_code=400, detail="Email уже занят")
    for key, value in data.model_dump(exclude_unset=True).items():
        if key == "email" and value:
            setattr(user, key, value.lower())
        else:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    log_audit(db, admin, "update", "user", user.id, user.email)
    db.commit()
    return _user_out(db, user)


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: int,
    data: AdminResetPasswordIn,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.hashed_password = hash_password(data.password)
    db.commit()
    log_audit(db, admin, "reset_password", "user", user.id, user.email)
    db.commit()
    return {"ok": True}


@router.get("/companies", response_model=list[AdminCompanyOut])
def list_companies(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    return db.query(Company).order_by(Company.id.desc()).limit(300).all()


@router.patch("/companies/{company_id}", response_model=AdminCompanyOut)
def update_company_admin(
    company_id: int,
    data: AdminCompanyUpdate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Компания не найдена")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(company, key, value)
    db.commit()
    db.refresh(company)
    log_audit(db, admin, "update", "company", company.id, company.name)
    db.commit()
    return company


@router.get("/audit-logs", response_model=list[AuditLogOut])
def list_audit_logs(
    action: str = Query(""),
    entity_type: str = Query(""),
    user_id: int | None = Query(None),
    limit: int = Query(200, le=500),
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action.ilike(f"%{action}%"))
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    rows = q.order_by(AuditLog.id.desc()).limit(limit).all()
    user_map = {}
    ids = {r.user_id for r in rows if r.user_id}
    if ids:
        for u in db.query(User).filter(User.id.in_(ids)).all():
            user_map[u.id] = u.full_name
    return [
        AuditLogOut(
            id=r.id,
            user_id=r.user_id,
            user_name=user_map.get(r.user_id, "—"),
            action=r.action,
            entity_type=r.entity_type or "",
            entity_id=r.entity_id,
            details=r.details or "",
            created_at=r.created_at,
        )
        for r in rows
    ]
