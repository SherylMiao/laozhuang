from __future__ import annotations

import re

from .annotation import parse_pn_line, strip_annotations


def validate_pn_sequence(lines: list[str]) -> tuple[bool, str]:
    expected = 1
    for line in lines:
        parsed = parse_pn_line(line)
        if parsed is None:
            continue
        pn, _ = parsed
        if "." in pn:
            continue
        if int(pn) != expected:
            return False, f"PN 不连续：期望 [{expected}]，实际 [{pn}]"
        expected += 1
    return True, ""


def check_text_integrity(tagged_lines: list[str], archive_text: str) -> tuple[bool, str]:
    normalized_tagged: list[str] = []
    for line in tagged_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(":::"):
            continue
        parsed = parse_pn_line(stripped)
        if parsed is None:
            continue
        _, content = parsed
        normalized_tagged.append(strip_annotations(content))
    candidate = "".join(normalized_tagged).strip()
    expected = archive_text.replace("\n", "").strip()
    if candidate != expected:
        return False, "去标记后的文本与 archive 底本不一致"
    return True, ""


def contains_nested_annotations(line: str) -> bool:
    stripped = re.sub(r"〖[^〖〗]+〗", "", line)
    return "〖" in stripped or "〗" in stripped
