"""R2 step 1: fetch every archived Viterra/Bunge weekly harvest report page.

Strategy:
  1. CDX-list snapshots of the listing page /media/Receivals-reports (all years) and
     fetch a handful of listing snapshots (latest per half-year) to data/raw.
  2. Parse hrefs from all cached listing snapshots -> unique report slugs.
  3. CDX prefix query over /media/Receivals-reports/Weekly-harvest-reports/* -> for each
     report page pick the LATEST 200 text/html snapshot (pages are static once published).
  4. Download each chosen snapshot (id_ raw HTML).
  5. Fetch the Bunge Sitecore getarticles listing (post-migration reports) as raw JSON pages.

Idempotent: existing files are never re-downloaded.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import RAW, cdx_query, fetch, update_manifest, wayback_snapshot_url

LISTING_URL = "viterra.com.au/media/Receivals-reports"
WEEKLY_PREFIX = "viterra.com.au/media/Receivals-reports/Weekly-harvest-reports"
OUT = RAW / "viterra_reports"
BUNGE_API = (
    "https://www.bunge.com.au/sitecore/api/ssc/Controllers/Search/1/getarticles"
    "?pageNum={page}&searchTerm=&pageSize=50&searchtags=&categories="
    "&regions=f17400b78dcc43ecae59a3fcc299024d&sites=Australia"
)

HREF_RE = re.compile(r'href="(/media/Receivals-reports/[^"]+)"', re.IGNORECASE)


def step1_listing_snapshots(client: httpx.Client) -> list[Path]:
    rows = cdx_query(LISTING_URL, collapse="timestamp:6", filter="statuscode:200", limit="200")
    saved = []
    if not rows:
        print("WARN: no CDX rows for listing page")
        return saved
    header, entries = rows[0], rows[1:]
    ts_i, orig_i = header.index("timestamp"), header.index("original")
    (OUT / "listings").mkdir(parents=True, exist_ok=True)
    for row in entries:
        ts, orig = row[ts_i], row[orig_i]
        dest = OUT / "listings" / f"listing_{ts}.html"
        fetch(wayback_snapshot_url(ts, orig), dest, client=client)
        saved.append(dest)
    print(f"listing snapshots cached: {len(saved)}")
    return saved


def step2_collect_slugs() -> dict[str, str]:
    """slug -> path (as it appeared). Dedup case-insensitively, keep first-seen casing."""
    slugs: dict[str, str] = {}
    for f in sorted((OUT / "listings").glob("listing_*.html")):
        html = f.read_text(encoding="utf-8", errors="replace")
        for m in HREF_RE.finditer(html):
            path = m.group(1)
            if "/Weekly-harvest-reports/" not in path and "/weekly-harvest-reports/" not in path.lower():
                continue
            if path.rstrip("/").lower().endswith("weekly-harvest-reports"):
                continue
            key = path.lower().rstrip("/")
            if key not in slugs:
                slugs[key] = path
    print(f"unique weekly report paths from listings: {len(slugs)}")
    return slugs


def step3_snapshot_index() -> dict[str, tuple[str, str]]:
    """For every archived weekly-report page: url_lower -> (latest_ts, original_url)."""
    rows = cdx_query(
        WEEKLY_PREFIX + "/",
        matchType="prefix",
        filter="statuscode:200",
        limit="20000",
    )
    index: dict[str, tuple[str, str]] = {}
    if not rows:
        return index
    header, entries = rows[0], rows[1:]
    ts_i, orig_i, mime_i = header.index("timestamp"), header.index("original"), header.index("mimetype")
    for row in entries:
        if row[mime_i] != "text/html":
            continue
        orig = row[orig_i]
        # normalise: strip protocol/host casing and query strings
        path = re.sub(r"^https?://(www\.)?viterra\.com\.au", "", orig).split("?")[0].rstrip("/")
        key = path.lower()
        ts = row[ts_i]
        if key not in index or ts > index[key][0]:
            index[key] = (ts, orig)
    print(f"archived weekly report pages in CDX: {len(index)}")
    return index


def step4_download(slugs: dict[str, str], index: dict[str, tuple[str, str]], client: httpx.Client):
    (OUT / "weekly").mkdir(parents=True, exist_ok=True)
    all_keys = sorted(set(slugs) | set(index))
    missing, saved = [], []
    for key in all_keys:
        if key not in index:
            missing.append(key)
            continue
        ts, orig = index[key]
        name = key.rsplit("/", 1)[-1]
        dest = OUT / "weekly" / f"{name}__{ts}.html"
        data = fetch(wayback_snapshot_url(ts, orig), dest, client=client)
        if data == b"":
            missing.append(key)
            continue
        saved.append(dest)
    (OUT / "weekly_missing.json").write_text(json.dumps(missing, indent=1), encoding="utf-8")
    print(f"weekly report pages downloaded/cached: {len(saved)} (+{len(list((OUT/'weekly').glob('*.html'))) - len(saved)} pre-existing); not archived: {len(missing)}")
    if missing:
        print("MISSING (no Wayback snapshot):")
        for m in missing:
            print("  ", m)


def step5_bunge_listing(client: httpx.Client):
    dest_dir = RAW / "bunge_news"
    dest_dir.mkdir(parents=True, exist_ok=True)
    page = 1
    while page <= 30:
        dest = dest_dir / f"getarticles_p{page:02d}.json"
        data = fetch(BUNGE_API.format(page=page), dest, client=client)
        if data is None:  # cached
            data = dest.read_bytes()
        if not data:
            break
        try:
            j = json.loads(data)
        except json.JSONDecodeError:
            print(f"WARN: page {page} not JSON")
            break
        items = j.get("newsListings") or []
        n = len(items)
        print(f"bunge getarticles page {page}: {n} items (totalResults={j.get('totalResults')})")
        if n == 0 or page >= int(j.get("totalPages") or 1):
            break
        page += 1


def main():
    with httpx.Client(follow_redirects=True, headers={"User-Agent": "WindrowResearch/0.1 (polite research crawler)"}, timeout=120) as client:
        step1_listing_snapshots(client)
        slugs = step2_collect_slugs()
        index = step3_snapshot_index()
        step4_download(slugs, index, client)
        step5_bunge_listing(client)
    update_manifest(list((OUT).rglob("*.*")) + list((RAW / "bunge_news").rglob("*.*")))
    print("done")


if __name__ == "__main__":
    main()
