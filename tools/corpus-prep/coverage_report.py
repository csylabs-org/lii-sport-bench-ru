#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from corpus_prep.coverage import write_coverage_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Report corpus coverage by source, sport, category, license lane, and audience proxy.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--input-root", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    input_root = args.input_root or args.repo_root / "corpus" / "lii-sport-sft-v0.1-current-agy-clean"
    report = write_coverage_report(input_root=input_root, output_json=args.output_json, output_md=args.output_md)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
