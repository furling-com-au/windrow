"""Phase 2: observed_{season}.json + vessels_{season}.json for the app bundle.

observed_*: real weekly receivals (Western is the calibration target), Port Lincoln
monthly grain shipments + vessel calls, district production, harvest-start dates.
vessels_*: AIS-derived Port Lincoln berth visits with per-visit cargo estimated by
allocating the month's official Flinders grain tonnage across visits (flagged
"allocated" — an estimate, not a measurement), + Lucky Bay anchorage stays,
+ Thevenard berth visits (grain share caveat).
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import PROCESSED, ROOT

APP_DATA = ROOT / "app" / "public" / "data"
SEASONS = ["2022/23", "2023/24", "2024/25", "2025/26"]
AIS_SEASONS = {"2023/24", "2024/25", "2025/26"}
FIRST_DELIVERY = {  # published first-receival dates (see CALIBRATION.md sources)
    "2022/23": "2022-10-11",
    "2023/24": "2023-09-25",
    "2024/25": "2024-10-10",
    "2025/26": "2025-10-13",
}


def season_window(season: str) -> tuple[date, date]:
    y = int(season[:4])
    return date(y, 10, 1), date(y + 1, 9, 30)


def main():
    weekly = pl.read_parquet(PROCESSED / "receivals_weekly.parquet")
    ships = pl.read_parquet(PROCESSED / "port_shipments_monthly.parquet")
    calls_off = pl.read_parquet(PROCESSED / "port_vessel_calls_monthly.parquet")
    visits = pl.read_parquet(PROCESSED / "vessel_calls.parquet")
    prod = pl.read_parquet(PROCESSED / "production_districts.parquet")

    for season in SEASONS:
        s0, s1 = season_window(season)
        w = weekly.filter(pl.col("season") == season).sort("week_ending")
        wk_out = []
        for we in sorted(w["week_ending"].unique().to_list()):
            sub = w.filter(pl.col("week_ending") == we)
            row = {"week_ending": we.isoformat(), "fortnight": bool(sub["report_kind"].first() == "fortnight")}
            for region in ("total", "western", "central", "eastern"):
                r = sub.filter(pl.col("region") == region)
                if r.height:
                    row[region] = {"weekly_t": r["weekly_t"][0], "cum_t": r["cum_t"][0]}
            wk_out.append(row)

        pls = (
            ships.filter(pl.col("port") == "Port Lincoln")
            .with_columns(pl.date(pl.col("year"), pl.col("month"), 1).alias("m0"))
            .filter((pl.col("m0") >= s0) & (pl.col("m0") <= s1))
        )
        ship_out = [
            {"year": r["year"], "month": r["month"], "commodity": r["commodity"], "export_t": r["export_t"]}
            for r in pls.iter_rows(named=True)
        ]
        thev = (
            ships.filter(pl.col("port") == "Thevenard")
            .with_columns(pl.date(pl.col("year"), pl.col("month"), 1).alias("m0"))
            .filter((pl.col("m0") >= s0) & (pl.col("m0") <= s1))
        )
        thev_out = [
            {"year": r["year"], "month": r["month"], "commodity": r["commodity"], "export_t": r["export_t"]}
            for r in thev.iter_rows(named=True)
        ]

        co = (
            calls_off.filter((pl.col("port") == "Port Lincoln") & (pl.col("vessel_class") == "Dry Bulk"))
            .with_columns(pl.date(pl.col("year"), pl.col("month"), 1).alias("m0"))
            .filter((pl.col("m0") >= s0) & (pl.col("m0") <= s1))
        )
        calls_out = [{"year": r["year"], "month": r["month"], "calls": r["calls"]} for r in co.iter_rows(named=True)]

        pd_ = prod.filter(pl.col("season") == season)
        prod_out = {}
        for r in pd_.filter(pl.col("crop") == "TOTAL").iter_rows(named=True):
            prod_out[r["district"]] = r["production_t"]

        obs = {
            "season": season,
            "attribution": {
                "receivals": "Viterra/Bunge weekly harvest reports (via Internet Archive)",
                "shipments_and_calls": "Flinders Port Holdings monthly statistics",
                "production": "PIRSA Crop and Pasture Reports",
                "note": "Observed data; see data/SOURCES.md for licences.",
            },
            "first_delivery": FIRST_DELIVERY.get(season),
            "weekly_receivals": wk_out,
            "port_lincoln_shipments_monthly": ship_out,
            "thevenard_shipments_monthly": thev_out,
            "port_lincoln_drybulk_calls_monthly": calls_out,
            "district_production_t": prod_out,
        }
        f = APP_DATA / f"observed_{season.replace('/', '-')}.json"
        f.write_text(json.dumps(obs), encoding="utf-8")
        print(f"{f.name}: {len(wk_out)} weeks, {len(ship_out)} PL shipment rows ({f.stat().st_size/1e3:.0f} kB)")

        # vessels
        if season not in AIS_SEASONS:
            continue
        vis = visits.filter(
            (pl.col("start") >= datetime(s0.year, s0.month, s0.day))
            & (pl.col("start") <= datetime(s1.year, s1.month, s1.day, 23, 59))
        )
        plv = vis.filter((pl.col("zone") == "port_lincoln") & (pl.col("state") == "berth")).sort("start")
        # link each berth visit to its preceding anchorage stay (same craftID, anchor stay
        # ending within [-36 h, +6 h] of berthing) so the sim shows ships waiting at anchor
        anchors = (
            vis.filter((pl.col("zone") == "port_lincoln") & (pl.col("state") == "anchor"))
            .sort("start")
            .to_dicts()
        )
        used_anchor: set[int] = set()

        def find_anchor(craft_id: int, berth_start) -> dict | None:
            best = None
            for i, a in enumerate(anchors):
                if i in used_anchor or a["craftID"] != craft_id:
                    continue
                gap_h = (berth_start - a["end"]).total_seconds() / 3600
                if a["start"] < berth_start and -6 <= gap_h <= 36:
                    if best is None or a["start"] > anchors[best]["start"]:
                        best = i
            if best is None:
                return None
            used_anchor.add(best)
            return anchors[best]
        # allocate monthly official grain tonnes across visits by duration
        month_t: dict[tuple[int, int], float] = {}
        for r in pls.group_by("year", "month").agg(pl.col("export_t").sum().alias("t")).iter_rows(named=True):
            month_t[(r["year"], r["month"])] = r["t"]
        rows = plv.to_dicts()
        by_month: dict[tuple[int, int], list[dict]] = {}
        for r in rows:
            by_month.setdefault((r["start"].year, r["start"].month), []).append(r)
        vessels = []
        n_anchored = 0
        for (yy, mm), lst in sorted(by_month.items()):
            tot_dur = sum(r["duration_h"] for r in lst) or 1.0
            mt = month_t.get((yy, mm), 0.0)
            for r in lst:
                a = find_anchor(r["craftID"], r["start"])
                if a is not None:
                    n_anchored += 1
                vessels.append(
                    {
                        "craft_id": r["craftID"],
                        "arrive": r["start"].isoformat(),
                        "anchor_arrive": a["start"].isoformat() if a else None,
                        "observed_wait_h": round((r["start"] - a["start"]).total_seconds() / 3600, 1) if a else None,
                        "berth_hours": round(r["duration_h"], 1),
                        "length_m": r["length_m"],
                        "draught_in": r["draught_start"],
                        "draught_out": r["draught_end"],
                        "est_cargo_t": round(mt * r["duration_h"] / tot_dur),
                        "cargo_provenance": "allocated-from-monthly-port-total",
                    }
                )
        lb = vis.filter((pl.col("zone") == "lucky_bay") & (pl.col("state") == "anchor") & (pl.col("duration_h") > 24)).sort("start")
        lb_out = [
            {"craft_id": r["craftID"], "arrive": r["start"].isoformat(), "anchor_hours": round(r["duration_h"], 1), "length_m": r["length_m"]}
            for r in lb.to_dicts()
        ]
        th = vis.filter((pl.col("zone") == "thevenard") & (pl.col("state") == "berth")).sort("start")
        th_out = [
            {"craft_id": r["craftID"], "arrive": r["start"].isoformat(), "berth_hours": round(r["duration_h"], 1), "length_m": r["length_m"]}
            for r in th.to_dicts()
        ]
        vj = {
            "season": season,
            "source": "AMSA CTS via AODN (CC BY-NC 3.0 AU at source; anonymised craft ids; times +/-1h)",
            "port_lincoln_berth_visits": vessels,
            "lucky_bay_anchorage_stays": lb_out,
            "thevenard_berth_visits_all_cargo": th_out,
            "note": "Thevenard visits include gypsum/salt/mineral-sands vessels; est_cargo_t at Port Lincoln is the month's official grain tonnage allocated across visits by berth time.",
        }
        f = APP_DATA / f"vessels_{season.replace('/', '-')}.json"
        f.write_text(json.dumps(vj), encoding="utf-8")
        print(f"{f.name}: PL {len(vessels)} ({n_anchored} with linked anchorage), LB {len(lb_out)}, THE {len(th_out)} ({f.stat().st_size/1e3:.0f} kB)")


if __name__ == "__main__":
    main()
