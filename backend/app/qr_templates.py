import io
from typing import Any

import qrcode
from PIL import Image, ImageDraw, ImageFont

TEMPLATES = {
    "minimal": {"label": "Минимальный", "preset": "clean"},
    "brand": {"label": "Брендовый", "preset": "dark"},
    "neon": {"label": "Неон", "preset": "neon"},
    "sunset": {"label": "Закат", "preset": "sunset"},
    "festive": {"label": "Праздничный", "preset": "festive"},
    "luxury": {"label": "Премиум", "preset": "luxury"},
    "custom": {"label": "Свой дизайн", "preset": "custom"},
}

PRESETS = {
    "clean": {"bg": "#ffffff", "fg": "#111827", "accent": "#3b82f6", "accent2": "#60a5fa"},
    "dark": {"bg": "#0f172a", "fg": "#f8fafc", "accent": "#38bdf8", "accent2": "#818cf8"},
    "neon": {"bg": "#0a0a12", "fg": "#00ffcc", "accent": "#ff00aa", "accent2": "#7c3aed"},
    "sunset": {"bg": "#1a0a2e", "fg": "#fff7ed", "accent": "#f97316", "accent2": "#fb7185"},
    "festive": {"bg": "#14532d", "fg": "#fef9c3", "accent": "#facc15", "accent2": "#ef4444"},
    "luxury": {"bg": "#1c1917", "fg": "#fafaf9", "accent": "#d4af37", "accent2": "#a8a29e"},
    "custom": {"bg": "#1e293b", "fg": "#ffffff", "accent": "#3d9cf5", "accent2": "#a855f7"},
}


def _hex(c: str, default: str) -> str:
    c = (c or default).strip()
    if not c.startswith("#"):
        c = f"#{c}"
    return c[:7] if len(c) >= 7 else default


def _font(size: int):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _draw_gradient_bg(draw: ImageDraw.ImageDraw, w: int, h: int, c1: str, c2: str):
    for y in range(h):
        t = y / max(h - 1, 1)
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def _draw_dots(draw: ImageDraw.ImageDraw, w: int, h: int, color: str, count: int = 40):
    import random

    random.seed(42)
    for _ in range(count):
        x, y = random.randint(0, w), random.randint(0, h)
        r = random.randint(2, 6)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=color)


def _draw_stars(draw: ImageDraw.ImageDraw, w: int, h: int, color: str):
    import random

    random.seed(7)
    for _ in range(18):
        x, y = random.randint(20, w - 20), random.randint(20, h - 20)
        s = random.randint(4, 10)
        draw.polygon(
            [(x, y - s), (x + s * 0.3, y - s * 0.3), (x + s, y), (x + s * 0.3, y + s * 0.3),
             (x, y + s), (x - s * 0.3, y + s * 0.3), (x - s, y), (x - s * 0.3, y - s * 0.3)],
            fill=color,
        )


def _draw_frame(draw: ImageDraw.ImageDraw, box: tuple, color: str, style: str, width: int = 4):
    if style == "none":
        return
    if style == "dashed":
        x1, y1, x2, y2 = box
        step = 16
        for x in range(x1, x2, step):
            draw.line([(x, y1), (min(x + 8, x2), y1)], fill=color, width=width)
            draw.line([(x, y2), (min(x + 8, x2), y2)], fill=color, width=width)
        for y in range(y1, y2, step):
            draw.line([(x1, y), (x1, min(y + 8, y2))], fill=color, width=width)
            draw.line([(x2, y), (x2, min(y + 8, y2))], fill=color, width=width)
    else:
        radius = 24 if style == "rounded" else 8
        draw.rounded_rectangle(box, radius=radius, outline=color, width=width)


def render_qr_card(
    url: str,
    company_name: str,
    template: str = "brand",
    caption: str = "",
    custom: dict[str, Any] | None = None,
) -> bytes:
    custom = custom or {}
    tpl = TEMPLATES.get(template, TEMPLATES["brand"])
    preset_name = tpl.get("preset", "dark")
    if template == "custom" or custom.get("mode") == "custom":
        preset_name = "custom"
    base = {**PRESETS.get(preset_name, PRESETS["dark"])}

    bg = _hex(custom.get("bg_color") or custom.get("bg"), base["bg"])
    fg = _hex(custom.get("fg_color") or custom.get("fg"), base["fg"])
    accent = _hex(custom.get("accent_color") or custom.get("accent"), base["accent"])
    accent2 = _hex(custom.get("accent2_color") or custom.get("accent2"), base["accent2"])

    qr_scale = float(custom.get("qr_scale", 0.52))
    qr_scale = max(0.32, min(0.65, qr_scale))
    show_dots = str(custom.get("show_dots", "true")).lower() in ("1", "true", "yes")
    show_stars = str(custom.get("show_stars", "false")).lower() in ("1", "true", "yes")
    show_gradient = str(custom.get("show_gradient", "true")).lower() in ("1", "true", "yes")
    frame_style = custom.get("frame_style", "rounded")
    show_badge = str(custom.get("show_badge", "true")).lower() in ("1", "true", "yes")

    w, h = 520, 740
    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)

    if show_gradient:
        _draw_gradient_bg(draw, w, h, bg, accent2)
    if show_dots:
        _draw_dots(draw, w, h, accent + "44", 50)
    if show_stars:
        _draw_stars(draw, w, h, accent)

    header_h = 88
    draw.rounded_rectangle((20, 20, w - 20, header_h), radius=20, fill=accent)
    draw.text((36, 36), "./dot", fill="#ffffff", font=_font(24))
    draw.text((36, 64), "SCAN ME", fill="#ffffff", font=_font(11))

    y_text = header_h + 22
    title = (company_name or "Компания")[:36]
    draw.text((36, y_text), title, fill=fg, font=_font(20))
    y_text += 30
    if caption:
        cap = caption[:56]
        draw.rounded_rectangle((28, y_text - 4, w - 28, y_text + 26), radius=10, fill=accent + "33")
        draw.text((40, y_text), cap, fill=accent, font=_font(16))
        y_text += 38

    footer_h = 88 if show_badge else 24
    qr_area_top = y_text + 14
    qr_area_bottom = h - footer_h - 10
    max_qr_h = max(140, qr_area_bottom - qr_area_top)
    qr_px = int(min(w * qr_scale, max_qr_h))
    qr_px = max(140, min(320, qr_px))

    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=fg, back_color=bg).convert("RGB").resize((qr_px, qr_px))

    x0 = (w - qr_px) // 2
    y0 = qr_area_top + (max_qr_h - qr_px) // 2
    pad = 14
    frame_box = (x0 - pad, y0 - pad, x0 + qr_px + pad, y0 + qr_px + pad)
    draw.rounded_rectangle(frame_box, radius=20, fill=bg)
    _draw_frame(draw, frame_box, accent, frame_style, 5)
    img.paste(qr_img, (x0, y0))

    if show_badge:
        badge = "Откройте камеру →"
        draw.rounded_rectangle((60, h - 88, w - 60, h - 38), radius=16, fill=accent)
        tw = draw.textlength(badge, font=_font(16))
        draw.text(((w - tw) / 2, h - 72), badge, fill="#ffffff", font=_font(16))

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    return buf.getvalue()
