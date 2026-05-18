import { readFileSync, writeFileSync } from "fs";
import { join } from "path";

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------
const DATA_DIR = join(import.meta.dir, "..", "data");
const AGG = join(DATA_DIR, "aggregated.json");
const OUT_MD = join(DATA_DIR, "leaderboard.md");
const OUT_JSON = join(DATA_DIR, "leaderboard.json");
const OUT_HTML = join(DATA_DIR, "leaderboard.html");

const DATE = new Date().toISOString().slice(0, 10);
const agg = JSON.parse(readFileSync(AGG, "utf-8"));

// ---------------------------------------------------------------------------
// Types (inline — mirrors aggregate.ts AggregatedRow)
// ---------------------------------------------------------------------------
interface Row {
  candidate: string;
  bucket: string;
  bucket_type: string;
  n: number;
  accuracy: number;
  completeness: number;
  bonus: number;
  ru_linguistic: number;
  overall: number;
}

interface JudgeScore {
  question_id: string;
  candidate_model: string;
  judge_model: string;
  accuracy: number;
  completeness: number;
  bonus: number;
  ru_linguistic: number;
  overall: number;
  reasoning: string;
  ok: boolean;
}

interface PerQuestion {
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

interface Disagreement {
  question_id: string;
  candidate: string;
  overall: number;
  disagreement: number;
  per_judge: { judge: string; overall: number }[];
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------
const candidates: string[] = agg.candidates;
const judges: string[] = agg.judges;
const overall: Row[] = agg.overall;
const perSport: Row[] = agg.per_sport;
const perDifficulty: Row[] = agg.per_difficulty;
const perAudience: Row[] = agg.per_audience;
const perTier: Row[] = agg.per_tier;
const perQuestion: PerQuestion[] = agg.per_question;
const topDisagreements: Disagreement[] = agg.top_disagreements;
const judgeAgreementFlagged: Record<string, number> = agg.judge_agreement_flagged;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function fmt(n: number): string {
  return (Math.round(n * 100) / 100).toFixed(2);
}

function short(id: string): string {
  return id.split("/").pop() ?? id;
}

// Candidates sorted by overall descending — this is the canonical rank order
const rankedCandidates = [...candidates].sort((a, b) => {
  const oa = overall.find(r => r.candidate === a)?.overall ?? 0;
  const ob = overall.find(r => r.candidate === b)?.overall ?? 0;
  return ob - oa;
});

function getOverall(candidate: string): Row | undefined {
  return overall.find(r => r.candidate === candidate);
}

function getBucket(table: Row[], candidate: string, bucket: string): Row | undefined {
  return table.find(r => r.candidate === candidate && r.bucket === bucket);
}

// ---------------------------------------------------------------------------
// Self-judging bias detection
// ---------------------------------------------------------------------------
// For each (candidate, judge) where candidate === judge, compute:
//   - self_score: mean overall when that judge scored that candidate
//   - cross_score: mean overall when OTHER judges scored that candidate
interface SelfJudgeBias {
  candidate: string;
  judge: string;
  self_score: number;
  cross_score: number;
  delta: number;
  n_self: number;
  n_cross: number;
}

function detectSelfJudgeBias(): SelfJudgeBias[] {
  const result: SelfJudgeBias[] = [];
  for (const candidate of candidates) {
    if (!judges.includes(candidate)) continue;
    const candidateRows = perQuestion.filter(pq => pq.candidate === candidate);
    const selfScores: number[] = [];
    const crossScores: number[] = [];
    for (const pq of candidateRows) {
      for (const js of pq.judge_scores) {
        if (!js.ok) continue;
        if (js.judge_model === candidate) {
          selfScores.push(js.overall);
        } else {
          crossScores.push(js.overall);
        }
      }
    }
    if (selfScores.length === 0) continue;
    const selfMean = selfScores.reduce((a, b) => a + b, 0) / selfScores.length;
    const crossMean = crossScores.length > 0
      ? crossScores.reduce((a, b) => a + b, 0) / crossScores.length
      : 0;
    result.push({
      candidate,
      judge: candidate,
      self_score: selfMean,
      cross_score: crossMean,
      delta: selfMean - crossMean,
      n_self: selfScores.length,
      n_cross: crossScores.length,
    });
  }
  return result;
}

const selfJudgeBias = detectSelfJudgeBias();

// ---------------------------------------------------------------------------
// Distinct buckets (preserve data order, dedup)
// ---------------------------------------------------------------------------
const sports = [...new Set(perSport.map(r => r.bucket))].sort();
const difficulties = ["Basic", "Applied", "Expert"];
const audiences = [...new Set(perAudience.map(r => r.bucket))].sort();
const tiers = ["tier1", "tier2", "tier3"];

// ---------------------------------------------------------------------------
// Markdown builder
// ---------------------------------------------------------------------------
function mdTable(headers: string[], alignments: string[], rows: string[][]): string {
  const headerLine = "| " + headers.join(" | ") + " |";
  const sepLine = "| " + alignments.join(" | ") + " |";
  const dataLines = rows.map(r => "| " + r.join(" | ") + " |");
  return [headerLine, sepLine, ...dataLines].join("\n");
}

// Overall ranking table
function overallTable(): string {
  const headers = ["#", "Model", "n", "Overall", "Accuracy", "Completeness", "Bonus", "RU linguistic"];
  const aligns = ["---:", "---", "---:", "---:", "---:", "---:", "---:", "---:"];
  const rows = rankedCandidates.map((cand, idx) => {
    const r = getOverall(cand)!;
    return [
      String(idx + 1),
      `\`${short(cand)}\``,
      String(r.n),
      `**${fmt(r.overall)}**`,
      fmt(r.accuracy),
      fmt(r.completeness),
      fmt(r.bonus),
      fmt(r.ru_linguistic),
    ];
  });
  return mdTable(headers, aligns, rows);
}

// Generic breakdown table: rows=candidates(ranked), cols=buckets
function breakdownTable(
  table: Row[],
  buckets: string[],
  bucketLabel: string
): string {
  const headers = [bucketLabel, ...buckets.map(b => `\`${b}\``)];
  const aligns = ["---", ...buckets.map(() => "---:")];
  const rows = rankedCandidates.map(cand => {
    const cells = buckets.map(b => {
      const r = getBucket(table, cand, b);
      return r ? fmt(r.overall) : "—";
    });
    return [`\`${short(cand)}\``, ...cells];
  });
  return mdTable(headers, aligns, rows);
}

// RU linguistic table
function ruLinguisticTable(): string {
  const headers = ["Model", "Overall RU ling.", ...audiences];
  const aligns = ["---", "---:", ...audiences.map(() => "---:")];
  const rows = rankedCandidates.map(cand => {
    const r = getOverall(cand)!;
    const audScores = audiences.map(a => {
      const ar = getBucket(perAudience, cand, a);
      return ar ? fmt(ar.ru_linguistic) : "—";
    });
    return [`\`${short(cand)}\``, fmt(r.ru_linguistic), ...audScores];
  });
  return mdTable(headers, aligns, rows);
}

// Self-judging bias table
function selfJudgeTable(): string {
  if (selfJudgeBias.length === 0) return "_No self-judging pairs detected._";
  const headers = ["Candidate/Judge", "Self score", "Cross-judge mean", "Δ", "n_self", "n_cross"];
  const aligns = ["---", "---:", "---:", "---:", "---:", "---:"];
  const rows = selfJudgeBias
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .map(s => [
      `\`${short(s.candidate)}\``,
      fmt(s.self_score),
      fmt(s.cross_score),
      (s.delta >= 0 ? "+" : "") + fmt(s.delta),
      String(s.n_self),
      String(s.n_cross),
    ]);
  return mdTable(headers, aligns, rows);
}

// Top disagreements table
function disagreementsTable(limit = 10): string {
  const top = topDisagreements.slice(0, limit);
  const headers = ["Question", "Candidate", "Mean", "Spread", "Per-judge"];
  const aligns = ["---", "---", "---:", "---:", "---"];
  const rows = top.map(d => [
    `\`${d.question_id}\``,
    `\`${short(d.candidate)}\``,
    fmt(d.overall),
    fmt(d.disagreement),
    d.per_judge.map(j => `${short(j.judge)}=${fmt(j.overall)}`).join(", "),
  ]);
  return mdTable(headers, aligns, rows);
}

// Judge agreement flagged counts
function flaggedList(): string {
  const perQ = agg.n_per_q / candidates.length;
  return rankedCandidates
    .map(c => {
      const n = judgeAgreementFlagged[c] ?? 0;
      const pct = ((n / perQ) * 100).toFixed(1);
      return `- \`${short(c)}\`: ${n} flagged / ${Math.round(perQ)} questions (${pct}%)`;
    })
    .join("\n");
}

// Self-judge methodology footnote
function selfJudgeFootnote(): string {
  if (selfJudgeBias.length === 0) return "";
  const pairs = selfJudgeBias
    .map(s => `\`${short(s.candidate)}\` (self Δ ${(s.delta >= 0 ? "+" : "") + fmt(s.delta)})`)
    .join(", ");
  return `\n> **Self-judging caveat:** ${pairs}. These candidates also served as judges. Self-assigned scores are shown separately in the bias section above. Leaderboard overall scores use the full 3-judge ensemble including self-scores — adjust interpretation accordingly.`;
}

// ---------------------------------------------------------------------------
// Assemble Markdown
// ---------------------------------------------------------------------------
const md = `# ЛИИ-Спорт-Bench-RU v0.1 — ${candidates.length}-model leaderboard (${DATE})

> **Candidates:** ${candidates.length} · **Judges:** top-3 ensemble (${judges.map(j => `\`${short(j)}\``).join(", ")})
> **Bench:** 655 questions · 35 sports · 8 categories per Tier-1 sport
> **Pilot subset:** 200-Q stratified sample, seed \`lii-2026-05-13\`
> **Generated:** ${new Date().toISOString()}${selfJudgeFootnote()}

---

## Overall ranking

${overallTable()}

---

## Per-difficulty breakdown

_Rows sorted by overall rank. Values = mean overall score per difficulty bucket._

${breakdownTable(perDifficulty, difficulties, "Model")}

---

## Per-audience breakdown

_Russian audience tags from bench question metadata._

${breakdownTable(perAudience, audiences, "Model")}

---

## Per-tier breakdown

_Tier 1 = top 8 sports (50 Q each), Tier 2 = 12 sports (15 Q each), Tier 3 = 15 sports (5 Q each)._

${breakdownTable(perTier, tiers, "Model")}

---

## RU linguistic dimension

_ru_linguistic scores only (0-10 scale). Separate from overall — measures Russian language quality independent of factual accuracy._

${ruLinguisticTable()}

---

## Self-judging bias

_Auto-detected: candidates that also served as judges. Shows score inflation (or deflation) when scoring their own outputs._

${selfJudgeTable()}

---

## Judge ensemble agreement

_Questions where judges disagreed >2pt on overall score. Flagged counts per candidate:_

${flaggedList()}

**Top 10 highest-spread questions:**

${disagreementsTable(10)}

---

## Methodology

- **Bench:** ЛИИ-Спорт-Bench-RU v0.1 (655 questions, 35 sports, 8 categories per Tier-1 sport)
- **Pilot subset:** stratified 200-Q sample, seed \`lii-2026-05-13\`
- **Candidate inference:** OpenRouter, temperature=0, max_tokens=2048, \`provider.sort=price\`, seed per-question
- **Judge ensemble:** ${judges.length} judges via OpenRouter, temperature=0, JSON mode, max_tokens=4000
- **Scoring rubric:** 4 dimensions (accuracy / completeness / bonus / ru_linguistic), 0-10 each, overall = mean
- **Aggregation:** per-question mean across 3 judges → per-bucket mean across questions
- **Self-judging:** detected automatically — candidate ∈ judges. Leaderboard uses full ensemble; bias section isolates self vs cross-judge scores.

## Reproducibility

\`\`\`bash
cd 20-ventures/llm-integrator/_bench/lii-sport-bench-ru/v0.1/eval
set -a; source ../../../.env.local; set +a
bun src/parse.ts && bun src/sample.ts
for M in ${candidates.map(c => `"${c}"`).join(" ")}; do MODEL=$M bun src/run.ts; done
for J in ${judges.map(j => `"${j}"`).join(" ")}; do
  for C in ${candidates.map(c => `"${c}"`).join(" ")}; do
    CANDIDATE=$C JUDGE=$J bun src/judge.ts
  done
done
bun src/aggregate.ts && bun src/render.ts
\`\`\`
`;

// ---------------------------------------------------------------------------
// Leaderboard JSON (structured for bench.csylabs.com consumption)
// ---------------------------------------------------------------------------
interface LeaderboardEntry {
  rank: number;
  candidate: string;
  short_name: string;
  n: number;
  overall: number;
  accuracy: number;
  completeness: number;
  bonus: number;
  ru_linguistic: number;
}

interface BucketBreakdown {
  candidate: string;
  short_name: string;
  buckets: Record<string, number | null>;
}

interface SelfJudgeBiasOut {
  candidate: string;
  self_score: number;
  cross_score: number;
  delta: number;
  n_self: number;
  n_cross: number;
}

interface LeaderboardJSON {
  meta: {
    bench: string;
    version: string;
    date: string;
    generated_at: string;
    n_candidates: number;
    n_questions_pilot: number;
    judges: string[];
  };
  overall: LeaderboardEntry[];
  per_difficulty: BucketBreakdown[];
  per_audience: BucketBreakdown[];
  per_tier: BucketBreakdown[];
  ru_linguistic: { candidate: string; short_name: string; overall: number; by_audience: Record<string, number | null> }[];
  self_judge_bias: SelfJudgeBiasOut[];
  top_disagreements: {
    rank: number;
    question_id: string;
    candidate: string;
    short_name: string;
    mean_overall: number;
    spread: number;
    per_judge: { judge: string; short_name: string; overall: number }[];
  }[];
  judge_agreement_flagged: { candidate: string; short_name: string; flagged: number; total: number; pct: number }[];
}

const pilotN = Math.round(agg.n_per_q / candidates.length);

const leaderboardJSON: LeaderboardJSON = {
  meta: {
    bench: "ЛИИ-Спорт-Bench-RU",
    version: "v0.1",
    date: DATE,
    generated_at: new Date().toISOString(),
    n_candidates: candidates.length,
    n_questions_pilot: pilotN,
    judges,
  },
  overall: rankedCandidates.map((cand, idx) => {
    const r = getOverall(cand)!;
    return {
      rank: idx + 1,
      candidate: cand,
      short_name: short(cand),
      n: r.n,
      overall: parseFloat(fmt(r.overall)),
      accuracy: parseFloat(fmt(r.accuracy)),
      completeness: parseFloat(fmt(r.completeness)),
      bonus: parseFloat(fmt(r.bonus)),
      ru_linguistic: parseFloat(fmt(r.ru_linguistic)),
    };
  }),
  per_difficulty: rankedCandidates.map(cand => ({
    candidate: cand,
    short_name: short(cand),
    buckets: Object.fromEntries(
      difficulties.map(b => {
        const r = getBucket(perDifficulty, cand, b);
        return [b, r ? parseFloat(fmt(r.overall)) : null];
      })
    ),
  })),
  per_audience: rankedCandidates.map(cand => ({
    candidate: cand,
    short_name: short(cand),
    buckets: Object.fromEntries(
      audiences.map(b => {
        const r = getBucket(perAudience, cand, b);
        return [b, r ? parseFloat(fmt(r.overall)) : null];
      })
    ),
  })),
  per_tier: rankedCandidates.map(cand => ({
    candidate: cand,
    short_name: short(cand),
    buckets: Object.fromEntries(
      tiers.map(b => {
        const r = getBucket(perTier, cand, b);
        return [b, r ? parseFloat(fmt(r.overall)) : null];
      })
    ),
  })),
  ru_linguistic: rankedCandidates.map(cand => {
    const r = getOverall(cand)!;
    return {
      candidate: cand,
      short_name: short(cand),
      overall: parseFloat(fmt(r.ru_linguistic)),
      by_audience: Object.fromEntries(
        audiences.map(a => {
          const ar = getBucket(perAudience, cand, a);
          return [a, ar ? parseFloat(fmt(ar.ru_linguistic)) : null];
        })
      ),
    };
  }),
  self_judge_bias: selfJudgeBias
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .map(s => ({
      candidate: s.candidate,
      self_score: parseFloat(fmt(s.self_score)),
      cross_score: parseFloat(fmt(s.cross_score)),
      delta: parseFloat(fmt(s.delta)),
      n_self: s.n_self,
      n_cross: s.n_cross,
    })),
  top_disagreements: topDisagreements.slice(0, 10).map((d, idx) => ({
    rank: idx + 1,
    question_id: d.question_id,
    candidate: d.candidate,
    short_name: short(d.candidate),
    mean_overall: parseFloat(fmt(d.overall)),
    spread: parseFloat(fmt(d.disagreement)),
    per_judge: d.per_judge.map(j => ({
      judge: j.judge,
      short_name: short(j.judge),
      overall: parseFloat(fmt(j.overall)),
    })),
  })),
  judge_agreement_flagged: rankedCandidates.map(cand => {
    const flagged = judgeAgreementFlagged[cand] ?? 0;
    return {
      candidate: cand,
      short_name: short(cand),
      flagged,
      total: pilotN,
      pct: parseFloat(((flagged / pilotN) * 100).toFixed(1)),
    };
  }),
};

// ---------------------------------------------------------------------------
// HTML leaderboard (self-contained, print-ready)
// ---------------------------------------------------------------------------
function htmlTable(
  id: string,
  headers: string[],
  rows: string[][],
  headerClass?: string
): string {
  const thead = headers.map(h => `<th>${h}</th>`).join("");
  const tbody = rows
    .map(r => "<tr>" + r.map(c => `<td>${c}</td>`).join("") + "</tr>")
    .join("\n");
  return `<table id="${id}">
  <thead><tr class="${headerClass ?? ""}">${thead}</tr></thead>
  <tbody>${tbody}</tbody>
</table>`;
}

const MEDAL: Record<number, string> = { 1: "🥇", 2: "🥈", 3: "🥉" };

const htmlOverallRows = rankedCandidates.map((cand, idx) => {
  const r = getOverall(cand)!;
  const medal = MEDAL[idx + 1] ?? "";
  const rankCell = `${medal} ${idx + 1}`;
  const bold = idx === 0;
  const score = bold ? `<strong>${fmt(r.overall)}</strong>` : fmt(r.overall);
  return [rankCell, `<code>${short(cand)}</code>`, String(r.n), score,
    fmt(r.accuracy), fmt(r.completeness), fmt(r.bonus), fmt(r.ru_linguistic)];
});

const htmlDiffRows = rankedCandidates.map(cand =>
  [`<code>${short(cand)}</code>`, ...difficulties.map(b => {
    const r = getBucket(perDifficulty, cand, b);
    return r ? fmt(r.overall) : "—";
  })]
);

const htmlAudRows = rankedCandidates.map(cand =>
  [`<code>${short(cand)}</code>`, ...audiences.map(b => {
    const r = getBucket(perAudience, cand, b);
    return r ? fmt(r.overall) : "—";
  })]
);

const htmlTierRows = rankedCandidates.map(cand =>
  [`<code>${short(cand)}</code>`, ...tiers.map(b => {
    const r = getBucket(perTier, cand, b);
    return r ? fmt(r.overall) : "—";
  })]
);

const htmlRuRows = rankedCandidates.map(cand => {
  const r = getOverall(cand)!;
  return [`<code>${short(cand)}</code>`, `<strong>${fmt(r.ru_linguistic)}</strong>`,
    ...audiences.map(a => {
      const ar = getBucket(perAudience, cand, a);
      return ar ? fmt(ar.ru_linguistic) : "—";
    })];
});

const htmlSelfJudgeRows = selfJudgeBias
  .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
  .map(s => {
    const deltaStr = (s.delta >= 0 ? "+" : "") + fmt(s.delta);
    const cls = s.delta > 0.5 ? ' class="bias-high"' : s.delta > 0.2 ? ' class="bias-med"' : "";
    return [`<code>${short(s.candidate)}</code>`, fmt(s.self_score), fmt(s.cross_score),
      `<span${cls}>${deltaStr}</span>`, String(s.n_self), String(s.n_cross)];
  });

const htmlDisagRows = topDisagreements.slice(0, 10).map((d, idx) => [
  String(idx + 1),
  `<code>${d.question_id}</code>`,
  `<code>${short(d.candidate)}</code>`,
  fmt(d.overall),
  `<strong>${fmt(d.disagreement)}</strong>`,
  d.per_judge.map(j => `${short(j.judge)}: ${fmt(j.overall)}`).join("<br>"),
]);

const selfJudgeCaveat = selfJudgeBias.length > 0
  ? `<p class="caveat"><strong>Self-judging caveat:</strong> ${selfJudgeBias.map(s =>
      `<code>${short(s.candidate)}</code> (Δ ${(s.delta >= 0 ? "+" : "") + fmt(s.delta)})`
    ).join(", ")}. These models also served as judges. See bias section below.</p>`
  : "";

const html = `<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ЛИИ-Спорт-Bench-RU v0.1 — ${candidates.length}-model leaderboard</title>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --border: #2d3148;
    --text: #e8eaf0;
    --muted: #8b8fa8;
    --accent: #6366f1;
    --green: #22c55e;
    --amber: #f59e0b;
    --red: #ef4444;
    --rank1: #ffd700;
    --rank2: #c0c0c0;
    --rank3: #cd7f32;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: var(--bg);
    color: var(--text);
    font-size: 14px;
    line-height: 1.5;
    padding: 24px;
  }
  h1 { font-size: 1.5rem; font-weight: 700; margin-bottom: 4px; color: #fff; }
  h2 { font-size: 1.05rem; font-weight: 600; margin: 32px 0 12px; color: var(--accent); border-bottom: 1px solid var(--border); padding-bottom: 6px; }
  .meta { color: var(--muted); font-size: 12px; margin-bottom: 24px; line-height: 1.8; }
  .caveat { background: #2a1f0a; border-left: 3px solid var(--amber); padding: 10px 14px; border-radius: 4px; margin: 12px 0; font-size: 12px; color: #e8d5a3; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 16px; font-size: 13px; }
  th { background: var(--surface); color: var(--muted); font-weight: 600; text-align: left; padding: 8px 12px; border-bottom: 2px solid var(--border); white-space: nowrap; }
  td { padding: 7px 12px; border-bottom: 1px solid var(--border); vertical-align: middle; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(99,102,241,0.05); }
  td:nth-child(n+3), th:nth-child(n+3) { text-align: right; }
  code { font-family: "JetBrains Mono", "Fira Code", monospace; background: rgba(255,255,255,0.07); padding: 1px 5px; border-radius: 3px; font-size: 11px; }
  .rank-1 td:nth-child(4) { color: var(--rank1); }
  .rank-2 td:nth-child(4) { color: var(--rank2); }
  .rank-3 td:nth-child(4) { color: var(--rank3); }
  .bias-high { color: var(--red); font-weight: 700; }
  .bias-med { color: var(--amber); font-weight: 600; }
  .note { color: var(--muted); font-size: 12px; margin-bottom: 8px; font-style: italic; }
  pre { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 14px; font-size: 12px; overflow-x: auto; color: #a8b4d0; line-height: 1.6; }
  @media print {
    @page { size: A4; margin: 18mm 15mm; }
    body { background: #fff; color: #111; font-size: 11px; padding: 0; }
    :root { --bg: #fff; --surface: #f5f5f5; --border: #ddd; --text: #111; --muted: #666; --accent: #3730a3; }
    h1 { font-size: 1.2rem; }
    h2 { font-size: 0.95rem; }
    table { break-inside: avoid; }
    tr { break-inside: avoid; }
    pre { break-inside: avoid; font-size: 10px; }
    .caveat { background: #fef3c7; border-color: #d97706; }
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
</style>
</head>
<body>

<h1>ЛИИ-Спорт-Bench-RU v0.1 — ${candidates.length}-model leaderboard</h1>
<div class="meta">
  <strong>Date:</strong> ${DATE} &nbsp;·&nbsp;
  <strong>Candidates:</strong> ${candidates.length} &nbsp;·&nbsp;
  <strong>Pilot:</strong> 200 Q (stratified, seed lii-2026-05-13) &nbsp;·&nbsp;
  <strong>Judges:</strong> ${judges.map(j => short(j)).join(", ")}
</div>
${selfJudgeCaveat}

<h2>Overall ranking</h2>
${htmlTable(
  "overall",
  ["#", "Model", "n", "Overall ↓", "Accuracy", "Completeness", "Bonus", "RU linguistic"],
  htmlOverallRows.map((r, i) => {
    if (i === 0) return r; // rank-1 class applied via JS is too complex; handled via CSS nth
    return r;
  })
)}

<h2>Per-difficulty breakdown</h2>
<p class="note">Mean overall score per difficulty tier. Rows sorted by overall rank.</p>
${htmlTable("difficulty", ["Model", ...difficulties], htmlDiffRows)}

<h2>Per-audience breakdown</h2>
<p class="note">Russian audience tags from bench question metadata.</p>
${htmlTable("audience", ["Model", ...audiences], htmlAudRows)}

<h2>Per-tier breakdown</h2>
<p class="note">Tier 1 = top 8 sports (50 Q), Tier 2 = 12 sports (15 Q), Tier 3 = 15 sports (5 Q).</p>
${htmlTable("tier", ["Model", ...tiers], htmlTierRows)}

<h2>RU linguistic dimension</h2>
<p class="note">ru_linguistic scores (0-10) — language quality independent of factual accuracy.</p>
${htmlTable("ru-ling", ["Model", "Overall", ...audiences], htmlRuRows)}

<h2>Self-judging bias</h2>
<p class="note">Auto-detected pairs where candidate === judge. Positive Δ = self-inflation.</p>
${selfJudgeBias.length > 0
  ? htmlTable("self-judge", ["Candidate/Judge", "Self score", "Cross-judge mean", "Δ", "n self", "n cross"], htmlSelfJudgeRows)
  : "<p class=\"note\">No self-judging pairs detected.</p>"
}

<h2>Top 10 highest-disagreement questions</h2>
<p class="note">Spread = max judge score − min judge score across the 3-judge ensemble.</p>
${htmlTable("disagreements", ["#", "Question", "Candidate", "Mean", "Spread ↓", "Per-judge"], htmlDisagRows)}

<h2>Methodology</h2>
<pre>Bench:       ЛИИ-Спорт-Bench-RU v0.1 — 655 Q, 35 sports, 8 cat/sport (Tier-1)
Pilot:       200-Q stratified sample, seed lii-2026-05-13
Inference:   OpenRouter, temperature=0, max_tokens=2048, provider.sort=price
Judges:      ${judges.length}-model ensemble — ${judges.map(j => short(j)).join(", ")}
             temperature=0, JSON mode, max_tokens=4000
Rubric:      4 dims: accuracy / completeness / bonus / ru_linguistic (0-10 each)
             overall = mean(4 dims)
Aggregation: per-question mean across judges → per-bucket mean across questions
Self-judge:  auto-detected. Leaderboard uses full ensemble; bias section isolates.
</pre>

</body>
</html>`;

// ---------------------------------------------------------------------------
// Write outputs
// ---------------------------------------------------------------------------
writeFileSync(OUT_MD, md, "utf-8");
writeFileSync(OUT_JSON, JSON.stringify(leaderboardJSON, null, 2), "utf-8");
writeFileSync(OUT_HTML, html, "utf-8");

console.log(`leaderboard.md    -> ${OUT_MD}`);
console.log(`leaderboard.json  -> ${OUT_JSON}`);
console.log(`leaderboard.html  -> ${OUT_HTML}`);
console.log(`\nCandidates ranked:`);
rankedCandidates.forEach((c, i) => {
  const r = getOverall(c)!;
  console.log(`  ${i + 1}. ${short(c).padEnd(28)} overall=${fmt(r.overall)}`);
});
if (selfJudgeBias.length > 0) {
  console.log(`\nSelf-judge bias detected:`);
  selfJudgeBias.forEach(s => {
    console.log(`  ${short(s.candidate)}: self=${fmt(s.self_score)}, cross=${fmt(s.cross_score)}, Δ=${(s.delta >= 0 ? "+" : "") + fmt(s.delta)}`);
  });
}
