# Changelog

## Unreleased — Corpus-Building Lane (May 23, 2026)

**Status:** First high-signal source batch complete. `agy` selected as the default cheap generation lane. Corpus collection is Mac-first; NVIDIA is deferred to SFT training.

### What shipped

- Added `tools/corpus-prep/` corpus pipeline scaffold:
  - verified source registry
  - capped resumable static harvester
  - grounded Q&A synthesis
  - benchmark-leakage, PII, duplicate, license, and split gates
  - release artifacts (`train.jsonl`, `val.jsonl`, `test.jsonl`, manifests, hashes, license matrix, stats)
- Centralized secret lookup through the local vault env:
  - `/Users/daniely/csylabs_vault/.env.local`
  - Gemini/OpenRouter legacy fallback paths remain supported
- Added Antigravity CLI provider:
  - default provider: `agy`
  - model label: `antigravity-default-gemini-3.5-flash`
  - OpenRouter remains the fallback/baseline lane
- Added MinSport document API/PDF lane:
  - Next/Strapi document API discovery for `minsport.gov.ru`
  - `pdftotext` extraction for text PDFs
  - Tesseract OCR fallback for scanned PDFs (`rus+eng`)
  - curl fallback for MinSport TLS/API fetches
- Added RCSI/Лесгафта methodology article lane:
  - current issue article discovery
  - per-article `DC.Rights=https://creativecommons.org/licenses/by/4.0` license gate
  - article metadata/abstract extraction for the first smoke batch
- Blocked `teoriya.ru` for training use pending permission:
  - current site footer states that all material rights belong to `teoriya.ru`
  - current site footer states copying materials is prohibited
- Confirmed local Mac corpus-prep stack:
  - Apple Silicon Mac is the default machine for harvest, PDF extraction, OCR, cleaning, and split generation
  - NVIDIA GPU is not required for corpus collection; keep it for Gemma 4 31B SFT / Unsloth / FA2 training
- Fixed prompt hygiene:
  - source text is scrubbed for phone/email/SNILS-style PII before generation
  - final corpus scan gates still run after generation
- Hardened model-output parsing:
  - synthesis now accepts the first JSON array when `agy` adds trailing commentary
- Fixed long-document synthesis quality:
  - OCR prompts now sample beginning, middle, and end of long documents
  - generic prompt wording no longer assumes every source is anti-doping material
- First retained RUSADA high-signal batch:
  - `51` generated examples from 17 source pages
  - `51` kept after cleaning
  - split: `46 train / 3 val / 2 test`
  - no PII/leak scan hits
- Expanded retained RUSADA high-signal batch:
  - `103` raw crawled RUSADA pages
  - `29` Russian high-signal pages selected after URL filtering
  - `87` generated examples
  - `87` kept after cleaning
- First retained EVSK/EKP batch:
  - `3` MinSport PDFs extracted
  - `9` generated examples
  - `9` kept after cleaning
- First retained OCR federal-standards batch:
  - `3` scanned MinSport federal-standard PDFs OCRed
  - sports covered in smoke batch: eastern martial arts, darts, marine multiathlon
  - `9` generated examples
  - `9` kept after cleaning
- Expanded Mac OCR federal-standards review batch:
  - `12` scanned MinSport federal-standard PDFs OCRed
  - `36` generated examples
  - `36` kept after cleaning
- Scaled strict MinSport federal-standard checkpoint:
  - strict MinSport API discovery currently yields `21` verified federal-standard PDFs
  - `63` generated examples
  - `63` kept after cleaning
- First retained Лесгафта methodology batch:
  - `12` RCSI article records harvested from the current issue
  - every retained article exposed CC BY 4.0 in `DC.Rights`
  - `36` generated examples
  - `36` kept after cleaning
- Added human-approved federation-rules lane:
  - source id: `fed-rules-approved`
  - approval note: Daniel approved federation and MinSport documents for the working corpus on `2026-05-23`
  - retained rows carry `requires_human_approval=true` and `license_kind=human-approved-federation-public-doc`
  - downloader cap raised from 20 MB to 80 MB after FHR PDFs exposed a truncation failure at exactly 20,000,000 bytes
- First retained federation-rules batch:
  - `4` FHR hockey PDF documents extracted
  - `12` generated examples through `agy`
  - `12` kept after cleaning
- First retained volleyball federation-rules batch:
  - `2` VFR PDF documents extracted from the official volleyball rules page
  - retained synthesis uses the clean `2025` Минспорт-approved volleyball rules PDF
  - the advertised FIVB `2025-2028` PDF link currently returns HTML and is rejected by the PDF gate
  - the older FIVB `2021-2024` PDF is retained raw but excluded from synth because extracted text produced mojibake-contaminated answers
  - `3` generated examples through `agy`
  - `3` kept after cleaning
- Added direct-PDF federation source support:
  - approved source endpoints can now be direct `.pdf` URLs, not only HTML pages with PDF links
  - this is needed for federation pages where the canonical rules link is stable but the document listing is dynamic or stale
- First retained basketball federation-rules batch:
  - `1` RFB official basketball rules PDF extracted
  - the old RFB rules page currently returns `404` on the live Nuxt site, but the official PDF remains reachable
  - the listed official-interpretations URL currently returns `404`, so it is excluded
  - `3` generated examples through `agy`
  - `3` kept after cleaning
- First retained swimming federation-rules batch:
  - `1` 2026 Federation/Минспорт swimming rules PDF extracted
  - `3` generated examples through `agy`
  - `3` kept after cleaning
- Combined current retained release:
  - `312` generated examples
  - `312` kept after cleaning
  - split: `288 train / 13 val / 11 test`
  - source mix: `87` RUSADA, `9` EVSK/EKP, `63` MinSport federal standards, `36` Лесгафта, `72` CC BY CyberLeninka sport-history rows, `15` official/internal history rows, `12` FHR hockey rules, `3` VFR volleyball rules, `3` RFB basketball rules, `3` swimming rules, `3` RFS football rules, `3` RusAthletics rules, `3` sport gymnastics rules
- Documented scale-up boundary:
  - current federation rows are source-validation smoke rows
  - production corpus generation should first complete official PDF inventory, then run section/page chunked synthesis over clean extracted text
  - added approximate production targets per source family in `tools/corpus-prep/README.md`
- Expanded federation document inventory:
  - added human-approved/internal source ids for RFS football, RusAthletics athletics, and sport gymnastics rules PDFs
  - harvested and saved the PDFs under ignored `corpus/raw/<source-id>/documents/`
  - extracted one raw record per new source and retained `3` smoke rows per source through `agy`
  - wrestling remains pending because the official documents page currently exposes a templated PDF URL with an unresolved `{item_id}` placeholder
- Added bench-gap history source lane:
  - source id: `sport-history-ccby-cyberleninka`
  - first 24 CC BY CyberLeninka sport-history/legal-history PDFs harvested and saved under ignored raw documents
  - PDF fallback added because CyberLeninka HTML extraction was abstract-only
  - `72` generated history examples through `agy`
  - `72` kept after cleaning
- Added official/internal history source lane:
  - source id: `sport-history-official-approved`
  - first 5 federation/official history pages harvested behind `--include-human-approval`
  - `15` generated history examples through `agy`
  - `15` kept after cleaning
  - extraction is acceptable for smoke, but needs cleaner page-content filtering before production scale

### A/B result

| Provider | Generated | Kept | Drops | Notes |
|---|---:|---:|---:|---|
| Antigravity CLI `agy` | 36 | 36 | 0 | Slower, cheaper/subscription lane, no per-call cost accounting |
| OpenRouter `google/gemini-3.5-flash` | 36 | 34 | 2 | Faster, model-pinned, paid/token-metered fallback |

### Full-current raw diagnostic

- The retained RUSADA release uses URL filtering before generation:
  - include Russian `/athletes`, `/doping-control`, `/substances`, `/federations_leagues`, and selected `/education/*` pages
  - exclude English duplicates, contact/request/calendar/news/disqualification/admin pages
- MinSport federal-standard PDFs require OCR; the current strict-query Tesseract checkpoint retains 21 PDFs.

### Cleanup

- Removed stale ignored comparison artifacts and old OpenRouter-first batch folders.
- Kept only:
  - raw RUSADA harvest
  - raw EVSK/EKP harvest
  - retained `agy` synthesized JSONLs
  - combined current `agy` release folder

### Next steps

1. Section-chunk the saved federation PDFs beyond smoke volume, keeping the human-approved/internal label.
2. Scale Лесгафта/RCSI article coverage beyond the 12-article CC BY smoke batch.
3. Keep `teoriya.ru` blocked unless explicit reuse permission is obtained.

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
