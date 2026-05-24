#!/usr/bin/env python3
"""Build a pilot training manifest by selecting license lanes from a FROZEN snapshot.

A manifest is a reproducible subset of the frozen corpus, pinned to the freeze it was
cut from. Two pilots run against the same frozen source so benchmark deltas are
attributable to *data composition*, not to corpus drift.

Lane derivation matches ``corpus_prep.coverage._license_lanes`` exactly:
  - ``requires_human_approval`` true        -> human-approved-internal
  - ``license_kind`` starts cc- / cc0       -> open-license
  - ``license_kind`` starts public          -> public-official
  - else                                    -> other

Examples:
  # all rows (max-lift, internal only)
  build_manifest.py --frozen corpus/_frozen/<snap> --name mixed-internal --lanes all
  # cc-only public-safe floor
  build_manifest.py --frozen corpus/_frozen/<snap> --name open-license-strict --lanes open-license
  # cc + official-public
  build_manifest.py --frozen corpus/_frozen/<snap> --name open-license-public-safe --lanes open-license public-official
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SPLITS = ("train", "val", "test")
ALL_LANES = ["open-license", "public-official", "human-approved-internal", "other"]


def lane_of(row: dict[str, Any]) -> str:
    if row.get("requires_human_approval"):
        return "human-approved-internal"
    kind = str(row.get("license_kind", ""))
    if kind.startswith(("cc-", "cc0")):
        return "open-license"
    if kind.startswith("public"):
        return "public-official"
    return "other"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def build(frozen: Path, name: str, lanes: list[str], out_root: Path) -> Path:
    freeze_record = json.loads((frozen / "FREEZE.json").read_text(encoding="utf-8"))
    allowed = set(ALL_LANES if lanes == ["all"] else lanes)

    out_dir = out_root / name
    out_dir.mkdir(parents=True, exist_ok=True)

    split_meta: dict[str, Any] = {}
    lane_totals: dict[str, int] = {lane: 0 for lane in ALL_LANES}
    grand_total = 0
    for split in SPLITS:
        rows = read_jsonl(frozen / f"{split}.jsonl")
        kept = [r for r in rows if lane_of(r) in allowed]
        for r in kept:
            lane_totals[lane_of(r)] += 1
        grand_total += len(kept)
        out_path = out_dir / f"{split}.jsonl"
        write_jsonl(out_path, kept)
        split_meta[split] = {"selected": len(kept), "from": len(rows), "sha256": file_sha256(out_path)}

    manifest = {
        "manifest_name": name,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "frozen_snapshot": freeze_record["snapshot_name"],
        "frozen_source_git": freeze_record.get("source_git", {}).get("commit"),
        "frozen_split_content_sha256": freeze_record["split_content_sha256"],
        "lanes_included": sorted(allowed),
        "total_selected": grand_total,
        "split_counts": {s: split_meta[s]["selected"] for s in SPLITS},
        "lane_breakdown": {k: v for k, v in lane_totals.items() if v},
        "splits": split_meta,
        "note": "Pilot training subset pinned to a frozen snapshot. Regenerate with build_manifest.py.",
    }
    (out_dir / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[{name}] {grand_total} rows  ({', '.join(f'{s}={split_meta[s]['selected']}' for s in SPLITS)})")
    print(f"         lanes={sorted(allowed)}  -> {out_dir}")
    print(f"         pinned to frozen: {freeze_record['snapshot_name']}")
    return out_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a pilot training manifest from a frozen corpus snapshot.")
    parser.add_argument("--frozen", type=Path, required=True, help="path to a frozen bundle (contains FREEZE.json)")
    parser.add_argument("--name", type=str, required=True)
    parser.add_argument("--lanes", nargs="+", default=["all"], help="lane names or 'all'")
    parser.add_argument("--out", type=Path, default=Path("corpus/_pilots"))
    args = parser.parse_args()
    build(args.frozen.resolve(), args.name, args.lanes, args.out.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
