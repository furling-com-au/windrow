"""R9: what the independent gateway is worth to growers, in cartage dollars.

Tier 2 (geometry over published road distances and site locations) x Tier 1 (a published
rate schedule). NO simulation, NO fitted parameter, NO calibrated knob. Nothing here reads
packages/sim/src/calibrated.json, engine.ts, matrix.json, or any of A1/A2/A9/A15/A24.

WHAT THIS COMPUTES
------------------
For every CLUM grain-production cell on the Eyre Peninsula (the same 2.5 km parcels R0
uses, app/public/data/parcels.json), the ONE-WAY LOADED ROAD KILOMETRES from that cell to
each receival point, priced at ESCOSA's published marginal road-cartage schedule (A18), and
aggregated tonne-weighted by PIRSA district over four network states:

    A  "lucky_bay_only"   Bunge network + T-Ports Lucky Bay.       (attributed 2025/26)
    B  "bunkers_reopened" Bunge network + Lucky Bay + Lock + Kimba (attributed 2023/24)
    C  "no_independent"   Bunge network only. No non-Bunge receival point anywhere.
    D  "pre_2019"         Bunge network + the six sites that closed in 2019 + the one
                          still-dormant site. T-Ports does not yet exist.

Membership at A, B and D is r8_choice_geometry.network_states() unchanged - the same
status-field rule, imported rather than re-derived, so the two pages cannot drift apart.
C is A with the single independent point removed and is new here.

THE MEASURE - WHY IT IS WHAT IT IS
----------------------------------
"Distance to the nearest independent point" is NOT a cartage cost and is not reported as
one here. A grower carts to whichever point is best for them, which is very nearly always
the nearest one of ANY owner; the gateway's cartage value is realised only by the growers
for whom it actually is the best destination. So four measures are computed, and which one
answers "what is the gateway worth" depends on what is being asked:

  M1  THE BILL. Cartage to the cheapest receival point of any owner, $/t.
      What a grower actually pays. Defined at ALL FOUR states - including pre-2019, where
      R0's ownership ladder is undefined - which is why the four-state ladder below is
      possible at all. Its state-to-state deltas are the REALISED cartage effect: what the
      network change did to the bill growers actually pay.

  M2  THE TOLL (PRIMARY). Cost to the nearest independent point MINUS cost to the nearest
      incumbent point, $/t. What it costs a grower to take a load to the non-Bunge option
      instead of their nearest Bunge site - equivalently, the price premium the independent
      must offer, per tonne, before that load is worth moving. Defined only where an
      independent point exists (A and B). This is the primary published measure because it
      is the number a grower can act on, and because it is the number that MOVED: at state
      C there is no alternative at any price, at A the toll is a number, at B a smaller one.

  M3  THE CATCHMENT. The subset of production for which the independent point is the
      cheapest destination, or within $1 / $2 / $5 a tonne of it. This is where M1's
      realised effect comes from and it is small; reporting M2 without M3 would imply every
      grower pays the toll, and almost none do - they simply keep delivering to Bunge.

  M4  THE PORT RUN. Cartage to the nearest EXPORT PORT of any owner, $/t. The task's
      "nearest export-capable destination" measure. Note that on the roster as it stands
      EVERY receival point is export-capable in the sense that matters - a Bunge upcountry
      silo feeds Bunge's Port Lincoln and Thevenard, a T-Ports bunker feeds Lucky Bay - so
      an "export-capable" test over all points collapses exactly onto M1. M4 is therefore
      defined narrowly and honestly as DIRECT-TO-PORT delivery, which is a real delivery
      pattern on EP and is the one where Lucky Bay's location does the most work.

STRUCTURAL POINT ABOUT LUCKY BAY, HANDLED EXPLICITLY
----------------------------------------------------
Lucky Bay is a PORT, not an upcountry silo, and T-Ports' model had growers delivering
either to the Lock and Kimba bunkers or direct to Lucky Bay. The grower's truck does the
same thing in every case: ONE loaded one-way run from farm to a place where it can tip and
be paid, and it stops there. What happens after that - T-Ports shuttling bunker grain to
Lucky Bay, or Bunge line-hauling silo grain to Port Lincoln - is the OPERATOR's cost, not
the grower's, and is outside every number on this page. That is what makes it coherent to
put a port and a silo in the same argmin: both are ends of a grower's cart leg. What it
does NOT do is make them equivalent commercially - see the caveats.

DESTINATION CHOICE AND THE BAND INVERSION
-----------------------------------------
The destination is selected by MINIMUM ROUTED ROAD KILOMETRES and then priced. It is not
selected by minimum dollars, and the difference is deliberate. ESCOSA's bands are flat and
selected by the whole distance (A18), so the priced cost is NOT monotone in distance across
the 50 km edge: 49 km prices at 49 x $0.12 = $5.88 and 51 km at 51 x $0.11 = $5.61, so a
strictly farther site can price cheaper. That is an artefact of a pricing convention, not
of anything a truck does. Selecting on kilometres keeps the behaviour real; the share of
production where a dollar-minimising choice would differ is measured and published below.

THE RATE
--------
ESCOSA, Inquiry into the South Australian bulk grain export supply chain costs - Final
Report, 29 January 2019, Box 5.2 (p. 91): $0.12/tonne-km up to 50 km, $0.11/tonne-km for
50-250 km. MARGINAL, one-way loaded kilometres, flat bands, 2018-19 A$, unindexed. The
bands are imported from pipeline/r9_escosa_rate_check.py rather than retyped, so the rate
exists once in this repo and the verification script and this script cannot disagree.
Read A18 before quoting anything here. The four things that matter most:
  * MARGINAL means these dollars are a FLOOR, not a delivered cartage price. At EP's
    ~144 km average haul the same rate gives $15.84/t where a full commercial rate card
    gives ~$29.90/t and a budget guide $35.00/t.
  * 2018-19 A$, deliberately not indexed.
  * SA-wide, not EP-specific, and the 50-250 km band - which carries most of the dollars
    here - is unpublished AEGIC advice to the Commission, not a public document.
  * Whether the underlying cost line embeds an empty return leg is UNRESOLVED and worth a
    factor of two. The distance is not doubled here; the bound is reported instead.

AND THE HALF OF THE DECISION THIS CANNOT SEE
--------------------------------------------
Growers deliver where PRICE MINUS CARTAGE is best. This project has no price data - 13 days
of off-season cash bids and nothing else. Nothing on this page is a total grower benefit or
loss, and every output says so.

Reproduce
---------
    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe pipeline/r9_cartage.py

Writes docs/r9_cartage.md and docs/r9_cartage.json.
"""
from __future__ import annotations

import heapq
import json
import math
import sys
from collections import defaultdict
from datetime import date
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
    wquantile,
    wshare,
)
from r9_escosa_rate_check import BANDS  # noqa: E402

INF = float("inf")

# ---------------------------------------------------------------- the published rate
# BANDS is imported, not retyped: [(50.0, 0.12), (250.0, 0.11)] in 2018-19 A$/tonne-km,
# ESCOSA 2019 Box 5.2 p.91. pipeline/r9_escosa_rate_check.py verifies BOTH the transcription
# (against the cached PDF) and the application rule (against ESCOSA's own four published
# results). Do not edit the numbers here; there are none to edit.
CEILING_KM = BANDS[-1][0]
RATE_BASE_YEAR = "2018-19 A$ (nominal, deliberately not indexed - A18)"
RATE_CITE = (
    "ESCOSA, Inquiry into the South Australian bulk grain export supply chain costs - "
    "Final Report, 29 January 2019, Box 5.2, p. 91: \"Only the marginal freight cost has "
    "been used, $0.12 ($/tonne-km) for up to 50 kilometres and $0.11 ($/tonne-km) for 50 "
    "to 250 kilometres.\""
)
RATE_VERIFY = ".venv/Scripts/python.exe pipeline/r9_escosa_rate_check.py   # VERDICT: PASS"


def cartage_aud_per_t(km: float) -> tuple[float, bool]:
    """ESCOSA marginal cartage for a one-way loaded haul of km kilometres.

    Flat bands selected by the WHOLE distance, applied once to the one-way distance, no
    cumulative tiering, empty return not added. Returns (dollars_per_tonne, extrapolated),
    where extrapolated is True above the schedule's 250 km ceiling - past which applying
    $0.11 is an EXTRAPOLATION and not a citation (A18). Nothing is silently clipped.
    """
    if not math.isfinite(km):
        return INF, False
    for upper, rate in BANDS:
        if km <= upper:
            return km * rate, False
    return km * BANDS[-1][1], True


# ---------------------------------------------------------------------- presentation
MEASURE_CHOICE = (
    "PRIMARY: M2, the TOLL - cartage to the nearest independent receival point minus "
    "cartage to the nearest incumbent one, A$/t, tonne-weighted by district. Chosen for "
    "three reasons. (1) It is the only one of the four measures that is a grower DECISION "
    "variable: it converts directly into the price premium, per tonne, that the "
    "independent has to beat before a load is worth moving, which is the same unit a "
    "grower reads a basis quote in. (2) It is the quantity the network change actually "
    "moved. At state C the toll is not a large number, it is NOT A NUMBER - there is no "
    "non-Bunge receival point on the peninsula at any price. State A gives it a value; "
    "state B roughly halves it. (3) The obvious alternative, 'cartage to the nearest "
    "independent point', is not a cost anybody pays: it is a distance to a place most "
    "growers never go. REPORTED BESIDE IT, AND NOT OPTIONAL: M1, the bill actually paid "
    "(cartage to the cheapest point of any owner), because M1 is what moves growers' real "
    "costs and it BARELY MOVES between states - that is a finding, not an omission, and a "
    "reader given M2 alone would wrongly infer that every grower pays the toll. M3, the "
    "share of production for which the independent point genuinely is the cheapest or "
    "near-cheapest destination, because that share is what M1's movement is made of. M4, "
    "direct-to-port cartage, because that is the delivery pattern in which Lucky Bay's "
    "position does the most work and it is the task's 'nearest export-capable "
    "destination' measure made honest."
)

MEASURE_REJECTED = [
    ("cartage to the nearest INDEPENDENT point, published bare",
     "Rejected as a headline. It is a distance to a place most EP growers have never "
     "delivered to, priced. It is reported here as an input to the toll and as a level "
     "(so a reader can see what using the gateway costs outright) but it is not 'what the "
     "gateway is worth', and quoting it alone would read as a cost growers bear."),
    ("cartage to the nearest EXPORT-CAPABLE destination, over all points",
     "Rejected as it collapses onto M1 exactly. Every receival point on this roster feeds "
     "an export chain: a Bunge upcountry silo feeds Port Lincoln and Thevenard, a T-Ports "
     "bunker feeds Lucky Bay. Making the test 'export-capable' therefore excludes nothing "
     "and adds no information. What does not collapse is DIRECT-TO-PORT delivery, which "
     "is M4."),
    ("the difference in cartage for the subset that uses the independent point",
     "Not rejected - it is M3, and it is published. But it cannot be the headline on its "
     "own: it is a saving conditional on a delivery choice this project cannot observe. "
     "There is no site-level receival series in this repo at any granularity "
     "(docs/gate_findings.md section 3), so who actually delivered where is not known and "
     "M3's catchment is a geometric catchment, not an observed one."),
    ("total cartage dollars saved across the peninsula",
     "Rejected. Multiplying $/t by district tonnage produces a large headline number that "
     "implies a measured aggregate benefit. It would be a product of two modelled "
     "quantities (the cell weighting, A14 x CLUM, and a geometric delivery choice) priced "
     "at a marginal rate that is explicitly not a full cartage price, with no price data "
     "on the other side of the ledger. The per-tonne figure is what a grower can check "
     "against their own farm; the aggregate is what a press release would quote."),
]

STRUCTURAL_NOTE = (
    "Lucky Bay is a PORT, not an upcountry silo. T-Ports' model had growers delivering "
    "either to the Lock and Kimba bunkers or direct to Lucky Bay, and in every case the "
    "grower's truck does one loaded one-way run from farm to a place where it tips and is "
    "paid, and stops. Whatever moves the grain onward - T-Ports shuttling bunker grain to "
    "Lucky Bay, Bunge line-hauling silo grain to Port Lincoln or Thevenard - is the "
    "OPERATOR's cost and is outside every number here. That is what makes it coherent to "
    "put a port and a silo in the same nearest-destination comparison. It does NOT make "
    "them commercially equivalent: a port and an upcountry silo differ in segregations, "
    "receival standards, opening hours, queueing and the contract on offer, none of which "
    "this page can see. And it is why state A's toll is as large as it is - with both "
    "bunkers shut, the only non-Bunge place to tip a load is a port on the far side of the "
    "peninsula."
)

CARTAGE_IS_HALF = (
    "CARTAGE IS HALF OF A DELIVERY DECISION. Growers deliver where PRICE MINUS CARTAGE is "
    "best. This project has no price data - 13 days of off-season cash bids and nothing "
    "else (data/SOURCES.md, operator-cash-prices-api). Every figure on this page is one "
    "side of that ledger. A toll of $X/t says the independent must be worth $X/t more at "
    "the weighbridge before the load moves; it does NOT say whether it was, and nothing "
    "here is a total grower benefit or loss."
)

MARGINAL_FLOOR = (
    "THESE ARE MARGINAL DOLLARS AND THEREFORE A FLOOR. ESCOSA's rate is explicitly the "
    "additional cost of travelling further once the truck is on the road. Truck ownership, "
    "loading, queueing, turnaround and driver time are outside it BY DESIGN, and ESCOSA "
    "says so. At EP's ~144 km average site-to-port haul the same rate gives $15.84/t "
    "against a 2026 commercial rate card's $29.90/t and a 2026 SA budget guide's $35.00/t "
    "- the marginal rate is roughly half a delivered cartage price. A grower reading "
    "'$X/t more' here is reading the extra fuel-and-running cost of the extra kilometres, "
    "not the extra cost of running the extra trips."
)

RETURN_LEG_OPEN = (
    "THE EMPTY RETURN LEG IS UNRESOLVED AND IS WORTH A FACTOR OF TWO. Established: ESCOSA "
    "APPLIES the rate to a one-way distance - all four of its own published results "
    "reproduce on that reading and on no other. Not established: whether AEGIC's "
    "underlying cost line was itself built on a round-trip cycle. The report is silent. "
    "The distance is NOT doubled here, because doubling would double-count if the cost "
    "line already embeds the return. The doubled figures are reported once, as a labelled "
    "UPPER BOUND on the open question, and are not a published result. Settling it needs "
    "AEGIC, Australia's grain supply chains, October 2018, Note 2c to Figure 4, p. 18, "
    "which is not cached in this repo."
)

ROSTER_CAVEAT = (
    "EVERY MEASURE ON THIS PAGE EXCEPT THE BARE INDEPENDENT LEVEL DEPENDS ON THE SITE "
    "ROSTER, AND THE ROSTER IS KNOWN INCOMPLETE. R0's threshold rows survive a roster "
    "defect because they are a function of the drive to the nearest INDEPENDENT point "
    "alone and every roster defect on record is incumbent-side. M1, M3 and M4 are not "
    "protected that way, and neither is the toll M2, because the toll is measured FROM "
    "the incumbent. docs/roster_audit_2026-08.md section 5: Tooligie (received 2022/23, "
    "2023/24, 2024/25), Cowell (2017/18, 2018/19) and Mangalo (2018/19) are absent from "
    "sites.geojson altogether, and Cungena is tagged closed_2019 but received grain in "
    "2022/23. THE DIRECTIONS ARE KNOWN AND ARE NOT SYMMETRIC. Missing incumbent sites "
    "raise the modelled cost to the nearest incumbent point, so: M1 levels are UPPER "
    "BOUNDS at every state; the toll M2 is a LOWER BOUND (a nearer real Bunge site would "
    "make the independent option relatively dearer); M3's catchment share is an UPPER "
    "BOUND. And the contamination is not even across states - Cowell and Mangalo bear on "
    "pre-2019 only, Tooligie on the 2023/24-attributed state and probably the current "
    "ones, Cungena on all three post-2019 states - so the state-to-state DELTAS carry it "
    "too. This is the single biggest defect in these numbers and it is not fixed here: "
    "fixing it means coordinates and capacities for three sites, and A4's capacity split "
    "entangles that with the calibration (roster_audit section 5)."
)

LUCKY_BAY_COORD = (
    "STATE A RESTS ENTIRELY ON ONE COORDINATE. With both bunkers shut, Lucky Bay is the "
    "only independent receival point on the peninsula, so the toll at state A is a pure "
    "function of the road distance to a single point. That point is registered in "
    "sites.geojson at a TOWN/HAMLET node ('Lucky Bay, South Australia' hamlet node, "
    "facility adjoins hamlet) - the same precision class A11 gives Lock and Kimba a <=5 km "
    "tolerance for, and it is registered in no assumption. It is swept here rather than "
    "asserted: the site is displaced 0 / 2.5 / 5 km on eight bearings, RE-SNAPPED to the "
    "road graph and RE-ROUTED with a fresh Dijkstra, and the envelope is published beside "
    "every state-A figure."
)

BUNKER_SOURCE_CAVEAT = (
    "THE SEASON LABELS ARE ATTRIBUTIONS AND ONE OF THEM IS UNSOURCED. The four states are "
    "defined by their CONTENT - which points exist - and every number here follows from "
    "that content alone. The attribution of state A to 2025/26 rests on the claim that "
    "both T-Ports bunkers were closed for that season, and that claim has no source in "
    "this repo: there is no tports.com/harvest entry in data/SOURCES.md, no cached page "
    "under data/raw/, no retrieval date, and for KIMBA no closure evidence at all (its "
    "status field is set with a notes field reading only 'Built for 2021 harvest'). The "
    "only record is a hand-typed note on LOCK in pipeline/manual_sites.json citing a live "
    "read of tports.com/harvest on 2026-08-19 - the same off-season live read that "
    "docs/roster_audit_2026-08.md section 1 identifies as the root cause of four wrongly "
    "closed Bunge sites. Read A and B as 'Lucky Bay alone' and 'Lucky Bay plus both "
    "bunkers'. Do not publish either season label until the page is archived and "
    "registered."
)

SNAP_NOTE = (
    "A cell is routed from its nearest node on the OSM graph and the snap leg itself is "
    "not driven, so a large snap understates that cell's kilometres to EVERY destination "
    "equally. On the LEVELS (M1, M4, the bare independent level) it understates the "
    "dollars. On the TOLL it very largely cancels, because the toll is a difference of two "
    "hauls that share the same snap - it survives only through the band edge, where the "
    "two hauls can fall in different bands. Tonne-weighted mean snap and the share of "
    "production snapping more than 2 km are printed with it so the size of it is visible."
)

BAND_INVERSION_NOTE = (
    "ESCOSA's bands are FLAT and selected by the whole distance, so the priced cost is not "
    "monotone in distance across the 50 km edge: 49 km prices at $5.88 and 51 km at $5.61. "
    "The destination here is chosen by MINIMUM KILOMETRES and then priced, because that is "
    "what a truck does; choosing by minimum dollars would let a pricing convention pick a "
    "farther silo. The share of production where the two choices differ, and what it is "
    "worth, is measured below rather than assumed away."
)

CARRIED_ASSUMPTIONS = [
    ("A18", "the ESCOSA marginal cartage schedule, used as published. This is the ONLY "
            "place a dollar enters this page. The app's flat A$0.10/t-km working lever is "
            "NOT used and must not be confused with it."),
    ("A5", "road class speeds - used only to CHOOSE the path (least time), not to price "
           "it. The kilometres are then read off that path, never derived as minutes x "
           "speed. A least-DISTANCE routing variant is published as a standing "
           "sensitivity and it depends on no assumed speed at all."),
    ("A11", "the Lock and Kimba town-centroid coordinates, <=5 km tolerance. Bears on "
            "state B only. Swept, with magnitudes and bearings both varied independently."),
    ("A12", "season site sets. Load-bearing here in a way it is not for R0's threshold "
            "rows - see the roster caveat. This script inherits r8_choice_geometry's "
            "status-field state construction, including its known omission of "
            "Nunjikompita from the 2023/24-attributed state."),
    ("A14", "district boundaries approximated by LGA composition - used for the tonne "
            "weighting only, not for routing."),
    ("Lucky Bay coordinate", "a hamlet node, registered in no assumption. Swept here. It "
                             "should be registered in ASSUMPTIONS.md."),
    ("A1/A2/A4/A9/A15/A24", "NOT USED. No payload, no bay count, no capacity, no fitted "
                            "parameter enters any number on this page. A cart leg is "
                            "priced per tonne, so the truck configuration cancels out of "
                            "it entirely."),
]

DISTRICTS = ("WEP", "EEP", "LEP")
DISTRICT_LONG = {"WEP": "Western Eyre Peninsula", "EEP": "Eastern Eyre Peninsula",
                 "LEP": "Lower Eyre Peninsula"}
NEAR_BANDS_AUD = (1.0, 2.0, 5.0)

SWEEP_OFFSET_KM = (0.0, 2.5, 5.0)
SWEEP_BEARINGS_DEG = (0, 45, 90, 135, 180, 225, 270, 315)


# --------------------------------------------------------------------------- routing
def dijkstra_time_then_km(adj, src: str) -> dict[str, float]:
    """Least-TIME tree from src, returning the KILOMETRES driven along that least-time path.

    This is the same construction pipeline/p2_build_matrix.py uses to fill matrix.json's
    site_km: route on minutes, then carry the network distance of the chosen path out
    beside it. A5's explicit instruction is that km must never be recovered as
    minutes x speed. The truck takes the fast road and pays for the kilometres it drives
    on it, which is why this and not least-distance is the primary.
    """
    dist = {src: 0.0}
    km = {src: 0.0}
    pq = [(0.0, src)]
    while pq:
        d, n = heapq.heappop(pq)
        if d > dist.get(n, INF):
            continue
        kn = km[n]
        for m, w, k in adj[n]:
            nd = d + w
            if nd < dist.get(m, INF):
                dist[m] = nd
                km[m] = kn + k
                heapq.heappush(pq, (nd, m))
    return km, dist


def dijkstra_km(adj, src: str) -> dict[str, float]:
    """Least-DISTANCE tree from src. Used only for the A5-free sensitivity."""
    dist = {src: 0.0}
    pq = [(0.0, src)]
    while pq:
        d, n = heapq.heappop(pq)
        if d > dist.get(n, INF):
            continue
        for m, _w, k in adj[n]:
            nd = d + k
            if nd < dist.get(m, INF):
                dist[m] = nd
                heapq.heappush(pq, (nd, m))
    return dist


def displace(lon: float, lat: float, km: float, bearing_deg: float):
    th = math.radians(bearing_deg)
    dlat = km * math.cos(th) / 111.32
    dlon = km * math.sin(th) / (111.32 * math.cos(math.radians(lat)))
    return lon + dlon, lat + dlat


# ------------------------------------------------------------------------ evaluation
def evaluate(km_of_site, idx, site_info, parcels, weights, n_parcels):
    """All four measures for one network state, given per-site km vectors.

    km_of_site: dict site_index -> list of km, one per parcel.
    idx:        the site indices that are receival points in this state.
    """
    inc = [i for i in idx if site_info[i]["operator"] in INCUMBENT_OPERATORS]
    ind = [i for i in idx if site_info[i]["operator"] not in INCUMBENT_OPERATORS]
    ports = [i for i in idx if site_info[i]["role"] == "port"]

    def best(pool, pi):
        """(km, site_index) of the fewest-kilometre point in pool, or (INF, None)."""
        bk, bi = INF, None
        for i in pool:
            k = km_of_site[i][pi]
            if k < bk:
                bk, bi = k, i
        return bk, bi

    out = {
        "km_any": [], "km_inc": [], "km_ind": [], "km_port": [],
        "cost_any": [], "cost_inc": [], "cost_ind": [], "cost_port": [],
        "name_any": [], "name_ind": [],
        "extrapolated_any": [], "extrapolated_ind": [],
        "dollar_choice_differs": [], "dollar_choice_gain": [],
    }
    unreachable = 0
    for pi in range(n_parcels):
        ka, ia = best(idx, pi)
        ki, _ = best(inc, pi)
        kd, id_ = best(ind, pi) if ind else (INF, None)
        kp, _ = best(ports, pi) if ports else (INF, None)
        if not math.isfinite(ka):
            unreachable += 1
        ca, xa = cartage_aud_per_t(ka)
        ci, _ = cartage_aud_per_t(ki)
        cd, xd = cartage_aud_per_t(kd)
        cp, _ = cartage_aud_per_t(kp)
        out["km_any"].append(ka); out["km_inc"].append(ki)
        out["km_ind"].append(kd); out["km_port"].append(kp)
        out["cost_any"].append(ca); out["cost_inc"].append(ci)
        out["cost_ind"].append(cd); out["cost_port"].append(cp)
        out["name_any"].append(site_info[ia]["name"] if ia is not None else None)
        out["name_ind"].append(site_info[id_]["name"] if id_ is not None else None)
        out["extrapolated_any"].append(xa)
        out["extrapolated_ind"].append(xd)
        # band inversion: would a dollar-minimising grower pick a different destination?
        cheapest = INF
        for i in idx:
            c, _ = cartage_aud_per_t(km_of_site[i][pi])
            if c < cheapest:
                cheapest = c
        out["dollar_choice_differs"].append(cheapest < ca - 1e-9)
        out["dollar_choice_gain"].append(max(0.0, ca - cheapest))
    out["unreachable"] = unreachable
    out["has_independent"] = bool(ind)
    out["n_points"] = len(idx)
    out["n_independent"] = len(ind)
    out["n_ports"] = len(ports)
    return out


def sweep_eval(km_inc, ind_km_vectors, parcels, weights):
    """M1 and M2 only, for a coordinate sweep.

    The incumbent side is FIXED during a coordinate sweep (no incumbent site is displaced),
    so km_inc is passed in already computed. The independent side is rebuilt from the
    displaced vectors. This is the same arithmetic as evaluate()/summarise(), narrowed to
    the two published measures so that 289 configurations run in seconds; it is checked
    against the full path at the undisplaced configuration (offset 0) in main().
    """
    cost_inc = [cartage_aud_per_t(k)[0] for k in km_inc]
    km_ind = [min(v[i] for v in ind_km_vectors) for i in range(len(km_inc))]
    cost_ind = [cartage_aud_per_t(k)[0] for k in km_ind]
    cost_any = [cartage_aud_per_t(min(ki, kd))[0] for ki, kd in zip(km_inc, km_ind)]
    toll = [b - a for a, b in zip(cost_inc, cost_ind)]
    out = {}
    for scope in ("EP",) + DISTRICTS:
        sel = (list(range(len(parcels))) if scope == "EP"
               else [i for i, p in enumerate(parcels) if p["district"] == scope])
        w = [weights[i] for i in sel]
        out[scope] = {
            "toll": round(wmean(w, [toll[i] for i in sel]), 2),
            "bill": round(wmean(w, [cost_any[i] for i in sel]), 2),
        }
    return out


def summarise(ev, parcels, weights, ep_only=None):
    """Tonne-weighted summary of one state, EP-wide and by district."""
    def rows(sel):
        w = [weights[i] for i in sel]
        km_any = [ev["km_any"][i] for i in sel]
        km_ind = [ev["km_ind"][i] for i in sel]
        km_inc = [ev["km_inc"][i] for i in sel]
        km_port = [ev["km_port"][i] for i in sel]
        c_any = [ev["cost_any"][i] for i in sel]
        c_inc = [ev["cost_inc"][i] for i in sel]
        c_ind = [ev["cost_ind"][i] for i in sel]
        c_port = [ev["cost_port"][i] for i in sel]
        r = {
            "tonnes_weight": round(sum(w), 0),
            "m1_bill_aud_per_t": round(wmean(w, c_any), 2),
            "m1_km": round(wmean(w, km_any), 1),
            "m1_p50_aud_per_t": round(wquantile(w, c_any, 0.5), 2),
            "m1_p90_aud_per_t": round(wquantile(w, c_any, 0.9), 2),
            "m4_port_aud_per_t": round(wmean(w, c_port), 2),
            "m4_port_km": round(wmean(w, km_port), 1),
            "incumbent_aud_per_t": round(wmean(w, c_inc), 2),
        }
        if ev["has_independent"]:
            toll = [b - a for a, b in zip(c_inc, c_ind)]
            r |= {
                "independent_level_aud_per_t": round(wmean(w, c_ind), 2),
                "independent_level_km": round(wmean(w, km_ind), 1),
                "m2_toll_aud_per_t": round(wmean(w, toll), 2),
                "m2_toll_p50_aud_per_t": round(wquantile(w, toll, 0.5), 2),
                "m2_toll_p90_aud_per_t": round(wquantile(w, toll, 0.9), 2),
                "m3_share_independent_is_cheapest": round(
                    wshare(w, [t <= 0 for t in toll]), 4),
                "m3_share_within": {
                    f"{b:.0f}": round(wshare(w, [t <= b for t in toll]), 4)
                    for b in NEAR_BANDS_AUD},
                "m3_saving_where_independent_cheapest_aud_per_t": round(
                    wmean([wi for wi, t in zip(w, toll) if t <= 0],
                          [-t for t in toll if t <= 0]), 2) if any(t <= 0 for t in toll)
                else 0.0,
                "share_over_250km_ceiling": round(
                    wshare(w, [k > CEILING_KM for k in km_ind]), 4),
                # The toll restricted to production whose independent haul is INSIDE the
                # published schedule, so a reader can separate the fully-cited part of the
                # answer from the extrapolated part. It is not a like-for-like alternative
                # to the row above: it is a different, smaller population - the growers
                # near enough to the gateway for the schedule to price their haul at all.
                "m2_toll_within_schedule_aud_per_t": (
                    round(wmean([wi for wi, k in zip(w, km_ind) if k <= CEILING_KM],
                                [t for t, k in zip(toll, km_ind) if k <= CEILING_KM]), 2)
                    if any(k <= CEILING_KM for k in km_ind) else None),
            }
        else:
            r |= {
                "independent_level_aud_per_t": None,
                "m2_toll_aud_per_t": None,
                "m2_undefined_why": (
                    "There is no non-Bunge receival point anywhere in this state. The "
                    "toll is not a large number, it is not a number: there is no "
                    "alternative to price at any premium. Compare this state on M1 and "
                    "M4, which are defined at every state."),
            }
        return r

    all_idx = list(range(len(parcels)))
    out = {"EP": rows(all_idx)}
    for d in DISTRICTS:
        out[d] = rows([i for i, p in enumerate(parcels) if p["district"] == d])
    return out


def main():
    nodes, adj = build_graph()
    snap = make_snapper(nodes)
    feats = json.loads((PROCESSED / "sites.geojson").read_text(encoding="utf-8"))["features"]
    parcels = json.load(open(APP_DATA / "parcels.json", encoding="utf-8"))["parcels"]
    weights, dist_t, _ = parcel_weights(parcels)
    n = len(parcels)
    print(f"parcels: {n}  sites: {len(feats)}  nodes: {len(nodes)}")

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

    parcel_nodes, parcel_snap = [], []
    for p in parcels:
        nid, err = snap(p["lon"], p["lat"])
        parcel_nodes.append(nid)
        parcel_snap.append(err)

    tree_cache: dict[str, list[float]] = {}
    min_cache: dict[str, list[float]] = {}

    def km_vector(nid: str, mode: str = "time") -> list[float]:
        key = f"{mode}:{nid}"
        if key not in tree_cache:
            if mode == "time":
                t, tmin = dijkstra_time_then_km(adj, nid)
                min_cache[nid] = [tmin.get(pn, INF) for pn in parcel_nodes]
            else:
                t = dijkstra_km(adj, nid)
            tree_cache[key] = [t.get(pn, INF) for pn in parcel_nodes]
        return tree_cache[key]

    km_of_site = {i: km_vector(s["node"]) for i, s in enumerate(site_info)}
    min_of_site = {i: min_cache[s["node"]] for i, s in enumerate(site_info)}

    # ------------------------------------------------------------------ the four states
    r8_states = network_states(feats)
    a_names = [f["properties"]["name"] for f in r8_states["s2025_26"]["sites"]]
    b_names = [f["properties"]["name"] for f in r8_states["s2023_24"]["sites"]]
    d_names = [f["properties"]["name"] for f in r8_states["pre_2019"]["sites"]]
    c_names = [nm for nm in a_names
               if site_info[site_key[nm]]["operator"] in INCUMBENT_OPERATORS]

    STATES = {
        "A_lucky_bay_only": {
            "letter": "A",
            "label": "Lucky Bay only",
            "attributed": "2025/26 as it stands (attribution UNSOURCED - see caveat)",
            "desc": "the current Bunge network plus T-Ports Lucky Bay; both inland "
                    "T-Ports bunkers absent",
            "names": a_names,
        },
        "B_bunkers_reopened": {
            "letter": "B",
            "label": "Lucky Bay + Lock + Kimba bunkers",
            "attributed": "the 2023/24 network; equivalently, the bunkers reopened",
            "desc": "the current Bunge network plus Lucky Bay plus both T-Ports inland "
                    "bunkers",
            "names": b_names,
        },
        "C_no_independent": {
            "letter": "C",
            "label": "no independent point at all",
            "attributed": "counterfactual - Lucky Bay unavailable",
            "desc": "the current Bunge network alone; every receival point on the "
                    "peninsula is operated by the incumbent",
            "names": c_names,
        },
        "D_pre_2019": {
            "letter": "D",
            "label": "pre-2019",
            "attributed": "before T-Ports existed and before the June 2019 closures",
            "desc": "the current Bunge network plus the six sites closed in June 2019 "
                    "plus the one still-dormant site (A12); no independent operator",
            "names": d_names,
        },
    }

    evals, summaries = {}, {}
    for skey, sdef in STATES.items():
        idx = [site_key[nm] for nm in sdef["names"]]
        ev = evaluate(km_of_site, idx, site_info, parcels, weights, n)
        evals[skey] = ev
        summaries[skey] = summarise(ev, parcels, weights)
        s = summaries[skey]["EP"]
        print(f"{sdef['letter']}  {sdef['label']:<38} points={ev['n_points']:>2} "
              f"M1 ${s['m1_bill_aud_per_t']:>5.2f}/t  M2 "
              f"{('$%.2f/t' % s['m2_toll_aud_per_t']) if s['m2_toll_aud_per_t'] is not None else 'undefined':>10}"
              f"  M4 ${s['m4_port_aud_per_t']:>6.2f}/t")

    # ------------------------------------------------------ cross-check against R0
    # R0 (pipeline/r8_choice_geometry.py) publishes the tonne-weighted mean drive in
    # MINUTES to the nearest receival point of any owner for the same states, off the same
    # graph and the same weights. M1 is the same journey priced in kilometres, so the two
    # must be consistent. This is an internal consistency check on the routing, not a
    # publication of R0's Ladder A, which is not quotable (docs/gate_findings.md).
    r0_check = {}
    for skey, sdef in STATES.items():
        idx = [site_key[nm] for nm in sdef["names"]]
        mins = [min(min_of_site[i][pi] for i in idx) for pi in range(n)]
        mm = wmean(weights, mins)
        kk = summaries[skey]["EP"]["m1_km"]
        r0_check[skey] = {
            "wmean_minutes_to_nearest_any_owner": round(mm, 1),
            "wmean_km_to_nearest_any_owner": kk,
            "implied_mean_speed_kmh": round(kk / mm * 60.0, 1),
        }
        print(f"   check {sdef['letter']}: nearest point of any owner "
              f"{mm:5.1f} min / {kk:5.1f} km  -> {kk / mm * 60.0:.1f} km/h implied")

    # ------------------------------------------- the bunkers are beside Bunge's own sites
    # Computed, not asserted. This is the single most important structural fact on the
    # page: it is why state B's TOLL collapses while state B's BILL does not move at all.
    colocation = {}
    for nm in ("Lock (T-Ports bunker)", "Kimba (T-Ports bunker)",
               "Lucky Bay (T-Ports port)"):
        s0 = site_info[site_key[nm]]
        best = None
        for i, s in enumerate(site_info):
            if s["operator"] not in INCUMBENT_OPERATORS or s["status"] != "active_2025_26":
                continue
            dkm = math.hypot((s["lon"] - s0["lon"]) * math.cos(math.radians(s0["lat"])),
                             s["lat"] - s0["lat"]) * 111.32
            if best is None or dkm < best[0]:
                best = (dkm, s["name"])
        colocation[nm] = {"nearest_active_incumbent_site": best[1],
                          "straight_line_km": round(best[0], 2)}
    COLOCATION_NOTE = (
        "THE TWO INLAND BUNKERS ARE NOT IN NEW COUNTRY; THEY ARE BESIDE BUNGE'S OWN SITES. "
        f"The T-Ports Lock bunker is {colocation['Lock (T-Ports bunker)']['straight_line_km']} "
        "km from Bunge's Lock silo and the T-Ports Kimba bunker is "
        f"{colocation['Kimba (T-Ports bunker)']['straight_line_km']} km from Bunge's Kimba "
        "silo. That single fact explains the shape of every table below. Reopening them "
        "moves the BILL by about a cent a tonne, because no grower has to drive anywhere "
        "new; it roughly halves the TOLL, because for a large part of the peninsula the "
        "second buyer is standing in the yard the grower was already driving to. The "
        "bunkers were never a cartage improvement. They were a competition one, at "
        "locations that had already been chosen. Lucky Bay is the opposite case: "
        f"{colocation['Lucky Bay (T-Ports port)']['straight_line_km']} km from the nearest "
        "active Bunge site, a genuinely new place to tip a load, and a port."
    )
    print("   " + COLOCATION_NOTE.split(". ")[0])

    # -------------------------------------------------------------------- state deltas
    def delta(frm: str, to: str, field: str):
        row = {}
        for scope in ("EP",) + DISTRICTS:
            a = summaries[frm][scope].get(field)
            b = summaries[to][scope].get(field)
            row[scope] = None if (a is None or b is None) else round(b - a, 2)
        return row

    LADDER = [
        ("D_pre_2019", "C_no_independent",
         "The cartage cost of losing the seven sites that went from the pre-2019 network "
         "to the current one - the six closed in June 2019 plus Nunjikompita, since gone "
         "dormant - holding OWNERSHIP constant, because both states are incumbent-only "
         "and no gateway effect is mixed in. READ IT AS AN UPPER BOUND. Only two of the "
         "six 2019 sites (Minnipa and Kyancutta) were operating the year before; the "
         "other four are in the group the operator described as 'not open the year prior' "
         "(Stock Journal, 6 June 2019). Treating all six as open overstates the pre-2019 "
         "network by four sites, understates state D's bill, and therefore overstates "
         "this delta. Pulling the other way, Cowell and Mangalo were receiving grain "
         "pre-2019 and are missing from sites.geojson entirely, which understates it"),
        ("C_no_independent", "A_lucky_bay_only",
         "WHAT THE GATEWAY IS WORTH in cartage actually paid: the change in the bill "
         "when the peninsula's one independent point is added to the network. This is "
         "the delta the task asks for, and the honest answer is that it is small, "
         "concentrated in EEP, and zero in WEP and LEP - because outside EEP nobody's "
         "nearest place to tip a load changes"),
        ("A_lucky_bay_only", "B_bunkers_reopened",
         "What reopening the two inland bunkers would be worth on top of Lucky Bay. Note "
         "the shape: the toll roughly halves while the bill does not move, because the "
         "bunkers sit beside Bunge's own Lock and Kimba sites (see the co-location "
         "table). They add a buyer, not a destination"),
        ("D_pre_2019", "A_lucky_bay_only",
         "Pre-2019 to now, end to end. CONTAMINATED - it mixes the 2019 closures, the "
         "arrival of T-Ports and two different roster-defect sets. Decompose it with the "
         "two rows above rather than quoting it"),
    ]
    deltas = []
    for frm, to, why in LADDER:
        deltas.append({
            "from": frm, "to": to, "why": why,
            "d_m1_bill_aud_per_t": delta(frm, to, "m1_bill_aud_per_t"),
            "d_m4_port_aud_per_t": delta(frm, to, "m4_port_aud_per_t"),
            "d_m2_toll_aud_per_t": delta(frm, to, "m2_toll_aud_per_t"),
        })

    # ------------------------------------------------- sensitivity 1: A5-free routing
    km_of_site_dist = {i: km_vector(s["node"], "dist") for i, s in enumerate(site_info)}
    sens_leastdist = {}
    for skey, sdef in STATES.items():
        idx = [site_key[nm] for nm in sdef["names"]]
        ev = evaluate(km_of_site_dist, idx, site_info, parcels, weights, n)
        srow = summarise(ev, parcels, weights)["EP"]
        sens_leastdist[skey] = {
            "m1_bill_aud_per_t": srow["m1_bill_aud_per_t"],
            "m2_toll_aud_per_t": srow.get("m2_toll_aud_per_t"),
            "m4_port_aud_per_t": srow["m4_port_aud_per_t"],
        }

    # ------------------------------------ sensitivity 2: the Lucky Bay coordinate (A)
    lb = site_info[site_key["Lucky Bay (T-Ports port)"]]
    lb_variants = []
    for d in SWEEP_OFFSET_KM:
        for b in ((None,) if d == 0 else SWEEP_BEARINGS_DEG):
            lon, lat = (lb["lon"], lb["lat"]) if b is None else displace(
                lb["lon"], lb["lat"], d, b)
            nid, err = snap(lon, lat)
            lb_variants.append({"offset_km": d, "bearing_deg": b, "node": nid,
                                "snap_km": round(err, 2), "km": km_vector(nid)})

    idx_a = [site_key[nm] for nm in STATES["A_lucky_bay_only"]["names"]]
    lb_rows = []
    for v in lb_variants:
        r = sweep_eval(evals["A_lucky_bay_only"]["km_inc"], [v["km"]], parcels, weights)
        lb_rows.append({
            "offset_km": v["offset_km"], "bearing_deg": v["bearing_deg"],
            "m2_toll_aud_per_t": r["EP"]["toll"],
            "m1_bill_aud_per_t": r["EP"]["bill"],
            "by_district_toll": {d: r[d]["toll"] for d in DISTRICTS},
        })
    # The fast sweep path must reproduce the full path exactly at zero displacement, or
    # the envelope is measuring a different quantity from the headline it brackets.
    base_lb = [r for r in lb_rows if r["offset_km"] == 0.0][0]
    full_a = summaries["A_lucky_bay_only"]["EP"]
    assert abs(base_lb["m2_toll_aud_per_t"] - full_a["m2_toll_aud_per_t"]) < 0.005, (
        "sweep path disagrees with the full path at offset 0: "
        f"{base_lb['m2_toll_aud_per_t']} vs {full_a['m2_toll_aud_per_t']}")
    assert abs(base_lb["m1_bill_aud_per_t"] - full_a["m1_bill_aud_per_t"]) < 0.005
    print("check: sweep path == full path at zero displacement (M1 and M2)  OK")

    lb_env = {
        "m2_toll_aud_per_t": [min(r["m2_toll_aud_per_t"] for r in lb_rows),
                              max(r["m2_toll_aud_per_t"] for r in lb_rows)],
        "m1_bill_aud_per_t": [min(r["m1_bill_aud_per_t"] for r in lb_rows),
                              max(r["m1_bill_aud_per_t"] for r in lb_rows)],
        "by_district_toll": {
            d: [min(r["by_district_toll"][d] for r in lb_rows),
                max(r["by_district_toll"][d] for r in lb_rows)] for d in DISTRICTS},
    }

    # ------------------------------ sensitivity 3: A11 on Lock and Kimba bunkers (B)
    # Magnitudes AND bearings vary independently here. r8's own A11 sweep locks the two
    # magnitudes together (both sites at the same offset), which is a narrower grid than
    # its method text claims; that is not repeated.
    a11_sites = ("Lock (T-Ports bunker)", "Kimba (T-Ports bunker)")
    a11_variants = {}
    for nm in a11_sites:
        s0 = site_info[site_key[nm]]
        opts = []
        for d in SWEEP_OFFSET_KM:
            for b in ((None,) if d == 0 else SWEEP_BEARINGS_DEG):
                lon, lat = (s0["lon"], s0["lat"]) if b is None else displace(
                    s0["lon"], s0["lat"], d, b)
                nid, _err = snap(lon, lat)
                opts.append({"offset_km": d, "bearing_deg": b, "km": km_vector(nid)})
        a11_variants[nm] = opts

    lb_fixed_km = km_of_site[site_key["Lucky Bay (T-Ports port)"]]
    a11_rows = []
    for ol in a11_variants[a11_sites[0]]:
        for ok in a11_variants[a11_sites[1]]:
            r = sweep_eval(evals["B_bunkers_reopened"]["km_inc"],
                           [lb_fixed_km, ol["km"], ok["km"]], parcels, weights)
            a11_rows.append({
                "lock_offset_km": ol["offset_km"], "lock_bearing_deg": ol["bearing_deg"],
                "kimba_offset_km": ok["offset_km"], "kimba_bearing_deg": ok["bearing_deg"],
                "m2_toll_aud_per_t": r["EP"]["toll"],
                "m1_bill_aud_per_t": r["EP"]["bill"],
                "by_district_toll": {d: r[d]["toll"] for d in DISTRICTS},
            })
    a11_env = {
        "n_configurations": len(a11_rows),
        "m2_toll_aud_per_t": [min(r["m2_toll_aud_per_t"] for r in a11_rows),
                              max(r["m2_toll_aud_per_t"] for r in a11_rows)],
        "m1_bill_aud_per_t": [min(r["m1_bill_aud_per_t"] for r in a11_rows),
                              max(r["m1_bill_aud_per_t"] for r in a11_rows)],
        "by_district_toll": {
            d: [min(r["by_district_toll"][d] for r in a11_rows),
                max(r["by_district_toll"][d] for r in a11_rows)] for d in DISTRICTS},
    }

    # --------------------------------------- sensitivity 4: weighting, ceiling, snap
    flat = [1.0] * n
    weight_sens = {}
    for skey in STATES:
        ev = evals[skey]
        row = {}
        for wname, ww in (("fixed_mean_2022-26_tonnes", weights),
                          ("unweighted_cells", flat)):
            row[wname] = {"m1_bill_aud_per_t": round(wmean(ww, ev["cost_any"]), 2)}
            if ev["has_independent"]:
                toll = [b - a for a, b in zip(ev["cost_inc"], ev["cost_ind"])]
                row[wname]["m2_toll_aud_per_t"] = round(wmean(ww, toll), 2)
        weight_sens[skey] = row

    ceiling = {}
    for skey, ev in evals.items():
        ceiling[skey] = {
            "share_production_independent_haul_over_250km": (
                round(wshare(weights, [k > CEILING_KM for k in ev["km_ind"]]), 4)
                if ev["has_independent"] else None),
            "share_production_nearest_haul_over_250km": round(
                wshare(weights, [k > CEILING_KM for k in ev["km_any"]]), 4),
            "max_independent_haul_km": (round(max(
                k for k in ev["km_ind"] if math.isfinite(k)), 1)
                if ev["has_independent"] else None),
        }

    band_inv = {}
    for skey, ev in evals.items():
        band_inv[skey] = {
            "share_production_where_cheapest_is_not_nearest": round(
                wshare(weights, ev["dollar_choice_differs"]), 4),
            "wmean_aud_per_t_forgone": round(wmean(weights, ev["dollar_choice_gain"]), 3),
            "max_aud_per_t_forgone": round(max(ev["dollar_choice_gain"]), 2),
        }

    snap_stats = {
        "wmean_cell_snap_km": round(wmean(weights, parcel_snap), 2),
        "wshare_cells_snapped_over_2km": round(wshare(weights, [e > 2 for e in parcel_snap]), 4),
        "worst_site_snap_km": round(max(s["snap_km"] for s in site_info), 2),
        "note": SNAP_NOTE,
    }

    # ------------------------------------------- the unresolved return leg, as a bound
    return_bound = {
        "status": "OPEN QUESTION, NOT A PUBLISHED RESULT",
        "note": RETURN_LEG_OPEN,
        "published_one_way": {
            k: summaries[k]["EP"].get("m2_toll_aud_per_t") for k in STATES},
        "upper_bound_if_cost_line_is_one_way_and_return_is_real": {
            k: (None if summaries[k]["EP"].get("m2_toll_aud_per_t") is None
                else round(2 * summaries[k]["EP"]["m2_toll_aud_per_t"], 2))
            for k in STATES},
        "which_is_right": "Unknown from any document in this repo. The published figures "
                          "everywhere else on this page are the one-way ones.",
    }

    # --------------------------------------------------------- who is the nearest ind.
    ind_mix = {}
    for skey, ev in evals.items():
        if not ev["has_independent"]:
            ind_mix[skey] = None
            continue
        names = set(ev["name_ind"])
        ind_mix[skey] = {
            (nm or "none"): round(wshare(weights, [x == nm for x in ev["name_ind"]]), 4)
            for nm in sorted(names, key=lambda x: (x is None, x))
        }

    total_t = sum(weights)
    out = {
        "generated": date.today().isoformat(),
        "tier": "Tier 2 geometry x Tier 1 published rate. No simulation, no fitted "
                "parameter, no calibrated knob.",
        "reproduce": "PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe pipeline/r9_cartage.py",
        "rate": {
            "citation": RATE_CITE,
            "bands_aud_per_tonne_km": [[u, r] for u, r in BANDS],
            "base_year": RATE_BASE_YEAR,
            "application": "one-way loaded kilometres; band selected by the whole "
                           "distance; no cumulative tiering; empty return not added",
            "verify": RATE_VERIFY,
            "marginal_floor": MARGINAL_FLOOR,
            "ceiling_km": CEILING_KM,
            "provenance_is_not_uniform": "ESCOSA footnote 289 traces the <=50 km $0.12 to "
                                         "a public AEGIC document but the 50-250 km $0.11 "
                                         "to unpublished 'AEGIC advice'. Most EP hauls to "
                                         "an independent point fall in the second band, so "
                                         "the weaker-provenance rate carries most of the "
                                         "dollars on this page.",
            "not_ep_specific": "The schedule is South Australia-wide and the case study "
                               "behind it is the upper Central region (Gladstone "
                               "catchment, 16-53 km hauls), not the Eyre Peninsula. No "
                               "EP-specific $/t-km schedule was found. EP arguments cut "
                               "both ways and neither is quantified.",
        },
        "measure": {
            "chosen": MEASURE_CHOICE,
            "definitions": {
                "M1_bill": "tonne-weighted mean cartage to the fewest-kilometre receival "
                           "point of ANY owner, A$/t",
                "M2_toll": "tonne-weighted mean of (cartage to the fewest-kilometre "
                           "INDEPENDENT point minus cartage to the fewest-kilometre "
                           "INCUMBENT point), A$/t. Signed: negative where the "
                           "independent point is the closer of the two",
                "M3_catchment": "tonne share whose toll is <= 0, <= $1, <= $2, <= $5/t",
                "M4_port_run": "tonne-weighted mean cartage to the nearest EXPORT PORT of "
                               "any owner, A$/t",
            },
            "rejected": [{"measure": m, "why": w} for m, w in MEASURE_REJECTED],
            "destination_choice": BAND_INVERSION_NOTE,
            "structural_note_lucky_bay_is_a_port": STRUCTURAL_NOTE,
        },
        "states": {k: {"letter": v["letter"], "label": v["label"],
                       "attributed": v["attributed"], "desc": v["desc"],
                       "n_points": evals[k]["n_points"],
                       "n_independent_points": evals[k]["n_independent"],
                       "n_ports": evals[k]["n_ports"],
                       "sites": sorted(v["names"])}
                   for k, v in STATES.items()},
        "results_by_district": summaries,
        "deltas": deltas,
        "colocation": {"note": COLOCATION_NOTE, "measured": colocation},
        "cross_check_vs_r0": {
            "what": "R0 (pipeline/r8_choice_geometry.py) routes the same journeys on the "
                    "same graph with the same weights and reports them in MINUTES. M1 is "
                    "those journeys priced in KILOMETRES. The implied mean speed is "
                    "printed so an inconsistency between the two scripts would be "
                    "visible. This is a routing check, not a publication of R0's Ladder "
                    "A, which is not quotable (docs/gate_findings.md).",
            "by_state": r0_check,
        },
        "nearest_independent_mix": ind_mix,
        "weighting": {
            "method": "District TOTAL production averaged over every PIRSA season this "
                      "repo holds (2022/23-2025/26), allocated to cells in proportion to "
                      "CLUM cropping_ha within the district (A14). Held FIXED across all "
                      "four states so a network change is not blended with a weather "
                      "change. Identical to pipeline/r8_choice_geometry.parcel_weights.",
            "district_mean_production_t": {k: round(dist_t[k]) for k in sorted(dist_t)},
            "total_t": round(total_t),
            "sensitivity": weight_sens,
        },
        "sensitivities": {
            "least_distance_routing_A5_free": {
                "what": "The primary figures route on least TIME (A5 class speeds) and "
                        "then read the kilometres off that path, as p2_build_matrix.py "
                        "does. This variant routes on least DISTANCE instead and so "
                        "depends on NO assumed speed at all. It is a floor on the "
                        "kilometres and therefore on the dollars.",
                "EP": sens_leastdist,
            },
            "lucky_bay_coordinate": {
                "what": LUCKY_BAY_COORD,
                "offsets_km": list(SWEEP_OFFSET_KM),
                "bearings_deg": list(SWEEP_BEARINGS_DEG),
                "n_configurations": len(lb_rows),
                "state": "A_lucky_bay_only",
                "envelope": lb_env,
                "rows": lb_rows,
            },
            "a11_lock_kimba_coordinates": {
                "what": "A11 gives the Lock and Kimba bunker coordinates a <=5 km "
                        "tolerance (town centroids, exact pads unpublished). They set "
                        "state B's independent side. Both sites are displaced, re-snapped "
                        "and re-routed with a fresh Dijkstra. MAGNITUDES AND BEARINGS BOTH "
                        "VARY INDEPENDENTLY here, so mixed configurations (Lock 5 km, "
                        "Kimba 2.5 km) are evaluated; r8_choice_geometry.py's own A11 "
                        "sweep locks the two magnitudes together and does not.",
                "state": "B_bunkers_reopened",
                "envelope": a11_env,
            },
            "band_inversion": band_inv,
            "250km_ceiling": {
                "what": "The schedule stops at 250 km. Above it, applying $0.11 is an "
                        "EXTRAPOLATION and not a citation (A18). Nothing is clipped; the "
                        "affected share is reported so a reader can discount it.",
                "by_state": ceiling,
            },
            "road_snap": snap_stats,
            "return_leg_bound": return_bound,
        },
        "caveats": {
            "cartage_is_half_the_decision": CARTAGE_IS_HALF,
            "marginal_is_a_floor": MARGINAL_FLOOR,
            "roster": ROSTER_CAVEAT,
            "lucky_bay_coordinate": LUCKY_BAY_COORD,
            "bunker_closure_unsourced": BUNKER_SOURCE_CAVEAT,
            "return_leg": RETURN_LEG_OPEN,
            "base_year": "The rate is 2018-19 A$ and is published here unindexed, on "
                         "A18's recorded decision. Seven years old. This must sit next to "
                         "every figure, not in a footnote.",
        },
        "carried_assumptions": [{"id": a, "note": b} for a, b in CARRIED_ASSUMPTIONS],
    }

    (DOCS / "r9_cartage.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=True), encoding="utf-8")

    write_md(out, summaries, STATES, evals, deltas, lb_env, a11_env, sens_leastdist,
             ind_mix)
    print("\nwrote docs/r9_cartage.md and docs/r9_cartage.json")


# ------------------------------------------------------------------------- markdown
def _m(v, fmt="{:.2f}", none="-"):
    return none if v is None else fmt.format(v)


def write_md(out, summaries, STATES, evals, deltas, lb_env, a11_env, sens_leastdist,
             ind_mix):
    L = []
    a = L.append
    a("# R9 - What the independent gateway is worth to growers, in cartage dollars")
    a("")
    a(f"Generated {out['generated']} by `pipeline/r9_cartage.py`.")
    a("")
    a("**Tier 2 (geometry over road distances and site locations) x Tier 1 (a published "
      "rate schedule). No simulation, no fitted parameter, no calibrated knob. Nothing "
      "here reads `packages/sim/src/calibrated.json`, `engine.ts` or `matrix.json`.**")
    a("")
    a("**Reproduce**")
    a("")
    a("```")
    a(out["reproduce"])
    a(f"{RATE_VERIFY}")
    a("```")
    a("")
    a("---")
    a("")
    a("## Read this first")
    a("")
    a(f"1. **{CARTAGE_IS_HALF}**")
    a("")
    a(f"2. **{MARGINAL_FLOOR}**")
    a("")
    a(f"3. **Base year.** {out['caveats']['base_year']}")
    a("")
    a("---")
    a("")
    a("## The answer, in three lines")
    a("")
    sA = summaries["A_lucky_bay_only"]
    sB = summaries["B_bunkers_reopened"]
    sC = summaries["C_no_independent"]
    d_ca = [d for d in deltas
            if d["from"] == "C_no_independent" and d["to"] == "A_lucky_bay_only"][0]
    a(f"1. **In cartage that growers actually pay, the gateway is worth very little, and "
      f"that is the finding.** Adding the peninsula's one independent receival point to "
      f"the network cuts the tonne-weighted EP cartage bill by "
      f"**${abs(d_ca['d_m1_bill_aud_per_t']['EP']):.2f}/t** "
      f"(${sC['EP']['m1_bill_aud_per_t']:.2f} -> ${sA['EP']['m1_bill_aud_per_t']:.2f}), "
      f"because only **{sA['EP']['m3_share_independent_is_cheapest']*100:.1f} %** of EP "
      f"production has it as the closest place to tip a load. In EEP, where that share is "
      f"{sA['EEP']['m3_share_independent_is_cheapest']*100:.1f} %, the cut is "
      f"${abs(d_ca['d_m1_bill_aud_per_t']['EEP']):.2f}/t. In WEP and LEP it is zero to "
      "the cent.")
    a("")
    a(f"2. **What it is worth is an option, and the option has a price.** To take a load "
      f"to the independent point instead of the nearest Bunge site costs a grower "
      f"**${sA['EP']['m2_toll_aud_per_t']:.2f}/t** on average across EP - "
      f"**${sA['WEP']['m2_toll_aud_per_t']:.2f}/t** in WEP, "
      f"**${sA['EEP']['m2_toll_aud_per_t']:.2f}/t** in EEP, "
      f"**${sA['LEP']['m2_toll_aud_per_t']:.2f}/t** in LEP. That is the price premium the "
      "independent has to beat, per tonne, before the load is worth moving. With the two "
      f"inland bunkers open it is **${sB['EP']['m2_toll_aud_per_t']:.2f}/t** EP-wide "
      f"(WEP ${sB['WEP']['m2_toll_aud_per_t']:.2f}, "
      f"EEP ${sB['EEP']['m2_toll_aud_per_t']:.2f}, "
      f"LEP ${sB['LEP']['m2_toll_aud_per_t']:.2f}). With no independent point at all it "
      "is not a larger number - it is **not a number**, because there is nothing to "
      "deliver to at any premium. **The WEP figure is mostly not a citation**: "
      f"{sA['WEP']['share_over_250km_ceiling']*100:.1f} % of WEP production is further "
      "from Lucky Bay than the published schedule's 250 km ceiling, so above that the "
      "rate is extrapolated. Over the WEP production the schedule can actually price, the "
      f"toll is ${sA['WEP']['m2_toll_within_schedule_aud_per_t']:.2f}/t.")
    a("")
    a(f"3. **Where it does show up is the direct-to-port run.** For a grower carting "
      f"straight to an export port, Lucky Bay takes EEP from "
      f"${sC['EEP']['m4_port_aud_per_t']:.2f}/t to "
      f"${sA['EEP']['m4_port_aud_per_t']:.2f}/t - a "
      f"{sC['EEP']['m4_port_aud_per_t'] - sA['EEP']['m4_port_aud_per_t']:.2f} A$/t "
      "difference, the largest single figure on this page, and the one place where the "
      "gateway changes a real cartage bill rather than an option price.")
    a("")
    a("All figures marginal, one-way loaded, 2018-19 A$, unindexed. **None of them is a "
      "grower benefit**: this project has no price data, and cartage is one side of a "
      "two-sided decision. Read the three notes above before quoting any of it.")
    a("")
    a("---")
    a("")
    a("## The measure, and why")
    a("")
    a(out["measure"]["chosen"])
    a("")
    a("### Definitions")
    a("")
    a("| | Measure | Definition | Defined at |")
    a("|---|---|---|---|")
    a("| **M1** | the bill | cartage to the fewest-kilometre receival point of **any "
      "owner**, A$/t | all four states |")
    a("| **M2** | **the toll (primary)** | cartage to the nearest **independent** point "
      "minus cartage to the nearest **incumbent** point, A$/t | A and B only |")
    a("| **M3** | the catchment | tonne share whose toll is <= $0 / $1 / $2 / $5 per tonne "
      "| A and B only |")
    a("| **M4** | the port run | cartage to the nearest **export port** of any owner, A$/t "
      "| all four states |")
    a("")
    a("### Measures considered and not made the headline")
    a("")
    for r in out["measure"]["rejected"]:
        a(f"- **{r['measure']}** - {r['why']}")
    a("")
    a("### The structural point about Lucky Bay")
    a("")
    a(STRUCTURAL_NOTE)
    a("")
    a("### Choosing the destination")
    a("")
    a(BAND_INVERSION_NOTE)
    a("")
    a("---")
    a("")
    a("## The rate")
    a("")
    a(out["rate"]["citation"])
    a("")
    a(f"Applied as: **{out['rate']['application']}**. Base year **{RATE_BASE_YEAR}**. "
      f"Verified by `{RATE_VERIFY.split('#')[0].strip()}`.")
    a("")
    a(f"- {out['rate']['provenance_is_not_uniform']}")
    a(f"- {out['rate']['not_ep_specific']}")
    a(f"- {RETURN_LEG_OPEN}")
    a("")
    a("---")
    a("")
    a("## The four network states")
    a("")
    a("| | State | Receival points | of which independent | Ports | Attribution |")
    a("|---|---|---|---|---|---|")
    for k, v in STATES.items():
        e = evals[k]
        a(f"| **{v['letter']}** | {v['label']} | {e['n_points']} | "
          f"{e['n_independent']} | {e['n_ports']} | {v['attributed']} |")
    a("")
    a(f"**{BUNKER_SOURCE_CAVEAT}**")
    a("")
    a("### The one structural fact that shapes every table below")
    a("")
    a(out["colocation"]["note"])
    a("")
    a("| T-Ports point | nearest active Bunge site | straight-line km |")
    a("|---|---|---|")
    for k, v in out["colocation"]["measured"].items():
        a(f"| {k} | {v['nearest_active_incumbent_site']} | "
          f"{v['straight_line_km']:.2f} km |")
    a("")
    a("---")
    a("")
    a("## M1 - the bill growers actually pay, A$/t")
    a("")
    a("Tonne-weighted mean marginal cartage to the nearest receival point of any owner. "
      "This is the measure that is defined at **all four** states, including pre-2019 "
      "where R0's ownership ladder is undefined.")
    a("")
    hdr = "| District | " + " | ".join(
        f"{v['letter']}. {v['label']}" for v in STATES.values()) + " |"
    a(hdr)
    a("|---" * (len(STATES) + 1) + "|")
    for d in ("EP",) + DISTRICTS:
        nm = "**EP (all)**" if d == "EP" else f"{d} ({DISTRICT_LONG[d]})"
        cells = " | ".join(
            f"${summaries[k][d]['m1_bill_aud_per_t']:.2f}" for k in STATES)
        a(f"| {nm} | {cells} |")
    a("")
    a("Mean one-way kilometres behind those dollars:")
    a("")
    a(hdr)
    a("|---" * (len(STATES) + 1) + "|")
    for d in ("EP",) + DISTRICTS:
        nm = "**EP (all)**" if d == "EP" else d
        cells = " | ".join(f"{summaries[k][d]['m1_km']:.1f} km" for k in STATES)
        a(f"| {nm} | {cells} |")
    a("")
    a("---")
    a("")
    a("## M2 - the toll: what it costs to use the independent option, A$/t")
    a("")
    a("Cartage to the nearest independent receival point **minus** cartage to the nearest "
      "incumbent one. Equivalently: the price premium, per tonne, the independent has to "
      "beat before the load is worth moving. **Undefined at C and D** - there is no "
      "non-Bunge receival point in either state, so there is no alternative to price at "
      "any premium.")
    a("")
    a("| District | A. Lucky Bay only | B. bunkers reopened | B - A |")
    a("|---|---|---|---|")
    for d in ("EP",) + DISTRICTS:
        nm = "**EP (all)**" if d == "EP" else f"{d} ({DISTRICT_LONG[d]})"
        ta = summaries["A_lucky_bay_only"][d]["m2_toll_aud_per_t"]
        tb = summaries["B_bunkers_reopened"][d]["m2_toll_aud_per_t"]
        a(f"| {nm} | ${ta:.2f} | ${tb:.2f} | {tb - ta:+.2f} |")
    a("")
    a("**How much of that is actually priced by the published schedule.** ESCOSA's "
      "schedule stops at 250 km. Where the haul to the independent point is longer, the "
      "$0.11/t-km applied above the ceiling is an **extrapolation, not a citation** (A18). "
      "The right-hand columns give the toll over the smaller population whose independent "
      "haul is inside the schedule - a different population, not a corrected number.")
    a("")
    a("| District | A: production over the 250 km ceiling | A: toll within the schedule | "
      "B: over the ceiling | B: toll within the schedule |")
    a("|---|---|---|---|---|")
    for d in ("EP",) + DISTRICTS:
        nm = "**EP (all)**" if d == "EP" else d
        ra = summaries["A_lucky_bay_only"][d]
        rb = summaries["B_bunkers_reopened"][d]
        a(f"| {nm} | {ra['share_over_250km_ceiling']*100:.1f} % | "
          f"{_m(ra['m2_toll_within_schedule_aud_per_t'], '${:.2f}')} | "
          f"{rb['share_over_250km_ceiling']*100:.1f} % | "
          f"{_m(rb['m2_toll_within_schedule_aud_per_t'], '${:.2f}')} |")
    a("")
    a("Coordinate envelopes on those tolls (site displaced <=5 km on eight bearings, "
      "re-snapped and re-routed):")
    a("")
    a("| District | A, over the Lucky Bay coordinate | B, over the A11 Lock/Kimba "
      "tolerance |")
    a("|---|---|---|")
    a(f"| **EP (all)** | ${lb_env['m2_toll_aud_per_t'][0]:.2f} - "
      f"${lb_env['m2_toll_aud_per_t'][1]:.2f} | "
      f"${a11_env['m2_toll_aud_per_t'][0]:.2f} - ${a11_env['m2_toll_aud_per_t'][1]:.2f} |")
    for d in DISTRICTS:
        a(f"| {d} | ${lb_env['by_district_toll'][d][0]:.2f} - "
          f"${lb_env['by_district_toll'][d][1]:.2f} | "
          f"${a11_env['by_district_toll'][d][0]:.2f} - "
          f"${a11_env['by_district_toll'][d][1]:.2f} |")
    a("")
    a(f"**{LUCKY_BAY_COORD}**")
    a("")
    a("### The toll's two halves, so a reader can see where it comes from")
    a("")
    a("| District | nearest incumbent, A$/t | nearest independent, A$/t | independent "
      "haul, km | = toll |")
    a("|---|---|---|---|---|")
    for k in ("A_lucky_bay_only", "B_bunkers_reopened"):
        v = STATES[k]
        a(f"| *{v['letter']}. {v['label']}* | | | | |")
        for d in ("EP",) + DISTRICTS:
            r = summaries[k][d]
            nm = "**EP (all)**" if d == "EP" else d
            a(f"| {nm} | ${r['incumbent_aud_per_t']:.2f} | "
              f"${r['independent_level_aud_per_t']:.2f} | "
              f"{r['independent_level_km']:.0f} km | "
              f"${r['m2_toll_aud_per_t']:.2f} |")
    a("")
    a("Which independent point is the nearest one, by tonne share:")
    a("")
    a("| State | mix |")
    a("|---|---|")
    for k, v in STATES.items():
        mix = ind_mix[k]
        txt = ("none - no independent point in this state" if mix is None else
               " - ".join(f"{nm} {sh*100:.1f} %" for nm, sh in
                          sorted(mix.items(), key=lambda kv: -kv[1])))
        a(f"| {v['letter']}. {v['label']} | {txt} |")
    a("")
    a("---")
    a("")
    a("## M3 - the catchment: who would actually use it")
    a("")
    a("Tonne share of district production whose toll falls at or below each level. The "
      "first column is the share for which the independent point is the **closest "
      "receival point of any owner** - the only production for which the gateway changes "
      "the cartage bill at all.")
    a("")
    for k in ("A_lucky_bay_only", "B_bunkers_reopened"):
        v = STATES[k]
        a(f"**{v['letter']}. {v['label']}**")
        a("")
        a("| District | independent is nearest | toll <= $1/t | <= $2/t | <= $5/t |")
        a("|---|---|---|---|---|")
        for d in ("EP",) + DISTRICTS:
            r = summaries[k][d]
            nm = "**EP (all)**" if d == "EP" else d
            a(f"| {nm} | {r['m3_share_independent_is_cheapest']*100:.1f} % | "
              f"{r['m3_share_within']['1']*100:.1f} % | "
              f"{r['m3_share_within']['2']*100:.1f} % | "
              f"{r['m3_share_within']['5']*100:.1f} % |")
        a("")
    a("---")
    a("")
    a("## M4 - the direct-to-port run, A$/t")
    a("")
    a("Cartage to the nearest **export port** of any owner. On EP that is Port Lincoln "
      "and Thevenard (Bunge) at every state, plus Lucky Bay (T-Ports) at A and B. This is "
      "the task's 'nearest export-capable destination' measure made honest: an "
      "export-capable test over *all* receival points excludes nothing, because every "
      "upcountry silo on this roster feeds a port, so it collapses exactly onto M1.")
    a("")
    a(hdr)
    a("|---" * (len(STATES) + 1) + "|")
    for d in ("EP",) + DISTRICTS:
        nm = "**EP (all)**" if d == "EP" else f"{d} ({DISTRICT_LONG[d]})"
        cells = " | ".join(f"${summaries[k][d]['m4_port_aud_per_t']:.2f}" for k in STATES)
        a(f"| {nm} | {cells} |")
    a("")
    a("---")
    a("")
    a("## The deltas between states")
    a("")
    a("Signed A$/t, positive = costs more. Each row is one step of a ladder; the last row "
      "is the end-to-end comparison and is contaminated, as noted.")
    a("")
    for dl in deltas:
        fa, fb = STATES[dl["from"]], STATES[dl["to"]]
        a(f"### {fa['letter']} -> {fb['letter']}: {fa['label']} -> {fb['label']}")
        a("")
        a(f"{dl['why']}.")
        a("")
        a("| District | delta M1 (the bill) | delta M4 (port run) | delta M2 (the toll) |")
        a("|---|---|---|---|")
        for d in ("EP",) + DISTRICTS:
            nm = "**EP (all)**" if d == "EP" else d
            a(f"| {nm} | {_m(dl['d_m1_bill_aud_per_t'][d], '{:+.2f}')} | "
              f"{_m(dl['d_m4_port_aud_per_t'][d], '{:+.2f}')} | "
              f"{_m(dl['d_m2_toll_aud_per_t'][d], '{:+.2f}')} |")
        a("")
    a("---")
    a("")
    a("## Sensitivities")
    a("")
    a("### Routing on least distance instead of least time (depends on no assumed speed)")
    a("")
    a("| State | M1 bill | M2 toll | M4 port run |")
    a("|---|---|---|---|")
    for k, v in STATES.items():
        r = sens_leastdist[k]
        a(f"| {v['letter']}. {v['label']} | ${r['m1_bill_aud_per_t']:.2f} | "
          f"{_m(r['m2_toll_aud_per_t'], '${:.2f}')} | ${r['m4_port_aud_per_t']:.2f} |")
    a("")
    a("### The 250 km ceiling")
    a("")
    a("| State | production whose independent haul exceeds 250 km | longest independent "
      "haul |")
    a("|---|---|---|")
    for k, v in STATES.items():
        c = out["sensitivities"]["250km_ceiling"]["by_state"][k]
        s = c["share_production_independent_haul_over_250km"]
        mx = c["max_independent_haul_km"]
        s_txt = "-" if s is None else f"{s * 100:.1f} %"
        mx_txt = "-" if mx is None else f"{mx:.0f} km"
        a(f"| {v['letter']}. {v['label']} | {s_txt} | {mx_txt} |")
    a("")
    a("Above 250 km the schedule stops. Applying $0.11/t-km there is an extrapolation, not "
      "a citation.")
    a("")
    a("### The band inversion")
    a("")
    a("| State | production where the cheapest point is not the nearest | mean A$/t "
      "forgone | worst cell |")
    a("|---|---|---|---|")
    for k, v in STATES.items():
        b = out["sensitivities"]["band_inversion"][k]
        a(f"| {v['letter']}. {v['label']} | "
          f"{b['share_production_where_cheapest_is_not_nearest']*100:.1f} % | "
          f"${b['wmean_aud_per_t_forgone']:.3f} | ${b['max_aud_per_t_forgone']:.2f} |")
    a("")
    a("### Weighting")
    a("")
    a("| State | M1, tonne-weighted | M1, unweighted cells | M2, tonne-weighted | M2, "
      "unweighted cells |")
    a("|---|---|---|---|---|")
    for k, v in STATES.items():
        w = out["weighting"]["sensitivity"][k]
        f_ = w["fixed_mean_2022-26_tonnes"]
        u_ = w["unweighted_cells"]
        a(f"| {v['letter']}. {v['label']} | ${f_['m1_bill_aud_per_t']:.2f} | "
          f"${u_['m1_bill_aud_per_t']:.2f} | "
          f"{_m(f_.get('m2_toll_aud_per_t'), '${:.2f}')} | "
          f"{_m(u_.get('m2_toll_aud_per_t'), '${:.2f}')} |")
    a("")
    a("### Cross-check against R0")
    a("")
    a(out["cross_check_vs_r0"]["what"])
    a("")
    a("| State | mean minutes to the nearest point of any owner | mean km | implied "
      "mean speed |")
    a("|---|---|---|---|")
    for k, v in STATES.items():
        c = out["cross_check_vs_r0"]["by_state"][k]
        a(f"| {v['letter']}. {v['label']} | "
          f"{c['wmean_minutes_to_nearest_any_owner']:.1f} min | "
          f"{c['wmean_km_to_nearest_any_owner']:.1f} km | "
          f"{c['implied_mean_speed_kmh']:.1f} km/h |")
    a("")
    a("### The road snap")
    a("")
    a(f"Tonne-weighted mean cell snap {out['sensitivities']['road_snap']['wmean_cell_snap_km']:.2f} km; "
      f"{out['sensitivities']['road_snap']['wshare_cells_snapped_over_2km']*100:.1f} % of "
      f"production snaps more than 2 km; worst site snap "
      f"{out['sensitivities']['road_snap']['worst_site_snap_km']:.2f} km.")
    a("")
    a(SNAP_NOTE)
    a("")
    a("### The unresolved return leg")
    a("")
    a(RETURN_LEG_OPEN)
    a("")
    a("| State | published (one-way) toll | upper bound if the return leg is real and not "
      "already in the cost line |")
    a("|---|---|---|")
    rb = out["sensitivities"]["return_leg_bound"]
    for k, v in STATES.items():
        a(f"| {v['letter']}. {v['label']} | "
          f"{_m(rb['published_one_way'][k], '${:.2f}')} | "
          f"{_m(rb['upper_bound_if_cost_line_is_one_way_and_return_is_real'][k], '${:.2f}')} |")
    a("")
    a("The right-hand column is **not a published result**. It is the size of an open "
      "question.")
    a("")
    a("---")
    a("")
    a("## Caveats")
    a("")
    titles = {
        "cartage_is_half_the_decision": "Cartage is half the decision",
        "marginal_is_a_floor": "These are marginal dollars, so they are a floor",
        "roster": "The site roster is known incomplete",
        "lucky_bay_coordinate": "State A rests on one coordinate",
        "bunker_closure_unsourced": "The season labels are attributions, and one is unsourced",
        "return_leg": "The empty return leg is unresolved",
        "base_year": "Base year",
    }
    for k, v in out["caveats"].items():
        a(f"- **{titles.get(k, k)}** - {v}")
    a("")
    a("---")
    a("")
    a("## Carried assumptions")
    a("")
    for c in out["carried_assumptions"]:
        a(f"- **{c['id']}** - {c['note']}")
    a("")
    (DOCS / "r9_cartage.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
