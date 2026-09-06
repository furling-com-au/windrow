"""R10: independent test of Arowana's "up to $15 per tonne" road-freight-saving claim.

THE CLAIM UNDER TEST
--------------------
Arowana, September 2021 release on its Lucky Bay investment: the port "generates road
freight savings for grain growers from the Eyre Peninsula of up to $15 per tonne".
No working is published anywhere we can find.

The claim is AMBIGUOUS in at least three independent ways, and this script refuses to
pick one reading and call it the test:

  (a) SAVING AGAINST WHAT?  Against the nearest Bunge upcountry silo?  Against carting
      direct to Port Lincoln?  To Thevenard?  Against the nearest Bunge port of either?
      Against the whole road chain farm->silo->port that the peninsula ran before
      Lucky Bay existed?
  (b) WHOSE SAVING?  "for grain growers" is the plain reading, but the largest road
      freight leg Lucky Bay removes is the OPERATOR's upcountry-silo-to-port line haul,
      which is a supply-chain saving that may or may not reach a grower.
  (c) "UP TO" WHERE?  The natural reading of "up to" is a MAXIMUM - the single most
      favoured farm, not the average one. That reading is the one most favourable to
      the claimant and is computed first, everywhere.

Every reading is enumerated and every reading is computed. Where a reading supports the
claim that is reported as plainly as where it does not.

METHOD - identical to R9, deliberately
--------------------------------------
Same graph, same snapper, same parcels, same fixed tonne weights, same ESCOSA marginal
rate schedule and the same application rule, all IMPORTED from pipeline/r9_cartage.py and
pipeline/r8_choice_geometry.py. No second router, no retyped rate, no fitted parameter,
nothing from packages/sim. If R9's numbers are right these are right, and if R9's numbers
are wrong these are wrong in the same direction.

Distances are one-way loaded routed road kilometres on the least-TIME path (A5 selects the
path; it prices nothing). A least-DISTANCE variant that depends on no assumed speed runs
as a standing sensitivity.

THE RATE QUESTION IS PART OF THE TEST, NOT A FOOTNOTE
-----------------------------------------------------
Arowana did not say what rate it used. ESCOSA's marginal schedule ($0.12/t-km <=50 km,
$0.11/t-km 50-250 km, 2018-19 A$) is the only published SA schedule and is what R9 uses,
but it is explicitly a MARGINAL rate and roughly half a delivered cartage price. A
promoter quoting a full commercial rate, or pricing a round trip, would get a materially
larger dollar figure off the SAME kilometres. Because of that, every reading below is
reported in SAVED KILOMETRES first and priced second, at three rates:

    escosa_oneway   ESCOSA marginal bands on the one-way distance  (R9's published rule)
    escosa_return   the same bands applied to distance x2          (A18's labelled upper
                    bound on the unresolved empty-return question - NOT a result)
    ach2026_marginal $0.10/t-km flat (Australian Custom Harvesters recommended rate card,
                    valid 1 Feb 2026, marginal increment beyond the first 10 km)

Saved kilometres are the invariant thing. The dollar figure is a rate choice, and the
claimant is entitled to the rate choice most favourable to them as long as it is a real
published one. That is why the km break-even for $15/t is printed for each rate.

Reproduce
---------
    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe pipeline/r10_arowana_claim.py

Prints everything. Writes docs/r10_arowana_claim.json.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wlib import PROCESSED  # noqa: E402
from r8_choice_geometry import (  # noqa: E402
    APP_DATA,
    DOCS,
    INCUMBENT_OPERATORS,
    build_graph,
    make_snapper,
    network_states,
    parcel_weights,
    wmean,
    wshare,
)
from r9_cartage import cartage_aud_per_t, dijkstra_km, dijkstra_time_then_km  # noqa: E402

INF = float("inf")
CLAIM_AUD = 15.0
DISTRICTS = ("WEP", "EEP", "LEP")


# ------------------------------------------------------------------------ the rates
def price_escosa_oneway(km: float) -> float:
    return cartage_aud_per_t(km)[0]


def price_escosa_return(km: float) -> float:
    """A18's labelled UPPER BOUND on the unresolved empty-return question. Not a result."""
    return cartage_aud_per_t(km * 2.0)[0]


def price_ach2026(km: float) -> float:
    """ACH 2026 recommended card, marginal increment only ($0.10/t-km ex GST)."""
    return km * 0.10 if math.isfinite(km) else INF


RATES = {
    "escosa_oneway": price_escosa_oneway,
    "escosa_return": price_escosa_return,
    "ach2026_marginal": price_ach2026,
}
# km of saved one-way distance needed to reach $15/t under each rate
BREAKEVEN_KM = {
    "escosa_oneway": CLAIM_AUD / 0.11,          # 136.4 km, in the 50-250 band
    "escosa_return": CLAIM_AUD / 0.11 / 2.0,    # 68.2 km one-way (136.4 km driven)
    "ach2026_marginal": CLAIM_AUD / 0.10,       # 150.0 km
}


def summarise_saving(sav_aud, sav_km, weights, parcels, cell_ids):
    """Tonne-weighted summary of one per-cell saving vector, EP-wide and by district."""
    out = {}
    for scope in ("EP",) + DISTRICTS:
        sel = ([i for i in range(len(parcels))] if scope == "EP"
               else [i for i, p in enumerate(parcels) if p["district"] == scope])
        w = [weights[i] for i in sel]
        v = [sav_aud[i] for i in sel]
        k = [sav_km[i] for i in sel]
        fin = [i for i in sel if math.isfinite(sav_aud[i])]
        if not fin:
            out[scope] = None
            continue
        bi = max(fin, key=lambda i: sav_aud[i])
        out[scope] = {
            "tonne_weighted_mean_aud_per_t": round(wmean(w, v), 2),
            "tonne_weighted_mean_saved_km": round(wmean(w, k), 1),
            "max_aud_per_t": round(sav_aud[bi], 2),
            "max_saved_km": round(sav_km[bi], 1),
            "max_cell": cell_ids[bi],
            "share_saving_ge_15": round(wshare(w, [sav_aud[i] >= CLAIM_AUD for i in sel]), 4),
            "share_saving_ge_10": round(wshare(w, [sav_aud[i] >= 10.0 for i in sel]), 4),
            "share_saving_ge_5": round(wshare(w, [sav_aud[i] >= 5.0 for i in sel]), 4),
            "share_saving_gt_0": round(wshare(w, [sav_aud[i] > 1e-9 for i in sel]), 4),
            "share_saving_le_0": round(wshare(w, [sav_aud[i] <= 1e-9 for i in sel]), 4),
        }
    return out


def main():
    nodes, adj = build_graph()
    snap = make_snapper(nodes)
    feats = json.loads((PROCESSED / "sites.geojson").read_text(encoding="utf-8"))["features"]
    parcels = json.load(open(APP_DATA / "parcels.json", encoding="utf-8"))["parcels"]
    weights, dist_t, _ = parcel_weights(parcels)
    n = len(parcels)
    print(f"parcels: {n}  sites: {len(feats)}  nodes: {len(nodes)}")
    print(f"CLAIM UNDER TEST: 'road freight savings ... of up to ${CLAIM_AUD:.0f} per tonne'")
    print("km of one-way saved distance needed to reach $15/t:")
    for k, v in BREAKEVEN_KM.items():
        print(f"   {k:<18} {v:6.1f} km one-way")

    site_key, site_info = {}, []
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

    parcel_nodes = []
    for p in parcels:
        nid, _err = snap(p["lon"], p["lat"])
        parcel_nodes.append(nid)
    cell_ids = [f"{p['district']} cell lon {p['lon']:.3f} lat {p['lat']:.3f}" for p in parcels]

    cache: dict[str, list[float]] = {}

    def km_vector(nid: str, mode: str = "time") -> list[float]:
        key = f"{mode}:{nid}"
        if key not in cache:
            if mode == "time":
                t, _ = dijkstra_time_then_km(adj, nid)
            else:
                t = dijkstra_km(adj, nid)
            cache[key] = [t.get(pn, INF) for pn in parcel_nodes]
        return cache[key]

    def run(mode: str):
        """Everything, for one routing mode ('time' = published, 'dist' = A5-free)."""
        km_of = {i: km_vector(s["node"], mode) for i, s in enumerate(site_info)}

        r8 = network_states(feats)
        a_names = [f["properties"]["name"] for f in r8["s2025_26"]["sites"]]
        b_names = [f["properties"]["name"] for f in r8["s2023_24"]["sites"]]
        # Contemporaneous state for a SEPTEMBER 2021 claim is B: Lucky Bay open (2019/20)
        # plus the Lock bunker, plus the Kimba bunker "built for 2021 harvest".
        LB = site_key["Lucky Bay (T-Ports port)"]
        PL = site_key["Port Lincoln"]
        TH = site_key["Thevenard"]
        LOCKB = site_key["Lock (T-Ports bunker)"]
        KIMBAB = site_key["Kimba (T-Ports bunker)"]

        def idxs(names):
            return [site_key[nm] for nm in names]

        def nearest(pool, pi):
            bk, bi = INF, None
            for i in pool:
                k = km_of[i][pi]
                if k < bk:
                    bk, bi = k, i
            return bk, bi

        A = idxs(a_names)
        B = idxs(b_names)
        inc_A = [i for i in A if site_info[i]["operator"] in INCUMBENT_OPERATORS]
        inc_up_A = [i for i in inc_A if site_info[i]["role"] == "upcountry"]
        inc_ports = [PL, TH]
        ind_B = [i for i in B if site_info[i]["operator"] not in INCUMBENT_OPERATORS]

        # per-cell km to the things every reading needs
        km_LB = km_of[LB]
        km_PL = km_of[PL]
        km_TH = km_of[TH]
        km_inc_near = [nearest(inc_A, pi)[0] for pi in range(n)]
        km_inc_up_near = [nearest(inc_up_A, pi)[0] for pi in range(n)]
        km_inc_port_near = [nearest(inc_ports, pi)[0] for pi in range(n)]
        km_ind_near_B = [nearest(ind_B, pi)[0] for pi in range(n)]
        # nearest incumbent site -> its own nearest Bunge port (the OPERATOR's line haul)
        inc_choice = [nearest(inc_A, pi)[1] for pi in range(n)]

        # site -> port line-haul km, routed on the same graph
        linehaul = {}
        for i in set(inc_choice):
            if i is None:
                continue
            v = km_vector(site_info[i]["node"], mode)
            # distance from that site to Port Lincoln / Thevenard: route from the site and
            # read off the port's node. Cheapest: run the tree from the port instead.
            linehaul[i] = None
        # run trees from the two ports once and read site nodes off them
        port_trees = {}
        for pidx in inc_ports:
            if mode == "time":
                t, _ = dijkstra_time_then_km(adj, site_info[pidx]["node"])
            else:
                t = dijkstra_km(adj, site_info[pidx]["node"])
            port_trees[pidx] = t
        for i in set(inc_choice):
            if i is None:
                continue
            linehaul[i] = min(port_trees[p].get(site_info[i]["node"], INF)
                              for p in inc_ports)

        READINGS = {}

        def add(key, desc, whose, km_with, km_without, defined=True):
            READINGS[key] = {
                "description": desc,
                "whose_saving": whose,
                "km_with_lucky_bay": km_with,
                "km_without_lucky_bay": km_without,
            }

        # -- R1: against the nearest Bunge UPCOUNTRY silo (the plain grower reading, and
        #        the negative of R9's toll M2)
        add("R1_vs_nearest_bunge_upcountry",
            "Grower switches from the nearest Bunge upcountry silo to Lucky Bay. "
            "Saving = cartage(nearest Bunge upcountry) - cartage(Lucky Bay). This is the "
            "negative of R9's primary measure M2, restricted to upcountry silos.",
            "grower", km_LB, km_inc_up_near)

        # -- R1b: against the nearest Bunge point of ANY role (silo or port)
        add("R1b_vs_nearest_bunge_any",
            "Grower switches from the nearest Bunge receival point of any role (silo or "
            "port) to Lucky Bay. Exactly the negative of R9's M2 at state A.",
            "grower", km_LB, km_inc_near)

        # -- R2: against carting direct to Port Lincoln
        add("R2_vs_port_lincoln",
            "Grower who would otherwise cart farm-direct to Port Lincoln instead carts "
            "farm-direct to Lucky Bay.",
            "grower", km_LB, km_PL)

        # -- R3: against carting direct to Thevenard
        add("R3_vs_thevenard",
            "Grower who would otherwise cart farm-direct to Thevenard instead carts "
            "farm-direct to Lucky Bay.",
            "grower", km_LB, km_TH)

        # -- R4: against the nearer of the two Bunge ports (R9's M4 delta)
        add("R4_vs_nearest_bunge_port",
            "Grower who carts farm-direct to an export port: nearest Bunge port "
            "(Port Lincoln or Thevenard) vs Lucky Bay. This is R9's M4, C -> A.",
            "grower", [min(km_LB[i], km_inc_port_near[i]) for i in range(n)],
            km_inc_port_near)

        # -- R5: against the nearest independent point at state B (Sept-2021 network:
        #        Lucky Bay + Lock + Kimba bunkers all available)
        add("R5_stateB_vs_nearest_bunge_any",
            "SEPTEMBER-2021 NETWORK (state B: Lucky Bay + Lock + Kimba bunkers). Grower "
            "switches from the nearest Bunge point to the nearest T-Ports point. Negative "
            "of R9's M2 at state B. This is the state that actually existed on the date "
            "of the claim.",
            "grower", km_ind_near_B, km_inc_near)

        # -- R6: WHOLE ROAD CHAIN to an export position - grower leg + operator line haul.
        #        Grain rail on EP ceased May 2019, so the Bunge upcountry->port leg is a
        #        ROAD leg. Lucky Bay removes it entirely for grain tipped at the port.
        add("R6_whole_road_chain_to_port",
            "WHOLE ROAD FREIGHT TASK, not the grower's leg alone. Without Lucky Bay: "
            "farm -> nearest Bunge point (grower, road) PLUS that site -> Port Lincoln or "
            "Thevenard (operator, road; EP grain rail ceased May 2019). With Lucky Bay: "
            "farm -> Lucky Bay (grower, road) and nothing further, because the grain is "
            "already at an export position. This is the most claimant-favourable "
            "arithmetic on this page and it is NOT a grower saving - most of the removed "
            "distance is the operator's.",
            "chain (grower + operator)", km_LB,
            [km_inc_near[i] + (linehaul[inc_choice[i]] if inc_choice[i] is not None else INF)
             for i in range(n)])

        # -- R7: the OPERATOR's leg alone
        add("R7_operator_linehaul_only",
            "The operator's upcountry-silo -> port line haul alone, which Lucky Bay "
            "removes for any load tipped at the port. Not a grower saving under any "
            "reading of the words 'for grain growers' unless it is passed through, which "
            "this project cannot observe.",
            "operator", [0.0] * n,
            [linehaul[inc_choice[i]] if inc_choice[i] is not None else INF
             for i in range(n)])

        # price every reading at every rate
        results = {}
        for key, r in READINGS.items():
            kw, kwo = r["km_with_lucky_bay"], r["km_without_lucky_bay"]
            sav_km = [kwo[i] - kw[i] if math.isfinite(kwo[i]) and math.isfinite(kw[i])
                      else float("nan") for i in range(n)]
            per_rate = {}
            for rk, fn in RATES.items():
                sav = [fn(kwo[i]) - fn(kw[i]) if math.isfinite(kwo[i]) and math.isfinite(kw[i])
                       else float("-inf") for i in range(n)]
                per_rate[rk] = summarise_saving(sav, sav_km, weights, parcels, cell_ids)
            results[key] = {
                "description": r["description"],
                "whose_saving": r["whose_saving"],
                "by_rate": per_rate,
            }
        return results, {
            "km_LB": km_LB, "km_PL": km_PL, "km_TH": km_TH,
            "km_inc_near": km_inc_near, "linehaul": linehaul, "inc_choice": inc_choice,
            "site_info": site_info, "cell_ids": cell_ids,
        }

    published, aux = run("time")
    leastdist, _ = run("dist")

    # ---------------------------------------------------------------------- reporting
    order = ["R1_vs_nearest_bunge_upcountry", "R1b_vs_nearest_bunge_any",
             "R2_vs_port_lincoln", "R3_vs_thevenard", "R4_vs_nearest_bunge_port",
             "R5_stateB_vs_nearest_bunge_any", "R6_whole_road_chain_to_port",
             "R7_operator_linehaul_only"]
    for key in order:
        r = published[key]
        print()
        print("=" * 100)
        print(f"{key}   [{r['whose_saving']}]")
        print(r["description"])
        for rk in RATES:
            ep = r["by_rate"][rk]["EP"]
            print(f"  {rk:<18} EP mean ${ep['tonne_weighted_mean_aud_per_t']:>8.2f}/t "
                  f"({ep['tonne_weighted_mean_saved_km']:>6.1f} km)   "
                  f"MAX ${ep['max_aud_per_t']:>8.2f}/t ({ep['max_saved_km']:.1f} km)   "
                  f">=$15: {ep['share_saving_ge_15'] * 100:5.1f}%   "
                  f"<=$0: {ep['share_saving_le_0'] * 100:5.1f}%")
        ep = r["by_rate"]["escosa_oneway"]["EP"]
        print(f"  best cell (escosa_oneway): {ep['max_cell']}")
        for d in DISTRICTS:
            dd = r["by_rate"]["escosa_oneway"][d]
            print(f"    {d}: mean ${dd['tonne_weighted_mean_aud_per_t']:>7.2f}/t  "
                  f"max ${dd['max_aud_per_t']:>7.2f}/t  >=$15 {dd['share_saving_ge_15'] * 100:5.1f}%  "
                  f"<=$0 {dd['share_saving_le_0'] * 100:5.1f}%")

    out = {
        "generated": "r10_arowana_claim.py",
        "claim": ("Arowana, September 2021: Lucky Bay 'generates road freight savings for "
                  "grain growers from the Eyre Peninsula of up to $15 per tonne'."),
        "claim_aud_per_t": CLAIM_AUD,
        "breakeven_one_way_km_for_15_aud": {k: round(v, 1) for k, v in BREAKEVEN_KM.items()},
        "published_least_time_routing": published,
        "sensitivity_least_distance_routing": leastdist,
    }
    (DOCS / "r10_arowana_claim.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("\nwrote docs/r10_arowana_claim.json")


if __name__ == "__main__":
    main()
