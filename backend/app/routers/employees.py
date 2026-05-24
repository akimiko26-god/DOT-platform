from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.auth import get_company_for_user, get_current_user, hash_password
from app.database import get_db
from app.models import CompanyMember, User
from app.permissions import is_owner
from app.presence import is_user_online
from app.schemas import EmployeeBulkIds, EmployeeCreate, EmployeeOut, EmployeeUpdate

router = APIRouter(prefix="/api/companies/{company_id}/employees", tags=["employees"])


def _to_out(member: CompanyMember) -> EmployeeOut:
    u = member.user
    return EmployeeOut(
        id=member.id,
        user_id=u.id,
        email=u.email,
        full_name=u.full_name,
        phone=member.phone or u.phone,
        job_title=member.job_title,
        department=member.department,
        role=member.role,
        perm_leads=member.perm_leads,
        perm_crm=member.perm_crm,
        perm_catalog=member.perm_catalog,
        perm_qr=member.perm_qr,
        perm_settings=member.perm_settings,
        perm_employees=member.perm_employees,
        is_active=member.is_active,
        is_online=is_user_online(u),
        last_seen_at=u.last_seen_at,
        created_at=member.created_at,
    )


@router.get("", response_model=list[EmployeeOut])
def list_employees(
    company_id: int,
    status: str = Query("all", description="active|blocked|all"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(company_id, user, db, module="employees")
    query = (
        db.query(CompanyMember)
        .options(joinedload(CompanyMember.user))
        .filter(CompanyMember.company_id == company.id)
    )
    if status == "active":
        query = query.filter(CompanyMember.is_active == True)
    elif status == "blocked":
        query = query.filter(CompanyMember.is_active == False)
    members = query.order_by(CompanyMember.id).all()
    return [_to_out(m) for m in members]


@router.post("", response_model=EmployeeOut, status_code=201)
def create_employee(
    company_id: int,
    data: EmployeeCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(company_id, user, db, module="employees")
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        dup = db.query(CompanyMember).filter(
            CompanyMember.company_id == company.id,
            CompanyMember.user_id == existing.id,
        ).first()
        if dup:
            raise HTTPException(status_code=400, detail="Пользователь уже в этой компании")
        new_user = existing
    else:
        new_user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            phone=data.phone,
        )
        db.add(new_user)
        db.flush()
    member = CompanyMember(
        company_id=company.id,
        user_id=new_user.id,
        job_title=data.job_title,
        phone=data.phone,
        department=data.department,
        role=data.role,
        perm_leads=data.perm_leads,
        perm_crm=data.perm_crm,
        perm_catalog=data.perm_catalog,
        perm_qr=data.perm_qr,
        perm_settings=data.perm_settings,
        perm_employees=data.perm_employees,
        is_active=True,
    )
    db.add(member)
    db.commit()
    member = (
        db.query(CompanyMember)
        .options(joinedload(CompanyMember.user))
        .filter(CompanyMember.id == member.id)
        .first()
    )
    return _to_out(member)


@router.patch("/{member_id}", response_model=EmployeeOut)
def update_employee(
    company_id: int,
    member_id: int,
    data: EmployeeUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(company_id, user, db, module="employees")
    member = (
        db.query(CompanyMember)
        .options(joinedload(CompanyMember.user))
        .filter(CompanyMember.id == member_id, CompanyMember.company_id == company.id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    if member.user_id == company.owner_id and not is_owner(user, company):
        raise HTTPException(status_code=403, detail="Нельзя изменять владельца")

    payload = data.model_dump(exclude_unset=True)
    user_fields = {"full_name", "phone", "password", "is_active"}
    for key, value in payload.items():
        if key in user_fields:
            if key == "password" and value:
                member.user.hashed_password = hash_password(value)
            elif key == "is_active" and value is not None:
                member.user.is_active = value
                member.is_active = value
            elif hasattr(member.user, key) and value is not None:
                setattr(member.user, key, value)
        elif hasattr(member, key) and value is not None:
            setattr(member, key, value)

    db.commit()
    db.refresh(member)
    return _to_out(member)


@router.delete("/{member_id}", status_code=204)
def deactivate_employee(
    company_id: int,
    member_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(company_id, user, db, module="employees")
    member = db.query(CompanyMember).filter(
        CompanyMember.id == member_id, CompanyMember.company_id == company.id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    if member.user_id == company.owner_id:
        raise HTTPException(status_code=400, detail="Нельзя отключить владельца компании")
    member.is_active = False
    member.user.is_active = False
    db.commit()


@router.post("/{member_id}/restore", response_model=EmployeeOut)
def restore_employee(
    company_id: int,
    member_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(company_id, user, db, module="employees")
    member = (
        db.query(CompanyMember)
        .options(joinedload(CompanyMember.user))
        .filter(CompanyMember.id == member_id, CompanyMember.company_id == company.id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    member.is_active = True
    member.user.is_active = True
    db.commit()
    db.refresh(member)
    return _to_out(member)


@router.post("/bulk-deactivate", status_code=204)
def bulk_deactivate(
    company_id: int,
    data: EmployeeBulkIds,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(company_id, user, db, module="employees")
    members = db.query(CompanyMember).filter(
        CompanyMember.company_id == company.id,
        CompanyMember.id.in_(data.ids),
    ).all()
    for m in members:
        if m.user_id == company.owner_id:
            continue
        m.is_active = False
        m.user.is_active = False
    db.commit()


@router.post("/bulk-restore")
def bulk_restore(
    company_id: int,
    data: EmployeeBulkIds,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(company_id, user, db, module="employees")
    members = db.query(CompanyMember).filter(
        CompanyMember.company_id == company.id,
        CompanyMember.id.in_(data.ids),
    ).all()
    for m in members:
        m.is_active = True
        m.user.is_active = True
    db.commit()
    return {"restored": len(members)}
