from __future__ import annotations

import hashlib
import html.parser
import json
import re
import subprocess
import time
import urllib.parse
import urllib.request
import urllib.robotparser
import tempfile
from pathlib import Path
from typing import Any, Callable


MAX_DOCUMENT_BYTES = 80_000_000


DEMO_EXAMPLES: list[dict[str, Any]] = [
    {
        "id": "demo-rusada-001",
        "source_id": "rusada-edu",
        "license_kind": "public-ru-state-agency",
        "license_verified": True,
        "requires_human_approval": False,
        "sport": "general",
        "category": "anti-doping",
        "text": "Антидопинговая безопасность начинается с проверки препарата до его применения. "
        "Спортсмен обязан сверять лекарственные средства с актуальными перечнями и консультироваться "
        "со спортивным врачом команды. " * 5,
        "messages": [
            {"role": "user", "content": "Как спортсмену проверить лекарство перед стартом?"},
            {
                "role": "assistant",
                "content": "Сначала сверить препарат с актуальными материалами РУСАДА, затем уточнить статус у врача команды и сохранить подтверждение проверки.",
            },
        ],
    },
    {
        "id": "demo-minsport-001",
        "source_id": "minsport-fed-standards",
        "license_kind": "public-domain",
        "license_verified": True,
        "requires_human_approval": False,
        "sport": "general",
        "category": "methodology",
        "text": "Федеральные стандарты спортивной подготовки задают требования к этапам подготовки, "
        "объему тренировочной нагрузки, медицинскому сопровождению и контрольным нормативам. " * 6,
        "messages": [
            {"role": "user", "content": "Зачем нужны федеральные стандарты спортивной подготовки?"},
            {
                "role": "assistant",
                "content": "Они фиксируют требования к этапам подготовки, нагрузке, медконтролю и нормативам, чтобы СШОР и федерации работали в единой методической рамке.",
            },
        ],
    },
    {
        "id": "demo-openstax-001",
        "source_id": "openstax-physiology",
        "license_kind": "cc-by",
        "license_verified": True,
        "requires_human_approval": False,
        "sport": "general",
        "category": "biomechanics",
        "text": "Мышечное сокращение зависит от взаимодействия актина и миозина, нервного импульса "
        "и доступности энергии. В спортивной биомеханике это используется для объяснения силы, "
        "скорости и утомления при движении. " * 5,
        "messages": [
            {"role": "user", "content": "Как физиология мышц связана с биомеханикой движения?"},
            {
                "role": "assistant",
                "content": "Механика движения опирается на работу мышечных волокон: нервный сигнал, взаимодействие актина и миозина и энергетическое обеспечение определяют силу и скорость.",
            },
        ],
    },
]


def seed_demo_raw_batch(repo_root: Path) -> list[Path]:
    written: list[Path] = []
    for example in DEMO_EXAMPLES:
        source_dir = repo_root / "corpus" / "raw" / str(example["source_id"])
        source_dir.mkdir(parents=True, exist_ok=True)
        path = source_dir / "demo.jsonl"
        path.write_text(json.dumps(example, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return written


def plan_harvest(sources: list[dict[str, Any]], *, include_human_approval: bool = False) -> list[dict[str, Any]]:
    planned = []
    for source in sources:
        if source.get("requires_human_approval") and not include_human_approval:
            continue
        planned.append(
            {
                "source_id": source["id"],
                "endpoint": source["endpoint"],
                "harvester": source["harvester"],
                "license_kind": source["license_kind"],
            }
        )
    return planned


def harvest_http_static(
    source: dict[str, Any],
    repo_root: Path,
    *,
    max_pages: int = 25,
    delay_seconds: float = 0.5,
    respect_robots: bool = True,
) -> list[dict[str, Any]]:
    if source.get("requires_human_approval"):
        raise ValueError(f"source {source['id']} requires human approval")
    if not source.get("license_verified"):
        raise ValueError(f"source {source['id']} license is not verified")

    start_url = str(source["endpoint"])
    raw_dir = repo_root / "corpus" / "raw" / str(source["id"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path = raw_dir / "harvest.jsonl"
    seen = _load_seen_urls(output_path)

    queue = [start_url]
    rows: list[dict[str, Any]] = []
    parser = _Robots(start_url, enabled=respect_robots)
    traversed: set[str] = set()

    while queue and len(rows) < max_pages:
        url = queue.pop(0)
        normalized_url = _normalize_url(url)
        if normalized_url in traversed:
            continue
        traversed.add(normalized_url)
        if not parser.can_fetch(normalized_url):
            seen.add(normalized_url)
            continue

        fetched = _fetch_text(normalized_url)
        if fetched is None:
            seen.add(normalized_url)
            continue

        content_type, body = fetched
        text, links = _html_to_text_and_links(body, normalized_url)
        if normalized_url not in seen:
            seen.add(normalized_url)
            row = {
                "id": _row_id(str(source["id"]), normalized_url),
                "source_id": source["id"],
                "url": normalized_url,
                "license_kind": source["license_kind"],
                "license_verified": source["license_verified"],
                "requires_human_approval": bool(source.get("requires_human_approval", False)),
                "sport": "general",
                "category": _first_category(source),
                "content_type": content_type,
                "text": text,
            }
            rows.append(row)

        for link in links:
            if len(queue) + len(rows) >= max_pages:
                break
            normalized_link = _normalize_url(link)
            if _same_origin(start_url, link) and normalized_link not in traversed:
                queue.append(link)

        if delay_seconds:
            time.sleep(delay_seconds)

    if rows:
        with output_path.open("a", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return rows


def harvest_pdf_documents(
    source: dict[str, Any],
    repo_root: Path,
    *,
    max_documents: int = 10,
    delay_seconds: float = 0.5,
    extract_pdf_text: Callable[[Path], str] | None = None,
) -> list[dict[str, Any]]:
    if source.get("requires_human_approval"):
        raise ValueError(f"source {source['id']} requires human approval")
    if not source.get("license_verified"):
        raise ValueError(f"source {source['id']} license is not verified")

    extract = extract_pdf_text or extract_pdf_text_with_ocr
    start_url = str(source["endpoint"])
    if _is_minsport_source(source):
        document_urls = _minsport_document_urls(source, max_documents=max_documents)
    else:
        fetched = _fetch_text(start_url)
        if fetched is None:
            return []

        _content_type, body = fetched
        _text, links = _html_to_text_and_links(body, start_url)
        document_urls = _document_links(links, start_url)[:max_documents]

    raw_dir = repo_root / "corpus" / "raw" / str(source["id"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path = raw_dir / "harvest.jsonl"
    seen = _load_seen_urls(output_path)
    docs_dir = raw_dir / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for url in document_urls:
        normalized_url = _normalize_url(url)
        if normalized_url in seen:
            continue
        pdf_bytes = _fetch_binary(normalized_url)
        seen.add(normalized_url)
        if not pdf_bytes or not _looks_like_pdf(pdf_bytes):
            continue
        document_path = docs_dir / f"{_row_id(str(source['id']), normalized_url)}.pdf"
        document_path.write_bytes(pdf_bytes)
        try:
            text = re.sub(r"\s+", " ", extract(document_path)).strip()
        except Exception:
            continue
        if not text:
            continue
        rows.append(
            {
                "id": _row_id(str(source["id"]), normalized_url),
                "source_id": source["id"],
                "url": normalized_url,
                "license_kind": source["license_kind"],
                "license_verified": source["license_verified"],
                "requires_human_approval": bool(source.get("requires_human_approval", False)),
                "sport": "general",
                "category": _first_category(source),
                "content_type": "application/pdf",
                "text": text,
            }
        )
        if delay_seconds:
            time.sleep(delay_seconds)

    if rows:
        with output_path.open("a", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return rows


def harvest_rcsi_journal(
    source: dict[str, Any],
    repo_root: Path,
    *,
    max_articles: int = 10,
    delay_seconds: float = 0.5,
) -> list[dict[str, Any]]:
    if source.get("requires_human_approval"):
        raise ValueError(f"source {source['id']} requires human approval")

    start_url = str(source["endpoint"])
    fetched = _fetch_text(start_url)
    if fetched is None:
        return []

    _content_type, body = fetched
    article_urls = rcsi_article_links_from_issue_html(body, start_url)

    raw_dir = repo_root / "corpus" / "raw" / str(source["id"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path = raw_dir / "harvest.jsonl"
    seen = _load_seen_urls(output_path)
    docs_dir = raw_dir / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for url in article_urls:
        normalized_url = _normalize_url(url)
        if normalized_url in seen:
            continue
        article = _fetch_text(normalized_url)
        seen.add(normalized_url)
        if article is None:
            continue
        _article_content_type, article_body = article
        row = rcsi_article_row_from_html(source, normalized_url, article_body)
        if row is None:
            continue
        rows.append(row)
        if len(rows) >= max_articles:
            break
        if delay_seconds:
            time.sleep(delay_seconds)

    if rows:
        with output_path.open("a", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return rows


def harvest_cyberleninka_articles(
    source: dict[str, Any],
    repo_root: Path,
    *,
    max_articles: int = 10,
    delay_seconds: float = 0.5,
) -> list[dict[str, Any]]:
    if source.get("requires_human_approval"):
        raise ValueError(f"source {source['id']} requires human approval")
    if not source.get("license_verified"):
        raise ValueError(f"source {source['id']} license is not verified")

    endpoints = source.get("endpoint")
    article_urls = endpoints if isinstance(endpoints, list) else [str(endpoints)]
    raw_dir = repo_root / "corpus" / "raw" / str(source["id"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path = raw_dir / "harvest.jsonl"
    seen = _load_seen_urls(output_path)
    docs_dir = raw_dir / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for url in article_urls:
        if len(rows) >= max_articles:
            break
        normalized_url = _normalize_url(str(url))
        if normalized_url in seen:
            continue
        article = _fetch_text(normalized_url)
        seen.add(normalized_url)
        if article is None:
            continue
        _content_type, body = article
        row = cyberleninka_article_row_from_html(source, normalized_url, body)
        if row is None:
            continue
        pdf_url = _cyberleninka_pdf_url(normalized_url)
        pdf_bytes = _fetch_binary(pdf_url)
        if pdf_bytes and _looks_like_pdf(pdf_bytes):
            document_path = docs_dir / f"{_row_id(str(source['id']), normalized_url)}.pdf"
            document_path.write_bytes(pdf_bytes)
            pdf_text = re.sub(r"\s+", " ", extract_pdf_text_with_ocr(document_path)).strip()
            if len(pdf_text) > len(row["text"]):
                row["text"] = re.sub(r"\s+", " ", f"{row.get('source_title', '')}\n{pdf_text}").strip()[:120_000]
                row["content_type"] = "application/pdf"
                row["pdf_url"] = pdf_url
        rows.append(row)
        if delay_seconds:
            time.sleep(delay_seconds)

    if rows:
        with output_path.open("a", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return rows


def harvest_official_history_static(
    source: dict[str, Any],
    repo_root: Path,
    *,
    max_pages: int = 10,
    delay_seconds: float = 0.5,
    refresh: bool = False,
) -> list[dict[str, Any]]:
    if not source.get("license_verified"):
        raise ValueError(f"source {source['id']} license is not verified")
    if not source.get("requires_human_approval"):
        raise ValueError(f"source {source['id']} must be marked for human approval")

    endpoints = source.get("endpoint")
    urls = endpoints if isinstance(endpoints, list) else [str(endpoints)]
    raw_dir = repo_root / "corpus" / "raw" / str(source["id"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path = raw_dir / "harvest.jsonl"
    seen = set() if refresh else _load_seen_urls(output_path)

    rows: list[dict[str, Any]] = []
    for url in urls:
        if len(rows) >= max_pages:
            break
        normalized_url = _normalize_url(str(url))
        if normalized_url in seen:
            continue
        fetched = _fetch_text(normalized_url)
        seen.add(normalized_url)
        if fetched is None:
            continue
        content_type, body = fetched
        text = _official_history_text_from_html(body, normalized_url)
        title = _first_meta_property(body, "og:title") or _html_title(body) or normalized_url
        text = re.sub(r"\s+", " ", "\n".join(part for part in [title, text] if part)).strip()
        if len(text) < 200:
            continue
        rows.append(
            {
                "id": _row_id(str(source["id"]), normalized_url),
                "source_id": source["id"],
                "source_title": title,
                "url": normalized_url,
                "license_kind": source["license_kind"],
                "license_verified": source["license_verified"],
                "requires_human_approval": True,
                "approved_by": "Daniel Ivanov",
                "approval_note": source.get("approval_note", "User approved official history pages for working corpus"),
                "sport": _infer_sport(f"{title} {text}"),
                "category": _first_category(source),
                "content_type": content_type,
                "text": text[:120_000],
            }
        )
        if delay_seconds:
            time.sleep(delay_seconds)

    if rows:
        mode = "w" if refresh else "a"
        with output_path.open(mode, encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return rows


def harvest_wikidata_sport_facts(
    source: dict[str, Any],
    repo_root: Path,
    *,
    max_records: int = 25,
) -> list[dict[str, Any]]:
    if source.get("requires_human_approval"):
        raise ValueError(f"source {source['id']} requires human approval")
    if source.get("license_kind") != "cc0" or not source.get("license_verified"):
        raise ValueError(f"source {source['id']} must be verified CC0")

    raw_dir = repo_root / "corpus" / "raw" / str(source["id"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path = raw_dir / "harvest.jsonl"
    seen = _load_seen_urls(output_path)

    query = _wikidata_sport_facts_query(max_records=max_records)
    endpoint = str(source["endpoint"])
    request_url = endpoint + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    data = _fetch_json(request_url)
    if data is None:
        return []

    rows: list[dict[str, Any]] = []
    for binding in data.get("results", {}).get("bindings", []):
        row = _wikidata_sport_fact_row(source, binding)
        if row is None:
            continue
        if row["url"] in seen:
            continue
        seen.add(row["url"])
        rows.append(row)

    if rows:
        with output_path.open("a", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return rows


def harvest_federation_rules(
    source: dict[str, Any],
    repo_root: Path,
    *,
    max_documents: int = 10,
    delay_seconds: float = 0.5,
    extract_pdf_text: Callable[[Path], str] | None = None,
) -> list[dict[str, Any]]:
    if not source.get("license_verified"):
        raise ValueError(f"source {source['id']} license is not verified")

    extract = extract_pdf_text or extract_pdf_text_with_ocr
    endpoints = source.get("endpoint")
    start_urls = endpoints if isinstance(endpoints, list) else [str(endpoints)]
    raw_dir = repo_root / "corpus" / "raw" / str(source["id"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path = raw_dir / "harvest.jsonl"
    seen = _load_seen_urls(output_path)
    docs_dir = raw_dir / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    candidates: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for start_url in start_urls:
        if source.get("direct_document") or urllib.parse.urlparse(str(start_url)).path.casefold().endswith(".pdf"):
            normalized = _normalize_url(str(start_url))
            if normalized not in seen and normalized not in seen_urls:
                seen_urls.add(normalized)
                candidates.append({"url": normalized, "title": _source_endpoint_title(source, normalized)})
            if len(candidates) >= max_documents:
                break
            continue
        fetched = _fetch_text(str(start_url))
        if fetched is None:
            continue
        _content_type, body = fetched
        for document in federation_document_links_from_html(body, str(start_url)):
            normalized = _normalize_url(document["url"])
            if normalized in seen:
                continue
            if normalized in seen_urls:
                continue
            seen_urls.add(normalized)
            candidates.append({"url": normalized, "title": document["title"]})
            if len(candidates) >= max_documents:
                break
        if len(candidates) >= max_documents:
            break

    rows: list[dict[str, Any]] = []
    for document in candidates:
        normalized_url = _normalize_url(document["url"])
        pdf_bytes = _fetch_binary(normalized_url)
        seen.add(normalized_url)
        if not pdf_bytes or not _looks_like_pdf(pdf_bytes):
            continue
        document_path = docs_dir / f"{_row_id(str(source['id']), normalized_url)}.pdf"
        document_path.write_bytes(pdf_bytes)
        try:
            text = re.sub(r"\s+", " ", extract(document_path)).strip()
        except Exception:
            continue
        if not text:
            continue
        title = document.get("title") or Path(urllib.parse.urlparse(normalized_url).path).name
        rows.append(
            {
                "id": _row_id(str(source["id"]), normalized_url),
                "source_id": source["id"],
                "source_title": title,
                "url": normalized_url,
                "license_kind": source["license_kind"],
                "license_verified": source["license_verified"],
                "requires_human_approval": bool(source.get("requires_human_approval", False)),
                "approved_by": "Daniel Ivanov",
                "approval_note": "User approved federation and MinSport documents for working corpus on 2026-05-23",
                "sport": _infer_sport(f"{title} {normalized_url}"),
                "category": _first_category(source),
                "content_type": "application/pdf",
                "text": text,
            }
        )
        if delay_seconds:
            time.sleep(delay_seconds)

    if rows:
        with output_path.open("a", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return rows


def rcsi_article_links_from_issue_html(body: str, base_url: str) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    for href in re.findall(r"""href=["']([^"']*/1994-4683/article/view/\d+(?:/[^"']*)?)["']""", body):
        url = urllib.parse.urljoin(base_url, href)
        match = re.search(r"(/1994-4683/article/view/\d+)", urllib.parse.urlparse(url).path)
        if not match:
            continue
        canonical = f"https://journals.rcsi.science{match.group(1)}"
        if canonical not in seen:
            seen.add(canonical)
            links.append(canonical)
    return links


def rcsi_article_row_from_html(source: dict[str, Any], url: str, body: str) -> dict[str, Any] | None:
    rights = _meta_contents(body, "DC.Rights")
    license_url = next((value for value in rights if value.rstrip("/") == "https://creativecommons.org/licenses/by/4.0"), None)
    if not license_url:
        return None

    title = _first_meta_content(body, "DC.Title", lang="ru") or _first_meta_content(body, "title", lang="ru")
    abstract = _first_meta_content(body, "DC.Abstract", lang="ru") or _first_meta_content(body, "abstract", lang="ru")
    subjects = _meta_contents(body, "DC.Subject", lang="ru") or _split_keywords(_first_meta_content(body, "keywords", lang="ru"))
    if not title or not abstract:
        return None

    text_parts = [title.strip(), "Аннотация:", abstract.strip()]
    if subjects:
        text_parts.extend(["Ключевые слова:", ", ".join(subject.strip() for subject in subjects if subject.strip())])
    text = re.sub(r"\s+", " ", "\n".join(text_parts)).strip()
    if len(text) < 200:
        return None

    return {
        "id": _row_id(str(source["id"]), url),
        "source_id": source["id"],
        "url": url,
        "license_kind": "cc-by-4.0",
        "license_url": license_url,
        "license_verified": True,
        "requires_human_approval": bool(source.get("requires_human_approval", False)),
        "sport": "general",
        "category": _first_category(source),
        "content_type": "text/html",
        "text": text,
    }


def cyberleninka_article_row_from_html(source: dict[str, Any], url: str, body: str) -> dict[str, Any] | None:
    if not _has_cc_by_marker(body):
        return None

    title = (
        _first_meta_content(body, "citation_title")
        or _first_meta_property(body, "og:title")
        or _first_meta_content(body, "description")
        or _html_title(body)
    )
    description = _first_meta_content(body, "description") or ""
    page_text, _links = _html_to_text_and_links(body, url)
    text_parts = [part.strip() for part in [title, description, page_text] if part and part.strip()]
    text = re.sub(r"\s+", " ", "\n".join(text_parts)).strip()
    text = _trim_cyberleninka_boilerplate(text)
    if len(text) < 200:
        return None

    return {
        "id": _row_id(str(source["id"]), url),
        "source_id": source["id"],
        "source_title": title or url,
        "url": url,
        "license_kind": source.get("license_kind", "cc-by-article"),
        "license_url": _cc_by_license_url(body) or "CC BY",
        "license_verified": True,
        "requires_human_approval": bool(source.get("requires_human_approval", False)),
        "sport": _infer_sport(text),
        "category": _first_category(source),
        "content_type": "text/html",
        "text": text[:120_000],
    }


def _cyberleninka_pdf_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.rstrip("/")
    if path.endswith("/pdf"):
        return _normalize_url(url)
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, f"{path}/pdf", "", parsed.query, ""))


def federation_document_links_from_html(body: str, base_url: str) -> list[dict[str, str]]:
    parser = _FederationDocumentParser(base_url)
    parser.feed(body)

    documents: list[dict[str, str]] = []
    seen: set[str] = set()
    for document in parser.documents:
        normalized = _normalize_url(document["url"])
        if normalized in seen:
            continue
        if not _same_origin(base_url, normalized):
            continue
        if not urllib.parse.urlparse(normalized).path.casefold().endswith(".pdf"):
            continue
        title = re.sub(r"\s+", " ", document.get("title", "")).strip()
        documents.append({"title": title or Path(urllib.parse.urlparse(normalized).path).name, "url": normalized})
        seen.add(normalized)
    return documents


def minsport_document_links_from_api(data: dict[str, Any], *, title_keywords: list[str]) -> list[str]:
    keywords = [keyword.casefold() for keyword in title_keywords]
    links: list[str] = []
    for item in data.get("data", []):
        attributes = item.get("attributes", {}) if isinstance(item, dict) else {}
        title = str(attributes.get("title", "")).casefold()
        if keywords and not all(keyword in title for keyword in keywords):
            continue
        file_attributes = (((attributes.get("file") or {}).get("data") or {}).get("attributes") or {})
        url = str(file_attributes.get("url") or "")
        if not url:
            continue
        normalized = url.replace("http://", "https://", 1)
        if urllib.parse.urlparse(normalized).path.casefold().endswith(".pdf"):
            links.append(normalized)
    return links


def _wikidata_sport_facts_query(*, max_records: int) -> str:
    limit = max(1, min(max_records, 200))
    return f"""
SELECT ?item ?itemLabel ?sportLabel ?countryLabel ?dob ?article WHERE {{
  ?item wdt:P106 wd:Q2066131;
        wdt:P27 ?country.
  VALUES ?country {{ wd:Q159 wd:Q15180 }}
  OPTIONAL {{ ?item wdt:P641 ?sport. }}
  OPTIONAL {{ ?item wdt:P569 ?dob. }}
  OPTIONAL {{
    ?article schema:about ?item;
             schema:isPartOf <https://ru.wikipedia.org/>.
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ru,en". }}
}}
LIMIT {limit}
""".strip()


def _wikidata_sport_fact_row(source: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any] | None:
    item_url = _binding_value(binding, "item")
    item_label = _binding_value(binding, "itemLabel")
    if not item_url or not item_label:
        return None

    sport = _binding_value(binding, "sportLabel") or "спорт не указан"
    country = _binding_value(binding, "countryLabel") or "страна не указана"
    dob = _binding_value(binding, "dob")
    birth_year = dob[:4] if dob and re.match(r"\d{4}", dob) else "год рождения не указан"
    article = _binding_value(binding, "article")
    facts = [
        f"Объект Wikidata: {item_label}.",
        f"Тип факта: российский или советский спортсмен.",
        f"Вид спорта: {sport}.",
        f"Страна/гражданство в записи: {country}.",
        f"Год рождения: {birth_year}.",
    ]
    if article:
        facts.append(f"Русская энциклопедическая статья: {article}.")
    facts.append("Лицензия фактических данных Wikidata: CC0; строка пригодна для фактологического sport-history корпуса.")
    text = " ".join(facts)
    if len(text) < 200:
        text = f"{text} " + " ".join(facts)

    return {
        "id": _row_id(str(source["id"]), item_url),
        "source_id": source["id"],
        "source_title": item_label,
        "url": item_url,
        "license_kind": "cc0",
        "license_url": "https://www.wikidata.org/wiki/Wikidata:Licensing",
        "license_verified": True,
        "requires_human_approval": False,
        "sport": _infer_sport(sport),
        "category": _first_category(source),
        "content_type": "application/sparql-results+json",
        "text": text,
    }


def _binding_value(binding: dict[str, Any], name: str) -> str | None:
    value = binding.get(name, {})
    if isinstance(value, dict) and value.get("value"):
        return str(value["value"])
    return None


def extract_pdf_text_with_ocr(
    path: Path,
    *,
    min_text_chars: int = 200,
    max_ocr_pages: int = 6,
    pdftotext: Callable[[Path], str] = None,
    ocr: Callable[..., str] = None,
) -> str:
    text_extractor = pdftotext or pdftotext_extract
    ocr_extractor = ocr or tesseract_ocr_extract
    text = text_extractor(path).strip()
    if len(text) >= min_text_chars:
        return text
    ocr_text = ocr_extractor(path, max_pages=max_ocr_pages).strip()
    return ocr_text or text


extract_pdf_text = extract_pdf_text_with_ocr


def pdftotext_extract(path: Path) -> str:
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception:
        return ""
    return result.stdout


def tesseract_ocr_extract(path: Path, *, max_pages: int = 6, lang: str = "rus+eng") -> str:
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "page"
        subprocess.run(
            ["pdftoppm", "-png", "-r", "220", "-f", "1", "-l", str(max_pages), str(path), str(prefix)],
            check=True,
            capture_output=True,
            timeout=90,
        )
        texts: list[str] = []
        for image_path in sorted(Path(tmp).glob("page-*.png")):
            result = subprocess.run(
                ["tesseract", str(image_path), "stdout", "-l", lang, "--psm", "6"],
                check=True,
                capture_output=True,
                text=True,
                timeout=90,
            )
            if result.stdout.strip():
                texts.append(result.stdout.strip())
        return "\n\n".join(texts)


def _load_seen_urls(path: Path) -> set[str]:
    seen: set[str] = set()
    if not path.exists():
        return seen
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("url"):
                seen.add(_normalize_url(str(row["url"])))
    return seen


def _fetch_text(url: str) -> tuple[str, str] | None:
    request_url = _quote_url(url)
    request = urllib.request.Request(request_url, headers={"User-Agent": "lii-sport-corpus-prep/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                return None
            charset = response.headers.get_content_charset() or "utf-8"
            body = response.read(2_000_000).decode(charset, errors="replace")
            return content_type, body
    except Exception:
        return None


def _fetch_binary(url: str, *, max_bytes: int = MAX_DOCUMENT_BYTES) -> bytes | None:
    request_url = _quote_url(url)
    request = urllib.request.Request(request_url, headers={"User-Agent": "lii-sport-corpus-prep/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read(max_bytes + 1)
            return data if len(data) <= max_bytes else None
    except Exception:
        return _curl_fetch(request_url, binary=True, max_bytes=max_bytes)


def _fetch_json(url: str) -> dict[str, Any] | None:
    request_url = _quote_url(url)
    request = urllib.request.Request(request_url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        fetched = _curl_fetch(request_url, binary=False)
        if fetched:
            try:
                return json.loads(fetched.decode("utf-8"))
            except json.JSONDecodeError:
                return None
        return None


def _curl_fetch(url: str, *, binary: bool, max_bytes: int = MAX_DOCUMENT_BYTES) -> bytes | None:
    try:
        result = subprocess.run(
            ["curl", "-L", "--max-time", "30", "-A", "Mozilla/5.0", url],
            check=True,
            capture_output=True,
            timeout=35,
        )
    except Exception:
        return None
    if binary:
        return result.stdout if len(result.stdout) <= max_bytes else None
    return result.stdout


def _html_to_text_and_links(body: str, base_url: str) -> tuple[str, list[str]]:
    parser = _TextAndLinkParser(base_url)
    parser.feed(body)
    text = re.sub(r"\s+", " ", " ".join(parser.text_parts)).strip()
    return text, parser.links


def _official_history_text_from_html(body: str, base_url: str) -> str:
    full_text, _links = _html_to_text_and_links(body, base_url)
    candidates = [full_text]
    candidates.extend(_readable_html_block_texts(body, base_url))
    best = max(candidates, key=_history_text_score, default=full_text)
    return _trim_official_history_boilerplate(_dedupe_adjacent_phrases(best))


def _readable_html_block_texts(body: str, base_url: str) -> list[str]:
    blocks: list[str] = []
    for tag in ("main", "article"):
        blocks.extend(re.findall(fr"<{tag}\b[^>]*>(.*?)</{tag}>", body, flags=re.IGNORECASE | re.DOTALL))

    keyword_pattern = r"(?:content|article|news|history|text|body|page|detail|post)"
    block_pattern = (
        r"<(div|section)\b(?=[^>]*(?:class|id)=['\"][^'\"]*"
        + keyword_pattern
        + r"[^'\"]*['\"])[^>]*>(.*?)</\1>"
    )
    blocks.extend(match.group(2) for match in re.finditer(block_pattern, body, flags=re.IGNORECASE | re.DOTALL))

    texts: list[str] = []
    for block in blocks:
        text, _links = _html_to_text_and_links(block, base_url)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) >= 200:
            texts.append(text)
    return texts


def _history_text_score(text: str) -> int:
    lowered = text.casefold()
    score = len(text)
    score += 250 * len(re.findall(r"\b(?:18|19|20)\d{2}\b", text))
    score += 300 * sum(word in lowered for word in ["история", "спорт", "федерац", "сборн", "олимп"])
    score -= 500 * sum(word in lowered for word in ["переключиться", "контакты", "закупки", "меню", "личный кабинет"])
    return score


def _dedupe_adjacent_phrases(text: str) -> str:
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\s{2,}", text) if part.strip()]
    deduped: list[str] = []
    previous = ""
    for part in parts:
        normalized = re.sub(r"\W+", "", part.casefold())
        if normalized and normalized == previous:
            continue
        deduped.append(part)
        previous = normalized
    return re.sub(r"\s+", " ", " ".join(deduped)).strip()


def _trim_official_history_boilerplate(text: str, *, max_chars: int = 8_000) -> str:
    early = text[:2_000].casefold()
    noise_terms = ["переключиться", "личный кабинет", "закупки", "контакты", "назад"]
    if len(text) <= max_chars and not any(term in early for term in noise_terms):
        return text

    starts = {0}
    for match in re.finditer(r"\b(?:18|19|20)\d{2}\b|История\s+[А-Яа-яЁёA-Za-z]", text):
        if match.start() < 250:
            continue
        starts.add(max(0, match.start() - 80))

    windows = [text[start : start + max_chars].strip() for start in sorted(starts)]
    return _remove_official_noise_phrases(max(windows, key=_history_window_score, default=text[:max_chars]).strip())


def _remove_official_noise_phrases(text: str) -> str:
    noise_patterns = [
        r"Переключиться на английскую версию сайта\.?",
        r"©\s*2004\s*-\s*2026[^.]+\.?",
        r"Задать вопрос",
        r"Горячая линия",
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def _history_window_score(text: str) -> int:
    lowered = text.casefold()
    score = 900 * len(re.findall(r"\b(?:18|19|20)\d{2}\b", text))
    score += 500 * sum(word in lowered for word in ["история", "спорт", "федерац", "сборн", "олимп"])
    score -= 900 * sum(word in lowered for word in ["переключиться", "личный кабинет", "закупки", "контакты", "назад"])
    score += min(len(text), 2_000)
    return score


def _document_links(links: list[str], start_url: str) -> list[str]:
    seen: set[str] = set()
    documents: list[str] = []
    for link in links:
        normalized = _normalize_url(link)
        if normalized in seen:
            continue
        if not _same_origin(start_url, normalized):
            continue
        path = urllib.parse.urlparse(normalized).path.casefold()
        if path.endswith(".pdf"):
            documents.append(normalized)
            seen.add(normalized)
    return documents


def _meta_contents(body: str, name: str, *, lang: str | None = None) -> list[str]:
    values: list[str] = []
    for tag in re.findall(r"<meta\b[^>]*>", body, flags=re.IGNORECASE):
        attrs = _tag_attrs(tag)
        if attrs.get("name") != name:
            continue
        if lang and attrs.get("lang") != lang and attrs.get("xml:lang") != lang:
            continue
        content = attrs.get("content")
        if content:
            values.append(html.unescape(content).strip())
    return values


def _first_meta_content(body: str, name: str, *, lang: str | None = None) -> str | None:
    values = _meta_contents(body, name, lang=lang)
    return values[0] if values else None


def _first_meta_property(body: str, property_name: str) -> str | None:
    for tag in re.findall(r"<meta\b[^>]*>", body, flags=re.IGNORECASE):
        attrs = _tag_attrs(tag)
        if attrs.get("property") != property_name:
            continue
        content = attrs.get("content")
        if content:
            return html.unescape(content).strip()
    return None


def _html_title(body: str) -> str | None:
    match = re.search(r"<title\b[^>]*>(.*?)</title>", body, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()


def _has_cc_by_marker(body: str) -> bool:
    normalized = re.sub(r"\s+", " ", html.unescape(body)).casefold()
    return "creativecommons.org/licenses/by" in normalized or re.search(r"\bcc\s*by\b", normalized) is not None


def _cc_by_license_url(body: str) -> str | None:
    match = re.search(r"https?://creativecommons\.org/licenses/by/[0-9.]+/?", body, flags=re.IGNORECASE)
    return match.group(0) if match else None


def _trim_cyberleninka_boilerplate(text: str) -> str:
    markers = [
        "Аннотация научной статьи",
        "Текст научной работы",
        "Похожие темы",
        "Список литературы",
    ]
    start_indexes = [text.find(marker) for marker in markers[:2] if marker in text]
    if start_indexes:
        text = text[min(start_indexes) :]
    end_indexes = [text.find(marker) for marker in markers[2:] if marker in text]
    if end_indexes:
        text = text[: min(end_indexes)]
    return text.strip()


def _tag_attrs(tag: str) -> dict[str, str]:
    return {
        name.casefold(): html.unescape(value)
        for name, value in re.findall(r"""([\w:-]+)=["']([^"']*)["']""", tag)
    }


def _split_keywords(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in re.split(r"[;,]", value) if part.strip()]


def _is_minsport_source(source: dict[str, Any]) -> bool:
    endpoint = str(source.get("endpoint", ""))
    return "minsport.gov.ru" in endpoint


def _minsport_document_urls(source: dict[str, Any], *, max_documents: int) -> list[str]:
    source_id = str(source.get("id", ""))
    if source_id == "minsport-fed-standards":
        keyword_sets = [
            ["федерального стандарта", "спортивной подготовки"],
            ["федеральный стандарт", "спортивной подготовки"],
        ]
    elif source_id == "evsk-ekp":
        keyword_sets = [
            ["единой всероссийской спортивной классификации"],
            ["евск"],
            ["единый календарный план"],
        ]
    else:
        keyword_sets = [[]]

    links: list[str] = []
    seen: set[str] = set()
    for page in range(1, 41):
        url = _minsport_folder_api_url(folder_id=33, page=page, page_size=50)
        data = _fetch_json(url)
        if not data:
            continue
        for keywords in keyword_sets:
            for link in minsport_document_links_from_api(data, title_keywords=keywords):
                if link not in seen:
                    links.append(link)
                    seen.add(link)
                    if len(links) >= max_documents:
                        return links
        pagination = (data.get("meta") or {}).get("pagination") or {}
        page_count = int(pagination.get("pageCount") or 0)
        if page_count and page >= page_count:
            break
    return links[:max_documents]


def _minsport_folder_api_url(*, folder_id: int, page: int, page_size: int) -> str:
    query = urllib.parse.urlencode(
        {
            "pagination[page]": page,
            "pagination[pageSize]": page_size,
            "sort[0]": "documentActiveSince:desc",
            "sort[1]": "displayPublishedAt:desc",
            "sort[2]": "title:asc",
            "populate": "file",
            "fields[0]": "createdAt",
            "fields[1]": "title",
            "fields[2]": "subTitle",
            "fields[3]": "displayPublishedAt",
            "fields[4]": "documentNumber",
            "fields[5]": "documentActiveSince",
        }
    )
    return f"https://minsport.gov.ru/api/document-center/folders/{folder_id}?{query}"


def _same_origin(left: str, right: str) -> bool:
    left_url = urllib.parse.urlparse(left)
    right_url = urllib.parse.urlparse(right)
    return (left_url.scheme, left_url.netloc) == (right_url.scheme, right_url.netloc)


def _normalize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path or "/", "", parsed.query, ""))


def _quote_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    path = urllib.parse.quote(urllib.parse.unquote(parsed.path), safe="/:%")
    query = urllib.parse.quote(urllib.parse.unquote(parsed.query), safe="=&?/:+,%")
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, path or "/", "", query, ""))


def _looks_like_pdf(data: bytes) -> bool:
    return data.lstrip().startswith(b"%PDF")


def _source_endpoint_title(source: dict[str, Any], url: str) -> str:
    titles = source.get("endpoint_titles") or {}
    if isinstance(titles, dict):
        for key, value in titles.items():
            if _normalize_url(str(key)) == _normalize_url(url):
                return str(value)
    path = urllib.parse.unquote(urllib.parse.urlparse(url).path)
    return Path(path).name


def _row_id(source_id: str, url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return f"{source_id}-{digest}"


def _first_category(source: dict[str, Any]) -> str:
    categories = source.get("bench_categories") or ["general"]
    return str(categories[0])


def _infer_sport(value: str) -> str:
    normalized = value.casefold()
    sport_markers = [
        ("hockey", ["хоккей", "fhr.ru", "vks.fhr.ru"]),
        ("volleyball", ["волейбол", "volley.ru", "volleyball"]),
        ("basketball", ["баскетбол", "russiabasket", "basketball"]),
        ("football", ["футбол", "rfs.ru", "football"]),
        ("swimming", ["плаван", "russwimming", "swimming"]),
        ("athletics", ["легк", "rusathletics", "athletics"]),
        ("wrestling", ["борьб", "wrestrus", "wrestling"]),
        ("gymnastics", ["гимнаст", "sportgymrus", "gymnastics"]),
        ("biathlon", ["биатлон", "biathlon"]),
        ("alpine-skiing", ["горнолыж", "gornolyzhn", "alpine"]),
        ("skiing", ["лыжные гонки", "лыжн", "flgr", "ski"]),
        ("snowboard", ["сноуборд", "snoubord", "snowboard"]),
        ("figure-skating", ["фигурное катание", "fsrussia", "figure"]),
        ("speed-skating", ["конькобеж", "konkobezh", "speed skating"]),
    ]
    for sport, markers in sport_markers:
        if any(marker in normalized for marker in markers):
            return sport
    return "general"


class _FederationDocumentParser(html.parser.HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.documents: list[dict[str, str]] = []
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []
        self._data_url_stack: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name.casefold(): value for name, value in attrs if value is not None}
        if tag == "a":
            href = attrs_dict.get("href")
            if href:
                self._anchor_href = urllib.parse.urljoin(self.base_url, href)
                self._anchor_text = []
        data_url = attrs_dict.get("data-url") or attrs_dict.get("data-href")
        if data_url:
            self._data_url_stack.append(
                {
                    "url": urllib.parse.urljoin(self.base_url, data_url),
                    "depth": 1,
                    "text": [],
                }
            )
        elif self._data_url_stack:
            self._data_url_stack[-1]["depth"] += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._anchor_href:
            self.documents.append({"url": self._anchor_href, "title": " ".join(self._anchor_text)})
            self._anchor_href = None
            self._anchor_text = []
        if self._data_url_stack:
            current = self._data_url_stack[-1]
            current["depth"] -= 1
            if current["depth"] <= 0:
                self.documents.append({"url": current["url"], "title": " ".join(current["text"])})
                self._data_url_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._anchor_href:
            self._anchor_text.append(data)
        if self._data_url_stack:
            self._data_url_stack[-1]["text"].append(data)


class _Robots:
    def __init__(self, start_url: str, *, enabled: bool) -> None:
        self.enabled = enabled
        self.parser = urllib.robotparser.RobotFileParser()
        if enabled:
            parsed = urllib.parse.urlparse(start_url)
            self.parser.set_url(f"{parsed.scheme}://{parsed.netloc}/robots.txt")
            try:
                self.parser.read()
            except Exception:
                self.enabled = False

    def can_fetch(self, url: str) -> bool:
        if not self.enabled:
            return True
        return self.parser.can_fetch("lii-sport-corpus-prep/0.1", url)


class _TextAndLinkParser(html.parser.HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.text_parts: list[str] = []
        self.links: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "header", "nav", "footer", "aside"}:
            self._skip_depth += 1
            return
        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href")
            if href:
                self.links.append(urllib.parse.urljoin(self.base_url, href))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "header", "nav", "footer", "aside"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and data.strip():
            self.text_parts.append(data.strip())
