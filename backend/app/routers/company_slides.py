from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.audit_helpers import log_audit
from app.auth import get_company_for_user, get_current_user
from app.database import get_db
from app.models import CompanySlide, User
from app.schemas import CompanySlideCreate, CompanySlideOut, CompanySlidesReplace

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


@router.put("", response_model=list[CompanySlideOut])
def replace_slides(
    company_id: int,
    data: CompanySlidesReplace,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="settings")
    if len(data.slides) > 10:
        raise HTTPException(status_code=400, detail="Максимум 10 слайдов")
    db.query(CompanySlide).filter(CompanySlide.company_id == company_id).delete()
    out = []
    for idx, s in enumerate(data.slides):
        slide = CompanySlide(
            company_id=company_id,
            image_url=s.image_url,
            caption=s.caption or "",
            sort_order=idx,
        )
        db.add(slide)
        out.append(slide)
    log_audit(db, user, "replace", "company_slides", company_id, f"Слайдов: {len(out)}")
    db.commit()
    for slide in out:
        db.refresh(slide)
    return out
