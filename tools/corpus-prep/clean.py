#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from corpus_prep.pipeline import run_validation_batch


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean raw corpus JSONL and write validation-batch splits.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--input-root", type=Path)
    parser.add_argument("--output-name", default="lii-sport-sft-v0.1")
    parser.add_argument("--max-input-mb", type=int, default=200)
    args = parser.parse_args()

    report = run_validation_batch(
        args.repo_root,
        output_name=args.output_name,
        input_root=args.input_root,
        max_input_bytes=args.max_input_mb * 1024 * 1024,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
