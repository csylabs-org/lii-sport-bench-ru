#!/usr/bin/env python3
"""Freeze a clean corpus checkpoint into an immutable, hash-verified release bundle.

The freeze is the gate before SFT: it pins an exact, reproducible training artifact
so pilots are reproducible and the license lanes can't silently drift.

What it does
------------
1. Cross-checks the source ``train/val/test`` bytes against the checkpoint's own
   ``hashes.json`` (whose ``splits.*.sha256`` are file-level SHA256s, written by
   ``corpus_prep.splits``). A mismatch means the checkpoint was edited after split —
   the freeze aborts.
2. Copies the checkpoint into ``<out>/<name>/`` and re-hashes every copied file to
   confirm the copy is byte-identical.
3. Records provenance: per-file SHA256 of the ``synth/`` generators and ``raw/`` source
   trees. These are *recorded, not copied* — large artifacts stay outside the bundle
   and outside git, but their hashes pin the lineage and make tampering evident.
4. Writes ``FREEZE.json`` (machine record) + ``FREEZE.md`` (human banner) into the bundle.
5. Sets the whole bundle read-only (``chmod a-w``) to enforce immutability.

Re-check before training:
    python3 freeze.py --verify-only corpus/_frozen/<name>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CHECKPOINT_FILES = [
    "train.jsonl",
    "val.jsonl",
    "test.jsonl",
    "manifest.json",
    "hashes.json",
    "stats.json",
    "coverage.json",
    "COVERAGE.md",
    "MANIFEST.md",
    "LICENSE-MATRIX.csv",
    "prep_log.txt",
    "README.md",
]
SPLITS = ("train", "val", "test")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_tree(root: Path) -> dict[str, Any]:
    """Per-file SHA256 of every file under ``root`` (sorted, relative paths)."""
    if not root.exists():
        return {"root": str(root), "present": False, "file_count": 0, "total_bytes": 0, "files": {}}
    files: dict[str, dict[str, Any]] = {}
    total = 0
    for path in sorted(p for p in root.rglob("*") if p.is_file() and ".DS_Store" not in p.name):
        size = path.stat().st_size
        total += size
        files[str(path.relative_to(root))] = {"sha256": file_sha256(path), "bytes": size}
    return {"root": str(root), "present": True, "file_count": len(files), "total_bytes": total, "files": files}


def git_state(repo: Path) -> dict[str, Any]:
    def run(*args: str) -> str:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout.strip()

    commit = run("rev-parse", "HEAD")
    dirty = bool(run("status", "--porcelain"))
    return {"commit": commit or None, "dirty": dirty, "branch": run("rev-parse", "--abbrev-ref", "HEAD") or None}


def make_writable(root: Path) -> None:
    for path in [root, *root.rglob("*")]:
        try:
            path.chmod(path.stat().st_mode | stat.S_IWUSR)
        except OSError:
            pass


def make_readonly(root: Path) -> None:
    drop_write = ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
    for path in sorted(root.rglob("*"), reverse=True):
        try:
            path.chmod(path.stat().st_mode & drop_write)
        except OSError:
            pass
    root.chmod(root.stat().st_mode & drop_write)


def verify_source_integrity(source: Path) -> dict[str, Any]:
    """Recompute file-level SHA256 of train/val/test and match against hashes.json."""
    hashes = json.loads((source / "hashes.json").read_text(encoding="utf-8"))
    results: dict[str, Any] = {"ok": True, "splits": {}}
    for split in SPLITS:
        expected = hashes["splits"][split]["sha256"]
        actual = file_sha256(source / f"{split}.jsonl")
        match = expected == actual
        results["ok"] &= match
        results["splits"][split] = {"expected": expected, "actual": actual, "match": match}
    return results


def freeze(source: Path, name: str, out_root: Path, provenance_dirs: list[Path], repo: Path, force: bool) -> Path:
    if not source.is_dir():
        sys.exit(f"ERROR: source checkpoint not found: {source}")
    for required in SPLITS:
        if not (source / f"{required}.jsonl").is_file():
            sys.exit(f"ERROR: source missing {required}.jsonl: {source}")

    bundle = out_root / name
    if bundle.exists():
        if not force:
            sys.exit(f"ERROR: bundle already exists (immutable): {bundle}\n  re-freeze with --force, or inspect with --verify-only")
        make_writable(bundle)
        shutil.rmtree(bundle)

    print(f"[1/6] Verifying source integrity against hashes.json ...")
    integrity = verify_source_integrity(source)
    for split, r in integrity["splits"].items():
        flag = "OK " if r["match"] else "MISMATCH"
        print(f"      {flag} {split}: {r['actual'][:16]}…")
    if not integrity["ok"]:
        sys.exit("ERROR: source train/val/test bytes do not match hashes.json — checkpoint was edited post-split. Aborting.")

    print(f"[2/6] Copying checkpoint -> {bundle}")
    bundle.mkdir(parents=True)
    copied: dict[str, dict[str, Any]] = {}
    for fname in CHECKPOINT_FILES:
        src = source / fname
        if not src.exists():
            print(f"      skip (absent): {fname}")
            continue
        dst = bundle / fname
        shutil.copy2(src, dst)
        copied[fname] = {"sha256": file_sha256(dst), "bytes": dst.stat().st_size}

    print(f"[3/6] Re-hashing copied files (copy must be byte-identical) ...")
    for fname in SPLITS:
        f = f"{fname}.jsonl"
        if copied[f]["sha256"] != integrity["splits"][fname]["actual"]:
            sys.exit(f"ERROR: copied {f} hash differs from source — copy corrupted. Aborting.")
    print(f"      OK — {len(copied)} files copied + verified")

    print(f"[4/6] Recording provenance hashes ({len(provenance_dirs)} trees, not copied) ...")
    provenance = {}
    for pdir in provenance_dirs:
        tree = hash_tree(pdir)
        provenance[pdir.name] = tree
        mb = tree["total_bytes"] / 1_048_576
        print(f"      {pdir.name}: {tree['file_count']} files, {mb:.1f} MB")

    coverage = json.loads((source / "coverage.json").read_text(encoding="utf-8"))
    stats = json.loads((source / "stats.json").read_text(encoding="utf-8"))
    hashes = json.loads((source / "hashes.json").read_text(encoding="utf-8"))

    print(f"[5/6] Writing FREEZE.json + FREEZE.md ...")
    record = {
        "snapshot_name": name,
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "source_checkpoint": str(source),
        "source_git": git_state(repo),
        "total_examples": hashes["total_examples"],
        "split_counts": {s: hashes["splits"][s]["count"] for s in SPLITS},
        "split_content_sha256": {s: hashes["splits"][s]["sha256"] for s in SPLITS},
        "split_seed": hashes.get("seed"),
        "source_integrity_verified": integrity["ok"],
        "license_lanes": coverage.get("by_license_lane"),
        "categories": coverage.get("by_category"),
        "sports": coverage.get("by_sport"),
        "undercovered_flags": coverage.get("undercovered_flags"),
        "frozen_files": copied,
        "provenance": provenance,
        "immutable": True,
        "note": "DO NOT EDIT. Train pilots from this frozen bundle only. Re-verify with `freeze.py --verify-only`.",
    }
    (bundle / "FREEZE.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (bundle / "FREEZE.md").write_text(render_freeze_md(record), encoding="utf-8")

    print(f"[6/6] Locking bundle read-only (immutable) ...")
    make_readonly(bundle)
    print(f"\nFROZEN: {bundle}")
    return bundle


def render_freeze_md(r: dict[str, Any]) -> str:
    lanes = r.get("license_lanes") or {}
    flags = r.get("undercovered_flags") or []
    lane_rows = "\n".join(f"| {k} | {v} |" for k, v in lanes.items())
    prov_rows = "\n".join(
        f"| {name} | {t['file_count']} | {t['total_bytes'] / 1_048_576:.1f} MB | {'recorded' if t['present'] else 'ABSENT'} |"
        for name, t in (r.get("provenance") or {}).items()
    )
    git = r.get("source_git") or {}
    return f"""# FROZEN SNAPSHOT — {r['snapshot_name']}

> ⛔ **IMMUTABLE.** Do not edit any file in this directory. Train pilots from this
> bundle only. Re-verify integrity before SFT: `python3 tools/corpus-prep/freeze.py
> --verify-only corpus/_frozen/{r['snapshot_name']}`

- **Frozen at:** {r['frozen_at']}
- **Source checkpoint:** `{r['source_checkpoint']}`
- **Source git:** `{git.get('commit')}` ({git.get('branch')}){' — DIRTY TREE' if git.get('dirty') else ''}
- **Total examples:** {r['total_examples']}  ·  seed `{r['split_seed']}`
- **Splits:** train {r['split_counts']['train']} / val {r['split_counts']['val']} / test {r['split_counts']['test']}
- **Source integrity verified:** {r['source_integrity_verified']}

## Split content hashes (SHA256 of file bytes)

| Split | Count | SHA256 |
|---|---:|---|
| train | {r['split_counts']['train']} | `{r['split_content_sha256']['train']}` |
| val | {r['split_counts']['val']} | `{r['split_content_sha256']['val']}` |
| test | {r['split_counts']['test']} | `{r['split_content_sha256']['test']}` |

## License lanes (drives the two pilot manifests)

| Lane | Examples |
|---|---:|
{lane_rows}

## Provenance (hashed, not copied — large artifacts stay outside git)

| Tree | Files | Size | Status |
|---|---:|---|---|
{prov_rows}

## Coverage flags

{('- ' + '\\n- '.join(flags)) if flags else '- None'}
"""


def verify_only(bundle: Path) -> int:
    record_path = bundle / "FREEZE.json"
    if not record_path.exists():
        print(f"ERROR: no FREEZE.json in {bundle}")
        return 2
    record = json.loads(record_path.read_text(encoding="utf-8"))
    ok = True
    print(f"Verifying frozen bundle: {bundle}\n  snapshot: {record['snapshot_name']}  frozen_at: {record['frozen_at']}")
    for fname, meta in record["frozen_files"].items():
        actual = file_sha256(bundle / fname)
        match = actual == meta["sha256"]
        ok &= match
        print(f"  {'OK  ' if match else 'FAIL'} {fname}")
    print("\nRESULT:", "INTACT — safe to train" if ok else "TAMPERED — do not train")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze a clean corpus checkpoint into an immutable hash-verified bundle.")
    parser.add_argument("--source", type=Path, default=Path("corpus/lii-sport-sft-v0.1-current-agy-clean"))
    parser.add_argument("--name", type=str, default=f"lii-sport-sft-v0.1-5k-review-{datetime.now().date()}")
    parser.add_argument("--out", type=Path, default=Path("corpus/_frozen"))
    parser.add_argument("--provenance", type=Path, nargs="*", default=[Path("corpus/synth"), Path("corpus/raw")])
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--force", action="store_true", help="overwrite an existing bundle of the same name")
    parser.add_argument("--verify-only", type=Path, metavar="BUNDLE", help="re-verify an existing frozen bundle and exit")
    args = parser.parse_args()

    if args.verify_only:
        return verify_only(args.verify_only)

    freeze(args.source.resolve(), args.name, args.out.resolve(), [p.resolve() for p in args.provenance], args.repo.resolve(), args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
