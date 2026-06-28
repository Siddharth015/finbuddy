"""AI helpers backed by Groq (open Llama models) with offline fallbacks.

Every function degrades gracefully: if no ``GROQ_API_KEY`` is configured, or the
request fails, a deterministic local summary is returned so the product keeps
working for free.
"""
from __future__ import annotations

import json
import logging
from decimal import Decimal

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_TIMEOUT = httpx.Timeout(20.0)


async def _chat(system: str, user: str) -> str | None:
    """Call Groq's OpenAI-compatible chat endpoint. Returns None on failure."""
    if not settings.groq_api_key:
        return None
    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.4,
        "max_tokens": 600,
    }
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(_GROQ_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except (httpx.HTTPError, KeyError, json.JSONDecodeError) as exc:
        logger.warning("Groq request failed, using fallback: %s", exc)
        return None


async def monthly_summary(
    *,
    month: str,
    currency: str,
    total_spent: Decimal,
    total_income: Decimal,
    categories: list[tuple[str, Decimal]],
) -> tuple[str, list[str]]:
    """Return ``(summary, advice)`` for a monthly report."""
    net = total_income - total_spent
    breakdown = ", ".join(f"{c}: {currency} {a}" for c, a in categories[:6]) or "none"

    fallback_summary = (
        f"In {month} you spent {currency} {total_spent} and earned "
        f"{currency} {total_income}, a net of {currency} {net}. "
        f"Your biggest categories were {breakdown}."
    )
    fallback_advice = _fallback_advice(total_spent, total_income, categories)

    system = (
        "You are FinBuddy, a concise, friendly personal-finance coach. "
        "Reply in STRICT JSON: {\"summary\": string, \"advice\": [string, ...]}. "
        "Keep the summary to 2-3 sentences and give 3 short, specific tips. "
        "Never invent numbers that were not provided."
    )
    user = (
        f"Month: {month}\nCurrency: {currency}\n"
        f"Total spent: {total_spent}\nTotal income: {total_income}\n"
        f"Net: {net}\nCategory breakdown: {breakdown}"
    )
    content = await _chat(system, user)
    if not content:
        return fallback_summary, fallback_advice

    try:
        parsed = json.loads(_extract_json(content))
        summary = str(parsed.get("summary") or fallback_summary)
        advice = [str(a) for a in parsed.get("advice", []) if str(a).strip()]
        return summary, (advice or fallback_advice)
    except (json.JSONDecodeError, AttributeError):
        return content, fallback_advice


def _fallback_advice(
    total_spent: Decimal,
    total_income: Decimal,
    categories: list[tuple[str, Decimal]],
) -> list[str]:
    advice: list[str] = []
    if total_income > 0:
        rate = (total_income - total_spent) / total_income * 100
        if rate < 20:
            advice.append(
                f"Your savings rate is {rate:.0f}%. Aim for at least 20% by trimming "
                "discretionary spending."
            )
        else:
            advice.append(f"Great job saving {rate:.0f}% of your income this month.")
    if categories:
        top_cat, top_amt = categories[0]
        advice.append(
            f"'{top_cat}' was your largest category at {top_amt}. Set a monthly cap "
            "and track it weekly."
        )
    advice.append("Automate a fixed transfer to savings on payday so you save first.")
    return advice[:3]


def _extract_json(text: str) -> str:
    """Best-effort extraction of a JSON object from an LLM response."""
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text
