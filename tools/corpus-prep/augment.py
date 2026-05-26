#!/usr/bin/env python3
"""Corpus answer augmentation — distil thorough, source-grounded expert answers.

Each frozen-corpus row has a terse (but verified) answer + a 2000-char source_excerpt from
the official document. A strong frontier teacher rewrites the terse answer into a thorough,
structured, cited expert answer (matching the bench's answer style), GROUNDED in the verified
answer + source — no new unverified facts. This fixes the v0.1/v0.2 finding that the corpus's
~114-token answers taught the model to be terse, which the (verbosity-rewarding) bench punishes.

The original verified answer is the factual anchor; the teacher may only expand/structure it.

Usage:
  # pilot: print 8 before/after pairs, no write
  OPENROUTER_API_KEY=... python augment.py --in <train.jsonl> --limit 8 --print
  # full run -> writes augmented jsonl (incremental, resumable)
  OPENROUTER_API_KEY=... python augment.py --in <train.jsonl> --out <aug.jsonl> --model google/gemini-3.1-pro-preview
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

KEY = os.environ.get("OPENROUTER_API_KEY")
AGY = os.path.expanduser("~/.local/bin/agy")  # Antigravity CLI — free via Google AI Pro sub (Gemini 3.5 Flash)

SYSTEM = """Ты — эксперт по российскому и международному спорту: правила и регламенты федераций, методики тренировки, физиология, спортивная медицина, спортивное право и регламенты РФ (Минспорт, РУСАДА), история и менеджмент спорта.

Тебе дают ВОПРОС, КРАТКИЙ ПРОВЕРЕННЫЙ ОТВЕТ (эталон фактов) и ВЫДЕРЖКУ ИЗ ОФИЦИАЛЬНОГО ИСТОЧНИКА. Перепиши краткий ответ в развёрнутый, структурированный экспертный ответ на русском языке.

ЖЁСТКИЕ ПРАВИЛА:
- СОХРАНИ все факты, цифры, названия, даты и ссылки на конкретные статьи/приказы/правила из эталонного ответа и источника. НЕ добавляй непроверенных фактов и НЕ противоречь эталону. Если чего-то нет в эталоне/источнике — не выдумывай.
- Раскрой тему полно: дай определения, контекст, поясни термины, приведи относящиеся детали и практические примеры, опираясь на источник.
- Структурируй ответ: где уместно — нумерованные списки, подзаголовки, логические блоки.
- Цитируй конкретные нормы (номера статей, приказов, правил) там, где они есть в источнике.
- Объём — соответственно сложности: для простых вопросов 150–250 слов, для сложных/экспертных 300–500 слов.
- Пиши на грамотном русском. НЕ пиши преамбул вида «Вот развёрнутый ответ» или «Это интересный вопрос». Начинай сразу с сути. Не повторяй вопрос дословно."""

USER_TMPL = """ВОПРОС:
{q}

КРАТКИЙ ПРОВЕРЕННЫЙ ОТВЕТ (эталон фактов — сохрани всё):
{a}

ВЫДЕРЖКА ИЗ ОФИЦИАЛЬНОГО ИСТОЧНИКА:
{src}"""


def msg_of(row, role):
    return next(m["content"] for m in row["messages"] if m["role"] == role)


def call_agy(q, a, src):
    """Antigravity CLI headless (`agy -p`). Free via the Google AI Pro sub. Single combined prompt
    (no separate system role) — defaults to Gemini 3.5 Flash. No tools needed for a pure rewrite."""
    prompt = SYSTEM + "\n\n" + USER_TMPL.format(q=q, a=a, src=(src or "")[:2000])
    for attempt in range(3):
        try:
            r = subprocess.run([AGY, "-p", prompt], capture_output=True, text=True, timeout=300)
            out = (r.stdout or "").strip()
            if out and len(out) > len(a):  # must be a real expansion, not an echo/refusal
                return out, None
            return None, f"thin/empty (rc={r.returncode}): {(r.stderr or out)[:160]}"
        except subprocess.TimeoutExpired:
            if attempt == 2:
                return None, "timeout"
            time.sleep(3)
        except Exception as e:
            return None, str(e)[:200]


def call(model, q, a, src):
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": USER_TMPL.format(q=q, a=a, src=(src or "")[:2000])},
        ],
        "temperature": 0.3,
        "max_tokens": 4000,
        "reasoning": {"effort": "low"},   # teacher is a reasoning model — minimise hidden thinking so
                                          # the token budget goes to the ANSWER, not starved by reasoning
        "provider": {"sort": "price"},
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
                 "HTTP-Referer": "https://csylabs.com", "X-Title": "LII-Sport corpus augment"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read())
            c = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
            if c.strip():
                return c.strip(), None
            return None, "empty"
        except Exception as e:
            if attempt == 3:
                return None, str(e)[:200]
            time.sleep(2 * (attempt + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--engine", choices=["openrouter", "agy"], default="agy",
                    help="agy = Antigravity CLI (free, Gemini 3.5 Flash via AI Pro sub); openrouter = paid API")
    ap.add_argument("--model", default="google/gemini-3.1-pro-preview", help="openrouter engine only")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--print", dest="prnt", action="store_true", help="pilot: print before/after, no write")
    args = ap.parse_args()
    if args.engine == "openrouter" and not KEY:
        sys.exit("OPENROUTER_API_KEY not set")
    if args.engine == "agy" and not os.path.exists(AGY):
        sys.exit(f"agy not found at {AGY}")

    rows = [json.loads(l) for l in args.inp.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.limit:
        # diverse sample: spread across the file
        step = max(1, len(rows) // args.limit)
        rows = rows[::step][:args.limit]
    teacher = "agy/Gemini-3.5-Flash" if args.engine == "agy" else args.model
    print(f"{len(rows)} rows  ·  engine={args.engine}  ·  teacher={teacher}  ·  concurrency={args.concurrency}", file=sys.stderr)

    done = {}
    if args.out and args.out.exists():
        for l in args.out.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                done[r["id"]] = r
        print(f"  resuming: {len(done)} already augmented", file=sys.stderr)

    todo = [r for r in rows if r["id"] not in done]

    def work(row):
        q, a, src = msg_of(row, "user"), msg_of(row, "assistant"), row.get("source_excerpt")
        if args.engine == "agy":
            new, err = call_agy(q, a, src)
        else:
            new, err = call(args.model, q, a, src)
        return row, new, err

    results, ok, fail = [], 0, 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = [ex.submit(work, r) for r in todo]
        for i, f in enumerate(as_completed(futs), 1):
            row, new, err = f.result()
            if err:
                fail += 1
                continue
            ok += 1
            if args.prnt:
                q = msg_of(row, "user"); a = msg_of(row, "assistant")
                print("=" * 70)
                print(f"[{row['id']}] sport={row.get('sport')} cat={row.get('category')}")
                print(f"Q: {q[:160]}")
                print(f"--- ORIG ({len(a)} ch) ---\n{a}")
                print(f"--- AUGMENTED ({len(new)} ch) ---\n{new}\n")
            else:
                aug = dict(row)
                aug["messages"] = [
                    next(m for m in row["messages"] if m["role"] == "user"),
                    {"role": "assistant", "content": new},
                ]
                aug["augmented_by"] = args.model
                aug["original_answer"] = msg_of(row, "assistant")
                results.append(aug)
            if i % 20 == 0 or i == len(todo):
                print(f"  [{i}/{len(todo)}] ok={ok} fail={fail}", file=sys.stderr)
                if args.out and results:
                    with args.out.open("a", encoding="utf-8") as fh:
                        for r in results:
                            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                    results.clear()
    if args.out and results:
        with args.out.open("a", encoding="utf-8") as fh:
            for r in results:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"DONE ok={ok} fail={fail}", file=sys.stderr)


if __name__ == "__main__":
    main()
