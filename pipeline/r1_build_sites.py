"""R1: build data/processed/sites.geojson.

Merges:
- operator API site details (data/raw/operator_sites/) - facility coordinates, names
- pipeline/manual_sites.json - T-Ports + closed sites, segregations, port capacities
- data/raw/osm/silos_ep.json (if present) - nearest OSM silo feature distance as a QA field

Every feature carries provenance fields. Bunge sites active in 2025/26 = those with
segregations listed; the 5 strategic/dormant sites are kept with status "dormant".

Also assigns each site a PIRSA district (LGA point-in-polygon, ASSUMPTIONS A14 - the
same mapping r4_build_demand.py uses for CLUM cropping cells) and, for the Bunge
upcountry sites whose capacity is NOT published, an estimated capacity_t following the
A4 method: the unpublished upcountry storage total is split between districts in
proportion to their long-run receivals, then evenly between that district's sites.
See ASSUMPTIONS.md A4 for the derivation and its limits.
"""
from __future__ import annotations

import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import polars as pl
from shapely.geometry import Point, shape
from shapely.prepared import prep

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import PROCESSED, RAW, ROOT

PORT_ROLES = {"PORT LINCOLN": "port", "THEVENARD": "port"}

# ASSUMPTIONS A14: PIRSA EP district composition by LGA. Kept identical to
# r4_build_demand.py's LGA_DISTRICT - if one changes, change both.
LGA_DISTRICT = {
    "CITY OF PORT LINCOLN": "LEP",
    "LOWER EYRE PENINSULA": "LEP",
    "TUMBY BAY": "LEP",
    "CLEVE": "EEP",
    "FRANKLIN HARBOUR": "EEP",
    "KIMBA": "EEP",
    "WUDINNA": "WEP",
    "ELLISTON": "WEP",
    "STREAKY BAY": "WEP",
    "CEDUNA": "WEP",
}
# A20's "long-run" window: the four seasons PIRSA district estimates cover.
LONGRUN_SEASONS = ["2022/23", "2023/24", "2024/25", "2025/26"]

# --- A12: per-season operating sets from the operator's own weekly narratives -----------
# A sentence must carry a receival verb before a site name in it counts as evidence that
# the site OPERATED that season. Absence of a mention is NOT evidence of closure: the
# reports name a site at its first receival of the season and when it is notable, not
# every week, so `operating_seasons` is a lower bound and must never be read as a roster.
RECEIVAL_TRIGGER = re.compile(
    r"receiv|deliver|kicked off|first load|taking grain|welcomed|opening for", re.I
)
# "...east of Kyancutta" locates a grower's paddock; it is not a receival at Kyancutta.
LOCATIONAL_PREFIX = re.compile(r"\b(east|west|north|south|near|outside|via)\s+(of\s+)?$", re.I)


def _named_as_site(sentence: str, name: str) -> bool:
    for m in re.finditer(r"\b" + re.escape(name) + r"\b", sentence, re.I):
        if LOCATIONAL_PREFIX.search(sentence[max(0, m.start() - 24) : m.start()]):
            continue
        return True
    return False


def annotate_operating_seasons(features: list[dict]) -> None:
    """Attach `operating_seasons` (+ a quote) to every feature, and correct any Bunge site
    tagged dormant that the operator's own 2025/26 reports show receiving grain.

    This implements A12, which until now was documented but not built: nothing in the
    pipeline or the engine varied the site set by season.
    """
    notes = PROCESSED / "receivals_notes.jsonl"
    if not notes.exists():
        print("WARNING: receivals_notes.jsonl absent - operating_seasons not derived")
        return
    # Match on the base name ("Cungena (closed)" -> "Cungena"), but skip T-Ports features:
    # these are Bunge/Viterra's own reports, so a bare "Kimba" or "Lock" in them is the
    # Bunge site, never the T-Ports bunker in the same town.
    match_name = {
        f["properties"]["name"]: re.sub(r"\s*\(.*\)", "", f["properties"]["name"]).strip()
        for f in features
        if f["properties"]["operator"] != "T-Ports"
    }
    per: dict[str, set[str]] = defaultdict(set)
    evidence: dict[tuple[str, str], str] = {}
    with notes.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            season, week = r.get("season"), r.get("week_ending")
            for sent in re.split(r"(?<=[.!?])\s+", " ".join(r.get("narrative") or [])):
                if not RECEIVAL_TRIGGER.search(sent):
                    continue
                for full, base in match_name.items():
                    if _named_as_site(sent, base):
                        per[season].add(full)
                        evidence.setdefault((full, season), f"[{week}] {sent.strip()[:180]}")

    corrected = []
    for f in features:
        p = f["properties"]
        seasons = sorted(s for s, st in per.items() if p["name"] in st)
        p["operating_seasons"] = seasons
        p["operating_seasons_source"] = (
            "operator weekly harvest reports (data/processed/receivals_notes.jsonl); "
            "positive evidence only - absence of a mention is NOT evidence of closure"
        )
        p["operating_evidence"] = evidence.get((p["name"], seasons[-1])) if seasons else None
        # The segregations table was read off-season (2026-08-19), when a site between
        # harvests correctly lists no segregations. Reading that emptiness as "dormant"
        # closed five sites the operator's own reports show taking 2025/26 deliveries.
        if p["status"] == "dormant" and "2025/26" in seasons:
            p["status"] = "active_2025_26"
            p["status_provenance"] = (
                "corrected: off-season segregations read listed none, but the operator's "
                f"own 2025/26 weekly report names it receiving - {p['operating_evidence']}"
            )
            corrected.append(p["name"])
        elif p["status"] == "closed_2019" and any(s >= "2020/21" for s in seasons):
            print(
                f"WARNING: {p['name']} is tagged closed_2019 but is named receiving in "
                f"{[s for s in seasons if s >= '2020/21']} - {p['operating_evidence']}"
            )
    if corrected:
        print(f"\nA12 status corrections (dormant -> active_2025_26): {', '.join(corrected)}")
    still = [
        f["properties"]["name"] for f in features if f["properties"]["status"] == "dormant"
    ]
    if still:
        print(f"  still dormant (no 2025/26 receival evidence): {', '.join(still)}")


def dist_m(lat1, lon1, lat2, lon2):
    kx = 111_320.0 * math.cos(math.radians(lat1))
    return math.hypot((lat1 - lat2) * 111_320.0, (lon1 - lon2) * kx)


def load_osm_silos() -> list[tuple[float, float]]:
    f = RAW / "osm" / "silos_ep.json"
    if not f.exists():
        return []
    j = json.loads(f.read_text(encoding="utf-8"))
    pts = []
    for el in j.get("elements", []):
        if "lat" in el:
            pts.append((el["lat"], el["lon"]))
        elif "center" in el:
            pts.append((el["center"]["lat"], el["center"]["lon"]))
    return pts


def load_district_polygons():
    """Prepared LGA polygons tagged with their PIRSA district (A14)."""
    lga_dir = RAW / "sa_lga"
    gj_files = [f for f in list(lga_dir.glob("*.geojson")) + list(lga_dir.glob("*.json")) if not f.name.endswith(".zip")]
    j = json.loads(sorted(gj_files)[0].read_text(encoding="utf-8"))
    feats = j["features"]
    name_key = next(k for k in feats[0]["properties"] if "name" in k.lower())
    out = []
    for f in feats:
        nm = str(f["properties"].get(name_key, "")).upper()
        for lga, dist in LGA_DISTRICT.items():
            if lga in nm or nm in lga:
                out.append((prep(shape(f["geometry"])), dist))
                break
    print(f"LGA polygons matched: {len(out)}/{len(LGA_DISTRICT)} (name key: {name_key})")
    return out


def district_of(lon: float, lat: float, polys) -> str | None:
    for pp, dist in polys:
        if pp.contains(Point(lon, lat)):
            return dist
    # unincorporated far-west cropping strip (Penong / Nullarbor fringe): same fallback
    # r4_build_demand.py applies to CLUM cells that land outside every LGA polygon
    if lon < 134.7 and lat > -33.2:
        return "WEP"
    return None


def longrun_district_shares() -> dict[str, float]:
    """Each PIRSA district's share of long-run EP production (A20 window)."""
    prod = pl.read_parquet(PROCESSED / "production_districts.parquet").filter(
        (pl.col("crop") == "TOTAL") & pl.col("season").is_in(LONGRUN_SEASONS)
    )
    means = prod.group_by("district").agg(pl.col("production_t").mean().alias("t"))
    total = float(means["t"].sum())
    return {r["district"]: float(r["t"]) / total for r in means.to_dicts()}


def upcountry_storage_target(port_caps: dict) -> tuple[int, int, int]:
    """A4: max Western season receivals - published Western port storage."""
    rec = pl.read_parquet(PROCESSED / "receivals_weekly.parquet").filter(pl.col("region") == "western")
    max_harvest = int(rec.group_by("season").agg(pl.col("cum_t").max().alias("t"))["t"].max())
    port_total = int(sum(v for k, v in port_caps.items() if not k.startswith("_")))
    return max_harvest - port_total, max_harvest, port_total


def allocate_capacities(features: list[dict], polys, port_caps: dict) -> None:
    """Write district + estimated capacity_t onto the Bunge upcountry features (A4)."""
    for f in features:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        p["district"] = district_of(lon, lat, polys)
        p["capacity_estimated"] = p.get("capacity_t") is None

    target, max_harvest, port_total = upcountry_storage_target(port_caps)
    shares = longrun_district_shares()

    # every Bunge upcountry site holds grain when it is operated, dormant ones included
    # (A12 re-enables them in earlier seasons), so all of them share the storage total
    pool = [f for f in features if f["properties"]["operator"].startswith("Bunge") and f["properties"]["role"] == "upcountry"]
    missing = [f["properties"]["name"] for f in pool if f["properties"]["district"] is None]
    if missing:
        raise SystemExit(f"no PIRSA district for upcountry site(s): {missing}")
    n_by_district: dict[str, int] = {}
    for f in pool:
        d = f["properties"]["district"]
        n_by_district[d] = n_by_district.get(d, 0) + 1

    prov = (
        "estimated (not published): A4 method - long-run district receivals share "
        f"(mean PIRSA district production {LONGRUN_SEASONS[0]}-{LONGRUN_SEASONS[-1]}) allocated across that "
        f"district's Bunge upcountry sites, scaled so all {len(pool)} of them total "
        f"{target/1e6:.2f} Mt (max Western season receivals {max_harvest/1e6:.2f} Mt "
        f"- published Western port storage {port_total/1e6:.2f} Mt)"
    )
    print(f"\nA4 upcountry storage target: {max_harvest:,} - {port_total:,} = {target:,} t over {len(pool)} sites")
    per_site = {d: int(round(target * shares[d] / n, -2)) for d, n in n_by_district.items()}
    for f in pool:
        f["properties"]["capacity_t"] = per_site[f["properties"]["district"]]
        f["properties"]["capacity_provenance"] = prov
        f["properties"]["capacity_estimated"] = True
    for d in sorted(n_by_district):
        print(f"  {d}: share {shares[d]:.3f} over {n_by_district[d]} sites -> {per_site[d]:,} t each")
    allocated = sum(f["properties"]["capacity_t"] for f in pool)
    opened = sum(f["properties"]["capacity_t"] for f in pool if f["properties"]["status"] == "active_2025_26")
    print(f"  allocated {allocated:,.0f} t ({allocated/1e6:.3f} Mt); operated in 2025/26: {opened/1e6:.3f} Mt")


def main():
    manual = json.loads((ROOT / "pipeline" / "manual_sites.json").read_text(encoding="utf-8"))
    segs = manual["segregations_2025_26"]
    caps = manual["port_capacities"]
    silos = load_osm_silos()
    print(f"osm silo features available: {len(silos)}")

    features = []
    for f in sorted((RAW / "operator_sites").glob("site_*.json")):
        detail = json.loads(f.read_text(encoding="utf-8"))
        d = detail[0] if isinstance(detail, list) else detail
        name = d["site"]
        if name.upper().startswith("PT "):
            name = "PORT " + name[3:]  # operator API abbreviates (PT LINCOLN, PT NEILL)
        lat, lon = d["latitude"], d["longitude"]
        commodities = segs.get(name)
        status = "active_2025_26" if commodities else ("dormant" if commodities == [] else "unknown")
        role = PORT_ROLES.get(name, "upcountry")
        props = {
            "name": name.title(),
            "operator": "Bunge (ex-Viterra)",
            "role": role,
            "status": status,
            "coord_precision": "facility",
            "coord_source": f"operator API mobilews.viterra.com.au/api/Sites/{d['id']} (retrieved 2026-08-19)",
            "commodities_2025_26": commodities or [],
            "commodities_source": segs["_source"] if commodities is not None else None,
            "capacity_t": caps.get(name),
            "capacity_provenance": caps["_source"] if name in caps else None,
            "region": "western",
        }
        if silos:
            nd = min(dist_m(lat, lon, s[0], s[1]) for s in silos)
            props["nearest_osm_silo_m"] = round(nd)
        features.append(
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": props}
        )

    for s in manual["extra_sites"]:
        props = {
            "name": s["name"],
            "operator": s["operator"],
            "role": s["role"],
            "status": s["status"],
            "coord_precision": s["coord_precision"],
            "coord_source": s["coord_source"],
            "commodities_2025_26": s["commodities"],
            "commodities_source": s.get("commodities_source"),
            "capacity_t": s["capacity_t"],
            "capacity_provenance": s.get("capacity_source"),
            "region": "western",
            "sources": s["sources"],
            "notes": s.get("notes"),
        }
        if silos and s["capacity_t"]:
            nd = min(dist_m(s["lat"], s["lon"], p[0], p[1]) for p in silos)
            props["nearest_osm_silo_m"] = round(nd)
        features.append(
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [s["lon"], s["lat"]]}, "properties": props}
        )

    # A12 must run BEFORE capacity allocation: allocation reports the operated total,
    # and four of the sites it would otherwise report as closed are in fact operating.
    annotate_operating_seasons(features)
    allocate_capacities(features, load_district_polygons(), caps)

    gj = {
        "type": "FeatureCollection",
        "name": "windrow_sites",
        "metadata": {
            "generated": "pipeline/r1_build_sites.py",
            "notes": "EP + far west grain receival sites. Coordinates: operator API (facility) or OSM town nodes (town). Bunge upcountry capacities are NOT published: those carry capacity_estimated=true and an estimate allocated by PIRSA district (ASSUMPTIONS.md A4). capacity_estimated=false marks the five published figures.",
            "attribution": ["Site data (c) Bunge/Viterra operator API", "OpenStreetMap contributors (ODbL) for town coordinates"],
        },
        "features": features,
    }
    PROCESSED.mkdir(parents=True, exist_ok=True)
    (PROCESSED / "sites.geojson").write_text(json.dumps(gj, indent=1), encoding="utf-8")
    n_active = sum(1 for f in features if f["properties"]["status"] == "active_2025_26")
    print(f"features: {len(features)} (active 2025/26 Bunge: {n_active}); wrote sites.geojson")
    for f in features:
        p = f["properties"]
        extra = f" silo@{p.get('nearest_osm_silo_m','?')}m" if "nearest_osm_silo_m" in p else ""
        cap = f"{p['capacity_t']:>7,.0f} t{'*' if p['capacity_estimated'] else ' '}" if p["capacity_t"] else "      - "
        print(f"  {p['name']:28s} {p['operator']:18s} {p['role']:9s} {p['status']:22s} {str(p['district']):4s} {cap} {p['coord_precision']}{extra}")
    print("  (* = estimated, not published)")


if __name__ == "__main__":
    main()
