"""R3: enumerate AMSA Craft Tracking System monthly extracts on data.gov.au (CKAN).

Saves the full package+resource metadata to data/raw/amsa_cts/ckan_packages.json and
prints a coverage table (month -> resource url, size, format). Downloads happen in
r3_fetch_cts.py once target months are chosen.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import RAW, fetch

CKAN = "https://data.gov.au/data/api/3/action/package_search?q=%22craft+tracking+system%22&rows=100"


def main():
    out_dir = RAW / "amsa_cts"
    out_dir.mkdir(parents=True, exist_ok=True)
    data = fetch(CKAN, timeout=90)
    j = json.loads(data)
    results = j["result"]["results"]
    (out_dir / "ckan_packages.json").write_bytes(json.dumps(j, indent=1).encode())
    print(f"packages: {len(results)} (total match count: {j['result']['count']})")
    rows = []
    for pkg in results:
        for res in pkg.get("resources", []):
            rows.append(
                {
                    "package": pkg["name"],
                    "pkg_title": pkg.get("title", ""),
                    "res_name": res.get("name", ""),
                    "format": res.get("format", ""),
                    "size": res.get("size"),
                    "url": res.get("url", ""),
                    "created": res.get("created", ""),
                }
            )
    rows.sort(key=lambda r: (r["package"], r["res_name"]))
    for r in rows:
        size_mb = ""
        try:
            size_mb = f"{int(r['size']) / 1e6:.0f}MB" if r["size"] else "?"
        except (TypeError, ValueError):
            size_mb = "?"
        print(f"{r['package'][:70]:70s} | {r['res_name'][:45]:45s} | {r['format']:6s} | {size_mb:>7s}")
    print(f"\ntotal resources: {len(rows)}")
    print("licences seen:", {p.get("license_title") or p.get("license_id") for p in results})


if __name__ == "__main__":
    main()
