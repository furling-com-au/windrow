"""R6: build a routable road graph from the OSM extract.

Input : data/raw/osm/roads_ep.json (Overpass, ODbL - OpenStreetMap contributors)
Output: data/processed/roads.graph.json
        { nodes: {id: [lon, lat]},
          edges: [[u, v, length_m, class]],
          geometry: {edge_index: [[lon,lat], ...]},   # polyline per edge for rendering
          meta: {...} }

QA: largest-connected-component share, site snap distances, Cummins->Port Lincoln
shortest path (published road distance ~ 68 km).
Default speeds by class are ASSUMPTIONS (see ASSUMPTIONS.md) applied later in the sim.
"""
from __future__ import annotations

import heapq
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import PROCESSED, RAW


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def main():
    j = json.loads((RAW / "osm" / "roads_ep.json").read_text(encoding="utf-8"))
    ways = [e for e in j["elements"] if e["type"] == "way" and "geometry" in e]
    print(f"ways: {len(ways)}")

    # "out tags geom" returns coordinates but no node ids -> synthesize node identity
    # from coordinates quantized to ~1e-6 deg (OSM shared nodes have identical coords).
    def key(g) -> int:
        return hash((round(g["lat"], 6), round(g["lon"], 6)))

    node_use = defaultdict(int)
    for w in ways:
        for g in w["geometry"]:
            node_use[key(g)] += 1
        node_use[key(w["geometry"][0])] += 1  # endpoints always split
        node_use[key(w["geometry"][-1])] += 1

    nodes: dict[int, tuple[float, float]] = {}
    edges: list[tuple[int, int, float, str]] = []
    geometry: list[list[list[float]]] = []
    for w in ways:
        hw = w["tags"].get("highway", "unclassified")
        geom = w["geometry"]
        nids = [key(g) for g in geom]
        seg_start = 0
        acc = 0.0
        for i in range(1, len(nids)):
            acc += haversine_m(geom[i - 1]["lat"], geom[i - 1]["lon"], geom[i]["lat"], geom[i]["lon"])
            if node_use[nids[i]] > 1 or i == len(nids) - 1:
                u, v = nids[seg_start], nids[i]
                nodes[u] = (geom[seg_start]["lon"], geom[seg_start]["lat"])
                nodes[v] = (geom[i]["lon"], geom[i]["lat"])
                poly = [[round(g["lon"], 6), round(g["lat"], 6)] for g in geom[seg_start : i + 1]]
                edges.append((u, v, round(acc, 1), hw))
                geometry.append(poly)
                seg_start = i
                acc = 0.0
    print(f"nodes: {len(nodes)}, edges: {len(edges)}")

    # largest connected component
    adj = defaultdict(list)
    for idx, (u, v, L, hw) in enumerate(edges):
        adj[u].append((v, L))
        adj[v].append((u, L))
    seen: set[int] = set()
    best_comp: set[int] = set()
    for start in nodes:
        if start in seen:
            continue
        comp = {start}
        stack = [start]
        seen.add(start)
        while stack:
            n = stack.pop()
            for m, _ in adj[n]:
                if m not in seen:
                    seen.add(m)
                    comp.add(m)
                    stack.append(m)
        if len(comp) > len(best_comp):
            best_comp = comp
    print(f"largest component: {len(best_comp)}/{len(nodes)} nodes ({100*len(best_comp)/len(nodes):.1f}%)")

    # drop edges not in main component (disconnected fragments, islands)
    keep = [i for i, (u, v, L, hw) in enumerate(edges) if u in best_comp]
    edges2 = [edges[i] for i in keep]
    geometry2 = [geometry[i] for i in keep]
    used_nodes = {u for u, v, _, _ in edges2} | {v for u, v, _, _ in edges2}
    nodes2 = {n: nodes[n] for n in used_nodes}
    print(f"after pruning to main component: {len(nodes2)} nodes, {len(edges2)} edges")

    def nearest(lat, lon):
        return min(nodes2, key=lambda n: (nodes2[n][1] - lat) ** 2 + (nodes2[n][0] - lon) ** 2)

    # site snapping QA
    sites = json.loads((PROCESSED / "sites.geojson").read_text(encoding="utf-8"))
    worst = 0.0
    for f in sites["features"]:
        lon, lat = f["geometry"]["coordinates"]
        n = nearest(lat, lon)
        d = haversine_m(lat, lon, nodes2[n][1], nodes2[n][0])
        worst = max(worst, d)
        if d > 2000:
            print(f"  WARN: {f['properties']['name']} snaps {d/1000:.1f} km from graph")
    print(f"worst site snap distance: {worst:.0f} m")

    # Dijkstra smoke test: Cummins silo -> Port Lincoln terminal
    adj2 = defaultdict(list)
    for u, v, L, hw in edges2:
        adj2[u].append((v, L))
        adj2[v].append((u, L))
    src, dst = nearest(-34.2713, 135.7277), nearest(-34.7221, 135.8659)
    dist = {src: 0.0}
    pq = [(0.0, src)]
    while pq:
        d, n = heapq.heappop(pq)
        if n == dst:
            break
        if d > dist.get(n, 1e18):
            continue
        for m, L in adj2[n]:
            nd = d + L
            if nd < dist.get(m, 1e18):
                dist[m] = nd
                heapq.heappush(pq, (nd, m))
    print(f"Cummins -> Port Lincoln shortest path: {dist.get(dst, float('nan'))/1000:.1f} km (published road distance ~68 km)")

    out = {
        "meta": {
            "source": "OpenStreetMap via Overpass API, retrieved 2026-08-19",
            "licence": "ODbL - (c) OpenStreetMap contributors",
            "bbox": [-35.25, 131.0, -31.0, 137.65],
            "classes": sorted({hw for _, _, _, hw in edges2}),
            "note": "speeds by class are simulation parameters (see ASSUMPTIONS.md), not stored here",
        },
        "nodes": {str(n): [round(lon, 6), round(lat, 6)] for n, (lon, lat) in nodes2.items()},
        "edges": [[str(u), str(v), L, hw] for u, v, L, hw in edges2],
        "geometry": geometry2,
    }
    dest = PROCESSED / "roads.graph.json"
    dest.write_text(json.dumps(out), encoding="utf-8")
    print(f"wrote {dest.name}: {dest.stat().st_size/1e6:.1f} MB")


if __name__ == "__main__":
    main()
