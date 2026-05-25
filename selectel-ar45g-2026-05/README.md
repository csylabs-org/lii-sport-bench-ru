# Selectel AR45G pilot — results (May 2026)

Independently-measured results from the ЛИИ × Selectel AR45G dedicated-GPU pilot. These docs are
the public, citable evidence behind Habr chapter 2 + the ЛИИ-Спорт-Gemma-4-31B-Preview model card.

Hardware: **1× NVIDIA RTX PRO 6000 Blackwell Server Edition 96 GB** · server «Young» · DC SPB-2.

| Doc | Phase | Produced by | Status |
|---|---|---|---|
| `hw-validation.md` | A | Ansible `capture_gpu_baseline.yml` + `gpu_stress_validation.yml` | ✅ **done 2026-05-24** |
| `serving-baseline.md` | B | manual fill from per-model serving runs (template) | ⬜ pending |
| `sft-results.md` | C | bench harness 655-Q A/B base vs Preview (template) | ⬜ pending |
| `production-economics.md` | C.4 | Ansible `gpu_combined_soak.yml` (A.7) + inference soak, post-training | ⬜ pending |

HW validation is run via reusable Ansible playbooks in the csylabs inventory (the box is
`lii-gpu-test-01`); results fetch back to `30-infrastructure/ansible/_baselines/` (private) and
are curated here. `serving-baseline.md` + `sft-results.md` are filled by hand from the Phase B/C runs.

Method + recipe are reproducible: see `lii-sft` (private) for the DoRA SFT recipe, and the
PRD/ROADMAP in `csylabs_vault/.../selectel-ar45g-pilot-2026-05/`.
