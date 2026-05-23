from __future__ import annotations

from pathlib import Path
from typing import Any

from corpus_prep.clean import clean_examples
from corpus_prep.io import read_bench_questions, read_jsonl_tree
from corpus_prep.manifest import write_release_artifacts
from corpus_prep.splits import make_splits


def run_validation_batch(
    repo_root: Path,
    *,
    output_name: str = "lii-sport-sft-v0.1",
    input_root: Path | None = None,
    max_input_bytes: int = 200 * 1024 * 1024,
) -> dict[str, Any]:
    raw_root = input_root or repo_root / "corpus" / "raw"
    raw_size = _tree_size(raw_root)
    if raw_size > max_input_bytes:
        raise ValueError(f"raw validation batch is {raw_size} bytes; limit is {max_input_bytes}")

    raw_examples = read_jsonl_tree(raw_root)
    bench_questions = read_bench_questions(repo_root / "data" / "questions.json")
    cleaned, clean_report = clean_examples(raw_examples, bench_questions)

    output_dir = repo_root / "corpus" / output_name
    split_manifest = make_splits(cleaned, output_dir)
    write_release_artifacts(output_dir, cleaned, split_manifest, clean_report)
    return {"raw_bytes": raw_size, "raw_examples": len(raw_examples), "clean": clean_report, "output_dir": str(output_dir)}


def _tree_size(root: Path) -> int:
    if not root.exists():
        return 0
    if root.is_file():
        return root.stat().st_size
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
