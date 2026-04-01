#!/usr/bin/env python3
from __future__ import annotations

import html
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from daozang_kb.builders import build_site_stats
from daozang_kb.config import DATA_DIR, DOCS_DIR
from daozang_kb.io_utils import ensure_dir, read_json, write_json, write_text


def render_segments(segments: list[dict[str, object]]) -> str:
    parts = []
    for segment in segments:
        text = html.escape(str(segment["text"]))
        if not segment.get("highlight"):
            parts.append(text)
            continue
        entity_type = segment["entity_type"]
        canonical = html.escape(str(segment.get("canonical", segment["text"])))
        parts.append(
            f'<span class="entity entity-{entity_type}" data-entity-type="{entity_type}" data-canonical="{canonical}">{text}</span>'
        )
    return "".join(parts)


def render_book(book: str, payload: dict[str, object]) -> None:
    output_dir = DOCS_DIR / "reader" / "rendered" / book
    ensure_dir(output_dir)
    for chapter in payload["chapters"]:
        body = []
        for paragraph in chapter["paragraphs"]:
            rendered = render_segments(paragraph["segments"])
            body.append(f'<p><a id="pn-{paragraph["pn"]}" class="pn">[{paragraph["pn"]}]</a> {rendered}</p>')
        write_text(
            output_dir / f'{chapter["id"]}.html',
            "\n".join(
                [
                    '<article class="reader-article">',
                    f"<h2>{chapter['title']}</h2>",
                    *body,
                    "</article>",
                ]
            )
            + "\n",
        )


def main() -> None:
    ddj = read_json(DATA_DIR / "daodejing" / "chapters.json")
    concept_graph = read_json(DATA_DIR / "daodejing" / "concept_graph.json")
    nanhua = read_json(DATA_DIR / "nanhua" / "chapters.json")
    fable_graph = read_json(DATA_DIR / "nanhua" / "fable_graph.json")

    render_book("daodejing", ddj)
    render_book("nanhua", nanhua)
    write_json(DATA_DIR / "site_stats.json", build_site_stats(ddj, concept_graph, nanhua, fable_graph))


if __name__ == "__main__":
    main()
