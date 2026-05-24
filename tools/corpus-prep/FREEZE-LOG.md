# Corpus Freeze Log

Committable record of frozen SFT snapshots. Hashes + counts only — no rows, no PDFs.
Large artifacts (frozen splits, raw PDFs, synth JSONL) stay local under gitignored
`corpus/`. Re-verify any bundle before training:

```bash
python3 tools/corpus-prep/freeze.py --verify-only corpus/_frozen/<snapshot>
```

---

## `lii-sport-sft-v0.1-5k-review-2026-05-24`

- **Frozen at:** 2026-05-24T13:06:48Z
- **Source checkpoint:** `corpus/lii-sport-sft-v0.1-current-agy-clean`
- **Source git:** `cb05537` (main)
- **Total:** 5,870 examples · seed `42` · splits train 5,298 / val 297 / test 275
- **Source integrity:** verified — file bytes match `hashes.json`
- **Coverage flags:** none

### Split content hashes (SHA256 of file bytes)

| Split | Count | SHA256 |
|---|---:|---|
| train | 5,298 | `2ae21a2bbb0fcaad76efc984b9439342fdec738166622355e5b9ee166fdd32d2` |
| val | 297 | `beb2fe7acf9e661f110f7a45f56586aa270aa032cf186c0d82cedee728afebcd` |
| test | 275 | `cd11d6757c24d29246e9b0a31fddacd0339c0bcf7a96c29282f4b5fe88998648` |

### License lanes

| Lane | Examples |
|---|---:|
| open-license (cc-by / cc0) | 3,760 |
| public-official (gov public-domain) | 1,006 |
| human-approved-internal | 1,104 |

### Provenance (hashed, recorded in `FREEZE.json`, not copied)

| Tree | Files | Size |
|---|---:|---|
| synth | 32 | 30.6 MB |
| raw | 178 | 262.2 MB |

### Pilot manifests cut from this snapshot

Built with `build_manifest.py`, pinned to the frozen split hashes above. Pilot splits
live under gitignored `corpus/_pilots/<name>/`.

| Manifest | Lanes | Rows | train/val/test |
|---|---|---:|---|
| `open-license-strict` | open-license | 3,760 | 3,401 / 181 / 178 |
| `open-license-public-safe` | open-license + public-official | 4,766 | 4,300 / 239 / 227 |
| `mixed-internal` | all lanes | 5,870 | 5,298 / 297 / 275 |

**Open decision:** whether `public-official` (gov public-domain texts) belongs in the
publicly-released open lane. `open-license-strict` is the unambiguous public floor;
`mixed-internal` is the internal max-lift set. Pilot compares base vs open vs mixed.
