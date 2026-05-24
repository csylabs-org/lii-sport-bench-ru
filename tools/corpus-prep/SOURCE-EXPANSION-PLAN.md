# History + Bench-Gap Source Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a bench-directed source expansion lane that improves Gemma 4 31B on the weakest ЛИИ-Спорт-Bench-RU buckets before SFT.

**Architecture:** Keep source families separated by license posture. CC BY / CC0 sources can feed a public dataset lane; official federation/OKR history pages stay in the human-approved/internal lane until redistribution policy is decided.

**Tech Stack:** Python stdlib harvesters, `tools/corpus-prep/sources.yaml`, Antigravity CLI `agy`, local `pdftotext`/Tesseract, existing clean/leak/PII/split gates.

**Lab-practice boundary:** Do not treat row count as the goal. Freeze immutable snapshots, preserve source/license provenance, evaluate small training pilots against held-out questions, and only then decide whether to scale. Raw PDFs and generated JSONL are working artifacts, not repository content; commit manifests and hashes, not large document payloads.

---

## Current Benchmark Motivation

Gemma 4 31B base scored `7.45` overall. Preview success target is `>=7.85`; beating DeepSeek V4 Flash needs roughly `>=8.03`.

Highest-leverage weak buckets from the 200-question pilot:

| Bucket | Gemma 4 base | Frontier mean | Corpus response |
|---|---:|---:|---|
| History (`ИС`) | 6.28 | 9.28 | Add RU sport history timelines, biographies, event summaries |
| ВУЗ | 6.65 | 9.34 | Add sport-science, textbook-style, biomechanics/methodology sources |
| СШОР | 6.37 | 8.03 | Add ФССП stages, age thresholds, loads, control norms |
| Winter sports | 5.84 | 8.07 | Add лыжные гонки, биатлон, skating/skiing rules + methodology |
| Volleyball | 7.05 | 8.99 | Section-chunk 2025 rules + add volleyball ФССП/methodology |
| Federation/regulatory (`ФР`) | 7.06 | 8.66 | Add Минспорт/ЕВСК/accreditation/judging procedures |
| Methodology (`МТ`) | 7.04 | 8.43 | Expand ФССП + CC BY sport-methodology articles |

## Source Lanes

| Lane | Source id | License posture | First target | Why |
|---|---|---|---|---|
| CC BY sport history papers | `sport-history-ccby-cyberleninka` | public-safe if page exposes CC BY | 800-1200 rows | Scaled to 943 retained rows after filtered section chunks and top-ups |
| CC BY sport methodology papers | `sport-methodology-ccby-cyberleninka` | public-safe if page exposes CC BY | 300-600 rows | Scaled to 393 retained rows across methodology, biomechanics, planning, selection, and training concepts |
| CC BY sport science papers | `sport-science-ccby-cyberleninka` | public-safe if page exposes CC BY | 1000-1500 rows | Scaled to 1197 retained rows across medicine, injuries, biomechanics, psychology, endurance, skiing, snowboard, basketball, volleyball, athletics, and wrestling |
| CC BY named-sport methodology papers | `sport-specific-ccby-cyberleninka` | public-safe if page exposes CC BY | 700-1200 rows | Scaled to 768 retained rows and cleared the `general_sport_above_50pct` flag |
| CC0 sport facts | `sport-facts-wikidata-cc0` | public-safe | 300-600 rows | Scaled to 423 retained rows; next query should be sport/event-specific |
| Official history pages | `sport-history-official-approved` | human-approved/internal | 500-1000 rows | Federation and OKR timelines, milestones, biographies |
| Winter sport rules/methodology | `winter-sports-approved` + CC BY article filters | mixed; keep separated | 500-1000 rows | Scaled to 558 retained rows after winter PDF section chunks |
| Section-chunked saved PDFs | existing federation/MinSport source ids | mixed; keep separated | 1500-3000 rows | Fastest way to scale from already saved docs |

## Task 1: Add Registry Entries

**Files:**
- Modify: `tools/corpus-prep/sources.yaml`
- Modify: `tools/corpus-prep/corpus_prep/registry.py`

- [x] Add `sport-history-ccby-cyberleninka` with `harvester=cyberleninka_article_list`, `license_kind=cc-by-article`, `license_verified=true`, `requires_human_approval=false`, categories `history`, `federation-procedures`, `methodology`.
- [x] Add `sport-facts-wikidata-cc0` with `harvester=wikidata_sparql`, `license_kind=cc0`, `license_verified=true`.
- [x] Add `sport-history-official-approved` with `harvester=official_history_static`, `license_kind=human-approved-official-history-public-doc`, `requires_human_approval=true`.
- [x] Run `python3 -m json.tool tools/corpus-prep/sources.yaml`.

## Task 2: Implement CC BY CyberLeninka History Harvester

**Files:**
- Modify: `tools/corpus-prep/corpus_prep/harvest.py`
- Modify: `tools/corpus-prep/harvest.py`
- Modify: `tools/corpus-prep/tests/test_pipeline.py`

- [x] Write a parser test that accepts a CyberLeninka article only when the page text or metadata exposes `CC BY`.
- [x] Write a parser test that rejects pages without a CC BY marker.
- [x] Implement `harvest_cyberleninka_articles(source, repo_root, max_articles, delay_seconds)`.
- [x] Store rows under `corpus/raw/sport-history-ccby-cyberleninka/harvest.jsonl`.
- [x] Set row metadata: `license_kind=cc-by-article`, `license_verified=true`, `category=history` unless source overrides.
- [x] Add PDF fallback so CyberLeninka rows use full article PDFs instead of abstract-only HTML when available.
- [x] Run `env PYTHONPYCACHEPREFIX=/private/tmp/lii-sport-pycache python3 -B -m unittest discover -s tests`.

## Task 3: First Harvest + Smoke Synthesis

**Files:**
- Write ignored raw data under `corpus/raw/sport-history-ccby-cyberleninka/`
- Write ignored synth data under `corpus/synth/agy-sport-history-ccby-cyberleninka-current.jsonl`

- [x] Harvest 17 CC BY history articles.
- [x] Inspect title, URL, char length, and license marker for every row.
- [x] Generate 3 rows/article through `agy`.
- [x] Rebuild `lii-sport-sft-v0.1-current-agy-clean`.
- [x] Confirm no bench leakage, PII, duplicate, or license drops.
- [x] Expand smoke batch to 17 PDFs / 51 rows and rebuild combined clean release at `276/276`.
- [x] Finish registered backlog at 24 PDFs / 72 rows and rebuild combined clean release at `297/297`.

## Task 4: Add Official/Internal History Lane

**Files:**
- Modify: source registry and harvester dispatch
- Write ignored raw data under `corpus/raw/sport-history-official-approved/`

- [ ] Add official pages from RusAthletics, FHR, RFS, OKR, and sport-specific federation history sections.
- [x] Require `--include-human-approval` for harvest.
- [x] Keep rows labeled internal/human-approved.
- [x] Generate smoke rows only after extraction QA.
- [x] Smoke-harvest 5 official/federation history pages -> 15 retained rows in combined clean release at `312/312`.
- [x] Improve main-content extraction before production scaling; official smoke rows now prefer `main`/`article`/content blocks and trim common navigation chrome.

## Task 4.5: Add Wikidata CC0 Fact Lane

**Files:**
- Modify: `tools/corpus-prep/corpus_prep/harvest.py`
- Modify: `tools/corpus-prep/harvest.py`
- Modify: `tools/corpus-prep/tests/test_pipeline.py`

- [x] Implement `wikidata_sparql` dispatch for `sport-facts-wikidata-cc0`.
- [x] Keep rows labeled `license_kind=cc0`, `license_verified=true`, `requires_human_approval=false`.
- [x] Smoke-harvest 16 Russian/Soviet athlete records -> 48 retained rows in combined clean release at `360/360`.
- [ ] Diversify SPARQL queries by sport, event, medal, and competition to avoid over-weighting famous athlete biography facts.

## Task 4.6: Add Winter Sport Rules Lane

**Files:**
- Modify: `tools/corpus-prep/sources.yaml`
- Modify: `tools/corpus-prep/corpus_prep/harvest.py`
- Modify: `tools/corpus-prep/corpus_prep/coverage.py`
- Modify: `tools/corpus-prep/tests/test_pipeline.py`

- [x] Add `winter-sports-approved` with stable direct PDF endpoints for biathlon, cross-country skiing, alpine skiing, figure skating, and snowboard.
- [x] Keep rows labeled `license_kind=human-approved-federation-public-doc`, `requires_human_approval=true`.
- [x] Extend sport inference for winter sports and ensure `горнолыжный спорт` maps to `alpine-skiing`.
- [x] Harvest 6 winter PDFs into ignored `corpus/raw/winter-sports-approved/documents/`.
- [x] Generate smoke rows through `agy`: 6 PDFs -> 18 retained rows.
- [x] Rebuild combined clean release at `954/954`; coverage no longer reports `winter_sports_missing`.
- [x] Section-chunk the saved winter PDFs toward 500-1000 rows before SFT: 180 chunks -> 540 new rows; winter total `558` retained rows.

## Task 4.7: Add CC BY Methodology Lane

**Files:**
- Modify: `tools/corpus-prep/sources.yaml`
- Modify: `tools/corpus-prep/corpus_prep/registry.py`
- Write ignored raw data under `corpus/raw/sport-methodology-ccby-cyberleninka/`

- [x] Add `sport-methodology-ccby-cyberleninka` with `harvester=cyberleninka_article_list`, `license_kind=cc-by-article`, `license_verified=true`, `requires_human_approval=false`.
- [x] Register 11 CC BY CyberLeninka article endpoints covering methodology, biomechanics, sport selection, planning, volleyball, skiing, and integral preparation.
- [x] Harvest 11 article records with 10 PDF full texts and 1 HTML full text saved under ignored raw documents.
- [x] Generate smoke rows through `agy`: 11 articles -> 33 rows.
- [x] Section-chunk the methodology corpus: 84 chunks -> 252 `agy` rows.
- [x] Use OpenRouter fallback for the second methodology top-up when `agy` returned empty output: 36 chunks -> 108 rows.
- [x] Rebuild combined clean release with `393` retained rows from this source.

## Task 4.8: Add CC BY Sport-Science Lane

**Files:**
- Modify: `tools/corpus-prep/sources.yaml`
- Modify: `tools/corpus-prep/corpus_prep/registry.py`
- Write ignored raw data under `corpus/raw/sport-science-ccby-cyberleninka/`

- [x] Add `sport-science-ccby-cyberleninka` with `harvester=cyberleninka_article_list`, `license_kind=cc-by-article`, `license_verified=true`, `requires_human_approval=false`.
- [x] Register 26 CC BY CyberLeninka article endpoints covering sport medicine, injury prevention, endurance, biomechanics, psychology, skiing, snowboard, basketball, volleyball, athletics, and wrestling.
- [x] Harvest 26 PDF full texts into ignored raw documents.
- [x] Filter noisy chunks before synthesis: initial pass kept 179/180 chunks; second pass kept 220/220 chunks.
- [x] Generate 537 rows through `agy` and 660 rows through OpenRouter `google/gemini-3.5-flash`.
- [x] Rebuild combined clean release with `1197` retained rows from this source.

## Task 4.9: Add Named-Sport CC BY Methodology Lane

**Files:**
- Modify: `tools/corpus-prep/sources.yaml`
- Modify: `tools/corpus-prep/corpus_prep/registry.py`
- Modify: `tools/corpus-prep/corpus_prep/harvest.py`
- Write ignored raw data under `corpus/raw/sport-specific-ccby-cyberleninka/`

- [x] Add `sport-specific-ccby-cyberleninka` with `harvester=cyberleninka_article_list`, `license_kind=cc-by-article`, `license_verified=true`, `requires_human_approval=false`.
- [x] Register 35 named-sport CC BY CyberLeninka article endpoints covering swimming, basketball, hockey, football, volleyball, athletics, gymnastics, and speed skating.
- [x] Harvest 34 verified PDF full texts into ignored raw documents.
- [x] Fix CyberLeninka sport inference to prefer title/description/URL before full text; this prevents bibliography terms from overriding the article sport.
- [x] Section-chunk the lane: 256 filtered chunks, 0 extraction-noise drops.
- [x] Generate 768 rows through OpenRouter `google/gemini-3.5-flash`.
- [x] Rebuild combined clean release with `768` retained rows from this source.

## Task 5: Production Scale Decision

**Gate:** Do not train until at least `5k-10k` clean high-signal rows exist and category/sport coverage is visibly closer to the bench distribution.

- [x] Run first bounded section-chunk scale pass over saved federation/MinSport PDFs: `64` chunks -> `192` new `agy` rows -> combined clean release at `552/552`.
- [x] Add `coverage_report.py` and produce a source/corpus coverage report by `source_id`, `sport`, `category`, `audience proxy`, and license lane.
- [x] Run second balanced section-chunk scale pass over saved federation/MinSport PDFs: `128` chunks -> `384` new `agy` rows -> combined clean release at `936/936`.
- [x] Confirm current corpus is still below SFT gate: `954` rows total, with history/СШОР/ВУЗ/methodology still under-covered; winter sports now have smoke coverage but need scale.
- [x] Scale saved winter PDFs: `180` chunks -> `540` new `agy` rows; winter total now `558` retained rows.
- [x] Scale CC BY history: `120`-chunk pool -> `111` filtered chunks after rejecting `9` noisy chunks -> `330` OpenRouter rows; sport-history source now `396` retained rows after cleaning old noisy smoke rows.
- [x] Scale CC BY methodology: 11 article records + section chunks + OpenRouter fallback top-up -> `393` retained rows.
- [x] Rebuild previous clean release at `2208/2217`; `9` source-excerpt extraction-noise rows dropped, content-balance flags were cleared, and only `below_sft_gate_5k` remained.
- [x] Confirm previous corpus was still below SFT gate: `2208` rows total. Do not train yet.
- [x] Add CC BY sport-science lane and scale it to `1197` retained rows.
- [x] Expand CC BY history to `943` retained rows and Wikidata CC0 sport facts to `423` retained rows.
- [x] Expand MinSport federal standards to `610` retained rows and RUSADA anti-doping to `387` retained rows.
- [x] Rebuild previous 5k clean release at `5102/5139`; `9` extraction-noise rows and `28` duplicates dropped.
- [x] Confirm the `5k` corpus-build gate is reached. Do not train until this checkpoint is frozen/reviewed and leakage/license/quality spot checks are signed off.
- [x] Reduce remaining `general_sport_above_50pct` coverage flag with named-sport methodology chunks: current `general` share is `2867/5870` (`48.84%`).
- [x] Rebuild current clean release at `5870/5907`; `9` extraction-noise rows and `28` duplicates dropped.
- [x] Confirm the coverage report now has no undercoverage flags.
- [ ] If the frozen `5k-10k` snapshot passes gates, run a small LoRA/DoRA pilot.

## Task 6: Freeze Snapshot + Pilot Decision

**Gate:** The current `5870/5907` clean checkpoint is enough for a first SFT signal test. Do not generate more rows until this checkpoint is frozen and evaluated.

**Files:**
- Use ignored artifact storage under `corpus/` or external object storage for large data.
- Commit only release manifests, hashes, coverage summaries, and policy notes.

- [ ] Freeze `corpus/lii-sport-sft-v0.1-current-agy-clean/` as `lii-sport-sft-v0.1-5k-review-2026-05-24`.
- [ ] Record SHA256 hashes for train/val/test, source manifests, raw harvest manifests, coverage report, and license matrix.
- [ ] Create two pilot manifests:
  - `open-license-public-safe`: CC BY / CC0 rows, with public-official inclusion decided explicitly.
  - `mixed-internal`: full clean checkpoint with human-approved/internal rows retained.
- [ ] Run the same LoRA/DoRA smoke recipe for both manifests.
- [ ] Evaluate base Gemma 4 31B vs open-license pilot vs mixed-internal pilot on held-out benchmark buckets.
- [ ] Decide next expansion:
  - expand to `10k-15k` only if target weak buckets improve
  - fix prompt/data format if no measurable lift appears
  - keep public release and internal training artifacts separated
