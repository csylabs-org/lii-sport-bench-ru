#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from corpus_prep.harvest import (
    harvest_cyberleninka_articles,
    harvest_federation_rules,
    harvest_http_static,
    harvest_official_history_static,
    harvest_pdf_documents,
    harvest_rcsi_journal,
    plan_harvest,
    seed_demo_raw_batch,
)
from corpus_prep.registry import load_sources


def main() -> None:
    parser = argparse.ArgumentParser(description="Harvest corpus sources. Default mode is offline-safe.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--sources", type=Path, default=Path(__file__).with_name("sources.yaml"))
    parser.add_argument("--seed-demo", action="store_true", help="write a tiny non-bench raw batch for pipeline validation")
    parser.add_argument("--include-human-approval", action="store_true")
    parser.add_argument("--run", action="store_true", help="execute supported harvesters instead of printing the plan")
    parser.add_argument("--source-id", action="append", default=[], help="limit to one or more source ids")
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--delay-seconds", type=float, default=0.5)
    parser.add_argument("--ignore-robots", action="store_true")
    args = parser.parse_args()

    if args.seed_demo:
        written = seed_demo_raw_batch(args.repo_root)
        print(json.dumps({"written": [str(path) for path in written]}, ensure_ascii=False, indent=2))
        return

    sources = load_sources(args.sources)
    if args.source_id:
        wanted = set(args.source_id)
        sources = [source for source in sources if source["id"] in wanted]

    if args.run:
        results = []
        for source in sources:
            if source.get("requires_human_approval") and not args.include_human_approval:
                continue
            if not source.get("license_verified"):
                continue
            if source["harvester"] == "http_static":
                rows = harvest_http_static(
                    source,
                    args.repo_root,
                    max_pages=args.max_pages,
                    delay_seconds=args.delay_seconds,
                    respect_robots=not args.ignore_robots,
                )
                results.append({"source_id": source["id"], "status": "ok", "rows": len(rows)})
                continue
            if source["harvester"] in {"pdf_extract", "gov_docs"}:
                rows = harvest_pdf_documents(
                    source,
                    args.repo_root,
                    max_documents=args.max_pages,
                    delay_seconds=args.delay_seconds,
                )
                results.append({"source_id": source["id"], "status": "ok", "rows": len(rows)})
                continue
            if source["harvester"] == "rcsi_journal":
                rows = harvest_rcsi_journal(
                    source,
                    args.repo_root,
                    max_articles=args.max_pages,
                    delay_seconds=args.delay_seconds,
                )
                results.append({"source_id": source["id"], "status": "ok", "rows": len(rows)})
                continue
            if source["harvester"] == "cyberleninka_article_list":
                rows = harvest_cyberleninka_articles(
                    source,
                    args.repo_root,
                    max_articles=args.max_pages,
                    delay_seconds=args.delay_seconds,
                )
                results.append({"source_id": source["id"], "status": "ok", "rows": len(rows)})
                continue
            if source["harvester"] == "federation_rules":
                rows = harvest_federation_rules(
                    source,
                    args.repo_root,
                    max_documents=args.max_pages,
                    delay_seconds=args.delay_seconds,
                )
                results.append({"source_id": source["id"], "status": "ok", "rows": len(rows)})
                continue
            if source["harvester"] == "official_history_static":
                rows = harvest_official_history_static(
                    source,
                    args.repo_root,
                    max_pages=args.max_pages,
                    delay_seconds=args.delay_seconds,
                )
                results.append({"source_id": source["id"], "status": "ok", "rows": len(rows)})
                continue
            else:
                results.append({"source_id": source["id"], "status": "skipped", "reason": f"unsupported harvester {source['harvester']}"})
                continue
        print(json.dumps({"mode": "run", "results": results}, ensure_ascii=False, indent=2))
        return

    plan = plan_harvest(sources, include_human_approval=args.include_human_approval)
    print(json.dumps({"mode": "plan-only", "sources": plan}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
