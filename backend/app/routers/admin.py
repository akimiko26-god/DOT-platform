from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_admin_user
from app.database import get_db
from app.models import Company, Lead, User
from app.presence import is_user_online
from app.schemas import AdminCompanyOut, AdminCompanyUpdate, AdminStatsOut, AdminUserOut, AdminUserUpdate

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsOut)
def platform_stats(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    return AdminStatsOut(
        users_total=db.query(func.count(User.id)).scalar() or 0,
        companies_total=db.query(func.count(Company.id)).scalar() or 0,
        companies_active=db.query(func.count(Company.id)).filter(Company.is_active == True).scalar() or 0,
        leads_total=db.query(func.count(Lead.id)).scalar() or 0,
    )


@router.get("/users", response_model=list[AdminUserOut])
def list_users(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.desc()).limit(200).all()
    return [
        AdminUserOut(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            is_admin=u.is_admin,
            is_active=u.is_active,
            is_online=is_user_online(u),
            last_seen_at=u.last_seen_at,
            created_at=u.created_at,
        )
        for u in users
    ]


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
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


@router.get("/companies", response_model=list[AdminCompanyOut])
def list_companies(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    return db.query(Company).order_by(Company.id.desc()).limit(200).all()


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
    return company
