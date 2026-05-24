from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Company, CompanyMember, User

MODULE_PERM = {
    "leads": "perm_leads",
    "crm": "perm_crm",
    "catalog": "perm_catalog",
    "qr": "perm_qr",
    "settings": "perm_settings",
    "employees": "perm_employees",
}


def user_company_ids(user: User, db: Session) -> list[int]:
    owned = [c.id for c in db.query(Company).filter(Company.owner_id == user.id).all()]
    member = [
        m.company_id
        for m in db.query(CompanyMember)
        .filter(CompanyMember.user_id == user.id, CompanyMember.is_active == True)
        .all()
    ]
    return list(dict.fromkeys(owned + member))


def get_membership(user: User, company_id: int, db: Session) -> CompanyMember | None:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        return None
    if company.owner_id == user.id:
        return None
    return (
        db.query(CompanyMember)
        .filter(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user.id,
            CompanyMember.is_active == True,
        )
        .first()
    )


def is_owner(user: User, company: Company) -> bool:
    return company.owner_id == user.id


def member_has_perm(member: CompanyMember, module: str) -> bool:
    attr = MODULE_PERM.get(module)
    return bool(attr and getattr(member, attr, False))


def require_company_access(
    company_id: int, user: User, db: Session, module: str | None = None
) -> tuple[Company, CompanyMember | None]:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Компания не найдена")
    if not company.is_active and not user.is_admin:
        raise HTTPException(status_code=403, detail="Компания отключена")

    if is_owner(user, company):
        return company, None

    if user.is_admin:
        return company, None

    member = get_membership(user, company_id, db)
    if not member:
        raise HTTPException(status_code=403, detail="Нет доступа к этой компании")

    if module:
        if not member_has_perm(member, module):
            raise HTTPException(status_code=403, detail="Недостаточно прав для этого раздела")
        if module == "crm" and not company.module_crm:
            raise HTTPException(status_code=403, detail="Модуль CRM отключён")
        if module == "catalog" and not company.module_catalog:
            raise HTTPException(status_code=403, detail="Модуль каталога отключён")
        if module == "leads" and not company.module_leads:
            raise HTTPException(status_code=403, detail="Модуль заявок отключён")
        if module == "qr" and not company.module_qr:
            raise HTTPException(status_code=403, detail="Модуль QR отключён")

    return company, member


def require_platform_admin(user: User) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Только для администратора платформы")
    return user
