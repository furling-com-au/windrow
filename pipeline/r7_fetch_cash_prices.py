"""Capture the operator's daily cash-bid board (ActivePurchaseOption feed).

The public page bunge.com.au/agriculture/delivering-to-sa-vic-sites/cash-pricing is fed
by https://mobilews.viterra.com.au/api/ActivePurchaseOption — one record per posted bid
(site x commodity x grade x buyer x price x payment terms). Bids expire next-day 12:00
Adelaide and NO history is published, so this feed is ephemeral: each day not captured
is lost. See data/SOURCES.md "operator-cash-prices-api".

Outputs
- data/raw/cash_prices/active_purchase_option_YYYY-MM-DD.json  (full feed, immutable,
  first capture of the day wins; skipped in CI where data/raw is not committed)
- data/processed/cash_prices/YYYY-MM-DD.json  (compact: the fields we keep, committed)
- data/processed/cash_prices/summary.json  (per-day per-commodity medians + EP bid
  counts, rebuilt from all daily files; imported by the app at build time)

Run daily via .github/workflows/prices.yml (12:30-13:00 Adelaide, after the morning
bids post). Needs only httpx + tzdata:
`uv run --no-project --with httpx --with tzdata python pipeline/r7_fetch_cash_prices.py`.
"""
from __future__ import annotations

import json
import os
import statistics
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from wlib import PROCESSED, RAW, fetch, update_manifest

FEED = "https://mobilews.viterra.com.au/api/ActivePurchaseOption"

# Eyre Peninsula receival sites (matches data/processed/sites.geojson names, upper-cased):
# used to count how many bids land in the modelled region each day.
EP_SITES = {
    "ARNO BAY", "BUCKLEBOO", "CLEVE", "COCKALEECHIE", "CUMMINS", "DARKE PEAK",
    "EDILLILIE", "ELLISTON", "KARKOO", "KIMBA", "KYANCUTTA", "LOCK", "LUCKY BAY",
    "MINNIPA", "MURDINGA", "NUNJIKOMPITA", "POOCHERA", "PORT LINCOLN", "PT LINCOLN",
    "RUDALL", "STREAKY BAY", "THEVENARD", "TUMBY BAY", "UNGARRA", "WARRAMBOO",
    "WIRRULLA", "WUDINNA", "YEELANNA",
}

KEEP = [
    "siteDescription", "siteCode", "commodityDescription", "grade", "ownerDescription",
    "price", "paymentCategory", "paymentTermCode", "paymentTermDescription",
    "sellingOptionType", "season", "startDate", "endDate",
]


def compact(rec: dict) -> dict:
    return {k: rec.get(k) for k in KEEP}


def rebuild_summary(outdir) -> dict:
    """Deterministic per-day rollup from every committed daily file."""
    days: dict[str, dict] = {}
    for f in sorted(outdir.glob("????-??-??.json")):
        bids = json.loads(f.read_text(encoding="utf-8"))["bids"]
        by_com: dict[str, list[float]] = {}
        for b in bids:
            if isinstance(b.get("price"), (int, float)):
                by_com.setdefault(b.get("commodityDescription") or "?", []).append(float(b["price"]))
        days[f.stem] = {
            "bids": len(bids),
            "sites": len({b["siteDescription"] for b in bids}),
            "buyers": sorted({b["ownerDescription"] for b in bids}),
            "epBids": sum(1 for b in bids if (b.get("siteDescription") or "").upper() in EP_SITES),
            "medianPerT": {c: round(statistics.median(v), 2) for c, v in sorted(by_com.items())},
        }
    return {
        "source": FEED,
        "note": "Median posted cash bid (A$/t) per commodity per capture day. Bids expire "
        "next-day 12:00 Adelaide; epBids counts bids at Eyre Peninsula sites (0 off-season).",
        "days": days,
    }


def main() -> int:
    adelaide_today = datetime.now(ZoneInfo("Australia/Adelaide")).date().isoformat()
    in_ci = os.environ.get("GITHUB_ACTIONS") == "true"

    raw_dir = RAW / "cash_prices"
    out_dir = PROCESSED / "cash_prices"
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    body = fetch(FEED, timeout=60.0)
    if body is None or not body:
        print("fetch returned nothing; leaving existing captures untouched", file=sys.stderr)
        return 1
    feed = json.loads(body)
    print(f"{adelaide_today}: {len(feed)} active bids")

    # raw snapshot: immutable, first capture of the day wins; local runs only (data/raw
    # is git-ignored, so a CI runner's copy would evaporate — CI keeps the compact file).
    raw_path = raw_dir / f"active_purchase_option_{adelaide_today}.json"
    if not in_ci and not raw_path.exists():
        raw_path.write_bytes(body)
        update_manifest([raw_path])

    day = {
        "_meta": {
            "date": adelaide_today,
            "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": FEED,
            "bids": len(feed),
        },
        "bids": [compact(r) for r in feed],
    }
    (out_dir / f"{adelaide_today}.json").write_text(
        json.dumps(day, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    summary = rebuild_summary(out_dir)
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    today = summary["days"][adelaide_today]
    print(f"summary: {today['bids']} bids, {today['sites']} sites, EP bids {today['epBids']}, medians {today['medianPerT']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
