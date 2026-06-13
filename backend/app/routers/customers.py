from fastapi import APIRouter, Body, Depends, HTTPException
import json
from sqlalchemy.orm import Session

from app.ai_insights import ask_customer_advice, generate_customer_insight
from app.audit_helpers import log_audit
from app.auth import get_company_for_user, get_current_user
from app.database import get_db
from app.models import Customer, CustomerInsightLog, Lead, LeadComment, User
from app.schemas import (
    CustomerAskAiIn,
    CustomerCreate,
    CustomerDetailOut,
    CustomerOut,
    CustomerUpdate,
)

router = APIRouter(prefix="/api/companies/{company_id}/customers", tags=["customers"])


def _load_customer_leads(db, company_id: int, customer: Customer) -> list:
    leads = (
        db.query(Lead)
        .filter(Lead.company_id == company_id)
        .filter(
            (Lead.customer_id == customer.id)
            | (Lead.client_phone == customer.phone)
            | (Lead.client_email == customer.email)
        )
        .order_by(Lead.created_at.desc())
        .all()
    )
    for l in leads:
        l.comments = (
            db.query(LeadComment)
            .filter(LeadComment.lead_id == l.id)
            .order_by(LeadComment.created_at)
            .all()
        )
    return leads


@router.get("", response_model=list[CustomerOut])
def list_customers(
    company_id: int,
    q: str = "",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="crm")
    query = db.query(Customer).filter(Customer.company_id == company_id)
    if q:
        query = query.filter(
            (Customer.name.ilike(f"%{q}%"))
            | (Customer.phone.ilike(f"%{q}%"))
            | (Customer.email.ilike(f"%{q}%"))
        )
    return query.order_by(Customer.updated_at.desc()).all()


@router.get("/{customer_id}", response_model=CustomerDetailOut)
def get_customer(
    company_id: int,
    customer_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="crm")
    customer = db.query(Customer).filter(
        Customer.id == customer_id, Customer.company_id == company_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    leads = _load_customer_leads(db, company_id, customer)
    return CustomerDetailOut(
        id=customer.id,
        name=customer.name,
        phone=customer.phone,
        email=customer.email,
        notes=customer.notes,
        is_vip=customer.is_vip,
        visit_count=customer.visit_count,
        ai_insight=customer.ai_insight,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        leads=leads,
        insight_meta={},
    )


@router.post("/{customer_id}/refresh-insight")
def refresh_insight(
    company_id: int,
    customer_id: int,
    card: CustomerUpdate | None = Body(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="crm")
    customer = db.query(Customer).filter(
        Customer.id == customer_id, Customer.company_id == company_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    for key, value in (card.model_dump(exclude_unset=True) if card else {}).items():
        setattr(customer, key, value)
    db.flush()

    leads = _load_customer_leads(db, company_id, customer)
    data = generate_customer_insight(customer, leads)
    customer.ai_insight = data["insight"]
    log_audit(db, user, "refresh_ai_insight", "customer", customer.id, "Обновлён AI-бриф")
    db.add(
        CustomerInsightLog(
            customer_id=customer.id,
            insight_text=data["insight"],
            source=data.get("source", "heuristic"),
            meta_json=json.dumps({k: v for k, v in data.items() if k != "insight"}, default=str),
        )
    )
    db.commit()
    return data


@router.post("/{customer_id}/ask-ai")
def ask_ai(
    company_id: int,
    customer_id: int,
    body: CustomerAskAiIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="crm")
    customer = db.query(Customer).filter(
        Customer.id == customer_id, Customer.company_id == company_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    leads = _load_customer_leads(db, company_id, customer)
    result = ask_customer_advice(customer, leads, body.question, customer.ai_insight or "")
    log_audit(db, user, "ask_ai", "customer", customer.id, body.question[:200])
    db.commit()
    return result


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(
    company_id: int,
    data: CustomerCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="crm")
    customer = Customer(company_id=company_id, **data.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    log_audit(db, user, "create", "customer", customer.id, customer.name)
    db.commit()
    return customer


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(
    company_id: int,
    customer_id: int,
    data: CustomerUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="crm")
    customer = db.query(Customer).filter(
        Customer.id == customer_id, Customer.company_id == company_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    db.commit()
    db.refresh(customer)
    log_audit(db, user, "update", "customer", customer.id, "Изменена карточка")
    db.commit()
    return customer


@router.delete("/{customer_id}", status_code=204)
def delete_customer(
    company_id: int,
    customer_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="crm")
    customer = db.query(Customer).filter(
        Customer.id == customer_id, Customer.company_id == company_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    log_audit(db, user, "delete", "customer", customer.id, customer.name)
    db.delete(customer)
    db.commit()
