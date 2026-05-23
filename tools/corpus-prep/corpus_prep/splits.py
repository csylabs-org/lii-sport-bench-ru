from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


def make_splits(examples: list[dict[str, Any]], output_dir: Path, *, seed: int = 42) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for example in examples:
        buckets[(str(example.get("sport", "unknown")), str(example.get("category", "unknown")))].append(example)

    rng = random.Random(seed)
    splits = {"train": [], "val": [], "test": []}
    for bucket_examples in buckets.values():
        shuffled = list(bucket_examples)
        rng.shuffle(shuffled)
        for index, example in enumerate(shuffled):
            ratio = index / max(len(shuffled), 1)
            if ratio < 0.90:
                splits["train"].append(example)
            elif ratio < 0.95:
                splits["val"].append(example)
            else:
                splits["test"].append(example)

    manifest_splits: dict[str, Any] = {}
    for split_name, rows in splits.items():
        path = output_dir / f"{split_name}.jsonl"
        _write_jsonl(path, rows)
        manifest_splits[split_name] = {
            "count": len(rows),
            "sha256": _file_sha256(path),
            "ids": [row["id"] for row in rows],
        }

    manifest = {"total_examples": len(examples), "splits": manifest_splits, "seed": seed}
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
