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
