#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from daozang_kb.annotation import parse_pn_line
from daozang_kb.config import ARCHIVE_DIR, CHAPTER_MD_DIR, COLLATION_DIR, DATA_DIR, KG_DIR
from daozang_kb.graphs import extract_fable_blocks
from daozang_kb.io_utils import ensure_dir, read_json, read_text, write_text
from daozang_kb.validation import check_text_integrity, contains_nested_annotations, validate_pn_sequence


def validate_markdown() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for path in sorted(CHAPTER_MD_DIR.glob("**/*.tagged.md")):
        chapter_key = path.name.replace(".tagged.md", "")
        lines = path.read_text(encoding="utf-8").splitlines()
        ok, message = validate_pn_sequence(lines)
        if not ok:
            errors.append(f"{path.relative_to(ROOT)}: {message}")

        for line in lines:
            if contains_nested_annotations(line):
                errors.append(f"{path.relative_to(ROOT)}: 检测到疑似嵌套标注")
                break

        if path.parent.name == "daodejing":
            archive_path = ARCHIVE_DIR / "daodejing" / "chapters" / f"{chapter_key}.txt"
            archive_lines = read_text(archive_path).splitlines()
            archive_text = "\n".join(line.strip() for line in archive_lines[1:] if line.strip())
        else:
            archive_path = ARCHIVE_DIR / "nanhua" / "chapters" / f"{chapter_key}.txt"
            archive_lines = read_text(archive_path).splitlines()
            blocks = []
            current = []
            for line in archive_lines[2:]:
                if line.strip():
                    current.append(line.strip())
                elif current:
                    blocks.append("".join(current))
                    current = []
            if current:
                blocks.append("".join(current))
            archive_text = "\n".join(blocks)

        ok, message = check_text_integrity(lines, archive_text)
        if not ok:
            errors.append(f"{path.relative_to(ROOT)}: {message}")

        if path.parent.name == "nanhua":
            chapter_id = path.name.replace(".tagged.md", "")
            blocks = extract_fable_blocks(lines, chapter_id, "")
            if not blocks:
                warnings.append(f"{path.relative_to(ROOT)}: 尚未识别到 fable 区块")
    return errors, warnings


def validate_json() -> list[str]:
    errors: list[str] = []
    required = [
        KG_DIR / "entities" / "entity_index.json",
        KG_DIR / "entities" / "disambiguation.json",
        KG_DIR / "relations" / "relations.json",
        DATA_DIR / "daodejing" / "chapters.json",
        DATA_DIR / "daodejing" / "concept_graph.json",
        DATA_DIR / "nanhua" / "chapters.json",
        DATA_DIR / "nanhua" / "fable_graph.json",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"缺少文件：{path.relative_to(ROOT)}")
    if errors:
        return errors

    ddj_chapters = read_json(DATA_DIR / "daodejing" / "chapters.json")
    concept_graph = read_json(DATA_DIR / "daodejing" / "concept_graph.json")
    nanhua_chapters = read_json(DATA_DIR / "nanhua" / "chapters.json")
    fable_graph = read_json(DATA_DIR / "nanhua" / "fable_graph.json")
    entity_index = read_json(KG_DIR / "entities" / "entity_index.json")

    if "chapters" not in ddj_chapters or "metadata" not in ddj_chapters:
        errors.append("data/daodejing/chapters.json 缺少 metadata 或 chapters")
    if "nodes" not in concept_graph or "links" not in concept_graph:
        errors.append("data/daodejing/concept_graph.json 缺少 nodes 或 links")
    if "chapters" not in nanhua_chapters:
        errors.append("data/nanhua/chapters.json 缺少 chapters")
    if "fables" not in fable_graph or "links" not in fable_graph:
        errors.append("data/nanhua/fable_graph.json 缺少 fables 或 links")
    if "entities" not in entity_index:
        errors.append("kg/entities/entity_index.json 缺少 entities")

    ddj_ids = {chapter["id"] for chapter in ddj_chapters["chapters"]}
    for node in concept_graph["nodes"]:
        for chapter in node.get("chapters", []):
            if f"{chapter:03d}" not in ddj_ids:
                errors.append(f"concept_graph 节点 {node['name']} 引用了不存在的章节 {chapter}")

    fable_names = {fable["name"] for fable in fable_graph["fables"]}
    for path in sorted((CHAPTER_MD_DIR / "nanhua").glob("*.tagged.md")):
        chapter_id = path.name.replace(".tagged.md", "")
        blocks = extract_fable_blocks(path.read_text(encoding="utf-8").splitlines(), chapter_id, "")
        for block in blocks:
            if block["name"] not in fable_names:
                errors.append(f"{path.relative_to(ROOT)}: fable 区块 {block['name']} 未进入 fable_graph.json")

    return errors


def main() -> None:
    ensure_dir(COLLATION_DIR)
    md_errors, md_warnings = validate_markdown()
    json_errors = validate_json()
    errors = md_errors + json_errors

    lines = ["# 校验报告", ""]
    if errors:
        lines.append("## 错误")
        lines.extend(f"- {item}" for item in errors)
        lines.append("")
    else:
        lines.append("## 错误")
        lines.append("- 无")
        lines.append("")

    if md_warnings:
        lines.append("## 警告")
        lines.extend(f"- {item}" for item in md_warnings)
        lines.append("")

    report_path = COLLATION_DIR / "validation_report.md"
    write_text(report_path, "\n".join(lines) + "\n")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
