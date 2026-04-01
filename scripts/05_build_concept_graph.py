#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from daozang_kb.builders import build_concept_graph, build_ddj_chapters
from daozang_kb.config import CHAPTER_MD_DIR, DATA_DIR, KG_DIR
from daozang_kb.io_utils import read_json, write_json


def main() -> None:
    chapter_paths = sorted((CHAPTER_MD_DIR / "daodejing").glob("*.tagged.md"))
    chapters_payload = build_ddj_chapters(chapter_paths)
    entity_index = read_json(KG_DIR / "entities" / "entity_index.json")
    concept_graph, concepts = build_concept_graph(chapters_payload, entity_index)

    write_json(DATA_DIR / "daodejing" / "chapters.json", chapters_payload)
    write_json(DATA_DIR / "daodejing" / "concepts.json", concepts)
    write_json(DATA_DIR / "daodejing" / "concept_graph.json", concept_graph)


if __name__ == "__main__":
    main()
