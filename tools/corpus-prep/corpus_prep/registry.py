from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_SOURCES: list[dict[str, Any]] = [
    {
        "id": "minsport-fed-standards",
        "tier": "S",
        "endpoint": "https://minsport.gov.ru/documents/",
        "harvester": "pdf_extract",
        "license_kind": "public-domain",
        "license_verified": True,
        "requires_human_approval": False,
        "bench_categories": ["methodology", "federation-procedures"],
    },
    {
        "id": "minsport-profstandards",
        "tier": "S",
        "endpoint": "https://profstandart.rosmintrud.ru/",
        "harvester": "pdf_extract",
        "license_kind": "public-domain",
        "license_verified": True,
        "requires_human_approval": False,
        "bench_categories": ["methodology", "federation-procedures"],
    },
    {
        "id": "rusada-edu",
        "tier": "S",
        "endpoint": "https://rusada.ru/education/",
        "harvester": "http_static",
        "license_kind": "public-ru-state-agency",
        "license_verified": True,
        "requires_human_approval": False,
        "bench_categories": ["anti-doping"],
    },
    {
        "id": "minzdrav-clinical-sport",
        "tier": "S",
        "endpoint": "https://cr.minzdrav.gov.ru/",
        "harvester": "gov_docs",
        "license_kind": "public-domain",
        "license_verified": True,
        "requires_human_approval": False,
        "bench_categories": ["sport-medicine"],
    },
    {
        "id": "teoriya-ru",
        "tier": "A",
        "endpoint": "https://teoriya.ru/",
        "harvester": "http_static",
        "license_kind": "blocked-copyright-permission-required",
        "license_verified": False,
        "requires_human_approval": False,
        "bench_categories": ["methodology", "biomechanics", "sport-psych", "history"],
    },
    {
        "id": "lesgaft-uchenye-zapiski",
        "tier": "A",
        "endpoint": "https://journals.rcsi.science/1994-4683/issue/current",
        "harvester": "rcsi_journal",
        "license_kind": "cc-by-article",
        "license_verified": True,
        "requires_human_approval": False,
        "bench_categories": ["methodology", "sport-medicine"],
    },
    {
        "id": "cyberleninka-sport",
        "tier": "A",
        "endpoint": "https://cyberleninka.ru/",
        "harvester": "cyberleninka",
        "license_kind": "cc-by-or-reject",
        "license_verified": False,
        "requires_human_approval": False,
        "bench_categories": ["all"],
    },
    {
        "id": "sport-history-ccby-cyberleninka",
        "tier": "A",
        "endpoint": [
            "https://cyberleninka.ru/article/n/fizkultura-i-sport-v-sssr-kak-sotsialnaya-laboratoriya-konstruirovaniya-ideala-sovetskogo-cheloveka",
            "https://cyberleninka.ru/article/n/istoriya-sportivnoy-propagandy-v-sssr-v-period-1945-1991-gg",
            "https://cyberleninka.ru/article/n/tendentsii-razvitiya-sovetskogo-zakonodatelstva-reguliruyuschego-sferu-fizicheskoy-kultury-i-sporta-v-pervoy-polovine-xx-veka",
            "https://cyberleninka.ru/article/n/istoriya-regulirovaniya-fizicheskoy-kultury-i-sporta-v-rossiyskoy-federatsii",
            "https://cyberleninka.ru/article/n/istoriya-regulirovaniya-fizicheskoy-kultury-i-sporta-v-rossiyskoy-imperii-v-period-xviii-nachale-xx-vv",
            "https://cyberleninka.ru/article/n/istoriya-razvitiya-zakonodatelstva-o-fizicheskoy-kulture-i-sporte-v-rossii",
            "https://cyberleninka.ru/article/n/kampaniya-nedelya-za-zdorovuyu-smenu-1928-goda-i-formirovanie-sovetskoy-modeli-fizicheskoy-kultury",
            "https://cyberleninka.ru/article/n/peredacha-gosudarstvennyh-funktsiy-v-sfere-fizicheskoy-kultury-i-sporta-obschestvennym-organizatsiyam-v-1960-e-gg",
            "https://cyberleninka.ru/article/n/razvitie-rossiyskoy-sotsiologii-fizicheskoy-kultury-i-sporta-kak-nauchnogo-napravleniya-i-uchebnoy-distsipliny",
            "https://cyberleninka.ru/article/n/vozniknovenie-i-razvitie-distsipliny-fizicheskaya-kultura-v-vysshih-uchebnyh-zavedeniyah-rossii-istoricheskiy-aspekt",
            "https://cyberleninka.ru/article/n/razvitie-fizicheskoy-kultury-i-sporta-v-kemerovskoy-oblasti-v-1940-1960-h-godah-istochnikovedcheskiy-analiz",
            "https://cyberleninka.ru/article/n/sport-vysokih-dostizheniy-v-kontekste-sovetskoy-politiki-i-ideologii",
            "https://cyberleninka.ru/article/n/istoriya-razvitiya-hokkeya-v-sssr",
            "https://cyberleninka.ru/article/n/istoriya-razvitiya-voleybola-v-rossii",
            "https://cyberleninka.ru/article/n/evolyutsiya-sistemy-sportivnyh-sorevnovaniy-adaptatsionnyy-faktor-sovremennogo-sporta-na-primere-lyzhnyh-gonok",
            "https://cyberleninka.ru/article/n/istoriya-deyatelnosti-federatsii-basketbola",
            "https://cyberleninka.ru/article/n/istoriya-vserossiyskogo-fizkulturno-sportivnogo-kompleksa-gto",
            "https://cyberleninka.ru/article/n/universalnaya-ideologema-sport-v-politicheskom-diskurse-sssr-i-sovremennoy-rossii",
            "https://cyberleninka.ru/article/n/sotsiokulturnye-faktory-poyavleniya-i-deyatelnosti-klubov-lyubiteley-bega-v-sssr",
            "https://cyberleninka.ru/article/n/istoriya-razvitiya-gimnastiki-v-gorode-eltse-konets-xix-nachalo-xxi-vekov",
            "https://cyberleninka.ru/article/n/razvitie-fizicheskoy-kultury-i-sporta-v-tuve",
            "https://cyberleninka.ru/article/n/sportivnoe-pravo",
            "https://cyberleninka.ru/article/n/yuridicheskoe-ponyatie-sporta",
            "https://cyberleninka.ru/article/n/razvitie-pravovoy-nauki-v-chasti-issledovaniya-voprosov-svyazannyh-s-normativnym-regulirovaniem-sporta",
        ],
        "harvester": "cyberleninka_article_list",
        "license_kind": "cc-by-article",
        "license_verified": True,
        "requires_human_approval": False,
        "bench_categories": ["history", "federation-procedures", "methodology"],
    },
    {
        "id": "sport-facts-wikidata-cc0",
        "tier": "A",
        "endpoint": "https://query.wikidata.org/sparql",
        "harvester": "wikidata_sparql",
        "license_kind": "cc0",
        "license_verified": True,
        "requires_human_approval": False,
        "bench_categories": ["history", "rules"],
    },
    {
        "id": "wiki-ru-sport",
        "tier": "A",
        "endpoint": "https://dumps.wikimedia.org/ruwiki/",
        "harvester": "wiki_subset",
        "license_kind": "cc-by-sa",
        "license_verified": True,
        "requires_human_approval": False,
        "bench_categories": ["history", "rules", "biomechanics"],
    },
    {
        "id": "fed-rules",
        "tier": "B",
        "endpoint": "russiabasket.ru, volley.ru, rfs.ru, fhr.ru, russwimming.ru, rusathletics.com, wrestrus.ru, sportgymrus.ru",
        "harvester": "pdf_extract",
        "license_kind": "license-check-required",
        "license_verified": False,
        "requires_human_approval": True,
        "bench_categories": ["rules", "federation-procedures"],
    },
    {
        "id": "sport-history-official-approved",
        "tier": "B",
        "endpoint": [
            "https://rusathletics.info/family/vidyi-idiscziplinyi/istoriya/",
            "https://75.fhr.ru/",
            "https://fhr.ru/news/item/2486/",
            "https://rfs.ru/news/view?id=207338",
            "https://www.rfs.ru/news/207464",
            "https://olympic.ru/news/meeting_roc/stanislav-pozdnyakov-prinyal-uchastie-v-prezentatsii-unikalnoj-antologii-rossijskogo-olimpijskogo-dvizheniya/",
        ],
        "harvester": "official_history_static",
        "license_kind": "human-approved-official-history-public-doc",
        "license_verified": True,
        "requires_human_approval": True,
        "approval_note": "User approved federation and MinSport documents for working corpus on 2026-05-23; official history pages remain internal until release policy is decided",
        "bench_categories": ["history", "federation-procedures"],
    },
    {
        "id": "fed-rules-approved",
        "tier": "B",
        "endpoint": [
            "https://vks.fhr.ru/docs/93/",
        ],
        "harvester": "federation_rules",
        "license_kind": "human-approved-federation-public-doc",
        "license_verified": True,
        "requires_human_approval": True,
        "approval_note": "User approved federation and MinSport documents for working corpus on 2026-05-23",
        "bench_categories": ["rules", "federation-procedures"],
    },
    {
        "id": "fed-rules-volleyball-approved",
        "tier": "B",
        "endpoint": [
            "https://volley.ru/federation/documents/official-volleyball-rules/",
        ],
        "harvester": "federation_rules",
        "license_kind": "human-approved-federation-public-doc",
        "license_verified": True,
        "requires_human_approval": True,
        "approval_note": "User approved federation and MinSport documents for working corpus on 2026-05-23",
        "bench_categories": ["rules", "federation-procedures"],
    },
    {
        "id": "fed-rules-basketball-approved",
        "tier": "B",
        "endpoint": [
            "https://www.russiabasket.ru/Files/Documents/%D0%9E%D1%84%D0%B8%D1%86%D0%B8%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D0%B5%20%D0%9F%D1%80%D0%B0%D0%B2%D0%B8%D0%BB%D0%B0%20%D0%91%D0%B0%D1%81%D0%BA%D0%B5%D1%82%D0%B1%D0%BE%D0%BB%D0%B0%202024%201.0%20%281%29.pdf",
            "https://russiabasket.ru/Files/Documents/%D0%9E%D1%84%D0%B8%D1%86%D0%B8%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D0%B5%20%D0%B8%D0%BD%D1%82%D0%B5%D1%80%D0%BF%D1%80%D0%B5%D1%82%D0%B0%D1%86%D0%B8%D0%B8%202024%20v1.0.pdf",
        ],
        "harvester": "federation_rules",
        "license_kind": "human-approved-federation-public-doc",
        "license_verified": True,
        "requires_human_approval": True,
        "approval_note": "User approved federation and MinSport documents for working corpus on 2026-05-23",
        "bench_categories": ["rules", "federation-procedures"],
    },
    {
        "id": "fed-rules-swimming-approved",
        "tier": "B",
        "endpoint": [
            "https://russwimming.ru/upload/iblock/6d0/ep8saaz1lm4er3cc4iy6t2r2gszq7v1v/Pravila_plavanie_prikaz_Minsport_012026.pdf",
        ],
        "harvester": "federation_rules",
        "license_kind": "human-approved-federation-public-doc",
        "license_verified": True,
        "requires_human_approval": True,
        "approval_note": "User approved federation and MinSport documents for working corpus on 2026-05-23",
        "bench_categories": ["rules", "federation-procedures"],
    },
    {
        "id": "fed-rules-football-approved",
        "tier": "B",
        "endpoint": [
            "https://www.rfs.ru/subject/1/documents/download?documentId=1889",
        ],
        "direct_document": True,
        "endpoint_titles": {
            "https://www.rfs.ru/subject/1/documents/download?documentId=1889": "Правила вида спорта «футбол» (приказ Минспорта России №589 от 22.07.2025)",
        },
        "harvester": "federation_rules",
        "license_kind": "human-approved-federation-public-doc",
        "license_verified": True,
        "requires_human_approval": True,
        "approval_note": "User approved federation and MinSport documents for working corpus on 2026-05-23",
        "bench_categories": ["rules", "federation-procedures"],
    },
    {
        "id": "fed-rules-athletics-approved",
        "tier": "B",
        "endpoint": [
            "https://rusathletics.info/uploads/content/docs/vks/pravila-legkaya-atletika-2023.pdf",
        ],
        "harvester": "federation_rules",
        "license_kind": "human-approved-federation-public-doc",
        "license_verified": True,
        "requires_human_approval": True,
        "approval_note": "User approved federation and MinSport documents for working corpus on 2026-05-23",
        "bench_categories": ["rules", "federation-procedures"],
    },
    {
        "id": "fed-rules-gymnastics-approved",
        "tier": "B",
        "endpoint": [
            "https://sportgymrus.ru/uploads/media_manager/2022/10/pravila-vida-sporta-22sportivnaya-gimnastika22prikaz-minsporta-rf-768-ot-27092022g.pdf",
        ],
        "harvester": "federation_rules",
        "license_kind": "human-approved-federation-public-doc",
        "license_verified": True,
        "requires_human_approval": True,
        "approval_note": "User approved federation and MinSport documents for working corpus on 2026-05-23",
        "bench_categories": ["rules", "federation-procedures"],
    },
    {
        "id": "winter-sports-approved",
        "tier": "B",
        "endpoint": [
            "https://biathlonrus.com/upload/iblock/68e/68e61d0495a02d4cde64607a45a823bd.pdf",
            "https://biathlonrus.com/upload/iblock/b34/v0y14gltax09ai60t2h62koyf495r11i/Dopolneniya-i-izmeneniya-v-Pravila-vida-sporta-biatlon.pdf",
            "https://www.flgr.ru/upload/iblock/c65/kc821wub3qsj0oc8us3l42hna1qecq0r.pdf",
            "https://storage.minsport.gov.ru/cms-uploads/cms/pravila_po_gornolyzhnomu_sportu_dde7aea906.pdf",
            "https://www.fsrussia.ru/files/docs/fs_rules_rus_16_10_24_1025.pdf",
            "https://storage.minsport.gov.ru/cms-uploads/cms/Snoubord_eb967f723d.pdf",
        ],
        "direct_document": True,
        "endpoint_titles": {
            "https://biathlonrus.com/upload/iblock/68e/68e61d0495a02d4cde64607a45a823bd.pdf": "Правила вида спорта «биатлон»",
            "https://biathlonrus.com/upload/iblock/b34/v0y14gltax09ai60t2h62koyf495r11i/Dopolneniya-i-izmeneniya-v-Pravila-vida-sporta-biatlon.pdf": "Дополнения и изменения в правила вида спорта «биатлон»",
            "https://www.flgr.ru/upload/iblock/c65/kc821wub3qsj0oc8us3l42hna1qecq0r.pdf": "Правила вида спорта «лыжные гонки»",
            "https://storage.minsport.gov.ru/cms-uploads/cms/pravila_po_gornolyzhnomu_sportu_dde7aea906.pdf": "Правила вида спорта «горнолыжный спорт»",
            "https://www.fsrussia.ru/files/docs/fs_rules_rus_16_10_24_1025.pdf": "Правила вида спорта «фигурное катание на коньках»",
            "https://storage.minsport.gov.ru/cms-uploads/cms/Snoubord_eb967f723d.pdf": "Положение о межрегиональных и всероссийских официальных спортивных соревнованиях по сноуборду",
        },
        "harvester": "federation_rules",
        "license_kind": "human-approved-federation-public-doc",
        "license_verified": True,
        "requires_human_approval": True,
        "approval_note": "User approved federation and MinSport documents for working corpus on 2026-05-23; winter-sport documents remain internal until release policy is decided",
        "bench_categories": ["rules", "methodology", "federation-procedures"],
    },
    {
        "id": "evsk-ekp",
        "tier": "B",
        "endpoint": "https://minsport.gov.ru/",
        "harvester": "gov_docs",
        "license_kind": "public-domain",
        "license_verified": True,
        "requires_human_approval": False,
        "bench_categories": ["federation-procedures", "rules"],
    },
    {
        "id": "avtoreferaty",
        "tier": "B",
        "endpoint": "https://search.rsl.ru/",
        "harvester": "pdf_extract",
        "license_kind": "public-distribution",
        "license_verified": False,
        "requires_human_approval": False,
        "bench_categories": ["biomechanics", "sport-medicine", "methodology"],
    },
    {
        "id": "pubmed-sport-oa",
        "tier": "C",
        "endpoint": "https://www.ncbi.nlm.nih.gov/pmc/",
        "harvester": "en_pubmed",
        "license_kind": "pmc-open-access",
        "license_verified": False,
        "requires_human_approval": False,
        "translate": "ru",
        "bench_categories": ["sport-medicine", "biomechanics"],
    },
    {
        "id": "cochrane-sport-oa",
        "tier": "C",
        "endpoint": "https://www.cochranelibrary.com/",
        "harvester": "http_static",
        "license_kind": "oa-only",
        "license_verified": False,
        "requires_human_approval": False,
        "translate": "ru",
        "bench_categories": ["sport-medicine"],
    },
    {
        "id": "openstax-physiology",
        "tier": "C",
        "endpoint": "https://openstax.org/details/books/anatomy-and-physiology-2e",
        "harvester": "http_static",
        "license_kind": "cc-by",
        "license_verified": True,
        "requires_human_approval": False,
        "translate": "ru",
        "bench_categories": ["biomechanics", "sport-medicine"],
    },
]


def ensure_sources_file(path: Path) -> None:
    if path.exists():
        return
    path.write_text(json.dumps(DEFAULT_SOURCES, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_sources(path: Path) -> list[dict[str, Any]]:
    ensure_sources_file(path)
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("sources registry must be a list")
    for item in data:
        _validate_source(item)
    return data


def _validate_source(source: dict[str, Any]) -> None:
    required = {"id", "tier", "endpoint", "harvester", "license_kind", "license_verified"}
    missing = required - set(source)
    if missing:
        raise ValueError(f"source {source.get('id', '<unknown>')} missing fields: {sorted(missing)}")
    if source.get("license_kind") == "license-check-required" and not source.get("requires_human_approval"):
        raise ValueError(f"source {source['id']} needs requires_human_approval=true")
