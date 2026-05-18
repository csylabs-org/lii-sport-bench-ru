import { readFileSync, writeFileSync, readdirSync } from "fs";
import { join } from "path";
import type { Question, JudgeScore } from "./types.ts";

const INPUT_FILE = process.env.INPUT ?? "pilot-200.json";
const IN = join(import.meta.dir, "..", "data", INPUT_FILE);
const SCORES_DIR = join(import.meta.dir, "..", "data", "scores");
const OUT = join(import.meta.dir, "..", "data", "aggregated.json");

const questions: Question[] = JSON.parse(readFileSync(IN, "utf-8"));
const qById = new Map(questions.map(q => [q.id, q]));

const scoreFiles = readdirSync(SCORES_DIR).filter(f => f.endsWith(".json"));
console.log(`Loading ${scoreFiles.length} score files...`);
const allScores: JudgeScore[] = [];
for (const f of scoreFiles) {
  const arr: JudgeScore[] = JSON.parse(readFileSync(join(SCORES_DIR, f), "utf-8"));
  console.log(`  ${f}: ${arr.length} scores (${arr.filter(s => s.ok).length} ok)`);
  allScores.push(...arr);
}

const candidates = [...new Set(allScores.map(s => s.candidate_model))];
const judges = [...new Set(allScores.map(s => s.judge_model))];
console.log(`\nCandidates: ${candidates.join(", ")}`);
console.log(`Judges: ${judges.join(", ")}`);

interface QStats {
  question_id: string;
  candidate: string;
  judge_scores: JudgeScore[];
  accuracy: number;
  completeness: number;
  bonus: number;
  ru_linguistic: number;
  overall: number;
  judge_disagreement: number;
}

const perQ: QStats[] = [];
for (const cand of candidates) {
  for (const q of questions) {
    const scores = allScores.filter(s => s.candidate_model === cand && s.question_id === q.id && s.ok);
    if (scores.length === 0) continue;
    const mean = (k: keyof JudgeScore) => scores.reduce((s, x) => s + (x[k] as number), 0) / scores.length;
    const overalls = scores.map(s => s.overall);
    const maxO = Math.max(...overalls);
    const minO = Math.min(...overalls);
    perQ.push({
      question_id: q.id,
      candidate: cand,
      judge_scores: scores,
      accuracy: mean("accuracy"),
      completeness: mean("completeness"),
      bonus: mean("bonus"),
      ru_linguistic: mean("ru_linguistic"),
      overall: mean("overall"),
      judge_disagreement: maxO - minO,
    });
  }
}

function aggregate(rows: QStats[], bucket_type: string, bucketFn: (qid: string) => string) {
  const groups = new Map<string, QStats[]>();
  for (const r of rows) {
    const key = `${r.candidate}::${bucketFn(r.question_id)}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(r);
  }
  return [...groups.entries()].map(([key, arr]) => {
    const [candidate, bucket] = key.split("::");
    return {
      candidate,
      bucket,
      bucket_type,
      n: arr.length,
      accuracy: arr.reduce((s, r) => s + r.accuracy, 0) / arr.length,
      completeness: arr.reduce((s, r) => s + r.completeness, 0) / arr.length,
      bonus: arr.reduce((s, r) => s + r.bonus, 0) / arr.length,
      ru_linguistic: arr.reduce((s, r) => s + r.ru_linguistic, 0) / arr.length,
      overall: arr.reduce((s, r) => s + r.overall, 0) / arr.length,
    };
  });
}

const overallRows = aggregate(perQ, "overall", () => "all");
const sportRows = aggregate(perQ, "sport", qid => {
  const q = qById.get(qid)!;
  return `tier${q.tier}/${q.sport_file}`;
});
const difficultyRows = aggregate(perQ, "difficulty", qid => qById.get(qid)!.difficulty);
const audienceRows = aggregate(perQ, "audience", qid => qById.get(qid)!.audience);
const tierRows = aggregate(perQ, "tier", qid => `tier${qById.get(qid)!.tier}`);

const judgeAgreement: Record<string, number> = {};
for (const cand of candidates) {
  const rows = perQ.filter(p => p.candidate === cand);
  if (rows.length === 0) continue;
  const flagged = rows.filter(r => r.judge_disagreement > 2).length;
  judgeAgreement[cand] = flagged;
}

const flaggedQs = perQ
  .filter(r => r.judge_disagreement > 2)
  .sort((a, b) => b.judge_disagreement - a.judge_disagreement)
  .slice(0, 20)
  .map(r => ({
    question_id: r.question_id,
    candidate: r.candidate,
    overall: r.overall,
    disagreement: r.judge_disagreement,
    per_judge: r.judge_scores.map(s => ({ judge: s.judge_model, overall: s.overall })),
  }));

writeFileSync(OUT, JSON.stringify({
  candidates,
  judges,
  n_per_q: perQ.length,
  overall: overallRows,
  per_sport: sportRows,
  per_difficulty: difficultyRows,
  per_audience: audienceRows,
  per_tier: tierRows,
  judge_agreement_flagged: judgeAgreement,
  top_disagreements: flaggedQs,
  per_question: perQ,
}, null, 2));

console.log(`\n✅ Aggregated`);
console.log(`   Per-question stats: ${perQ.length} rows`);
console.log(`   Overall: ${overallRows.length} rows`);
console.log(`   Per-sport: ${sportRows.length} rows`);
console.log(`   Judge disagreement (>2pt) flagged: ${JSON.stringify(judgeAgreement)}`);
console.log(`   Output: ${OUT}`);
