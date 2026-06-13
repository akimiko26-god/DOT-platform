from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_company_for_user, get_current_user
from app.database import get_db
from app.models import CompanySlide, User
from app.schemas import CompanySlideCreate, CompanySlideOut

router = APIRouter(prefix="/api/companies/{company_id}/slides", tags=["company-slides"])


@router.get("", response_model=list[CompanySlideOut])
def list_slides(
    company_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="settings")
    return (
        db.query(CompanySlide)
        .filter(CompanySlide.company_id == company_id)
        .order_by(CompanySlide.sort_order, CompanySlide.id)
        .all()
    )


@router.post("", response_model=CompanySlideOut, status_code=201)
def add_slide(
    company_id: int,
    data: CompanySlideCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="settings")
    count = db.query(CompanySlide).filter(CompanySlide.company_id == company_id).count()
    if count >= 10:
        raise HTTPException(status_code=400, detail="Максимум 10 слайдов")
    slide = CompanySlide(
        company_id=company_id,
        image_url=data.image_url,
        caption=data.caption,
        sort_order=count,
    )
    db.add(slide)
    db.commit()
    db.refresh(slide)
    return slide


@router.delete("/{slide_id}", status_code=204)
def delete_slide(
    company_id: int,
    slide_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="settings")
    slide = db.query(CompanySlide).filter(
        CompanySlide.id == slide_id, CompanySlide.company_id == company_id
    ).first()
    if not slide:
        raise HTTPException(status_code=404, detail="Слайд не найден")
    db.delete(slide)
    db.commit()
