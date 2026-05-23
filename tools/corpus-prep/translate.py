#!/usr/bin/env python3
from __future__ import annotations

import argparse

from corpus_prep.models import DEFAULT_MODELS


def main() -> None:
    parser = argparse.ArgumentParser(description="Translate EN open-access source chunks to Russian.")
    parser.add_argument("--model", default=DEFAULT_MODELS["gemini_direct"])
    parser.parse_args()
    raise SystemExit("translate requires an API-backed translation pass; not run in offline validation.")


if __name__ == "__main__":
    main()
