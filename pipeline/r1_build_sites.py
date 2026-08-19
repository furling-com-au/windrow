"""R1: build data/processed/sites.geojson.

Merges:
- operator API site details (data/raw/operator_sites/) - facility coordinates, names
- pipeline/manual_sites.json - T-Ports + closed sites, segregations, port capacities
- data/raw/osm/silos_ep.json (if present) - nearest OSM silo feature distance as a QA field

Every feature carries provenance fields. Bunge sites active in 2025/26 = those with
segregations listed; the 5 strategic/dormant sites are kept with status "dormant".
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import PROCESSED, RAW, ROOT

PORT_ROLES = {"PORT LINCOLN": "port", "THEVENARD": "port"}


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

    gj = {
        "type": "FeatureCollection",
        "name": "windrow_sites",
        "metadata": {
            "generated": "pipeline/r1_build_sites.py",
            "notes": "EP + far west grain receival sites. Coordinates: operator API (facility) or OSM town nodes (town). Capacities only where published; upcountry Bunge capacities are NOT published (see ASSUMPTIONS.md).",
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
        print(f"  {p['name']:28s} {p['operator']:18s} {p['role']:9s} {p['status']:22s} {p['coord_precision']}{extra}")


if __name__ == "__main__":
    main()
