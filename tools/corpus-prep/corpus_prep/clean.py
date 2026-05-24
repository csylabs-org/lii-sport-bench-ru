from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import Any


PII_PATTERNS = [
    re.compile(r"(?<!\d)(?:\+7|8)[\s\-()]*\d{3}[\s\-()]*\d{3}[\s\-()]*\d{2}[\s\-()]*\d{2}(?!\d)"),
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    re.compile(r"\b\d{3}-\d{3}-\d{3}\s?\d{2}\b"),  # SNILS
    re.compile(r"\b(?:\d{10}|\d{12})\b"),  # INN-like
    re.compile(r"\b\d{4}\s?\d{6}\b"),  # RU passport-like
]


def clean_examples(
    examples: list[dict[str, Any]],
    bench_questions: list[dict[str, Any]],
    *,
    min_chars: int = 100,
    max_chars: int = 8192 * 5,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    bench_texts = [_normalize(question["question"]) for question in bench_questions]
    seen: set[str] = set()
    kept: list[dict[str, Any]] = []
    dropped: Counter[str] = Counter()

    for example in examples:
        text = _example_text(example)
        normalized = _normalize(text)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

        if len(text) < min_chars:
            dropped["too_short"] += 1
            continue
        if len(text) > max_chars:
            dropped["too_long"] += 1
            continue
        if not example.get("license_kind") or example.get("license_verified") is False:
            dropped["license"] += 1
            continue
        if _has_extraction_noise(str(example.get("source_excerpt", ""))):
            dropped["extraction_noise"] += 1
            continue
        if _has_pii(text):
            dropped["pii"] += 1
            continue
        if digest in seen:
            dropped["duplicate"] += 1
            continue
        if _bench_leakage(normalized, bench_texts):
            dropped["bench_leakage"] += 1
            continue

        seen.add(digest)
        cleaned = dict(example)
        cleaned["content_hash"] = digest
        kept.append(cleaned)

    return kept, {"input": len(examples), "kept": len(kept), "dropped": dict(dropped)}


def _example_text(example: dict[str, Any]) -> str:
    parts = [str(example.get("text", ""))]
    for message in example.get("messages", []):
        parts.append(str(message.get("content", "")))
    return "\n".join(part for part in parts if part)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def _has_pii(text: str) -> bool:
    return any(pattern.search(text) for pattern in PII_PATTERNS)


def _has_extraction_noise(text: str) -> bool:
    if "\ufffd" in text:
        return True
    if re.search(r"[À-ÿ]{4,}", text):
        return True
    return False


def _bench_leakage(text: str, bench_texts: list[str]) -> bool:
    for bench_text in bench_texts:
        if len(bench_text) >= 30 and bench_text in text:
            return True
        if _token_jaccard(text, bench_text) >= 0.92:
            return True
    return False


def _token_jaccard(left: str, right: str) -> float:
    left_tokens = set(re.findall(r"[\w-]+", left))
    right_tokens = set(re.findall(r"[\w-]+", right))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
