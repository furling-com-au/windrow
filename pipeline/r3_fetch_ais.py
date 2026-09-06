"""R3: download AMSA vessel-tracking monthly parquet files (AODN cloud-optimised product).

Source: s3://aodn-cloud-optimised/aggregated_amsa_nonqc.parquet (public HTTP access,
ap-southeast-2). Product: "Australian Search and Rescue Region Vessel Tracking -
Aggregated data product (2012 - ongoing)" (NESP MaC 5.9 / IMOS / AODN), derived from
AMSA Craft Tracking System monthly extracts. Licence: CC-BY 4.0 (IMOS/AODN + AMSA
attribution). Vessel identities are anonymised; craftID is a per-vessel surrogate key.

Layout: timestamp=<epoch of Jan 1>/polygon=<WKB hex box>/cts_srr_MM_YYYY_pt.parquet-0.parquet
The polygon box covering (0..180E, 90S..0) holds all Australian mainland waters
(~45 MB/month); a second small box covers the western SRR remainder.

We take months 2023-10 .. 2026-08 (three shipping years) for the big box only.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import RAW, fetch, update_manifest

BUCKET = "https://aodn-cloud-optimised.s3.ap-southeast-2.amazonaws.com"
PREFIX = "aggregated_amsa_nonqc.parquet"
OUT = RAW / "amsa_cts"

MONTHS = [(y, m) for y in (2023, 2024, 2025, 2026) for m in range(1, 13)]
MONTHS = [(y, m) for (y, m) in MONTHS if (2023, 10) <= (y, m) <= (2026, 8)]


def year_epoch(year: int) -> int:
    return int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp())


def list_year_keys(year: int) -> list[tuple[str, int]]:
    """[(key, size)] for a year partition (handles pagination)."""
    keys: list[tuple[str, int]] = []
    token = None
    while True:
        url = f"{BUCKET}/?list-type=2&prefix={PREFIX}/timestamp={year_epoch(year)}/&max-keys=1000"
        if token:
            url += f"&continuation-token={token}"
        xml = fetch(url, timeout=60, interval=0.3).decode()
        for block in re.finditer(r"<Contents>(.*?)</Contents>", xml, re.DOTALL):
            k = re.search(r"<Key>([^<]+)</Key>", block.group(1))
            s = re.search(r"<Size>(\d+)</Size>", block.group(1))
            if k and s:
                keys.append((k.group(1), int(s.group(1))))
        if "<IsTruncated>true</IsTruncated>" not in xml:
            break
        t = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", xml)
        if not t:
            break
        token = t.group(1).replace("+", "%2B").replace("=", "%3D").replace("/", "%2F")
    return keys


def main():
    by_year: dict[int, list[tuple[str, int]]] = {}
    for y in sorted({y for y, _ in MONTHS}):
        by_year[y] = list_year_keys(y)
        print(f"year {y}: {len(by_year[y])} keys in partition")

    missing, saved = [], []
    total_bytes = 0
    for y, m in MONTHS:
        pat = f"cts_srr_{m:02d}_{y}_pt.parquet"
        candidates = [(k, s) for k, s in by_year.get(y, []) if pat in k.lower()]
        if not candidates:
            missing.append(f"{y}-{m:02d}")
            continue
        key, size = max(candidates, key=lambda t: t[1])  # big box = largest file
        dest = OUT / str(y) / f"cts_srr_{m:02d}_{y}_pt.parquet"
        if dest.exists() and dest.stat().st_size > 0:
            print(f"{y}-{m:02d}: cached ({dest.stat().st_size/1e6:.1f} MB)")
            saved.append(dest)
            continue
        fetch(f"{BUCKET}/{key}", dest, timeout=600, interval=0.3)
        total_bytes += dest.stat().st_size
        print(f"{y}-{m:02d}: downloaded {dest.stat().st_size/1e6:.1f} MB")
        saved.append(dest)
    print(f"\nnew download volume: {total_bytes/1e9:.2f} GB; months missing upstream: {missing}")
    update_manifest(saved)


if __name__ == "__main__":
    main()
