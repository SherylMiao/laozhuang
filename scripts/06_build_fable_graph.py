#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from daozang_kb.builders import build_fable_graph, build_nanhua_chapters
from daozang_kb.config import CHAPTER_MD_DIR, DATA_DIR, KG_DIR
from daozang_kb.io_utils import read_json, write_json


def main() -> None:
    all_paths = sorted((CHAPTER_MD_DIR / "nanhua").glob("*.tagged.md"))

    chapters_payload = build_nanhua_chapters(all_paths)
    fable_graph, fables, characters = build_fable_graph(all_paths)

    write_json(DATA_DIR / "nanhua" / "chapters.json", chapters_payload)
    write_json(DATA_DIR / "nanhua" / "fables.json", fables)
    write_json(DATA_DIR / "nanhua" / "characters.json", characters)
    write_json(DATA_DIR / "nanhua" / "fable_graph.json", fable_graph)

    relations = []
    concept_graph_path = DATA_DIR / "daodejing" / "concept_graph.json"
    if concept_graph_path.exists():
        concept_graph = read_json(concept_graph_path)
        for link in concept_graph["links"]:
            relations.append(
                {
                    "id": f"{link['source']}_{link['type']}_{link['target']}",
                    "source": link["source"],
                    "target": link["target"],
                    "type": link["type"],
                }
            )
    for link in fable_graph["links"]:
        relations.append(
            {
                "id": f"{link['source']}_{link['type']}_{link['target']}",
                "source": link["source"],
                "target": link["target"],
                "type": link["type"],
            }
        )
    write_json(
        KG_DIR / "relations" / "relations.json",
        {"generated_at": datetime.now().isoformat(timespec="seconds"), "relations": relations},
    )


if __name__ == "__main__":
    main()
