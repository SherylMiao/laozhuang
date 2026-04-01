from __future__ import annotations

import json
import re
import time
from html import unescape
from urllib.request import Request, urlopen

from .seeds import NANHUA_CHAPTERS


USER_AGENT = "Mozilla/5.0 (compatible; DaozangKB/1.0; +https://github.com/pages)"


def fetch_text(url: str, timeout: int = 30) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "ignore")


def fetch_daodejing_api() -> list[str]:
    payload = fetch_text("https://api.ctext.org/gettext?urn=ctp:dao-de-jing")
    data = json.loads(payload)
    return list(data["fulltext"])


def extract_ctext_rows(html: str) -> list[str]:
    rows = re.findall(r'<tr id="n\d+">(.*?)</tr>', html, re.S)
    extracted: list[str] = []
    for row in rows:
        match = re.search(
            r'<td[^>]*class="ctext opt"[^>]*>.*?</td>\s*<td[^>]*class="ctext"[^>]*>(.*?)</td>',
            row,
            re.S,
        )
        if not match:
            continue
        content = re.sub(r"<sup[^>]*>.*?</sup>", "", match.group(1), flags=re.S)
        content = re.sub(r"<div[^>]*>.*?</div>", "", content, flags=re.S)
        content = re.sub(r"<br\s*/?>", "\n", content)
        content = re.sub(r"<[^>]+>", "", content)
        content = unescape(content).replace("\xa0", " ").strip()
        if content:
            extracted.append(re.sub(r"\s+", "", content))
    return extracted


def fetch_nanhua_chapters(delay_seconds: float = 0.5) -> list[dict[str, object]]:
    chapters: list[dict[str, object]] = []
    for chapter in NANHUA_CHAPTERS:
        url = f"https://ctext.org/zhuangzi/{chapter['slug']}/zh"
        html = fetch_text(url)
        rows = extract_ctext_rows(html)
        chapters.append({**chapter, "url": url, "rows": rows})
        time.sleep(delay_seconds)
    return chapters
