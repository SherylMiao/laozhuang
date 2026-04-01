from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from .annotation import parse_pn_line, strip_annotations


def build_cooccurrence_links(chapters: list[dict[str, object]]) -> list[dict[str, object]]:
    pair_map: dict[tuple[str, str], dict[str, object]] = {}
    for chapter in chapters:
        concepts = sorted(set(chapter.get("concepts", [])))
        chapter_id = str(chapter["chapter"])
        for left, right in combinations(concepts, 2):
            key = (left, right)
            if key not in pair_map:
                pair_map[key] = {
                    "source": left,
                    "target": right,
                    "type": "共现",
                    "weight": 0,
                    "co_chapters": [],
                }
            pair_map[key]["weight"] += 1
            pair_map[key]["co_chapters"].append(chapter_id)
    for item in pair_map.values():
        item["co_chapters"] = sorted(set(item["co_chapters"]))
    return sorted(pair_map.values(), key=lambda item: (-item["weight"], item["source"], item["target"]))


def extract_fable_blocks(lines: list[str], chapter_id: str, section: str) -> list[dict[str, object]]:
    blocks: list[dict[str, object]] = []
    current_name: str | None = None
    current_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("::: fable "):
            current_name = stripped.replace("::: fable ", "", 1).strip()
            current_lines = []
            continue
        if stripped == ":::" and current_name:
            para_numbers = []
            text_lines = []
            tagged_lines = []
            for content_line in current_lines:
                parsed = parse_pn_line(content_line)
                if parsed is None:
                    continue
                pn, content = parsed
                para_numbers.append(pn)
                text_lines.append(strip_annotations(content))
                tagged_lines.append(content)
            if para_numbers:
                blocks.append(
                    {
                        "name": current_name,
                        "chapter": chapter_id,
                        "section": section,
                        "para_range": f"{para_numbers[0]}-{para_numbers[-1]}",
                        "lines": text_lines,
                        "tagged_lines": tagged_lines,
                    }
                )
            current_name = None
            current_lines = []
            continue
        if current_name:
            current_lines.append(stripped)
    return blocks
