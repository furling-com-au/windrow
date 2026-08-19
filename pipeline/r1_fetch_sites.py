"""R1: fetch the operator's live site roster + per-site details (first-party source).

The Bunge (ex-Viterra) segregations/opening-hours page at bunge.com.au is backed by a
still-live Viterra mobile API:
  https://mobilews.viterra.com.au/api/Sites/GeographicalRegion/Western  (roster)
  https://mobilews.viterra.com.au/api/Sites/{guid}                      (detail: lat/lon, hours, status)

"Western" = Eyre Peninsula + far west region in operator terminology.
Raw responses cached under data/raw/operator_sites/ (immutable).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import RAW, UA, fetch, slugify, update_manifest

BASE = "https://mobilews.viterra.com.au/api"


def main():
    out = RAW / "operator_sites"
    out.mkdir(parents=True, exist_ok=True)
    saved = []
    with httpx.Client(follow_redirects=True, headers={"User-Agent": UA}, timeout=60) as client:
        roster_dest = out / "western_roster.json"
        data = fetch(f"{BASE}/Sites/GeographicalRegion/Western", roster_dest, client=client)
        if data is None:
            data = roster_dest.read_bytes()
        saved.append(roster_dest)
        roster = json.loads(data)
        items = roster if isinstance(roster, list) else roster.get("Sites") or roster.get("sites") or []
        print(f"roster entries: {len(items)}")
        for it in items:
            sid = it.get("Id") or it.get("id") or it.get("SiteId") or it.get("siteId")
            name = it.get("Name") or it.get("name") or str(sid)
            if not sid:
                print(f"  no id for {name}; keys: {list(it)[:8]}")
                continue
            dest = out / f"site_{slugify(str(name))}.json"
            fetch(f"{BASE}/Sites/{sid}", dest, client=client)
            saved.append(dest)
            print(f"  {name}: cached")
    update_manifest(saved)


if __name__ == "__main__":
    main()
