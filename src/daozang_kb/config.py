from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_DIR = ROOT / "archive"
CHAPTER_MD_DIR = ROOT / "chapter_md"
KG_DIR = ROOT / "kg"
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
COLLATION_DIR = ROOT / "collation_reports"

ENTITY_TYPE_TO_PREFIX = {
    "person": "@",
    "deity": "?",
    "place": "=",
    "concept": "~",
    "scripture": "{",
    "identity": "#",
    "school": "&",
    "creature": "+",
    "object": "•",
    "quantity": "$",
}

PREFIX_TO_ENTITY_TYPE = {value: key for key, value in ENTITY_TYPE_TO_PREFIX.items()}

DAOZANG_ONTOLOGY = {
    "version": "1.0",
    "project": "daozang-kb",
    "scope": ["道德经", "南华真经"],
    "entity_types": {
        "person": {"prefix": "@", "color": "#c9a96e", "label": "人物"},
        "deity": {"prefix": "?", "color": "#d4a0d0", "label": "神灵"},
        "place": {"prefix": "=", "color": "#7eb8da", "label": "地名"},
        "concept": {"prefix": "~", "color": "#5bc0be", "label": "核心概念"},
        "scripture": {"prefix": "{", "color": "#4a8c6f", "label": "经典"},
        "identity": {"prefix": "#", "color": "#e8a87c", "label": "身份"},
        "school": {"prefix": "&", "color": "#6b4c9a", "label": "学派"},
        "creature": {"prefix": "+", "color": "#95c17b", "label": "生物"},
        "object": {"prefix": "•", "color": "#e07040", "label": "器物"},
        "quantity": {"prefix": "$", "color": "#aaaaaa", "label": "数量"},
    },
    "relation_types": {
        "对立": {"desc": "概念对立（有↔无, 大↔小）"},
        "蕴含": {"desc": "概念蕴含（道→无为）"},
        "共现": {"desc": "同一章节/段落中共同出现"},
        "师承": {"desc": "A 为 B 之师"},
        "互文": {"desc": "不同经典间的文本互引"},
        "出场": {"desc": "人物在寓言中出场"},
        "主题关联": {"desc": "寓言共享主题"},
        "引用": {"desc": "A 引用/论及 B"},
        "辩论": {"desc": "A 与 B 辩论"},
        "注释": {"desc": "A 注释/阐发 B"},
    },
}
