from __future__ import annotations

import re
from typing import Iterable

from .config import ENTITY_TYPE_TO_PREFIX, PREFIX_TO_ENTITY_TYPE


ANNOTATION_RE = re.compile(r"〖([@?=~{#&+\$•])([^〖〗|]+)(?:\|([^〖〗]+))?〗")
PN_RE = re.compile(r"^\[(\d+(?:\.\d+)*)\]\s*(.*)$")
FABLE_MATCH_RE = re.compile(r"[\s，。、「」『』！？；：、（）《》〈〉“”‘’·—…,.!?;:'\"-]+")
FABLE_VARIANTS = str.maketrans(
    {
        "机": "幾",
        "几": "幾",
        "無": "无",
        "无": "无",
        "為": "为",
        "为": "为",
        "與": "与",
        "与": "与",
        "樂": "乐",
        "乐": "乐",
        "黃": "黄",
        "黄": "黄",
        "雲": "云",
        "云": "云",
    }
)


def strip_annotations(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        display = match.group(2)
        return display

    return ANNOTATION_RE.sub(repl, text)


def _sorted_lexicon(lexicon: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(
        lexicon,
        key=lambda item: (len(item["term"]), item["term"]),
        reverse=True,
    )


def annotate_text(text: str, lexicon: Iterable[dict[str, str]]) -> str:
    lexicon_items = _sorted_lexicon(lexicon)
    if not lexicon_items:
        return text

    by_first_char: dict[str, list[dict[str, str]]] = {}
    for item in lexicon_items:
        by_first_char.setdefault(item["term"][0], []).append(item)

    output: list[str] = []
    index = 0
    while index < len(text):
        candidates = by_first_char.get(text[index], [])
        chosen: dict[str, str] | None = None
        for candidate in candidates:
            term = candidate["term"]
            if text.startswith(term, index):
                chosen = candidate
                break

        if chosen is None:
            output.append(text[index])
            index += 1
            continue

        prefix = ENTITY_TYPE_TO_PREFIX[chosen["type"]]
        display = chosen["term"]
        canonical = chosen.get("canonical", display)
        if canonical != display:
            output.append(f"〖{prefix}{display}|{canonical}〗")
        else:
            output.append(f"〖{prefix}{display}〗")
        index += len(display)
    return "".join(output)


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", "", text)
    segments: list[str] = []
    current = []
    for char in normalized:
        current.append(char)
        if char in "。！？":
            segment = "".join(current).strip()
            if segment:
                segments.append(segment)
            current = []
    tail = "".join(current).strip()
    if tail:
        segments.append(tail)
    return segments


def text_to_paragraphs(text: str, strategy: str = "sentence") -> list[str]:
    if strategy != "sentence":
        raise ValueError(f"Unsupported strategy: {strategy}")
    paragraphs = split_sentences(text)
    return [f"[{index}] {paragraph}" for index, paragraph in enumerate(paragraphs, start=1)]


def parse_marked_entities(text: str) -> list[dict[str, str]]:
    entities: list[dict[str, str]] = []
    for match in ANNOTATION_RE.finditer(text):
        prefix, display, canonical = match.groups()
        entities.append(
            {
                "type": PREFIX_TO_ENTITY_TYPE[prefix],
                "display": display,
                "canonical": canonical or display,
                "raw": match.group(0),
            }
        )
    return entities


def tagged_line_to_segments(text: str) -> list[dict[str, str | bool]]:
    segments: list[dict[str, str | bool]] = []
    cursor = 0
    for match in ANNOTATION_RE.finditer(text):
        start, end = match.span()
        if start > cursor:
            segments.append({"text": text[cursor:start], "highlight": False})
        prefix, display, canonical = match.groups()
        segments.append(
            {
                "text": display,
                "highlight": True,
                "entity_type": PREFIX_TO_ENTITY_TYPE[prefix],
                "canonical": canonical or display,
            }
        )
        cursor = end
    if cursor < len(text):
        segments.append({"text": text[cursor:], "highlight": False})
    return segments


def parse_pn_line(line: str) -> tuple[str, str] | None:
    match = PN_RE.match(line.strip())
    if not match:
        return None
    return match.group(1), match.group(2)


def normalize_fable_match(text: str) -> str:
    return FABLE_MATCH_RE.sub("", text).translate(FABLE_VARIANTS)


def inject_fable_markers(
    lines: list[str],
    fables: list[dict[str, object]],
    fallback_name: str | None = None,
) -> list[str]:
    rendered: list[str] = []
    pointer = 0
    open_block = False
    matched_any = False

    for line in lines:
        parsed = parse_pn_line(line)
        if parsed is not None and pointer < len(fables):
            _, content = parsed
            plain = strip_annotations(content)
            current = fables[pointer]
            start = str(current.get("start", ""))
            if start and normalize_fable_match(start) in normalize_fable_match(plain):
                if open_block:
                    rendered.append(":::")
                rendered.append(f"::: fable {current['name']}")
                open_block = True
                matched_any = True
                pointer += 1
        rendered.append(line)

    if open_block:
        rendered.append(":::")

    if matched_any or not fallback_name:
        return rendered

    fallback_opened = False
    wrapped: list[str] = []
    for line in lines:
        if not fallback_opened and parse_pn_line(line) is not None:
            wrapped.append(f"::: fable {fallback_name}")
            fallback_opened = True
        wrapped.append(line)
    if fallback_opened:
        wrapped.append(":::")
        return wrapped
    return rendered
