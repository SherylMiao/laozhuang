#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from daozang_kb.builders import build_entity_index
from daozang_kb.config import CHAPTER_MD_DIR, KG_DIR
from daozang_kb.io_utils import write_json


def main() -> None:
    paths = list(CHAPTER_MD_DIR.glob("**/*.tagged.md"))
    entity_index, disambiguation = build_entity_index(paths)
    write_json(KG_DIR / "entities" / "entity_index.json", entity_index)
    write_json(KG_DIR / "entities" / "disambiguation.json", disambiguation)


if __name__ == "__main__":
    main()
