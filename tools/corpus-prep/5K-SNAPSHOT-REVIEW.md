# 5k Snapshot Review — ЛИИ-Спорт SFT v0.1

Date: 2026-05-24

## Snapshot

- Local ignored clean path: `corpus/lii-sport-sft-v0.1-current-agy-clean/`
- Generated examples scanned: `5907`
- Clean examples retained: `5870`
- Drops: `9` extraction-noise, `28` duplicate
- Split: `5298` train, `297` val, `275` test

## Coverage

- Undercoverage flags: none
- License lanes: `3760` open-license, `1104` human-approved/internal, `1006` public-official
- Category mix: `3004` methodology, `1381` history, `1089` rules, `387` anti-doping, `9` federation-procedures
- Sport balance: `general` is `2867/5870` (`48.84%`), below the 50% guardrail

## Structural QA

- Missing two-message examples: `0`
- Missing source fields: `0`
- Missing or unverified license fields: `0`
- Encoding marker hits in final clean files: `0`
- Short questions below 20 chars: `0`
- Short answers below 40 chars: `30`, all from atomic Wikidata fact rows
- Long answers above 2500 chars: `0`

## Decision

The corpus has crossed the 5k build gate and cleared the coverage underflags. Do not start SFT until an immutable snapshot/export location is chosen and the mixed internal vs open-license training policy is signed off.

## Best-Practice Alignment

This checkpoint is aligned with practical model-lab corpus practice: held-out benchmark data is excluded from training, source provenance is retained, license lanes are explicit, and the next step is a frozen snapshot plus measured pilot rather than blind row-count expansion.

Raw PDFs, OCR text, synthetic JSONL, and clean split artifacts should remain ignored under `corpus/` during Mac-local iteration. Before SFT, freeze the exact artifact bundle and store the large files outside git; commit only the manifest, hashes, coverage summary, and release-policy notes.

Recommended pilot decision:

1. Open-license/public-safe pilot for release optionality.
2. Mixed-internal pilot for maximum benchmark-lift measurement.
3. Expand beyond this checkpoint only after per-bucket evaluation shows signal.
