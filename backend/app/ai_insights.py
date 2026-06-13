"""AI-анализ клиентов: Gemini (бесплатный ключ) + улучшенная эвристика без ключа."""

import json
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
}


def _lead_status(l) -> str:
    return l.status.value if hasattr(l.status, "value") else str(l.status)


def _lead_source(l) -> str:
    return l.source.value if hasattr(l.source, "value") else str(l.source)


def _collect_context(customer, leads: list) -> dict:
    messages = []
    comments = []
    for l in leads:
        if l.message:
            messages.append(l.message)
        for c in getattr(l, "comments", []) or []:
            comments.append(c.text or "")
    combined = " ".join(messages + comments).lower()
    pains = []
    for word, label in PAIN_WORDS.items():
        if word in combined:
            pains.append(label)
    if not pains and messages:
        pains.append("стандартный запрос без явных негативных сигналов")

    sources = Counter(_lead_source(l) for l in leads)
    statuses = Counter(_lead_status(l) for l in leads)
    top_source = sources.most_common(1)[0][0] if sources else "неизвестно"
    repeat = customer.visit_count > 1
    tone = "теплый и персональный" if repeat else "информативный и убедительный"

    offer = []
    if "цен" in combined or "дорого" in combined:
        offer.append("предложить пакет со скидкой или рассрочку")
    if repeat:
        offer.append("напомнить про прошлый успешный опыт и бонусы лояльности")
    if "срочно" in combined:
        offer.append("зафиксировать SLA ответа и приоритетную линию")
    if customer.is_vip:
        offer.append("персональный менеджер и приоритетное обслуживание")
    if not offer:
        offer.append("уточнить потребность и предложить 2–3 релевантных варианта из каталога")

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
        "leads_count": len(leads),
    }


def _heuristic_insight(customer, ctx: dict) -> str:
    summary = (
        f"Клиент «{customer.name}» — {'повторное' if ctx['repeat'] else 'первое'} обращение "
        f"({customer.visit_count} визитов). Основной канал: {ctx['top_source']}."
    )
    if customer.is_vip:
        summary += " Статус: VIP."
    pain_block = "Возможные боли: " + (", ".join(ctx["pains"]) if ctx["pains"] else "не выявлены явно")
    approach = (
        f"Рекомендуемый тон: {ctx['tone']}. "
        f"С какой стороны зайти: начните с уточнения цели, затем {ctx['offer'][0]}."
    )
    extras = []
    if customer.notes:
        extras.append(f"Заметки менеджера:\n{customer.notes[:400]}")
    waiting = ctx["statuses"].get("waiting", 0) + ctx["statuses"].get("in_progress", 0)
    if waiting:
        extras.append(f"Активных заявок в работе: {waiting} — приоритет на закрытие диалога.")
    if ctx["comments"]:
        extras.append(f"Комментариев менеджеров: {len(ctx['comments'])}")

    return "\n\n".join(
        [
            "🤖 AI-подсказка (локальный анализ)",
            summary,
            pain_block,
            approach,
            "Что предложить: " + "; ".join(ctx["offer"]),
            *extras,
        ]
    )


def _gemini_insight(customer, leads: list, ctx: dict) -> str | None:
    key = (settings.gemini_api_key or "").strip()
    if not key:
        return None

    lead_lines = []
    for l in leads[:12]:
        line = f"- [{_lead_status(l)} / {_lead_source(l)}] {l.message or '(без текста)'}"
        lead_lines.append(line)
        for c in getattr(l, "comments", []) or []:
            lead_lines.append(f"  · комментарий: {c.text}")

    prompt = f"""Ты CRM-аналитик для малого бизнеса в Казахстане. Проанализируй клиента и дай краткие практичные рекомендации менеджеру на русском языке.

Клиент: {customer.name}
Телефон: {customer.phone or '—'}
Email: {customer.email or '—'}
VIP: {'да' if customer.is_vip else 'нет'}
Визитов: {customer.visit_count}
Заметки: {customer.notes or '—'}

История обращений ({len(leads)}):
{chr(10).join(lead_lines) if lead_lines else 'нет заявок'}

Выявленные сигналы: {', '.join(ctx['pains'])}

Ответь структурированно (4–6 абзацев):
1) Краткий портрет клиента
2) Основные потребности и боли
3) Рекомендуемый тон общения
4) Что предложить сейчас
5) Риски (если есть)
6) Следующий шаг для менеджера"""

    try:
        r = httpx.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            params={"key": key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=45.0,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return f"🤖 AI-подсказка (Gemini)\n\n{text}"
    except Exception:
        return None


def generate_customer_insight(customer, leads: list) -> dict:
    ctx = _collect_context(customer, leads)
    gemini_text = _gemini_insight(customer, leads, ctx)
    source = "gemini" if gemini_text else "heuristic"
    insight = gemini_text or _heuristic_insight(customer, ctx)

    return {
        "insight": insight,
        "pains": ctx["pains"],
        "suggestions": ctx["offer"],
        "tone": ctx["tone"],
        "leads_count": ctx["leads_count"],
        "top_source": ctx["top_source"],
        "source": source,
        "generated_at": datetime.utcnow().isoformat(),
    }
