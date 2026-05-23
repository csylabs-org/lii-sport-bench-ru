from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from corpus_prep.io import read_jsonl_tree


def build_coverage_report(examples: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total_examples": len(examples),
        "by_source": _count(examples, "source_id"),
        "by_sport": _count(examples, "sport"),
        "by_category": _count(examples, "category"),
        "by_license_lane": _license_lanes(examples),
        "by_audience_proxy": _audience_proxies(examples),
        "undercovered_flags": _undercovered_flags(examples),
    }


def write_coverage_report(*, input_root: Path, output_json: Path | None = None, output_md: Path | None = None) -> dict[str, Any]:
    report = build_coverage_report(read_jsonl_tree(input_root))
    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if output_md:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(render_coverage_markdown(report), encoding="utf-8")
    return report


def render_coverage_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# ЛИИ-Спорт Corpus Coverage",
        "",
        f"- Examples: {report['total_examples']}",
        "",
        "## Source",
        *_table(report["by_source"]),
        "",
        "## Sport",
        *_table(report["by_sport"]),
        "",
        "## Category",
        *_table(report["by_category"]),
        "",
        "## License Lane",
        *_table(report["by_license_lane"]),
        "",
        "## Audience Proxy",
        *_table(report["by_audience_proxy"]),
        "",
        "## Undercovered Flags",
        *_flag_lines(report["undercovered_flags"]),
        "",
    ]
    return "\n".join(lines)


def _count(examples: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(example.get(key) or "unknown") for example in examples)
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def _license_lanes(examples: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for example in examples:
        if example.get("requires_human_approval"):
            counter["human-approved-internal"] += 1
        elif str(example.get("license_kind", "")).startswith(("cc-", "cc0")):
            counter["open-license"] += 1
        elif str(example.get("license_kind", "")).startswith("public"):
            counter["public-official"] += 1
        else:
            counter["other"] += 1
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def _audience_proxies(examples: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for example in examples:
        category = str(example.get("category") or "unknown")
        sport = str(example.get("sport") or "general")
        if category == "history":
            counter["history"] += 1
        elif category == "anti-doping":
            counter["compliance"] += 1
        elif category == "rules":
            counter["federation-regulatory"] += 1
        elif category == "methodology":
            counter["vuz-sshor-methodology"] += 1
        elif sport != "general":
            counter["sport-specific"] += 1
        else:
            counter["general"] += 1
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def _undercovered_flags(examples: list[dict[str, Any]]) -> list[str]:
    total = max(1, len(examples))
    by_sport = Counter(str(example.get("sport") or "unknown") for example in examples)
    by_category = Counter(str(example.get("category") or "unknown") for example in examples)
    flags: list[str] = []
    if total < 5_000:
        flags.append("below_sft_gate_5k")
    if by_category["history"] / total < 0.20:
        flags.append("history_below_20pct")
    if by_category["methodology"] / total < 0.25:
        flags.append("methodology_below_25pct")
    if by_sport["general"] / total > 0.50:
        flags.append("general_sport_above_50pct")
    for sport in ["biathlon", "skiing", "alpine-skiing", "snowboard", "figure-skating", "speed-skating", "skating", "winter-sports"]:
        if by_sport[sport] > 0:
            break
    else:
        flags.append("winter_sports_missing")
    return flags


def _table(counts: dict[str, int]) -> list[str]:
    return ["| Key | Examples |", "|---|---:|", *[f"| {key} | {value} |" for key, value in counts.items()]]


def _flag_lines(flags: list[str]) -> list[str]:
    if not flags:
        return ["- None"]
    return [f"- {flag}" for flag in flags]
