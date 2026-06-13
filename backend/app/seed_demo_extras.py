"""Дополнительные демо-данные для графиков и каталога с картинками."""

import json
import random
from datetime import datetime, timedelta

from app.models import (
    CatalogItem,
    Company,
    Customer,
    Lead,
    LeadComment,
    LeadSource,
    LeadStatus,
    PageView,
    User,
)

STATUS_CYCLE = [
    LeadStatus.new,
    LeadStatus.in_progress,
    LeadStatus.waiting,
    LeadStatus.done,
    LeadStatus.cancelled,
]
SOURCE_CYCLE = [
    LeadSource.qr,
    LeadSource.website,
    LeadSource.form,
    LeadSource.whatsapp,
    LeadSource.telegram,
]

PRODUCT_IMAGES = {
    "Капучино": "https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=400&h=300&fit=crop",
    "Чизкейк": "https://images.unsplash.com/photo-1524351199678-941a58a3df50?w=400&h=300&fit=crop",
    "Завтрак": "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=400&h=300&fit=crop",
    "Стрижка": "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=400&h=300&fit=crop",
    "Маникюр": "https://images.unsplash.com/photo-1604654894610-df63bc536371?w=400&h=300&fit=crop",
    "Пилинг": "https://images.unsplash.com/photo-1616394584738-fc6e612e71b9?w=400&h=300&fit=crop",
    "масла": "https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?w=400&h=300&fit=crop",
    "Диагностика": "https://images.unsplash.com/photo-1487754180441-d069ca3a50c5?w=400&h=300&fit=crop",
    "Шиномонтаж": "https://images.unsplash.com/photo-1619642751034-765df0367c46?w=400&h=300&fit=crop",
}


def _img_for(title: str) -> str:
    for key, url in PRODUCT_IMAGES.items():
        if key.lower() in title.lower():
            return url
    return f"https://picsum.photos/seed/{abs(hash(title)) % 9999}/400/300"


def ensure_demo_extras(db) -> None:
    companies = db.query(Company).filter(Company.slug.like("demo-%")).all()
    if not companies:
        return
    if db.query(Lead).count() >= 40:
        return

    manager = db.query(User).filter(User.email == "manager@dot.kz").first()
    now = datetime.utcnow()

    for company in companies:
        items = db.query(CatalogItem).filter(CatalogItem.company_id == company.id).all()
        for item in items:
            if not item.image_url:
                item.image_url = _img_for(item.title)

        existing_leads = db.query(Lead).filter(Lead.company_id == company.id).count()
        for i in range(max(0, 12 - existing_leads)):
            days_ago = random.randint(0, 45)
            created = now - timedelta(days=days_ago, hours=random.randint(0, 12))
            status = STATUS_CYCLE[i % len(STATUS_CYCLE)]
            source = SOURCE_CYCLE[i % len(SOURCE_CYCLE)]
            lead = Lead(
                company_id=company.id,
                client_name=f"Клиент {company.slug}-{i + 1}",
                client_phone=f"+7700{random.randint(1000000, 9999999)}",
                client_email=f"client{i}@example.kz",
                message=f"Обращение #{i + 1}.\nИнтересует услуга компании {company.name}.",
                source=source,
                status=status,
                created_at=created,
            )
            db.add(lead)
            db.flush()
            if manager and status in (LeadStatus.in_progress, LeadStatus.waiting):
                db.add(
                    LeadComment(
                        lead_id=lead.id,
                        user_id=manager.id,
                        author_name=manager.full_name,
                        author_job_title=manager.job_title or "Менеджер",
                        text="Связались с клиентом, ждём ответ.",
                        created_at=created + timedelta(hours=2),
                    )
                )

        if db.query(PageView).filter(PageView.company_id == company.id).count() < 30:
            pages = ["profile", "catalog", "lead", "contacts"]
            for _ in range(35):
                db.add(
                    PageView(
                        company_id=company.id,
                        page=random.choice(pages),
                        created_at=now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23)),
                    )
                )

        if db.query(Customer).filter(Customer.company_id == company.id).count() < 4:
            for j in range(3):
                db.add(
                    Customer(
                        company_id=company.id,
                        name=f"Демо-клиент {j + 1}",
                        phone=f"+7705{random.randint(1000000, 9999999)}",
                        email=f"demo{j}@mail.kz",
                        notes="Тестовый клиент для CRM.",
                        visit_count=random.randint(1, 5),
                        is_vip=j == 0,
                    )
                )

    db.commit()
