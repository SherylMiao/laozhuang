#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from daozang_kb.annotation import annotate_text, inject_fable_markers, parse_pn_line, strip_annotations
from daozang_kb.config import CHAPTER_MD_DIR
from daozang_kb.io_utils import write_text
from daozang_kb.seeds import NANHUA_FABLES, build_ddj_lexicon, build_nanhua_lexicon


def normalize_lines(lines: list[str]) -> list[str]:
    normalized = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(":::"):
            continue
        parsed = parse_pn_line(line)
        if parsed is None:
            normalized.append(line.rstrip())
            continue
        pn, content = parsed
        normalized.append(f"[{pn}] {strip_annotations(content)}")
    return normalized


def annotate_file(path: Path, lexicon: list[dict[str, str]]) -> list[str]:
    lines = normalize_lines(path.read_text(encoding="utf-8").splitlines())
    output = []
    for line in lines:
        parsed = parse_pn_line(line)
        if parsed is None:
            output.append(line)
            continue
        pn, content = parsed
        output.append(f"[{pn}] {annotate_text(content, lexicon)}")
    return output


def annotate_daodejing() -> None:
    lexicon = build_ddj_lexicon()
    for path in sorted((CHAPTER_MD_DIR / "daodejing").glob("*.tagged.md")):
        lines = annotate_file(path, lexicon)
        write_text(path, "\n".join(lines) + "\n")


def annotate_nanhua() -> None:
    lexicon = build_nanhua_lexicon()
    for path in sorted((CHAPTER_MD_DIR / "nanhua").glob("*.tagged.md")):
        chapter_id = path.name.replace(".tagged.md", "")
        title = chapter_id.split("_", 1)[1]
        lines = annotate_file(path, lexicon)
        rendered = inject_fable_markers(lines, NANHUA_FABLES.get(chapter_id, []), fallback_name=title)
        write_text(path, "\n".join(rendered) + "\n")


if __name__ == "__main__":
    annotate_daodejing()
    annotate_nanhua()
