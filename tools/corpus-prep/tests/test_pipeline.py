import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


class CorpusPrepPipelineTests(unittest.TestCase):
    def test_source_registry_marks_federation_rules_for_human_approval(self):
        from corpus_prep.registry import load_sources

        sources = load_sources(Path("sources.yaml"))
        fed_rules = {source["id"]: source for source in sources}["fed-rules"]

        self.assertTrue(fed_rules["requires_human_approval"])
        self.assertEqual(fed_rules["license_kind"], "license-check-required")

    def test_clean_pipeline_drops_pii_and_bench_leakage(self):
        from corpus_prep.clean import clean_examples

        bench_questions = [
            {
                "id": "bench-1",
                "question": "Что такое технический фол в баскетболе?",
            }
        ]
        examples = [
            {
                "id": "ok-1",
                "source_id": "rusada-edu",
                "license_kind": "public-ru-state-agency",
                "license_verified": True,
                "text": "Антидопинговые правила требуют проверки препаратов перед применением. " * 8,
                "messages": [
                    {"role": "user", "content": "Как проверить препарат спортсмену?"},
                    {"role": "assistant", "content": "Нужно сверить препарат с актуальными материалами РУСАДА."},
                ],
            },
            {
                "id": "pii-1",
                "source_id": "demo",
                "license_kind": "public-domain",
                "license_verified": True,
                "text": "Телефон тренера +7 999 123-45-67 указан в документе. " * 8,
                "messages": [
                    {"role": "user", "content": "Кому звонить?"},
                    {"role": "assistant", "content": "Позвоните по номеру +7 999 123-45-67."},
                ],
            },
            {
                "id": "leak-1",
                "source_id": "demo",
                "license_kind": "public-domain",
                "license_verified": True,
                "text": "Что такое технический фол в баскетболе?\nОтвет из источника. " * 8,
                "messages": [
                    {"role": "user", "content": "Что такое технический фол в баскетболе?"},
                    {"role": "assistant", "content": "Это нарушение поведения."},
                ],
            },
        ]

        cleaned, report = clean_examples(examples, bench_questions, min_chars=100, max_chars=2000)

        self.assertEqual([example["id"] for example in cleaned], ["ok-1"])
        self.assertEqual(report["dropped"]["pii"], 1)
        self.assertEqual(report["dropped"]["bench_leakage"], 1)

    def test_make_splits_writes_manifest_hashes_without_overlap(self):
        from corpus_prep.splits import make_splits

        examples = [
            {
                "id": f"ex-{index}",
                "sport": "basketball" if index % 2 else "volleyball",
                "category": "rules" if index % 3 else "methodology",
                "messages": [
                    {"role": "user", "content": f"Вопрос {index}"},
                    {"role": "assistant", "content": f"Ответ {index}"},
                ],
            }
            for index in range(30)
        ]

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            manifest = make_splits(examples, output_dir, seed=42)

            split_ids = {}
            for split_name in ("train", "val", "test"):
                split_path = output_dir / f"{split_name}.jsonl"
                rows = [json.loads(line) for line in split_path.read_text(encoding="utf-8").splitlines()]
                split_ids[split_name] = {row["id"] for row in rows}

            self.assertEqual(len(split_ids["train"] & split_ids["val"]), 0)
            self.assertEqual(len(split_ids["train"] & split_ids["test"]), 0)
            self.assertEqual(len(split_ids["val"] & split_ids["test"]), 0)
            self.assertEqual(manifest["total_examples"], 30)
            self.assertEqual(set(manifest["splits"]), {"train", "val", "test"})

    def test_validation_batch_runner_writes_release_artifacts(self):
        from corpus_prep.pipeline import run_validation_batch

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir = root / "corpus" / "raw" / "rusada-edu"
            raw_dir.mkdir(parents=True)
            (raw_dir / "sample.jsonl").write_text(
                json.dumps(
                    {
                        "id": "raw-1",
                        "source_id": "rusada-edu",
                        "license_kind": "public-ru-state-agency",
                        "license_verified": True,
                        "sport": "general",
                        "category": "anti-doping",
                        "text": "Антидопинговая проверка требует заранее сверить препарат с перечнем РУСАДА. " * 8,
                        "messages": [
                            {"role": "user", "content": "Как спортсмену проверить препарат?"},
                            {
                                "role": "assistant",
                                "content": "Сверить препарат с актуальными материалами РУСАДА и обратиться к врачу команды.",
                            },
                        ],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            bench_path = root / "data" / "questions.json"
            bench_path.parent.mkdir()
            bench_path.write_text(
                json.dumps([{"id": "bench-1", "question": "Контрольный вопрос бенчмарка"}], ensure_ascii=False),
                encoding="utf-8",
            )

            report = run_validation_batch(root, output_name="lii-sport-sft-v0.1-test")

            output_dir = root / "corpus" / "lii-sport-sft-v0.1-test"
            self.assertEqual(report["clean"]["kept"], 1)
            self.assertTrue((output_dir / "train.jsonl").exists())
            self.assertTrue((output_dir / "MANIFEST.md").exists())
            self.assertTrue((output_dir / "LICENSE-MATRIX.csv").exists())
            self.assertTrue((output_dir / "stats.json").exists())

    def test_validation_batch_accepts_single_jsonl_input_file(self):
        from corpus_prep.pipeline import run_validation_batch

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "synth.jsonl"
            input_path.write_text(
                json.dumps(
                    {
                        "id": "synth-1",
                        "source_id": "rusada-edu",
                        "license_kind": "public-ru-state-agency",
                        "license_verified": True,
                        "sport": "general",
                        "category": "anti-doping",
                        "text": "Как спортсмену проверить препарат?\nПроверить препарат по материалам РУСАДА до применения.",
                        "messages": [
                            {"role": "user", "content": "Как спортсмену проверить препарат?"},
                            {"role": "assistant", "content": "Проверить препарат по материалам РУСАДА до применения."},
                        ],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            report = run_validation_batch(root, input_root=input_path, output_name="single-file")

            self.assertEqual(report["raw_examples"], 1)
            self.assertEqual(report["clean"]["kept"], 1)

    def test_seed_demo_raw_batch_uses_only_non_bench_material(self):
        from corpus_prep.harvest import seed_demo_raw_batch

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            written = seed_demo_raw_batch(root)

            self.assertEqual(len(written), 3)
            for path in written:
                text = path.read_text(encoding="utf-8")
                self.assertIn('"source_id"', text)
                self.assertNotIn("Что такое технический фол в баскетболе?", text)

    def test_env_loader_reads_dotenv_and_claude_settings_without_exposing_values(self):
        from corpus_prep.secrets import load_secret_env

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dotenv = root / ".env.local"
            settings = root / "settings.json"
            dotenv.write_text("OPENROUTER_API_KEY=or-test\n", encoding="utf-8")
            settings.write_text(json.dumps({"env": {"GEMINI_API_KEY": "gem-test"}}), encoding="utf-8")

            loaded = load_secret_env([dotenv], [settings])

            self.assertEqual(loaded["OPENROUTER_API_KEY"], "or-test")
            self.assertEqual(loaded["GEMINI_API_KEY"], "gem-test")

    def test_default_secret_paths_prefer_vault_root_env(self):
        from corpus_prep.secrets import default_secret_paths

        dotenv_paths, settings_paths = default_secret_paths()

        self.assertEqual(dotenv_paths[0], Path("/Users/daniely/csylabs_vault/.env.local"))
        self.assertIn(Path("/Users/daniely/csylabs_vault/.claude/settings.json"), settings_paths)

    def test_default_generation_models_use_latest_available_gemini(self):
        from corpus_prep.models import DEFAULT_MODELS

        self.assertEqual(DEFAULT_MODELS["agy_default"], "antigravity-default-gemini-3.5-flash")
        self.assertEqual(DEFAULT_MODELS["gemini_direct"], "gemini-3.5-flash")
        self.assertEqual(DEFAULT_MODELS["openrouter_bulk"], "google/gemini-3.5-flash")

    def test_http_static_harvest_writes_resumable_raw_rows(self):
        from corpus_prep.harvest import harvest_http_static

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            web = root / "web"
            web.mkdir()
            (web / "index.html").write_text(
                '<html><body><h1>РУСАДА</h1><p>Антидопинговое обучение для спортсменов.</p>'
                '<a href="page.html">page</a></body></html>',
                encoding="utf-8",
            )
            (web / "page.html").write_text(
                "<html><body><p>Проверка препаратов и образовательные материалы РУСАДА.</p></body></html>",
                encoding="utf-8",
            )

            source = {
                "id": "rusada-edu",
                "endpoint": (web / "index.html").as_uri(),
                "harvester": "http_static",
                "license_kind": "public-ru-state-agency",
                "license_verified": True,
                "requires_human_approval": False,
                "bench_categories": ["anti-doping"],
            }
            rows = harvest_http_static(source, root, max_pages=2, delay_seconds=0, respect_robots=False)

            raw_path = root / "corpus" / "raw" / "rusada-edu" / "harvest.jsonl"
            self.assertEqual(len(rows), 2)
            self.assertTrue(raw_path.exists())
            raw_text = raw_path.read_text(encoding="utf-8")
            self.assertIn("Антидопинговое обучение", raw_text)
            self.assertIn('"license_verified": true', raw_text)

    def test_http_static_harvest_continues_discovery_from_seen_pages(self):
        from corpus_prep.harvest import harvest_http_static

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            web = root / "web"
            web.mkdir()
            (web / "index.html").write_text(
                '<html><body><p>Стартовая страница.</p><a href="page.html">page</a></body></html>',
                encoding="utf-8",
            )
            (web / "page.html").write_text(
                "<html><body><p>Новая содержательная страница РУСАДА.</p></body></html>",
                encoding="utf-8",
            )
            source = {
                "id": "rusada-edu",
                "endpoint": (web / "index.html").as_uri(),
                "harvester": "http_static",
                "license_kind": "public-ru-state-agency",
                "license_verified": True,
                "requires_human_approval": False,
                "bench_categories": ["anti-doping"],
            }

            first_rows = harvest_http_static(source, root, max_pages=1, delay_seconds=0, respect_robots=False)
            second_rows = harvest_http_static(source, root, max_pages=2, delay_seconds=0, respect_robots=False)

            self.assertEqual(len(first_rows), 1)
            self.assertEqual(len(second_rows), 1)
            self.assertEqual(second_rows[0]["url"], (web / "page.html").as_uri())

    def test_pdf_harvest_discovers_pdf_links_and_writes_raw_rows(self):
        from corpus_prep.harvest import harvest_pdf_documents

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            web = root / "web"
            web.mkdir()
            pdf_path = web / "standard.pdf"
            pdf_path.write_bytes(b"%PDF-test")
            (web / "index.html").write_text(
                '<html><body><a href="standard.pdf">Федеральный стандарт спортивной подготовки</a></body></html>',
                encoding="utf-8",
            )
            source = {
                "id": "minsport-fed-standards",
                "endpoint": (web / "index.html").as_uri(),
                "harvester": "pdf_extract",
                "license_kind": "public-domain",
                "license_verified": True,
                "requires_human_approval": False,
                "bench_categories": ["methodology"],
            }

            rows = harvest_pdf_documents(
                source,
                root,
                max_documents=1,
                delay_seconds=0,
                extract_pdf_text=lambda _path: "Федеральный стандарт спортивной подготовки устанавливает этапы подготовки. " * 4,
            )

            raw_path = root / "corpus" / "raw" / "minsport-fed-standards" / "harvest.jsonl"
            self.assertEqual(len(rows), 1)
            self.assertTrue(raw_path.exists())
            row = json.loads(raw_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(row["source_id"], "minsport-fed-standards")
            self.assertEqual(row["content_type"], "application/pdf")
            self.assertIn("Федеральный стандарт", row["text"])

    def test_minsport_api_records_filter_to_pdf_links_by_keyword(self):
        from corpus_prep.harvest import minsport_document_links_from_api

        data = {
            "data": [
                {
                    "attributes": {
                        "title": "Об утверждении федерального стандарта спортивной подготовки по виду спорта баскетбол",
                        "file": {"data": {"attributes": {"url": "http://storage.minsport.gov.ru/cms-uploads/cms/basketball.pdf"}}},
                    }
                },
                {
                    "attributes": {
                        "title": "О назначении стипендий",
                        "file": {"data": {"attributes": {"url": "http://storage.minsport.gov.ru/cms-uploads/cms/stipend.pdf"}}},
                    }
                },
            ]
        }

        links = minsport_document_links_from_api(data, title_keywords=["федерального стандарта", "спортивной подготовки"])

        self.assertEqual(links, ["https://storage.minsport.gov.ru/cms-uploads/cms/basketball.pdf"])

    def test_rcsi_issue_parser_finds_canonical_article_links(self):
        from corpus_prep.harvest import rcsi_article_links_from_issue_html

        html = """
        <a href="https://journals.rcsi.science/1994-4683/article/view/410388">article</a>
        <a href="https://journals.rcsi.science/1994-4683/article/view/410388/677830">pdf</a>
        <a href="/1994-4683/article/view/410390">relative</a>
        """

        links = rcsi_article_links_from_issue_html(html, "https://journals.rcsi.science/1994-4683/issue/current")

        self.assertEqual(
            links,
            [
                "https://journals.rcsi.science/1994-4683/article/view/410388",
                "https://journals.rcsi.science/1994-4683/article/view/410390",
            ],
        )

    def test_rcsi_article_row_requires_cc_by_license(self):
        from corpus_prep.harvest import rcsi_article_row_from_html

        source = {
            "id": "lesgaft-uchenye-zapiski",
            "license_kind": "cc-by-article",
            "requires_human_approval": False,
            "bench_categories": ["methodology"],
        }
        allowed = """
        <meta name="DC.Title" lang="ru" content="Методика подготовки юных спортсменов"/>
        <meta name="DC.Abstract" lang="ru" content="Цель исследования – описать методику подготовки. Результаты исследования показывают применимость модели в спортивной школе."/>
        <meta name="DC.Subject" lang="ru" content="спортивная подготовка"/>
        <meta name="DC.Rights" content="https://creativecommons.org/licenses/by/4.0"/>
        """
        blocked = allowed.replace("https://creativecommons.org/licenses/by/4.0", "Авторы, 2026")

        row = rcsi_article_row_from_html(source, "https://journals.rcsi.science/1994-4683/article/view/1", allowed)

        self.assertIsNotNone(row)
        self.assertEqual(row["license_kind"], "cc-by-4.0")
        self.assertTrue(row["license_verified"])
        self.assertIn("Методика подготовки", row["text"])
        self.assertIsNone(rcsi_article_row_from_html(source, "https://journals.rcsi.science/1994-4683/article/view/2", blocked))

    def test_cyberleninka_article_row_requires_cc_by_marker(self):
        from corpus_prep.harvest import cyberleninka_article_row_from_html

        source = {"id": "sport-history-ccby-cyberleninka", "bench_categories": ["history"]}
        html = """
        <html>
          <head>
            <meta property="og:title" content="Физкультура и спорт в СССР как социальная лаборатория">
            <meta name="description" content="Аннотация статьи о роли физической культуры и спорта в СССР.">
          </head>
          <body>
            <article>
              <p>Текст научной статьи по истории физической культуры и спорта.</p>
              <p>Физическая культура и спорт в СССР выполняли функции социальной политики.</p>
              <p>Материал распространяется на условиях лицензии CC BY.</p>
            </article>
          </body>
        </html>
        """

        row = cyberleninka_article_row_from_html(source, "https://cyberleninka.ru/article/n/example", html)

        self.assertIsNotNone(row)
        self.assertEqual(row["license_kind"], "cc-by-article")
        self.assertEqual(row["category"], "history")
        self.assertIn("Физкультура и спорт в СССР", row["text"])

    def test_cyberleninka_article_row_rejects_unlicensed_page(self):
        from corpus_prep.harvest import cyberleninka_article_row_from_html

        source = {"id": "sport-history-ccby-cyberleninka", "bench_categories": ["history"]}
        html = """
        <html>
          <head><meta property="og:title" content="История спорта"></head>
          <body><article><p>Текст статьи без открытой лицензии.</p></article></body>
        </html>
        """

        row = cyberleninka_article_row_from_html(source, "https://cyberleninka.ru/article/n/example", html)

        self.assertIsNone(row)

    def test_cyberleninka_harvest_uses_pdf_full_text_when_available(self):
        from corpus_prep.harvest import harvest_cyberleninka_articles

        source = {
            "id": "sport-history-ccby-cyberleninka",
            "endpoint": ["https://cyberleninka.ru/article/n/example"],
            "license_kind": "cc-by-article",
            "license_verified": True,
            "requires_human_approval": False,
            "bench_categories": ["history"],
        }
        html = """
        <html>
          <head><meta property="og:title" content="История спорта в СССР"></head>
          <body><p>Краткая аннотация о развитии физической культуры и спорта в СССР. Краткая аннотация о развитии физической культуры и спорта в СССР. Краткая аннотация о развитии физической культуры и спорта в СССР. CC BY.</p></body>
        </html>
        """

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("corpus_prep.harvest._fetch_text", return_value=("text/html", html)):
                with patch("corpus_prep.harvest._fetch_binary", return_value=b"%PDF-test"):
                    with patch("corpus_prep.harvest.extract_pdf_text_with_ocr", return_value="Полный текст статьи. " * 30):
                        rows = harvest_cyberleninka_articles(source, root, max_articles=1, delay_seconds=0)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["content_type"], "application/pdf")
            self.assertIn("/pdf", rows[0]["pdf_url"])
            self.assertTrue((root / "corpus" / "raw" / "sport-history-ccby-cyberleninka" / "documents").exists())

    def test_federation_document_parser_finds_data_url_and_pdf_anchors(self):
        from corpus_prep.harvest import federation_document_links_from_html

        html = """
        <div class="documents__item" data-url="/upload/hockey-rules.pdf">
          <div class="documents__item-name">Правила вида спорта "хоккей"</div>
        </div>
        <a href="/docs/volleyball-rules.pdf">Официальные правила волейбола</a>
        <a href="/docs/page.html">Не PDF</a>
        """

        links = federation_document_links_from_html(html, "https://vks.fhr.ru/docs/93/")

        self.assertEqual(
            links,
            [
                {
                    "title": 'Правила вида спорта "хоккей"',
                    "url": "https://vks.fhr.ru/upload/hockey-rules.pdf",
                },
                {
                    "title": "Официальные правила волейбола",
                    "url": "https://vks.fhr.ru/docs/volleyball-rules.pdf",
                },
            ],
        )

    def test_federation_rules_harvest_keeps_human_approval_metadata(self):
        from corpus_prep.harvest import harvest_federation_rules

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            web = root / "web"
            web.mkdir()
            pdf_path = web / "rules.pdf"
            pdf_path.write_bytes(b"%PDF-test")
            (web / "index.html").write_text(
                '<html><body><a href="rules.pdf">Правила вида спорта хоккей</a></body></html>',
                encoding="utf-8",
            )
            source = {
                "id": "fed-rules-approved",
                "endpoint": [(web / "index.html").as_uri()],
                "harvester": "federation_rules",
                "license_kind": "human-approved-federation-public-doc",
                "license_verified": True,
                "requires_human_approval": True,
                "bench_categories": ["rules"],
            }

            rows = harvest_federation_rules(
                source,
                root,
                max_documents=1,
                delay_seconds=0,
                extract_pdf_text=lambda _path: "Правила вида спорта хоккей описывают игровое время и порядок судейства. " * 4,
            )

            raw_path = root / "corpus" / "raw" / "fed-rules-approved" / "harvest.jsonl"
            self.assertEqual(len(rows), 1)
            self.assertTrue(raw_path.exists())
            row = json.loads(raw_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(row["source_id"], "fed-rules-approved")
            self.assertEqual(row["license_kind"], "human-approved-federation-public-doc")
            self.assertEqual(row["approval_note"], "User approved federation and MinSport documents for working corpus on 2026-05-23")
            self.assertTrue(row["requires_human_approval"])
            self.assertEqual(row["sport"], "hockey")
            self.assertEqual(row["source_title"], "Правила вида спорта хоккей")

    def test_official_history_static_harvest_keeps_internal_metadata(self):
        from corpus_prep.harvest import harvest_official_history_static

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            web = root / "web"
            web.mkdir()
            (web / "history.html").write_text(
                "<html><head><title>История федерации</title></head><body>"
                "<h1>История федерации</h1>"
                f"<p>{'Развитие физической культуры и спорта в регионе. ' * 12}</p>"
                "</body></html>",
                encoding="utf-8",
            )
            source = {
                "id": "sport-history-official-approved",
                "endpoint": [(web / "history.html").as_uri()],
                "harvester": "official_history_static",
                "license_kind": "human-approved-official-history-public-doc",
                "license_verified": True,
                "requires_human_approval": True,
                "approval_note": "approved for internal corpus",
                "bench_categories": ["history", "federation-procedures"],
            }

            rows = harvest_official_history_static(source, root, max_pages=1, delay_seconds=0)

            self.assertEqual(len(rows), 1)
            self.assertTrue(rows[0]["requires_human_approval"])
            self.assertEqual(rows[0]["approved_by"], "Daniel Ivanov")
            self.assertEqual(rows[0]["approval_note"], "approved for internal corpus")
            self.assertEqual(rows[0]["license_kind"], "human-approved-official-history-public-doc")
            self.assertIn("Развитие физической культуры", rows[0]["text"])

    def test_federation_rules_harvest_skips_seen_candidates_before_limit(self):
        from corpus_prep.harvest import harvest_federation_rules

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            web = root / "web"
            web.mkdir()
            (web / "seen.pdf").write_bytes(b"%PDF-seen")
            (web / "new.pdf").write_bytes(b"%PDF-new")
            seen_url = (web / "seen.pdf").as_uri()
            new_url = (web / "new.pdf").as_uri()
            (web / "index.html").write_text(
                f"""
                <html><body>
                  <a href="{seen_url}">Правила вида спорта хоккей</a>
                  <a href="{new_url}">Официальные правила волейбола</a>
                </body></html>
                """,
                encoding="utf-8",
            )
            raw_dir = root / "corpus" / "raw" / "fed-rules-approved"
            raw_dir.mkdir(parents=True)
            (raw_dir / "harvest.jsonl").write_text(
                json.dumps({"id": "seen", "url": seen_url}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            source = {
                "id": "fed-rules-approved",
                "endpoint": [(web / "index.html").as_uri()],
                "harvester": "federation_rules",
                "license_kind": "human-approved-federation-public-doc",
                "license_verified": True,
                "requires_human_approval": True,
                "bench_categories": ["rules"],
            }

            rows = harvest_federation_rules(
                source,
                root,
                max_documents=1,
                delay_seconds=0,
                extract_pdf_text=lambda _path: "Официальные правила волейбола описывают игровые действия и судейство. " * 4,
            )

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["url"], new_url)
            self.assertEqual(rows[0]["sport"], "volleyball")

    def test_federation_rules_harvest_rejects_html_returned_for_pdf_link(self):
        from corpus_prep.harvest import harvest_federation_rules

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            web = root / "web"
            web.mkdir()
            bad_pdf = web / "rules.pdf"
            bad_pdf.write_text("<html><body>not a pdf</body></html>", encoding="utf-8")
            (web / "index.html").write_text(
                '<html><body><a href="rules.pdf">Официальные правила волейбола</a></body></html>',
                encoding="utf-8",
            )
            source = {
                "id": "fed-rules-volleyball-approved",
                "endpoint": [(web / "index.html").as_uri()],
                "harvester": "federation_rules",
                "license_kind": "human-approved-federation-public-doc",
                "license_verified": True,
                "requires_human_approval": True,
                "bench_categories": ["rules"],
            }

            rows = harvest_federation_rules(
                source,
                root,
                max_documents=1,
                delay_seconds=0,
                extract_pdf_text=lambda _path: "Этот текст не должен попасть в корпус.",
            )

            self.assertEqual(rows, [])

    def test_federation_rules_harvest_accepts_direct_pdf_endpoint(self):
        from corpus_prep.harvest import harvest_federation_rules

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            web = root / "web"
            web.mkdir()
            pdf_path = web / "basketball-rules.pdf"
            pdf_path.write_bytes(b"%PDF-test")
            source = {
                "id": "fed-rules-basketball-approved",
                "endpoint": [pdf_path.as_uri()],
                "harvester": "federation_rules",
                "license_kind": "human-approved-federation-public-doc",
                "license_verified": True,
                "requires_human_approval": True,
                "bench_categories": ["rules"],
            }

            rows = harvest_federation_rules(
                source,
                root,
                max_documents=1,
                delay_seconds=0,
                extract_pdf_text=lambda _path: "Официальные правила баскетбола описывают игровое время, фолы и обязанности судей. " * 4,
            )

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["url"], pdf_path.as_uri())
            self.assertEqual(rows[0]["sport"], "basketball")
            self.assertEqual(rows[0]["source_title"], "basketball-rules.pdf")

    def test_federation_rules_harvest_accepts_declared_direct_download_endpoint(self):
        from corpus_prep.harvest import harvest_federation_rules

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            web = root / "web"
            web.mkdir()
            download_path = web / "download"
            download_path.write_bytes(b"%PDF-test")
            source = {
                "id": "fed-rules-football-approved",
                "endpoint": [download_path.as_uri()],
                "direct_document": True,
                "endpoint_titles": {download_path.as_uri(): "Правила вида спорта футбол"},
                "harvester": "federation_rules",
                "license_kind": "human-approved-federation-public-doc",
                "license_verified": True,
                "requires_human_approval": True,
                "bench_categories": ["rules"],
            }

            rows = harvest_federation_rules(
                source,
                root,
                max_documents=1,
                delay_seconds=0,
                extract_pdf_text=lambda _path: "Правила вида спорта футбол описывают дисциплины, игровое время и обязанности судей. " * 4,
            )

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["url"], download_path.as_uri())
            self.assertEqual(rows[0]["sport"], "football")
            self.assertEqual(rows[0]["source_title"], "Правила вида спорта футбол")

    def test_extract_pdf_text_uses_ocr_fallback_when_pdftotext_is_empty(self):
        from corpus_prep.harvest import extract_pdf_text

        calls = []

        def fake_pdftotext(_path):
            calls.append("pdftotext")
            return " "

        def fake_ocr(_path, **_kwargs):
            calls.append("ocr")
            return "Федеральный стандарт спортивной подготовки"

        text = extract_pdf_text(Path("scan.pdf"), min_text_chars=20, pdftotext=fake_pdftotext, ocr=fake_ocr)

        self.assertEqual(text, "Федеральный стандарт спортивной подготовки")
        self.assertEqual(calls, ["pdftotext", "ocr"])

    def test_synthesize_examples_builds_messages_with_provenance(self):
        from corpus_prep.synthesize import synthesize_examples

        raw_examples = [
            {
                "id": "raw-1",
                "source_id": "rusada-edu",
                "license_kind": "public-ru-state-agency",
                "license_verified": True,
                "requires_human_approval": False,
                "sport": "general",
                "category": "anti-doping",
                "url": "https://example.test/rusada",
                "text": "Антидопинговое обучение помогает спортсмену проверять препараты до старта. " * 6,
            }
        ]

        def fake_generate(prompt: str) -> str:
            self.assertIn("Антидопинговое обучение", prompt)
            self.assertIn("Игнорируй меню", prompt)
            return json.dumps(
                [
                    {
                        "question": "Как спортсмену проверить препарат?",
                        "answer": "Сверить препарат с актуальными материалами РУСАДА до применения.",
                    }
                ],
                ensure_ascii=False,
            )

        examples = synthesize_examples(raw_examples, fake_generate, questions_per_chunk=1)

        self.assertEqual(len(examples), 1)
        self.assertEqual(examples[0]["source_id"], "rusada-edu")
        self.assertEqual(examples[0]["messages"][0]["role"], "user")
        self.assertEqual(examples[0]["messages"][1]["role"], "assistant")
        self.assertIn("РУСАДА", examples[0]["messages"][1]["content"])

    def test_synthesize_examples_reports_progress_per_raw_chunk(self):
        from corpus_prep.synthesize import synthesize_examples

        raw_examples = [
            {
                "id": "raw-1",
                "source_id": "rusada-edu",
                "license_kind": "public-ru-state-agency",
                "license_verified": True,
                "text": "Антидопинговое обучение помогает спортсмену проверять препараты до старта. " * 6,
            }
        ]
        seen = []

        synthesize_examples(
            raw_examples,
            lambda _prompt: '[{"question":"Что проверить?","answer":"Проверить препарат."}]',
            questions_per_chunk=1,
            on_raw_start=lambda index, raw: seen.append((index, raw["id"])),
        )

        self.assertEqual(seen, [(1, "raw-1")])

    def test_synthesis_keeps_source_excerpt_out_of_training_text(self):
        from corpus_prep.synthesize import synthesize_examples

        raw_examples = [
            {
                "id": "raw-1",
                "source_id": "rusada-edu",
                "license_kind": "public-ru-state-agency",
                "license_verified": True,
                "text": "Антидопинговое обучение. Контакты: +7 999 123-45-67. " * 8,
            }
        ]

        examples = synthesize_examples(
            raw_examples,
            lambda _prompt: '[{"question":"Что проверить?","answer":"Проверить препарат по материалам РУСАДА."}]',
            questions_per_chunk=1,
        )

        self.assertNotIn("+7 999", examples[0]["text"])
        self.assertNotIn("+7 999", examples[0]["source_excerpt"])
        self.assertIn("[PHONE]", examples[0]["source_excerpt"])

    def test_synthesis_masks_parenthesized_ru_phone(self):
        from corpus_prep.synthesize import scrub_pii

        self.assertEqual(scrub_pii("+7 (499) 271-77-61"), "[PHONE]")

    def test_synthesis_prompt_scrubs_pii_before_generation(self):
        from corpus_prep.synthesize import synthesize_examples

        raw_examples = [
            {
                "id": "raw-1",
                "source_id": "rusada-edu",
                "license_kind": "public-ru-state-agency",
                "license_verified": True,
                "text": "Пулы тестирования и информация о местонахождении. Контакты: +7 (499) 271-77-61 rusada@rusada.ru. " * 8,
            }
        ]

        def fake_generate(prompt: str) -> str:
            self.assertNotIn("+7 (499)", prompt)
            self.assertNotIn("rusada@rusada.ru", prompt)
            self.assertIn("[PHONE]", prompt)
            self.assertIn("[EMAIL]", prompt)
            return '[{"question":"Что обязан делать спортсмен?","answer":"Поддерживать актуальные сведения о местонахождении."}]'

        synthesize_examples(raw_examples, fake_generate, questions_per_chunk=1)

    def test_synthesis_prompt_samples_long_ocr_documents_across_sections(self):
        from corpus_prep.synthesize import synthesize_examples

        captured_prompts = []
        raw_examples = [
            {
                "id": "raw-ocr-1",
                "source_id": "minsport-fed-standards",
                "license_kind": "public-domain",
                "license_verified": True,
                "text": (
                    "НАЧАЛО федерального стандарта. " * 120
                    + " СЕРЕДИНА: контрольные нормативы и этапы подготовки. "
                    + "методика подготовки спортсменов. " * 120
                    + " КОНЕЦ: требования к оборудованию и кадрам."
                ),
            }
        ]

        def fake_generate(prompt: str) -> str:
            captured_prompts.append(prompt)
            return '[{"question":"Что проверить?","answer":"Проверить требования стандарта."}]'

        synthesize_examples(raw_examples, fake_generate, questions_per_chunk=1)

        self.assertIn("НАЧАЛО", captured_prompts[0])
        self.assertIn("СЕРЕДИНА", captured_prompts[0])
        self.assertIn("КОНЕЦ", captured_prompts[0])

    def test_synthesis_parser_accepts_json_array_with_trailing_text(self):
        from corpus_prep.synthesize import synthesize_examples

        raw_examples = [
            {
                "id": "raw-1",
                "source_id": "rusada-edu",
                "license_kind": "public-ru-state-agency",
                "license_verified": True,
                "text": "Права и обязанности спортсмена в антидопинговой системе. " * 8,
            }
        ]

        examples = synthesize_examples(
            raw_examples,
            lambda _prompt: '[{"question":"Что обязан делать спортсмен?","answer":"Соблюдать антидопинговые правила."}]\n\nКомментарий: готово.',
            questions_per_chunk=1,
        )

        self.assertEqual(len(examples), 1)
        self.assertEqual(examples[0]["messages"][0]["content"], "Что обязан делать спортсмен?")

    def test_filter_raw_examples_by_url_regex(self):
        from corpus_prep.synthesize import filter_raw_examples

        rows = [
            {"url": "https://rusada.ru/athletes/anti-doping-rules-violations/", "text": "ok"},
            {"url": "https://rusada.ru/about/documents/", "text": "admin"},
        ]

        filtered = filter_raw_examples(rows, include_url_regex=r"/athletes/")

        self.assertEqual([row["text"] for row in filtered], ["ok"])

    def test_openrouter_model_id_normalization_preserves_google_prefix(self):
        from corpus_prep.synthesize import normalize_model_for_provider

        self.assertEqual(normalize_model_for_provider("google/gemini-3.5-flash", "openrouter"), "google/gemini-3.5-flash")
        self.assertEqual(normalize_model_for_provider("google/gemini-3.5-flash", "gemini-direct"), "gemini-3.5-flash")

    def test_agy_generate_text_uses_print_mode_with_timeout(self):
        from corpus_prep.synthesize import agy_generate_text

        calls = []

        class Result:
            stdout = " AGY response \n"

        def fake_runner(args, **kwargs):
            calls.append((args, kwargs))
            return Result()

        response = agy_generate_text("Сгенерируй JSON", timeout_seconds=45, runner=fake_runner)

        self.assertEqual(response, "AGY response")
        self.assertEqual(calls[0][0], ["agy", "--print", "Сгенерируй JSON", "--print-timeout", "45s"])
        self.assertTrue(calls[0][1]["check"])
        self.assertTrue(calls[0][1]["capture_output"])
        self.assertTrue(calls[0][1]["text"])


if __name__ == "__main__":
    unittest.main()
