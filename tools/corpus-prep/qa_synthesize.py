#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from corpus_prep.io import read_jsonl_tree
from corpus_prep.models import DEFAULT_MODELS
from corpus_prep.secrets import load_default_secret_env
from corpus_prep.synthesize import (
    agy_generate_text,
    filter_raw_examples,
    gemini_generate_text,
    normalize_model_for_provider,
    openrouter_generate_text,
    synthesize_examples,
    write_synthesized_jsonl,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate grounded Q&A from cleaned source chunks.")
    parser.add_argument("--model")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--input-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-examples", type=int, default=10)
    parser.add_argument("--questions-per-chunk", type=int, default=3)
    parser.add_argument("--provider", choices=["openrouter", "gemini-direct", "agy"], default="agy")
    parser.add_argument("--agy-timeout-seconds", type=int, default=300)
    parser.add_argument("--include-url-regex")
    parser.add_argument("--exclude-url-regex")
    args = parser.parse_args()

    input_root = args.input_root or args.repo_root / "corpus" / "raw"
    output = args.output or args.repo_root / "corpus" / "synth" / "sft.jsonl"
    raw_examples = filter_raw_examples(
        read_jsonl_tree(input_root),
        include_url_regex=args.include_url_regex,
        exclude_url_regex=args.exclude_url_regex,
    )
    secrets = load_default_secret_env()
    if args.model:
        requested_model = args.model
    elif args.provider == "agy":
        requested_model = DEFAULT_MODELS["agy_default"]
    elif args.provider == "gemini-direct":
        requested_model = DEFAULT_MODELS["gemini_direct"]
    else:
        requested_model = DEFAULT_MODELS["openrouter_bulk"]
    model = normalize_model_for_provider(requested_model, args.provider)

    def generate(prompt: str) -> str:
        if args.provider == "agy":
            return agy_generate_text(prompt, timeout_seconds=args.agy_timeout_seconds)
        if args.provider == "gemini-direct":
            gemini_key = secrets.get("GEMINI_API_KEY")
            if not gemini_key:
                raise SystemExit("GEMINI_API_KEY missing from vault root .env.local or Claude settings")
            return gemini_generate_text(gemini_key, prompt, model=model)
        openrouter_key = secrets.get("OPENROUTER_API_KEY")
        if not openrouter_key:
            raise SystemExit("OPENROUTER_API_KEY missing from vault root .env.local or llm-integrator .env.local")
        return openrouter_generate_text(openrouter_key, prompt, model=model)

    examples = synthesize_examples(
        raw_examples,
        generate,
        questions_per_chunk=args.questions_per_chunk,
        max_examples=args.max_examples,
        on_raw_start=lambda index, raw: print(
            f"[{index}/{min(args.max_examples, len(raw_examples))}] {raw.get('id')} {raw.get('url', '')}",
            file=sys.stderr,
            flush=True,
        ),
    )
    write_synthesized_jsonl(output, examples)
    print(json.dumps({"input": len(raw_examples), "written": len(examples), "output": str(output), "model": model}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
