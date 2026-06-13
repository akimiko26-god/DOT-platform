"""AI-анализ клиентов: Gemini + улучшенная эвристика без ключа."""

import re
from collections import Counter
from datetime import datetime

import httpx

from app.config import settings

PAIN_WORDS = {
    "дорого": "чувствительность к цене",
    "цена": "важен прайс и прозрачность условий",
    "срочно": "нужен быстрый ответ",
    "жалоб": "есть недовольство — важно восстановить доверие",
    "не работает": "техническая проблема",
    "скидк": "ожидает выгодное предложение",
    "конкурент": "сравнивает с альтернативами",
    "повтор": "заинтересован в долгосрочном сотрудничестве",
    "брак": "проблема с качеством товара/услуги",
    "возврат": "возможен спор по оплате или возврату",
    "долго": "ожидает ускорения процесса",
    "не отвеч": "риск потери клиента из-за задержки",
    "разочар": "снижение лояльности",
    "плох": "негативный опыт в прошлом",
    "злой": "эскалация конфликта",
}

STATUS_RU = {
    "new": "Новая",
    "in_progress": "В работе",
    "waiting": "Ожидает ответа",
    "done": "Выполнена",
    "cancelled": "Отменена",
}

SOURCE_RU = {
    "website": "Сайт",
    "landing": "Лендинг",
    "qr": "QR-код",
    "form": "Форма",
    "whatsapp": "WhatsApp",
    "telegram": "Telegram",
    "other": "Другое",
}

SECTION_HEADERS = [
    "Предыстория",
    "Портрет клиента",
    "Настрой и характер",
    "Рекомендации менеджеру",
    "Риски",
    "Точки соприкосновения",
    "Следующий шаг",
]


def _lead_status(l) -> str:
    return l.status.value if hasattr(l.status, "value") else str(l.status)


def _lead_source(l) -> str:
    return l.source.value if hasattr(l.source, "value") else str(l.source)


def _fmt_dt(dt) -> str:
    if not dt:
        return "—"
    return dt.strftime("%d.%m.%Y %H:%M")


def _format_lead_history(leads: list) -> str:
    if not leads:
        return "Обращений пока нет."
    lines = []
    for l in leads[:20]:
        status = STATUS_RU.get(_lead_status(l), _lead_status(l))
        source = SOURCE_RU.get(_lead_source(l), _lead_source(l))
        lines.append(
            f"• [{_fmt_dt(l.created_at)}] {status} / {source}\n"
            f"  Сообщение: {l.message or '(без текста)'}"
        )
        for c in getattr(l, "comments", []) or []:
            author = c.author_name or "Менеджер"
            job = f", {c.author_job_title}" if getattr(c, "author_job_title", "") else ""
            lines.append(f"  ↳ {_fmt_dt(c.created_at)} {author}{job}: {c.text}")
    return "\n".join(lines)


def _format_customer_card(customer) -> str:
    return "\n".join(
        [
            f"Имя: {customer.name}",
            f"Телефон: {customer.phone or '—'}",
            f"Email: {customer.email or '—'}",
            f"VIP: {'да' if customer.is_vip else 'нет'}",
            f"Количество обращений: {customer.visit_count}",
            f"Клиент с: {_fmt_dt(customer.created_at)}",
            f"Последнее изменение карточки: {_fmt_dt(customer.updated_at)}",
            f"Заметки менеджера:\n{customer.notes or '—'}",
        ]
    )


def _parse_sections(text: str) -> dict:
    sections = {}
    pattern = r"^##\s*(.+?)\s*$"
    parts = re.split(pattern, text, flags=re.MULTILINE)
    if len(parts) > 1:
        for i in range(1, len(parts), 2):
            title = parts[i].strip()
            body = parts[i + 1].strip() if i + 1 < len(parts) else ""
            sections[title] = body
    return sections


def _collect_context(customer, leads: list) -> dict:
    messages = []
    comments = []
    for l in leads:
        if l.message:
            messages.append(l.message)
        for c in getattr(l, "comments", []) or []:
            comments.append(c.text or "")
    combined = " ".join(messages + comments + [customer.notes or ""]).lower()
    pains = []
    for word, label in PAIN_WORDS.items():
        if word in combined:
            pains.append(label)
    if not pains and (messages or customer.notes):
        pains.append("явных негативных сигналов не выявлено")

    sources = Counter(_lead_source(l) for l in leads)
    statuses = Counter(_lead_status(l) for l in leads)
    top_source = SOURCE_RU.get(sources.most_common(1)[0][0], "неизвестно") if sources else "неизвестно"
    repeat = customer.visit_count > 1 or len(leads) > 1
    active = statuses.get("waiting", 0) + statuses.get("in_progress", 0) + statuses.get("new", 0)

    tone = "спокойный и уверенный"
    if any(w in combined for w in ("жалоб", "злой", "разочар", "плох", "возврат")):
        tone = "эмпатичный, без оправданий — сначала признать проблему"
    elif repeat or customer.is_vip:
        tone = "теплый, персональный, с уважением к истории"
    elif "срочно" in combined:
        tone = "оперативный, конкретный, с чёткими сроками"

    offer = []
    if "цен" in combined or "дорого" in combined:
        offer.append("предложить пакет со скидкой или рассрочку")
    if repeat:
        offer.append("сослаться на прошлый успешный опыт и бонусы лояльности")
    if "срочно" in combined:
        offer.append("зафиксировать SLA ответа и приоритетную линию")
    if customer.is_vip:
        offer.append("персональный менеджер и приоритетное обслуживание")
    if active:
        offer.append("закрыть открытые заявки до новых предложений")
    if not offer:
        offer.append("уточнить потребность и предложить 2–3 релевантных варианта")

    risks = []
    if statuses.get("cancelled", 0):
        risks.append("есть отменённые заявки — возможна потеря интереса")
    if statuses.get("waiting", 0):
        risks.append("клиент ждёт ответа — риск ухода к конкуренту")
    if any(w in combined for w in ("жалоб", "брак", "возврат")):
        risks.append("вероятна эскалация — нужна эскалация старшему менеджеру")
    if not risks:
        risks.append("критических рисков не видно, но важно не затягивать ответ")

    touch_points = []
    if customer.phone:
        touch_points.append(f"звонок/WhatsApp: {customer.phone}")
    if customer.email:
        touch_points.append(f"email: {customer.email}")
    if messages:
        touch_points.append("вернуться к формулировкам из последнего обращения")
    if customer.notes:
        touch_points.append("опереться на заметки менеджера в карточке")
    if not touch_points:
        touch_points.append("уточнить удобный канал связи при первом контакте")

    return {
        "messages": messages,
        "comments": comments,
        "pains": pains,
        "sources": dict(sources),
        "statuses": dict(statuses),
        "top_source": top_source,
        "repeat": repeat,
        "tone": tone,
        "offer": offer,
        "risks": risks,
        "touch_points": touch_points,
        "leads_count": len(leads),
        "active_leads": active,
    }


def _heuristic_insight(customer, leads: list, ctx: dict) -> str:
    comments_note = ""
    if ctx["comments"]:
        comments_note = f" Комментариев менеджеров: {len(ctx['comments'])}."

    sections = {
        "Ситуация": (
            f"{'Повторный' if ctx['repeat'] else 'Новый'} клиент · {customer.visit_count} обращений · "
            f"канал {ctx['top_source']}. Активных заявок: {ctx['active_leads']}."
            + (" VIP." if customer.is_vip else "")
            + comments_note
        ),
        "Настрой": f"Тон общения: {ctx['tone']}.",
        "Важно знать": "; ".join(ctx["pains"][:4]) if ctx["pains"] else "Явных проблем не видно.",
        "Что предпринять": "; ".join(ctx["offer"][:3]),
        "Риски": "; ".join(ctx["risks"][:2]),
    }
    body = "\n\n".join(f"## {title}\n{text}" for title, text in sections.items())
    return f"🤖 AI-бриф (локальный анализ)\n\n{body}"


def _gemini_models() -> list[str]:
    preferred = (settings.gemini_model or "gemini-2.5-flash").strip()
    fallbacks = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-flash-latest",
        "gemini-3.5-flash",
        "gemini-3-flash-preview",
        "gemini-flash-lite-latest",
    ]
    models = []
    if preferred:
        models.append(preferred)
    for m in fallbacks:
        if m not in models:
            models.append(m)
    return models


def _call_gemini(prompt: str) -> tuple[str | None, str | None, str | None]:
    """Returns (text, error_code, model_used)."""
    key = (settings.gemini_api_key or "").strip()
    if not key:
        return None, "no_key", None

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2048},
    }
    last_error = "error"
    quota_hits = 0

    for model in _gemini_models():
        try:
            r = httpx.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": key},
                json=payload,
                timeout=60.0,
            )
            if r.status_code == 429:
                quota_hits += 1
                last_error = "quota"
                continue
            if r.status_code == 404:
                last_error = f"model_not_found:{model}"
                continue
            if r.status_code != 200:
                detail = r.text[:200]
                last_error = f"http_{r.status_code}:{detail}"
                continue
            data = r.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return text, None, model
        except Exception as exc:
            last_error = f"error:{exc.__class__.__name__}"
            continue

    if quota_hits and quota_hits == len(_gemini_models()):
        return None, "quota", None
    return None, last_error, None


def _gemini_insight(customer, leads: list, ctx: dict) -> tuple[str | None, str | None, str | None]:
    key = (settings.gemini_api_key or "").strip()
    if not key:
        return None, "no_key", None

    prompt = f"""Ты опытный управляющий малого бизнеса в Казахстане. Составь КОРОТКИЙ бриф для менеджера (не более 500 слов).

=== КАРТОЧКА ===
{_format_customer_card(customer)}

=== ИСТОРИЯ ({len(leads)} обращений) ===
{_format_lead_history(leads)}

Сигналы: {', '.join(ctx['pains'][:5]) if ctx['pains'] else 'нет'}

Используй заголовки ## (по 2–4 предложения каждый):
## Ситуация
## Комментарии и заявки
## Настрой клиента
## Важно знать
## Что предпринять
## Риски

Только факты из данных. Без воды."""

    text, err, model = _call_gemini(prompt)
    if text:
        header = f"🤖 AI-бриф для менеджера (Gemini · {model})"
        return f"{header}\n\n{text}", None, model
    return None, err, model


def generate_customer_insight(customer, leads: list) -> dict:
    ctx = _collect_context(customer, leads)
    gemini_text, gemini_error, gemini_model = _gemini_insight(customer, leads, ctx)

    if gemini_text:
        insight = gemini_text
        source = "gemini"
    else:
        insight = _heuristic_insight(customer, leads, ctx)
        source = "heuristic"
        if gemini_error == "quota":
            insight = (
                "⚠️ Лимит Gemini на всех моделях исчерпан — показан локальный анализ. Повторите через несколько минут.\n\n"
                + insight
            )
        elif gemini_error == "no_key":
            insight = (
                "⚠️ Ключ GEMINI_API_KEY не задан — локальный анализ.\n\n" + insight
            )
        elif gemini_error:
            insight = f"⚠️ Gemini недоступен ({gemini_error}) — локальный анализ.\n\n{insight}"

    sections = _parse_sections(insight.split("\n\n", 1)[-1] if "\n\n" in insight else insight)

    return {
        "insight": insight,
        "sections": sections,
        "pains": ctx["pains"],
        "suggestions": ctx["offer"],
        "risks": ctx["risks"],
        "touch_points": ctx["touch_points"],
        "tone": ctx["tone"],
        "leads_count": ctx["leads_count"],
        "active_leads": ctx["active_leads"],
        "top_source": ctx["top_source"],
        "source": source,
        "gemini_error": gemini_error,
        "gemini_model": gemini_model,
        "generated_at": datetime.utcnow().isoformat(),
    }


def ask_customer_advice(customer, leads: list, question: str, prior_insight: str = "") -> dict:
    ctx = _collect_context(customer, leads)
    q = (question or "").strip()
    if not q:
        return {"answer": "Введите вопрос для ИИ.", "source": "local"}

    prompt = f"""Менеджер CRM задаёт вопрос по клиенту. Ответь кратко (до 150 слов), по делу, на русском.

Клиент: {customer.name}, VIP={customer.is_vip}, визитов={customer.visit_count}
Заметки: {customer.notes or '—'}

История:
{_format_lead_history(leads)[:2500]}

Текущий бриф:
{(prior_insight or 'нет')[:1200]}

Вопрос менеджера: {q}"""

    text, err, model = _call_gemini(prompt)
    if text:
        return {"answer": text, "source": "gemini", "gemini_model": model}
    fallback = (
        f"По клиенту «{customer.name}»: {ctx['tone']}. "
        f"Рекомендация: {ctx['offer'][0] if ctx['offer'] else 'уточните запрос клиента.'}"
    )
    if err == "quota":
        fallback = "Лимит Gemini исчерпан. " + fallback
    elif err == "no_key":
        fallback = "Gemini не настроен. " + fallback
    return {"answer": fallback, "source": "heuristic", "gemini_error": err}
