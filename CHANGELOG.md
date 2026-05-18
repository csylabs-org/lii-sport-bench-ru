# Changelog

## v0.1 — 7-Model Open-vs-Closed Pilot (May 18, 2026)

**Status:** Pilot complete. Public release.

### What shipped

- **655 expert questions** across 35 sports in Russian
- **Top-3 judge ensemble** (Claude Opus 4.7 + GPT-5.5 + Gemini 3.1 Pro Preview)
- **200-Q stratified sample** (deterministic seed `lii-2026-05-13`)
- **7 candidate models** evaluated:

| Rank | Model | Weights | Overall |
|---|---|---|---:|
| 1 | Claude Opus 4.7 | closed | 9.10 |
| 2 | Gemini 3.1 Pro Preview | closed | 8.88 |
| 3 | GPT-5.5 | closed | 8.53 |
| 4 | DeepSeek V4 Flash | MIT | 8.03 |
| 5 | Qwen 3.5 27B | Apache 2.0 | 7.52 |
| 6 | Gemma 4 31B Instruct | Apache 2.0 | 7.45 |
| 7 | Qwen 3.6 27B | Apache 2.0 | 6.67 |

- **Cost:** ~$150 USD on OpenRouter (full reproducibility cost, 1400 candidate calls + 4200 judge calls)
- **Self-judging bias** disclosed openly (Opus + Gemini are both candidates and judges; cross-judge means also reported)

### What this enables

- ЛИИ-Спорт-Gemma-4-31B-Preview SFT (planned release June 15, 2026 on HuggingFace) will be scored against this baseline
- Methodology proof-of-concept for v1.0 (full 655-Q with academic validation)
- First open RU sport LLM benchmark — no prior art on this intersection

### Methodology decisions

- Stratified sampling within tiers (proportional to question counts)
- `temperature: 0` for reproducibility
- `seed: hash32("lii-2026-05-13:" + question_id)` deterministic per-question seed
- `provider.sort: "price"` on OpenRouter (cheapest provider per call)
- `max_tokens: 8000` for reasoning-mode candidates (Qwen 3.5/3.6, GPT-5.5, Gemini 3.1 Pro, Claude Opus 4.7) to avoid reasoning-truncation
- `max_tokens: 6000` + `reasoning: { effort: "low" }` for Gemini-as-judge calls (was 4000, hit JSON truncation in early runs)

### Known limitations

- 200-Q subset (not full 655-Q) — v1.0 will run on full set
- Two self-judging rows in the data (Opus × Opus, Gemini × Gemini) — bias quantified but not removed
- Only Tier-1 sports have full 8-category coverage; Tier-2/3 are abbreviated
- No human-graded ground truth yet — v1.0 adds 50-question expert-validated calibration set

### Source

- Original 2-candidate decision doc: [`docs/2026-05-16-pilot-gemma-vs-qwen.md`](./docs/2026-05-16-pilot-gemma-vs-qwen.md)
- Aggregator output: [`data/aggregated.json`](./data/aggregated.json)
- Raw scores: [`data/scores/`](./data/scores/) (21 files, one per candidate × judge pair)
- Raw candidate outputs: [`data/outputs/`](./data/outputs/) (7 files, one per candidate)

---

## Planned

### v0.2 — Full 655-Q + ЛИИ-Спорт-Preview (target: Q3 2026)

- Full 655-Q run (not just 200-Q stratified sample)
- ЛИИ-Спорт-Gemma-4-31B-Preview (our fine-tune) added as candidate
- Self-judging avoidance: ensemble auto-rebuilds when a candidate is also a judge
- Possibly: 50-question human-graded calibration set
- Tighter methodology footnote per ICMJE authorship criteria

### v1.0 — Academic Release with ДВГАФК Validation (target: late Q3 / Q4 2026)

- Methodology validated by ДВГАФК faculty (subject experts)
- Possible additions: scenario-rich items contributed by sports academies
- Open publication on Хабр / arXiv / HuggingFace
- Attribution by contribution depth (Acknowledgments → co-authorship per ICMJE)

---

*This bench is a living artifact. Critique, new questions, new model runs, methodology improvements — all welcome via GitHub Issues and PRs.*
