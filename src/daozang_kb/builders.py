from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Iterable

from .annotation import parse_marked_entities, parse_pn_line, strip_annotations, tagged_line_to_segments
from .graphs import build_cooccurrence_links, extract_fable_blocks
from .seeds import (
    CONCEPT_RELATIONS,
    DDJ_CONCEPTS,
    DDJ_IDENTITIES,
    FABLE_THEME_DESCRIPTIONS,
    NANHUA_CHAPTERS,
    NANHUA_FABLES,
)


DDJ_CONCEPT_META = {term: {"category": category, "description": description} for term, category, description in DDJ_CONCEPTS}
DDJ_IDENTITY_META = {term: description for term, description in DDJ_IDENTITIES}
NANHUA_CHAPTER_META = {f"{chapter['order']:02d}_{chapter['name']}": chapter for chapter in NANHUA_CHAPTERS}

CATEGORY_COLORS = {
    "本体": "#5bc0be",
    "修养": "#c9a96e",
    "实践": "#e07040",
    "自然": "#95c17b",
    "治术": "#6b4c9a",
}


def chinese_numeral(number: int) -> str:
    digits = "零一二三四五六七八九"
    if number <= 10:
        return "十" if number == 10 else digits[number]
    if number < 20:
        return f"十{digits[number % 10]}"
    tens, ones = divmod(number, 10)
    result = f"{digits[tens]}十"
    if ones:
        result += digits[ones]
    return result


def load_tagged_chapter(path: Path) -> dict[str, object]:
    lines = path.read_text(encoding="utf-8").splitlines()
    heading = next((line[2:].strip() for line in lines if line.startswith("# ")), path.stem)
    paragraphs = []
    concept_names: list[str] = []
    for line in lines:
        parsed = parse_pn_line(line)
        if parsed is None:
            continue
        pn, content = parsed
        entities = parse_marked_entities(content)
        for entity in entities:
            if entity["type"] == "concept":
                concept_names.append(entity["canonical"])
        paragraphs.append(
            {
                "pn": pn,
                "text": strip_annotations(content),
                "segments": tagged_line_to_segments(content),
                "entities": entities,
            }
        )
    return {
        "heading": heading,
        "paragraphs": paragraphs,
        "concepts": sorted(set(concept_names)),
        "lines": lines,
    }


def infer_ddj_theme(concepts: list[str]) -> str:
    concept_set = set(concepts)
    if {"道", "無", "有"} & concept_set:
        return "道的本体论"
    if {"聖人", "侯王", "百姓"} & concept_set:
        return "圣人与治术"
    if {"水", "柔弱", "不爭"} & concept_set:
        return "柔弱与自然"
    if {"德", "玄德", "常德"} & concept_set:
        return "德的修养论"
    return "道家思想主题"


def build_entity_index(paths: Iterable[Path]) -> tuple[dict[str, object], dict[str, object]]:
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    aliases_by_type: dict[str, dict[str, str]] = defaultdict(dict)
    descriptions = {}
    descriptions.update({term: meta["description"] for term, meta in DDJ_CONCEPT_META.items()})
    descriptions.update(DDJ_IDENTITY_META)

    for path in sorted(paths):
        source = path.parent.name
        chapter_key = path.name.replace(".tagged.md", "")
        lines = path.read_text(encoding="utf-8").splitlines()
        for line in lines:
            parsed = parse_pn_line(line)
            if parsed is None:
                continue
            pn, content = parsed
            for entity in parse_marked_entities(content):
                key = (entity["type"], entity["canonical"])
                if key not in grouped:
                    grouped[key] = {
                        "name": entity["canonical"],
                        "type": entity["type"],
                        "aliases": set(),
                        "refs": [],
                        "frequency": 0,
                        "description": descriptions.get(entity["canonical"], ""),
                        "book_prefix": "ddj" if source == "daodejing" else "nh",
                    }
                grouped[key]["frequency"] += 1
                grouped[key]["refs"].append({"source": source, "chapter": chapter_key, "para": pn})
                grouped[key]["book_prefix"] = "ddj" if source == "daodejing" else grouped[key]["book_prefix"]
                if entity["display"] != entity["canonical"]:
                    grouped[key]["aliases"].add(entity["display"])
                    aliases_by_type[entity["type"]][entity["display"]] = entity["canonical"]

    counters: Counter[str] = Counter()
    entities: dict[str, object] = {}
    for (entity_type, canonical), payload in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
        counters[entity_type] += 1
        entity_id = f"{payload['book_prefix']}_{entity_type}_{counters[entity_type]:03d}"
        entities[entity_id] = {
            "name": canonical,
            "type": entity_type,
            "aliases": sorted(payload["aliases"]),
            "refs": payload["refs"],
            "frequency": payload["frequency"],
            "description": payload["description"],
        }

    by_type = Counter(item["type"] for item in entities.values())
    entity_index = {
        "metadata": {
            "total_entities": len(entities),
            "by_type": dict(sorted(by_type.items())),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "entities": entities,
    }
    disambiguation = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "aliases": {key: dict(sorted(value.items())) for key, value in sorted(aliases_by_type.items())},
    }
    return entity_index, disambiguation


def build_ddj_chapters(paths: Iterable[Path]) -> dict[str, object]:
    chapters = []
    total_chars = 0
    for path in sorted(paths):
        chapter_id = path.name.replace(".tagged.md", "")
        parsed = load_tagged_chapter(path)
        text = "\n".join(paragraph["text"] for paragraph in parsed["paragraphs"])
        char_count = len(text.replace("\n", ""))
        total_chars += char_count
        number = int(chapter_id)
        chapters.append(
            {
                "id": chapter_id,
                "number": number,
                "title": f"第{chinese_numeral(number)}章",
                "text_traditional": text,
                "paragraphs": parsed["paragraphs"],
                "concepts": parsed["concepts"],
                "theme": infer_ddj_theme(parsed["concepts"]),
                "char_count": char_count,
            }
        )

    return {
        "metadata": {
            "title": "道德經",
            "author": "老子",
            "total_chapters": len(chapters),
            "total_chars": total_chars,
            "source": "ctext.org (繁體)",
        },
        "chapters": chapters,
    }


def build_concept_graph(chapters_payload: dict[str, object], entity_index: dict[str, object]) -> tuple[dict[str, object], list[dict[str, object]]]:
    chapters = chapters_payload["chapters"]
    entity_lookup = {
        payload["name"]: payload
        for payload in entity_index["entities"].values()
        if payload["type"] == "concept"
    }
    present_concepts = sorted({concept for chapter in chapters for concept in chapter["concepts"]})

    nodes = []
    category_map: dict[str, list[str]] = defaultdict(list)
    for concept in present_concepts:
        meta = DDJ_CONCEPT_META.get(concept, {"category": "本体", "description": ""})
        refs = entity_lookup.get(concept, {}).get("refs", [])
        key_quotes = []
        for ref in refs[:3]:
            chapter = next((item for item in chapters if item["id"] == ref["chapter"]), None)
            if chapter is None:
                continue
            paragraph = next((item for item in chapter["paragraphs"] if item["pn"] == ref["para"]), None)
            if paragraph is None:
                continue
            key_quotes.append({"chapter": int(chapter["id"]), "text": paragraph["text"]})
        nodes.append(
            {
                "id": concept,
                "name": concept,
                "category": meta["category"],
                "frequency": entity_lookup.get(concept, {}).get("frequency", 0),
                "chapters": sorted({int(ref["chapter"]) for ref in refs if ref["source"] == "daodejing"}),
                "description": meta["description"],
                "key_quotes": key_quotes,
            }
        )
        category_map[meta["category"]].append(concept)

    base_links = build_cooccurrence_links(
        [{"chapter": chapter["id"], "concepts": chapter["concepts"]} for chapter in chapters]
    )
    link_map = {(link["source"], link["target"]): link for link in base_links}
    for (left, right), relation_type in CONCEPT_RELATIONS.items():
        if left not in present_concepts or right not in present_concepts:
            continue
        key = tuple(sorted((left, right)))
        if key not in link_map:
            link_map[key] = {
                "source": key[0],
                "target": key[1],
                "type": relation_type,
                "weight": 1,
                "co_chapters": [],
            }
        else:
            link_map[key]["type"] = relation_type
    links = sorted(link_map.values(), key=lambda item: (-item["weight"], item["source"], item["target"]))

    categories = {
        category: {"color": CATEGORY_COLORS.get(category, "#5bc0be"), "concepts": sorted(concepts)}
        for category, concepts in sorted(category_map.items())
    }
    concepts = [
        {
            "name": node["name"],
            "category": node["category"],
            "frequency": node["frequency"],
            "description": node["description"],
        }
        for node in sorted(nodes, key=lambda item: (-item["frequency"], item["name"]))
    ]
    return {"nodes": nodes, "links": links, "categories": categories}, concepts


def build_nanhua_chapters(paths: Iterable[Path]) -> dict[str, object]:
    chapters = []
    total_chars = 0
    for path in sorted(paths):
        chapter_id = path.name.replace(".tagged.md", "")
        parsed = load_tagged_chapter(path)
        meta = NANHUA_CHAPTER_META[chapter_id]
        text = "\n\n".join(paragraph["text"] for paragraph in parsed["paragraphs"])
        char_count = len(text.replace("\n", ""))
        total_chars += char_count
        chapters.append(
            {
                "id": chapter_id,
                "number": meta["order"],
                "title": meta["name"],
                "section": meta["section"],
                "text_traditional": text,
                "paragraphs": parsed["paragraphs"],
                "concepts": parsed["concepts"],
                "char_count": char_count,
                "annotated": True,
            }
        )
    return {
        "metadata": {
            "title": "南華真經",
            "author": "莊周",
            "total_chapters": len(chapters),
            "annotated_chapters": len(chapters),
            "total_chars": total_chars,
            "source": "ctext.org (繁體)",
        },
        "chapters": chapters,
    }


def build_fable_graph(paths: Iterable[Path]) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    fables: list[dict[str, object]] = []
    character_map: dict[str, dict[str, object]] = {}
    theme_map: dict[str, dict[str, object]] = {}
    links: list[dict[str, object]] = []

    for path in sorted(paths):
        chapter_id = path.name.replace(".tagged.md", "")
        lines = path.read_text(encoding="utf-8").splitlines()
        chapter_meta = NANHUA_CHAPTER_META[chapter_id]
        blocks = extract_fable_blocks(lines, chapter_id, chapter_meta["section"])
        expected = {item["name"]: item for item in NANHUA_FABLES.get(chapter_id, [])}
        for index, block in enumerate(blocks, start=1):
            record = expected.get(block["name"], {"themes": []})
            characters = []
            for line in block.get("tagged_lines", []):
                for entity in parse_marked_entities(line):
                    if entity["type"] not in {"person", "creature"}:
                        continue
                    if entity["canonical"] not in characters:
                        characters.append(entity["canonical"])
            fable_id = f"f{len(fables) + 1:03d}"
            opening_quote = block["lines"][0] if block["lines"] else ""
            fable_entry = {
                "id": fable_id,
                "name": block["name"],
                "chapter": chapter_id,
                "section": chapter_meta["section"],
                "para_range": block["para_range"],
                "characters": characters,
                "themes": record["themes"],
                "opening_quote": opening_quote,
                "char_count": len("".join(block["lines"])),
            }
            fables.append(fable_entry)
            for character in characters:
                if character not in character_map:
                    character_map[character] = {
                        "id": f"c{len(character_map) + 1:03d}",
                        "name": character,
                        "type": "寓言角色",
                        "aliases": [],
                        "fable_ids": [],
                        "fable_count": 0,
                        "chapters": set(),
                        "description": "",
                    }
                character_map[character]["fable_ids"].append(fable_id)
                character_map[character]["fable_count"] += 1
                character_map[character]["chapters"].add(chapter_id)
                links.append({"source": character_map[character]["id"], "target": fable_id, "type": "出场"})

            for theme in record["themes"]:
                if theme not in theme_map:
                    theme_map[theme] = {
                        "id": f"t{len(theme_map) + 1:03d}",
                        "name": theme,
                        "fable_ids": [],
                        "description": FABLE_THEME_DESCRIPTIONS.get(theme, ""),
                    }
                theme_map[theme]["fable_ids"].append(fable_id)

            if {"莊周", "惠施"} <= set(characters) or {"莊子", "惠子"} <= set(characters):
                left = character_map.get("莊周") or character_map.get("莊子")
                right = character_map.get("惠施") or character_map.get("惠子")
                if left and right:
                    links.append({"source": left["id"], "target": right["id"], "type": "辩论", "fable_ids": [fable_id]})

    for left, right in combinations(fables, 2):
        shared = sorted(set(left["themes"]) & set(right["themes"]))
        if shared:
            links.append({"source": left["id"], "target": right["id"], "type": "主题关联", "theme": shared[0]})

    characters = []
    for payload in character_map.values():
        payload["chapters"] = sorted(payload["chapters"])
        characters.append(payload)
    themes = list(theme_map.values())
    graph = {
        "fables": fables,
        "characters": characters,
        "themes": themes,
        "links": links,
    }
    return graph, fables, characters


def build_site_stats(ddj_chapters: dict[str, object], concept_graph: dict[str, object], nanhua_chapters: dict[str, object], fable_graph: dict[str, object]) -> dict[str, object]:
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "daodejing": {
            "chapters": ddj_chapters["metadata"]["total_chapters"],
            "concepts": len(concept_graph["nodes"]),
            "chars": ddj_chapters["metadata"]["total_chars"],
        },
        "nanhua": {
            "chapters": nanhua_chapters["metadata"]["total_chapters"],
            "annotated_chapters": nanhua_chapters["metadata"]["annotated_chapters"],
            "fables": len(fable_graph["fables"]),
            "chars": nanhua_chapters["metadata"]["total_chars"],
        },
    }
