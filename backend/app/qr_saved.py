import json

SYSTEM_QR_TEMPLATES = [
    {"id": "minimal", "name": "Минимальный", "base_template": "minimal", "is_system": True, "config": {}},
    {"id": "brand", "name": "Брендовый", "base_template": "brand", "is_system": True, "config": {}},
]

PRESET_QR_TEMPLATES = [
    {"id": "neon", "name": "Неон", "base_template": "neon", "is_system": True, "config": {}},
    {"id": "sunset", "name": "Закат", "base_template": "sunset", "is_system": True, "config": {}},
    {"id": "festive", "name": "Праздничный", "base_template": "festive", "is_system": True, "config": {}},
    {"id": "luxury", "name": "Премиум", "base_template": "luxury", "is_system": True, "config": {}},
]


def parse_config(raw: str) -> dict:
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}


def dump_config(cfg: dict) -> str:
    return json.dumps(cfg or {}, ensure_ascii=False)


def saved_to_out(row) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "base_template": row.base_template,
        "config": parse_config(row.config_json),
        "is_system": False,
    }
