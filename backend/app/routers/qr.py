import io
import json
from urllib.parse import quote

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth import get_company_for_user, get_current_user
from app.public_url import public_frontend_url
from app.database import get_db
from app.models import QrCustomLink, QrSavedTemplate, User
from app.qr_saved import (
    PRESET_QR_TEMPLATES,
    SYSTEM_QR_TEMPLATES,
    dump_config,
    parse_config,
    saved_to_out,
)
from app.qr_templates import TEMPLATES, render_qr_card
from app.schemas import QrCustomLinkCreate, QrCustomLinkOut, QrTemplateOut, QrTemplateSave

router = APIRouter(prefix="/api/companies/{company_id}/qr", tags=["qr"])

TARGETS = {
    "profile": "/c/{slug}",
    "catalog": "/c/{slug}/catalog",
    "lead": "/c/{slug}/contact",
    "contacts": "/c/{slug}#contacts",
}

TARGET_LABELS = {
    "profile": "Страница компании",
    "catalog": "Каталог",
    "lead": "Форма заявки",
    "contacts": "Контакты",
}

PROTECTED_SYSTEM = {"minimal", "brand"}


def _build_url(company, target: str, db: Session, request: Request | None = None) -> str:
    if target.startswith("link:"):
        try:
            link_id = int(target.split(":", 1)[1])
        except ValueError:
            raise HTTPException(status_code=400, detail="Некорректная ссылка")
        link = db.query(QrCustomLink).filter(
            QrCustomLink.id == link_id,
            QrCustomLink.company_id == company.id,
        ).first()
        if not link:
            raise HTTPException(status_code=404, detail="Ссылка не найдена")
        url = link.url.strip()
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        return url
    path_tpl = TARGETS.get(target, TARGETS["profile"])
    return f"{public_frontend_url(request)}{path_tpl.format(slug=company.slug)}"


def _caption_for_target(target: str, company_id: int, db: Session) -> str:
    if target.startswith("link:"):
        try:
            link_id = int(target.split(":", 1)[1])
        except ValueError:
            return "Своя ссылка"
        link = db.query(QrCustomLink).filter(
            QrCustomLink.id == link_id,
            QrCustomLink.company_id == company_id,
        ).first()
        return link.name if link else "Своя ссылка"
    return TARGET_LABELS.get(target, "")


def _custom_from_query(
    bg_color: str = "",
    fg_color: str = "",
    accent_color: str = "",
    accent2_color: str = "",
    qr_scale: float = 0.58,
    show_dots: bool = True,
    show_stars: bool = False,
    show_gradient: bool = True,
    show_badge: bool = True,
    frame_style: str = "rounded",
    custom_json: str = "",
) -> dict:
    if custom_json:
        try:
            data = json.loads(custom_json)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    return {
        "bg_color": bg_color,
        "fg_color": fg_color,
        "accent_color": accent_color,
        "accent2_color": accent2_color,
        "qr_scale": qr_scale,
        "show_dots": show_dots,
        "show_stars": show_stars,
        "show_gradient": show_gradient,
        "show_badge": show_badge,
        "frame_style": frame_style,
    }


def _resolve_render(company_id: int, template: str, custom_json: str, db: Session) -> tuple[str, dict]:
    if template.startswith("saved:"):
        try:
            saved_id = int(template.split(":", 1)[1])
        except ValueError:
            raise HTTPException(status_code=400, detail="Некорректный id шаблона")
        row = db.query(QrSavedTemplate).filter(
            QrSavedTemplate.id == saved_id,
            QrSavedTemplate.company_id == company_id,
        ).first()
        if not row:
            raise HTTPException(status_code=404, detail="Шаблон не найден")
        cfg = parse_config(row.config_json)
        if custom_json:
            try:
                overlay = json.loads(custom_json)
                if isinstance(overlay, dict):
                    cfg = {**cfg, **overlay}
            except json.JSONDecodeError:
                pass
        base = row.base_template or "custom"
        tpl_key = "custom" if cfg or base == "custom" else base
        return tpl_key, cfg
    if custom_json:
        try:
            data = json.loads(custom_json)
            if isinstance(data, dict):
                return "custom", data
        except json.JSONDecodeError:
            pass
    return template, {}


@router.get("/templates", response_model=list[QrTemplateOut])
def list_templates(
    company_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="qr")
    out = []
    for t in SYSTEM_QR_TEMPLATES + PRESET_QR_TEMPLATES:
        out.append(QrTemplateOut(
            id=None,
            name=t["name"],
            base_template=t["base_template"],
            config=t.get("config", {}),
            is_system=t["is_system"],
        ))
    rows = (
        db.query(QrSavedTemplate)
        .filter(QrSavedTemplate.company_id == company_id)
        .order_by(QrSavedTemplate.created_at.desc())
        .all()
    )
    for row in rows:
        d = saved_to_out(row)
        out.append(QrTemplateOut(**d))
    return out


@router.post("/templates", response_model=QrTemplateOut, status_code=201)
def save_template(
    company_id: int,
    data: QrTemplateSave,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="qr")
    if data.base_template in PROTECTED_SYSTEM and data.name.lower() in ("минимальный", "брендовый"):
        raise HTTPException(status_code=400, detail="Это имя зарезервировано для системных шаблонов")
    row = QrSavedTemplate(
        company_id=company_id,
        name=data.name.strip(),
        base_template=data.base_template,
        config_json=dump_config(data.config),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return QrTemplateOut(**saved_to_out(row))


@router.get("/custom-links", response_model=list[QrCustomLinkOut])
def list_custom_links(
    company_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="qr")
    return (
        db.query(QrCustomLink)
        .filter(QrCustomLink.company_id == company_id)
        .order_by(QrCustomLink.created_at.desc())
        .all()
    )


@router.post("/custom-links", response_model=QrCustomLinkOut, status_code=201)
def create_custom_link(
    company_id: int,
    data: QrCustomLinkCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="qr")
    row = QrCustomLink(company_id=company_id, name=data.name.strip(), url=data.url.strip())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/custom-links/{link_id}", status_code=204)
def delete_custom_link(
    company_id: int,
    link_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="qr")
    row = db.query(QrCustomLink).filter(
        QrCustomLink.id == link_id,
        QrCustomLink.company_id == company_id,
    ).first()
    if row:
        db.delete(row)
        db.commit()


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(
    company_id: int,
    template_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_company_for_user(company_id, user, db, module="qr")
    row = db.query(QrSavedTemplate).filter(
        QrSavedTemplate.id == template_id,
        QrSavedTemplate.company_id == company_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    db.delete(row)
    db.commit()


@router.get("/links")
def qr_links(
    company_id: int,
    request: Request,
    target: str = "profile",
    template: str = "brand",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(company_id, user, db, module="qr")
    url = _build_url(company, target, db, request)
    return {
        "url": url,
        "target": target,
        "template": template,
        "slug": company.slug,
        "system_templates": [t["id"] for t in SYSTEM_QR_TEMPLATES],
        "protected": list(PROTECTED_SYSTEM),
        "frame_styles": ["rounded", "square", "dashed", "none"],
        "target_labels": TARGET_LABELS,
    }


@router.get("/share")
def share_links(
    company_id: int,
    request: Request,
    target: str = "profile",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(company_id, user, db, module="qr")
    url = _build_url(company, target, db, request)
    label = _caption_for_target(target, company_id, db)
    text = quote(f"{company.name} — {label}")
    encoded_url = quote(url)
    return {
        "url": url,
        "telegram": f"https://t.me/share/url?url={encoded_url}&text={text}",
        "whatsapp": f"https://wa.me/?text={text}%20{encoded_url}",
        "facebook": f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}",
        "vk": f"https://vk.com/share.php?url={encoded_url}&title={text}",
        "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}",
    }


@router.get("/image")
def qr_image(
    company_id: int,
    request: Request,
    target: str = "profile",
    template: str = Query("brand"),
    styled: bool = Query(True),
    bg_color: str = "",
    fg_color: str = "",
    accent_color: str = "",
    accent2_color: str = "",
    qr_scale: float = Query(0.58),
    show_dots: bool = Query(True),
    show_stars: bool = Query(False),
    show_gradient: bool = Query(True),
    show_badge: bool = Query(True),
    frame_style: str = Query("rounded"),
    custom_json: str = Query(""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(company_id, user, db, module="qr")
    url = _build_url(company, target, db, request)
    caption = _caption_for_target(target, company_id, db)

    tpl_key, resolved_custom = _resolve_render(company_id, template, custom_json, db)
    if custom_json:
        merged = resolved_custom
    elif template.startswith("saved:"):
        merged = resolved_custom
    else:
        merged = {}

    if styled:
        png = render_qr_card(url, company.name, tpl_key, caption, merged)
        buf = io.BytesIO(png)
    else:
        img = qrcode.make(url)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

    filename = f"qr-{company.slug}-{target}-{template}.png"
    return StreamingResponse(
        buf,
        media_type="image/png",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/messenger")
def messenger_links(
    company_id: int,
    message: str = "Здравствуйте! Хочу оставить заявку.",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = get_company_for_user(company_id, user, db, module="qr")
    encoded = quote(message)
    wa = f"https://wa.me/{company.whatsapp}?text={encoded}" if company.whatsapp else None
    tg = f"https://t.me/{company.telegram}?text={encoded}" if company.telegram else None
    return {"whatsapp_url": wa, "telegram_url": tg, "prefilled_message": message}
