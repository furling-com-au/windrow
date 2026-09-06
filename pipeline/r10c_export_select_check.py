"""R10c: the published EP upcountry->port freight rates, and what they do to the claim.

WHY THIS EXISTS
---------------
The Arowana claim is about "road freight savings". The biggest road freight leg that a
port at Lucky Bay removes is not the grower's cart leg at all - it is the UPCOUNTRY SITE
-> PORT line haul, which on the Eyre Peninsula has been an all-road task since grain rail
ceased in May 2019. R10 prices that leg at ESCOSA's MARGINAL rate, which is explicitly not
a delivered freight price. This script replaces that estimate with the incumbent's OWN
PUBLISHED per-tonne freight charges for two Eyre Peninsula pathways, which ESCOSA
reproduces, and checks them against the routed distances used everywhere else.

It also settles whether that leg is a grower cost. ESCOSA records that Export Select rates
are "published every" season and were adopted "by Grain Trade Australia as the location
differentials", and that "Buyers deduct location differentials from port prices to
establish a grain price at each site" (footnote 185). So the upcountry->port freight is
charged through to the grain price at the silo: it is not purely an operator cost, and a
reading of "road freight savings for grain growers" that includes it is defensible.

THE TWO PUBLISHED EP PATHWAYS
-----------------------------
ESCOSA 2019, Appendix E (full fee breakdowns for the four sample pathways of Table 4.5):
  Cummins -> Port Lincoln, BY RAIL:  freight to port $8.46 (2013-14) -> $8.25 (2017-18)/t
  Poochera -> Thevenard,   BY ROAD:  freight to port $16.65 (2013-14) -> $16.76 (2017-18)/t

The Poochera row is recovered by arithmetic as well as read, because pdftotext mangles
Table E.2's label column: Table 4.5 gives the Poochera->Thevenard pathway total as $63.76
and Table F.1 gives the same pathway's fees EXCLUDING freight as $47.00, and
63.76 - 47.00 = 16.76 exactly. The same cross-check on Cummins gives 50.82 - 42.57 = 8.25,
which Table E.1 prints in an unmangled row. Both are asserted below; the script fails if
either drifts.

Reproduce
---------
    .venv/Scripts/python.exe pipeline/r10c_export_select_check.py
    # underlying text, if you want to read the tables yourself:
    pdftotext -layout data/raw/reference/escosa_grain_supply_chain_2019.pdf - | sed -n '6640,6700p'
    pdftotext -layout data/raw/reference/escosa_grain_supply_chain_2019.pdf - | sed -n '6808,6845p'
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
# The PDF path is anchored to the repo and pdftotext's absence is a clean exit there; a
# cwd-relative path here silently produced an empty extraction and three FAIL rows when
# the script was run from anywhere but the repo root (code review 2026-09-06).
from r9_escosa_rate_check import PDF, pdf_text  # noqa: E402

INF = float("inf")

# Published, 2017-18 A$/tonne, ESCOSA 2019 Appendix E / Table 4.5 / Table F.1.
PUBLISHED = {
    "Cummins->Port Lincoln (rail)": {"freight_2017_18": 8.25, "pathway_total": 50.82,
                                     "fees_ex_freight": 42.57,
                                     "site": "Cummins", "port": "Port Lincoln"},
    "Poochera->Thevenard (road)": {"freight_2017_18": 16.76, "pathway_total": 63.76,
                                   "fees_ex_freight": 47.00,
                                   "site": "Poochera", "port": "Thevenard"},
}


def verify_pdf() -> bool:
    """Fail loudly if the cached PDF no longer contains what is quoted above."""
    txt = pdf_text()  # exits 2 if the PDF or pdftotext is missing
    need = ["Freight to port                 $8.46    $8.25",
            "Cummins to Port Lincoln--rail                $46.16   $50.82",
            "Poochera to Thevenard--road                  $57.75   $63.76"]
    ok = True
    for s in need:
        hit = s in txt
        ok &= hit
        print(f"   {'PASS' if hit else 'FAIL'}  {s.strip()[:70]}")
    for k, v in PUBLISHED.items():
        d = round(v["pathway_total"] - v["fees_ex_freight"], 2)
        hit = abs(d - v["freight_2017_18"]) < 0.005
        ok &= hit
        print(f"   {'PASS' if hit else 'FAIL'}  {k}: pathway total {v['pathway_total']} "
              f"- fees ex-freight {v['fees_ex_freight']} = {d} "
              f"(claimed {v['freight_2017_18']})")
    print(f"   VERDICT: {'PASS' if ok else 'FAIL'}")
    return ok


def main():
    print(f"PDF / arithmetic verification of the published EP freight-to-port figures ({PDF.name})")
    if not verify_pdf():
        # The module docstring promises the script fails if the transcription drifts.
        # Until 2026-09-06 the verdict was printed and then ignored, exit code 0.
        sys.exit(1)

    nodes, adj = build_graph()
    snap = make_snapper(nodes)
    feats = json.loads((PROCESSED / "sites.geojson").read_text(encoding="utf-8"))["features"]
    parcels = json.load(open(APP_DATA / "parcels.json", encoding="utf-8"))["parcels"]
    weights, _a, _b = parcel_weights(parcels)
    n = len(parcels)

    site_key, site_info = snap_sites(feats, snap)
    parcel_nodes, _snap_km = snap_parcels(parcels, snap)

    trees = {}

    def tree(nid):
        if nid not in trees:
            trees[nid] = dijkstra_time_then_km(adj, nid)[0]
        return trees[nid]

    def site_km(a, b):
        return tree(site_info[site_key[a]]["node"]).get(site_info[site_key[b]]["node"], INF)

    print()
    print("Published freight-to-port against our routed road distance")
    implied = []
    for k, v in PUBLISHED.items():
        km = site_km(v["site"], v["port"])
        rate = v["freight_2017_18"] / km
        esc = cartage_aud_per_t(km)[0]
        implied.append((k, km, rate))
        print(f"   {k:<32} routed {km:6.1f} km   published ${v['freight_2017_18']:5.2f}/t"
              f"   -> ${rate:.4f}/t-km   (ESCOSA marginal on the same km: ${esc:5.2f}/t)")
    road_rate = [r for k, _km, r in implied if "road" in k][0]
    print(f"   The ROAD pathway (Poochera->Thevenard) implies ${road_rate:.4f}/t-km, against")
    print("   ESCOSA's marginal $0.11-0.12/t-km. The marginal schedule is therefore a fair")
    print("   proxy for the incumbent's own published ROAD line-haul charge on EP, and the")
    print("   'marginal dollars are a floor' caveat bites much harder on the GROWER's short")
    print("   cart leg than on this long line haul.")

    # ------------------------------------------------ every EP site's line haul, both ways
    ports = [site_key["Port Lincoln"], site_key["Thevenard"]]
    r8 = network_states(feats)
    A = [site_key[f["properties"]["name"]] for f in r8["s2025_26"]["sites"]]
    inc_up = [i for i in A if site_info[i]["operator"] in INCUMBENT_OPERATORS
              and site_info[i]["role"] == "upcountry"]
    print()
    print("Every active Bunge upcountry site: routed km to its nearest Bunge port, priced")
    print("both at ESCOSA's marginal schedule and at the published Export Select road rate")
    print(f"implied above (${road_rate:.4f}/t-km, 2017-18 A$, DERIVED - see caveats).")
    rows = []
    for i in inc_up:
        km = min(tree(site_info[p]["node"]).get(site_info[i]["node"], INF) for p in ports)
        rows.append((site_info[i]["name"], km, cartage_aud_per_t(km)[0], km * road_rate))
    for nm, km, esc, es in sorted(rows, key=lambda r: -r[1]):
        print(f"   {nm:<14} {km:6.1f} km   ESCOSA ${esc:6.2f}/t   ExportSelect-implied ${es:6.2f}/t")

    # ------------------------------------- what that does to the whole-chain reading
    LB = site_key["Lucky Bay (T-Ports port)"]
    LOCKB, KIMBAB = site_key["Lock (T-Ports bunker)"], site_key["Kimba (T-Ports bunker)"]
    inc_A = [i for i in A if site_info[i]["operator"] in INCUMBENT_OPERATORS]
    km_of = {i: [tree(site_info[i]["node"]).get(pn, INF) for pn in parcel_nodes]
             for i in set(inc_A + [LB, LOCKB, KIMBAB])}
    linehaul = {i: min(tree(site_info[p]["node"]).get(site_info[i]["node"], INF) for p in ports)
                for i in inc_A}
    shuttle = {LB: 0.0,
               LOCKB: tree(site_info[LB]["node"]).get(site_info[LOCKB]["node"], INF),
               KIMBAB: tree(site_info[LB]["node"]).get(site_info[KIMBAB]["node"], INF)}

    def nearest_inc(pi):
        return min(((km_of[i][pi], i) for i in inc_A))

    for label, tp_pool in (("state A (Lucky Bay alone)", [LB]),
                           ("state B (Sept 2021: Lucky Bay + Lock + Kimba bunkers)",
                            [LB, LOCKB, KIMBAB])):
        sav_esc, sav_es = [], []
        for pi in range(n):
            bk, bi = nearest_inc(pi)
            without = bk + linehaul[bi]
            with_ = min(km_of[i][pi] + shuttle[i] for i in tp_pool)
            sav_esc.append(cartage_aud_per_t(without)[0] - cartage_aud_per_t(with_)[0])
            sav_es.append((without - with_) * road_rate)
        print()
        print(f"WHOLE ROAD CHAIN farm -> export position, {label}")
        for nm, v in (("ESCOSA marginal", sav_esc),
                      (f"Export Select implied ${road_rate:.3f}/t-km", sav_es)):
            print(f"   {nm:<38} EP mean ${wmean(weights, v):7.2f}/t   EP max ${max(v):7.2f}/t"
                  f"   >=$15 {wshare(weights, [x >= 15 for x in v]) * 100:5.1f}%"
                  f"   <=$0 {wshare(weights, [x <= 1e-9 for x in v]) * 100:5.1f}%")
            for d in ("WEP", "EEP", "LEP"):
                s2 = [i for i, p in enumerate(parcels) if p["district"] == d]
                w2 = [weights[i] for i in s2]
                print(f"      {d}: mean ${wmean(w2, [v[i] for i in s2]):7.2f}/t  "
                      f"max ${max(v[i] for i in s2):7.2f}/t  "
                      f">=$15 {wshare(w2, [v[i] >= 15 for i in s2]) * 100:5.1f}%  "
                      f"<=$0 {wshare(w2, [v[i] <= 1e-9 for i in s2]) * 100:5.1f}%")


if __name__ == "__main__":
    main()
