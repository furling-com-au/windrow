"""R10d: is the Arowana verdict a function of one unregistered coordinate?

The reading on which Arowana's "$15 per tonne" IS supported - a grower who would
otherwise cart farm-direct to Port Lincoln or Thevenard carting farm-direct to Lucky Bay
instead - depends entirely on where Lucky Bay is. That coordinate is an OSM hamlet node
("Lucky Bay, South Australia"), coord_precision "town", the same precision class A11 gives
the Lock and Kimba bunkers a <=5 km tolerance for, and it is registered in NO assumption
(docs/ready_to_draft.md, defect D1). The verdict must not turn on it silently.

So the site is displaced 0 / 2.5 / 5 km on 8 bearings, re-snapped to the road graph and
re-routed from scratch (17 configurations), and the four quantities the verdict rests on
are recomputed at every one:

  max saving vs the nearest Bunge export port    - the "up to" figure that clears $15
  catchment-mean saving vs the nearest port      - the figure for the growers who use it
  Lucky Bay's catchment share of EP production   - how many growers that is
  max saving vs the nearest Bunge point (any)    - the "up to" figure that does NOT clear
  realised EP-wide cartage saving (R9's dM1)     - the peninsula-wide average

Reproduce
---------
    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe pipeline/r10d_lucky_bay_sweep.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wlib import PROCESSED  # noqa: E402
from roads import (  # noqa: E402
    build_graph, dijkstra_time_then_km, displace, make_snapper, snap_parcels, snap_sites,
    sweep_grid,
)
from r8_choice_geometry import (  # noqa: E402
    APP_DATA, INCUMBENT_OPERATORS, network_states, parcel_weights, wmean, wshare,
)
from r9_cartage import cartage_aud_per_t as P  # noqa: E402

INF = float("inf")
CLAIM_AUD = 15.0


def main():
    nodes, adj = build_graph()
    snap = make_snapper(nodes)
    feats = json.loads((PROCESSED / "sites.geojson").read_text(encoding="utf-8"))["features"]
    parcels = json.load(open(APP_DATA / "parcels.json", encoding="utf-8"))["parcels"]
    w, _a, _b = parcel_weights(parcels)
    n = len(parcels)

    sk, si = snap_sites(feats, snap)
    pn, _snap_km = snap_parcels(parcels, snap)

    def kv(nid):
        t, _ = dijkstra_time_then_km(adj, nid)
        return [t.get(x, INF) for x in pn]

    PL, TH, LB = sk["Port Lincoln"], sk["Thevenard"], sk["Lucky Bay (T-Ports port)"]
    kport = [min(a, b) for a, b in zip(kv(si[PL]["node"]), kv(si[TH]["node"]))]
    inc = [sk[f["properties"]["name"]] for f in network_states(feats)["s2025_26"]["sites"]
           if f["properties"]["operator"] in INCUMBENT_OPERATORS]
    kinc_v = {i: kv(si[i]["node"]) for i in inc}
    kinc = [min(kinc_v[i][j] for i in inc) for j in range(n)]

    lo0, la0 = si[LB]["lon"], si[LB]["lat"]
    print(f"Lucky Bay as registered: lon {lo0}, lat {la0}  (OSM hamlet node, precision "
          f"'town', registered in NO assumption)")
    print("cfg              snap   max_vsPort  catch_mean  catch_share  max_vsBunge  dM1_EP")
    rows = []
    # the same 17-configuration grid r8, r8a and r9 sweep (roads.SWEEP_*), not a local copy
    for mag, br in sweep_grid():
            lo, la = (lo0, la0) if br is None else displace(lo0, la0, mag, br)
            br = br or 0
            nid, serr = snap(lo, la)
            kLB = kv(nid)
            sav_port = [P(kport[j])[0] - P(min(kLB[j], kport[j]))[0] for j in range(n)]
            inct = [kLB[j] <= kinc[j] + 1e-9 for j in range(n)]
            sel = [j for j in range(n) if inct[j]]
            ws = [w[j] for j in sel]
            cm = wmean(ws, [sav_port[j] for j in sel]) if sel else float("nan")
            savb = [P(kinc[j])[0] - P(kLB[j])[0] for j in range(n)]
            dm1 = wmean(w, [P(kinc[j])[0] - P(min(kinc[j], kLB[j]))[0] for j in range(n)])
            rows.append((max(sav_port), cm, wshare(w, inct), max(savb), dm1))
            print(f"{mag:4.1f} km / {br:3d} deg  {serr:4.2f}   ${max(sav_port):8.2f}   "
                  f"${cm:8.2f}    {wshare(w, inct) * 100:6.2f}%   ${max(savb):8.2f}   "
                  f"${dm1:5.3f}")
    labels = ["max saving vs nearest Bunge port", "catchment mean vs nearest port",
              "catchment share of EP production", "max saving vs nearest Bunge point",
              "realised EP-wide cartage saving (dM1)"]
    print()
    for k, name in enumerate(labels):
        v = [r[k] for r in rows]
        print(f"ENVELOPE over {len(rows)} configs  {name:<40} {min(v):8.3f} .. {max(v):8.3f}")
    print()
    # The conclusion is DERIVED from the envelope just printed, never typed: a literal
    # "$18.72" here survived every input change silently until 2026-09-06.
    port_floor = min(r[0] for r in rows)   # 'up to' vs nearest Bunge port, worst config
    bunge_ceiling = max(r[3] for r in rows)  # 'up to' vs nearest Bunge point, best config
    port_clears = port_floor >= CLAIM_AUD
    bunge_fails = bunge_ceiling < CLAIM_AUD
    robust = port_clears and bunge_fails
    print(f"READ: the two findings the verdict rests on are "
          f"{'both coordinate-robust' if robust else 'NOT both coordinate-robust'}. The")
    print(f"'up to' figure on the direct-to-port reading never falls below ${port_floor:.2f}/t "
          f"({'clears' if port_clears else 'DOES NOT clear'}")
    print(f"${CLAIM_AUD:.0f} at every configuration) and the 'up to' figure on the "
          f"nearest-Bunge-point")
    print(f"reading never rises above ${bunge_ceiling:.2f}/t "
          f"({'fails' if bunge_fails else 'REACHES'} ${CLAIM_AUD:.0f} at "
          f"{'every' if bunge_fails else 'some'} configuration).")


if __name__ == "__main__":
    main()
