# Corpus Prep — ЛИИ-Спорт SFT v0.1

Offline-safe corpus pipeline scaffold for the Selectel AR45G validation batch.

## Current State

- Recommended provider: `agy` (Antigravity CLI, Gemini 3.5 Flash default routing).
- Fallback provider: OpenRouter `google/gemini-3.5-flash`.
- Runtime decision: collect/prep on the Mac first (`pdftotext` + Tesseract `rus+eng` OCR); reserve NVIDIA for Gemma 4 31B SFT training.
- Current retained release: expanded RUSADA high-signal anti-doping + MinSport ЕКП/EVSK procedures + OCR federal standards + CC BY Лесгафта methodology articles + CC BY CyberLeninka sport-history, sport-methodology, sport-science, and named-sport methodology articles + Wikidata CC0 sport facts + human-approved official history pages + human-approved federation rules batches for hockey, volleyball, basketball, swimming, football, athletics, gymnastics, and winter sports, plus section-chunk passes over saved federation/MinSport/winter PDFs, `5870/5907` examples kept after cleaning.
- Corpus example counts are generated SFT Q&A rows. Source counts are separate raw pages/PDFs/article records under `corpus/raw/`.
- Federation-rule rows are retained for the working/internal corpus only: `requires_human_approval=true`, `license_kind=human-approved-federation-public-doc`.
- New federation source inventory has saved football, athletics, gymnastics, and winter-sport PDFs under `corpus/raw/<source-id>/documents/`; winter sport PDFs are now section-chunked into the current internal release.
- Retained generated artifacts:
  - `corpus/raw/rusada-edu/harvest.jsonl`
  - `corpus/raw/evsk-ekp/harvest.jsonl`
  - `corpus/raw/minsport-fed-standards/harvest.jsonl`
  - `corpus/raw/lesgaft-uchenye-zapiski/harvest.jsonl`
  - `corpus/raw/fed-rules-approved/harvest.jsonl`
  - `corpus/raw/fed-rules-volleyball-approved/harvest.jsonl`
  - `corpus/raw/fed-rules-basketball-approved/harvest.jsonl`
  - `corpus/raw/fed-rules-swimming-approved/harvest.jsonl`
  - `corpus/raw/fed-rules-football-approved/harvest.jsonl`
  - `corpus/raw/fed-rules-athletics-approved/harvest.jsonl`
  - `corpus/raw/fed-rules-gymnastics-approved/harvest.jsonl`
  - `corpus/raw/winter-sports-approved/harvest.jsonl`
  - `corpus/raw/sport-methodology-ccby-cyberleninka/harvest.jsonl`
  - `corpus/raw/sport-science-ccby-cyberleninka/harvest.jsonl`
  - `corpus/raw/sport-specific-ccby-cyberleninka/harvest.jsonl`
  - `corpus/raw/sport-history-ccby-cyberleninka/harvest.jsonl`
  - `corpus/raw/sport-history-official-approved/harvest.jsonl`
  - `corpus/raw/sport-facts-wikidata-cc0/harvest.jsonl`
  - `corpus/raw/section-chunks-winter-sports-current/harvest.jsonl`
  - `corpus/raw/section-chunks-methodology-ccby-current/harvest.jsonl`
  - `corpus/raw/section-chunks-methodology-ccby-balanced-02/harvest.jsonl`
  - `corpus/raw/section-chunks-history-ccby-filtered/harvest.jsonl`
  - `corpus/raw/section-chunks-sport-science-ccby-current/harvest.jsonl`
  - `corpus/raw/section-chunks-sport-science-ccby-balanced-02/harvest.jsonl`
  - `corpus/raw/section-chunks-minsport-fed-standards-balanced-02/harvest.jsonl`
  - `corpus/raw/section-chunks-history-ccby-balanced-03/harvest.jsonl`
  - `corpus/raw/section-chunks-history-ccby-balanced-04/harvest.jsonl`
  - `corpus/raw/section-chunks-rusada-edu-balanced-01/harvest.jsonl`
  - `corpus/raw/section-chunks-sport-specific-ccby-named-01/harvest.jsonl`
  - `corpus/raw/section-chunks-sport-specific-ccby-named-01-filtered/harvest.jsonl`
  - `corpus/synth/agy-rusada-high-signal-current.jsonl`
  - `corpus/synth/agy-evsk-ekp-current.jsonl`
  - `corpus/synth/agy-minsport-fed-standards-ocr-current.jsonl`
  - `corpus/synth/agy-lesgaft-current.jsonl`
  - `corpus/synth/agy-fed-rules-approved-current.jsonl`
  - `corpus/synth/agy-fed-rules-volleyball-approved-current.jsonl`
  - `corpus/synth/agy-fed-rules-basketball-approved-current.jsonl`
  - `corpus/synth/agy-fed-rules-swimming-approved-current.jsonl`
  - `corpus/synth/agy-fed-rules-football-approved-current.jsonl`
  - `corpus/synth/agy-fed-rules-athletics-approved-current.jsonl`
  - `corpus/synth/agy-fed-rules-gymnastics-approved-current.jsonl`
  - `corpus/synth/agy-winter-sports-approved-current.jsonl`
  - `corpus/synth/agy-section-chunks-fed-minsport-current.jsonl`
  - `corpus/synth/agy-section-chunks-fed-minsport-balanced-01.jsonl`
  - `corpus/synth/agy-section-chunks-winter-sports-current.jsonl`
  - `corpus/synth/agy-sport-history-ccby-cyberleninka-current.jsonl`
  - `corpus/synth/agy-sport-methodology-ccby-cyberleninka-current.jsonl`
  - `corpus/synth/agy-section-chunks-methodology-ccby-current.jsonl`
  - `corpus/synth/agy-section-chunks-sport-science-ccby-current.jsonl`
  - `corpus/synth/openrouter-section-chunks-history-ccby-current.jsonl`
  - `corpus/synth/openrouter-section-chunks-methodology-ccby-balanced-02.jsonl`
  - `corpus/synth/openrouter-section-chunks-sport-science-ccby-balanced-02.jsonl`
  - `corpus/synth/openrouter-section-chunks-minsport-fed-standards-balanced-02.jsonl`
  - `corpus/synth/openrouter-section-chunks-history-ccby-balanced-03.jsonl`
  - `corpus/synth/openrouter-section-chunks-history-ccby-balanced-04.jsonl`
  - `corpus/synth/openrouter-section-chunks-rusada-edu-balanced-01.jsonl`
  - `corpus/synth/openrouter-section-chunks-sport-specific-ccby-named-01.jsonl`
  - `corpus/synth/agy-sport-history-official-approved-current.jsonl`
  - `corpus/synth/agy-sport-facts-wikidata-cc0-current.jsonl`
  - `corpus/synth/openrouter-sport-facts-wikidata-cc0-expanded-current.jsonl`
  - `corpus/lii-sport-sft-v0.1-current-agy-clean/`

## Scale-Up Workflow

The current federation-rule rows have passed the first section-chunk validation pass, but they are still below final training volume. The production sequence is:

1. Source inventory: find stable official pages/PDF URLs, add them to `sources.yaml`, and harvest the PDFs into `corpus/raw/<source-id>/documents/`.
2. Extraction QA: spot-check `pdftotext`/OCR output before generation; reject HTML masquerading as PDF, broken links, mojibake-heavy text, and duplicates.
3. Smoke synthesis: generate `3` grounded rows from each new document or source family to confirm prompt/extraction quality.
4. Production synthesis: split clean long documents into topical/page chunks and generate `3-5` rows per chunk, then run dedupe, benchmark-leakage, PII, license, and split gates.
5. Release decision: keep human-approved/internal federation rows separate from open-license publication rows until downstream release policy is decided.

Approximate production targets after chunking:

| Source family | Current retained rows | Production target | Status |
|---|---:|---:|---|
| FHR hockey rules/officiating PDFs | 84 | 150+ | Second balanced pass retained across multiple PDFs; continue toward target |
| VFR volleyball 2025 rules PDF | 75 | 60-120 | Production-range seed retained; older PDF rows require spot-checking before publication |
| RFB basketball 2024 rules PDF | 75 | 80-150 | Near production target; interpretations URL currently 404 |
| Swimming 2026 rules PDF | 75 | 50-100 | Production-range seed retained |
| RFS football 2025 rules PDF | 75 | 100-180 | Continue section chunking toward target |
| RusAthletics 2023 rules PDF | 75 | 80-150 | Near production target |
| Sport Gymnastics 2022 rules PDF | 75 | 80-150 | Near production target |
| Winter sport federation/MinSport PDFs | 558 | 500-1000 | Inside lower target band after 180 section chunks -> 540 rows; keep internal/human-approved |
| MinSport federal standards | 610 | 600-1000 | Second balanced pass now covers more standards documents; continue named-sport/СШОР scaling |
| RUSADA high-signal pages | 387 | 300-500 | Inside near-term anti-doping target; avoid over-weighting compliance |
| Лесгафта/RCSI CC BY articles | 36 | 100+ | Needs more CC BY article inventory beyond current issue |
| CyberLeninka CC BY sport-history PDFs | 943 | 800-1200 | Above first target band after two top-ups; use only named-sport history from here |
| CyberLeninka CC BY sport-methodology PDFs | 393 | 300-600 | Inside target band after article smoke + section chunks + OpenRouter top-up |
| CyberLeninka CC BY sport-science PDFs | 1197 | 1000-1500 | Main new open-license methodology/medicine/biomechanics lane; use targeted named-sport chunks next |
| CyberLeninka CC BY named-sport methodology PDFs | 768 | 700-1200 | Cleared the `general_sport_above_50pct` flag; current batch covers swimming, basketball, hockey, football, volleyball, athletics, gymnastics, and speed skating |
| Official/internal history pages | 15 | 500-1000 | First 5 pages retained behind `--include-human-approval`; needs cleaner page extraction |
| Wikidata CC0 sport facts | 423 | 300-600 | Inside first target band; next queries should be sport/event-specific |

Current immediate task: cut an immutable internal snapshot from the `5870/5907` checkpoint before any SFT attempt. The current coverage report has no undercoverage flags; `general` rows are `2867/5870` (`48.84%`). Wrestling remains pending because the official documents page currently exposes a templated PDF URL with an unresolved `{item_id}` placeholder; resolve the live API/JS document id before harvesting it.

## Bench-Gap Source Expansion

The next corpus scale-up must be bench-directed, not just larger. The weak buckets for Gemma 4 31B base are history, ВУЗ, СШОР, winter sports, volleyball, federation/regulatory, and methodology. The source expansion plan is tracked in [`SOURCE-EXPANSION-PLAN.md`](./SOURCE-EXPANSION-PLAN.md).

Priority new lanes:

| Lane | Source id | License posture | First target |
|---|---|---|---:|
| CC BY sport-history papers | `sport-history-ccby-cyberleninka` | Public-safe if each article exposes CC BY | 800-1200 rows; 943 retained |
| CC BY sport-methodology papers | `sport-methodology-ccby-cyberleninka` | Public-safe if each article exposes CC BY | 300-600 rows; 393 retained |
| CC BY sport-science papers | `sport-science-ccby-cyberleninka` | Public-safe if each article exposes CC BY | 1000-1500 rows; 1197 retained |
| CC BY named-sport methodology papers | `sport-specific-ccby-cyberleninka` | Public-safe if each article exposes CC BY | 700-1200 rows; 768 retained |
| CC0 structured sport facts | `sport-facts-wikidata-cc0` | Public-safe | 300-600 rows; 423 retained |
| Official federation/OKR history pages | `sport-history-official-approved` | Human-approved/internal | 500-1000 rows; first 15 retained |
| Winter-sport rules/methodology | `winter-sports-approved` + CC BY filters | Mixed; keep separated | 500-1000 rows; 558 retained |
| Section-chunked saved PDFs | existing federation/MinSport sources | Mixed; keep separated | 1500-3000 rows |

The `5k` corpus-build gate is reached and undercoverage flags are clear, but do not start SFT until this checkpoint is exported/frozen and the mixed internal vs open-license training policy is signed off. The serious public Preview target remains `30k-60k` examples.

## Commands

```bash
cd /path/to/lii-sport-bench-ru

# Inspect source plan without scraping or API calls.
python3 -B tools/corpus-prep/harvest.py --repo-root "$PWD"

# Run a capped verified-license static harvest (human-approval sources excluded).
python3 -B tools/corpus-prep/harvest.py --repo-root "$PWD" --run --source-id rusada-edu --max-pages 10

# Seed a tiny local non-bench demo batch for pipeline validation.
python3 -B tools/corpus-prep/harvest.py --repo-root "$PWD" --seed-demo

# Clean, leakage-check, split, and write release artifacts.
PYTHONPATH=tools/corpus-prep python3 -B tools/corpus-prep/clean.py --repo-root "$PWD" --output-name lii-sport-sft-v0.1-demo

# Build balanced section chunks from harvested long PDFs/pages.
PYTHONPATH=tools/corpus-prep python3 -B tools/corpus-prep/chunk_raw.py \
  --repo-root "$PWD" \
  --input-root "$PWD/corpus/raw" \
  --output "$PWD/corpus/raw/section-chunks-fed-minsport-current/harvest.jsonl" \
  --source-id fed-rules-approved \
  --source-id fed-rules-volleyball-approved \
  --source-id fed-rules-basketball-approved \
  --source-id fed-rules-swimming-approved \
  --source-id fed-rules-football-approved \
  --source-id fed-rules-athletics-approved \
  --source-id fed-rules-gymnastics-approved \
  --source-id minsport-fed-standards \
  --chunks-per-source 16 \
  --batch-id balanced-01

# Report coverage after a clean release rebuild.
PYTHONPATH=tools/corpus-prep python3 -B tools/corpus-prep/coverage_report.py \
  --repo-root "$PWD" \
  --input-root "$PWD/corpus/lii-sport-sft-v0.1-current-agy-clean" \
  --output-json "$PWD/corpus/lii-sport-sft-v0.1-current-agy-clean/coverage.json" \
  --output-md "$PWD/corpus/lii-sport-sft-v0.1-current-agy-clean/COVERAGE.md"

# Recommended cheap lane: generate grounded Q&A through Antigravity CLI.
python3 -B tools/corpus-prep/qa_synthesize.py --repo-root "$PWD" --provider agy --max-examples 10 --questions-per-chunk 3

# Baseline / fallback lane: generate grounded Q&A through OpenRouter.
python3 -B tools/corpus-prep/qa_synthesize.py --repo-root "$PWD" --provider openrouter --model google/gemini-3.5-flash --max-examples 10 --questions-per-chunk 3

# Clean synthesized SFT rows only.
python3 -B tools/corpus-prep/clean.py --repo-root "$PWD" --input-root "$PWD/corpus/synth" --output-name lii-sport-sft-v0.1-first-batch
```

Current retained RUSADA high-signal batch:

```bash
python3 -B tools/corpus-prep/qa_synthesize.py \
  --repo-root "$PWD" \
  --provider agy \
  --input-root "$PWD/corpus/raw" \
  --output "$PWD/corpus/synth/agy-rusada-high-signal-current.jsonl" \
  --include-url-regex '^https://rusada\.ru/(athletes|doping-control|substances|federations_leagues|education/(educational-programs|online-training|training-course-code-of-ethics-rusada|for-children|materials)/?)' \
  --exclude-url-regex '/en/|contact|request|ratings|scientific-conference|calendar|news|disqualifications' \
  --max-examples 29 \
  --questions-per-chunk 3 \
  --agy-timeout-seconds 120

python3 -B tools/corpus-prep/clean.py \
  --repo-root "$PWD" \
  --input-root "$PWD/corpus/synth/agy-rusada-high-signal-current.jsonl" \
  --output-name lii-sport-sft-v0.1-rusada-high-signal-agy-clean
```

MinSport EVSK/EKP batch and combined current release:

```bash
python3 -B tools/corpus-prep/harvest.py \
  --repo-root "$PWD" \
  --run \
  --source-id evsk-ekp \
  --max-pages 5 \
  --delay-seconds 0.5

python3 -B tools/corpus-prep/qa_synthesize.py \
  --repo-root "$PWD" \
  --provider agy \
  --input-root "$PWD/corpus/raw/evsk-ekp" \
  --output "$PWD/corpus/synth/agy-evsk-ekp-current.jsonl" \
  --max-examples 3 \
  --questions-per-chunk 3 \
  --agy-timeout-seconds 120

python3 -B tools/corpus-prep/clean.py \
  --repo-root "$PWD" \
  --input-root "$PWD/corpus/synth" \
  --output-name lii-sport-sft-v0.1-current-agy-clean
```

MinSport OCR federal-standards smoke batch:

```bash
python3 -B tools/corpus-prep/harvest.py \
  --repo-root "$PWD" \
  --run \
  --source-id minsport-fed-standards \
  --max-pages 3 \
  --delay-seconds 0.5

python3 -B tools/corpus-prep/qa_synthesize.py \
  --repo-root "$PWD" \
  --provider agy \
  --input-root "$PWD/corpus/raw/minsport-fed-standards" \
  --output "$PWD/corpus/synth/agy-minsport-fed-standards-ocr-current.jsonl" \
  --max-examples 3 \
  --questions-per-chunk 3 \
  --agy-timeout-seconds 120
```

Current Mac checkpoint:

```bash
python3 -B tools/corpus-prep/harvest.py \
  --repo-root "$PWD" \
  --run \
  --source-id minsport-fed-standards \
  --max-pages 30 \
  --delay-seconds 0.5

python3 -B tools/corpus-prep/qa_synthesize.py \
  --repo-root "$PWD" \
  --provider agy \
  --input-root "$PWD/corpus/raw/minsport-fed-standards" \
  --output "$PWD/corpus/synth/agy-minsport-fed-standards-ocr-current.jsonl" \
  --max-examples 21 \
  --questions-per-chunk 3 \
  --agy-timeout-seconds 120

python3 -B tools/corpus-prep/clean.py \
  --repo-root "$PWD" \
  --input-root "$PWD/corpus/synth" \
  --output-name lii-sport-sft-v0.1-current-agy-clean
```

Лесгафта/RCSI CC BY methodology smoke batch:

```bash
python3 -B tools/corpus-prep/harvest.py \
  --repo-root "$PWD" \
  --run \
  --source-id lesgaft-uchenye-zapiski \
  --max-pages 12 \
  --delay-seconds 0.5

python3 -B tools/corpus-prep/qa_synthesize.py \
  --repo-root "$PWD" \
  --provider agy \
  --input-root "$PWD/corpus/raw/lesgaft-uchenye-zapiski" \
  --output "$PWD/corpus/synth/agy-lesgaft-current.jsonl" \
  --max-examples 12 \
  --questions-per-chunk 3 \
  --agy-timeout-seconds 120

python3 -B tools/corpus-prep/clean.py \
  --repo-root "$PWD" \
  --input-root "$PWD/corpus/synth" \
  --output-name lii-sport-sft-v0.1-current-agy-clean
```

Human-approved federation-rules batch:

```bash
python3 -B tools/corpus-prep/harvest.py \
  --repo-root "$PWD" \
  --run \
  --include-human-approval \
  --source-id fed-rules-approved \
  --max-pages 4 \
  --delay-seconds 0.3

python3 -B tools/corpus-prep/qa_synthesize.py \
  --repo-root "$PWD" \
  --provider agy \
  --input-root "$PWD/corpus/raw/fed-rules-approved" \
  --output "$PWD/corpus/synth/agy-fed-rules-approved-current.jsonl" \
  --max-examples 4 \
  --questions-per-chunk 3 \
  --agy-timeout-seconds 420

python3 -B tools/corpus-prep/clean.py \
  --repo-root "$PWD" \
  --input-root "$PWD/corpus/synth" \
  --output-name lii-sport-sft-v0.1-current-agy-clean
```

Human-approved volleyball federation-rules batch:

```bash
python3 -B tools/corpus-prep/harvest.py \
  --repo-root "$PWD" \
  --run \
  --include-human-approval \
  --source-id fed-rules-volleyball-approved \
  --max-pages 3 \
  --delay-seconds 0.3

python3 -B tools/corpus-prep/qa_synthesize.py \
  --repo-root "$PWD" \
  --provider agy \
  --input-root "$PWD/corpus/raw/fed-rules-volleyball-approved" \
  --output "$PWD/corpus/synth/agy-fed-rules-volleyball-approved-current.jsonl" \
  --include-url-regex '5515' \
  --max-examples 1 \
  --questions-per-chunk 3 \
  --agy-timeout-seconds 420

python3 -B tools/corpus-prep/clean.py \
  --repo-root "$PWD" \
  --input-root "$PWD/corpus/synth" \
  --output-name lii-sport-sft-v0.1-current-agy-clean
```

Human-approved direct-PDF federation-rules batches:

```bash
python3 -B tools/corpus-prep/harvest.py \
  --repo-root "$PWD" \
  --run \
  --include-human-approval \
  --source-id fed-rules-basketball-approved \
  --max-pages 2 \
  --delay-seconds 0.3

python3 -B tools/corpus-prep/qa_synthesize.py \
  --repo-root "$PWD" \
  --provider agy \
  --input-root "$PWD/corpus/raw/fed-rules-basketball-approved" \
  --output "$PWD/corpus/synth/agy-fed-rules-basketball-approved-current.jsonl" \
  --max-examples 1 \
  --questions-per-chunk 3 \
  --agy-timeout-seconds 420

python3 -B tools/corpus-prep/harvest.py \
  --repo-root "$PWD" \
  --run \
  --include-human-approval \
  --source-id fed-rules-swimming-approved \
  --max-pages 1 \
  --delay-seconds 0.3

python3 -B tools/corpus-prep/qa_synthesize.py \
  --repo-root "$PWD" \
  --provider agy \
  --input-root "$PWD/corpus/raw/fed-rules-swimming-approved" \
  --output "$PWD/corpus/synth/agy-fed-rules-swimming-approved-current.jsonl" \
  --max-examples 1 \
  --questions-per-chunk 3 \
  --agy-timeout-seconds 420
```

Newly harvested federation-rule inventory PDFs:

```bash
python3 -B tools/corpus-prep/harvest.py \
  --repo-root "$PWD" \
  --run \
  --include-human-approval \
  --source-id fed-rules-football-approved \
  --max-pages 1 \
  --delay-seconds 0.3

python3 -B tools/corpus-prep/harvest.py \
  --repo-root "$PWD" \
  --run \
  --include-human-approval \
  --source-id fed-rules-athletics-approved \
  --max-pages 1 \
  --delay-seconds 0.3

python3 -B tools/corpus-prep/harvest.py \
  --repo-root "$PWD" \
  --run \
  --include-human-approval \
  --source-id fed-rules-gymnastics-approved \
  --max-pages 1 \
  --delay-seconds 0.3
```

Human-approved winter-sport PDF smoke batch:

```bash
python3 -B tools/corpus-prep/harvest.py \
  --repo-root "$PWD" \
  --run \
  --include-human-approval \
  --source-id winter-sports-approved \
  --max-pages 6 \
  --delay-seconds 0.3

python3 -B tools/corpus-prep/qa_synthesize.py \
  --repo-root "$PWD" \
  --provider agy \
  --input-root "$PWD/corpus/raw/winter-sports-approved" \
  --output "$PWD/corpus/synth/agy-winter-sports-approved-current.jsonl" \
  --max-examples 6 \
  --questions-per-chunk 3 \
  --agy-timeout-seconds 420

PYTHONPATH=tools/corpus-prep python3 -B tools/corpus-prep/clean.py \
  --repo-root "$PWD" \
  --input-root "$PWD/corpus/synth" \
  --output-name lii-sport-sft-v0.1-current-agy-clean
```

Winter section-chunk scale pass:

```bash
PYTHONPATH=tools/corpus-prep python3 -B tools/corpus-prep/chunk_raw.py \
  --repo-root "$PWD" \
  --input-root "$PWD/corpus/raw" \
  --output "$PWD/corpus/raw/section-chunks-winter-sports-current/harvest.jsonl" \
  --source-id winter-sports-approved \
  --chunks-per-source 180 \
  --chunk-chars 4500 \
  --min-chars 800 \
  --batch-id winter-scale-01

python3 -B tools/corpus-prep/qa_synthesize.py \
  --repo-root "$PWD" \
  --provider agy \
  --input-root "$PWD/corpus/raw/section-chunks-winter-sports-current" \
  --output "$PWD/corpus/synth/agy-section-chunks-winter-sports-current.jsonl" \
  --max-examples 180 \
  --questions-per-chunk 3 \
  --agy-timeout-seconds 420
```

CyberLeninka CC BY methodology scale pass:

```bash
python3 -B tools/corpus-prep/harvest.py \
  --repo-root "$PWD" \
  --run \
  --source-id sport-methodology-ccby-cyberleninka \
  --max-pages 11 \
  --delay-seconds 0.3

PYTHONPATH=tools/corpus-prep python3 -B tools/corpus-prep/chunk_raw.py \
  --repo-root "$PWD" \
  --input-root "$PWD/corpus/raw" \
  --output "$PWD/corpus/raw/section-chunks-methodology-ccby-current/harvest.jsonl" \
  --source-id sport-methodology-ccby-cyberleninka \
  --chunks-per-source 84 \
  --chunk-chars 3200 \
  --min-chars 800 \
  --batch-id methodology-scale-01

python3 -B tools/corpus-prep/qa_synthesize.py \
  --repo-root "$PWD" \
  --provider agy \
  --input-root "$PWD/corpus/raw/section-chunks-methodology-ccby-current" \
  --output "$PWD/corpus/synth/agy-section-chunks-methodology-ccby-current.jsonl" \
  --max-examples 84 \
  --questions-per-chunk 3 \
  --agy-timeout-seconds 420
```

CyberLeninka CC BY history filtered scale pass:

```bash
PYTHONPATH=tools/corpus-prep python3 -B tools/corpus-prep/chunk_raw.py \
  --repo-root "$PWD" \
  --input-root "$PWD/corpus/raw" \
  --output "$PWD/corpus/raw/section-chunks-history-ccby-pool/harvest.jsonl" \
  --source-id sport-history-ccby-cyberleninka \
  --chunks-per-source 120 \
  --chunk-chars 3000 \
  --min-chars 800 \
  --batch-id history-scale-02

# Filter extraction-noise chunks before synthesis, then use OpenRouter if AGY returns empty output.
python3 -B tools/corpus-prep/qa_synthesize.py \
  --repo-root "$PWD" \
  --provider openrouter \
  --model google/gemini-3.5-flash \
  --input-root "$PWD/corpus/raw/section-chunks-history-ccby-filtered" \
  --output "$PWD/corpus/synth/openrouter-section-chunks-history-ccby-current.jsonl" \
  --max-examples 111 \
  --questions-per-chunk 3
```

Secret lookup:

- exported `GEMINI_API_KEY` / `OPENROUTER_API_KEY`
- repo-local ignored `.env.local`
- optional vault root via `CSYLABS_VAULT_ROOT`
- optional explicit path lists via `CORPUS_DOTENV_PATHS` / `CORPUS_CLAUDE_SETTINGS_PATHS`

## Model Defaults

- Antigravity CLI bulk Q&A generation: `antigravity-default-gemini-3.5-flash`
- Direct Gemini extraction / translation / quality checks: `gemini-3.5-flash`
- OpenRouter bulk Q&A generation: `google/gemini-3.5-flash`
- Cheap OpenRouter smoke tests: `qwen/qwen3.6-flash`
- Trainable base for SFT: `google/gemma-4-31b-it`

## Guardrails

- `data/questions.json` is treated as the held-out benchmark and is never used as training data.
- `fed-rules` is marked `requires_human_approval=true` and is excluded from normal harvest plans unless explicitly included. Current human-approved/internal lanes: FHR hockey, VFR volleyball, RFB basketball, swimming, RFS football, RusAthletics, sport gymnastics, winter sports, and official history pages.
- Raw input over 200 MB is rejected by default; the first real batch must stop for review before scale-up.
- API-backed OCR, translation, and Q&A synthesis are intentionally separate commands so they cannot run accidentally.
- Source text is scrubbed for phone/email/SNILS-style PII before prompt submission and final corpora are scanned after cleaning.
- Static HTTP harvesting is resumable and can traverse already-seen pages to discover deeper source pages without duplicating rows.
- Synthesis parsing accepts the first JSON array if the model adds trailing commentary, and skips malformed model JSON so one bad response does not abort a long batch.
- Source excerpts with mojibake/extraction-noise markers are dropped during cleaning; a synthesis file with `0` written rows is invalid for scale-up and should trigger inspection/fallback before rebuilding a release.
- MinSport API/PDF harvesting supports text PDFs via `pdftotext`; scanned PDFs fall back to local Tesseract OCR (`rus+eng`).
- Federation PDFs allow up to 80 MB per document; this avoids corrupting large public rule PDFs during download.
- Federation harvest rejects links that end in `.pdf` but return HTML or another non-PDF payload.
- Federation harvest supports direct `.pdf` endpoints for stable document URLs when the source listing page is dynamic or stale.
- Лесгафта/RCSI harvesting requires per-article CC BY 4.0 metadata in `DC.Rights`; article pages without that metadata are rejected.
- `teoriya.ru` is blocked for training use unless permission is obtained because the site currently prohibits copying materials.
- Apple Silicon is sufficient for current harvest/OCR/cleaning work. NVIDIA becomes relevant at the training stage, not for corpus construction.

## Roadmap

1. Cut an immutable internal snapshot from the current `5870/5907` clean high-signal checkpoint before any SFT attempt.
2. Decide whether the first LoRA/DoRA pilot uses open-license rows only or the mixed internal corpus, while keeping internal federation rows separated.
3. Keep `teoriya.ru` blocked unless explicit reuse permission is obtained.

## Source Backlog

Priority source families:

| Priority | Source | Why it matters | Gate |
|---|---|---|---|
| S | Минспорт федеральные стандарты спортивной подготовки | Core СШОР/ВУЗ training structure, stages, loads, controls, anti-doping plans | OCR quality sampling |
| S | Минспорт ЕКП / ЕВСК / procedures | Federation operations, event financing, official calendar procedures | Text-PDF extraction works |
| S | РУСАДА education | Anti-doping rights, obligations, ADAMS, testing, sanctions | Already retained |
| S | Минздрав clinical/sport medicine docs | Sport medicine and medical supervision coverage | Gov-doc adapter |
| A | `teoriya.ru` | Methodology, biomechanics, psychology, sport science articles | Blocked: copying prohibited without permission |
| A | Лесгафта ученые записки via RCSI | Sport pedagogy, medicine, methodology | CC BY 4.0 per-article metadata gate |
| A | CyberLeninka sport corpus | Broad Russian sport-science coverage | CC/license filter per article |
| A | Russian Wikipedia sport subset | History and general sport background | CC BY-SA contamination handling |
| B | Federation rules | Sport-specific rules and procedures | Hockey, volleyball, basketball, swimming, football, athletics, gymnastics, and winter sports retained; wrestling pending URL resolution |
| B | RSL dissertations / abstracts | Deep biomechanics, medicine, methodology | Public-distribution check |
| C | PubMed Central OA sport medicine | Medicine/biomechanics evidence base | OA license filter + RU translation |
| C | OpenStax physiology | Anatomy/physiology foundations | CC BY + RU translation |

Do not mix benchmark questions into any source family. The benchmark remains held out for evaluation only.

## Output

`corpus/<output-name>/` contains `train.jsonl`, `val.jsonl`, `test.jsonl`, `MANIFEST.md`, `LICENSE-MATRIX.csv`, `hashes.json`, `stats.json`, `prep_log.txt`, and `README.md`.
