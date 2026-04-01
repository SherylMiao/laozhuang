#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from daozang_kb.annotation import text_to_paragraphs
from daozang_kb.config import ARCHIVE_DIR, CHAPTER_MD_DIR
from daozang_kb.io_utils import ensure_dir, read_text, write_text


def split_daodejing() -> None:
    output_dir = CHAPTER_MD_DIR / "daodejing"
    ensure_dir(output_dir)
    for path in sorted((ARCHIVE_DIR / "daodejing" / "chapters").glob("*.txt")):
        lines = read_text(path).splitlines()
        chapter_number = int(lines[0])
        text = "".join(line.strip() for line in lines[1:] if line.strip())
        paragraphs = text_to_paragraphs(text, strategy="sentence")
        heading = f"# 第{chapter_number}章"
        content = "\n".join([heading, ""] + paragraphs) + "\n"
        write_text(output_dir / f"{path.stem}.tagged.md", content)


def split_nanhua() -> None:
    output_dir = CHAPTER_MD_DIR / "nanhua"
    ensure_dir(output_dir)
    for path in sorted((ARCHIVE_DIR / "nanhua" / "chapters").glob("*.txt")):
        lines = read_text(path).splitlines()
        title = lines[0].strip()
        section = lines[1].strip()
        body_lines = lines[2:]
        blocks = []
        current = []
        for line in body_lines:
            if line.strip():
                current.append(line.strip())
            elif current:
                blocks.append("".join(current))
                current = []
        if current:
            blocks.append("".join(current))

        paragraphs = [f"[{index}] {block}" for index, block in enumerate(blocks, start=1)]
        heading = f"# {title}（{section}）"
        content = "\n".join([heading, ""] + paragraphs) + "\n"
        write_text(output_dir / f"{path.stem}.tagged.md", content)


if __name__ == "__main__":
    split_daodejing()
    split_nanhua()
