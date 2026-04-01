#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from daozang_kb.config import ARCHIVE_DIR, KG_DIR, DAOZANG_ONTOLOGY
from daozang_kb.fetchers import fetch_daodejing_api, fetch_nanhua_chapters
from daozang_kb.io_utils import ensure_dir, write_json, write_text


def write_daodejing() -> None:
    ensure_dir(ARCHIVE_DIR / "daodejing" / "chapters")
    chapters = fetch_daodejing_api()
    write_text(ARCHIVE_DIR / "daodejing" / "ctext_raw.txt", "\n\n".join(chapters) + "\n")
    for index, content in enumerate(chapters, start=1):
        write_text(
            ARCHIVE_DIR / "daodejing" / "chapters" / f"{index:03d}.txt",
            f"{index:03d}\n{content.strip()}\n",
        )


def write_nanhua(delay: float) -> None:
    ensure_dir(ARCHIVE_DIR / "nanhua" / "chapters")
    chapters = fetch_nanhua_chapters(delay_seconds=delay)
    raw_chunks = []
    for chapter in chapters:
        chapter_id = f"{chapter['order']:02d}_{chapter['name']}"
        text_body = "\n\n".join(chapter["rows"])
        raw_chunks.append(f"## {chapter['name']}（{chapter['section']}）\n{text_body}")
        write_text(
            ARCHIVE_DIR / "nanhua" / "chapters" / f"{chapter_id}.txt",
            f"{chapter['name']}\n{chapter['section']}\n{text_body}\n",
        )
    write_text(ARCHIVE_DIR / "nanhua" / "ctext_raw.txt", "\n\n".join(raw_chunks) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="抓取 ctext《道德经》与《南华真经》文本。")
    parser.add_argument("--book", choices=["all", "daodejing", "nanhua"], default="all")
    parser.add_argument("--delay", type=float, default=0.5, help="抓取《南华真经》页面时的请求间隔秒数。")
    args = parser.parse_args()

    ensure_dir(KG_DIR / "ontology")
    write_json(KG_DIR / "ontology" / "daozang_ontology.json", DAOZANG_ONTOLOGY)

    if args.book in {"all", "daodejing"}:
        write_daodejing()
    if args.book in {"all", "nanhua"}:
        write_nanhua(args.delay)


if __name__ == "__main__":
    main()
