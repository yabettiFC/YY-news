#!/usr/bin/env python3
"""
ニュースリリース監視スクリプト（Playwright版）
JavaScript動的サイト含めて取得可能
"""

import json
import hashlib
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

JST = timezone(timedelta(hours=9))
SITES_FILE  = Path(__file__).parent.parent / "sites.json"
DATA_FILE   = Path(__file__).parent.parent / "data" / "news.json"
OUTPUT_FILE = Path(__file__).parent.parent / "docs" / "news.json"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
WAIT_MS = 3500            # ページ読込後の待ち時間（JSが描画するのを待つ）
TIMEOUT_MS = 30000        # ページ読込タイムアウト
MAX_ITEMS = 30            # 1サイトあたり最大件数


def load_json(path, default):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def make_id(url, text):
    return hashlib.md5(f"{url}|{text}".encode()).hexdigest()[:12]


def normalize_url(href, base_url):
    if not href:
        return ""
    if href.startswith("http"):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        p = urlparse(base_url)
        return f"{p.scheme}://{p.netloc}{href}"
    return href


def fetch_items(page, site):
    """1サイトを開いてニュース一覧を返す"""
    try:
        page.goto(site["url"], timeout=TIMEOUT_MS, wait_until="domcontentloaded")
        # JSで描画されるサイト対策：少し待つ
        page.wait_for_timeout(WAIT_MS)
    except Exception as e:
        print(f"  [ERROR] page load: {e}", file=sys.stderr)
        return []

    selector = site["selector"]

    try:
        elements = page.query_selector_all(selector)
    except Exception as e:
        print(f"  [ERROR] selector: {e}", file=sys.stderr)
        return []

    items = []
    seen_texts = set()

    for el in elements[:MAX_ITEMS]:
        try:
            text = (el.inner_text() or "").strip()
        except Exception:
            continue
        text = " ".join(text.split())  # 改行・空白整理
        if not text or len(text) < 5:
            continue
        if text in seen_texts:
            continue
        seen_texts.add(text)

        # リンク取得
        href = ""
        try:
            # 要素自体がaタグの場合
            tag = el.evaluate("e => e.tagName")
            if tag and tag.lower() == "a":
                href = el.get_attribute("href") or ""
            else:
                link_el = el.query_selector(site.get("link_selector", "a"))
                if link_el:
                    href = link_el.get_attribute("href") or ""
        except Exception:
            pass

        href = normalize_url(href, site["url"])

        items.append({
            "id":   make_id(site["url"], text),
            "text": text[:200],
            "url":  href,
        })

    return items


def main():
    sites    = load_json(SITES_FILE, [])
    old_data = load_json(DATA_FILE, {})

    now_str = datetime.now(JST).isoformat()
    new_data = {}
    all_news = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT, locale="ja-JP")
        page = context.new_page()

        for site in sites:
            name = site["name"]
            print(f"Checking: {name}")
            items = fetch_items(page, site)

            old_ids = {it["id"] for it in old_data.get(name, [])}
            new_data[name] = items

            for it in items:
                is_new = it["id"] not in old_ids
                all_news.append({
                    "company":     name,
                    "company_url": site["url"],
                    "text":        it["text"],
                    "url":         it["url"],
                    "is_new":      is_new,
                    "id":          it["id"],
                })

            new_count = sum(1 for it in items if it["id"] not in old_ids)
            print(f"  -> {len(items)} items, {new_count} new")

        browser.close()

    save_json(DATA_FILE, new_data)
    save_json(OUTPUT_FILE, {"updated_at": now_str, "news": all_news})
    print(f"\nDone. Output -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
