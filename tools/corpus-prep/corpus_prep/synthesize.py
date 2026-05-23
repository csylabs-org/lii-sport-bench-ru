from __future__ import annotations

import json
import re
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Callable

from corpus_prep.models import DEFAULT_MODELS


GenerateFn = Callable[[str], str]
ProgressFn = Callable[[int, dict[str, Any]], None]


def synthesize_examples(
    raw_examples: list[dict[str, Any]],
    generate: GenerateFn,
    *,
    questions_per_chunk: int = 3,
    max_examples: int | None = None,
    on_raw_start: ProgressFn | None = None,
) -> list[dict[str, Any]]:
    synthesized: list[dict[str, Any]] = []
    for raw_index, raw in enumerate(raw_examples[:max_examples], start=1):
        text = str(raw.get("text", "")).strip()
        if len(text) < 200:
            continue
        if on_raw_start:
            on_raw_start(raw_index, raw)
        response = generate(_prompt_for_raw(raw, questions_per_chunk=questions_per_chunk))
        for index, qa in enumerate(_parse_qa_json(response), start=1):
            question = str(qa.get("question", "")).strip()
            answer = str(qa.get("answer", "")).strip()
            if not question or not answer:
                continue
            synthesized.append(
                {
                    "id": f"{raw['id']}-qa-{index}",
                    "source_id": raw["source_id"],
                    "source_url": raw.get("url"),
                    "license_kind": raw["license_kind"],
                    "license_verified": raw["license_verified"],
                    "requires_human_approval": bool(raw.get("requires_human_approval", False)),
                    "sport": raw.get("sport", "general"),
                    "category": raw.get("category", "general"),
                    "text": f"{question}\n{answer}",
                    "source_excerpt": scrub_pii(text[:2000]),
                    "messages": [
                        {"role": "user", "content": question},
                        {"role": "assistant", "content": answer},
                    ],
                }
            )
    return synthesized


def filter_raw_examples(
    raw_examples: list[dict[str, Any]],
    *,
    include_url_regex: str | None = None,
    exclude_url_regex: str | None = None,
) -> list[dict[str, Any]]:
    include = re.compile(include_url_regex) if include_url_regex else None
    exclude = re.compile(exclude_url_regex) if exclude_url_regex else None
    filtered: list[dict[str, Any]] = []
    for row in raw_examples:
        url = str(row.get("url", ""))
        if include and not include.search(url):
            continue
        if exclude and exclude.search(url):
            continue
        filtered.append(row)
    return filtered


def scrub_pii(text: str) -> str:
    text = re.sub(r"(?<!\d)(?:\+7|8)[\s\-()]*\d{3}[\s\-()]*\d{3}[\s\-()]*\d{2}[\s\-()]*\d{2}(?!\d)", "[PHONE]", text)
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL]", text)
    text = re.sub(r"\b\d{3}-\d{3}-\d{3}\s?\d{2}\b", "[SNILS]", text)
    return text


def write_synthesized_jsonl(path: Path, examples: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for example in examples:
            handle.write(json.dumps(example, ensure_ascii=False, sort_keys=True) + "\n")


def gemini_generate_text(api_key: str, prompt: str, *, model: str = DEFAULT_MODELS["gemini_direct"]) -> str:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 2048,
            "temperature": 0.2,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["candidates"][0]["content"]["parts"][0]["text"]


def openrouter_generate_text(api_key: str, prompt: str, *, model: str = DEFAULT_MODELS["openrouter_bulk"]) -> str:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048,
        "temperature": 0.2,
        "reasoning": {"effort": "minimal"},
    }
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def agy_generate_text(
    prompt: str,
    *,
    timeout_seconds: int = 300,
    command: str = "agy",
    runner: Callable[..., Any] = subprocess.run,
) -> str:
    result = runner(
        [command, "--print", prompt, "--print-timeout", f"{timeout_seconds}s"],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds + 15,
    )
    return str(result.stdout).strip()


def normalize_model_for_provider(model: str, provider: str) -> str:
    if provider == "gemini-direct" and model.startswith("google/"):
        return model.split("/", 1)[1]
    return model


def _prompt_for_raw(raw: dict[str, Any], *, questions_per_chunk: int) -> str:
    source_text = _sample_source_text(scrub_pii(str(raw.get("text", ""))))
    return (
        "Сгенерируй grounded SFT пары вопрос-ответ на русском языке для модели ЛИИ-Спорт.\n"
        f"Количество пар: {questions_per_chunk}.\n"
        "Требования: ответ должен опираться только на источник; без персональных данных; "
        "без выдуманных ссылок; стиль ВУЗ/СШОР, ясно и прикладно.\n"
        "Игнорируй меню сайта, футер, контакты, адреса, cookie/legal boilerplate, списки новостей "
        "и любые вопросы о структуре сайта. Вопросы должны быть только по содержательному спортивному, "
        "методическому, медицинскому или регуляторному материалу источника.\n"
        "Если источник длинный, используй разные фрагменты текста, а не только начало документа.\n"
        "Верни только JSON array вида [{\"question\":\"...\",\"answer\":\"...\"}].\n\n"
        f"Источник: {raw.get('source_id')} {raw.get('url', '')}\n"
        f"Категория: {raw.get('category', 'general')}\n"
        f"Текст:\n{source_text}"
    )


def _sample_source_text(text: str, *, max_chars: int = 6000, segment_chars: int = 2000) -> str:
    normalized = text.strip()
    if len(normalized) <= max_chars:
        return normalized

    middle_start = max(0, (len(normalized) // 2) - (segment_chars // 2))
    middle_end = min(len(normalized), middle_start + segment_chars)
    return "\n\n".join(
        [
            f"[НАЧАЛО ДОКУМЕНТА]\n{normalized[:segment_chars]}",
            f"[СЕРЕДИНА ДОКУМЕНТА]\n{normalized[middle_start:middle_end]}",
            f"[КОНЕЦ ДОКУМЕНТА]\n{normalized[-segment_chars:]}",
        ]
    )


def _parse_qa_json(text: str) -> list[dict[str, Any]]:
    stripped = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", stripped, flags=re.DOTALL)
    if fenced:
        stripped = fenced.group(1).strip()
    if not stripped.startswith("["):
        match = re.search(r"(\[.*)", stripped, flags=re.DOTALL)
        if match:
            stripped = match.group(1)
    data, _end = json.JSONDecoder().raw_decode(stripped)
    if not isinstance(data, list):
        raise ValueError("synthesis response must be a JSON array")
    return [item for item in data if isinstance(item, dict)]
