# Methodology

Full methodology documentation for ЛИИ-Спорт-Bench-RU. Companion to `README.md`.

## 1. Corpus design (655 questions)

### Tier 1 — Major RF sport disciplines (400 questions)

8 sports × 50 questions each. Selected by federation visibility, Олимпийский register prevalence, and Russian-language source density:

- Баскетбол (basketball)
- Волейбол (volleyball)
- Футбол (football / soccer)
- Хоккей (ice hockey)
- Плавание (swimming)
- Лёгкая атлетика (athletics / track-and-field)
- Борьба (wrestling)
- Гимнастика (gymnastics)

### Tier 2 — Sport groups (180 questions)

4 groups × 45 questions each. Groups chosen to surface group-level methodology + regulatory patterns:

- Единоборства (combat sports — judo, sambo, boxing, taekwondo)
- Зимние виды (winter — skiing, biathlon, figure skating, hockey-adjacent)
- Силовые и скиллорно-силовые (strength + technical-strength — powerlifting, weightlifting, throws)
- Точностные (precision — shooting, archery, billiards)

### Tier 3 — Long-tail (75 questions)

3 batches × 25 questions each. Light-coverage breadth across ~15 sports (badminton, table tennis, cycling, rowing, fencing, equestrian, etc.). Catches "models don't know niche sports" failure modes.

### 8 categories per Tier-1 sport

Each Tier-1 sport has 8 questions per category, structured to surface different capability axes:

| Category | Tests |
|---|---|
| **Правила и регламент** | Knowledge of official rules + recent rule changes |
| **Методика тренировок** | Training periodization, exercise selection, age-stage progression |
| **Биомеханика** | Joint mechanics, force vectors, technique analysis |
| **Психология** | Sport psychology, motivation, peak performance, anxiety management |
| **Регуляторика и федерации** | Federation structure, certification paths, tournament organization |
| **История** | Discipline history, key figures, milestone events |
| **Антидопинг РУСАДА** | WADA + РУСАДА regulations, prohibited substances, testing procedures |
| **Сценарные ситуации** | Real-world decision scenarios — "what would you do if..." |

### Audience tagging (7 audiences)

Each question is tagged with the intended professional audience:

- **ФУНКЦИОНЕР** (federation functionary) — administrative, regulatory, certification scenarios
- **ТРЕНЕР** (coach) — training method, periodization, athlete development
- **СПОРТСМЕН** (athlete) — preparation, recovery, in-event decisions
- **МЕДИК** (sports physician) — injury, recovery, anti-doping medical
- **АНАЛИТИК** (analyst) — performance data, scouting, tactical breakdown
- **СШОР** (sports school) — youth development, ФГОС-aligned curriculum, junior pathway
- **ВУЗ** (physical culture university) — academic register, methodology research, ФГОС ВО programs

### Difficulty tagging (3 levels)

- **Basic** — first-year/-textbook level. Should be answerable with general knowledge of the sport
- **Applied** — practitioner-level. Requires understanding of how rules + methodology interact in practice
- **Expert** — domain-specialist level. Requires citation of specific regulations, edge cases, or recent rule changes

### Question block format

```markdown
**{ID-PREFIX}-{CATEGORY-CODE}-{NUM}** `[AUDIENCE]` `[DIFFICULTY]` [`[MCQ]` if applicable]
> Вопрос: {question text in Russian}
>
> Эталонный ответ: {reference answer in Russian, with source citation}
>
> Критерии оценки:
> - Точность: {what constitutes accurate answer}
> - Полнота: {what constitutes complete answer}
> - Дополнительный балл: {bonus criterion — depth, edge cases, etc.}
```

ID-PREFIX is 3-character Cyrillic sport code (e.g., БАС = баскетбол, ВОЛ = волейбол). Category code is 2-3 character (e.g., ПР = правила, МТ = методика тренировок). NUM is zero-padded 3-digit sequence.

## 2. Stratified sampling (pilot = 200 questions from 655)

For pilot runs (~$150 USD on OpenRouter), 200 questions are sampled proportionally:

- Tier 1: 120 questions (60% of pilot, matches 61% of full corpus)
- Tier 2: 56 questions (28% of pilot, matches 27%)
- Tier 3: 24 questions (12% of pilot, matches 11%)

By difficulty: 57 Basic / 107 Applied / 36 Expert (matches difficulty distribution of full corpus).

**Deterministic sampling:** within each (tier, sport_file) group, questions are sorted by `SHA256(seed + question_id)` then the first N are selected. Seed for v0.1: `"lii-2026-05-13"`. Anyone running `bun code/sample.ts` gets the same 200 questions.

## 3. Top-3 judge ensemble

LLM-as-judge with three independent vendor families to mitigate single-vendor bias:

| Judge | OpenRouter ID | Why included |
|---|---|---|
| Claude Opus 4.7 | `anthropic/claude-opus-4.7` | Strong on completeness scoring + nuance |
| GPT-5.5 | `openai/gpt-5.5` | Systemically strictest — useful counterweight |
| Gemini 3.1 Pro Preview | `google/gemini-3.1-pro-preview` | Strong on factual accuracy + lowest cost |

**Per-question score:** mean across 3 judges across 4 dimensions.
**Per-bucket score:** mean across questions in bucket (per-sport, per-tier, per-difficulty, per-audience).
**Overall:** mean across all dimensions.

### Self-judging bias

A candidate model that is also one of the judges (e.g., Claude Opus 4.7 as candidate run through Claude Opus 4.7 judge) is **flagged but kept**. Self-judging inflation typically observed: +0.5 to +1.2 on overall score. The aggregator computes both the all-judges mean AND the cross-judge-only mean. The `render.ts` output flags self-judging rows explicitly in the leaderboard.

v0.2 will offer an opt-in mode where the ensemble auto-rebuilds (e.g., substitutes Claude Sonnet 4.6 for the Claude judge when the candidate is Claude Opus). For v0.1 the disclosure-and-keep approach matches the convention used by LMSYS Arena.

## 4. Scoring rubric (4 dimensions, 0-10 each)

**Точность (accuracy)** — Did the model give factually correct information?
- 10: Perfectly accurate, reference-grade
- 7-9: Mostly accurate, minor errors
- 4-6: Mixed — some accurate, some incorrect
- 1-3: Mostly incorrect
- 0: Refused / answered in wrong language / completely wrong

**Полнота (completeness)** — Did the model cover the criteria specified in the rubric?
- 10: Covers all rubric criteria + adds context
- 7-9: Covers most criteria
- 4-6: Covers some criteria
- 1-3: Missing most criteria
- 0: Did not address the question

**Бонус (bonus)** — Expert depth beyond the reference answer
- 10: Cites specific regulation/source, notes edge cases, mentions recent rule changes
- 7-9: Some bonus content (depth or sources)
- 4-6: Minor bonus content
- 1-3: No bonus
- 0: Generic or repetitive answer

**Русский язык (ru_linguistic)** — Russian language quality
- 10: Native-speaker level, correct terminology, no calques from English
- 7-9: Good Russian, minor stilted phrasings
- 4-6: Functional but awkward in places
- 1-3: Significant grammar/word-choice issues
- 0: Wrong language or unintelligible

**Hard rules in judge system prompt:**
- Don't penalize brevity if essence is covered
- Don't reward verbosity for its own sake
- "Я не знаю" / refusal = accuracy ≤ 2
- Answer in non-Russian = ru_linguistic = 0
- Return strictly JSON, no markdown wrappers

## 5. Inference parameters

| Parameter | Value | Rationale |
|---|---|---|
| `temperature` | 0 | Reproducibility |
| `seed` | `hash32(SEED + ":" + question_id)` | Deterministic per-question seed (when provider supports) |
| `provider.sort` | `"price"` | OpenRouter routes to cheapest provider per call |
| `max_tokens` (non-reasoning candidates) | 2048 | Sufficient for free-form answers |
| `max_tokens` (reasoning candidates) | 8000 | Reasoning tokens consume budget; 2048 leaves no room for answer |
| `max_tokens` (judges) | 6000 | Was 4000 in early runs, hit JSON truncation in Gemini judge |
| `reasoning: { effort: "low" }` (Gemini judge) | enabled | Cut Gemini judge cost from $0.05/call → $0.007/call |

Models flagged as "reasoning-capable" (Qwen 3.5/3.6, GPT-5.5, Gemini 3.1 Pro, Claude Opus 4.7) always get `MAX_TOKENS=8000` for the candidate run.

## 6. Cost estimates

For a new model added by a contributor:

| Item | Typical cost |
|---|---|
| Candidate run (200 questions) | $0.50 - $25 depending on output pricing |
| Judge × 3 ensemble (600 calls) | $5 - $30 depending on judge pricing |
| Total per new model | **~$5 - $50** |

Full pilot v0.1 (7 candidates + 21 judge passes) cost ~$150 USD on OpenRouter.

## 7. Data quality

For v0.1, automated audit found:
- 9 zero-score-but-OK rows out of 4176 judge calls (0.22%) — most are legitimate (judge correctly scoring 0 on candidate-truncated answers); fewer than 0.1% are true parse failures
- ~60 rows (1.4%) with empty `reasoning` field — Gemini judge brevity, doesn't affect numerical aggregation
- Rankings stable across all difficulty / audience / tier / RU-linguistic cuts

## 8. Limitations

1. **200-Q subset only.** Full 655-Q run reserved for v0.2 — pilot was cost-bounded.
2. **Two self-judging rows.** Bias quantified but not removed in v0.1.
3. **No human-graded calibration.** LLM-as-judge alone in v0.1. v0.2 plans 50-question expert-validated set as calibration anchor.
4. **Tier-1 / Tier-2 / Tier-3 imbalance.** Tier-1 has 8-category coverage; Tier-2/3 don't. Per-category analysis only meaningful within Tier-1.
5. **Reference answer quality varies.** Some answers cite specific regulations; others are method-summary descriptions. v1.0 will standardize.
6. **No multi-turn / agentic evaluation.** Single-prompt single-answer only.

## 9. Citation

```bibtex
@misc{lii-sport-bench-ru-v01,
  title = {ЛИИ-Спорт-Bench-RU v0.1: An Open Russian-Language Sports-Domain LLM Benchmark},
  author = {Ivanov, Daniil and ООО ЛИИ},
  year = {2026},
  url = {https://github.com/csylabs-org/lii-sport-bench-ru},
  note = {655 questions across 35 sports, top-3 judge ensemble, Apache 2.0 / MIT}
}
```
