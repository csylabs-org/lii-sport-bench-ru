import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { join } from "path";
import type { Question, CandidateOutput } from "./types.ts";

// Candidate endpoint: default OpenRouter, override CANDIDATE_BASE_URL to point at any
// OpenAI-compatible /chat/completions endpoint (e.g. a local llama.cpp server for same-stack A/B).
const BASE_URL = process.env.CANDIDATE_BASE_URL ?? "https://openrouter.ai/api/v1/chat/completions";
const IS_OR = BASE_URL.includes("openrouter.ai");
const KEY = process.env.OPENROUTER_API_KEY ?? "sk-local-dummy";
if (IS_OR && !process.env.OPENROUTER_API_KEY) throw new Error("OPENROUTER_API_KEY not set in env");

const MODEL = process.env.MODEL;
if (!MODEL) throw new Error("MODEL not set (e.g. MODEL=google/gemma-4-31b-it)");

const INPUT_FILE = process.env.INPUT ?? "pilot-200.json";
const CONCURRENCY = parseInt(process.env.CONCURRENCY ?? "5", 10);
const SEED = process.env.SEED ?? "lii-2026-05-13";
const MAX_TOKENS = parseInt(process.env.MAX_TOKENS ?? "2048", 10);

const IN = join(import.meta.dir, "..", "data", INPUT_FILE);
const SYS_PROMPT_BASE = readFileSync(join(import.meta.dir, "..", "prompts", "candidate-system.md"), "utf-8");
// Optional suffix appended to the system prompt (e.g. force thoroughness for a length-controlled A/B).
const SYS_SUFFIX = process.env.SYS_SUFFIX ?? "";
const SYS_PROMPT = SYS_SUFFIX ? SYS_PROMPT_BASE + "\n\n" + SYS_SUFFIX : SYS_PROMPT_BASE;
const OUT_DIR = join(import.meta.dir, "..", "data", "outputs");
mkdirSync(OUT_DIR, { recursive: true });
const MODEL_SAFE = MODEL.replace(/\//g, "__");
const OUT = join(OUT_DIR, `${MODEL_SAFE}.json`);

const questions: Question[] = JSON.parse(readFileSync(IN, "utf-8"));

let existing: CandidateOutput[] = [];
if (existsSync(OUT)) {
  existing = JSON.parse(readFileSync(OUT, "utf-8"));
  console.log(`  Resuming: ${existing.length} prior outputs in ${OUT}`);
}
const doneIds = new Set(existing.filter(o => o.ok).map(o => o.question_id));
const todo = questions.filter(q => !doneIds.has(q.id));

console.log(`Running ${MODEL} on ${todo.length}/${questions.length} questions (concurrency=${CONCURRENCY})`);

async function callOR(q: Question): Promise<CandidateOutput> {
  const start = performance.now();
  try {
    const resp = await fetch(BASE_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${KEY}`,
        "Content-Type": "application/json",
        "HTTP-Referer": "https://csylabs.com",
        "X-Title": "LII-Sport-Bench-RU v0.1",
      },
      body: JSON.stringify({
        model: MODEL,
        messages: [
          { role: "system", content: SYS_PROMPT },
          { role: "user", content: q.question },
        ],
        max_tokens: MAX_TOKENS,
        temperature: 0,
        seed: hash32(SEED + ":" + q.id),
        ...(IS_OR ? { provider: { sort: "price" } } : {}),
      }),
    });
    const elapsed_ms = Math.round(performance.now() - start);
    if (!resp.ok) {
      const body = await resp.text();
      return {
        question_id: q.id,
        model: MODEL,
        content: "",
        prompt_tokens: 0,
        completion_tokens: 0,
        elapsed_ms,
        ok: false,
        error: `HTTP ${resp.status}: ${body.slice(0, 300)}`,
      };
    }
    const data = await resp.json();
    if (data.error) {
      return {
        question_id: q.id,
        model: MODEL,
        content: "",
        prompt_tokens: 0,
        completion_tokens: 0,
        elapsed_ms,
        ok: false,
        error: JSON.stringify(data.error).slice(0, 300),
      };
    }
    const choice = data.choices?.[0];
    return {
      question_id: q.id,
      model: MODEL,
      content: choice?.message?.content ?? "",
      prompt_tokens: data.usage?.prompt_tokens ?? 0,
      completion_tokens: data.usage?.completion_tokens ?? 0,
      elapsed_ms,
      ok: !!choice?.message?.content,
      error: choice?.message?.content ? undefined : "empty response",
    };
  } catch (e: any) {
    return {
      question_id: q.id,
      model: MODEL,
      content: "",
      prompt_tokens: 0,
      completion_tokens: 0,
      elapsed_ms: Math.round(performance.now() - start),
      ok: false,
      error: String(e).slice(0, 300),
    };
  }
}

function hash32(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return Math.abs(h | 0);
}

async function pool<T>(items: T[], n: number, worker: (item: T, i: number) => Promise<CandidateOutput>): Promise<CandidateOutput[]> {
  const results: CandidateOutput[] = new Array(items.length);
  let cursor = 0;
  async function loop() {
    while (true) {
      const i = cursor++;
      if (i >= items.length) return;
      results[i] = await worker(items[i], i);
      if ((i + 1) % 10 === 0 || i + 1 === items.length) {
        const ok = results.filter(r => r?.ok).length;
        const failed = results.filter(r => r && !r.ok).length;
        console.log(`  [${i + 1}/${items.length}] ok=${ok} failed=${failed}`);
        writeFileSync(OUT, JSON.stringify([...existing, ...results.filter(Boolean)], null, 2));
      }
    }
  }
  await Promise.all(Array.from({ length: n }, () => loop()));
  return results;
}

const fresh = await pool(todo, CONCURRENCY, callOR);
const all = [...existing.filter(o => o.ok || !todo.find(q => q.id === o.question_id)), ...fresh];
writeFileSync(OUT, JSON.stringify(all, null, 2));

const okCount = all.filter(o => o.ok).length;
const failCount = all.length - okCount;
const totalIn = all.reduce((s, o) => s + o.prompt_tokens, 0);
const totalOut = all.reduce((s, o) => s + o.completion_tokens, 0);
console.log(`\n✅ ${MODEL}`);
console.log(`   Outputs: ${okCount} ok / ${failCount} failed (total ${all.length})`);
console.log(`   Tokens: ${totalIn} in / ${totalOut} out`);
console.log(`   Output: ${OUT}`);
