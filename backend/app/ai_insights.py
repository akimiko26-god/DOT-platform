"""Генерация подсказок по клиенту (эвристика; при наличии OPENAI_API_KEY — расширяемо)."""

import json
import re
from collections import Counter

PAIN_WORDS = {
    "дорого": "чувствительность к цене",
    "цена": "важен прайс и прозрачность условий",
    "срочно": "нужен быстрый ответ",
    "жалоб": "есть недовольство — важно восстановить доверие",
    "не работает": "техническая проблема",
    "скидк": "ожидает выгодное предложение",
    "конкурент": "сравнивает с альтернативами",
    "повтор": "заинтересован в долгосрочном сотрудничестве",
}


def _parse_tags(raw: str) -> list[str]:
    if not raw:
        return []
    try:
        return json.loads(raw) if raw.startswith("[") else [t.strip() for t in raw.split(",") if t.strip()]
    except json.JSONDecodeError:
        return []


def generate_customer_insight(customer, leads: list) -> dict:
    messages = [l.message or "" for l in leads if l.message]
    combined = " ".join(messages).lower()
    pains = []
    for word, label in PAIN_WORDS.items():
        if word in combined:
            pains.append(label)
    if not pains and messages:
        pains.append("стандартный запрос без явных негативных сигналов")

    sources = Counter(l.source.value if hasattr(l.source, "value") else str(l.source) for l in leads)
    top_source = sources.most_common(1)[0][0] if sources else "неизвестно"
    statuses = Counter(l.status.value if hasattr(l.status, "value") else str(l.status) for l in leads)

    repeat = customer.visit_count > 1
    tone = "теплый и персональный" if repeat else "информативный и убедительный"

    offer = []
    if "цен" in combined or "дорого" in combined:
        offer.append("предложить пакет со скидкой или рассрочку")
    if repeat:
        offer.append("напомнить про прошлый успешный опыт и бонусы лояльности")
    if "срочно" in combined:
        offer.append("зафиксировать SLA ответа и приоритетную линию")
    if not offer:
        offer.append("уточнить потребность и предложить 2–3 релевантных варианта из каталога")

    summary = (
        f"Клиент «{customer.name}» — {'повторное' if repeat else 'первое'} обращение "
        f"({customer.visit_count} визитов). Основной канал: {top_source}."
    )
    pain_block = "Возможные боли: " + (", ".join(pains) if pains else "не выявлены явно")
    approach = f"Рекомендуемый тон: {tone}. С какой стороны зайти: начните с уточнения цели, затем {offer[0]}."
    extras = []
    if customer.notes:
        extras.append(f"Заметки менеджера: {customer.notes[:200]}")
    if statuses.get("waiting", 0) + statuses.get("waiting", 0):
        extras.append("Есть ожидающие ответа заявки — приоритет на закрытие диалога.")

    full_text = "\n\n".join(
        [
            "🤖 AI-подсказка",
            summary,
            pain_block,
            approach,
            "Что предложить: " + "; ".join(offer),
            *extras,
        ]
    )

    return {
        "insight": full_text,
        "pains": pains,
        "suggestions": offer,
        "tone": tone,
        "leads_count": len(leads),
        "top_source": top_source,
    }
