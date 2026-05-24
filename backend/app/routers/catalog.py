import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import get_company_for_user, get_current_user, get_admin_user
from app.database import get_db
from app.catalog_seed import seed_catalog_refs
from app.models import CatalogCategoryRef, CatalogFolder, CatalogItem, CatalogTagRef, Company, User
from app.schemas import (
    CatalogBulkIds,
    CatalogBulkMove,
    CatalogBulkPublish,
    CatalogFolderCreate,
    CatalogFolderOut,
    CatalogItemCreate,
    CatalogItemOut,
    CatalogItemUpdate,
    CatalogRefOut,
    RefNameCreate,
)

router = APIRouter(prefix="/api/companies/{company_id}/catalog", tags=["catalog"])


def _item_out(item: CatalogItem) -> CatalogItemOut:
    tags = []
    try:
        tags = json.loads(item.tags or "[]")
    except json.JSONDecodeError:
        tags = []
    return CatalogItemOut(
        id=item.id,
        folder_id=item.folder_id,
        title=item.title,
        description=item.description,
        category=item.category,
        tags=tags,
        price=item.price,
        image_url=item.image_url,
        is_available=item.is_available,
        is_published=getattr(item, "is_published", True),
        deleted_at=item.deleted_at,
        sort_order=item.sort_order,
    )


def _dump_tags(tags: list[str]) -> str:
    return json.dumps(tags or [], ensure_ascii=False)


def _category_full_name(row: CatalogCategoryRef, db: Session) -> str:
    if not row.parent_id:
        return row.name
    parent = db.query(CatalogCategoryRef).filter(CatalogCategoryRef.id == row.parent_id).first()
    if parent:
        return f"{parent.name} — {row.name}"
    return row.name


def _category_out(row: CatalogCategoryRef, db: Session) -> CatalogRefOut:
    return CatalogRefOut(
        id=row.id,
        name=row.name,
        parent_id=row.parent_id,
        full_name=_category_full_name(row, db),
        sort_order=row.sort_order,
    )


@router.get("/items", response_model=list[CatalogItemOut])
def list_items(
    company_id: int,
    q: str = "",
    tag: str = "",
    category: str = "",
    folder_id: int | None = None,
    status: str = Query("active", description="active|hidden|trash|all"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="catalog")
    query = db.query(CatalogItem).filter(CatalogItem.company_id == company_id)
    if status == "trash":
        query = query.filter(CatalogItem.deleted_at.isnot(None))
    elif status == "all":
        query = query.filter(CatalogItem.deleted_at.is_(None))
    elif status == "hidden":
        query = query.filter(CatalogItem.deleted_at.is_(None), CatalogItem.is_published == False)
    else:
        query = query.filter(CatalogItem.deleted_at.is_(None), CatalogItem.is_available == True)
    if folder_id is not None:
        query = query.filter(CatalogItem.folder_id == folder_id)
    if category:
        query = query.filter(CatalogItem.category.ilike(f"%{category}%"))
    if tag:
        query = query.filter(CatalogItem.tags.ilike(f"%{tag}%"))
    if q:
        query = query.filter(
            (CatalogItem.title.ilike(f"%{q}%")) | (CatalogItem.description.ilike(f"%{q}%"))
        )
    items = query.order_by(CatalogItem.sort_order, CatalogItem.id).all()
    return [_item_out(i) for i in items]


@router.get("", response_model=list[CatalogItemOut])
def list_items_legacy(company_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_items(company_id, user=user, db=db)


@router.get("/folders", response_model=list[CatalogFolderOut])
def list_folders(
    company_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    get_company_for_user(company_id, user, db, module="catalog")
    return (
        db.query(CatalogFolder)
        .filter(CatalogFolder.company_id == company_id)
        .order_by(CatalogFolder.sort_order, CatalogFolder.id)
        .all()
    )


@router.get("/refs/categories", response_model=list[CatalogRefOut])
def list_categories(
    company_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    get_company_for_user(company_id, user, db, module="catalog")
    seed_catalog_refs(company_id, db)
    rows = (
        db.query(CatalogCategoryRef)
        .filter(CatalogCategoryRef.company_id == company_id)
        .order_by(CatalogCategoryRef.sort_order, CatalogCategoryRef.name)
        .all()
    )
    return [_category_out(r, db) for r in rows]


@router.post("/refs/categories", response_model=CatalogRefOut, status_code=201)
def create_category(
    company_id: int,
    data: RefNameCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="catalog")
    name = data.name.strip()
    parent_id = data.parent_id
    if parent_id:
        parent = db.query(CatalogCategoryRef).filter(
            CatalogCategoryRef.id == parent_id,
            CatalogCategoryRef.company_id == company_id,
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Родительская категория не найдена")
    q = db.query(CatalogCategoryRef).filter(
        CatalogCategoryRef.company_id == company_id,
        CatalogCategoryRef.name == name,
    )
    if parent_id:
        q = q.filter(CatalogCategoryRef.parent_id == parent_id)
    else:
        q = q.filter(CatalogCategoryRef.parent_id.is_(None))
    existing = q.first()
    if existing:
        return _category_out(existing, db)
    row = CatalogCategoryRef(company_id=company_id, name=name, parent_id=parent_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _category_out(row, db)


@router.delete("/refs/categories/{ref_id}", status_code=204)
def delete_category(
    company_id: int, ref_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    get_company_for_user(company_id, user, db, module="catalog")
    row = db.query(CatalogCategoryRef).filter(
        CatalogCategoryRef.id == ref_id, CatalogCategoryRef.company_id == company_id
    ).first()
    if row:
        db.delete(row)
        db.commit()


@router.get("/refs/tags", response_model=list[CatalogRefOut])
def list_tags(
    company_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    get_company_for_user(company_id, user, db, module="catalog")
    seed_catalog_refs(company_id, db)
    return (
        db.query(CatalogTagRef)
        .filter(CatalogTagRef.company_id == company_id)
        .order_by(CatalogTagRef.sort_order, CatalogTagRef.name)
        .all()
    )


@router.post("/refs/tags", response_model=CatalogRefOut, status_code=201)
def create_tag(
    company_id: int,
    data: RefNameCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="catalog")
    name = data.name.strip()
    existing = (
        db.query(CatalogTagRef)
        .filter(CatalogTagRef.company_id == company_id, CatalogTagRef.name == name)
        .first()
    )
    if existing:
        return existing
    row = CatalogTagRef(company_id=company_id, name=name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/refs/tags/{ref_id}", status_code=204)
def delete_tag(
    company_id: int, ref_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    get_company_for_user(company_id, user, db, module="catalog")
    row = db.query(CatalogTagRef).filter(
        CatalogTagRef.id == ref_id, CatalogTagRef.company_id == company_id
    ).first()
    if row:
        db.delete(row)
        db.commit()


@router.post("/folders", response_model=CatalogFolderOut, status_code=201)
def create_folder(
    company_id: int,
    data: CatalogFolderCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="catalog")
    folder = CatalogFolder(company_id=company_id, **data.model_dump())
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@router.patch("/folders/{folder_id}", response_model=CatalogFolderOut)
def update_folder(
    company_id: int,
    folder_id: int,
    data: CatalogFolderCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="catalog")
    folder = db.query(CatalogFolder).filter(
        CatalogFolder.id == folder_id, CatalogFolder.company_id == company_id
    ).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Папка не найдена")
    folder.name = data.name
    folder.sort_order = data.sort_order
    db.commit()
    db.refresh(folder)
    return folder


@router.delete("/folders/{folder_id}", status_code=204)
def delete_folder(
    company_id: int,
    folder_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="catalog")
    folder = db.query(CatalogFolder).filter(
        CatalogFolder.id == folder_id, CatalogFolder.company_id == company_id
    ).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Папка не найдена")
    db.query(CatalogItem).filter(CatalogItem.folder_id == folder_id).update({"folder_id": None})
    db.delete(folder)
    db.commit()


@router.post("/items", response_model=CatalogItemOut, status_code=201)
def create_item(
    company_id: int,
    data: CatalogItemCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="catalog")
    payload = data.model_dump()
    payload["tags"] = _dump_tags(payload.pop("tags", []))
    item = CatalogItem(company_id=company_id, **payload)
    db.add(item)
    db.commit()
    db.refresh(item)
    return _item_out(item)


@router.post("", response_model=CatalogItemOut, status_code=201)
def create_item_legacy(
    company_id: int,
    data: CatalogItemCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_item(company_id, data, user, db)


@router.patch("/{item_id}", response_model=CatalogItemOut)
def update_item_legacy(
    company_id: int,
    item_id: int,
    data: CatalogItemUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_item(company_id, item_id, data, user, db)


@router.patch("/items/{item_id}", response_model=CatalogItemOut)
def update_item(
    company_id: int,
    item_id: int,
    data: CatalogItemUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="catalog")
    item = db.query(CatalogItem).filter(
        CatalogItem.id == item_id, CatalogItem.company_id == company_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    payload = data.model_dump(exclude_unset=True)
    if "tags" in payload:
        payload["tags"] = _dump_tags(payload["tags"])
    for key, value in payload.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return _item_out(item)


@router.patch("/items/{item_id}/move", response_model=CatalogItemOut)
def move_item(
    company_id: int,
    item_id: int,
    folder_id: int | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="catalog")
    item = db.query(CatalogItem).filter(
        CatalogItem.id == item_id, CatalogItem.company_id == company_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    if folder_id:
        folder = db.query(CatalogFolder).filter(
            CatalogFolder.id == folder_id, CatalogFolder.company_id == company_id
        ).first()
        if not folder:
            raise HTTPException(status_code=404, detail="Папка не найдена")
    item.folder_id = folder_id
    db.commit()
    db.refresh(item)
    return _item_out(item)


@router.delete("/items/{item_id}", status_code=204)
def delete_item(
    company_id: int,
    item_id: int,
    permanent: bool = Query(False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="catalog")
    item = db.query(CatalogItem).filter(
        CatalogItem.id == item_id, CatalogItem.company_id == company_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    if permanent:
        db.delete(item)
    else:
        item.deleted_at = datetime.utcnow()
    db.commit()


@router.post("/items/{item_id}/restore", response_model=CatalogItemOut)
def restore_item(
    company_id: int,
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="catalog")
    item = db.query(CatalogItem).filter(
        CatalogItem.id == item_id, CatalogItem.company_id == company_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    item.deleted_at = None
    db.commit()
    db.refresh(item)
    return _item_out(item)


@router.post("/items/bulk-delete", status_code=204)
def bulk_delete_items(
    company_id: int,
    data: CatalogBulkIds,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="catalog")
    now = datetime.utcnow()
    db.query(CatalogItem).filter(
        CatalogItem.company_id == company_id,
        CatalogItem.id.in_(data.ids),
    ).update({"deleted_at": now}, synchronize_session=False)
    db.commit()


@router.post("/items/bulk-restore")
def bulk_restore_items(
    company_id: int,
    data: CatalogBulkIds,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="catalog")
    db.query(CatalogItem).filter(
        CatalogItem.company_id == company_id,
        CatalogItem.id.in_(data.ids),
    ).update({"deleted_at": None}, synchronize_session=False)
    db.commit()
    return {"restored": len(data.ids)}


@router.post("/items/bulk-move")
def bulk_move_items(
    company_id: int,
    data: CatalogBulkMove,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="catalog")
    if data.folder_id:
        folder = db.query(CatalogFolder).filter(
            CatalogFolder.id == data.folder_id, CatalogFolder.company_id == company_id
        ).first()
        if not folder:
            raise HTTPException(status_code=404, detail="Папка не найдена")
    db.query(CatalogItem).filter(
        CatalogItem.company_id == company_id,
        CatalogItem.id.in_(data.ids),
    ).update({"folder_id": data.folder_id}, synchronize_session=False)
    db.commit()
    return {"moved": len(data.ids)}


@router.post("/items/bulk-publish")
def bulk_publish_items(
    company_id: int,
    data: CatalogBulkPublish,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="catalog")
    db.query(CatalogItem).filter(
        CatalogItem.company_id == company_id,
        CatalogItem.id.in_(data.ids),
    ).update({"is_published": data.is_published}, synchronize_session=False)
    db.commit()
    return {"updated": len(data.ids)}


@router.delete("/{item_id}", status_code=204)
def delete_item_legacy(company_id: int, item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return delete_item(company_id, item_id, user, db)


admin_router = APIRouter(prefix="/api/admin/catalog", tags=["admin-catalog"])


@admin_router.get("/items", response_model=list[CatalogItemOut])
def admin_list_catalog(
    company_id: int | None = None,
    q: str = "",
    tag: str = "",
    category: str = "",
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    query = db.query(CatalogItem)
    if company_id:
        query = query.filter(CatalogItem.company_id == company_id)
    if category:
        query = query.filter(CatalogItem.category.ilike(f"%{category}%"))
    if tag:
        query = query.filter(CatalogItem.tags.ilike(f"%{tag}%"))
    if q:
        query = query.filter(
            (CatalogItem.title.ilike(f"%{q}%")) | (CatalogItem.description.ilike(f"%{q}%"))
        )
    return [_item_out(i) for i in query.order_by(CatalogItem.id.desc()).limit(500).all()]
