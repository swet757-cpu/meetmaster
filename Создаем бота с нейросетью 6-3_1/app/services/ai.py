from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pandas as pd
from openai import OpenAI


MAX_ACCOUNT_ROWS = 30
MAX_MAPPING_ROWS = 25


@dataclass(frozen=True)
class AiAnalysis:
    text: str
    skipped: bool = False


async def analyze_osv_with_ai(
    *,
    api_key: str | None,
    model: str,
    base_url: str | None,
    report: str,
    osv: pd.DataFrame,
    mapping: pd.DataFrame,
) -> AiAnalysis:
    if not api_key:
        return AiAnalysis(
            text=(
                "Нейросеть не подключена: в `.env` нет `OPENAI_API_KEY`.\n"
                "Правила проверки ОСВ уже отработали выше."
            ),
            skipped=True,
        )

    prompt = _build_prompt(report, osv, mapping)
    return await asyncio.to_thread(_request_ai_analysis, api_key, model, base_url, prompt)


def _request_ai_analysis(api_key: str, model: str, base_url: str | None, prompt: str) -> AiAnalysis:
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.responses.create(
        model=model,
        instructions=(
            "Ты финансовый аналитик для российского бухгалтера. "
            "Пиши по-русски, кратко и предметно. "
            "Не выдумывай цифры: используй только данные из входного текста. "
            "Если данных нет, пиши 'данных нет'. "
            "Сначала дай результат, потом коротко объясни логику. "
            "Не советуй менять исходные файлы без копии. "
            "Не используй Markdown-разметку: без жирного текста, без символов **."
        ),
        input=prompt,
        max_output_tokens=900,
    )
    return AiAnalysis(text=_clean_ai_text(response.output_text))


def _clean_ai_text(text: str) -> str:
    return text.replace("**", "").strip()


def _build_prompt(report: str, osv: pd.DataFrame, mapping: pd.DataFrame) -> str:
    account_summary = _account_summary(osv)
    mapping_summary = _mapping_summary(mapping)
    return "\n\n".join(
        [
            "Проверь ОСВ и маппинг P&L по рассчитанным данным.",
            "Отчет правил:",
            report,
            "Крупные строки ОСВ:",
            account_summary,
            "Строки маппинга:",
            mapping_summary,
            (
                "Дай ответ в формате:\n"
                "1. Вывод.\n"
                "2. Риски и аномалии.\n"
                "3. Что проверить бухгалтеру.\n"
                "Не пересчитывай суммы руками, опирайся на предоставленные факты."
            ),
        ]
    )


def _account_summary(osv: pd.DataFrame) -> str:
    columns = ["Счет", "ОборотДт", "ОборотКт", "КонДт", "КонКт"]
    existing = [column for column in columns if column in osv.columns]
    if not existing:
        return "данных нет"

    summary = osv[existing].copy()
    amount_columns = [column for column in existing if column != "Счет"]
    if amount_columns:
        summary["_abs_total"] = summary[amount_columns].abs().sum(axis=1)
        summary = summary.sort_values("_abs_total", ascending=False).drop(columns=["_abs_total"])

    return summary.head(MAX_ACCOUNT_ROWS).to_csv(index=False, sep=";")


def _mapping_summary(mapping: pd.DataFrame) -> str:
    columns = ["Активно", "Статья", "Счет mask", "Источник", "Знак", "Сумма"]
    existing = [column for column in columns if column in mapping.columns]
    if not existing:
        return "данных нет"
    return mapping[existing].head(MAX_MAPPING_ROWS).to_csv(index=False, sep=";")
