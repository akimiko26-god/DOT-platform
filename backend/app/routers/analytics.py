from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_company_for_user, get_current_user
from app.database import get_db
from app.models import CatalogItem, Customer, Lead, PageView, User
from app.permissions import user_company_ids
from app.schemas import AnalyticsOut

router = APIRouter(prefix="/api/companies/{company_id}/analytics", tags=["analytics"])
overview_router = APIRouter(prefix="/api/analytics", tags=["analytics-overview"])


def _build_analytics(company_id: int, db: Session) -> AnalyticsOut:
    leads = db.query(Lead).filter(Lead.company_id == company_id).all()
    views = db.query(func.count(PageView.id)).filter(PageView.company_id == company_id).scalar() or 0
    customers = db.query(Customer).filter(Customer.company_id == company_id).all()
    repeat = sum(1 for c in customers if c.visit_count > 1)

    status_counter = Counter(l.status.value for l in leads)
    source_counter = Counter(l.source.value for l in leads)
    conversion = round((len(leads) / views * 100), 2) if views else 0.0

    items = db.query(CatalogItem).filter(CatalogItem.company_id == company_id).limit(5).all()
    popular = [{"title": i.title, "category": i.category, "price": i.price} for i in items]

    timeline = []
    for i in range(6, -1, -1):
        day = datetime.utcnow().date() - timedelta(days=i)
        count = sum(1 for l in leads if l.created_at.date() == day)
        timeline.append({"label": day.strftime("%d.%m"), "value": count})

    status_chart = [{"label": k, "value": v} for k, v in status_counter.items()]
    source_chart = [{"label": k, "value": v} for k, v in source_counter.items()]

    return AnalyticsOut(
        total_leads=len(leads),
        leads_by_status=dict(status_counter),
        leads_by_source=dict(source_counter),
        total_customers=len(customers),
        repeat_customers=repeat,
        page_views=views,
        conversion_rate=conversion,
        popular_items=popular,
        leads_timeline=timeline,
        status_chart=status_chart,
        source_chart=source_chart,
    )


@router.get("", response_model=AnalyticsOut)
def get_analytics(
    company_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    get_company_for_user(company_id, user, db)
    return _build_analytics(company_id, db)


@overview_router.get("/overview")
def analytics_overview(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ids = user_company_ids(user, db)
    companies_stats = []
    for cid in ids:
        from app.models import Company

        c = db.query(Company).filter(Company.id == cid).first()
        if not c:
            continue
        a = _build_analytics(cid, db)
        companies_stats.append(
            {
                "company_id": cid,
                "company_name": c.name,
                "total_leads": a.total_leads,
                "total_customers": a.total_customers,
                "conversion_rate": a.conversion_rate,
                "leads_timeline": a.leads_timeline,
            }
        )
    return {"companies": companies_stats}
