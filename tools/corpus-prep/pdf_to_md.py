#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from corpus_prep.harvest import pdftotext_extract


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract text from a text PDF using local pdftotext.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    text = pdftotext_extract(args.pdf)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
