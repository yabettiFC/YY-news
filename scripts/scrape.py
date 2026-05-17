#!/usr/bin/env python3
"""
ニュースリリース監視スクリプト
各企業のニュースページをスクレイピングし、新着を検出してJSONに保存する
"""

import json
import hashlib
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---- 定数 ----------------------------------------------------------------
JST = timezone(timedelta(hours=9))
SITES_FILE   = Path(__file__).parent.parent / "sites.json"
DATA_FILE    = Path(__file__).parent.parent / "data" / "news.json"
OUTPUT_FILE  = Path(__file__).parent.parent / "docs" / "news.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; NewsMonitorBot/1.0; "
        "+https://github.com/YOUR_USERNAME/YOUR_REPO)"
    )
}
TIMEOUT = 15  # seconds


# ---- ユーティリティ -------------------------------------------------------

def load_json(path: Path, default):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def make_id(url: str, text: str) -> str:
    return hashlib.md5(f"{url}|{text}".encode()).hexdigest()[:12]


# ---- スクレイピング -------------------------------------------------------

def fetch_items(site: dict) -> list[dict]:
    """1サイトのニュース一覧を取得して返す"""
    try:
        resp = requests.get(site["url"], headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
    except Exception as e:
        print(f"  [ERROR] fetch failed: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    candidates = soup.select(site["selector"])

    items = []
    seen_texts = set()

    for elem in candidates[:30]:  # 最大30件チェック
        # テキスト取得
        text = elem.get_text(" ", strip=True)
        if not text or len(text) < 5:
            continue
        if text in seen_texts:
            continue
        seen_texts.add(text)

        # リンク取得
        link_elem = elem.select_one(site.get("link_selector", "a"))
        href = ""
        if link_elem and link_elem.get("href"):
            href = link_elem["href"]
            if href.startswith("/"):
                from urllib.parse import urlparse
                base = urlparse(site["url"])
                href = f"{base.scheme}://{base.netloc}{href}"

        items.append({
            "id":   make_id(site["url"], text),
            "text": text[:200],
            "url":  href,
        })

    return items


# ---- メイン --------------------------------------------------------------

def main():
    sites    = load_json(SITES_FILE, [])
    old_data = load_json(DATA_FILE, {})   # {site_name: [item, ...]}

    now_str = datetime.now(JST).isoformat()
    new_data   = {}   # 今回取得した全データ（保存用）
    all_news   = []   # ダッシュボード表示用（新着フラグ付き）

    for site in sites:
        name = site["name"]
        print(f"Checking: {name}")
        items = fetch_items(site)

        old_ids = {it["id"] for it in old_data.get(name, [])}
        new_data[name] = items

        for item in items:
            is_new = item["id"] not in old_ids
            all_news.append({
                "company":    name,
                "company_url": site["url"],
                "text":       item["text"],
                "url":        item["url"],
                "is_new":     is_new,
                "id":         item["id"],
            })

        new_count = sum(1 for it in items if it["id"] not in old_ids)
        print(f"  -> {len(items)} items, {new_count} new")

    # 保存
    save_json(DATA_FILE, new_data)

    output = {
        "updated_at": now_str,
        "news": all_news,
    }
    save_json(OUTPUT_FILE, output)
    print(f"\nDone. Output -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
