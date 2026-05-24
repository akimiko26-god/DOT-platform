DEFAULT_CATEGORIES = [
    "Косметика",
    "Одежда",
    "Продукты",
    "Кондитерские изделия",
    "Услуги",
    "Электроника",
    "Для дома",
    "Спорт и отдых",
    "Здоровье",
    "Детские товары",
    "Парфюмерия",
    "Обувь",
]

DEFAULT_TAGS = [
    "для лица",
    "диетическое",
    "для женщин",
    "для мужчин",
    "новинка",
    "хит продаж",
    "со скидкой",
    "премиум",
    "органическое",
    "набор",
    "для тела",
    "веган",
    "без глютена",
]


def seed_catalog_refs(company_id: int, db) -> None:
    from app.models import CatalogCategoryRef, CatalogTagRef

    existing_cats = {
        c.name.lower()
        for c in db.query(CatalogCategoryRef).filter(CatalogCategoryRef.company_id == company_id).all()
    }
    existing_tags = {
        t.name.lower()
        for t in db.query(CatalogTagRef).filter(CatalogTagRef.company_id == company_id).all()
    }
    added = False
    order = len(existing_cats)
    for name in DEFAULT_CATEGORIES:
        if name.lower() not in existing_cats:
            db.add(CatalogCategoryRef(company_id=company_id, name=name, sort_order=order))
            order += 1
            added = True
    order = len(existing_tags)
    for name in DEFAULT_TAGS:
        if name.lower() not in existing_tags:
            db.add(CatalogTagRef(company_id=company_id, name=name, sort_order=order))
            order += 1
            added = True
    if added:
        db.commit()
