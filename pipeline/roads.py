"""Shared road-network routing for the pipeline.

ONE copy of everything that turns data/processed/roads.graph.json into distances:

- ``SPEED_KMH``            A5 loaded-grain-truck speeds by OSM class. This is the ONLY
                           place they live. matrix.json (the engine's input) and every
                           r8/r9/r10 published minute or km figure read this dict.
- ``load_graph``           nodes, edges, geometry and the weighted adjacency.
- ``make_snapper``         nearest road node to a coordinate, with the snap error in km.
- ``dijkstra``             least-TIME tree carrying the km driven along that same path
                           (A5: km must never be recovered as minutes x speed).
- ``dijkstra_km``          least-DISTANCE tree, for the A5-free sensitivity only.
- ``snap_sites`` / ``snap_parcels``   the site and parcel snapping every r8-r10 script
                           needs, so all of them carry the same record shape.
- ``displace`` + ``SWEEP_*``          the A11 coordinate-sweep grid, declared once.

History: until 2026-09-06 p2_build_matrix.py, r8_choice_geometry.py and r9_cartage.py
each carried their own copy of the graph build, the grid snapper and a Dijkstra, and six
scripts copy-pasted the site-snap loop with three different dict schemas. The snapper
copies shared a bug (see ``make_snapper``), which is the kind of thing one copy prevents.
"""
from __future__ import annotations

import heapq
import json
import math
from collections import defaultdict
from pathlib import Path

from wlib import PROCESSED

INF = float("inf")

# A5 road speeds by OSM class, loaded grain truck.
SPEED_KMH = {
    "trunk": 90.0, "primary": 90.0, "secondary": 80.0,
    "tertiary": 70.0, "unclassified": 60.0, "residential": 40.0,
}
DEFAULT_SPEED_KMH = 60.0

# Grid cell for the nearest-node snapper, in degrees (~5 km).
SNAP_CELL_DEG = 0.05

# A11 coordinate sweep: displacement magnitudes and bearings, shared by r8 (Lock/Kimba),
# r8a (Lucky Bay, mixed magnitudes), r9 (both) and r10d (Lucky Bay). Declared once so the
# scripts that claim to run "the same grid" cannot drift apart.
SWEEP_OFFSET_KM = (0.0, 2.5, 5.0)
SWEEP_BEARINGS_DEG = (0, 45, 90, 135, 180, 225, 270, 315)

# adjacency entry: (neighbour node id, minutes, km, edge index)
Adj = dict[str, list[tuple[str, float, float, int]]]


def load_graph(path: Path | None = None) -> tuple[dict, list, list, Adj]:
    """Return (nodes, edges, geometry, adj) from roads.graph.json.

    nodes: {node_id: [lon, lat]}; edges: [[u, v, length_m, highway], ...];
    geometry: per-edge polyline; adj: undirected, weighted by A5 minutes and km.
    """
    g = json.loads((path or PROCESSED / "roads.graph.json").read_text(encoding="utf-8"))
    nodes = g["nodes"]
    edges = g["edges"]
    adj: Adj = defaultdict(list)
    for ei, (u, v, length_m, hw) in enumerate(edges):
        km = length_m / 1000.0
        minutes = km / SPEED_KMH.get(hw, DEFAULT_SPEED_KMH) * 60.0
        adj[u].append((v, minutes, km, ei))
        adj[v].append((u, minutes, km, ei))
    return nodes, edges, g["geometry"], adj


def build_graph() -> tuple[dict, Adj]:
    """(nodes, adj) only - what the analysis scripts need."""
    nodes, _edges, _geom, adj = load_graph()
    return nodes, adj


def flat_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Equirectangular straight-line distance in km (fine at the <10 km scale used here)."""
    return math.hypot((lon2 - lon1) * math.cos(math.radians(lat1)), lat2 - lat1) * 111.32


def make_snapper(nodes: dict, cell: float = SNAP_CELL_DEG):
    """Return nearest(lon, lat) -> (node_id, straight-line snap error in km).

    Nearest is by squared degree distance, searched outward over Chebyshev rings of grid
    cells. The search may only stop once no unscanned ring can hold a closer node: a
    node in ring r+1 is at least r cells away, so ring r is the last one needed exactly
    when the best distance so far is <= r * cell. The earlier rule ("stop at the first
    non-empty ring r >= 1") returned a farther node whenever the first hit sat diagonally
    in ring 1 while a straight-ahead node sat in ring 2 - six EP parcels were mis-snapped
    that way (code review 2026-09-06).
    """
    grid: dict[tuple[int, int], list[str]] = defaultdict(list)
    for nid, (lon, lat) in nodes.items():
        grid[(int(lon / cell), int(lat / cell))].append(nid)

    def nearest(lon: float, lat: float) -> tuple[str, float]:
        cx, cy = int(lon / cell), int(lat / cell)
        best, bd = None, INF
        for r in range(0, 8):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) != r:
                        continue
                    for nid in grid.get((cx + dx, cy + dy), ()):
                        lo, la = nodes[nid]
                        d = (lo - lon) ** 2 + (la - lat) ** 2
                        if d < bd:
                            bd, best = d, nid
            if best is not None and bd <= (r * cell) ** 2:
                break
        if best is None:
            raise ValueError(f"no road node within 8 grid cells of ({lon}, {lat})")
        lo, la = nodes[best]
        return best, flat_km(lon, lat, lo, la)

    return nearest


def dijkstra(adj: Adj, src: str) -> tuple[dict[str, float], dict[str, float], dict[str, tuple[str, int]]]:
    """Least-TIME tree from src.

    Returns (minutes, km, prev). ``km`` is the network distance along the SAME chosen
    path - not a shortest-distance tree - so minutes and km always describe one route;
    ``prev`` maps node -> (parent, edge index) for polyline reconstruction.
    """
    minutes = {src: 0.0}
    km = {src: 0.0}
    prev: dict[str, tuple[str, int]] = {}
    pq = [(0.0, src)]
    while pq:
        d, n = heapq.heappop(pq)
        if d > minutes.get(n, INF):
            continue
        kn = km[n]
        for m, w, k, ei in adj[n]:
            nd = d + w
            if nd < minutes.get(m, INF):
                minutes[m] = nd
                km[m] = kn + k
                prev[m] = (n, ei)
                heapq.heappush(pq, (nd, m))
    return minutes, km, prev


def dijkstra_minutes(adj: Adj, src: str) -> dict[str, float]:
    return dijkstra(adj, src)[0]


def dijkstra_time_then_km(adj: Adj, src: str) -> tuple[dict[str, float], dict[str, float]]:
    """(km along the least-time path, minutes) - the order r9/r10 have always used."""
    minutes, km, _prev = dijkstra(adj, src)
    return km, minutes


def dijkstra_km(adj: Adj, src: str) -> dict[str, float]:
    """Least-DISTANCE tree from src. Used only for the A5-free sensitivity."""
    dist = {src: 0.0}
    pq = [(0.0, src)]
    while pq:
        d, n = heapq.heappop(pq)
        if d > dist.get(n, INF):
            continue
        for m, _w, k, _ei in adj[n]:
            nd = d + k
            if nd < dist.get(m, INF):
                dist[m] = nd
                heapq.heappush(pq, (nd, m))
    return dist


def displace(lon: float, lat: float, km: float, bearing_deg: float) -> tuple[float, float]:
    """Move a coordinate km along a compass bearing (equirectangular)."""
    th = math.radians(bearing_deg)
    dlat = km * math.cos(th) / 111.32
    dlon = km * math.sin(th) / (111.32 * math.cos(math.radians(lat)))
    return lon + dlon, lat + dlat


def sweep_grid():
    """Yield (offset_km, bearing_deg-or-None) over the A11 grid: 1 + 8 + 8 = 17 configs."""
    for d in SWEEP_OFFSET_KM:
        for b in ((None,) if d == 0 else SWEEP_BEARINGS_DEG):
            yield d, b


def snap_sites(feats: list[dict], snap) -> tuple[dict[str, int], list[dict]]:
    """Snap every sites.geojson feature. Returns (name -> index, site records).

    Every record carries the same keys, so any script can read status/district/snap_km
    without a fourth copy of this loop: name, operator, role, status, district, lon, lat,
    node, snap_km.
    """
    site_key: dict[str, int] = {}
    site_info: list[dict] = []
    for f in feats:
        lon, lat = f["geometry"]["coordinates"]
        nid, err = snap(lon, lat)
        p = f["properties"]
        site_key[p["name"]] = len(site_info)
        site_info.append({
            "name": p["name"], "operator": p["operator"], "role": p["role"],
            "status": p["status"], "district": p.get("district"),
            "lon": lon, "lat": lat, "node": nid, "snap_km": round(err, 2),
        })
    return site_key, site_info


def snap_parcels(parcels: list[dict], snap) -> tuple[list[str], list[float]]:
    """Snap every demand cell. Returns (node ids, snap errors in km), parcel order."""
    nodes, errs = [], []
    for p in parcels:
        nid, err = snap(p["lon"], p["lat"])
        nodes.append(nid)
        errs.append(err)
    return nodes, errs
