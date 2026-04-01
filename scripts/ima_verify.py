#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from daozang_kb.config import COLLATION_DIR
from daozang_kb.io_utils import ensure_dir, write_text


KB_ID = "zv9KcCrcRfhppiGq3s465KGhXtURjn85psgkzZM2vTM="
URL = "https://ima.qq.com/openapi/wiki/v1/search_knowledge"


def read_secret(name: str, file_name: str) -> str:
    if os.environ.get(name):
        return os.environ[name]
    path = Path.home() / ".config" / "ima" / file_name
    return path.read_text(encoding="utf-8").strip()


def search(query: str, client_id: str, api_key: str) -> dict[str, object]:
    payload = json.dumps({"query": query, "knowledge_base_id": KB_ID}).encode("utf-8")
    request = Request(
        URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "ima-openapi-clientid": client_id,
            "ima-openapi-apikey": api_key,
        },
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    ensure_dir(COLLATION_DIR)
    report_path = COLLATION_DIR / "ima_verify_report.md"
    queries = [
        "道可道非常道",
        "天下皆知美之為美",
        "治大國若烹小鮮",
        "北冥有魚",
        "庖丁為文惠君解牛",
        "昔者莊周夢為蝴蝶",
    ]
    try:
        client_id = read_secret("IMA_OPENAPI_CLIENTID", "client_id")
        api_key = read_secret("IMA_OPENAPI_APIKEY", "api_key")
    except FileNotFoundError:
        write_text(report_path, "# IMA 交叉校验报告\n\n- 未找到 IMA 凭证，跳过校验。\n")
        return

    lines = ["# IMA 交叉校验报告", ""]
    for query in queries:
        try:
            payload = search(query, client_id, api_key)
        except Exception as exc:  # pragma: no cover - 网络异常分支
            lines.append(f"- `{query}`: 请求失败，{exc}")
            continue
        lines.append(f"## {query}")
        items = payload.get("data", {}).get("list", []) if isinstance(payload, dict) else []
        if not items:
            lines.append("- 未返回命中结果")
            lines.append("")
            continue
        for item in items[:3]:
            title = item.get("title", "无标题")
            highlight = item.get("highlight", "")
            lines.append(f"- {title}: {highlight}")
        lines.append("")
    write_text(report_path, "\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
