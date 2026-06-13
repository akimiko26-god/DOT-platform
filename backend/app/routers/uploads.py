import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import get_company_for_user, get_current_user
from app.database import get_db
from app.models import Company, User

router = APIRouter(prefix="/api", tags=["uploads"])
UPLOAD_ROOT = Path(__file__).resolve().parent.parent / "uploads"


async def _save_image(file: UploadFile, folder: Path, prefix: str = "") -> str:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Только изображения")
    ext = ".png"
    if "jpeg" in file.content_type or "jpg" in file.content_type:
        ext = ".jpg"
    elif "webp" in file.content_type:
        ext = ".webp"
    elif "gif" in file.content_type:
        ext = ".gif"
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{prefix}{uuid.uuid4().hex}{ext}" if prefix else f"{uuid.uuid4().hex}{ext}"
    path = folder / name
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Файл больше 5 МБ")
    path.write_bytes(content)
    return name


@router.post("/auth/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    folder = UPLOAD_ROOT / "avatars"
    name = await _save_image(file, folder, prefix=f"{user.id}_")
    user.avatar_url = f"/api/uploads/avatars/{name}"
    db.commit()
    return {"url": user.avatar_url}


@router.get("/uploads/avatars/{filename}")
def get_avatar(filename: str):
    path = UPLOAD_ROOT / "avatars" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(path)


@router.post("/companies/{company_id}/upload")
async def upload_image(
    company_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="catalog")
    folder = UPLOAD_ROOT / str(company_id)
    name = await _save_image(file, folder)
    return {"url": f"/api/uploads/{company_id}/{name}"}


@router.post("/companies/{company_id}/logo")
async def upload_logo(
    company_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(company_id, user, db, module="settings")
    folder = UPLOAD_ROOT / str(company_id) / "brand"
    name = await _save_image(file, folder, prefix="logo_")
    company.logo_url = f"/api/uploads/{company_id}/brand/{name}"
    db.commit()
    return {"url": company.logo_url}


@router.get("/uploads/{company_id}/brand/{filename}")
def get_brand(company_id: int, filename: str):
    path = UPLOAD_ROOT / str(company_id) / "brand" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(path)


@router.get("/uploads/{company_id}/{filename}")
def get_upload(company_id: int, filename: str):
    path = UPLOAD_ROOT / str(company_id) / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(path)
