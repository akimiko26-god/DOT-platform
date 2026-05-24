from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CatalogItem, Company, Customer, Lead, LeadSource, PageView
from app.routers.catalog import _item_out
from app.schemas import CatalogItemOut, CompanyOut, LeadCreate, LeadOut, MessengerLinkOut

router = APIRouter(prefix="/api/public", tags=["public"])


def get_company_by_slug(slug: str, db: Session) -> Company:
    company = db.query(Company).filter(Company.slug == slug, Company.is_active == True).first()
    if not company:
        raise HTTPException(status_code=404, detail="Компания не найдена")
    return company


def track_view(company_id: int, page: str, db: Session):
    db.add(PageView(company_id=company_id, page=page))
    db.commit()


@router.get("/companies/{slug}", response_model=CompanyOut)
def public_company(slug: str, db: Session = Depends(get_db)):
    company = get_company_by_slug(slug, db)
    track_view(company.id, "profile", db)
    return company


@router.get("/companies/{slug}/catalog", response_model=list[CatalogItemOut])
def public_catalog(slug: str, db: Session = Depends(get_db)):
    company = get_company_by_slug(slug, db)
    if not company.module_catalog:
        return []
    track_view(company.id, "catalog", db)
    items = (
        db.query(CatalogItem)
        .filter(
            CatalogItem.company_id == company.id,
            CatalogItem.deleted_at.is_(None),
            CatalogItem.is_published == True,
            CatalogItem.is_available == True,
        )
        .order_by(CatalogItem.sort_order, CatalogItem.id)
        .all()
    )
    return [_item_out(i) for i in items]


@router.post("/companies/{slug}/leads", response_model=LeadOut, status_code=201)
def public_lead(slug: str, data: LeadCreate, db: Session = Depends(get_db)):
    company = get_company_by_slug(slug, db)
    if not company.module_leads:
        raise HTTPException(status_code=403, detail="Приём заявок отключён")
    track_view(company.id, "lead_form", db)

    customer = None
    if data.client_phone or data.client_email:
        q = db.query(Customer).filter(Customer.company_id == company.id)
        if data.client_phone:
            customer = q.filter(Customer.phone == data.client_phone).first()
        if not customer and data.client_email:
            customer = q.filter(Customer.email == data.client_email).first()
        if customer:
            customer.visit_count += 1
        else:
            customer = Customer(
                company_id=company.id,
                name=data.client_name,
                phone=data.client_phone,
                email=data.client_email,
            )
            db.add(customer)
            db.flush()

    lead = Lead(
        company_id=company.id,
        customer_id=customer.id if customer else None,
        client_name=data.client_name,
        client_phone=data.client_phone,
        client_email=data.client_email,
        message=data.message,
        source=data.source,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/companies/{slug}/messenger", response_model=MessengerLinkOut)
def public_messenger(slug: str, message: str = "Здравствуйте!", db: Session = Depends(get_db)):
    company = get_company_by_slug(slug, db)
    encoded = quote(message)
    wa = f"https://wa.me/{company.whatsapp}?text={encoded}" if company.whatsapp else None
    tg = f"https://t.me/{company.telegram}?text={encoded}" if company.telegram else None
    return MessengerLinkOut(whatsapp_url=wa, telegram_url=tg, prefilled_message=message)
