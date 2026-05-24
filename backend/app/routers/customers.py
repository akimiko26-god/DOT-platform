from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai_insights import generate_customer_insight
from app.auth import get_company_for_user, get_current_user
from app.database import get_db
from app.models import Customer, Lead, User
from app.schemas import CustomerCreate, CustomerDetailOut, CustomerOut, CustomerUpdate

router = APIRouter(prefix="/api/companies/{company_id}/customers", tags=["customers"])


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
    insight_data = generate_customer_insight(customer, leads)
    if not customer.ai_insight:
        customer.ai_insight = insight_data["insight"]
        db.commit()
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
        insight_meta=insight_data,
    )


@router.post("/{customer_id}/refresh-insight")
def refresh_insight(
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
    leads = db.query(Lead).filter(Lead.customer_id == customer.id).all()
    data = generate_customer_insight(customer, leads)
    customer.ai_insight = data["insight"]
    db.commit()
    return data


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
    db.delete(customer)
    db.commit()
