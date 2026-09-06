"""R8a - coordinate sensitivity checks that pipeline/r8_choice_geometry.py does not run.

READ-ONLY. Imports r8's own build_graph / make_snapper / dijkstra_minutes / network_states /
parcel_weights / wshare and writes nothing. Two checks, both raised by adversarial
verification on 2026-08-31 and both of which r8's published A11 sweep cannot answer:

  CHECK 1 - Lucky Bay.
    In the 2025/26 state Lucky Bay is the ONLY independent receival point, so it alone sets
    the headline. Its coordinate is coord_precision "town" (Nominatim/OSM hamlet node) -
    the same precision class A11 gives Lock and Kimba a <=5 km tolerance for. r8's A11 sweep
    holds the 2025/26 independent set fixed (`ni25 = fixed_ind_min` inside the grid loop),
    so its result "66.8 % at every one of the 129 configurations" is true by construction of
    the sweep, not a demonstration that the level is coordinate-independent. This check
    displaces Lucky Bay over the identical 0/2.5/5 km x 8-bearing grid, re-snapping and
    re-routing each time.

  CHECK 2 - A11 with the two offsets genuinely independent.
    r8's grid loop filters BOTH Lock and Kimba to `offset_km == d`, so the two magnitudes
    are locked together and only the bearings vary: 129 = 1 + 2*8*8 configurations. Mixed
    magnitudes (e.g. Lock 5.0 km, Kimba 2.5 km) - both inside A11's stated tolerance - are
    never evaluated. This check runs the full 17x17 = 289 grid.

Run from the repo root:

    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe pipeline/r8a_coord_sensitivity.py
"""
import importlib.util
import json
import math
import pathlib
import sys

R8_PATH = pathlib.Path(__file__).resolve().parent / "r8_choice_geometry.py"
_spec = importlib.util.spec_from_file_location("r8_choice_geometry", R8_PATH)
r8 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r8)

# The grid and the displacement are r8's own (pipeline/roads.py), not a second copy: this
# script's claim is that it runs the IDENTICAL grid r8 does, so it must not declare one.
OFFSETS_KM = r8.SWEEP_OFFSET_KM
BEARINGS_DEG = r8.SWEEP_BEARINGS_DEG
displace = r8.displace
INF = float("inf")


def main():
    nodes, adj = r8.build_graph()
    snap = r8.make_snapper(nodes)
    feats = json.loads((r8.PROCESSED / "sites.geojson").read_text(encoding="utf-8"))["features"]
    parcels = json.load(open(r8.APP_DATA / "parcels.json", encoding="utf-8"))["parcels"]
    weights, _dist_t, _dist_ha = r8.parcel_weights(parcels)
    parcel_nodes = [snap(p["lon"], p["lat"])[0] for p in parcels]
    states = r8.network_states(feats)

    trees = {}

    def minutes_from(nid):
        if nid not in trees:
            trees[nid] = r8.dijkstra_minutes(adj, nid)
        t = trees[nid]
        return [t.get(pn, INF) for pn in parcel_nodes]

    def independent(state_key):
        return [f for f in states[state_key]["sites"]
                if f["properties"]["operator"] not in r8.INCUMBENT_OPERATORS]

    def sweep_row(mins):
        return {R: r8.wshare(weights, [not math.isfinite(x) or x > R for x in mins])
                for R in r8.SWEEP_MIN}

    def variants(feat):
        lon0, lat0 = feat["geometry"]["coordinates"]
        out = []
        for d in OFFSETS_KM:
            for b in ((None,) if d == 0 else BEARINGS_DEG):
                lon, lat = (lon0, lat0) if b is None else displace(lon0, lat0, d, b)
                nid, err = snap(lon, lat)
                out.append({"offset_km": d, "bearing_deg": b, "snap_km": round(err, 2),
                            "minutes": minutes_from(nid)})
        return out

    # ---------------------------------------------------------------- CHECK 1: Lucky Bay
    ind25 = independent("s2025_26")
    print("CHECK 1 - Lucky Bay coordinate sensitivity of the 2025/26 headline")
    print(f"  2025/26 independent points: {[f['properties']['name'] for f in ind25]}")
    lb = [f for f in ind25 if "Lucky Bay" in f["properties"]["name"]][0]
    rest = [f for f in ind25 if f is not lb]
    fixed = None
    for f in rest:
        m = minutes_from(snap(*f["geometry"]["coordinates"])[0])
        fixed = m if fixed is None else [min(a, b) for a, b in zip(fixed, m)]

    rows = {}
    for v in variants(lb):
        mins = v["minutes"] if fixed is None else [min(a, b) for a, b in zip(fixed, v["minutes"])]
        rows[(v["offset_km"], v["bearing_deg"])] = sweep_row(mins)

    base = rows[(0.0, None)]
    H = r8.HEADLINE_MIN
    print(f"  published coordinates, {H} min: {base[H] * 100:.2f} %")
    for d in OFFSETS_KM[1:]:
        vals = [r[H] for k, r in rows.items() if k[0] == d]
        print(f"  {d} km displacement, {H} min: {min(vals) * 100:.2f} % - {max(vals) * 100:.2f} %")
    allv = [r[H] for r in rows.values()]
    print(f"  ENVELOPE over all {len(rows)} configurations, {H} min: "
          f"{min(allv) * 100:.2f} % - {max(allv) * 100:.2f} %")
    print("  whole 2025/26 sweep column, envelope over the same grid:")
    for R in r8.SWEEP_MIN:
        a = [r[R] for r in rows.values()]
        print(f"    R={R:>3} min: published {base[R] * 100:5.1f} %   "
              f"envelope {min(a) * 100:5.1f} % - {max(a) * 100:5.1f} %")

    # ------------------------------------------- CHECK 2: A11 with independent offsets
    print()
    print("CHECK 2 - A11 (Lock, Kimba) with the two offsets INDEPENDENT, 289 configurations")
    ind23 = independent("s2023_24")
    byname = {f["properties"]["name"]: f for f in ind23}
    swept = list(r8.A11_SITES)
    fixed23 = None
    for f in ind23:
        if f["properties"]["name"] in swept:
            continue
        m = minutes_from(snap(*f["geometry"]["coordinates"])[0])
        fixed23 = m if fixed23 is None else [min(a, b) for a, b in zip(fixed23, m)]

    vl = variants(byname[swept[0]])
    vk = variants(byname[swept[1]])
    env = {R: [1.0, 0.0] for R in r8.SWEEP_MIN}
    n = 0
    for a in vl:
        for b in vk:
            n += 1
            ni = [min(x, y, z) for x, y, z in zip(fixed23, a["minutes"], b["minutes"])]
            row = sweep_row(ni)
            for R in r8.SWEEP_MIN:
                e = env[R]
                e[0], e[1] = min(e[0], row[R]), max(e[1], row[R])
    print(f"  configurations evaluated: {n}   (r8 publishes 129, offsets locked together)")
    print("  2023/24 envelope, no independent point within R minutes:")
    for R in r8.SWEEP_MIN:
        lo, hi = env[R]
        print(f"    R={R:>3} min: {lo * 100:5.2f} % - {hi * 100:5.2f} %")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
