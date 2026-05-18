# ЛИИ-Спорт-Bench-RU v0.1 — 7-model leaderboard (2026-05-18)

> **Candidates:** 7 · **Judges:** top-3 ensemble (`gemini-3.1-pro-preview`, `claude-opus-4.7`, `gpt-5.5`)
> **Bench:** 655 questions · 35 sports · 8 categories per Tier-1 sport
> **Pilot subset:** 200-Q stratified sample, seed `lii-2026-05-13`
> **Generated:** 2026-05-18T12:33:42.437Z
> **Self-judging caveat:** `gpt-5.5` (self Δ -0.26), `gemini-3.1-pro-preview` (self Δ +0.77), `claude-opus-4.7` (self Δ +0.15). These candidates also served as judges. Self-assigned scores are shown separately in the bias section above. Leaderboard overall scores use the full 3-judge ensemble including self-scores — adjust interpretation accordingly.

---

## Overall ranking

| # | Model | n | Overall | Accuracy | Completeness | Bonus | RU linguistic |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `claude-opus-4.7` | 200 | **9.10** | 8.67 | 9.16 | 8.92 | 9.65 |
| 2 | `gemini-3.1-pro-preview` | 200 | **8.88** | 8.58 | 8.72 | 8.49 | 9.74 |
| 3 | `gpt-5.5` | 200 | **8.53** | 8.54 | 8.35 | 7.55 | 9.68 |
| 4 | `deepseek-v4-flash` | 193 | **8.03** | 7.75 | 8.06 | 7.28 | 9.05 |
| 5 | `qwen3.5-27b` | 199 | **7.52** | 7.07 | 7.46 | 6.53 | 9.03 |
| 6 | `gemma-4-31b-it` | 200 | **7.45** | 7.30 | 7.39 | 6.14 | 8.98 |
| 7 | `qwen3.6-27b` | 200 | **6.67** | 6.21 | 6.31 | 5.76 | 8.42 |

---

## Per-difficulty breakdown

_Rows sorted by overall rank. Values = mean overall score per difficulty bucket._

| Model | `Basic` | `Applied` | `Expert` |
| --- | ---: | ---: | ---: |
| `claude-opus-4.7` | 8.91 | 9.18 | 9.17 |
| `gemini-3.1-pro-preview` | 8.56 | 8.98 | 9.10 |
| `gpt-5.5` | 8.42 | 8.50 | 8.78 |
| `deepseek-v4-flash` | 7.93 | 8.06 | 8.11 |
| `qwen3.5-27b` | 7.18 | 7.53 | 8.04 |
| `gemma-4-31b-it` | 7.20 | 7.48 | 7.79 |
| `qwen3.6-27b` | 6.73 | 6.71 | 6.49 |

---

## Per-audience breakdown

_Russian audience tags from bench question metadata._

| Model | `АНАЛИТИК` | `ВУЗ` | `МЕДИК` | `СПОРТСМЕН` | `СШОР` | `ТРЕНЕР` | `ФУНКЦИОНЕР` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `claude-opus-4.7` | 9.13 | 9.59 | 9.61 | 9.59 | 8.24 | 9.24 | 8.87 |
| `gemini-3.1-pro-preview` | 8.88 | 9.23 | 9.41 | 9.27 | 8.17 | 9.01 | 8.66 |
| `gpt-5.5` | 9.12 | 9.20 | 8.84 | 9.23 | 7.68 | 8.52 | 8.37 |
| `deepseek-v4-flash` | 6.50 | 8.23 | 8.82 | 8.46 | 7.48 | 8.09 | 7.85 |
| `qwen3.5-27b` | 6.73 | 7.13 | 8.95 | 8.67 | 6.47 | 7.72 | 7.05 |
| `gemma-4-31b-it` | 7.13 | 6.65 | 8.44 | 8.46 | 6.37 | 7.65 | 7.23 |
| `qwen3.6-27b` | 5.69 | 5.28 | 7.49 | 7.88 | 5.73 | 6.92 | 6.52 |

---

## Per-tier breakdown

_Tier 1 = top 8 sports (50 Q each), Tier 2 = 12 sports (15 Q each), Tier 3 = 15 sports (5 Q each)._

| Model | `tier1` | `tier2` | `tier3` |
| --- | ---: | ---: | ---: |
| `claude-opus-4.7` | 9.14 | 8.98 | 9.22 |
| `gemini-3.1-pro-preview` | 8.94 | 8.70 | 9.00 |
| `gpt-5.5` | 8.62 | 8.26 | 8.69 |
| `deepseek-v4-flash` | 8.06 | 7.95 | 8.10 |
| `qwen3.5-27b` | 7.68 | 7.08 | 7.80 |
| `gemma-4-31b-it` | 7.55 | 6.98 | 8.08 |
| `qwen3.6-27b` | 6.74 | 6.43 | 6.91 |

---

## RU linguistic dimension

_ru_linguistic scores only (0-10 scale). Separate from overall — measures Russian language quality independent of factual accuracy._

| Model | Overall RU ling. | АНАЛИТИК | ВУЗ | МЕДИК | СПОРТСМЕН | СШОР | ТРЕНЕР | ФУНКЦИОНЕР |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `claude-opus-4.7` | 9.65 | 9.25 | 9.90 | 9.74 | 9.70 | 9.64 | 9.57 | 9.68 |
| `gemini-3.1-pro-preview` | 9.74 | 9.58 | 9.82 | 9.86 | 9.77 | 9.65 | 9.72 | 9.74 |
| `gpt-5.5` | 9.68 | 9.50 | 9.90 | 9.67 | 9.81 | 9.62 | 9.62 | 9.70 |
| `deepseek-v4-flash` | 9.05 | 8.17 | 8.97 | 9.33 | 8.88 | 9.07 | 8.98 | 9.17 |
| `qwen3.5-27b` | 9.03 | 8.83 | 9.05 | 9.37 | 9.28 | 8.67 | 9.07 | 8.95 |
| `gemma-4-31b-it` | 8.98 | 8.50 | 8.05 | 9.25 | 9.11 | 9.03 | 9.05 | 9.01 |
| `qwen3.6-27b` | 8.42 | 7.92 | 7.27 | 8.32 | 8.60 | 8.64 | 8.41 | 8.63 |

---

## Self-judging bias

_Auto-detected: candidates that also served as judges. Shows score inflation (or deflation) when scoring their own outputs._

| Candidate/Judge | Self score | Cross-judge mean | Δ | n_self | n_cross |
| --- | ---: | ---: | ---: | ---: | ---: |
| `gemini-3.1-pro-preview` | 9.40 | 8.63 | +0.77 | 200 | 400 |
| `gpt-5.5` | 8.36 | 8.62 | -0.26 | 200 | 400 |
| `claude-opus-4.7` | 9.20 | 9.05 | +0.15 | 200 | 400 |

---

## Judge ensemble agreement

_Questions where judges disagreed >2pt on overall score. Flagged counts per candidate:_

- `claude-opus-4.7`: 26 flagged / 199 questions (13.1%)
- `gemini-3.1-pro-preview`: 26 flagged / 199 questions (13.1%)
- `gpt-5.5`: 8 flagged / 199 questions (4.0%)
- `deepseek-v4-flash`: 40 flagged / 199 questions (20.1%)
- `qwen3.5-27b`: 29 flagged / 199 questions (14.6%)
- `gemma-4-31b-it`: 14 flagged / 199 questions (7.0%)
- `qwen3.6-27b`: 50 flagged / 199 questions (25.1%)

**Top 10 highest-spread questions:**

| Question | Candidate | Mean | Spread | Per-judge |
| --- | --- | ---: | ---: | --- |
| `ТРИ-ДП-001` | `qwen3.6-27b` | 6.25 | 9.75 | claude-opus-4.7=9.75, gpt-5.5=9.00, gemini-3.1-pro-preview=0.00 |
| `ЛЫЖ-ПР-002` | `gpt-5.5` | 6.00 | 9.50 | gemini-3.1-pro-preview=0.00, claude-opus-4.7=9.50, gpt-5.5=8.50 |
| `БАС-СП-002` | `deepseek-v4-flash` | 6.08 | 9.50 | gemini-3.1-pro-preview=0.00, gpt-5.5=8.75, claude-opus-4.7=9.50 |
| `ПЛА-ПР-003` | `gpt-5.5` | 7.75 | 5.75 | gemini-3.1-pro-preview=10.00, claude-opus-4.7=4.25, gpt-5.5=9.00 |
| `ЛЁГ-ФР-006` | `claude-opus-4.7` | 6.67 | 5.50 | gemini-3.1-pro-preview=10.00, claude-opus-4.7=4.50, gpt-5.5=5.50 |
| `ЛЁГ-ПР-007` | `deepseek-v4-flash` | 6.83 | 5.00 | gemini-3.1-pro-preview=10.00, gpt-5.5=5.50, claude-opus-4.7=5.00 |
| `ШАХ-ПР-001` | `qwen3.6-27b` | 6.92 | 4.75 | claude-opus-4.7=7.00, gpt-5.5=4.50, gemini-3.1-pro-preview=9.25 |
| `ХОК-ПР-001` | `gemini-3.1-pro-preview` | 7.50 | 4.50 | gpt-5.5=5.25, gemini-3.1-pro-preview=9.75, claude-opus-4.7=7.50 |
| `ДЗЮ-ПР-003` | `claude-opus-4.7` | 6.75 | 4.50 | gemini-3.1-pro-preview=9.50, claude-opus-4.7=5.00, gpt-5.5=5.75 |
| `ЛЁГ-МТ-009` | `gpt-5.5` | 6.00 | 4.00 | gemini-3.1-pro-preview=8.50, claude-opus-4.7=5.00, gpt-5.5=4.50 |

---

## Methodology

- **Bench:** ЛИИ-Спорт-Bench-RU v0.1 (655 questions, 35 sports, 8 categories per Tier-1 sport)
- **Pilot subset:** stratified 200-Q sample, seed `lii-2026-05-13`
- **Candidate inference:** OpenRouter, temperature=0, max_tokens=2048, `provider.sort=price`, seed per-question
- **Judge ensemble:** 3 judges via OpenRouter, temperature=0, JSON mode, max_tokens=4000
- **Scoring rubric:** 4 dimensions (accuracy / completeness / bonus / ru_linguistic), 0-10 each, overall = mean
- **Aggregation:** per-question mean across 3 judges → per-bucket mean across questions
- **Self-judging:** detected automatically — candidate ∈ judges. Leaderboard uses full ensemble; bias section isolates self vs cross-judge scores.

## Reproducibility

```bash
cd 20-ventures/llm-integrator/_bench/lii-sport-bench-ru/v0.1/eval
set -a; source ../../../.env.local; set +a
bun src/parse.ts && bun src/sample.ts
for M in "openai/gpt-5.5" "qwen/qwen3.6-27b" "google/gemini-3.1-pro-preview" "deepseek/deepseek-v4-flash" "qwen/qwen3.5-27b" "google/gemma-4-31b-it" "anthropic/claude-opus-4.7"; do MODEL=$M bun src/run.ts; done
for J in "google/gemini-3.1-pro-preview" "anthropic/claude-opus-4.7" "openai/gpt-5.5"; do
  for C in "openai/gpt-5.5" "qwen/qwen3.6-27b" "google/gemini-3.1-pro-preview" "deepseek/deepseek-v4-flash" "qwen/qwen3.5-27b" "google/gemma-4-31b-it" "anthropic/claude-opus-4.7"; do
    CANDIDATE=$C JUDGE=$J bun src/judge.ts
  done
done
bun src/aggregate.ts && bun src/render.ts
```
