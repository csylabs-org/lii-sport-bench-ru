# Changelog

## Unreleased — Corpus-Building Lane (May 23, 2026)

**Status:** First high-signal source batch complete and scaled past the 5k corpus-build gate at `5870/5907` clean rows, with no coverage underflags. `agy` remains the default cheap generation lane, with OpenRouter used as fallback/scale lane when `agy` returns malformed or empty output or batch throughput matters. Corpus collection is Mac-first; NVIDIA is deferred to SFT training.

### What shipped

- Added `tools/corpus-prep/` corpus pipeline scaffold:
  - verified source registry
  - capped resumable static harvester
  - grounded Q&A synthesis
  - benchmark-leakage, PII, duplicate, license, and split gates
  - release artifacts (`train.jsonl`, `val.jsonl`, `test.jsonl`, manifests, hashes, license matrix, stats)
- Centralized secret lookup without committed secret values:
  - exported env vars and repo-local ignored `.env.local`
  - optional vault root via `CSYLABS_VAULT_ROOT`
  - optional explicit path lists for Gemini/OpenRouter fallback env files
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
  - `360` generated examples
  - `360` kept after cleaning
  - split: `332 train / 16 val / 12 test`
  - source mix: `87` RUSADA, `9` EVSK/EKP, `63` MinSport federal standards, `36` Лесгафта, `72` CC BY CyberLeninka sport-history rows, `48` Wikidata CC0 sport-fact rows, `15` official/internal history rows, `12` FHR hockey rules, `3` VFR volleyball rules, `3` RFB basketball rules, `3` swimming rules, `3` RFS football rules, `3` RusAthletics rules, `3` sport gymnastics rules
- Added reproducible section-chunk scale pass:
  - new CLI: `tools/corpus-prep/chunk_raw.py`
  - generated `64` balanced section chunks from saved federation/MinSport raw documents
  - synthesized `192` additional grounded examples through `agy`
  - rebuilt current retained release at `552/552` with no PII, duplicate, license, or benchmark-leakage drops
  - rules coverage increased from `30` to `198` retained examples; sport-specific rows increased for hockey, volleyball, basketball, swimming, football, athletics, and gymnastics
- Added coverage reporting and second balanced scale pass:
  - new CLI: `tools/corpus-prep/coverage_report.py`
  - chunker now round-robins across multiple PDFs inside a source family, skips existing chunk rows by default, and supports `--batch-id` to avoid id collisions between scale batches
  - generated `128` balanced section chunks from saved federation/MinSport raw documents
  - synthesized `384` additional grounded examples through `agy`
  - cleaned extraction-noise glyphs from generated source excerpts before rebuilding
  - rebuilt current retained release at `936/936` with no PII, duplicate, license, or benchmark-leakage drops
  - coverage report still flags `below_sft_gate_5k`, `history_below_20pct`, `methodology_below_25pct`, and `winter_sports_missing`
- Added human-approved winter-sport source lane:
  - source id: `winter-sports-approved`
  - registered stable PDF endpoints for biathlon, cross-country skiing, alpine skiing, figure skating, and snowboard
  - harvested and saved `6` winter PDFs under ignored `corpus/raw/winter-sports-approved/documents/`
  - fixed sport inference so `горнолыжный спорт` maps to `alpine-skiing` before the broader skiing marker
  - generated `18` grounded smoke rows through `agy`
  - rebuilt current retained release at `954/954` with no PII, duplicate, license, or benchmark-leakage drops
  - coverage report no longer flags `winter_sports_missing`; remaining flags are `below_sft_gate_5k`, `history_below_20pct`, and `methodology_below_25pct`
- Scaled the winter-sport lane:
  - section-chunked the saved winter PDFs into `180` chunks
  - generated `540` additional grounded rows through `agy`
  - winter-sport retained rows now total `558`, inside the documented `500-1000` internal-row target band
- Added CC BY CyberLeninka sport-methodology lane:
  - source id: `sport-methodology-ccby-cyberleninka`
  - registered `11` CC BY article endpoints covering sport methodology, biomechanics, planning, selection, and training concepts
  - harvested `11` article records, with `10` PDF full texts and `1` HTML full text saved under ignored raw artifacts
  - generated `33` smoke rows plus `252` section-chunk rows through `agy`
  - generated a `108`-row OpenRouter top-up after the corresponding `agy` top-up returned empty output
  - retained `393` rows from this source in the current clean release
- Scaled CC BY CyberLeninka sport-history:
  - built a `120`-chunk history pool and rejected `9` mojibake/noise-heavy chunks before synthesis
  - `agy` returned malformed/empty output for this history batch, so OpenRouter `google/gemini-3.5-flash` produced the retained `330` section-chunk rows
  - sport-history source retained rows now total `396`, inside the documented `300-600` row target band
- Added CC BY CyberLeninka sport-science lane:
  - source id: `sport-science-ccby-cyberleninka`
  - registered `26` CC BY article endpoints covering sport medicine, injury prevention, endurance, biomechanics, psychology, skiing, snowboard, basketball, volleyball, athletics, and wrestling
  - harvested and saved `26` PDF full texts under ignored raw artifacts
  - initial filtered section pass retained `179` chunks -> `537` generated rows through `agy`
  - second filtered section pass retained `220` chunks -> `660` generated rows through OpenRouter `google/gemini-3.5-flash`
  - current clean release retains `1197` rows from this source
- Scaled CC BY history and CC0 facts:
  - added a `57`-chunk history top-up -> `171` OpenRouter rows
  - added a `131`-chunk history top-up -> `393` OpenRouter rows
  - expanded Wikidata CC0 from `16` raw facts to `141` total raw facts and synthesized `125` new records -> `375` OpenRouter rows
  - current clean release retains `943` CyberLeninka history rows and `423` Wikidata CC0 rows
- Scaled MinSport/RUSADA toward the 5k gate:
  - second MinSport federal-standard section pass retained `162` chunks -> `486` OpenRouter rows
  - RUSADA section pass retained `100` chunks -> `300` OpenRouter rows
  - current clean release retains `610` MinSport federal-standard rows and `387` RUSADA rows
- Added named-sport CC BY CyberLeninka methodology lane:
  - source id: `sport-specific-ccby-cyberleninka`
  - registered `35` named-sport article endpoints covering swimming, basketball, hockey, football, volleyball, athletics, gymnastics, and speed skating
  - harvested `34` verified CC BY PDF full texts
  - fixed CyberLeninka sport inference to prefer title/description/URL before full text, so bibliography terms do not override the article sport
  - section-chunked `256` named-sport chunks and generated `768` OpenRouter rows
  - current clean release retains all `768` rows from this source
- Hardened long-batch synthesis:
  - malformed model JSON responses are skipped instead of aborting the entire job
  - source excerpts with mojibake/extraction-noise markers are dropped during cleaning
  - zero-row synthesis output is treated as invalid for scale-up and should trigger inspection/fallback before rebuilding
- Current retained corpus checkpoint:
  - `5907` generated examples
  - `5870` kept after cleaning
  - `37` dropped: `9` extraction-noise rows and `28` duplicates
  - coverage: `3760` open-license rows, `1104` human-approved/internal rows, `1006` public-official rows
  - category mix: `3004` methodology, `1381` history, `1089` rules, `387` anti-doping, `9` federation-procedures
  - sport mix: `general` down to `2867/5870` (`48.84%`); no undercoverage flags remain
- Tightened the PII gate for standalone INN-like identifiers:
  - ВРВС sport-discipline codes such as `0420013611Я` are no longer dropped as false-positive INN-like PII
  - added regression coverage for retained sport discipline codes
- Documented scale-up boundary:
  - current federation rows are validation-scale rows, not final training volume
  - production corpus generation should widen section/page chunked synthesis over clean extracted text and keep human-approved/internal rows separate from public-release lanes
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
  - main-content extraction now prefers `main`/`article`/content blocks and trims common official-page navigation boilerplate
- Added Wikidata CC0 sport-facts lane:
  - source id: `sport-facts-wikidata-cc0`
  - first 16 Russian/Soviet athlete fact records harvested from Wikidata SPARQL
  - `48` generated history/factual examples through `agy`
  - `48` kept after cleaning
  - next scale-up should diversify by sport/event instead of relying on one broad athlete query

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
- Current ignored corpus artifacts are retained locally under `corpus/raw/`, `corpus/synth/`, and the combined clean release folder; they remain out of git until a reviewed publication snapshot is cut.

### Next steps

1. Cut an immutable internal snapshot from the current `5870/5907` checkpoint.
2. Decide whether the first LoRA/DoRA pilot uses open-license rows only or the mixed internal corpus.
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
