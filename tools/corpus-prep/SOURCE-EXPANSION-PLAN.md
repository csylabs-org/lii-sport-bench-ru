# History + Bench-Gap Source Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a bench-directed source expansion lane that improves Gemma 4 31B on the weakest ЛИИ-Спорт-Bench-RU buckets before SFT.

**Architecture:** Keep source families separated by license posture. CC BY / CC0 sources can feed a public dataset lane; official federation/OKR history pages stay in the human-approved/internal lane until redistribution policy is decided.

**Tech Stack:** Python stdlib harvesters, `tools/corpus-prep/sources.yaml`, Antigravity CLI `agy`, local `pdftotext`/Tesseract, existing clean/leak/PII/split gates.

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
| CC BY sport history papers | `sport-history-ccby-cyberleninka` | public-safe if page exposes CC BY | 300-600 rows | Expanded smoke batch retained: 24 PDFs -> 72 rows |
| CC0 sport facts | `sport-facts-wikidata-cc0` | public-safe | 300-600 rows | First smoke batch retained: 16 records -> 48 rows |
| Official history pages | `sport-history-official-approved` | human-approved/internal | 500-1000 rows | Federation and OKR timelines, milestones, biographies |
| Winter sport rules/methodology | `winter-sports-approved` + CC BY article filters | mixed; keep separated | 500-1000 rows | First smoke retained: 6 PDFs -> 18 rows; biggest sport-level gap |
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
- [ ] Section-chunk the saved winter PDFs toward 500-1000 rows before SFT.

## Task 5: Production Scale Decision

**Gate:** Do not train until at least `5k-10k` clean high-signal rows exist and category/sport coverage is visibly closer to the bench distribution.

- [x] Run first bounded section-chunk scale pass over saved federation/MinSport PDFs: `64` chunks -> `192` new `agy` rows -> combined clean release at `552/552`.
- [x] Add `coverage_report.py` and produce a source/corpus coverage report by `source_id`, `sport`, `category`, `audience proxy`, and license lane.
- [x] Run second balanced section-chunk scale pass over saved federation/MinSport PDFs: `128` chunks -> `384` new `agy` rows -> combined clean release at `936/936`.
- [x] Confirm current corpus is still below SFT gate: `954` rows total, with history/СШОР/ВУЗ/methodology still under-covered; winter sports now have smoke coverage but need scale.
- [ ] If `5k-10k` rows pass gates, freeze a first training snapshot and run a small LoRA/DoRA pilot.
