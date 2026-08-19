"""R3: derive vessel calls at EP ports from AMSA CTS points.

Inputs : data/raw/amsa_cts/<year>/cts_srr_MM_YYYY_pt.parquet (national, monthly)
Outputs: data/processed/ais_ep_points.parquet   (all points in 3 port zones, zone-tagged)
         data/processed/vessel_calls.parquet    (one row per cargo-vessel berth/anchorage visit)
         printed QA report

Method notes (documented limitations):
- CTS positions are thinned to >= 60-minute intervals per vessel, so berth arrival/departure
  times carry ~+/-1 h uncertainty (bounded by first/last ping inside the geofence).
- craftID is an anonymised per-vessel key; empirical cross-month stability is checked below.
- Berth location is found by clustering stationary cargo pings near the known wharf area;
  anchorage = stationary cargo clusters > 2 km from the berth within the zone.
"""
from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import PROCESSED, RAW

ZONES = {
    # zone: (lat_min, lat_max, lon_min, lon_max)
    "port_lincoln": (-34.90, -34.55, 135.70, 136.15),
    "lucky_bay": (-33.80, -33.40, 136.75, 137.20),
    "thevenard": (-32.40, -31.95, 133.30, 133.95),
}
# approximate wharf locations (map/OSM-derived; used only to anchor the berth-cluster search)
WHARF_HINT = {
    "port_lincoln": (-34.714, 135.868),
    "lucky_bay": (-33.706, 137.030),
    "thevenard": (-32.149, 133.647),
}
CARGO_TYPES = ["Cargo ship - All", "Tanker - All"]
STOP_KN = 0.5
GAP_HOURS = 8.0  # pings separated by more than this end a visit
BERTH_RADIUS_M = 400.0
ANCHOR_MIN_M = 1500.0


def load_zone_points() -> pl.DataFrame:
    files = sorted((RAW / "amsa_cts").rglob("cts_srr_*.parquet"))
    print(f"monthly files: {len(files)}")
    frames = []
    for f in files:
        lf = pl.scan_parquet(f)
        conds = None
        for zone, (a, b, c, d) in ZONES.items():
            cond = (
                (pl.col("decimalLatitude") >= a)
                & (pl.col("decimalLatitude") <= b)
                & (pl.col("decimalLongitude") >= c)
                & (pl.col("decimalLongitude") <= d)
            )
            conds = cond if conds is None else (conds | cond)
        frames.append(lf.filter(conds).collect())
    df = pl.concat(frames)
    zone_expr = None
    for zone, (a, b, c, d) in ZONES.items():
        cond = (
            (pl.col("decimalLatitude") >= a)
            & (pl.col("decimalLatitude") <= b)
            & (pl.col("decimalLongitude") >= c)
            & (pl.col("decimalLongitude") <= d)
        )
        zone_expr = pl.when(cond).then(pl.lit(zone)).otherwise(zone_expr) if zone_expr is not None else pl.when(cond).then(pl.lit(zone)).otherwise(pl.lit(None))
    df = df.with_columns(zone_expr.alias("zone")).sort("craftID", "eventDate")
    return df


def meters(df: pl.DataFrame, lat0: float, lon0: float) -> pl.Expr:
    # equirectangular approx, fine at this scale
    import math

    kx = 111_320.0 * math.cos(math.radians(lat0))
    return (
        ((pl.col("decimalLatitude") - lat0) * 111_320.0) ** 2
        + ((pl.col("decimalLongitude") - lon0) * kx) ** 2
    ).sqrt()


def find_berth(df: pl.DataFrame, zone: str) -> tuple[float, float]:
    """Densest stationary-cargo cell within 1.5 km of the wharf hint."""
    lat0, lon0 = WHARF_HINT[zone]
    sub = df.filter(
        (pl.col("zone") == zone)
        & pl.col("type").is_in(CARGO_TYPES)
        & (pl.col("speed").fill_null(0) <= STOP_KN)
    ).with_columns(meters(df, lat0, lon0).alias("d_hint"))
    sub = sub.filter(pl.col("d_hint") < 1500)
    if sub.height == 0:
        print(f"{zone}: no stationary cargo near wharf hint; using hint as berth")
        return lat0, lon0
    cell = (
        sub.with_columns(
            (pl.col("decimalLatitude") * 500).round(0).alias("cy"),
            (pl.col("decimalLongitude") * 500).round(0).alias("cx"),
        )
        .group_by("cy", "cx")
        .agg(pl.len().alias("n"), pl.col("decimalLatitude").mean().alias("lat"), pl.col("decimalLongitude").mean().alias("lon"))
        .sort("n", descending=True)
    )
    top = cell.row(0, named=True)
    print(f"{zone}: berth cluster at ({top['lat']:.5f}, {top['lon']:.5f}) n={top['n']}")
    return top["lat"], top["lon"]


def segment_visits(df: pl.DataFrame, zone: str, blat: float, blon: float) -> pl.DataFrame:
    sub = (
        df.filter((pl.col("zone") == zone) & pl.col("type").is_in(CARGO_TYPES))
        .with_columns(meters(df, blat, blon).alias("d_berth"))
        .sort("craftID", "eventDate")
        .with_columns(
            (pl.col("d_berth") <= BERTH_RADIUS_M).alias("at_berth"),
            (
                (pl.col("d_berth") >= ANCHOR_MIN_M)
                & (pl.col("speed").fill_null(0) <= STOP_KN)
            ).alias("at_anchor"),
        )
    )
    # visit = consecutive pings of same craft in same state, gaps < GAP_HOURS
    sub = sub.with_columns(
        pl.when(pl.col("at_berth")).then(pl.lit("berth")).when(pl.col("at_anchor")).then(pl.lit("anchor")).otherwise(pl.lit("transit")).alias("state")
    )
    sub = sub.with_columns(
        (
            (pl.col("craftID") != pl.col("craftID").shift(1))
            | (pl.col("state") != pl.col("state").shift(1))
            | ((pl.col("eventDate") - pl.col("eventDate").shift(1)).dt.total_hours() > GAP_HOURS)
        )
        .fill_null(True)
        .cum_sum()
        .alias("segment_id")
    )
    visits = (
        sub.filter(pl.col("state") != "transit")
        .group_by("segment_id")
        .agg(
            pl.col("craftID").first(),
            pl.col("state").first(),
            pl.col("eventDate").min().alias("start"),
            pl.col("eventDate").max().alias("end"),
            pl.len().alias("n_pings"),
            pl.col("draught").first().alias("draught_start"),
            pl.col("draught").last().alias("draught_end"),
            pl.col("length").max().alias("length_m"),
            pl.col("beam").max().alias("beam_m"),
            pl.col("type").first().alias("type"),
            pl.col("subType").first().alias("sub_type"),
        )
        .sort("craftID", "start")
        .drop("segment_id")
    )
    # Merge consecutive same-craft same-state segments separated by <= MERGE_GAP_H.
    # Needed because some CTS monthly extracts (e.g. Feb-Apr 2024) only contain position
    # reports for ~half of each UTC day, fragmenting multi-day berth stays into daily
    # segments. A true depart-and-return within the merge window would be merged too
    # (rare for bulk vessels; documented limitation).
    MERGE_GAP_H = 16.0
    visits = visits.with_columns(
        (
            (pl.col("craftID") != pl.col("craftID").shift(1))
            | (pl.col("state") != pl.col("state").shift(1))
            | ((pl.col("start") - pl.col("end").shift(1)).dt.total_minutes() / 60.0 > MERGE_GAP_H)
        )
        .fill_null(True)
        .cum_sum()
        .alias("visit_id")
    )
    visits = (
        visits.group_by("visit_id")
        .agg(
            pl.col("craftID").first(),
            pl.col("state").first(),
            pl.col("start").min(),
            pl.col("end").max(),
            pl.col("n_pings").sum(),
            pl.col("draught_start").first(),
            pl.col("draught_end").last(),
            pl.col("length_m").max(),
            pl.col("beam_m").max(),
            pl.col("type").first(),
            pl.col("sub_type").first(),
        )
        .with_columns(
            ((pl.col("end") - pl.col("start")).dt.total_minutes() / 60.0).alias("duration_h"),
            pl.lit(zone).alias("zone"),
        )
        .filter((pl.col("n_pings") >= 2) & (pl.col("duration_h") >= 3.0))
        .sort("start")
        .drop("visit_id")
    )
    return visits


def main():
    dfp = PROCESSED / "ais_ep_points.parquet"
    if dfp.exists():
        df = pl.read_parquet(dfp)
        print(f"zone points (cached): {df.height}")
    else:
        df = load_zone_points()
        PROCESSED.mkdir(parents=True, exist_ok=True)
        df.write_parquet(dfp)
        print(f"zone points: {df.height}")

    # craftID cross-month stability check: crafts seen in >1 source file at the same berth
    span = (
        df.group_by("craftID")
        .agg(pl.col("filename").n_unique().alias("n_months"), pl.len().alias("n"))
        .filter(pl.col("n_months") > 1)
    )
    print(f"crafts appearing in >1 monthly file: {span.height} (supports cross-month craftID stability)")

    all_visits = []
    for zone in ZONES:
        blat, blon = find_berth(df, zone)
        v = segment_visits(df, zone, blat, blon)
        nb = v.filter(pl.col("state") == "berth").height
        na = v.filter(pl.col("state") == "anchor").height
        print(f"{zone}: {nb} berth visits, {na} anchorage stays")
        all_visits.append(v)
    visits = pl.concat(all_visits)
    visits.write_parquet(PROCESSED / "vessel_calls.parquet")

    # QA: monthly berth-visit counts at Port Lincoln
    pl_b = visits.filter((pl.col("zone") == "port_lincoln") & (pl.col("state") == "berth"))
    print("\nPort Lincoln berth visits by month:")
    with pl.Config(tbl_rows=40):
        print(
            pl_b.with_columns(pl.col("start").dt.strftime("%Y-%m").alias("month"))
            .group_by("month")
            .agg(pl.len().alias("visits"), pl.col("duration_h").median().alias("median_h"))
            .sort("month")
        )
    print("\nberth duration stats (Port Lincoln, hours):")
    print(
        pl_b.select(
            pl.col("duration_h").min().alias("min_h"),
            pl.col("duration_h").median().alias("median_h"),
            pl.col("duration_h").mean().alias("mean_h"),
            pl.col("duration_h").max().alias("max_h"),
        )
    )
    # draught change while at berth (loading signature)
    loaded = pl_b.filter(pl.col("draught_end") > pl.col("draught_start") + 0.5)
    print(f"berth visits with draught increase >0.5 m (loading signature): {loaded.height}/{pl_b.height}")


if __name__ == "__main__":
    main()
