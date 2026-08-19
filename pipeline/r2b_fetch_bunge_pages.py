"""R2 step 1b: fetch post-migration Bunge report article pages.

Reads data/raw/bunge_news/getarticles_p*.json, selects items whose category mentions
receivals/harvest, fetches each linkURL to data/raw/bunge_news/pages/.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import RAW, UA, fetch, slugify, update_manifest

def main():
    src = RAW / "bunge_news"
    pages_dir = src / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    items = {}
    for f in sorted(src.glob("getarticles_p*.json")):
        j = json.loads(f.read_text(encoding="utf-8"))
        for it in j.get("newsListings") or []:
            cat = (it.get("category") or "").lower()
            title = (it.get("title") or "").lower()
            if any(k in cat or k in title for k in ("receival", "harvest", "shipped", "shipping")):
                items[it["linkURL"]] = it
    print(f"report-like articles: {len(items)}")
    saved = []
    with httpx.Client(follow_redirects=True, headers={"User-Agent": UA}, timeout=60) as client:
        for url, it in sorted(items.items()):
            slug = slugify(url.rsplit("/", 1)[-1])[:120]
            dest = pages_dir / f"{slug}.html"
            fetch(url, dest, client=client)
            saved.append(dest)
            print(f"  {it.get('date','')}  [{it.get('category','')}] {it.get('title','')}")
    (src / "report_articles_index.json").write_text(
        json.dumps(list(items.values()), indent=1), encoding="utf-8"
    )
    update_manifest(saved)


if __name__ == "__main__":
    main()
