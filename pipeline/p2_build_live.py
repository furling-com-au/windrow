"""Live-season builder: (re)generate the 2026/27 bundle from live sources.

  uv run python pipeline/p2_build_live.py

Designed to run repeatedly (weekly during harvest). Produces:
  demand_2026-27.json   - PROVISIONAL: 4-season mean of PIRSA district production (A20),
                          replaced by PIRSA 2026/27 estimates when published
  weather_2026-27.json  - ERA5 to date (open-meteo); future days default to benign
  observed_2026-27.json - weekly receivals parsed from bunge.com.au (live fetch, dated
                          cache), Flinders shipments when published, provisional carry-in
  vessels_2026-27.json  - upcoming Pt Lincoln vessels from the current shipping stem

Everything provisional is marked in the file; the app labels the season "(live)".
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r2_parse_receivals import parse_report, season_of
from wlib import PROCESSED, RAW, ROOT, fetch

APP_DATA = ROOT / "app" / "public" / "data"
SEASON = "2026/27"
SID = "2026-27"
S0 = dt.date(2026, 10, 1)
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
CROP_GROUPS = {
    "wheat": ["wheat"], "barley": ["barley"], "canola": ["canola"], "lentils": ["lentils"],
    "beans": ["beans"], "other": ["oats", "triticale", "peas", "lupins", "chickpeas", "vetch"],
}
POINTS = {
    "cummins_lower_ep": ("LEP", -34.264, 135.729), "yeelanna_lower_ep": ("LEP", -34.141, 135.727),
    "lock_central_ep": ("EEP", -33.568, 135.756), "kimba_eastern_ep": ("EEP", -33.140, 136.417),
    "cleve_eastern_ep": ("EEP", -33.699, 136.492), "wudinna_central_ep": ("WEP", -33.046, 135.461),
    "streaky_bay_western_ep": ("WEP", -32.796, 134.209), "ceduna_far_west": ("WEP", -32.127, 133.673),
}


def build_demand():
    prod = pl.read_parquet(PROCESSED / "production_districts.parquet")
    mean = (
        prod.filter(pl.col("crop") != "TOTAL")
        .group_by("district", "crop")
        .agg(pl.col("production_t").mean().alias("t"))
    )
    dg: dict[tuple[str, str], float] = {}
    for r in mean.iter_rows(named=True):
        grp = next((g for g, crops in CROP_GROUPS.items() if r["crop"] in crops), "other")
        dg[(r["district"], grp)] = dg.get((r["district"], grp), 0.0) + float(r["t"])
    parcels = json.loads((APP_DATA / "parcels.json").read_text(encoding="utf-8"))["parcels"]
    dist_ha: dict[str, float] = {}
    for p in parcels:
        dist_ha[p["district"]] = dist_ha.get(p["district"], 0.0) + p["cropping_ha"]
    demand = []
    total = 0.0
    for p in parcels:
        w = p["cropping_ha"] / dist_ha[p["district"]]
        crops = {}
        for (d, g), t in dg.items():
            if d == p["district"] and t > 0:
                v = round(t * w, 1)
                if v >= 1:
                    crops[g] = v
                    total += v
        demand.append({"id": p["id"], "crops": crops})
    out = {
        "season": SEASON,
        "provenance": "A20 PROVISIONAL: mean of PIRSA district production 2022/23-2025/26; replace when PIRSA publishes 2026/27 estimates",
        "parcels": demand,
    }
    (APP_DATA / f"demand_{SID}.json").write_text(json.dumps(out), encoding="utf-8")
    print(f"demand_{SID}.json: {total/1e6:.2f} Mt provisional")


def build_weather():
    today = dt.date.today()
    if today < dt.date(2026, 9, 2):
        # pre-season: nothing to fetch yet; engine treats missing days as benign
        empty = {d: {"start": "2026-09-01", "rain_mm": [], "tmax_c": [], "rh_min_pct": [], "wind_max_kmh": []} for d in ("WEP", "LEP", "EEP")}
        (APP_DATA / f"weather_{SID}.json").write_text(
            json.dumps({"season": SEASON, "source": "pre-season placeholder; refreshed from ERA5 once Sep 2026 data exists", "districts": empty}),
            encoding="utf-8",
        )
        print(f"weather_{SID}.json: pre-season placeholder")
        return
    end = min(today - dt.timedelta(days=1), dt.date(2027, 3, 31)).isoformat()
    url_t = (
        "https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}"
        "&start_date=2026-09-01&end_date=" + end +
        "&daily=precipitation_sum,temperature_2m_max,relative_humidity_2m_min,wind_speed_10m_max"
        "&timezone=Australia%2FAdelaide"
    )
    by_d: dict[str, list[dict]] = {"WEP": [], "LEP": [], "EEP": []}
    for name, (d, lat, lon) in POINTS.items():
        dest = RAW / "climate" / "live" / f"{name}_{end}.json"
        data = fetch(url_t.format(lat=lat, lon=lon), dest, timeout=120)
        j = json.loads(data if data is not None else dest.read_bytes())
        by_d[d].append(j["daily"])
    out: dict[str, dict] = {}
    for d, lst in by_d.items():
        n = min(len(x["time"]) for x in lst)
        out[d] = {
            "start": lst[0]["time"][0],
            "rain_mm": [round(sum((x["precipitation_sum"][i] or 0) for x in lst) / len(lst), 2) for i in range(n)],
            "tmax_c": [round(sum((x["temperature_2m_max"][i] or 20) for x in lst) / len(lst), 1) for i in range(n)],
            "rh_min_pct": [round(sum((x["relative_humidity_2m_min"][i] or 30) for x in lst) / len(lst)) for i in range(n)],
            "wind_max_kmh": [round(sum((x["wind_speed_10m_max"][i] or 20) for x in lst) / len(lst)) for i in range(n)],
        }
    (APP_DATA / f"weather_{SID}.json").write_text(
        json.dumps({"season": SEASON, "source": "ERA5 via open-meteo, to date; future days default benign in-engine", "districts": out}),
        encoding="utf-8",
    )
    print(f"weather_{SID}.json: to {end}")


def curl(url: str) -> bytes:
    return subprocess.run(
        ["curl", "-sS", "--max-time", "120", "-A", BROWSER_UA, "-L", url],
        check=True, capture_output=True,
    ).stdout


def build_observed():
    stamp = dt.date.today().isoformat()
    live_dir = RAW / "bunge_news" / "live" / stamp
    live_dir.mkdir(parents=True, exist_ok=True)
    weekly_rows = []
    try:
        listing = json.loads(
            curl("https://www.bunge.com.au/sitecore/api/ssc/Controllers/Search/1/getarticles?pageNum=1&searchTerm=&pageSize=50&searchtags=&categories=&regions=f17400b78dcc43ecae59a3fcc299024d&sites=Australia")
        )
        (live_dir / "getarticles.json").write_bytes(json.dumps(listing).encode())
        for it in listing.get("newsListings") or []:
            if "Weekly harvest report" not in (it.get("category") or ""):
                continue
            slug = re.sub(r"[^A-Za-z0-9-]", "-", it["linkURL"].rsplit("/", 1)[-1])[:120]
            page = live_dir / f"{slug}.html"
            if not page.exists():
                page.write_bytes(curl(it["linkURL"]))
            parsed = parse_report(page, "bunge-live")
            if parsed:
                for row in parsed[0]:
                    if row["season"] == SEASON:
                        weekly_rows.append(row)
    except Exception as e:  # noqa: BLE001 - live fetch is best-effort
        print(f"  live fetch warning: {e}")

    wk_out = []
    for we in sorted({r["week_ending"] for r in weekly_rows}):
        sub = [r for r in weekly_rows if r["week_ending"] == we]
        row = {"week_ending": we.isoformat(), "fortnight": sub[0]["report_kind"] == "fortnight"}
        for region in ("total", "western", "central", "eastern"):
            m = next((r for r in sub if r["region"] == region), None)
            if m:
                row[region] = {"weekly_t": m["weekly_t"], "cum_t": m["cum_t"]}
        wk_out.append(row)

    ships = pl.read_parquet(PROCESSED / "port_shipments_monthly.parquet")
    ship_out = [
        {"year": r["year"], "month": r["month"], "commodity": r["commodity"], "export_t": r["export_t"]}
        for r in ships.filter(
            (pl.col("port") == "Port Lincoln")
            & (((pl.col("year") == 2026) & (pl.col("month") >= 10)) | (pl.col("year") == 2027))
        ).iter_rows(named=True)
    ]
    # provisional carry-in: mean of the last two seasons' Oct+Nov shipments
    prior = ships.filter(
        pl.col("port").is_in(["Port Lincoln", "Thevenard"])
        & (((pl.col("year") == 2024) | (pl.col("year") == 2025)) & pl.col("month").is_in([10, 11]))
    )
    pl_t = prior.filter(pl.col("port") == "Port Lincoln")["export_t"].sum() / 2
    the_t = prior.filter(pl.col("port") == "Thevenard")["export_t"].sum() / 2
    obs = {
        "season": SEASON,
        "live": True,
        "generated": stamp,
        "attribution": {"receivals": "Bunge weekly harvest reports (live)", "note": "LIVE season: provisional until data lands; see A20"},
        "first_delivery": None,
        "weekly_receivals": wk_out,
        "port_lincoln_shipments_monthly": ship_out,
        "thevenard_shipments_monthly": [],
        "port_lincoln_drybulk_calls_monthly": [],
        "district_production_t": {},
        "carry_in": {
            "port_lincoln_t": round(pl_t), "thevenard_t": round(the_t),
            "upcountry_t": round(0.2 * (pl_t + the_t)),
            "provenance": "A17/A20 provisional: mean of 2024+2025 Oct-Nov shipments (2026 not yet published)",
        },
        "annotations": [],
    }
    (APP_DATA / f"observed_{SID}.json").write_text(json.dumps(obs), encoding="utf-8")
    print(f"observed_{SID}.json: {len(wk_out)} weeks live, {len(ship_out)} shipment rows")


def build_vessels():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from p2_stem_names import parse_stem

    stems = sorted((RAW / "stems" / "current").glob("*shipping-stem*.pdf"))
    visits = []
    if stems:
        rows = parse_stem(stems[-1])
        vid = -1
        for r in rows:
            if not r["date_max"]:
                continue
            d_max = dt.date.fromisoformat(r["date_max"])
            if d_max < S0:
                continue
            d_min = dt.date.fromisoformat(r["date_min"]) if r["date_min"] else d_max
            d = d_min if d_min >= S0 else d_max
            visits.append(
                {
                    "craft_id": vid,
                    "arrive": f"{d.isoformat()}T06:00:00",
                    "anchor_arrive": None,
                    "berth_hours": 55,
                    "est_cargo_t": r["volume_t"] or 25000,
                    "name_candidate": r["vessel"],
                    "stem_volume_t": r["volume_t"],
                    "stem_commodity": r["commodity"],
                }
            )
            vid -= 1
    vj = {
        "season": SEASON,
        "source": "current Bunge shipping stem (rolling snapshot; refresh via r3_fetch_stems.py)",
        "port_lincoln_berth_visits": visits,
        "lucky_bay_anchorage_stays": [],
        "thevenard_berth_visits_all_cargo": [],
        "note": "LIVE season: schedule from the public stem; regenerate weekly during harvest",
    }
    (APP_DATA / f"vessels_{SID}.json").write_text(json.dumps(vj), encoding="utf-8")
    print(f"vessels_{SID}.json: {len(visits)} upcoming vessels from stem")


def main():
    build_demand()
    build_weather()
    build_observed()
    build_vessels()
    print("live bundle refreshed; rebuild + deploy: npm --workspace app run build && npx wrangler deploy")


if __name__ == "__main__":
    main()
