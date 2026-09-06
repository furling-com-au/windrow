"""Phase 2: catchment clusters, travel-time matrix, and route polylines.

- Parcels (2.5 km demand cells) are grouped into ~12 km catchment CLUSTERS: the unit for
  truck logistics (spec: "paddock-cluster -> site" matrix).
- Drive minutes computed on the OSM graph with A5 speeds; the network distance ALONG the
  same fastest path is carried out with them, so the sim never has to back out km from
  minutes at a single blended speed (that understated trunk hauls and overstated farm legs).
- Route POLYLINES (simplified) are emitted for every cluster->candidate-site pair and
  site->port pair so the browser renders trucks along real roads without routing.

Outputs (app/public/data/):
  matrix.json  {sites[], site_minutes[][], site_km[][], clusters[],
                cluster_site_minutes{cid:{sid:min}}, cluster_site_km{cid:{sid:km}}}
  paths.json   {cluster_site: {"cid-sid": [[lon,lat],...]}, site_site: {"i-j": [...]}}
  parcels.json (updated in place with cluster_id per parcel)
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import PROCESSED, ROOT
from roads import SPEED_KMH, dijkstra, load_graph, make_snapper  # A5 lives in roads.py

APP_DATA = ROOT / "app" / "public" / "data"
PORT_NAMES = {"Port Lincoln", "Thevenard", "Lucky Bay (T-Ports port)"}
CLUSTER_DEG = 0.12  # ~12 km
N_CANDIDATES = 8


def simplify(points: list[list[float]], tol_deg: float = 0.004) -> list[list[float]]:
    """Douglas-Peucker."""
    if len(points) < 3:
        return points

    def dp(pts):
        if len(pts) < 3:
            return pts
        x1, y1 = pts[0]
        x2, y2 = pts[-1]
        dx, dy = x2 - x1, y2 - y1
        norm = math.hypot(dx, dy) or 1e-12
        dmax, idx = 0.0, 0
        for i in range(1, len(pts) - 1):
            d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / norm
            if d > dmax:
                dmax, idx = d, i
        if dmax > tol_deg:
            left = dp(pts[: idx + 1])
            right = dp(pts[idx:])
            return left[:-1] + right
        return [pts[0], pts[-1]]

    return dp(points)


def main():
    nodes, edges, geometry, adj = load_graph()
    snap = make_snapper(nodes)

    def nearest(lon: float, lat: float) -> str:
        return snap(lon, lat)[0]

    def path_polyline(prev, src: str, dst: str) -> list[list[float]]:
        if dst not in prev and dst != src:
            return []
        pts: list[list[float]] = []
        n = dst
        while n != src:
            p, ei = prev[n]
            seg = geometry[ei]
            # orient segment from p -> n
            u = edges[ei][0]
            s = seg if u == p else seg[::-1]
            pts = s[:-1] + pts if pts else s
            n = p
        return simplify(pts)

    # sites
    sj = json.loads((PROCESSED / "sites.geojson").read_text(encoding="utf-8"))
    sites = []
    for f in sj["features"]:
        p = f["properties"]
        if p["role"] == "closed":
            continue
        lon, lat = f["geometry"]["coordinates"]
        sites.append(
            {
                "id": len(sites),
                "name": p["name"],
                "role": "port" if p["name"] in PORT_NAMES or p["role"] == "port" else "upcountry",
                "operator": p["operator"],
                "status": p["status"],
                "lon": lon,
                "lat": lat,
                "capacity_t": p.get("capacity_t"),
                # True where capacity_t is the A4 district allocation rather than a
                # published figure: the engine's capacity lever moves only those.
                "capacity_estimated": bool(p.get("capacity_estimated")),
                "commodities": p.get("commodities_2025_26") or [],
                # Seasons in which the site did not operate (data, not engine code): the
                # engine closes a site for any season listed here. Empty = open whenever
                # its status is not dormant.
                "closed_seasons": p.get("closed_seasons") or [],
            }
        )
    # A site the engine will treat as open must accept something. `chooseSite` skips any
    # site whose segregation list is empty, so an open site with `commodities: []` sits in
    # the network looking open and receives zero tonnes all season - and takes carry-in
    # stock by capacity share it could never have received. This is exactly how the four
    # A12-corrected sites shipped on 2026-08-31 (status active, no segregations): fail
    # the build here, so the data gets an assumed list (A12) rather than the engine a guess.
    bad = [s["name"] for s in sites
           if s["role"] != "port" and s["status"] != "dormant" and not s["commodities"]]
    if bad:
        raise SystemExit(
            f"sites open in some season but with no segregations: {', '.join(bad)}. "
            "Give each an (assumed, A12-style) commodity list in pipeline/manual_sites.json."
        )
    print(f"routing sites: {len(sites)}")
    site_nodes = [nearest(s["lon"], s["lat"]) for s in sites]
    site_results = [dijkstra(adj, nd) for nd in site_nodes]  # (minutes, km, prev)
    n = len(sites)
    site_minutes = [[round(site_results[i][0].get(site_nodes[j], -1.0), 1) for j in range(n)] for i in range(n)]
    site_km = [[round(site_results[i][1].get(site_nodes[j], -1.0), 2) for j in range(n)] for i in range(n)]

    # clusters from parcels
    pj = json.loads((APP_DATA / "parcels.json").read_text(encoding="utf-8"))
    parcels = pj["parcels"]
    cl_map: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for p in parcels:
        cl_map[(int(p["lon"] / CLUSTER_DEG), int(p["lat"] / CLUSTER_DEG))].append(p)
    clusters = []
    for key, plist in sorted(cl_map.items()):
        ha = sum(p["cropping_ha"] for p in plist)
        lon = sum(p["lon"] * p["cropping_ha"] for p in plist) / ha
        lat = sum(p["lat"] * p["cropping_ha"] for p in plist) / ha
        cid = len(clusters)
        for p in plist:
            p["cluster_id"] = cid
        # majority district
        dh: dict[str, float] = defaultdict(float)
        for p in plist:
            dh[p["district"]] += p["cropping_ha"]
        clusters.append(
            {"id": cid, "lon": round(lon, 4), "lat": round(lat, 4), "cropping_ha": round(ha, 1),
             "district": max(dh, key=dh.get), "n_parcels": len(plist)}
        )
    print(f"clusters: {len(clusters)}")
    (APP_DATA / "parcels.json").write_text(json.dumps({"parcels": parcels}), encoding="utf-8")

    cluster_nodes = [nearest(c["lon"], c["lat"]) for c in clusters]
    port_idx = [i for i, s in enumerate(sites) if s["role"] == "port"]

    cluster_site_minutes: dict[str, dict[str, float]] = {}
    cluster_site_km: dict[str, dict[str, float]] = {}
    paths_cs: dict[str, list[list[float]]] = {}
    for ci, cn in enumerate(cluster_nodes):
        times = []
        for si in range(n):
            t = site_results[si][0].get(cn)
            if t is not None:
                times.append((t, si))
        times.sort()
        chosen = {si for _, si in times[:N_CANDIDATES]} | set(port_idx)
        cluster_site_minutes[str(ci)] = {str(si): round(t, 1) for t, si in times if si in chosen}
        cluster_site_km[str(ci)] = {
            str(si): round(site_results[si][1].get(cn, -1.0), 2) for _, si in times if si in chosen
        }
        for t, si in times:
            if si in chosen:
                poly = path_polyline(site_results[si][2], site_nodes[si], cn)
                if poly:
                    paths_cs[f"{ci}-{si}"] = [[round(x, 4), round(y, 4)] for x, y in poly]

    paths_ss: dict[str, list[list[float]]] = {}
    for si in range(n):
        for pi in port_idx:
            if si == pi:
                continue
            poly = path_polyline(site_results[pi][2], site_nodes[pi], site_nodes[si])
            if poly:
                paths_ss[f"{si}-{pi}"] = [[round(x, 4), round(y, 4)] for x, y in poly]

    matrix = {
        "meta": {"speeds_kmh": SPEED_KMH, "cluster_deg": CLUSTER_DEG,
                 "note": "drive minutes on OSM network (ODbL (c) OpenStreetMap contributors); speeds = assumption A5",
                 "km_note": "*_km are network distances along the same fastest path as *_minutes, "
                            "summed from OSM way lengths -- do not re-derive km from minutes"},
        "sites": sites,
        "site_minutes": site_minutes,
        "site_km": site_km,
        "clusters": clusters,
        "cluster_site_minutes": cluster_site_minutes,
        "cluster_site_km": cluster_site_km,
    }
    (APP_DATA / "matrix.json").write_text(json.dumps(matrix), encoding="utf-8")
    (APP_DATA / "paths.json").write_text(json.dumps({"cluster_site": paths_cs, "site_port": paths_ss}), encoding="utf-8")
    print(f"matrix.json: {(APP_DATA/'matrix.json').stat().st_size/1e6:.2f} MB; paths.json: {(APP_DATA/'paths.json').stat().st_size/1e6:.2f} MB")

    def sidx(name):
        return next(i for i, s in enumerate(sites) if name.lower() in s["name"].lower())
    for a, b in (("Cummins", "Port Lincoln"), ("Kimba", "Lucky Bay")):
        i, j = sidx(a), sidx(b)
        mins, km = site_minutes[i][j], site_km[i][j]
        print(f"{a} -> {b}: {mins} min, {km} km ({km / (mins / 60):.0f} km/h implied)")


if __name__ == "__main__":
    main()
