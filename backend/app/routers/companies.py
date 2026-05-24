from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_company_for_user, get_current_user
from app.database import get_db
from app.models import Company, User
from app.permissions import user_company_ids
from app.schemas import CompanyCreate, CompanyOut, CompanyUpdate

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=list[CompanyOut])
def list_companies(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ids = user_company_ids(user, db)
    if not ids:
        return []
    return db.query(Company).filter(Company.id.in_(ids)).order_by(Company.id).all()


@router.post("", response_model=CompanyOut, status_code=201)
def create_company(
    data: CompanyCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if db.query(Company).filter(Company.slug == data.slug).first():
        raise HTTPException(status_code=400, detail="Slug уже занят")
    company = Company(**data.model_dump(), owner_id=user.id)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(
    company_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return get_company_for_user(company_id, user, db)


@router.patch("/{company_id}", response_model=CompanyOut)
def update_company(
    company_id: int,
    data: CompanyUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(company_id, user, db, module="settings")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return company
