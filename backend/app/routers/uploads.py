import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.auth import get_company_for_user, get_current_user
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/api", tags=["uploads"])
UPLOAD_ROOT = Path(__file__).resolve().parent.parent / "uploads"


@router.post("/auth/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Только изображения")
    ext = ".png"
    if "jpeg" in file.content_type or "jpg" in file.content_type:
        ext = ".jpg"
    elif "webp" in file.content_type:
        ext = ".webp"
    folder = UPLOAD_ROOT / "avatars"
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{user.id}_{uuid.uuid4().hex}{ext}"
    path = folder / name
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Файл больше 5 МБ")
    path.write_bytes(content)
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
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Только изображения")
    ext = ".png"
    if "jpeg" in file.content_type or "jpg" in file.content_type:
        ext = ".jpg"
    elif "webp" in file.content_type:
        ext = ".webp"
    elif "gif" in file.content_type:
        ext = ".gif"

    folder = UPLOAD_ROOT / str(company_id)
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    path = folder / name
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Файл больше 5 МБ")
    path.write_bytes(content)
    return {"url": f"/api/uploads/{company_id}/{name}"}


@router.get("/uploads/{company_id}/{filename}")
def get_upload(company_id: int, filename: str):
    path = UPLOAD_ROOT / str(company_id) / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(path)
