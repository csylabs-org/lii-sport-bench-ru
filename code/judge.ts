import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { join } from "path";
import type { Question, CandidateOutput, JudgeScore } from "./types.ts";

const KEY = process.env.OPENROUTER_API_KEY;
if (!KEY) throw new Error("OPENROUTER_API_KEY not set");

const CANDIDATE = process.env.CANDIDATE;
if (!CANDIDATE) throw new Error("CANDIDATE not set (e.g. CANDIDATE=google/gemma-4-31b-it)");

const JUDGE = process.env.JUDGE;
if (!JUDGE) throw new Error("JUDGE not set (e.g. JUDGE=google/gemini-3.1-pro-preview)");

const INPUT_FILE = process.env.INPUT ?? "pilot-200.json";
const CONCURRENCY = parseInt(process.env.CONCURRENCY ?? "5", 10);
const MAX_TOKENS = parseInt(process.env.MAX_TOKENS ?? "4000", 10);

const IN = join(import.meta.dir, "..", "data", INPUT_FILE);
const SYS_PROMPT = readFileSync(join(import.meta.dir, "..", "prompts", "judge-system.md"), "utf-8");

const OUT_DIR = join(import.meta.dir, "..", "data", "scores");
mkdirSync(OUT_DIR, { recursive: true });
const CAND_SAFE = CANDIDATE.replace(/\//g, "__");
const JUDGE_SAFE = JUDGE.replace(/\//g, "__");
const OUT = join(OUT_DIR, `${CAND_SAFE}__by__${JUDGE_SAFE}.json`);

const CAND_OUT_FILE = join(import.meta.dir, "..", "data", "outputs", `${CAND_SAFE}.json`);

const questions: Question[] = JSON.parse(readFileSync(IN, "utf-8"));
const candidateOutputs: CandidateOutput[] = JSON.parse(readFileSync(CAND_OUT_FILE, "utf-8"));
const byQid = new Map(candidateOutputs.map(o => [o.question_id, o]));

let existing: JudgeScore[] = [];
if (existsSync(OUT)) {
  existing = JSON.parse(readFileSync(OUT, "utf-8"));
  console.log(`  Resuming: ${existing.length} prior scores`);
}
const doneIds = new Set(existing.filter(s => s.ok).map(s => s.question_id));

const todo = questions
  .filter(q => !doneIds.has(q.id))
  .filter(q => {
    const o = byQid.get(q.id);
    return o && o.ok;
  });

console.log(`Judging ${CANDIDATE} via ${JUDGE} on ${todo.length}/${questions.length} questions (concurrency=${CONCURRENCY})`);

function buildPrompt(q: Question, candidateAnswer: string): string {
  return `**ВОПРОС:**
${q.question}

**ЭТАЛОННЫЙ ОТВЕТ:**
${q.reference_answer}

**КРИТЕРИИ ОЦЕНКИ (рубрика из бенчмарка):**
${q.rubric}

**МЕТА:** ID=${q.id} · аудитория=${q.audience} · сложность=${q.difficulty}${q.is_mcq ? " · MCQ" : ""}

**ОТВЕТ КАНДИДАТА:**
${candidateAnswer}

Оцени ответ кандидата по 4 измерениям. Верни только JSON.`;
}

function safeJSON(s: string): any {
  const trimmed = s.trim().replace(/^```(?:json)?\s*/i, "").replace(/```\s*$/, "");
  try { return JSON.parse(trimmed); } catch {}
  const match = trimmed.match(/\{[\s\S]*\}/);
  if (match) { try { return JSON.parse(match[0]); } catch {} }
  return null;
}

function clamp01_10(v: any): number {
  const n = Number(v);
  if (!isFinite(n)) return 0;
  return Math.max(0, Math.min(10, Math.round(n)));
}

async function callJudge(q: Question): Promise<JudgeScore> {
  const cand = byQid.get(q.id)!;
  const prompt = buildPrompt(q, cand.content);
  try {
    const resp = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${KEY}`,
        "Content-Type": "application/json",
        "HTTP-Referer": "https://csylabs.com",
        "X-Title": "LII-Sport-Bench-RU v0.1 - judge",
      },
      body: JSON.stringify({
        model: JUDGE,
        messages: [
          { role: "system", content: SYS_PROMPT },
          { role: "user", content: prompt },
        ],
        max_tokens: MAX_TOKENS,
        temperature: 0,
        response_format: { type: "json_object" },
        reasoning: { effort: "low" },
        provider: { sort: "price" },
      }),
    });
    if (!resp.ok) {
      const body = await resp.text();
      return failed(q, `HTTP ${resp.status}: ${body.slice(0, 200)}`);
    }
    const data = await resp.json();
    if (data.error) return failed(q, JSON.stringify(data.error).slice(0, 200));
    const content = data.choices?.[0]?.message?.content ?? "";
    const parsed = safeJSON(content);
    if (!parsed) return failed(q, `unparseable: ${content.slice(0, 200)}`);
    const a = clamp01_10(parsed.accuracy);
    const c = clamp01_10(parsed.completeness);
    const b = clamp01_10(parsed.bonus);
    const r = clamp01_10(parsed.ru_linguistic);
    return {
      question_id: q.id,
      candidate_model: CANDIDATE,
      judge_model: JUDGE,
      accuracy: a,
      completeness: c,
      bonus: b,
      ru_linguistic: r,
      overall: Math.round(((a + c + b + r) / 4) * 100) / 100,
      reasoning: String(parsed.reasoning ?? "").slice(0, 500),
      ok: true,
    };
  } catch (e: any) {
    return failed(q, String(e).slice(0, 200));
  }
}

function failed(q: Question, error: string): JudgeScore {
  return {
    question_id: q.id,
    candidate_model: CANDIDATE,
    judge_model: JUDGE,
    accuracy: 0, completeness: 0, bonus: 0, ru_linguistic: 0, overall: 0,
    reasoning: "",
    ok: false,
    error,
  };
}

async function pool<T>(items: T[], n: number, worker: (item: T) => Promise<JudgeScore>): Promise<JudgeScore[]> {
  const results: JudgeScore[] = new Array(items.length);
  let cursor = 0;
  async function loop() {
    while (true) {
      const i = cursor++;
      if (i >= items.length) return;
      results[i] = await worker(items[i]);
      if ((i + 1) % 20 === 0 || i + 1 === items.length) {
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

const fresh = await pool(todo, CONCURRENCY, callJudge);
const all = [...existing.filter(s => s.ok || !todo.find(q => q.id === s.question_id)), ...fresh];
writeFileSync(OUT, JSON.stringify(all, null, 2));

const ok = all.filter(s => s.ok).length;
const failedC = all.length - ok;
const avgOverall = ok > 0 ? all.filter(s => s.ok).reduce((s, x) => s + x.overall, 0) / ok : 0;
console.log(`\n✅ ${CANDIDATE} judged by ${JUDGE}`);
console.log(`   Scores: ${ok} ok / ${failedC} failed`);
console.log(`   Avg overall (judge alone): ${avgOverall.toFixed(2)}/10`);
console.log(`   Output: ${OUT}`);
