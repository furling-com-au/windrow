"""R10b: supplementary detail for the Arowana "$15/t" claim test (pipeline/r10_arowana_claim.py).

Answers four things R10's summary tables cannot:

  1. WHERE is the most-favoured cell?  "Up to" is a maximum, so the location that reaches
     the maximum is part of the finding. Named by its nearest receival point and its
     distance to Lucky Bay.
  2. Does ANY grower reading, at ANY cell, reach $15/t?  Tested cell-by-cell across the
     grower readings simultaneously, not reading-by-reading.
  3. What does the saving look like INSIDE Lucky Bay's own catchment - the growers for
     whom Lucky Bay is actually the nearest place to tip a load, i.e. the only ones who
     realise any cartage saving at all?
  4. The whole road chain at the SEPTEMBER 2021 network (state B), where the T-Ports
     system is farm -> bunker -> Lucky Bay shuttle, not farm -> Lucky Bay alone.

Same imports, same graph, same rate. Nothing new is assumed.

Reproduce
---------
    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe pipeline/r10b_arowana_detail.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wlib import PROCESSED  # noqa: E402
from roads import (  # noqa: E402
    build_graph, dijkstra_time_then_km, make_snapper, snap_parcels, snap_sites,
)
from r8_choice_geometry import (  # noqa: E402
    APP_DATA, INCUMBENT_OPERATORS, network_states, parcel_weights, wmean, wshare,
)
from r9_cartage import cartage_aud_per_t  # noqa: E402

INF = float("inf")
P = cartage_aud_per_t


def main():
    nodes, adj = build_graph()
    snap = make_snapper(nodes)
    feats = json.loads((PROCESSED / "sites.geojson").read_text(encoding="utf-8"))["features"]
    parcels = json.load(open(APP_DATA / "parcels.json", encoding="utf-8"))["parcels"]
    weights, _dt, _dh = parcel_weights(parcels)
    n = len(parcels)

    site_key, site_info = snap_sites(feats, snap)
    parcel_nodes, _snap_km = snap_parcels(parcels, snap)

    cache = {}

    def kmv(nid):
        if nid not in cache:
            t, _ = dijkstra_time_then_km(adj, nid)
            cache[nid] = [t.get(pn, INF) for pn in parcel_nodes]
        return cache[nid]

    km_of = {i: kmv(s["node"]) for i, s in enumerate(site_info)}

    r8 = network_states(feats)
    A = [site_key[f["properties"]["name"]] for f in r8["s2025_26"]["sites"]]
    B = [site_key[f["properties"]["name"]] for f in r8["s2023_24"]["sites"]]
    LB, PL, TH = site_key["Lucky Bay (T-Ports port)"], site_key["Port Lincoln"], site_key["Thevenard"]
    LOCKB, KIMBAB = site_key["Lock (T-Ports bunker)"], site_key["Kimba (T-Ports bunker)"]
    inc_A = [i for i in A if site_info[i]["operator"] in INCUMBENT_OPERATORS]
    ports = [PL, TH]

    def nearest(pool, pi):
        bk, bi = INF, None
        for i in pool:
            if km_of[i][pi] < bk:
                bk, bi = km_of[i][pi], i
        return bk, bi

    km_LB, km_PL, km_TH = km_of[LB], km_of[PL], km_of[TH]
    inc_near = [nearest(inc_A, pi) for pi in range(n)]
    port_near = [nearest(ports, pi) for pi in range(n)]

    # operator line haul: routed silo -> nearer Bunge port, and bunker -> Lucky Bay
    port_trees = {p: dijkstra_time_then_km(adj, site_info[p]["node"])[0] for p in ports}
    lb_tree = dijkstra_time_then_km(adj, site_info[LB]["node"])[0]
    linehaul = {i: min(port_trees[p].get(site_info[i]["node"], INF) for p in ports)
                for i in set(x[1] for x in inc_near) if i is not None}
    shuttle = {LB: 0.0,
               LOCKB: lb_tree.get(site_info[LOCKB]["node"], INF),
               KIMBAB: lb_tree.get(site_info[KIMBAB]["node"], INF)}
    print("T-Ports onward shuttle km to Lucky Bay: "
          f"Lock bunker {shuttle[LOCKB]:.1f} km, Kimba bunker {shuttle[KIMBAB]:.1f} km")
    print("Bunge line-haul km, nearest Bunge port, by site:")
    for i in sorted(linehaul, key=lambda i: -linehaul[i]):
        pk = min((port_trees[p].get(site_info[i]["node"], INF), site_info[p]["name"]) for p in ports)
        print(f"   {site_info[i]['name']:<22} {linehaul[i]:6.1f} km -> {pk[1]}   "
              f"= ${P(linehaul[i])[0]:5.2f}/t")

    # ------------------------------------------------ grower readings, per cell
    readings = {
        "vs nearest Bunge point": [P(inc_near[i][0])[0] - P(km_LB[i])[0] for i in range(n)],
        "vs Port Lincoln direct": [P(km_PL[i])[0] - P(km_LB[i])[0] for i in range(n)],
        "vs Thevenard direct": [P(km_TH[i])[0] - P(km_LB[i])[0] for i in range(n)],
        "vs nearest Bunge port": [P(port_near[i][0])[0] - P(min(km_LB[i], port_near[i][0]))[0]
                                  for i in range(n)],
    }
    best_any = [max(v[i] for v in readings.values()) for i in range(n)]
    print()
    print("BEST GROWER READING AT EACH CELL, taken cell-by-cell (an upper envelope over "
          "all four grower readings simultaneously):")
    print(f"   tonne-weighted EP mean ${wmean(weights, best_any):.2f}/t")
    print(f"   EP max            ${max(best_any):.2f}/t")
    for thr in (15.0, 10.0, 5.0, 0.0):
        print(f"   share of EP production with best-of-any-reading >= ${thr:5.2f}/t: "
              f"{wshare(weights, [b >= thr for b in best_any]) * 100:5.1f}%")

    # ------------------------------------------------ where the maximum is
    print()
    for name, v in list(readings.items()) + [("BEST OF ANY GROWER READING", best_any)]:
        bi = max(range(n), key=lambda i: v[i])
        p = parcels[bi]
        nk, ni = nearest(A, bi)
        print(f"{name:<32} max ${v[bi]:6.2f}/t at lon {p['lon']:.3f} lat {p['lat']:.3f} "
              f"({p['district']}); nearest point {site_info[ni]['name']} {nk:.1f} km; "
              f"Lucky Bay {km_LB[bi]:.1f} km; Port Lincoln {km_PL[bi]:.1f} km; "
              f"nearest Bunge {site_info[inc_near[bi][1]]['name']} {inc_near[bi][0]:.1f} km")

    # ------------------------------------------------ inside Lucky Bay's own catchment
    in_catch = [km_LB[i] <= inc_near[i][0] + 1e-9 for i in range(n)]
    sel = [i for i in range(n) if in_catch[i]]
    w = [weights[i] for i in sel]
    print()
    print("LUCKY BAY'S OWN CATCHMENT (state A: cells where Lucky Bay is the fewest-km point "
          "of any owner)")
    print(f"   {wshare(weights, in_catch) * 100:.1f}% of EP production, {len(sel)} of {n} cells")
    if sel:
        for name, v in readings.items():
            vv = [v[i] for i in sel]
            print(f"   {name:<26} mean ${wmean(w, vv):6.2f}/t   max ${max(vv):6.2f}/t   "
                  f">=$15 {wshare(w, [x >= 15 for x in vv]) * 100:5.1f}% of catchment")

    # ------------------------------------------------ whole road chain, state B (Sept 2021)
    ind_B = [i for i in B if site_info[i]["operator"] not in INCUMBENT_OPERATORS]
    chain_tp, chain_bunge = [], []
    for pi in range(n):
        bk, bi = INF, None
        for i in ind_B:
            tot = km_of[i][pi] + shuttle[i]
            if tot < bk:
                bk, bi = tot, i
        chain_tp.append(bk)
        ii = inc_near[pi][1]
        chain_bunge.append(inc_near[pi][0] + (linehaul[ii] if ii is not None else INF))
    sav = [P(chain_bunge[i])[0] - P(chain_tp[i])[0] for i in range(n)]
    savkm = [chain_bunge[i] - chain_tp[i] for i in range(n)]
    print()
    print("WHOLE ROAD CHAIN TO AN EXPORT POSITION, SEPTEMBER-2021 NETWORK (state B):")
    print("   T-Ports: farm -> nearest T-Ports point + that point's onward road shuttle to")
    print("   Lucky Bay.  Bunge: farm -> nearest Bunge point + that site's road line haul")
    print("   to Port Lincoln or Thevenard. Both legs road; EP grain rail ceased May 2019.")
    print(f"   EP tonne-weighted mean saving ${wmean(weights, sav):.2f}/t "
          f"({wmean(weights, savkm):.1f} km)")
    print(f"   EP max ${max(sav):.2f}/t")
    for thr in (15.0, 10.0, 0.0):
        print(f"   share >= ${thr:5.2f}/t: {wshare(weights, [s >= thr for s in sav]) * 100:5.1f}%")
    print(f"   share <= $0: {wshare(weights, [s <= 1e-9 for s in sav]) * 100:5.1f}%")
    for d in ("WEP", "EEP", "LEP"):
        s2 = [i for i, p in enumerate(parcels) if p["district"] == d]
        w2 = [weights[i] for i in s2]
        print(f"     {d}: mean ${wmean(w2, [sav[i] for i in s2]):6.2f}/t  "
              f"max ${max(sav[i] for i in s2):6.2f}/t  "
              f">=$15 {wshare(w2, [sav[i] >= 15 for i in s2]) * 100:5.1f}%  "
              f"<=$0 {wshare(w2, [sav[i] <= 1e-9 for i in s2]) * 100:5.1f}%")

    # ------------------------------------------------ what $15 requires
    print()
    print("WHAT $15/t REQUIRES, AND WHAT THE PENINSULA OFFERS")
    print("   $15/t at ESCOSA's 50-250 km band rate ($0.11/t-km, one way) = 136.4 km saved.")
    print(f"   Longest one-way haul from any EP production cell to its nearest Bunge point: "
          f"{max(inc_near[i][0] for i in range(n)):.1f} km")
    print(f"   Tonne-weighted mean haul to nearest Bunge point: "
          f"{wmean(weights, [inc_near[i][0] for i in range(n)]):.1f} km")
    print(f"   So the entire grower cart leg it could ever replace is worth, at most, "
          f"${P(max(inc_near[i][0] for i in range(n)))[0]:.2f}/t - and that is the whole "
          f"leg, not a saving on it.")
    print(f"   Tonne-weighted mean cartage to nearest Bunge point: "
          f"${wmean(weights, [P(inc_near[i][0])[0] for i in range(n)]):.2f}/t")


if __name__ == "__main__":
    main()
