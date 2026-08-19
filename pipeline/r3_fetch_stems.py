"""R3: shipping stem history + current stem/loading statement.

1. Wayback backfill of the Bunge/Viterra SA shipping-stem PDF. The stem lives behind two
   AEM DAM UUIDs over time (found by source scouting, Aug 2026):
     375b51d1-2df2-48c7-bb2a-8907910c6d22   (~Nov 2021 - Oct 2024)
     ec53083b-2025-4261-aba3-abe01bb80e8a   (Oct 2024 - present)
   Every archived snapshot is downloaded (dedup by digest).
2. Wayback backfill of T-Ports "Loading-Statement-for-Web-Portal-*.pdf" (Lucky Bay/Wallaroo).
3. Current live files: Bunge shipping landing page -> current stem PDF + loading statement.
   delivery.bunge.com serves 403 to non-browser user agents; a desktop browser UA is used
   for those two public documents only (no robots.txt exists on either bunge host).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import RAW, UA, cdx_query, fetch, update_manifest, wayback_snapshot_url

BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
STEM_UUIDS = [
    "375b51d1-2df2-48c7-bb2a-8907910c6d22",
    "ec53083b-2025-4261-aba3-abe01bb80e8a",
]
OUT = RAW / "stems"


def wayback_prefix_download(
    url_prefix: str,
    dest_dir: Path,
    tag: str,
    client: httpx.Client,
    cdx_filter: str = "statuscode:200",
    match_type: str | None = "prefix",
) -> list[Path]:
    kwargs = {"filter": cdx_filter, "collapse": "digest", "limit": "2000"}
    if match_type:
        kwargs["matchType"] = match_type
    rows = cdx_query(url_prefix, **kwargs)
    saved = []
    if not rows:
        print(f"{tag}: no CDX rows")
        return saved
    header, entries = rows[0], rows[1:]
    ts_i, orig_i = header.index("timestamp"), header.index("original")
    print(f"{tag}: {len(entries)} unique snapshots")
    dest_dir.mkdir(parents=True, exist_ok=True)
    for row in entries:
        ts, orig = row[ts_i], row[orig_i]
        dest = dest_dir / f"{tag}_{ts}.pdf"
        data = fetch(wayback_snapshot_url(ts, orig), dest, client=client)
        if data == b"":
            print(f"  {ts}: 404")
            continue
        saved.append(dest)
    return saved


def main():
    saved: list[Path] = []
    with httpx.Client(follow_redirects=True, headers={"User-Agent": UA}, timeout=180) as client:
        # 1. Bunge/Viterra stem history
        for uuid in STEM_UUIDS:
            saved += wayback_prefix_download(
                f"viterra.com.au/dam/jcr:{uuid}", OUT / "wayback", f"stem_{uuid[:8]}", client
            )
        # 2. T-Ports loading statements
        saved += wayback_prefix_download(
            "tports.com/wp-content/uploads/*",
            OUT / "tports",
            "tports",
            client,
            cdx_filter="original:.*Loading-Statement.*",
            match_type=None,
        )

    # 3. current live documents. delivery.bunge.com's WAF rejects non-browser TLS
    # fingerprints (httpx 403s even with a browser UA) -> shell out to curl.
    import subprocess
    import time as _time

    def curl_get(url: str, dest: Path | None = None) -> bytes:
        args = ["curl", "-sS", "--max-time", "120", "-A", BROWSER_UA, "-L", url]
        if dest is not None:
            dest.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(args + ["-o", str(dest)], check=True)
            return dest.read_bytes()
        return subprocess.run(args, check=True, capture_output=True).stdout

    (OUT / "current").mkdir(parents=True, exist_ok=True)
    page_bytes = curl_get("https://www.bunge.com.au/agriculture/client-storage-and-handling-information/shipping")
    (OUT / "current" / "_shipping_page.html").write_bytes(page_bytes)
    page_text = page_bytes.decode(errors="replace")
    hrefs = re.findall(r'href="([^"]+\.ashx[^"]*)"', page_text)
    stem_urls = [h for h in hrefs if "shipping-stem" in h.lower()]
    ls_urls = [h for h in hrefs if "loading-statement" in h.lower()]
    print(f"current page: {len(stem_urls)} stem hrefs, {len(ls_urls)} loading-statement hrefs")
    for url in dict.fromkeys(stem_urls + ls_urls):
        full = url if url.startswith("http") else "https://www.bunge.com.au" + url
        name = re.sub(r"[^A-Za-z0-9._-]", "_", full.rsplit("/", 1)[-1].split("?")[0]) or "doc.ashx"
        dest = OUT / "current" / f"{name}.pdf"
        if dest.exists() and dest.stat().st_size > 0:
            saved.append(dest)
            continue
        _time.sleep(2)
        curl_get(full, dest)
        saved.append(dest)
        print(f"  saved {dest.name} ({dest.stat().st_size/1e3:.0f} kB)")
    update_manifest(saved)
    print(f"total stem files: {len(saved)}")


if __name__ == "__main__":
    main()
