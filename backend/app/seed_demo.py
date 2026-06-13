"""Демо-данные для презентации платформы."""

import json
import os

from app.auth import hash_password
from app.catalog_seed import seed_catalog_refs
from app.seed_demo_extras import _img_for
from app.models import (
    CatalogFolder,
    CatalogItem,
    Company,
    CompanyMember,
    CompanySlide,
    Customer,
    Lead,
    LeadSource,
    LeadStatus,
    User,
)


def seed_demo_data(db) -> None:
    if db.query(Company).filter(Company.slug.in_(["demo-cafe", "demo-beauty", "demo-auto"])).first():
        return

    owner = db.query(User).filter(User.email == "demo@dot.kz").first()
    if not owner:
        owner = User(
            email="demo@dot.kz",
            hashed_password=hash_password("Demo2026!"),
            full_name="Демо Владелец",
            phone="+77001112233",
            job_title="Директор",
            is_admin=False,
            is_active=True,
        )
        db.add(owner)
        db.flush()

    emp = db.query(User).filter(User.email == "manager@dot.kz").first()
    if not emp:
        emp = User(
            email="manager@dot.kz",
            hashed_password=hash_password("Demo2026!"),
            full_name="Айгуль Менеджер",
            phone="+77005556677",
            job_title="Менеджер по продажам",
            department="CRM",
            is_active=True,
        )
        db.add(emp)
        db.flush()

    companies_data = [
        {
            "slug": "demo-cafe",
            "name": "Кофейня «Алма»",
            "description": "Уютная кофейня в центре Алматы.\n\nМы готовим specialty-кофе, авторские десерты и завтраки.\nРаботаем с 08:00 до 22:00 без выходных.",
            "activities": "Кофе на зернах\nДесерты ручной работы\nКейтеринг\nДоставка по городу",
            "phone": "+77001234567",
            "email": "hello@alma-cafe.kz",
            "address": "г. Алматы, ул. Абая 150",
            "work_schedule": "Пн–Вс 08:00–22:00",
            "whatsapp": "77001234567",
            "telegram": "almacafe",
            "logo": "https://placehold.co/200x200/3d9cf5/ffffff?text=Alma",
            "slides": [
                ("https://placehold.co/1200x480/1a2332/3d9cf5?text=Specialty+Coffee", "Авторский кофе"),
                ("https://placehold.co/1200x480/243044/e8edf4?text=Breakfast", "Завтраки"),
                ("https://placehold.co/1200x480/2563a8/ffffff?text=Desserts", "Десерты"),
            ],
            "items": [
                ("Капучино", "Классический капучино 250 мл", "Напитки", 1890),
                ("Чизкейк Нью-Йорк", "Нежный чизкейк с ягодным соусом", "Десерты", 2490),
                ("Завтрак «Алма»", "Яйца, авокадо, тост, сок", "Завтраки", 3990),
            ],
        },
        {
            "slug": "demo-beauty",
            "name": "Салон «Glow»",
            "description": "Премиальный салон красоты.\n\nСтрижки, окрашивание, уход за кожей и маникюр.\nИндивидуальный подход к каждому клиенту.",
            "activities": "Парикмахерские услуги\nКосметология\nМаникюр и педикюр",
            "phone": "+77007654321",
            "email": "info@glow.kz",
            "address": "г. Алматы, пр. Достык 89",
            "work_schedule": "Пн–Сб 10:00–20:00",
            "logo": "https://placehold.co/200x200/a855f7/ffffff?text=Glow",
            "slides": [
                ("https://placehold.co/1200x480/2b1d3a/a855f7?text=Hair+Studio", "Стрижки и окрашивание"),
                ("https://placehold.co/1200x480/1e293b/ec4899?text=Spa", "SPA-уход"),
            ],
            "items": [
                ("Стрижка женская", "Модельная стрижка + укладка", "Услуги", 8500),
                ("Маникюр классический", "С покрытием гель-лак", "Услуги", 6500),
                ("Пилинг лица", "Профессиональный уход", "Косметология", 12000),
            ],
        },
        {
            "slug": "demo-auto",
            "name": "Автосервис «Drive»",
            "description": "Полный цикл обслуживания автомобилей.\n\nДиагностика, ТО, ремонт подвески и электрики.\nГарантия на все виды работ.",
            "activities": "Техническое обслуживание\nРемонт\nДиагностика\nШиномонтаж",
            "phone": "+77009876543",
            "email": "service@drive.kz",
            "address": "г. Алматы, ул. Райымбека 45",
            "work_schedule": "Пн–Сб 09:00–19:00",
            "logo": "https://placehold.co/200x200/e8b84a/1a1200?text=Drive",
            "slides": [
                ("https://placehold.co/1200x480/0f1419/e8b84a?text=Auto+Service", "Профессиональный сервис"),
            ],
            "items": [
                ("Замена масла", "Масло + фильтр + работа", "ТО", 15000),
                ("Диагностика ходовой", "Полная проверка подвески", "Диагностика", 5000),
                ("Шиномонтаж R16", "Балансировка 4 колёс", "Шины", 8000),
            ],
        },
    ]

    for idx, cd in enumerate(companies_data):
        company = Company(
            slug=cd["slug"],
            name=cd["name"],
            description=cd["description"],
            activities=cd["activities"],
            phone=cd["phone"],
            email=cd["email"],
            address=cd["address"],
            work_schedule=cd.get("work_schedule", ""),
            whatsapp=cd.get("whatsapp", ""),
            telegram=cd.get("telegram", ""),
            logo_url=cd.get("logo", ""),
            owner_id=owner.id,
            director_name=owner.full_name,
            bin_iin=f"990{idx:05d}000001",
        )
        db.add(company)
        db.flush()
        seed_catalog_refs(company.id, db)

        for si, (img, cap) in enumerate(cd.get("slides", [])):
            db.add(CompanySlide(company_id=company.id, image_url=img, caption=cap, sort_order=si))

        folder = CatalogFolder(company_id=company.id, name="Основное")
        db.add(folder)
        db.flush()

        for ti, (title, desc, cat, price) in enumerate(cd["items"]):
            db.add(
                CatalogItem(
                    company_id=company.id,
                    folder_id=folder.id,
                    title=title,
                    description=desc,
                    category=cat,
                    tags=json.dumps(["хит продаж"] if ti == 0 else []),
                    price=price,
                    image_url=_img_for(title),
                    is_published=True,
                    is_available=True,
                    sort_order=ti,
                )
            )

        customer = Customer(
            company_id=company.id,
            name="Асхат Нурланов",
            phone="+77001112233",
            email="asxat@mail.kz",
            notes="Постоянный клиент.\nПредпочитает связь в WhatsApp.",
            visit_count=3,
            is_vip=idx == 0,
        )
        db.add(customer)
        db.flush()

        db.add(
            Lead(
                company_id=company.id,
                customer_id=customer.id,
                client_name=customer.name,
                client_phone=customer.phone,
                client_email=customer.email,
                message="Интересует ваш каталог.\nХотел бы уточнить цены и сроки.",
                source=LeadSource.qr if idx == 0 else LeadSource.website,
                status=LeadStatus.in_progress if idx == 0 else LeadStatus.done,
            )
        )

        if idx == 0:
            db.add(
                CompanyMember(
                    company_id=company.id,
                    user_id=emp.id,
                    role="employee",
                    perm_leads=True,
                    perm_crm=True,
                    perm_catalog=True,
                    perm_qr=True,
                )
            )

    db.commit()
