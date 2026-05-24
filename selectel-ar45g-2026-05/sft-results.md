# Selectel AR45G — SFT A/B results (Phase C)

_ЛИИ-Спорт-Gemma-4-31B-Preview (DoRA, r64/α128, 1 epoch) vs `gemma-4-31b-it` base, on the full
655-Q ЛИИ-Спорт-Bench-RU v0.1, top-3 judge ensemble. **TEMPLATE — fill from the A/B run.**_

## Headline (PRD S2 — ship gate ≥ +0.4)

| Model | Overall mean | Δ vs base |
|---|---:|---:|
| `gemma-4-31b-it` base | __FILL__ (May-18 ref 7.45) | — |
| ЛИИ-Спорт-Preview (mixed-internal) | | |
| ЛИИ-Спорт-Preview (open-license-strict) | | _secondary — informs public-dataset lane_ |

**Ship decision:** ⬜ S2 met (≥ +0.4) → ship Preview · ⬜ missed → honesty post (PRD §10).

## Per-sport delta (mixed-internal Preview vs base)

| Sport | base | Preview | Δ |
|---|---:|---:|---:|
| basketball | | | |
| volleyball | | | |
| football | | | |
| ... | | | |

## 4-dimension breakdown

| Dimension | base | Preview | Δ |
|---|---:|---:|---:|
| accuracy | | | |
| completeness | | | |
| bonus | | | |
| RU linguistic | | | |

## Lane experiment (open-strict → mixed)

How much do the official + internal lanes add over the cc-only publishable floor? Drives the
decision on whether `public-official` belongs in the public HF dataset.

| Bucket | base | open-strict | mixed | strict→mixed Δ |
|---|---:|---:|---:|---:|
| overall | | | | |
| history | | | | |
| methodology | | | | |
| rules (fed/reg) | | | | |

## Training facts (for the model card)

| | |
|---|---|
| Recipe | DoRA r64 / α128 / LR 2e-4 / 1 epoch / seq 4096 / eff-batch 16 |
| Corpus | `lii-sport-sft-v0.1-5k-review-2026-05-24` (5,870; train 5,298) |
| Wall-clock | __measured__ |
| Watt-hours | __measured (from inference + train power logs)__ |
| Hardware | 1× RTX PRO 6000 Blackwell Server Edition 96 GB (Selectel AR45G) |
