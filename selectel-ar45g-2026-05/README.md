# Selectel AR45G pilot — results (May 2026)

Independently-measured results from the ЛИИ × Selectel AR45G dedicated-GPU pilot. These docs are
the public, citable evidence behind Habr chapter 2 + the ЛИИ-Спорт-Gemma-4-31B-Preview model card.

Hardware: **1× NVIDIA RTX PRO 6000 Blackwell Server Edition 96 GB** · server «Young» · DC SPB-2.

| Doc | Phase | Produced by | Status |
|---|---|---|---|
| `hw-validation.md` | A | `lii-sft/infra/ar45g/{10,20,30}` → `collect_to_bench.sh` | ⬜ pending box run |
| `serving-baseline.md` | B | manual fill from per-model serving runs (template below) | ⬜ pending |
| `sft-results.md` | C | bench harness 655-Q A/B base vs Preview (template below) | ⬜ pending |
| `production-economics.md` | C.4 | `lii-sft/infra/ar45g/40_inference_soak.sh` → `collect_to_bench.sh` | ⬜ pending box run |

`hw-validation.md` + `production-economics.md` are **auto-assembled** from the private test suite
(raw logs stay in `lii-sft/infra/ar45g/out/`, gitignored). `serving-baseline.md` + `sft-results.md`
are filled by hand from the Phase B/C runs.

Method + recipe are reproducible: see `lii-sft` (private) for the DoRA recipe + scripts, and the
PRD/ROADMAP in `csylabs_vault/.../selectel-ar45g-pilot-2026-05/`.
