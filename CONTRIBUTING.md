# Contributing to ЛИИ-Спорт-Bench-RU

Three ways to contribute:

## 1. Add a new model to the leaderboard

Anyone can run any new model through the bench. The result goes straight onto the leaderboard.

```bash
# 1. Clone + setup
git clone https://github.com/csylabs-org/lii-sport-bench-ru.git
cd lii-sport-bench-ru
cp .env.local.example .env.local
# Edit .env.local — add your OpenRouter API key

# 2. Run the candidate
MAX_TOKENS=8000 MODEL=<openrouter/model-id> bun code/run.ts
# Writes to data/outputs/<safe-model-name>.json

# 3. Judge it with all 3 judges
CANDIDATE=<openrouter/model-id> JUDGE=anthropic/claude-opus-4.7 MAX_TOKENS=6000 bun code/judge.ts
CANDIDATE=<openrouter/model-id> JUDGE=openai/gpt-5.5 MAX_TOKENS=6000 bun code/judge.ts
CANDIDATE=<openrouter/model-id> JUDGE=google/gemini-3.1-pro-preview MAX_TOKENS=6000 bun code/judge.ts
# Writes to data/scores/<candidate>__by__<judge>.json each

# 4. Re-aggregate + render
bun code/aggregate.ts
bun code/render.ts

# 5. Open a PR with:
#    - data/outputs/<your-model>.json
#    - data/scores/<your-model>__by__*.json (3 files)
#    - data/aggregated.json (updated)
#    - data/leaderboard.md / leaderboard.json / leaderboard.html (regenerated)
```

**Cost per model:** ~$3-25 USD depending on model pricing + reasoning-token consumption. Typical mid-tier model adds ~$5-10.

**Methodology rule:** if your candidate model also appears in the judges list (e.g., adding Claude Sonnet 4.6 and it's already a judge), the diagonal self-judge row will be flagged automatically by `render.ts`. Cross-judge mean is reported separately.

## 2. Propose new questions or categories

Open an Issue first to discuss scope. Then PR with new question files following the existing format in `data/tier1/`, `data/tier2/`, `data/tier3/`:

```markdown
**{ID-PREFIX}-{CATEGORY}-{NUM}** `[AUDIENCE]` `[DIFFICULTY]` [`[MCQ]` if applicable]
> Вопрос: {Russian question text}
>
> Эталонный ответ: {Russian reference answer with source citation}
>
> Критерии оценки:
> - Точность: {scoring criterion 1}
> - Полнота: {scoring criterion 2}
> - Дополнительный балл: {bonus criterion}
```

**Required tags:**
- Audience: `ФУНКЦИОНЕР` / `ТРЕНЕР` / `СПОРТСМЕН` / `МЕДИК` / `АНАЛИТИК` / `СШОР` / `ВУЗ`
- Difficulty: `Basic` / `Applied` / `Expert`
- Optional: `MCQ` for multiple-choice format

**Source citation requirement:** reference answers must cite specific regulation, rule, or method (e.g., "Правила ФИБА §29.1.2", "Приказ Минспорта №1006", "Регламент РФБ 2024"). Educated-guess answers without sources are rejected — they degrade the dataset.

## 3. Validate methodology (academic / federation experts)

If you teach at a sports academy / university / СШОР / federation training center and want to validate the methodology:

1. Open an Issue describing your expertise area (e.g., "biomechanics teacher at ДВГАФК" / "методист by Min Sport") and what you'd like to validate
2. We'll send you the relevant tier files + scoring rubric for review
3. Your written feedback gets posted in the Issue thread for transparency
4. Substantive contribution (new test items, graded eval rounds, written taxonomy analysis) → co-authorship eligibility on v1.0 publication
5. Methodology critique only (review without new contributions) → Acknowledgments in v1.0

**Co-authorship threshold** follows [ICMJE criteria](http://www.icmje.org/recommendations/browse/roles-and-responsibilities/defining-the-role-of-authors-and-contributors.html) — substantial contribution to design/data, drafting/revision, final approval, and accountability. Critique-only ≠ co-authorship per academic norms.

---

## Code style

- Bun TypeScript native — no external dependencies beyond `@types/bun`
- ESM imports, native `fetch`, native `path.join`
- 2-space indent, semicolons, double-quote strings
- No `any` — strict TypeScript
- Path constants at top of each script: `const IN = join(import.meta.dir, "..", "data", ...)`
- Stream-write incremental progress for long runs (write to disk every 10-20 calls so a kill mid-run doesn't lose all data)

## Data hygiene

- All raw outputs + scores are committed to git (yes, even the large JSON arrays). Reproducibility is non-negotiable.
- `aggregated.json` is regenerated from raw scores; commit it on update.
- `leaderboard.{md,json,html}` are committed on each release for snapshot stability.

## Issue templates

- `[QUESTION]` — propose a new test question or critique an existing one
- `[BUG]` — eval harness bug
- `[METHODOLOGY]` — methodology critique or proposal
- `[MODEL]` — request a model be run, or report results of a model you ran

---

*Methodology questions, license clarifications, federation-level collaboration asks → daniel@csylabs.com or [@techaroundsports](https://t.me/techaroundsports).*
