#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from corpus_prep.chunk import write_chunked_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Create balanced section chunks from harvested raw JSONL.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--input-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--chunks-per-source", type=int, default=8)
    parser.add_argument("--chunk-chars", type=int, default=5600)
    parser.add_argument("--min-chars", type=int, default=800)
    parser.add_argument("--source-id", action="append", help="Limit chunking to one source id; repeatable.")
    parser.add_argument("--include-existing-chunks", action="store_true", help="Allow re-chunking rows that already have chunk_strategy metadata.")
    parser.add_argument("--batch-id", help="Optional id segment added before section-NN to avoid collisions between scale batches.")
    args = parser.parse_args()

    input_root = args.input_root or args.repo_root / "corpus" / "raw"
    output = args.output or args.repo_root / "corpus" / "raw" / "section-chunks-current" / "harvest.jsonl"
    chunks = write_chunked_jsonl(
        input_root=input_root,
        output=output,
        chunks_per_source=args.chunks_per_source,
        chunk_chars=args.chunk_chars,
        min_chars=args.min_chars,
        source_ids=set(args.source_id) if args.source_id else None,
        include_existing_chunks=args.include_existing_chunks,
        batch_id=args.batch_id,
    )
    print(
        json.dumps(
            {
                "input_root": str(input_root),
                "output": str(output),
                "written": len(chunks),
                "by_source": dict(sorted(Counter(str(row.get("source_id")) for row in chunks).items())),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
