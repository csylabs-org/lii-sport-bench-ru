import { readdirSync, readFileSync, writeFileSync, mkdirSync } from "fs";
import { join, basename } from "path";
import type { Question, Tier, Difficulty } from "./types.ts";

const BENCH_ROOT = join(import.meta.dir, "..", "data");
const OUT = join(import.meta.dir, "..", "data", "questions.json");

const SPORT_NAMES: Record<string, string> = {
  "БАС": "basketball",
  "ВОЛ": "volleyball",
  "ФУТ": "football",
  "ХОК": "hockey",
  "ПЛВ": "swimming",
  "ЛЕГ": "athletics",
  "БОР": "wrestling",
  "ГИМ": "gymnastics",
};

const QUESTION_BLOCK_RE = /\*\*([А-ЯЁA-Z]+)-([А-ЯЁA-Z]+)-(\d+)\*\*\s*((?:`\[[^\]]+\]`\s*)+)\n((?:>.*(?:\n|$))+)/gm;

function classifyTier(filePath: string): Tier {
  if (filePath.includes("/tier1/")) return 1;
  if (filePath.includes("/tier2/")) return 2;
  if (filePath.includes("/tier3/")) return 3;
  throw new Error("Cannot classify tier: " + filePath);
}

function parseTags(tagBlock: string): { audience: string; difficulty: Difficulty; is_mcq: boolean } {
  const tags = [...tagBlock.matchAll(/`\[([^\]]+)\]`/g)].map(m => m[1].trim());
  const difficulties: Difficulty[] = ["Basic", "Applied", "Expert"];
  const difficulty = tags.find((t): t is Difficulty => difficulties.includes(t as Difficulty)) ?? "Applied";
  const is_mcq = tags.some(t => t.toUpperCase() === "MCQ");
  const audience = tags.find(t => !difficulties.includes(t as Difficulty) && t.toUpperCase() !== "MCQ") ?? "ОБЩИЙ";
  return { audience, difficulty, is_mcq };
}

function parseBody(body: string): { question: string; reference_answer: string; rubric: string } {
  const stripped = body
    .split("\n")
    .map(l => l.replace(/^>\s?/, ""))
    .join("\n")
    .trim();

  const qMatch = stripped.match(/Вопрос[^:]*:\s*([\s\S]*?)(?=\n\s*Эталонный ответ[^:]*:|\n\s*Критерии оценки[^:]*:|$)/);
  const aMatch = stripped.match(/Эталонный ответ[^:]*:\s*([\s\S]*?)(?=\n\s*Критерии оценки[^:]*:|$)/);
  const rMatch = stripped.match(/Критерии оценки[^:]*:\s*([\s\S]*?)$/);

  return {
    question: (qMatch?.[1] ?? "").trim(),
    reference_answer: (aMatch?.[1] ?? "").trim(),
    rubric: (rMatch?.[1] ?? "").trim(),
  };
}

function parseFile(filePath: string): Question[] {
  const content = readFileSync(filePath, "utf-8");
  const tier = classifyTier(filePath);
  const sport_file = basename(filePath, ".md");

  const questions: Question[] = [];
  let match;
  QUESTION_BLOCK_RE.lastIndex = 0;
  while ((match = QUESTION_BLOCK_RE.exec(content)) !== null) {
    const [, sport_prefix, category_prefix, number_str, tagBlock, body] = match;
    const { audience, difficulty, is_mcq } = parseTags(tagBlock);
    const { question, reference_answer, rubric } = parseBody(body);

    if (!question || !reference_answer) {
      console.warn(`  ⚠️  Skipping ${sport_prefix}-${category_prefix}-${number_str}: missing question or reference`);
      continue;
    }

    questions.push({
      id: `${sport_prefix}-${category_prefix}-${number_str.padStart(3, "0")}`,
      sport_prefix,
      category_prefix,
      number: parseInt(number_str, 10),
      audience,
      difficulty,
      is_mcq,
      question,
      reference_answer,
      rubric,
      tier,
      sport_file,
    });
  }
  return questions;
}

function walkBench(): string[] {
  const files: string[] = [];
  for (const tier of ["tier1", "tier2", "tier3"]) {
    const dir = join(BENCH_ROOT, tier);
    for (const f of readdirSync(dir)) {
      if (f.endsWith(".md")) files.push(join(dir, f));
    }
  }
  return files;
}

const files = walkBench();
console.log(`Parsing ${files.length} bench files...`);
const all: Question[] = [];
for (const f of files) {
  const qs = parseFile(f);
  console.log(`  ${basename(f).padEnd(28)} → ${qs.length} questions`);
  all.push(...qs);
}

mkdirSync(join(import.meta.dir, "..", "data"), { recursive: true });
writeFileSync(OUT, JSON.stringify(all, null, 2));

const byTier = all.reduce<Record<string, number>>((acc, q) => {
  acc[`tier${q.tier}`] = (acc[`tier${q.tier}`] ?? 0) + 1;
  return acc;
}, {});
console.log(`\n✅ Parsed ${all.length} total questions`);
console.log(`   By tier: ${JSON.stringify(byTier)}`);
console.log(`   Output: ${OUT}`);
