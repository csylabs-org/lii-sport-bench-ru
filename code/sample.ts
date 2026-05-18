import { readFileSync, writeFileSync } from "fs";
import { join } from "path";
import { createHash } from "crypto";
import type { Question } from "./types.ts";

const SEED = process.env.SEED ?? "lii-2026-05-13";
const TARGET = parseInt(process.env.TARGET ?? "200", 10);

const IN = join(import.meta.dir, "..", "data", "questions.json");
const OUT = join(import.meta.dir, "..", "data", `pilot-${TARGET}.json`);

const questions: Question[] = JSON.parse(readFileSync(IN, "utf-8"));

function hash(s: string): number {
  const buf = createHash("sha256").update(s).digest();
  return buf.readUInt32BE(0);
}

const groups = new Map<string, Question[]>();
for (const q of questions) {
  const key = `tier${q.tier}/${q.sport_file}`;
  if (!groups.has(key)) groups.set(key, []);
  groups.get(key)!.push(q);
}

const total = questions.length;
const sampled: Question[] = [];
const allocations: Record<string, { allocated: number; available: number }> = {};

const groupKeys = [...groups.keys()].sort();
const exact: Record<string, number> = {};
let runningInt = 0;
for (const k of groupKeys) {
  const g = groups.get(k)!;
  const share = (g.length / total) * TARGET;
  exact[k] = share;
  runningInt += Math.floor(share);
}
let remainder = TARGET - runningInt;
const fractional = groupKeys
  .map(k => ({ k, frac: exact[k] - Math.floor(exact[k]) }))
  .sort((a, b) => b.frac - a.frac);
const bumped = new Set<string>();
for (let i = 0; i < remainder && i < fractional.length; i++) bumped.add(fractional[i].k);

for (const k of groupKeys) {
  const g = groups.get(k)!;
  const alloc = Math.floor(exact[k]) + (bumped.has(k) ? 1 : 0);
  allocations[k] = { allocated: alloc, available: g.length };
  const sorted = [...g].sort((a, b) => hash(SEED + ":" + a.id) - hash(SEED + ":" + b.id));
  sampled.push(...sorted.slice(0, alloc));
}

sampled.sort((a, b) => a.id.localeCompare(b.id));

writeFileSync(OUT, JSON.stringify(sampled, null, 2));

console.log(`Sampling ${TARGET} questions stratified by tier/sport with seed "${SEED}":`);
for (const k of groupKeys) {
  const a = allocations[k];
  console.log(`  ${k.padEnd(28)} → ${a.allocated.toString().padStart(3)} / ${a.available}`);
}
const byDifficulty = sampled.reduce<Record<string, number>>((acc, q) => {
  acc[q.difficulty] = (acc[q.difficulty] ?? 0) + 1;
  return acc;
}, {});
const byTier = sampled.reduce<Record<string, number>>((acc, q) => {
  acc[`tier${q.tier}`] = (acc[`tier${q.tier}`] ?? 0) + 1;
  return acc;
}, {});
console.log(`\n✅ Sampled ${sampled.length} questions`);
console.log(`   By tier: ${JSON.stringify(byTier)}`);
console.log(`   By difficulty: ${JSON.stringify(byDifficulty)}`);
console.log(`   Output: ${OUT}`);
