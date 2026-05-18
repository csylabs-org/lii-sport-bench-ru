# ЛИИ-Спорт-Bench-RU v0.1 — Pilot Re-Lock Results (2026-05-16)

> **Decision:** Gemma 4 31B vs Qwen 3.6 27B base model lock for the 7 RU-heavy ЛИИ domains.
> **Pilot subset:** 200 questions stratified from 655-Q bench.
> **Judges:** top-3 ensemble (`claude-opus-4.7`, `gpt-5.5`, `gemini-3.1-pro-preview`)
> **Generated:** 2026-05-16T18:26:42.603Z

---

## Decision

**Gemma 4 31B locks as ЛИИ base.** Wins 13/15 sports AND total margin = +0.78pt. RU linguistic correctness: Gemma 8.98 vs Qwen 8.42 (Δ +0.56). Per COMPUTE-STRATEGY §4.4 decision rule. Action: 1-2 day plumbing rework (HF model class `Qwen2ForCausalLM` → `Gemma3ForCausalLM`, tokenizer swap, chat template Gemma `<start_of_turn>user`/`<start_of_turn>model`, `transformers>=4.51` + `flash-attn>=2.7` + `Unsloth>=2026.04`); EduLLM-RU migrates to Gemma 4 31B as v2 with Образование Stage 2; Y1 compute spend drops ~170K ₽.

---

## Overall scores (mean of 3 judges, 4 dimensions averaged)

| Candidate | n | Accuracy | Completeness | Bonus | RU linguistic | **Overall** |
|---|---:|---:|---:|---:|---:|---:|
| `gemma-4-31b-it` | 200 | 7.30 | 7.39 | 6.14 | 8.98 | **7.45** |
| `qwen3.6-27b` | 200 | 6.21 | 6.31 | 5.76 | 8.42 | **6.67** |
| **Δ (gemma-4-31b-it − qwen3.6-27b)** | | +1.09 | +1.08 | +0.38 | +0.56 | **+0.78** |

---

## Per-sport breakdown (tier-1 + tier-2)

gemma-4-31b-it wins: **13** · qwen3.6-27b wins: **1** · ties: 1

| Sport/Group | `gemma-4-31b-it` | `qwen3.6-27b` | Δ | Winner |
|---|---:|---:|---:|---|
| `tier1/athletics` | 7.27 | 7.77 | -0.50 | **qwen3.6-27b** |
| `tier1/basketball` | 7.63 | 6.82 | +0.81 | **gemma-4-31b-it** |
| `tier1/football` | 7.89 | 6.83 | +1.06 | **gemma-4-31b-it** |
| `tier1/gymnastics` | 8.25 | 7.14 | +1.11 | **gemma-4-31b-it** |
| `tier1/hockey` | 7.15 | 6.89 | +0.26 | **gemma-4-31b-it** |
| `tier1/swimming` | 7.86 | 6.33 | +1.53 | **gemma-4-31b-it** |
| `tier1/volleyball` | 7.05 | 6.26 | +0.79 | **gemma-4-31b-it** |
| `tier1/wrestling` | 7.28 | 5.91 | +1.38 | **gemma-4-31b-it** |
| `tier2/combat-sports` | 7.55 | 6.58 | +0.98 | **gemma-4-31b-it** |
| `tier2/precision-sports` | 7.33 | 7.29 | +0.05 | tie |
| `tier2/strength-skill` | 7.19 | 6.21 | +0.98 | **gemma-4-31b-it** |
| `tier2/winter-sports` | 5.84 | 5.64 | +0.20 | **gemma-4-31b-it** |
| `tier3/batch-a` | 7.36 | 6.23 | +1.14 | **gemma-4-31b-it** |
| `tier3/batch-b` | 8.18 | 7.86 | +0.31 | **gemma-4-31b-it** |
| `tier3/batch-c` | 8.69 | 6.62 | +2.06 | **gemma-4-31b-it** |

---

## Per-tier breakdown

| Tier | n | `gemma-4-31b-it` | `qwen3.6-27b` | Δ |
|---|---:|---:|---:|---:|
| tier1 | 120 | 7.55 | 6.74 | +0.80 |
| tier2 | 56 | 6.98 | 6.43 | +0.55 |
| tier3 | 24 | 8.08 | 6.91 | +1.17 |

---

## Per-difficulty breakdown

| Difficulty | n | `gemma-4-31b-it` | `qwen3.6-27b` | Δ |
|---|---:|---:|---:|---:|
| Basic | 57 | 7.20 | 6.73 | +0.47 |
| Applied | 107 | 7.48 | 6.71 | +0.77 |
| Expert | 36 | 7.79 | 6.49 | +1.30 |

---

## Per-audience breakdown

| Audience | n | `gemma-4-31b-it` | `qwen3.6-27b` | Δ |
|---|---:|---:|---:|---:|
| АНАЛИТИК | 4 | 7.13 | 5.69 | +1.44 |
| ВУЗ | 13 | 6.65 | 5.28 | +1.37 |
| МЕДИК | 19 | 8.44 | 7.49 | +0.95 |
| СПОРТСМЕН | 19 | 8.46 | 7.88 | +0.57 |
| СШОР | 24 | 6.37 | 5.73 | +0.64 |
| ТРЕНЕР | 63 | 7.65 | 6.92 | +0.73 |
| ФУНКЦИОНЕР | 58 | 7.23 | 6.52 | +0.71 |

---

## Judge ensemble agreement

Per-question scores >2pt range across the 3 judges = potential calibration issue. Flagged counts:

- `qwen3.6-27b`: 50 flagged questions (of 200)
- `gemma-4-31b-it`: 14 flagged questions (of 200)

Top 10 highest-disagreement questions:

| Question | Candidate | Mean | Range | Per-judge |
|---|---|---:|---:|---|
| `ТРИ-ДП-001` | `qwen3.6-27b` | 6.25 | 9.75 | claude-opus-4.7=9.75, gpt-5.5=9.00, gemini-3.1-pro-preview=0.00 |
| `ШАХ-ПР-001` | `qwen3.6-27b` | 6.92 | 4.75 | claude-opus-4.7=7.00, gpt-5.5=4.50, gemini-3.1-pro-preview=9.25 |
| `ПЛА-ФР-003` | `qwen3.6-27b` | 7.75 | 4.00 | claude-opus-4.7=8.75, gpt-5.5=5.25, gemini-3.1-pro-preview=9.25 |
| `ТЯЖ-МТ-003` | `qwen3.6-27b` | 6.42 | 4.00 | claude-opus-4.7=5.75, gpt-5.5=4.75, gemini-3.1-pro-preview=8.75 |
| `БАС-ПР-005` | `qwen3.6-27b` | 8.08 | 3.75 | claude-opus-4.7=9.00, gpt-5.5=5.75, gemini-3.1-pro-preview=9.50 |
| `ПЛА-СМ-005` | `qwen3.6-27b` | 8.25 | 3.75 | claude-opus-4.7=9.00, gpt-5.5=6.00, gemini-3.1-pro-preview=9.75 |
| `ПЛА-ФР-001` | `qwen3.6-27b` | 7.58 | 3.75 | claude-opus-4.7=7.50, gpt-5.5=5.75, gemini-3.1-pro-preview=9.50 |
| `ФЕХ-МТ-002` | `qwen3.6-27b` | 5.17 | 3.75 | claude-opus-4.7=7.00, gpt-5.5=5.25, gemini-3.1-pro-preview=3.25 |
| `ЛЁГ-ПР-007` | `qwen3.6-27b` | 7.75 | 3.50 | claude-opus-4.7=6.50, gpt-5.5=6.75, gemini-3.1-pro-preview=10.00 |
| `ФЕХ-БФ-001` | `qwen3.6-27b` | 4.83 | 3.50 | claude-opus-4.7=6.75, gpt-5.5=4.50, gemini-3.1-pro-preview=3.25 |

---

## Methodology

- **Bench:** ЛИИ-Спорт-Bench-RU v0.1 (655 questions, 35 sports, 8 categories per Tier-1 sport)
- **Pilot subset:** stratified 200-Q sample, seed `lii-2026-05-13`
- **Candidate inference:** OpenRouter, temperature=0, max_tokens=2048 (8000 for Qwen reasoning-mode retries), `provider.sort=price`, seed per-question
- **Judge ensemble:** 3 judges via OpenRouter, temperature=0, JSON mode, max_tokens=4000, `reasoning: {effort: "low"}` for Gemini Pro reasoning-mode
- **Scoring rubric:** 4 dimensions (accuracy / completeness / bonus / ru_linguistic), 0-10 each, overall = mean
- **Aggregation:** per-question mean across 3 judges → per-bucket mean across questions
- **Decision rule:** per `COMPUTE-STRATEGY-2026-05-13.md` §4.4

## Reproducibility

```bash
cd 20-ventures/llm-integrator/_bench/lii-sport-bench-ru/v0.1/eval
set -a; source ../../../.env.local; set +a
bun src/parse.ts
bun src/sample.ts
MODEL=google/gemma-4-31b-it bun src/run.ts
MODEL=qwen/qwen3.6-27b bun src/run.ts
for J in google/gemini-3.1-pro-preview openai/gpt-5.5 anthropic/claude-opus-4.7; do
  CANDIDATE=google/gemma-4-31b-it JUDGE=$J bun src/judge.ts
  CANDIDATE=qwen/qwen3.6-27b JUDGE=$J bun src/judge.ts
done
bun src/aggregate.ts
bun src/render.ts
```
