from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.auth import get_company_for_user, get_current_user
from app.database import get_db
from app.models import CompanyMember, Lead, LeadComment, User
from app.permissions import is_owner
from app.schemas import LeadCommentCreate, LeadCommentOut, LeadOut, LeadUpdate

router = APIRouter(prefix="/api/companies/{company_id}/leads", tags=["leads"])


def _comment_out(c: LeadComment) -> LeadCommentOut:
    return LeadCommentOut(
        id=c.id,
        author_name=c.author_name,
        author_job_title=c.author_job_title or "",
        text=c.text,
        created_at=c.created_at,
    )


@router.get("", response_model=list[LeadOut])
def list_leads(
    company_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    get_company_for_user(company_id, user, db, module="leads")
    leads = (
        db.query(Lead)
        .options(joinedload(Lead.comments))
        .filter(Lead.company_id == company_id)
        .order_by(Lead.created_at.desc())
        .all()
    )
    result = []
    for lead in leads:
        result.append(
            LeadOut(
                id=lead.id,
                client_name=lead.client_name,
                client_phone=lead.client_phone,
                client_email=lead.client_email,
                message=lead.message,
                source=lead.source,
                status=lead.status,
                created_at=lead.created_at,
                updated_at=lead.updated_at,
                comments=[_comment_out(c) for c in lead.comments],
            )
        )
    return result


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(
    company_id: int,
    lead_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="leads")
    lead = (
        db.query(Lead)
        .options(joinedload(Lead.comments))
        .filter(Lead.id == lead_id, Lead.company_id == company_id)
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return LeadOut(
        id=lead.id,
        client_name=lead.client_name,
        client_phone=lead.client_phone,
        client_email=lead.client_email,
        message=lead.message,
        source=lead.source,
        status=lead.status,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
        comments=[_comment_out(c) for c in lead.comments],
    )


@router.patch("/{lead_id}", response_model=LeadOut)
def update_lead(
    company_id: int,
    lead_id: int,
    data: LeadUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="leads")
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.company_id == company_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(lead, key, value)
    db.commit()
    return get_lead(company_id, lead_id, user, db)


@router.post("/{lead_id}/comments", response_model=LeadCommentOut, status_code=201)
def add_comment(
    company_id: int,
    lead_id: int,
    data: LeadCommentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(company_id, user, db, module="leads")
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.company_id == company_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    job_title = ""
    if is_owner(user, company):
        job_title = "Директор"
    else:
        member = (
            db.query(CompanyMember)
            .filter(CompanyMember.company_id == company_id, CompanyMember.user_id == user.id)
            .first()
        )
        if member:
            job_title = member.job_title or member.role
    if user.job_title:
        job_title = user.job_title

    comment = LeadComment(
        lead_id=lead.id,
        user_id=user.id,
        text=data.text,
        author_name=user.full_name,
        author_job_title=job_title,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _comment_out(comment)
