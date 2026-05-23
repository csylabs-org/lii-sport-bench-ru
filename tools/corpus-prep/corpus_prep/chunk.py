from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from corpus_prep.io import read_jsonl_tree


def chunk_raw_examples(
    raw_examples: list[dict[str, Any]],
    *,
    chunks_per_source: int,
    chunk_chars: int = 5600,
    min_chars: int = 800,
    source_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in raw_examples:
        source_id = str(row.get("source_id", "unknown"))
        if source_ids is not None and source_id not in source_ids:
            continue
        grouped.setdefault(source_id, []).append(row)

    chunks: list[dict[str, Any]] = []
    for source_id in sorted(grouped):
        source_chunks: list[dict[str, Any]] = []
        for row in grouped[source_id]:
            source_chunks.extend(
                _chunks_for_row(
                    row,
                    chunk_chars=chunk_chars,
                    min_chars=min_chars,
                    max_chunks=chunks_per_source,
                )
            )
        chunks.extend(source_chunks[:chunks_per_source])
    return chunks


def write_chunked_jsonl(
    *,
    input_root: Path,
    output: Path,
    chunks_per_source: int,
    chunk_chars: int = 5600,
    min_chars: int = 800,
    source_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    chunks = chunk_raw_examples(
        read_jsonl_tree(input_root),
        chunks_per_source=chunks_per_source,
        chunk_chars=chunk_chars,
        min_chars=min_chars,
        source_ids=source_ids,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in chunks:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return chunks


def _chunks_for_row(
    row: dict[str, Any],
    *,
    chunk_chars: int,
    min_chars: int,
    max_chunks: int,
) -> list[dict[str, Any]]:
    text = re.sub(r"\s+", " ", str(row.get("text", ""))).strip()
    if len(text) < min_chars:
        return []

    possible_chunks = max(1, math.ceil(len(text) / chunk_chars))
    take = min(max_chunks, possible_chunks)
    starts = _even_starts(len(text), chunk_chars=chunk_chars, count=take)
    chunks: list[dict[str, Any]] = []
    for index, start in enumerate(starts, start=1):
        chunk_text = text[start : start + chunk_chars].strip()
        if len(chunk_text) < min_chars:
            continue
        chunk = dict(row)
        chunk["id"] = f"{row['id']}-section-{index:02d}"
        chunk["text"] = chunk_text
        chunk["source_title"] = f"{row.get('source_title') or row.get('id')} [section {index}]"
        chunk["chunk_index"] = index
        chunk["chunk_chars"] = len(chunk_text)
        chunk["chunk_strategy"] = "even-window-v1"
        chunks.append(chunk)
    return chunks


def _even_starts(text_len: int, *, chunk_chars: int, count: int) -> list[int]:
    if count <= 1:
        return [0]
    max_start = max(0, text_len - chunk_chars)
    return [round(index * max_start / (count - 1)) for index in range(count)]
