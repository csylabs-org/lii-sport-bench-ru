# ЛИИ-Спорт-Bench-RU

[![Habr article](https://img.shields.io/badge/Habr-1036448-orange)](https://habr.com/ru/articles/1036448/) [![License: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](./LICENSE) [![Data License: Apache 2.0](https://img.shields.io/badge/data-Apache_2.0-green.svg)](./LICENSE)

**The first open benchmark for evaluating Large Language Models on Russian-language sports-domain expertise.**

📖 **Featured article (Habr, RU, May 2026):** https://habr.com/ru/articles/1036448/  «Прогнали семь LLM через свой русский спортивный бенчмарк. Frontier-closed выигрывает 1.5-1.7 балла. Базовой моделью всё равно остаётся Gemma 4 31B — рассказываю почему.»

ЛИИ-Спорт-Bench-RU tests LLMs on 655 expert-level questions across 35 sports, designed to surface practical capability gaps for: federation officials (functionaries), coaches, athletes, sports physicians, analysts, sports schools (СШОР), and physical-culture universities (ВУЗы).

## Why this benchmark?

No open benchmark currently sits at the intersection of "Russian language" + "sports domain" + "open data" + "open methodology":

| Benchmark | Russian? | Sports? | Open? | Domain depth? |
|-----------|----------|---------|-------|---------------|
| [SportQA (NAACL 2024)](https://aclanthology.org/2024.findings-naacl.108/) | English only | Yes | Yes | Trivia-leaning |
| [MERA (AIRI + Sber)](https://github.com/ai-forever/MERA) | Russian | No | Partial (closed test set) | General reasoning |
| [RuMedBench](https://medbench.ru) | Russian | Medical only | Partial | Last updated 2022 |
| [EduBench-RU](https://github.com/csylabs-org/edubench-ru) | Russian | Education | Yes | Sibling project — pedagogy |
| **ЛИИ-Спорт-Bench-RU** | **Russian** | **Yes** | **Apache 2.0 / MIT** | **35 sports × 8 categories × 3 difficulties** |

## Benchmark structure

**655 questions** across three tiers:

| Tier | Sports | Q/sport | Total | Coverage |
|---|---|---|---|---|
| **Tier 1** | 8 (basketball, volleyball, football, hockey, swimming, athletics, wrestling, gymnastics) | 50 | 400 | Major RF disciplines |
| **Tier 2** | 4 groups (combat, winter, strength, precision-skill) | 45 | 180 | Group-level coverage |
| **Tier 3** | 3 batches (long-tail, ~15 sports) | 25 each | 75 | Surface-level |

**8 categories per Tier-1 sport:**

1. Правила и регламент (Rules)
2. Методика тренировок (Training methodology)
3. Биомеханика (Biomechanics)
4. Психология (Sport psychology)
5. Регуляторика и федерации (Regulatory + federations)
6. История (History)
7. Антидопинг РУСАДА (Anti-doping)
8. Сценарные ситуации (Scenario reasoning)

**Each question is tagged with:**
- **Audience:** ФУНКЦИОНЕР / ТРЕНЕР / СПОРТСМЕН / МЕДИК / АНАЛИТИК / СШОР / ВУЗ
- **Difficulty:** Basic / Applied / Expert
- **Format:** free-form or `[MCQ]` multiple-choice
- **Reference answer** with source citation (FIBA rules, Min Sport order numbers, RFB regulations, etc.)
- **Scoring rubric** for accuracy / completeness / bonus

## Evaluation methodology

**Top-3 judge ensemble** (independent vendor families to avoid single-judge bias):

| Judge | OpenRouter ID | Notes |
|---|---|---|
| Claude Opus 4.7 | `anthropic/claude-opus-4.7` | Strong on completeness |
| GPT-5.5 | `openai/gpt-5.5` | Systemically strictest |
| Gemini 3.1 Pro Preview | `google/gemini-3.1-pro-preview` | Strong on factual accuracy |

**4-dimension scoring rubric** (0-10 each):

1. **Accuracy** — factual correctness vs reference
2. **Completeness** — coverage of rubric criteria
3. **Bonus** — expert depth, source citations, nuances beyond reference
4. **RU linguistic** — Russian grammar, terminology, register

Per-question score = mean across 3 judges across 4 dimensions. Overall = mean across all dimensions.

**Self-judging bias is disclosed transparently:** when a candidate model is also one of the judges (e.g., Claude Opus 4.7 as both candidate AND judge), the self-rating row is flagged in `data/aggregated.json` and the cross-judge mean is also reported.

## Quick start

```bash
# Clone
git clone https://github.com/csylabs-org/lii-sport-bench-ru.git
cd lii-sport-bench-ru

# Install bun (https://bun.sh)
curl -fsSL https://bun.sh/install | bash

# Set up env
cp .env.local.example .env.local
# Edit .env.local — add your OPENROUTER_API_KEY

# Re-aggregate from committed data (no new API calls)
bun code/aggregate.ts
bun code/render.ts
# → data/aggregated.json + data/leaderboard.md + data/leaderboard.json + data/leaderboard.html

# Run a new model against the bench
MAX_TOKENS=8000 MODEL=anthropic/claude-haiku-4.5 bun code/run.ts
# Then judge it with 3 judges
CANDIDATE=anthropic/claude-haiku-4.5 JUDGE=anthropic/claude-opus-4.7 MAX_TOKENS=6000 bun code/judge.ts
CANDIDATE=anthropic/claude-haiku-4.5 JUDGE=openai/gpt-5.5 MAX_TOKENS=6000 bun code/judge.ts
CANDIDATE=anthropic/claude-haiku-4.5 JUDGE=google/gemini-3.1-pro-preview MAX_TOKENS=6000 bun code/judge.ts
# Re-aggregate
bun code/aggregate.ts && bun code/render.ts
```

## Current leaderboard — v0.1 pilot (200-Q stratified sample)

| Rank | Model | License | n | Accuracy | Completeness | Bonus | RU | **Overall** |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | Claude Opus 4.7 | closed | 200 | 8.67 | 9.16 | 8.92 | 9.65 | **9.10** |
| 2 | Gemini 3.1 Pro Preview | closed | 200 | 8.58 | 8.72 | 8.49 | 9.74 | **8.88** |
| 3 | GPT-5.5 | closed | 200 | 8.54 | 8.35 | 7.55 | 9.68 | **8.53** |
| 4 | DeepSeek V4 Flash | MIT | 193 | 7.75 | 8.06 | 7.28 | 9.05 | **8.03** |
| 5 | Qwen 3.5 27B | Apache 2.0 | 199 | 7.07 | 7.46 | 6.53 | 9.03 | **7.52** |
| 6 | **Gemma 4 31B Instruct** | Apache 2.0 | 200 | 7.30 | 7.39 | 6.14 | 8.98 | **7.45** |
| 7 | Qwen 3.6 27B | Apache 2.0 | 200 | 6.21 | 6.31 | 5.76 | 8.42 | **6.67** |

→ See [`docs/2026-05-16-pilot-gemma-vs-qwen.md`](./docs/2026-05-16-pilot-gemma-vs-qwen.md) for the original 2-candidate decision doc that triggered the expansion to 7 models.
→ See [`data/aggregated.json`](./data/aggregated.json) for full per-sport / per-difficulty / per-audience breakdowns.
→ Live interactive leaderboard at [bench.csylabs.com](https://bench.csylabs.com) (Sport tab).
→ Reasoning / Habr article: TBA Wed-Thu May 20-21.

## Reproducibility

Pilot cost: **~$150 USD on OpenRouter** for the full 7-candidate × 3-judge × 200-Q matrix. Anyone can reproduce.

All inputs (questions, prompts, sampling seed `lii-2026-05-13`) and outputs (1400 candidate answers, 4200 judge scores with reasoning) are committed to this repo. `bun code/aggregate.ts && bun code/render.ts` regenerates the leaderboard from committed data without any new API calls.

## Corpus-building lane

The benchmark is now also being used as the held-out evaluation core for the ЛИИ-Спорт SFT corpus. Training data must be built only from external sources and pass benchmark-leakage checks before release.

Current status:

- Corpus prep tooling lives in [`tools/corpus-prep/`](./tools/corpus-prep/).
- Corpus collection/prep runs Mac-first: local `pdftotext` + Tesseract `rus+eng` OCR on Apple Silicon, with NVIDIA reserved for later SFT training.
- Default generation lane: Antigravity CLI `agy` using Gemini 3.5 Flash routing.
- Fallback/audit lane: OpenRouter `google/gemini-3.5-flash`.
- Current retained corpus: expanded RUSADA high-signal anti-doping + MinSport ЕКП/EVSK procedures + OCR federal standards + CC BY Лесгафта methodology articles + CC BY CyberLeninka sport-history, sport-methodology, sport-science, and named-sport methodology articles + Wikidata CC0 sport facts + human-approved official history pages + human-approved federation rules batches for hockey, volleyball, basketball, swimming, football, athletics, gymnastics, and winter sports, plus section-chunk passes over saved federation/MinSport/winter PDFs, `5870/5907` examples kept after cleaning.
- Count semantics: corpus counts are generated SFT Q&A examples, not source-document counts. Source documents/pages are tracked separately under ignored `corpus/raw/`.
- The current release crosses the `5k` corpus-build gate, with `3760` open-license rows, `1104` human-approved/internal rows, and `1006` public-official rows. The coverage report has no undercoverage flags, and `general` rows are down to `48.84%`.
- Freeze/review notes are tracked in [`tools/corpus-prep/5K-SNAPSHOT-REVIEW.md`](./tools/corpus-prep/5K-SNAPSHOT-REVIEW.md). Do not start SFT until an immutable snapshot/export location is chosen and the human-approved/internal rows policy is signed off.
- Federation-rule examples are marked `requires_human_approval=true` and `license_kind=human-approved-federation-public-doc`; keep them separate from clean open-license publication lanes until downstream release policy is decided.
- Generated corpus artifacts are ignored by git under `corpus/`; release candidates should be reviewed before publication.

Next corpus milestones:

1. Cut an immutable internal snapshot from the current `5870/5907` clean checkpoint.
2. Decide whether the first LoRA/DoRA pilot uses open-license rows only or the mixed internal corpus.
3. Keep `teoriya.ru` blocked unless explicit reuse permission is obtained; current site footer says copying materials is prohibited.

## License

Two licenses, separate concerns:

- **Code / harness:** MIT — see [`LICENSE`](./LICENSE)
- **Questions / data:** Apache 2.0 — patent-grant clause matters for downstream educational reuse

Both fully commercial-friendly. Attribution: ООО «ЛИИ» (Лаборатория инновационных инициатив) / csylabs.

## Contributing

Critique of methodology, new questions for any sport, new model runs on the bench — all welcome via Issues and PRs. See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for how to:
- Add a new model to the leaderboard
- Propose new questions or new categories
- Validate methodology (academic / federation experts)

If you validate methodology with a substantive contribution (new test items / graded eval rounds / written taxonomy analysis), you're eligible for co-authorship on the v1.0 publication.

## Related projects

- [EduBench-RU](https://github.com/csylabs-org/edubench-ru) — sibling Russian education LLM benchmark by the same team
- [csylabs HuggingFace org](https://huggingface.co/csylabs) — open-weight RU domain LLMs in this lineup (EduLLM-RU + EduLLM-Chuvash + ЛИИ-Спорт coming June 15)
- [bench.csylabs.com](https://bench.csylabs.com) — live interactive leaderboard portal

## Authors

ООО «Лаборатория инновационных инициатив» (ЛИИ)
ИНН 2100031165 · Чебоксары, Чувашская Республика, РФ
daniel@csylabs.com · [@techaroundsports](https://t.me/techaroundsports)

## Cite

If you use this benchmark in research or product comparisons:

```bibtex
@misc{lii-sport-bench-ru-v01,
  title = {ЛИИ-Спорт-Bench-RU v0.1: An Open Russian-Language Sports-Domain LLM Benchmark},
  author = {Ivanov, Daniil and ООО ЛИИ},
  year = {2026},
  url = {https://github.com/csylabs-org/lii-sport-bench-ru},
  note = {655 questions across 35 sports, top-3 judge ensemble, Apache 2.0 / MIT}
}
```
