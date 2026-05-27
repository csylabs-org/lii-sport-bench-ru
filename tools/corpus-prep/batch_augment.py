#!/usr/bin/env python3
"""Corpus augmentation via the Gemini Batch API — 50% cheaper than sync, async (<=24h, usually fast).

Same SYSTEM/USER prompt as augment.py (imported — single source of truth). Builds a JSONL of
GenerateContentRequests, uploads, creates a batch job, polls, downloads, and appends augmented rows
to --out in the SAME format as the agy/openrouter engine (so v0.3 training reads one merged file).
Resumable: skips rows already in --out. Reasoning disabled (thinkingBudget 0) so the budget goes to
the answer, not hidden thinking (the v0.1/v0.2 content-starvation gotcha).

Run with the venv:  ~/.venvs/gembatch/bin/python batch_augment.py --in <train.jsonl> --out <v0.3 train.jsonl>
"""
from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from augment import SYSTEM, USER_TMPL, msg_of   # reuse the validated prompt

from google import genai
from google.genai import types

KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-3.5-flash"


def build_request(row):
    q, a, src = msg_of(row, "user"), msg_of(row, "assistant"), row.get("source_excerpt")
    user = USER_TMPL.format(q=q, a=a, src=(src or "")[:2000])
    return {
        "key": row["id"],
        "request": {
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "systemInstruction": {"parts": [{"text": SYSTEM}]},
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 2048,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        },
    }


def run_one_batch(client, chunk, out_path, workdir, poll):
    """Submit one chunk as a batch job, poll, download, append augmented rows to out_path."""
    by_key = {r["id"]: r for r in chunk}
    inp = workdir / "batch_input.jsonl"
    with inp.open("w", encoding="utf-8") as f:
        for r in chunk:
            f.write(json.dumps(build_request(r), ensure_ascii=False) + "\n")
    uploaded = client.files.upload(
        file=str(inp), config=types.UploadFileConfig(display_name="lii-aug", mime_type="application/jsonl"))
    job = client.batches.create(model=MODEL, src=uploaded.name)
    print(f"  batch {job.name} ({len(chunk)} rows) ...", file=sys.stderr)
    while True:
        job = client.batches.get(name=job.name)
        st = str(job.state)
        if any(x in st for x in ("SUCCEEDED", "FAILED", "CANCELLED", "EXPIRED")):
            break
        time.sleep(poll)
    if "SUCCEEDED" not in str(job.state):
        raise RuntimeError(f"batch ended {job.state}: {getattr(job,'error',None)}")
    raw = client.files.download(file=job.dest.file_name)
    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
    ok = fail = 0
    with out_path.open("a", encoding="utf-8") as out:
        for l in text.splitlines():
            if not l.strip():
                continue
            d = json.loads(l)
            key = d.get("key")
            try:
                ans = d["response"]["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception:
                ans = ""
            if not ans or key not in by_key:
                fail += 1
                continue
            row = by_key[key]
            aug = dict(row)
            aug["messages"] = [next(m for m in row["messages"] if m["role"] == "user"),
                               {"role": "assistant", "content": ans}]
            aug["augmented_by"] = MODEL + "-batch"
            aug["original_answer"] = msg_of(row, "assistant")
            out.write(json.dumps(aug, ensure_ascii=False) + "\n")
            ok += 1
    return ok, fail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--chunk", type=int, default=500, help="rows per batch job (Tier-1 enqueued-token limit)")
    ap.add_argument("--poll", type=int, default=30)
    args = ap.parse_args()
    if not KEY:
        sys.exit("GEMINI_API_KEY not set")

    rows = [json.loads(l) for l in args.inp.read_text(encoding="utf-8").splitlines() if l.strip()]
    done = set()
    if args.out.exists():
        for l in args.out.read_text(encoding="utf-8").splitlines():
            if l.strip():
                done.add(json.loads(l)["id"])
    todo = [r for r in rows if r["id"] not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(todo)} to augment (of {len(rows)}; {len(done)} done)  chunk={args.chunk}", file=sys.stderr)
    if not todo:
        return

    client = genai.Client(api_key=KEY)
    workdir = args.out.parent
    total_ok = total_fail = 0
    n_chunks = (len(todo) + args.chunk - 1) // args.chunk
    for i in range(0, len(todo), args.chunk):
        chunk = todo[i:i + args.chunk]
        cn = i // args.chunk + 1
        print(f"[chunk {cn}/{n_chunks}] {time.strftime('%H:%M:%S')}", file=sys.stderr)
        ok, fail = run_one_batch(client, chunk, args.out, workdir, args.poll)
        total_ok += ok; total_fail += fail
        print(f"[chunk {cn}/{n_chunks}] ok={ok} fail={fail}  (cum ok={total_ok} fail={total_fail})", file=sys.stderr)
    print(f"ALL DONE ok={total_ok} fail={total_fail}", file=sys.stderr)


if __name__ == "__main__":
    main()
