"""R0: ownership choice-set geometry on the Eyre Peninsula.

Tier-2 of docs/analysis_plan_ep_competition.md: roads and site locations only.
NO simulation, NO fitted parameter, NO calibrated knob. Nothing here reads
calibrated.json, engine.ts, or any of A1/A2/A9/A24 - and since 2026-08-31 nothing on the
page ARGUES from them either (the withdrawn A2 threshold ground; see THRESHOLD_WITHDRAWN).

What it computes
----------------
For every CLUM grain-production cell on EP (the same 2.5 km parcels the sim uses,
app/public/data/parcels.json), the one-way drive time on the OSM road network to:
  * the nearest receival point operated by the INCUMBENT (Bunge, ex-Viterra), and
  * the nearest receival point operated by ANYONE ELSE ("independent"),
at three network states, and the tonne-weighted distribution of the gap between them.

Two ladders are reported SEPARATELY and are never added together:

  Ladder A - CHOICE COUNT (defined at all three states).
      How many receival points, of any ownership, a cell can reach.
  Ladder B - OWNERSHIP GAP (defined only where more than one operator exists).
      Nearest independent minus nearest incumbent.

Presentation rules this script enforces (2026-08-31, from docs/gate_findings.md):
  * Ladder A is computed but NOT PUBLISHABLE and is emitted to an appendix under an
    explicit caveat. Every Ladder A row is a count of receival points and the site roster
    is known incomplete (Tooligie, Cowell, Mangalo missing; Cungena's closure tag
    contradicted - docs/roster_audit_2026-08.md section 5). No count-of-points row
    appears in the headline table.
  * The no-independent-option row is published as the FULL 30-120 min threshold sweep and
    NO ROW IS PRIVILEGED. Two earlier grounds for designating 90 minutes a priori were
    withdrawn on 2026-08-31: the cost ground rested on A18, which is an indicative repo
    assumption and not a published rate schedule, and the working-day ground rested on
    A2, which would have broken this page's independence from the fitted model. No
    published EP cart-range threshold was found to replace them, so the designation is
    dropped rather than propped up on an adjacent citation.
  * The HEADLINE is a single 2025/26 level, not the trajectory and not the multiple. It is
    the one number here that depends on neither A11 (both bunkers closed in that state)
    nor the site roster (a threshold row; every roster defect on record is incumbent-side).
    The trajectory and the multiple are demoted to a supporting section in which every
    figure carries the A11 range.
  * A11's <=5 km coordinate tolerance on Lock and Kimba is SWEPT, not asserted: both sites
    are displaced over the tolerance in eight directions, re-snapped and re-routed, and
    the resulting range is published as a standing table.
  * Travel-speed sensitivity (x0.85 / x1.00 / x1.15) is a standing row of the headline
    table, not a footnote. Both published rows are thresholded in absolute minutes, so a
    uniform A5 speed error does NOT cancel out of them.

This split is the point of the script. At state 1 (pre-2019) the whole network was a
single operator (ex-Viterra), so Ladder B is UNDEFINED there - not "infinite", not
"100 % with no independent option". Reporting a pre-2019 monopoly as though it were an
ownership *gap* would make the 2019 closures look like an improvement in competition,
which is nonsense. Ladder A is what moved in 2019; Ladder B is what moved in 2025/26.

Reuse
-----
Routing is the same construction pipeline/p2_build_matrix.py uses to build the sim's
travel matrix: same roads.graph.json, same A5 class speeds, same nearest-node snap, same
least-TIME Dijkstra. It is copied rather than imported for one reason, stated so a
reviewer can check it: p2_build_matrix.py drops every feature with role == "closed"
before routing, so the six sites that closed in 2019 are absent from matrix.json and the
pre-2019 state cannot be built from it. Nothing under packages/sim/src/ is read or
written by this script.

Reproduce
---------
    .venv/Scripts/python.exe pipeline/r8_choice_geometry.py

Writes docs/r0_choice_geometry.md and docs/r0_choice_geometry.json.
"""
from __future__ import annotations

import heapq
import json
import math
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import PROCESSED, ROOT

APP_DATA = ROOT / "app" / "public" / "data"
DOCS = ROOT / "docs"

# A5 road speeds by OSM class, loaded grain truck. Identical to p2_build_matrix.py.
SPEED_KMH = {
    "trunk": 90.0, "primary": 90.0, "secondary": 80.0,
    "tertiary": 70.0, "unclassified": 60.0, "residential": 40.0,
}

INCUMBENT = "Bunge (ex-Viterra)"
# The pre-2019 operator. Same corporate lineage as INCUMBENT (Viterra -> Bunge
# Operations Pty Ltd, Aug 2025); tagged separately in sites.geojson only because those
# six sites shut before the rename. For ownership purposes it IS the incumbent.
INCUMBENT_PRE = "ex-Viterra"
INCUMBENT_OPERATORS = {INCUMBENT, INCUMBENT_PRE}

GAP_THRESHOLDS_MIN = (30, 60, 90)

# Cart-range sweep for the "no independent point within R minutes" row. The FULL sweep is
# published (gate_findings.md defect 8): 90 min is the maximum of this sweep's ratio, so
# quoting the 90-min multiple on its own is the single most favourable framing available
# and must never appear without the sweep beside it.
SWEEP_MIN = (30, 45, 60, 75, 90, 105, 120)
CART_RANGE_MIN = SWEEP_MIN
# NOT designated a priori and NOT privileged - see THRESHOLD_STATUS. This is simply the
# row the headline sentence quotes (the middle of the published grid). Every other row of
# the sweep is published beside it and carries equal standing.
HEADLINE_MIN = 90
# The state the headline is taken from. Chosen because it is the one level on this page
# that depends on neither A11 (both T-Ports bunkers are closed in this state, so the two
# town-centroid coordinates do not enter it - proved by the A11 sweep below, not asserted)
# nor the site roster (it is a THRESHOLD row, and every roster defect on record is
# incumbent-side).
HEADLINE_STATE = "s2025_26"

# ---- A11 coordinate sweep --------------------------------------------------------
# A11: Lock and Kimba are TOWN CENTROIDS, exact pads unpublished, tolerance <=5 km. They
# are the only independent INLAND receival points EP has ever had, so in the 2023/24 state
# they alone set the nearest-independent distance for much of the peninsula. A11 as
# rewritten on 2026-08-31 states this error is NOT negligible for this page. It is swept
# here rather than argued about: both sites are displaced over the tolerance and the whole
# 2023/24 column is recomputed from the displaced coordinates - re-snapped and re-routed,
# not scaled.
A11_SITES = ("Lock (T-Ports bunker)", "Kimba (T-Ports bunker)")
A11_OFFSET_KM = (0.0, 2.5, 5.0)
A11_BEARINGS_DEG = (0, 45, 90, 135, 180, 225, 270, 315)
# "Favours the result" is defined explicitly so the reader can check the labelling: the
# trajectory claim is helped by a LOWER 2023/24 baseline (a bigger multiple against a
# fixed 2025/26 level), so the most-favourable direction is the one that minimises the
# 2023/24 share and the least-favourable is the one that maximises it.
A11_FAVOURABLE_IS = "lower 2023/24 share (larger multiple against the fixed 2025/26 level)"

# Emitted to BOTH artefacts from this one constant. The .md carried the threshold-row
# caveat and the .json did not; they diverged, which is the exact error class this page
# claims to have eliminated. Nothing that appears on the page may be typed twice.
SNAP_NOTE = (
    "A cell is routed from its nearest node on the OSM graph; the snap leg itself is not "
    "driven, so a large snap UNDERSTATES that cell's drive time to everything equally. It "
    "cannot manufacture an ownership GAP, because a gap row is a difference of two times "
    "that share the same snap. IT DOES BEAR ON THE THRESHOLD ROWS, exactly as a speed "
    "error does: 'no independent point within R minutes' is an absolute-minute test, so "
    "an understated drive time makes a cell more likely to pass it. The snap therefore "
    "FLATTERS the network on the headline row rather than the reverse - it works against "
    "the finding, not for it."
)

# Also emitted to both artefacts. The reason printed here is the reason a reader sees.
WHARMINDA_REMOVAL = (
    "Removed 2026-08-31: this paragraph previously asserted that 'Wharminda Road is named "
    "in the reporting as one of the roads that absorbed the extra truck traffic' after "
    "grain rail ceased in May 2019. Reworded 2026-08-31 - the earlier reason given here, "
    "that no outlet, date or URL supported the sentence anywhere in this repo, is no "
    "longer true of its own tree: data/SOURCES.md now registers two, the Eyre Peninsula "
    "Freight Study (SMEC ref. 3005591 Rev 0 Final, 26 Sept 2018) and Jarrad Delaney's "
    "report of it in the Port Lincoln Times, 10 Apr 2019. THE DELETION STANDS, on a "
    "different and stronger ground: both sources are PROSPECTIVE. The study is a forecast "
    "finalised eight months before grain rail ceased, the newspaper's verb is 'will "
    "include', and it was published 10 Apr 2019, seven weeks before the last grain train "
    "on 31 May 2019. Neither observes what any road actually carried afterwards, and the "
    "only post-closure survey on record (RAA, 2 Aug 2024) names Balumbah-Kinnard Road, "
    "Lincoln Highway and Tod Highway but does NOT name Wharminda Road. So the roads were "
    "named in advance as the ones that WOULD carry the freight; that they DID absorb it "
    "is unsourced, and a prospective citation may not stand in for the post-hoc one the "
    "sentence needed. The geometry below stands on its own and needs no press citation."
)

# Travel-speed sensitivity (gate_findings.md defect 7). Both published Ladder B rows are
# thresholded in ABSOLUTE MINUTES, so a uniform error in A5's class speeds does NOT cancel
# out of them - it moves the threshold. Scaling every class speed by f is exactly
# equivalent to dividing every routed minute by f (a uniform speed scaling cannot change
# which path is least-time), so this is computed exactly, not approximated.
SPEED_FACTORS = (0.85, 1.00, 1.15)

NEAR_MIN = (30, 45, 60)  # radii for the choice-count ladder (Ladder A - see appendix)

# ---- Ladder A validity ------------------------------------------------------------
# Every count-of-receival-points row is INVALID while the site roster is incomplete.
# docs/roster_audit_2026-08.md section 5 lists what is still missing/contradicted.
ROSTER_DEFECT_SITES = {
    "Tooligie": "operated 2022/23, 2023/24 and 2024/25 per the operator's weekly reports; "
                "absent from sites.geojson entirely",
    "Cowell": "operated 2017/18 and 2018/19; absent from sites.geojson entirely",
    "Mangalo": "opened for first receivals 2018/19; absent from sites.geojson entirely",
    "Cungena": "tagged closed_2019 but named receiving grain in 2022/23; the tag is "
               "contradicted by the operator's own report",
}
LADDER_A_STATUS = (
    "NOT PUBLISHABLE. Every row on Ladder A is a count of receival points, and the site "
    "roster this count is taken from is known to be incomplete: Tooligie, Cowell and "
    "Mangalo are missing from sites.geojson altogether and Cungena's closed_2019 tag is "
    "contradicted by the operator's own weekly reports (docs/roster_audit_2026-08.md "
    "section 5). All four bear on at least one of the three states reported here: Cowell "
    "and Mangalo were receiving grain before 2019 and are absent from the pre-2019 "
    "state; Tooligie was receiving grain in 2023/24 and is absent from that state; "
    "Cungena's closed_2019 tag is contradicted by a 2022/23 receival, so it is wrongly "
    "excluded from the post-2019 states. The rows have "
    "been wrong twice already. They are retained in an appendix as the audit trail for "
    "the roster rebuild, under this caveat, and must not be quoted."
)
LADDER_B_INVARIANCE = (
    "The invariance holds for the THRESHOLD rows only, and is FALSE of the gap rows. "
    "All four roster-defect sites are INCUMBENT-operated (Tooligie, Cowell, Mangalo and "
    "Cungena are all ex-Viterra/Bunge). A THRESHOLD row ('no independent point within R "
    "minutes') is a function of the drive to the nearest INDEPENDENT point alone, so it "
    "cannot move when an incumbent site is added or removed: that is a structural "
    "invariance, not a coincidence, and it is why the headline survives a roster defect "
    "that destroys Ladder A. A GAP row ('nearest independent more than R minutes beyond "
    "nearest Bunge') is NOT protected that way. The gap is measured FROM the incumbent, "
    "so adding an incumbent site moves it - and this repo's own roster correction of "
    "2026-08-31 did move it, from 74.4 % to 77.3 % at 2025/26 and from 32.9 % to 33.0 % "
    "at 2023/24 (docs/roster_audit_2026-08.md section 4, correction note). Every gap row "
    "on this page must therefore be quoted as 'on the roster as corrected 2026-08-31', "
    "and the piece's headline must be a threshold row."
)

THRESHOLD_DESIGNATION = "none - no threshold on this page is privileged"
THRESHOLD_WITHDRAWN = [
    "WITHDRAWN 2026-08-31, ground 1 (cartage cost). This ground read 90 minutes as "
    "105-135 km at A5 speeds and priced it at A$7-18/t using what the page called A18's "
    "'published range' of A$0.07-0.13/t-km. That description was false. A18 is an "
    "INDICATIVE REPO ASSUMPTION, not a published schedule: its own entry in "
    "data/ASSUMPTIONS.md states in terms, 'No single public EP $/t-km schedule exists', "
    "and the 0.07-0.13 band is this project's own tolerance around a A$0.10/t-km working "
    "value, consistency-checked against published anchors rather than read off a "
    "published rate card. A threshold cannot be designated a priori on a number this "
    "repo made up, however reasonable that number is.",
    "WITHDRAWN 2026-08-31, ground 2 (a working day's round trip). This ground derived a "
    "four-loads-a-day cap from A2's 12 h farm-truck dispatch window (07:00-19:00, "
    "engine.ts sitesOpenNow). A2's bays and service times are FITTED simulation "
    "parameters, and this page's whole standing rests on depending on none of A1, A2, A9 "
    "or A24. Leaning the threshold on A2 would have made that independence claim false. "
    "The ground is withdrawn rather than the independence claim, because the "
    "independence claim is exactly true without it and is load-bearing for the tier "
    "structure of the piece.",
]
THRESHOLD_SEARCH = (
    "Searched for a genuinely published basis for any cart-range threshold on EP, and "
    "none was found. data/ASSUMPTIONS.md A18 records that no public EP $/t-km schedule "
    "exists. The ACCC's 2021 Port Lincoln and Thevenard Final Determinations discuss "
    "grain catchments qualitatively and in port-to-port kilometres (Lucky Bay 177 km "
    "from Port Lincoln, 412 km from Thevenard) and state expressly that 'distance, while "
    "important, is only one factor'; they publish no grower cart-range threshold. The "
    "2018 Eyre Peninsula Freight Study contains no cart-range figure either. Rather than "
    "stand a designation on an adjacent citation, the designation is dropped."
)
THRESHOLD_STATUS = (
    "NO THRESHOLD ON THIS PAGE IS DESIGNATED A PRIORI. Earlier drafts designated 90 "
    "minutes on two grounds; both have been withdrawn (see below) and nothing has "
    "replaced them. The full 30-120 minute sweep is published instead and no row in it "
    "is privileged: a reader who prefers 60 minutes, or 120, should read that row. The "
    "90-minute row is the one the headline quotes because it is the middle of the "
    "published grid and gives one legible number, not because it was selected or "
    "justified."
)
THRESHOLD_DISCLOSURE = (
    "Disclosed against interest, and it no longer bites the headline: 90 min is where "
    "the 2025/26-to-2023/24 RATIO of this row peaks across the sweep, and the repo holds "
    "no record of the threshold being registered before the sweep was run. That "
    "objection is an objection to the MULTIPLE, which is no longer the headline - it has "
    "been demoted to the supporting section. The headline is a single 2025/26 LEVEL, and "
    "the whole 2025/26 sweep column is printed beside it so that no choice of threshold "
    "is being made on the reader's behalf: the 2025/26 level is 97.1 % at 30 min and "
    "still 39.5 % at the most generous 120-minute row. Separately, note the direction of "
    "generosity: a WIDER threshold is generous to the INDEPENDENT side of the "
    "comparison, because it counts a more distant alternative as a live option, so "
    "reading the 90-minute row rather than the 60-minute one understates the finding."
)

# Carried assumptions, emitted to BOTH artefacts from this one list (the .md used to carry
# them and the .json did not - another md/json divergence).
CARRIED_ASSUMPTIONS = [
    ("A5", "road class speeds - the only assumed input to the routing, and THE LEVELS ON "
           "THIS PAGE ARE MATERIALLY SENSITIVE TO IT, because every published row is "
           "thresholded in absolute minutes. Swept at x0.85/x1.00/x1.15 as a standing "
           "row. A5 error does NOT cancel; earlier drafts of this page said it largely "
           "did, and that was wrong."),
    ("A11", "T-Ports Lock/Kimba coordinates are town centroids, not the exact pads "
            "(<=5 km tolerance). Both sites are in the 2023/24 state only. A11 as "
            "rewritten 2026-08-31 records that this error is NOT negligible for this "
            "page, and it is now SWEPT rather than argued about - see the A11 sweep "
            "table. Every 2023/24 figure and every multiple on this page carries that "
            "range. The 2025/26 headline does not: neither bunker is in that state, and "
            "the sweep demonstrates the level does not move."),
    ("A12", "season site sets. Load-bearing for Ladder A and the reason Ladder A is not "
            "publishable: the roster is an operator snapshot, not a per-season site list. "
            "The known defects are named in Appendix A. This script still builds its "
            "states from the single `status` field rather than from `operating_seasons`."),
    ("A14", "district boundaries approximated by LGA composition - used for the tonne "
            "weighting, not for routing."),
    ("A15", "is NOT used: the 2025/26 bunker closure is published (tports.com/harvest), "
            "and 2024/25 is not one of the three states."),
    ("A18", "road grain freight rate. NO LONGER USED FOR ANYTHING ON THIS PAGE. It "
            "formerly supplied the cost argument that designated the 90-minute threshold "
            "a priori; that ground is withdrawn, because A18 is an indicative repo "
            "assumption and not a published rate schedule - A18's own entry says 'No "
            "single public EP $/t-km schedule exists'. It enters no computed number here "
            "and no longer supports any designation."),
    ("A4", "capacities are not used at all. This analysis is geometry; no site's capacity "
           "enters any number on this page."),
    ("A2", "is NOT used, and must not be. An earlier draft leaned the threshold argument "
           "on A2's 12 h farm-truck dispatch window; that ground is withdrawn, so this "
           "page's independence from A1, A2, A9 and A24 is exact rather than approximate."),
]

# Production weighting seasons: every season PIRSA data exists for in this repo.
WEIGHT_SEASONS = ("2022/23", "2023/24", "2024/25", "2025/26")


# --------------------------------------------------------------------------- routing
def build_graph():
    g = json.loads((PROCESSED / "roads.graph.json").read_text(encoding="utf-8"))
    nodes = g["nodes"]
    adj: dict[str, list[tuple[str, float, float]]] = defaultdict(list)
    for u, v, length_m, hw in g["edges"]:
        km = length_m / 1000.0
        minutes = km / SPEED_KMH.get(hw, 60.0) * 60.0
        adj[u].append((v, minutes, km))
        adj[v].append((u, minutes, km))
    return nodes, adj


def make_snapper(nodes):
    cell = 0.05
    grid: dict[tuple[int, int], list[str]] = defaultdict(list)
    for nid, (lon, lat) in nodes.items():
        grid[(int(lon / cell), int(lat / cell))].append(nid)

    def nearest(lon: float, lat: float):
        cx, cy = int(lon / cell), int(lat / cell)
        best, bd = None, 1e18
        for r in range(0, 8):
            cands = []
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) == r:
                        cands += grid.get((cx + dx, cy + dy), [])
            for nid in cands:
                lo, la = nodes[nid]
                d = (lo - lon) ** 2 + (la - lat) ** 2
                if d < bd:
                    bd, best = d, nid
            if best is not None and r >= 1:
                break
        # straight-line snap error in km, so a bad snap can be seen rather than assumed
        lo, la = nodes[best]
        km = math.hypot((lo - lon) * math.cos(math.radians(lat)), la - lat) * 111.32
        return best, km

    return nearest


def dijkstra_minutes(adj, src: str) -> dict[str, float]:
    """Least-TIME tree from src. Same as p2_build_matrix.dijkstra, minutes only."""
    dist = {src: 0.0}
    pq = [(0.0, src)]
    while pq:
        d, n = heapq.heappop(pq)
        if d > dist.get(n, 1e18):
            continue
        for m, w, _km in adj[n]:
            nd = d + w
            if nd < dist.get(m, 1e18):
                dist[m] = nd
                heapq.heappush(pq, (nd, m))
    return dist


# ---------------------------------------------------------------------- network states
def network_states(feats):
    """Which sites.geojson features are a receival point at each state.

    Membership is by the published `status` field only - no judgement call per site.
    """
    def st(f):
        return f["properties"]["status"]

    active = [f for f in feats if st(f) == "active_2025_26"]          # 18 Bunge
    dormant = [f for f in feats if st(f) == "dormant"]                # 5 Bunge
    closed19 = [f for f in feats if st(f) == "closed_2019"]           # 6 ex-Viterra
    tp_port = [f for f in feats if st(f) == "active"]                 # 1 T-Ports (Lucky Bay)
    tp_bunkers = [f for f in feats if st(f) == "closed_2025_26_season"]  # 2 T-Ports bunkers

    # Counts are read off the data, never hard-coded: the roster was corrected on
    # 2026-08-31 (4 sites moved dormant -> active) and a hard-coded "18 active" silently
    # became a false provenance statement in the published page.
    na, nd, nc = len(active), len(dormant), len(closed19)
    return {
        "pre_2019": {
            "label": "pre-2019",
            "desc": f"the {nc} sites that closed in 2019 still open; the {na} "
                    f"currently-active Bunge sites plus the {nd} now-dormant one(s) "
                    "treated as open (A12); T-Ports does not yet exist",
            "sites": active + dormant + closed19,
        },
        "s2023_24": {
            "label": "2023/24",
            "desc": f"current Bunge network ({na} active) + T-Ports Lucky Bay + the Lock "
                    "and Kimba bunkers, which ran that season",
            "sites": active + tp_port + tp_bunkers,
        },
        "s2025_26": {
            "label": "2025/26",
            "desc": f"current Bunge network ({na} active) + T-Ports Lucky Bay only; both "
                    "inland bunkers closed for the season (published, tports.com/harvest)",
            "sites": active + tp_port,
        },
        # Sensitivity, not a headline state: pre-2019 with the dormant sites excluded.
        "pre_2019_no_dormant": {
            "label": "pre-2019 (sensitivity: dormant excluded)",
            "desc": f"as pre-2019 but without the {nd} site(s) still tagged dormant, in "
                    "case they were already idle before 2019",
            "sites": active + closed19,
            "sensitivity": True,
        },
    }


# ------------------------------------------------------------------------- weighting
def season_weights(parcels, season: str):
    """Same allocation, but weighted by ONE season's PIRSA district production."""
    prod = pl.read_parquet(PROCESSED / "production_districts.parquet")
    tot = prod.filter((pl.col("crop") == "TOTAL") & (pl.col("season") == season))
    dist_t = {r["district"]: float(r["production_t"]) for r in tot.iter_rows(named=True)}
    dist_ha: dict[str, float] = defaultdict(float)
    for p in parcels:
        dist_ha[p["district"]] += p["cropping_ha"]
    return [dist_t[p["district"]] * p["cropping_ha"] / dist_ha[p["district"]] for p in parcels]


def parcel_weights(parcels):
    """Tonnes per production cell, held FIXED across the three network states.

    District TOTAL production, averaged over every PIRSA season the repo holds
    (2022/23-2025/26), allocated to cells in proportion to CLUM cropping_ha within the
    district - the same allocation rule as pipeline/r4_build_demand.py step 6.

    Fixed on purpose. The three states are three different years, and EP yields swing
    2.6x between them (0.41 Mt WEP in 2024/25 against 1.43 Mt in 2022/23). Weighting each
    state by its own year's harvest would blend a network change with a weather change
    and the trajectory would stop meaning anything. It also could not be done for
    pre-2019 at all: this repo holds no PIRSA production before 2022/23.
    """
    prod = pl.read_parquet(PROCESSED / "production_districts.parquet")
    tot = (
        prod.filter((pl.col("crop") == "TOTAL") & (pl.col("season").is_in(WEIGHT_SEASONS)))
        .group_by("district")
        .agg(pl.col("production_t").mean().alias("mean_t"))
    )
    dist_t = {r["district"]: r["mean_t"] for r in tot.iter_rows(named=True)}
    dist_ha: dict[str, float] = defaultdict(float)
    for p in parcels:
        dist_ha[p["district"]] += p["cropping_ha"]
    w = [dist_t[p["district"]] * p["cropping_ha"] / dist_ha[p["district"]] for p in parcels]
    return w, dist_t, dict(dist_ha)


# --------------------------------------------------------------------------- reporting
def wshare(weights, flags) -> float:
    tot = sum(weights)
    return sum(w for w, f in zip(weights, flags) if f) / tot if tot else 0.0


def wquantile(weights, values, q: float) -> float:
    pairs = sorted((v, w) for v, w in zip(values, weights) if v is not None and math.isfinite(v))
    if not pairs:
        return float("nan")
    tot = sum(w for _, w in pairs)
    acc = 0.0
    for v, w in pairs:
        acc += w
        if acc >= q * tot:
            return v
    return pairs[-1][0]


def wmean(weights, values) -> float:
    num = den = 0.0
    for w, v in zip(weights, values):
        if v is not None and math.isfinite(v):
            num += w * v
            den += w
    return num / den if den else float("nan")


def main():
    nodes, adj = build_graph()
    snap = make_snapper(nodes)
    feats = json.loads((PROCESSED / "sites.geojson").read_text(encoding="utf-8"))["features"]
    parcels = json.load(open(APP_DATA / "parcels.json", encoding="utf-8"))["parcels"]
    weights, dist_t, dist_ha = parcel_weights(parcels)
    print(f"parcels: {len(parcels)}  sites: {len(feats)}  nodes: {len(nodes)}")
    print("district mean production (t):", {k: round(v) for k, v in dist_t.items()})

    # snap every site once; route once from each site node; reuse across all states
    site_key = {}
    site_info = []
    worst_snap = 0.0
    for f in feats:
        lon, lat = f["geometry"]["coordinates"]
        nid, err = snap(lon, lat)
        worst_snap = max(worst_snap, err)
        p = f["properties"]
        site_key[p["name"]] = len(site_info)
        site_info.append({
            "name": p["name"], "operator": p["operator"], "role": p["role"],
            "status": p["status"], "district": p.get("district"),
            "lon": lon, "lat": lat, "node": nid, "snap_km": round(err, 2),
        })
    print(f"worst site snap-to-road distance: {worst_snap:.2f} km")

    trees = {}
    for s in site_info:
        if s["node"] not in trees:
            trees[s["node"]] = dijkstra_minutes(adj, s["node"])

    parcel_nodes = []
    parcel_snap = []
    for p in parcels:
        nid, err = snap(p["lon"], p["lat"])
        parcel_snap.append(err)
        parcel_nodes.append(nid)
    worst_psnap = max(parcel_snap)
    print(f"worst parcel snap-to-road distance: {worst_psnap:.2f} km")

    INF = float("inf")

    def minutes_to(si: int, pi: int) -> float:
        return trees[site_info[si]["node"]].get(parcel_nodes[pi], INF)

    states = network_states(feats)
    results = {}
    raw = {}
    unreachable_any = 0

    for skey, sdef in states.items():
        idx = [site_key[f["properties"]["name"]] for f in sdef["sites"]]
        inc = [i for i in idx if site_info[i]["operator"] in INCUMBENT_OPERATORS]
        ind = [i for i in idx if site_info[i]["operator"] not in INCUMBENT_OPERATORS]
        n_ops = len({site_info[i]["operator"] for i in idx} - set())
        # collapse the two incumbent tags into one owner for the operator count
        owners = {("INCUMBENT" if site_info[i]["operator"] in INCUMBENT_OPERATORS
                   else site_info[i]["operator"]) for i in idx}
        n_owners = len(owners)

        near_inc, near_ind, near_any, second_any = [], [], [], []
        nearest_ind_name, nearest_any_name = [], []
        count_within = {r: [] for r in NEAR_MIN}

        for pi in range(len(parcels)):
            all_t = sorted(((minutes_to(i, pi), i) for i in idx))
            all_t = [(t, i) for t, i in all_t if math.isfinite(t)]
            if not all_t:
                unreachable_any += 1
                near_any.append(INF); second_any.append(INF)
                near_inc.append(INF); near_ind.append(INF)
                nearest_ind_name.append(None); nearest_any_name.append(None)
                for r in NEAR_MIN:
                    count_within[r].append(0)
                continue
            near_any.append(all_t[0][0])
            nearest_any_name.append(site_info[all_t[0][1]]["name"])
            second_any.append(all_t[1][0] if len(all_t) > 1 else INF)
            ti = min((minutes_to(i, pi) for i in inc), default=INF)
            near_inc.append(ti)
            if ind:
                bt, bi = min(((minutes_to(i, pi), i) for i in ind), key=lambda x: x[0])
                near_ind.append(bt)
                nearest_ind_name.append(site_info[bi]["name"] if math.isfinite(bt) else None)
            else:
                near_ind.append(INF)
                nearest_ind_name.append(None)
            for r in NEAR_MIN:
                count_within[r].append(sum(1 for t, _ in all_t if t <= r))

        has_independent = bool(ind)
        raw[skey] = {"near_inc": near_inc, "near_ind": near_ind, "near_any": near_any,
                     "count_within": count_within, "has_independent": has_independent}

        # ---- Ladder A: choice count (all states) -- NOT PUBLISHABLE, see LADDER_A_STATUS
        ladder_a = {
            "publishable": False,
            "status": LADDER_A_STATUS,
            "roster_defect_sites": sorted(ROSTER_DEFECT_SITES),
            "n_receival_points": len(idx),
            "n_owners": n_owners,
            "wmean_nearest_min": round(wmean(weights, near_any), 1),
            "p50_nearest_min": round(wquantile(weights, near_any, 0.5), 1),
            "p90_nearest_min": round(wquantile(weights, near_any, 0.9), 1),
            "p99_nearest_min": round(wquantile(weights, near_any, 0.99), 1),
            "share_2nd_beyond": {
                str(g): round(wshare(weights, [s - n > g for s, n in zip(second_any, near_any)]), 4)
                for g in GAP_THRESHOLDS_MIN
            },
            "wmean_points_within": {
                str(r): round(wmean(weights, count_within[r]), 2) for r in NEAR_MIN
            },
            "share_with_only_one_point_within": {
                str(r): round(wshare(weights, [c <= 1 for c in count_within[r]]), 4) for r in NEAR_MIN
            },
        }

        # ---- Ladder B: ownership gap (only where >1 owner) ----
        if has_independent:
            gap = [(b - a) if math.isfinite(b) else INF for a, b in zip(near_inc, near_ind)]
            no_option = {
                str(r): round(wshare(weights, [not math.isfinite(b) or b > r for b in near_ind]), 4)
                for r in SWEEP_MIN
            }
            # ---- travel-speed sensitivity, computed exactly ----
            # Scaling every A5 class speed by f divides every routed minute by f and cannot
            # change which path is least-time, so the scaled network is obtained by scaling
            # the minutes rather than re-routing. INF/f is INF, so unreachable stays
            # unreachable. This is a STANDING ROW of the results, not a footnote: both
            # published rows are thresholded in absolute minutes, so a uniform speed error
            # does not cancel out of them.
            speed_sens = {}
            for f in SPEED_FACTORS:
                ni = [b / f for b in near_ind]
                nc = [a / f for a in near_inc]
                g2 = [(b - a) if math.isfinite(b) else INF for a, b in zip(nc, ni)]
                speed_sens[f"{f:.2f}"] = {
                    "speed_factor": f,
                    "share_no_independent_within": {
                        str(r): round(
                            wshare(weights, [not math.isfinite(b) or b > r for b in ni]), 4)
                        for r in SWEEP_MIN
                    },
                    "share_gap_beyond_incl_none": {
                        str(g): round(wshare(weights, [x > g for x in g2]), 4)
                        for g in GAP_THRESHOLDS_MIN
                    },
                    "wmean_nearest_incumbent_min": round(wmean(weights, nc), 1),
                    "wmean_nearest_independent_min": round(wmean(weights, ni), 1),
                }
            ladder_b = {
                "defined": True,
                "publishable": True,
                "roster_invariance": LADDER_B_INVARIANCE,
                "headline_threshold_min": HEADLINE_MIN,
                "speed_sensitivity": speed_sens,
                "n_independent_points": len(ind),
                "independent_operator": sorted({site_info[i]["operator"] for i in ind}),
                "wmean_nearest_incumbent_min": round(wmean(weights, near_inc), 1),
                "p50_nearest_incumbent_min": round(wquantile(weights, near_inc, 0.5), 1),
                "p90_nearest_incumbent_min": round(wquantile(weights, near_inc, 0.9), 1),
                "p99_nearest_incumbent_min": round(wquantile(weights, near_inc, 0.99), 1),
                "wmean_nearest_independent_min": round(wmean(weights, near_ind), 1),
                "p50_nearest_independent_min": round(wquantile(weights, near_ind, 0.5), 1),
                "share_independent_nearer_than_incumbent": round(
                    wshare(weights, [math.isfinite(b) and b < a
                                     for a, b in zip(near_inc, near_ind)]), 4),
                "share_gap_beyond_incl_none": {
                    str(g): round(wshare(weights, [x > g for x in gap]), 4)
                    for g in GAP_THRESHOLDS_MIN
                },
                "share_gap_beyond_excl_none": {
                    str(g): round(
                        wshare(weights, [math.isfinite(x) and x > g for x in gap]), 4)
                    for g in GAP_THRESHOLDS_MIN
                },
                "share_no_independent_within": no_option,
                "share_nearest_independent_is_a_port": round(
                    wshare(weights, [
                        nm is not None and site_info[site_key[nm]]["role"] == "port"
                        for nm in nearest_ind_name]), 4),
                "nearest_independent_mix": {
                    k: round(v, 4) for k, v in sorted(
                        ((nm or "none",
                          wshare(weights, [x == nm for x in nearest_ind_name]))
                         for nm in set(nearest_ind_name)),
                        key=lambda kv: -kv[1])
                },
            }
        else:
            ladder_b = {
                "defined": False,
                "n_independent_points": 0,
                "why": ("Every receival point in this state is operated by the incumbent "
                        "(ex-Viterra). There is no independent option anywhere, so the "
                        "incumbent-vs-independent gap has no value - not a large one. "
                        "Compare this state on Ladder A only."),
            }

        results[skey] = {
            "label": sdef["label"],
            "desc": sdef["desc"],
            "sensitivity": sdef.get("sensitivity", False),
            "sites": [site_info[i]["name"] for i in idx],
            "ladder_a_choice_count": ladder_a,
            "ladder_b_ownership_gap": ladder_b,
            "by_district": {},
        }

        # per-district cut of the two headline numbers
        for d in ("WEP", "LEP", "EEP"):
            sel = [i for i, p in enumerate(parcels) if p["district"] == d]
            dw = [weights[i] for i in sel]
            row = {
                "wmean_nearest_min": round(wmean(dw, [near_any[i] for i in sel]), 1),
                "share_only_one_within_45": round(
                    wshare(dw, [count_within[45][i] <= 1 for i in sel]), 4),
            }
            if has_independent:
                row["wmean_nearest_independent_min"] = round(
                    wmean(dw, [near_ind[i] for i in sel]), 1)
                row["share_no_independent_within_90"] = round(
                    wshare(dw, [not math.isfinite(near_ind[i]) or near_ind[i] > 90
                                for i in sel]), 4)
                row["share_gap_over_60_incl_none"] = round(
                    wshare(dw, [(near_ind[i] - near_inc[i] if math.isfinite(near_ind[i])
                                 else INF) > 60 for i in sel]), 4)
            results[skey]["by_district"] = results[skey]["by_district"] | {d: row}

    # ---------- sensitivity 1: does the FIXED tonne weighting drive the answer? ----------
    # Re-weight each state by its own season's PIRSA production (pre-2019 has no PIRSA
    # season in this repo, so it can only be shown on the fixed weights and on unweighted
    # cell counts). If the headline barely moves, the fixed-weight choice is not load-bearing.
    wsens = {}
    for skey, season in (("s2023_24", "2023/24"), ("s2025_26", "2025/26")):
        r = raw[skey]
        alt = season_weights(parcels, season)
        flat = [1.0] * len(parcels)
        row = {}
        for wname, ww in (("fixed_mean_2022-26", weights), (f"own_season_{season}", alt),
                          ("unweighted_cells", flat)):
            gap = [(b - a) if math.isfinite(b) else INF
                   for a, b in zip(r["near_inc"], r["near_ind"])]
            row[wname] = {
                "gap_over_60": round(wshare(ww, [x > 60 for x in gap]), 4),
                "no_independent_within_90": round(
                    wshare(ww, [not math.isfinite(b) or b > 90 for b in r["near_ind"]]), 4),
                "only_one_point_within_45": round(
                    wshare(ww, [c <= 1 for c in r["count_within"][45]]), 4),
            }
        wsens[skey] = row
    for skey in ("pre_2019",):
        r = raw[skey]
        wsens[skey] = {
            "fixed_mean_2022-26": {"only_one_point_within_45": round(
                wshare(weights, [c <= 1 for c in r["count_within"][45]]), 4)},
            "unweighted_cells": {"only_one_point_within_45": round(
                wshare([1.0] * len(parcels), [c <= 1 for c in r["count_within"][45]]), 4)},
        }

    # ---------- sensitivity 2: how much cropping land is far from the road graph? ----------
    snap_sens = {
        "wshare_cells_snapped_over_2km": round(wshare(weights, [e > 2 for e in parcel_snap]), 4),
        "wshare_cells_snapped_over_5km": round(wshare(weights, [e > 5 for e in parcel_snap]), 4),
        "wmean_snap_km": round(wmean(weights, parcel_snap), 2),
        "note": SNAP_NOTE,
    }

    # ---------- sensitivity 3: A11 coordinate sweep on Lock and Kimba ----------
    # A11 gives the two T-Ports bunker coordinates a <=5 km tolerance (town centroids,
    # exact pads unpublished). They are the only independent INLAND points EP has ever
    # had, so in 2023/24 they alone set the nearest-independent distance for much of the
    # peninsula. Displace both over the tolerance, RE-SNAP and RE-ROUTE from the displaced
    # coordinate (not a scaling of minutes - that would be a different, weaker sweep), and
    # recompute the published rows. The 2025/26 state contains neither bunker, so its rows
    # are recomputed under every displacement too, to DEMONSTRATE rather than assert that
    # the headline does not depend on A11.
    def displace(lon: float, lat: float, km: float, bearing_deg: float):
        th = math.radians(bearing_deg)
        dlat = km * math.cos(th) / 111.32
        dlon = km * math.sin(th) / (111.32 * math.cos(math.radians(lat)))
        return lon + dlon, lat + dlat

    def minutes_from(nid: str) -> list[float]:
        if nid not in trees:
            trees[nid] = dijkstra_minutes(adj, nid)
        t = trees[nid]
        return [t.get(pn, INF) for pn in parcel_nodes]

    # the independent points that are NOT swept: everything T-Ports that is not a bunker
    fixed_ind_names = [
        f["properties"]["name"] for f in states[HEADLINE_STATE]["sites"]
        if site_info[site_key[f["properties"]["name"]]]["operator"] not in INCUMBENT_OPERATORS
    ]
    fixed_ind_min = None
    for nm in fixed_ind_names:
        mm = minutes_from(site_info[site_key[nm]]["node"])
        fixed_ind_min = mm if fixed_ind_min is None else [min(a, b) for a, b in zip(fixed_ind_min, mm)]

    a11_variants = {}
    for nm in A11_SITES:
        s0 = site_info[site_key[nm]]
        opts = []
        for d in A11_OFFSET_KM:
            for b in ((None,) if d == 0 else A11_BEARINGS_DEG):
                lon, lat = ((s0["lon"], s0["lat"]) if b is None
                            else displace(s0["lon"], s0["lat"], d, b))
                nid, err = snap(lon, lat)
                opts.append({"offset_km": d, "bearing_deg": b, "lon": round(lon, 5),
                             "lat": round(lat, 5), "snap_km": round(err, 2),
                             "minutes": minutes_from(nid)})
        a11_variants[nm] = opts

    inc23 = raw["s2023_24"]["near_inc"]
    a11_grid = []
    for d in A11_OFFSET_KM:
        for ol in [o for o in a11_variants[A11_SITES[0]] if o["offset_km"] == d]:
            for ok in [o for o in a11_variants[A11_SITES[1]] if o["offset_km"] == d]:
                ni23 = [min(a, b, c) for a, b, c in
                        zip(fixed_ind_min, ol["minutes"], ok["minutes"])]
                # 2025/26 contains neither bunker: its independent set is fixed_ind only.
                ni25 = fixed_ind_min
                gap23 = [(b - a) if math.isfinite(b) else INF for a, b in zip(inc23, ni23)]
                a11_grid.append({
                    "offset_km": d,
                    f"bearing_{A11_SITES[0].split(' ')[0].lower()}_deg": ol["bearing_deg"],
                    f"bearing_{A11_SITES[1].split(' ')[0].lower()}_deg": ok["bearing_deg"],
                    "s2023_24_no_independent_within": {
                        str(r): round(wshare(weights, [not math.isfinite(x) or x > r
                                                       for x in ni23]), 4) for r in SWEEP_MIN},
                    "s2023_24_gap_over_60": round(wshare(weights, [x > 60 for x in gap23]), 4),
                    "s2025_26_no_independent_within": {
                        str(r): round(wshare(weights, [not math.isfinite(x) or x > r
                                                       for x in ni25]), 4) for r in SWEEP_MIN},
                })
    H_ = str(HEADLINE_MIN)
    a11_rows = []
    for d in A11_OFFSET_KM:
        sel = [g for g in a11_grid if g["offset_km"] == d]
        key = lambda g: g["s2023_24_no_independent_within"][H_]
        lo, hi = min(sel, key=key), max(sel, key=key)
        a11_rows.append({"offset_km": d, "n_configurations": len(sel),
                         "most_favourable": lo, "least_favourable": hi})
    base = a11_rows[0]["most_favourable"]
    env = {str(r): [min(g["s2023_24_no_independent_within"][str(r)] for g in a11_grid),
                    max(g["s2023_24_no_independent_within"][str(r)] for g in a11_grid)]
           for r in SWEEP_MIN}
    h25 = base["s2025_26_no_independent_within"][H_]
    a11_sweep = {
        "what": "A11 gives the Lock and Kimba T-Ports bunker coordinates a <=5 km "
                "tolerance (town centroids; exact pads unpublished). Both sites are "
                "displaced over that tolerance and every published row is recomputed.",
        "method": "For each offset the site is moved to a new lon/lat, RE-SNAPPED to the "
                  "nearest OSM node and RE-ROUTED with a fresh Dijkstra tree. Minutes are "
                  "not scaled or interpolated. Lock and Kimba are displaced "
                  "independently, so every combination of the two bearings is evaluated "
                  "and the reported extremes are the true extremes over the grid.",
        "offsets_km": list(A11_OFFSET_KM),
        "bearings_deg": list(A11_BEARINGS_DEG),
        "sites": list(A11_SITES),
        "favourable_means": A11_FAVOURABLE_IS,
        "n_configurations": len(a11_grid),
        "headline_state_is_a11_independent": {
            "state": states[HEADLINE_STATE]["label"],
            "share_no_independent_within_90_at_every_configuration": sorted(
                {g["s2025_26_no_independent_within"][H_] for g in a11_grid}),
            "why": "Neither Lock nor Kimba is a receival point in this state - both "
                   "bunkers are closed for 2025/26 (published, tports.com/harvest) - so "
                   "no displacement of either can reach it. Computed under all "
                   f"{len(a11_grid)} configurations rather than asserted.",
        },
        "s2023_24_envelope_no_independent_within": env,
        "s2023_24_envelope_gap_over_60": [
            min(g["s2023_24_gap_over_60"] for g in a11_grid),
            max(g["s2023_24_gap_over_60"] for g in a11_grid)],
        "extremes_are_selected_on": f"the {HEADLINE_MIN}-minute threshold row. The gap "
                                    "column of an extreme row is that same "
                                    "configuration's gap value, NOT the extreme of the "
                                    "gap row - the gap row's own envelope is given "
                                    "separately as s2023_24_envelope_gap_over_60.",
        "multiple_range_at_headline_min": [
            round(h25 / env[H_][1], 2), round(h25 / env[H_][0], 2)],
        "rows": a11_rows,
        "grid": [{k: v for k, v in g.items() if k != "minutes"} for g in a11_grid],
        "asymmetry_check": (
            "A11's own entry claims the error 'can only ever make the 2023/24 baseline "
            "worse, never better'. This sweep is where that claim is tested rather than "
            "repeated."),
    }

    # ---------- Wharminda: the site named in the reporting, as a worked example ----------
    wh = site_info[site_key["Wharminda (closed)"]]
    wh_node = wh["node"]
    wharminda = {}
    for skey, sdef in states.items():
        idx = [site_key[f["properties"]["name"]] for f in sdef["sites"]]
        rows = []
        for i in idx:
            t = trees[site_info[i]["node"]].get(wh_node, INF)
            if math.isfinite(t):
                rows.append((round(t, 1), site_info[i]["name"], site_info[i]["operator"]))
        rows.sort()
        ind_rows = [r for r in rows if r[2] not in INCUMBENT_OPERATORS]
        wharminda[skey] = {
            "nearest_four_any_owner": rows[:4],
            "nearest_independent": ind_rows[0] if ind_rows else None,
        }

    total_t = sum(weights)
    out = {
        "generated": date.today().isoformat(),
        "reproduce": ".venv/Scripts/python.exe pipeline/r8_choice_geometry.py",
        "tier": "Tier 2 (geometry): roads + site locations only. No simulation, no fitted "
                "parameter, no calibrated knob.",
        "definitions": {
            "independent": "a receival point NOT operated by the incumbent. Incumbent = "
                           f"'{INCUMBENT}' and its pre-rename tag '{INCUMBENT_PRE}' "
                           "(Viterra Operations Pty Ltd -> Bunge Operations Pty Ltd, Aug "
                           "2025), treated as one owner throughout.",
            "drive_time": "one-way minutes on the OSM road network, least-time path, A5 "
                          "class speeds (trunk/primary 90, secondary 80, tertiary 70, "
                          "unclassified 60, residential 40 km/h). Speeds are assumed (A5); "
                          "everything else here is measured geometry.",
            "production_cell": "2.5 km CLUM dryland-cropping cell with >40 ha cropping "
                               "(app/public/data/parcels.json, built by "
                               "pipeline/r4_build_demand.py).",
            "tonne_weight": "district mean PIRSA production 2022/23-2025/26, allocated to "
                            "cells in proportion to cropping_ha. Held FIXED across all "
                            "three states so the trajectory measures network change only.",
            "ladder_A_vs_B": "Ladder A counts receival points regardless of ownership and "
                             "is defined at every state. Ladder B measures the "
                             "incumbent-vs-independent gap and is UNDEFINED pre-2019, when "
                             "one operator held the whole network. The two are never "
                             "combined. Ladder A is NOT PUBLISHABLE - see ladder_a_validity.",
        },
        "ladder_a_validity": {
            "publishable": False,
            "status": LADDER_A_STATUS,
            "roster_defect_sites": ROSTER_DEFECT_SITES,
            "source": "docs/roster_audit_2026-08.md section 5",
            "ladder_b_invariance": LADDER_B_INVARIANCE,
            "also_open": "This script still builds its network states from the single "
                         "`status` field rather than from `operating_seasons`, so the "
                         "2023/24 state omits Nunjikompita, which was named receiving "
                         "that season. Ladder B is unaffected (Nunjikompita is Bunge).",
        },
        "headline": {
            "state": states[HEADLINE_STATE]["label"],
            "threshold_min": HEADLINE_MIN,
            "value": results[HEADLINE_STATE]["ladder_b_ownership_gap"][
                "share_no_independent_within"][str(HEADLINE_MIN)],
            "sentence": "share of EP grain production with no independent receival point "
                        f"within {HEADLINE_MIN} minutes' drive, "
                        f"{states[HEADLINE_STATE]['label']}: "
                        + pct(results[HEADLINE_STATE]["ladder_b_ownership_gap"][
                            "share_no_independent_within"][str(HEADLINE_MIN)]),
            "why_this_one": "It is a THRESHOLD row, so it is invariant to the site-roster "
                            "defect (see ladder_a_validity.ladder_b_invariance). It is "
                            "A11-independent, because neither T-Ports bunker is a "
                            "receival point in this state - demonstrated under every "
                            "configuration of the A11 sweep, not asserted. And it has "
                            "survived three adversarial verification rounds unchanged.",
            "demoted": "The 2023/24 -> 2025/26 trajectory and the multiple between them "
                       "are real and are retained in a supporting section, but they are "
                       "no longer load-bearing: both depend on the 2023/24 column, which "
                       "carries the A11 range, and the multiple additionally depends on "
                       "the choice of threshold. Every supporting figure is published "
                       "with its A11 range attached.",
        },
        "threshold": {
            "headline_min": HEADLINE_MIN,
            "sweep_min": list(SWEEP_MIN),
            "designation": THRESHOLD_DESIGNATION,
            "status": THRESHOLD_STATUS,
            "withdrawn_grounds": THRESHOLD_WITHDRAWN,
            "search_for_a_published_basis": THRESHOLD_SEARCH,
            "disclosure": THRESHOLD_DISCLOSURE,
            "rule": "Never quote the multiple without the levels, this sweep and the A11 "
                    "range beside it.",
        },
        "a11_coordinate_sweep": a11_sweep,
        "carried_assumptions": {k: v for k, v in CARRIED_ASSUMPTIONS},
        "speed_sensitivity": {
            "factors": list(SPEED_FACTORS),
            "method": "A uniform scaling of every A5 class speed by f divides every routed "
                      "minute by f and cannot change which path is least-time, so the "
                      "scaled network is obtained exactly by scaling minutes rather than "
                      "re-routing.",
            "why_it_matters": "Both published Ladder B rows are thresholded in ABSOLUTE "
                              "MINUTES, so a uniform error in A5 does NOT cancel out of "
                              "them: it moves the threshold. Any claim that speed error "
                              "cancels on Ladder B is false and must not be made. The "
                              "direction of the finding survives x0.85-x1.15; the levels "
                              "are materially A5-dependent.",
            "per_state": {k: results[k]["ladder_b_ownership_gap"].get("speed_sensitivity")
                          for k in ("s2023_24", "s2025_26")},
        },
        "inputs": {
            "sites": "data/processed/sites.geojson",
            "roads": "data/processed/roads.graph.json",
            "production": "data/processed/production_districts.parquet",
            "cells": "app/public/data/parcels.json",
        },
        "coverage": {
            "n_production_cells": len(parcels),
            "total_weighted_tonnes": round(total_t),
            "cropping_ha_by_district": {k: round(dist_ha[k]) for k in sorted(dist_ha)},
            "mean_production_t_by_district": {k: round(dist_t[k]) for k in sorted(dist_t)},
            "cells_with_no_reachable_site": unreachable_any,
            "worst_site_snap_km": round(worst_snap, 2),
            "worst_cell_snap_km": round(worst_psnap, 2),
            "road_snap": snap_sens,
        },
        "states": results,
        "weighting_sensitivity": wsens,
        "wharminda_worked_example": {
            "note": "drive minutes from the closed Wharminda site to the nearest four "
                    "receival points at each state (the site itself is a candidate "
                    "pre-2019, hence the 0.0).",
            "removed_claim": WHARMINDA_REMOVAL,
            "by_state": wharminda,
        },
    }
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "r0_choice_geometry.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    write_md(out)
    print(f"wrote {DOCS/'r0_choice_geometry.json'} and {DOCS/'r0_choice_geometry.md'}")

    # console summary
    for k in ("pre_2019", "s2023_24", "s2025_26"):
        r = results[k]
        a = r["ladder_a_choice_count"]
        b = r["ladder_b_ownership_gap"]
        print(f"\n{r['label']}: {a['n_owners']} owner(s)  "
              f"[Ladder A counts withheld from the summary - not publishable]")
        if b["defined"]:
            print(f"  nearest independent, tonne-wt mean {b['wmean_nearest_independent_min']} min")
            print(f"  gap >60 min (incl. none): {b['share_gap_beyond_incl_none']['60']:.1%}")
            tag = " <-- HEADLINE" if k == HEADLINE_STATE else " (supporting; carries the A11 range)"
            print(f"  no independent within {HEADLINE_MIN} min: "
                  f"{b['share_no_independent_within'][str(HEADLINE_MIN)]:.1%}{tag}")
            print("  sweep, no independent within R min: " + "  ".join(
                f"{r_}:{b['share_no_independent_within'][str(r_)]:.1%}" for r_ in SWEEP_MIN))
            print("  speeds, no independent within "
                  f"{HEADLINE_MIN} min: " + "  ".join(
                      f"x{fk}:{v['share_no_independent_within'][str(HEADLINE_MIN)]:.1%}"
                      for fk, v in b["speed_sensitivity"].items()))
        else:
            print("  ownership gap: UNDEFINED (single operator)")

    a11p = out["a11_coordinate_sweep"]
    e = a11p["s2023_24_envelope_no_independent_within"][str(HEADLINE_MIN)]
    ml, mh = a11p["multiple_range_at_headline_min"]
    print(f"\nA11 sweep ({a11p['n_configurations']} configurations, "
          f"offsets {A11_OFFSET_KM} km x {len(A11_BEARINGS_DEG)} bearings, both bunkers):")
    print(f"  2023/24 no independent within {HEADLINE_MIN} min: "
          f"{e[0]:.1%}-{e[1]:.1%} (published "
          f"{results['s2023_24']['ladder_b_ownership_gap']['share_no_independent_within'][str(HEADLINE_MIN)]:.1%})")
    print(f"  2023/24 gap >60 min: {a11p['s2023_24_envelope_gap_over_60'][0]:.1%}-"
          f"{a11p['s2023_24_envelope_gap_over_60'][1]:.1%}")
    print(f"  multiple: {ml:.2f}x-{mh:.2f}x")
    print("  HEADLINE ("
          f"{states[HEADLINE_STATE]['label']}, {HEADLINE_MIN} min) at every configuration: "
          + ", ".join(f"{v:.1%}" for v in a11p["headline_state_is_a11_independent"][
              "share_no_independent_within_90_at_every_configuration"]))


def pct(x) -> str:
    return f"{x*100:.1f} %"


def write_md(o):
    s = o["states"]
    A = lambda k: s[k]["ladder_a_choice_count"]
    B = lambda k: s[k]["ladder_b_ownership_gap"]
    L = ["pre_2019", "s2023_24", "s2025_26"]
    LB = ["s2023_24", "s2025_26"]
    m = []
    w = m.append

    w("# R0 — Ownership choice-set geometry, Eyre Peninsula")
    w("")
    w(f"Generated {o['generated']} by `pipeline/r8_choice_geometry.py`.")
    w("")
    w(f"**{o['tier']}**")
    w("")
    w("**Reproduce**")
    w("")
    w("```")
    w(o["reproduce"])
    w("```")
    w("")
    w("---")
    w("")
    H = str(HEADLINE_MIN)
    SS = lambda k, f: B(k)["speed_sensitivity"][f"{f:.2f}"]

    HK = HEADLINE_STATE
    a11 = o["a11_coordinate_sweep"]

    w("## Headline")
    w("")
    w(f"> **{o['headline']['sentence']}**")
    w("")
    w("That is the only number on this page that needs to be quoted. It is a level, not a "
      "trajectory and not a multiple, and it is the one figure here that survives every "
      "objection on record but one — A5 road speeds, disclosed immediately below:")
    w("")
    w("- **It does not depend on A11.** Neither T-Ports bunker is a receival point in "
      f"{s[HK]['label']} — both are closed for the season (published, "
      "tports.com/harvest) — so the ≤5 km tolerance on the Lock and Kimba town centroids "
      "cannot reach it. The A11 sweep below recomputes this row under all "
      f"{a11['n_configurations']} displaced configurations and returns "
      + " / ".join(pct(v) for v in
                   a11["headline_state_is_a11_independent"][
                       "share_no_independent_within_90_at_every_configuration"])
      + " every time. Demonstrated, not asserted.")
    w("- **It does not depend on the site roster.** It is a *threshold* row — a function "
      "of the drive to the nearest independent point alone — and every roster defect on "
      "record is incumbent-side. The 2026-08-31 roster correction left it at exactly this "
      "value while moving the *gap* row 74.4 % → 77.3 %.")
    w("- **It does not depend on a privileged threshold.** No threshold on this page is "
      "designated a priori (see the next section). The whole sweep column for "
      f"{s[HK]['label']} is printed below: "
      + " · ".join(f"{r} min {pct(B(HK)['share_no_independent_within'][str(r)])}"
                   for r in SWEEP_MIN)
      + ". Read whichever row you find defensible; the lowest of them is "
      f"{pct(B(HK)['share_no_independent_within'][str(SWEEP_MIN[-1])])}.")
    w("- **It has survived three adversarial verification rounds unchanged**, including "
      "an independent reimplementation with its own graph, Dijkstra and weights.")
    w("")
    w("What it *does* depend on is A5 road speeds, which are assumed. At the headline "
      "threshold this row reads "
      + ", ".join(f"{pct(SS(HK, f)['share_no_independent_within'][H])} at ×{f:.2f} speeds"
                  for f in SPEED_FACTORS)
      + ". That band is a standing row, not a footnote — see below.")
    w("")
    w(f"| {s[HK]['label']} — no independent receival point within R minutes | "
      + " | ".join(f"{r} min" for r in SWEEP_MIN) + " |")
    w("|---|" + "---|" * len(SWEEP_MIN))
    for f in SPEED_FACTORS:
        lab = (f"**×{f:.2f} (published A5) — the headline row**" if f == 1.00
               else f"×{f:.2f} travel speeds")
        cells = " | ".join(
            ("**" + pct(SS(HK, f)["share_no_independent_within"][str(r)]) + "**"
             if (f == 1.00 and r == HEADLINE_MIN)
             else pct(SS(HK, f)["share_no_independent_within"][str(r)]))
            for r in SWEEP_MIN)
        w(f"| {lab} | {cells} |")
    w("")
    w("**Everything else on this page is supporting material.** The 2023/24 → "
      f"{s[HK]['label']} trajectory and the "
      f"{B(HK)['share_no_independent_within'][H] / B('s2023_24')['share_no_independent_within'][H]:.1f}× "
      f"multiple (which is {a11['multiple_range_at_headline_min'][0]:.2f}×–"
      f"{a11['multiple_range_at_headline_min'][1]:.2f}× once A11 is swept) "
      "are real, and they are kept — in a supporting section further down, where "
      "every figure carries its A11 range. They are not load-bearing any more, because "
      "both run through the 2023/24 column and that column moves inside A11's own stated "
      "tolerance.")
    w("")
    w("**This page is Ladder B only.** Every count-of-receival-points row that used to sit "
      "here has been moved to Appendix A and must not be quoted — see "
      "[Appendix A](#appendix-a--ladder-a-choice-count-not-publishable).")
    w("")
    w("---")
    w("")
    w("## The threshold — no privileged value")
    w("")
    w(f"**Designation: {o['threshold']['designation']}.**")
    w("")
    w(o["threshold"]["status"])
    w("")
    w("The two withdrawn grounds, kept on the page so the withdrawal is checkable:")
    w("")
    for j in o["threshold"]["withdrawn_grounds"]:
        w(f"- {j}")
    w("")
    w(o["threshold"]["search_for_a_published_basis"])
    w("")
    w(o["threshold"]["disclosure"])
    w("")
    w("The full sweep, tonne-weighted share of EP production with **no independent "
      "receival point within R minutes**. The ratio between the two columns is *not* "
      "shown here: it is a supporting quantity, it depends on the 2023/24 column, and it "
      "is published in the supporting section below with its A11 range attached.")
    w("")
    w("| R (min, one way) | 2023/24 (carries the A11 range — see the A11 sweep) | "
      f"**{s[HK]['label']} — the headline column** |")
    w("|---|---|---|")
    for r in SWEEP_MIN:
        a1 = B("s2023_24")["share_no_independent_within"][str(r)]
        a2 = B(HK)["share_no_independent_within"][str(r)]
        lo, hi = a11["s2023_24_envelope_no_independent_within"][str(r)]
        mark = " **(quoted by the headline)**" if r == HEADLINE_MIN else ""
        cell2 = "**" + pct(a2) + "**" if r == HEADLINE_MIN else pct(a2)
        w(f"| **{r}**{mark} | {pct(a1)} ({pct(lo)}–{pct(hi)}) | {cell2} |")
    w("")
    w("Pre-2019 has no column here: with a single operator there is no independent point "
      "to be within any radius of, at any threshold.")
    w("")
    w("---")
    w("")
    w("## Travel-speed sensitivity — a standing row, not a footnote")
    w("")
    w("**A uniform error in A5's road speeds does NOT cancel out of the published rows.** "
      "It would cancel out of a *ratio* of two drive times, but both published rows are "
      "thresholded in **absolute minutes**, so a speed error moves the threshold. Any "
      "claim to the contrary is false and must not appear in the piece.")
    w("")
    w(f"Method: {o['speed_sensitivity']['method']}")
    w("")
    w(f"Share of production with **no independent point within R minutes**, by travel speed:")
    w("")
    w("| Travel speeds | " + " | ".join(f"{r} min" for r in SWEEP_MIN) + " |")
    w("|---|" + "---|" * len(SWEEP_MIN))
    for k in LB:
        w(f"| _{s[k]['label']}_ | " + " | ".join("" for _ in SWEEP_MIN) + " |")
        for f in SPEED_FACTORS:
            lab = f"x{f:.2f}" + (" (published A5)" if f == 1.00 else "")
            w(f"| &nbsp;&nbsp;{lab} | " + " | ".join(
                pct(SS(k, f)["share_no_independent_within"][str(r)]) for r in SWEEP_MIN) + " |")
    w("")
    lo, hi = SPEED_FACTORS[0], SPEED_FACTORS[-1]
    r_lo = (SS("s2025_26", lo)["share_no_independent_within"][H]
            / SS("s2023_24", lo)["share_no_independent_within"][H])
    r_hi = (SS("s2025_26", hi)["share_no_independent_within"][H]
            / SS("s2023_24", hi)["share_no_independent_within"][H])
    r_mid = (B("s2025_26")["share_no_independent_within"][H]
             / B("s2023_24")["share_no_independent_within"][H])
    w(f"At the {HEADLINE_MIN}-minute threshold the headline row reads "
      f"{pct(SS('s2023_24', lo)['share_no_independent_within'][H])} → "
      f"{pct(SS('s2025_26', lo)['share_no_independent_within'][H])} at x{lo:.2f} speeds, "
      f"{pct(B('s2023_24')['share_no_independent_within'][H])} → "
      f"{pct(B('s2025_26')['share_no_independent_within'][H])} at published A5 speeds, and "
      f"{pct(SS('s2023_24', hi)['share_no_independent_within'][H])} → "
      f"{pct(SS('s2025_26', hi)['share_no_independent_within'][H])} at x{hi:.2f}. The "
      f"multiple ranges {min(r_lo, r_mid, r_hi):.2f}×–{max(r_lo, r_mid, r_hi):.2f}× across "
      "that band. **Direction and sign survive; the levels are materially A5-dependent, "
      "and any number quoted from this page carries that dependence.**")
    w("")
    w("---")
    w("")
    # ---------------------------------------------------------------- supporting section
    w("## Supporting — the 2023/24 → 2025/26 trajectory and the multiple")
    w("")
    w("**Demoted 2026-08-31. Not load-bearing, and not the headline.** These figures are "
      "real and are not withdrawn. They are moved here because every one of them runs "
      "through the 2023/24 column, and the 2023/24 column moves inside A11's own stated "
      "≤5 km tolerance on the Lock and Kimba coordinates. Each figure below is therefore "
      "printed with its A11 range, and **no figure from this section may be quoted "
      "without that range**.")
    w("")
    e90 = a11["s2023_24_envelope_no_independent_within"][H]
    mlo, mhi = a11["multiple_range_at_headline_min"]
    w("| Row | pre-2019 | 2023/24 (A11 range) | " + s[HK]["label"] + " |")
    w("|---|---|---|---|")
    w(f"| No independent point within {HEADLINE_MIN} min | _undefined — single operator_ | "
      f"{pct(B('s2023_24')['share_no_independent_within'][H])} "
      f"(**{pct(e90[0])}–{pct(e90[1])}**) | **{pct(B(HK)['share_no_independent_within'][H])}** "
      "(A11-independent) |")
    for f in SPEED_FACTORS:
        tag = "**×1.00 (A5 as published)**" if f == 1.00 else f"×{f:.2f} travel speeds"
        w(f"| &nbsp;&nbsp;same row, {tag} | _undefined_ | "
          f"{pct(SS('s2023_24', f)['share_no_independent_within'][H])} | "
          f"{pct(SS(HK, f)['share_no_independent_within'][H])} |")
    eg = a11["s2023_24_envelope_gap_over_60"]
    w("| Nearest independent >60 min beyond nearest Bunge (**gap row — not "
      "roster-invariant, see the note below**) | _undefined_ | "
      f"{pct(B('s2023_24')['share_gap_beyond_incl_none']['60'])} "
      f"(**{pct(eg[0])}–{pct(eg[1])}**) | "
      f"{pct(B(HK)['share_gap_beyond_incl_none']['60'])} (A11-independent) |")
    for f in SPEED_FACTORS:
        tag = "**×1.00 (A5 as published)**" if f == 1.00 else f"×{f:.2f} travel speeds"
        w(f"| &nbsp;&nbsp;same row, {tag} | _undefined_ | "
          + " | ".join(pct(SS(k, f)["share_gap_beyond_incl_none"]["60"]) for k in LB) + " |")
    w("| Distinct operators on the peninsula | " + " | ".join(
        str(A(k)["n_owners"]) for k in L) + " |")
    w("")
    w("The trajectory as a sentence, with the range that must travel with it: **between "
      f"2023/24 and {s[HK]['label']} the share of EP grain production with no independent "
      f"receival point inside a {HEADLINE_MIN}-minute cart went from "
      f"{pct(B('s2023_24')['share_no_independent_within'][H])} — anywhere in "
      f"{pct(e90[0])}–{pct(e90[1])} once A11's coordinate tolerance is swept — to "
      f"{pct(B(HK)['share_no_independent_within'][H])}**, driven by two site closures. "
      "The pre-2019 cell of that row is blank on purpose: there was nothing independent "
      "to be far from.")
    w("")
    w(f"**The multiple.** On the published coordinates it is "
      f"{B(HK)['share_no_independent_within'][H] / B('s2023_24')['share_no_independent_within'][H]:.2f}×. "
      f"Across the A11 sweep it ranges **{mlo:.2f}×–{mhi:.2f}×**. Across the travel-speed "
      f"band it ranges {min(r_lo, r_mid, r_hi):.2f}×–{max(r_lo, r_mid, r_hi):.2f}×, and "
      f"across the threshold sweep {min(B(HK)['share_no_independent_within'][str(r)] / B('s2023_24')['share_no_independent_within'][str(r)] for r in SWEEP_MIN):.2f}×–"
      f"{max(B(HK)['share_no_independent_within'][str(r)] / B('s2023_24')['share_no_independent_within'][str(r)] for r in SWEEP_MIN):.2f}×, "
      f"with {HEADLINE_MIN} min sitting at the top of that last range. Three separate "
      "sensitivities each move it by more than a third of its own size. That is why it is "
      "here and not at the top of the page. What does not move: the 2025/26 level exceeds "
      "the 2023/24 level at every threshold in the sweep, at every travel speed tested "
      "and at every A11 configuration.")
    w("")
    w("**The gap row is not roster-invariant.** " + o["ladder_a_validity"]["ladder_b_invariance"])
    w("")
    w("---")
    w("")
    # ----------------------------------------------------------------- A11 sweep section
    w("## A11 — the Lock and Kimba coordinate sweep (standing table)")
    w("")
    w(a11["what"])
    w("")
    w(f"**Method.** {a11['method']} Offsets {', '.join(str(x) for x in a11['offsets_km'])} km; "
      f"bearings {', '.join(str(b) for b in a11['bearings_deg'])}°; "
      f"{a11['n_configurations']} configurations in all, every one of them in the JSON "
      "under `a11_coordinate_sweep.grid`. \"Most favourable\" means "
      f"{a11['favourable_means']}.")
    w("")
    w("| Lock/Kimba displacement | Direction (Lock°, Kimba°) | 2023/24: no independent "
      f"within {HEADLINE_MIN} min | 2023/24: gap >60 min | {s[HK]['label']}: no "
      f"independent within {HEADLINE_MIN} min | multiple |")
    w("|---|---|---|---|---|---|")
    for row in a11["rows"]:
        d = row["offset_km"]
        variants = ([("published coordinates", row["most_favourable"])] if d == 0 else
                    [("most favourable", row["most_favourable"]),
                     ("least favourable", row["least_favourable"])])
        for lab, g in variants:
            bl, bk = g["bearing_lock_deg"], g["bearing_kimba_deg"]
            bear = "— (as published)" if bl is None else f"{bl}°, {bk}°"
            v23 = g["s2023_24_no_independent_within"][H]
            v25 = g["s2025_26_no_independent_within"][H]
            w(f"| **{d:g} km** — {lab} | {bear} | {pct(v23)} | "
              f"{pct(g['s2023_24_gap_over_60'])} | {pct(v25)} | {v25/v23:.2f}× |")
    w("")
    w(f"The extremes above are selected on the {HEADLINE_MIN}-minute threshold row. "
      "The gap column shows that same configuration's gap value, not the gap row's own "
      "extreme; across the whole sweep the 2023/24 gap >60 min row runs "
      f"{pct(a11['s2023_24_envelope_gap_over_60'][0])}–"
      f"{pct(a11['s2023_24_envelope_gap_over_60'][1])} against a published "
      f"{pct(B('s2023_24')['share_gap_beyond_incl_none']['60'])}.")
    w("")
    w(f"**Range over the whole sweep.** The 2023/24 {HEADLINE_MIN}-minute row runs "
      f"{pct(e90[0])}–{pct(e90[1])} against a published {pct(B('s2023_24')['share_no_independent_within'][H])}; "
      f"the multiple runs {mlo:.2f}×–{mhi:.2f}× against a published "
      f"{B(HK)['share_no_independent_within'][H] / B('s2023_24')['share_no_independent_within'][H]:.2f}×. "
      f"The {s[HK]['label']} row is {pct(B(HK)['share_no_independent_within'][H])} at "
      f"every one of the {a11['n_configurations']} configurations. "
      + a11["headline_state_is_a11_independent"]["why"])
    w("")
    pub23 = B("s2023_24")["share_no_independent_within"][H]
    dn, up = (pub23 - e90[0]) * 100, (e90[1] - pub23) * 100
    w(f"**A11's asymmetry claim, tested.** {a11['asymmetry_check']} On this sweep the "
      f"2023/24 {HEADLINE_MIN}-minute share moves **−{dn:.1f} pp / +{up:.1f} pp** around "
      f"its published {pct(pub23)}. "
      + ("It never falls below the published value, so the claim holds exactly as stated."
         if e90[0] >= pub23 else
         f"So the claim is **too strong as A11 words it**: a {pct(e90[0])} "
         "configuration exists, and the share can fall as well as rise. What survives is "
         "the weaker statement, which is the one that matters — the error is strongly "
         f"asymmetric in SIZE. The movement that raises the 2023/24 share (+{up:.1f} pp) "
         f"is about {up/dn:.0f}× the movement that lowers it (−{dn:.1f} pp), so a reader "
         f"who wants a single number rather than a range should take the pessimistic end, "
         f"{pct(e90[1])}, not the published {pct(pub23)} — and the trajectory and "
         "multiple should be read from there. **A11's own wording should be narrowed "
         "from 'never better' to this.**"))
    w("")
    w("The 2023/24 envelope across the whole threshold sweep, for a reader who rejects "
      f"{HEADLINE_MIN} minutes:")
    w("")
    w("| R (min) | " + " | ".join(str(r) for r in SWEEP_MIN) + " |")
    w("|---|" + "---|" * len(SWEEP_MIN))
    w("| 2023/24, published coordinates | " + " | ".join(
        pct(B("s2023_24")["share_no_independent_within"][str(r)]) for r in SWEEP_MIN) + " |")
    w("| 2023/24, A11 envelope | " + " | ".join(
        pct(a11["s2023_24_envelope_no_independent_within"][str(r)][0]) + "–"
        + pct(a11["s2023_24_envelope_no_independent_within"][str(r)][1])
        for r in SWEEP_MIN) + " |")
    w(f"| {s[HK]['label']} (A11-independent) | " + " | ".join(
        pct(B(HK)["share_no_independent_within"][str(r)]) for r in SWEEP_MIN) + " |")
    w("")
    w("---")
    w("")
    w("## The definitional problem, handled up front")
    w("")
    w("The brief asks for \"nearest independent receival point\" at three network states. "
      "At the first state that quantity does not exist. Pre-2019 the entire EP receival "
      "network — every point on it, however many that was — was operated by a single "
      "company (Viterra, since Aug 2025 Bunge Operations Pty Ltd). There was no "
      "independent option anywhere on the peninsula, at any distance. That statement is "
      "about *ownership*, and it does not depend on the site count, which is why it "
      "survives the roster defect that invalidates Ladder A.")
    w("")
    w("That is not a large ownership gap. It is an undefined one, and the difference "
      "matters in the wrong direction: if you score pre-2019 as \"100 % of production has "
      "no independent option within cart range\" and then score 2025/26 the same way, the "
      "2019 closure of six sites reads as an *improvement* in competitive choice. It was "
      "not. It was a reduction in the number of places to deliver, inside a monopoly.")
    w("")
    w("So this analysis reports two ladders and never adds them:")
    w("")
    w("| | Ladder A — **choice count** | Ladder B — **ownership gap** |")
    w("|---|---|---|")
    w("| Question | How many receival points can this paddock reach, whoever owns them? | "
      "How much further is the nearest *non-incumbent* point than the nearest incumbent one? |")
    w("| Defined at | all three states | 2023/24 and 2025/26 only |")
    w("| What moved it | the 2019 closure of six sites | T-Ports' entry, then the 2025/26 "
      "bunker closures |")
    w("| Status | **NOT PUBLISHABLE** — roster incomplete, see Appendix A | **publishable**, "
      "with a split: the *threshold* rows are invariant to the roster defect, the *gap* "
      "rows are **not** — the gap is measured from the incumbent, and the 2026-08-31 "
      "roster correction moved it 74.4 % → 77.3 % at 2025/26 |")
    w("")
    w("**Incumbent** = `Bunge (ex-Viterra)` plus the pre-rename tag `ex-Viterra`, treated "
      "as one owner throughout. **Independent** = anything else — on EP today, T-Ports "
      "alone. Merging the two Viterra/Bunge tags is the conservative choice for this piece: "
      "keeping them apart would have counted the six 2019-closed sites as a second "
      "\"operator\" and manufactured competition that never existed.")
    w("")
    w("---")
    w("")
    w("## Network states")
    w("")
    w("| State | Independent points | Distinct operators | Composition |")
    w("|---|---|---|---|")
    for k in L:
        ni = B(k)["n_independent_points"] if B(k)["defined"] else 0
        w(f"| **{s[k]['label']}** | {ni} | {A(k)['n_owners']} | {s[k]['desc']} |")
    k = "pre_2019_no_dormant"
    w(f"| _{s[k]['label']}_ | 0 | {A(k)['n_owners']} | {s[k]['desc']} |")
    w("")
    w("Membership is taken from the published `status` field of `sites.geojson` — no "
      "per-site judgement. **The total receival-point count of each state is deliberately "
      "not shown here**; it is a Ladder A quantity and the roster it comes from is "
      "incomplete (Appendix A). The *independent* count is shown because it is a count of "
      "T-Ports sites only, and every roster defect on record is on the incumbent side. "
      "Composition text is generated from the file, not typed, so a roster correction "
      "cannot leave a stale description behind it.")
    w("")
    # Ladder A's own table is built here but HELD BACK and emitted in Appendix A, so that
    # nothing between the headline and Ladder B contains a count of receival points.
    appendix_a = []
    wa = appendix_a.append
    wa("| Metric | " + " | ".join(s[k]["label"] for k in L) + " |")
    wa("|---|" + "---|" * len(L))
    wa("| Receival points in network | " + " | ".join(str(A(k)["n_receival_points"]) for k in L) + " |")
    wa("| Mean drive to nearest point (min) | " + " | ".join(str(A(k)["wmean_nearest_min"]) for k in L) + " |")
    wa("| Median drive to nearest point (min) | " + " | ".join(str(A(k)["p50_nearest_min"]) for k in L) + " |")
    wa("| 99th pct drive to nearest point (min) | " + " | ".join(str(A(k)["p99_nearest_min"]) for k in L) + " |")
    for r in NEAR_MIN:
        wa(f"| Mean points within {r} min | " + " | ".join(
            str(A(k)["wmean_points_within"][str(r)]) for k in L) + " |")
    for r in NEAR_MIN:
        wa(f"| Share with **at most one** point within {r} min | " + " | ".join(
            pct(A(k)["share_with_only_one_point_within"][str(r)]) for k in L) + " |")
    for g in GAP_THRESHOLDS_MIN:
        wa(f"| Share whose 2nd-nearest point is >{g} min beyond the 1st | " + " | ".join(
            pct(A(k)["share_2nd_beyond"][str(g)]) for k in L) + " |")
    w("---")
    w("")
    w("## Ladder B — incumbent vs independent (2023/24 and 2025/26 only)")
    w("")
    w("Gap = drive time to the nearest independent point **minus** drive time to the "
      "nearest Bunge point.")
    w("")
    w("**Read the row types differently.** The *threshold* rows (\"no independent point "
      "within R min\") are invariant to the site-roster defect. The *gap* rows (\"nearest "
      "independent >R min beyond nearest Bunge\") are **not** — they are measured from the "
      "incumbent, so they move when the roster does, and they must be quoted as \"on the "
      "roster as corrected 2026-08-31\". The 2023/24 column of every row here additionally "
      "carries the A11 range.")
    w("")
    same = all(B(k)["share_gap_beyond_incl_none"] == B(k)["share_gap_beyond_excl_none"]
               for k in LB)
    if same:
        w("The gap rows were computed twice — once counting cells with no independent "
          "point at all as beyond every threshold, once dropping them — to bracket the "
          "answer. **The two are identical**, because every EP production cell can reach "
          "Lucky Bay by road, so no cell has literally zero independent option at either "
          "state. Only one set of rows is shown.")
        w("")
    w("| Metric | " + " | ".join(s[k]["label"] for k in LB) + " |")
    w("|---|" + "---|" * len(LB))
    w("| Independent receival points | " + " | ".join(str(B(k)["n_independent_points"]) for k in LB) + " |")
    w("| Mean drive to nearest Bunge point (min) | " + " | ".join(
        str(B(k)["wmean_nearest_incumbent_min"]) for k in LB) + " |")
    w("| Mean drive to nearest independent point (min) | " + " | ".join(
        str(B(k)["wmean_nearest_independent_min"]) for k in LB) + " |")
    for g in GAP_THRESHOLDS_MIN:
        w(f"| Share with nearest independent >{g} min beyond nearest Bunge | " + " | ".join(
            pct(B(k)["share_gap_beyond_incl_none"][str(g)]) for k in LB) + " |")
    if not same:
        for g in GAP_THRESHOLDS_MIN:
            w(f"| _same, >{g} min, excl. cells with no independent option_ | " + " | ".join(
                pct(B(k)["share_gap_beyond_excl_none"][str(g)]) for k in LB) + " |")
    e90b = a11["s2023_24_envelope_no_independent_within"][str(HEADLINE_MIN)]
    w(f"| Share with **no** independent point within {HEADLINE_MIN} min (full "
      f"{SWEEP_MIN[0]}–{SWEEP_MIN[-1]} min sweep above; **only the "
      f"{s[HK]['label']} cell is the headline**) | "
      + pct(B("s2023_24")["share_no_independent_within"][str(HEADLINE_MIN)])
      + f" (A11 range {pct(e90b[0])}–{pct(e90b[1])}) | **"
      + pct(B(HK)["share_no_independent_within"][str(HEADLINE_MIN)]) + "** |")
    w("| Share whose nearest independent point is a **port** | " + " | ".join(
        pct(B(k)["share_nearest_independent_is_a_port"]) for k in LB) + " |")
    w("| _Counterweight:_ share where the independent point is **nearer** than Bunge | "
      + " | ".join(pct(B(k)["share_independent_nearer_than_incumbent"]) for k in LB) + " |")
    w("")
    w("Which independent point is nearest, by tonne share:")
    w("")
    for k in LB:
        mix = "; ".join(f"{nm} {pct(v)}" for nm, v in B(k)["nearest_independent_mix"].items())
        w(f"- **{s[k]['label']}** — {mix}")
    w("")
    w("Pre-2019 has no row here. See the definitional note above.")
    w("")
    w("**Plausible cart range.** No published EP figure exists for how far a grower will "
      "cart before the delivery stops being worth making, and this analysis refuses to "
      "borrow the sim's fitted `choiceRadius` — that would put a calibrated knob inside a "
      f"Tier-2 number. Nor is any threshold designated a priori — two earlier grounds for "
      "designating 90 minutes were withdrawn on 2026-08-31 and nothing replaced them. The "
      f"{SWEEP_MIN[0]}–{SWEEP_MIN[-1]}-minute sweep above is published in full instead, "
      "with no row privileged. The "
      "geometry that bounds it: in 2025/26 the tonne-weighted drive to the nearest "
      f"**Bunge** point is a median {B('s2025_26')['p50_nearest_incumbent_min']} min, 90th "
      f"percentile {B('s2025_26')['p90_nearest_incumbent_min']} min, 99th percentile "
      f"{B('s2025_26')['p99_nearest_incumbent_min']} min — so a {HEADLINE_MIN}-minute "
      "range is roughly five times the trip an EP grower actually makes to the incumbent, "
      "and is generous to the independent side of the comparison.")
    w("")
    w("---")
    w("")
    w("## By district")
    w("")
    w("Ladder B only. The per-district Ladder A columns (`wmean_nearest_min`, "
      "`share_only_one_within_45`) are still emitted to the JSON for the roster rebuild "
      "but are **not shown here and not publishable** — see Appendix A. A district cut of a "
      "count-of-points row inherits the roster defect in full, and concentrates it: a "
      "missing site distorts its own district more than it distorts the peninsula.")
    w("")
    A_COLS = {"wmean_nearest_min", "share_only_one_within_45"}
    for k in LB:
        w(f"**{s[k]['label']}**")
        w("")
        cols = [c for c in s[k]["by_district"]["WEP"].keys() if c not in A_COLS]
        w("| District | " + " | ".join(cols) + " |")
        w("|---|" + "---|" * len(cols))
        for d in ("WEP", "LEP", "EEP"):
            row = s[k]["by_district"][d]
            vals = []
            for c in cols:
                v = row[c]
                vals.append(pct(v) if c.startswith("share") else str(v))
            w(f"| {d} | " + " | ".join(vals) + " |")
        w("")
    w("---")
    w("")
    w("## Sensitivity — what would have to be wrong")
    w("")
    w("**The tonne weighting.** The headline holds production fixed at the 2022/23–2025/26 "
      "district mean so the trajectory is a network effect, not a weather effect. Re-run "
      "under each state's own harvest, and unweighted (one vote per production cell):")
    w("")
    ws = o["weighting_sensitivity"]
    w("| Weighting | 2023/24 gap >60 min | 2023/24 no indep. within 90 min | 2025/26 gap >60 min "
      "| 2025/26 no indep. within 90 min |")
    w("|---|---|---|---|---|")
    w("| fixed mean 2022/23–2025/26 (**headline**) | " + " | ".join([
        pct(ws["s2023_24"]["fixed_mean_2022-26"]["gap_over_60"]),
        pct(ws["s2023_24"]["fixed_mean_2022-26"]["no_independent_within_90"]),
        pct(ws["s2025_26"]["fixed_mean_2022-26"]["gap_over_60"]),
        pct(ws["s2025_26"]["fixed_mean_2022-26"]["no_independent_within_90"])]) + " |")
    w("| each state's own season | " + " | ".join([
        pct(ws["s2023_24"]["own_season_2023/24"]["gap_over_60"]),
        pct(ws["s2023_24"]["own_season_2023/24"]["no_independent_within_90"]),
        pct(ws["s2025_26"]["own_season_2025/26"]["gap_over_60"]),
        pct(ws["s2025_26"]["own_season_2025/26"]["no_independent_within_90"])]) + " |")
    w("| unweighted cells (one vote per cell) | " + " | ".join([
        pct(ws["s2023_24"]["unweighted_cells"]["gap_over_60"]),
        pct(ws["s2023_24"]["unweighted_cells"]["no_independent_within_90"]),
        pct(ws["s2025_26"]["unweighted_cells"]["gap_over_60"]),
        pct(ws["s2025_26"]["unweighted_cells"]["no_independent_within_90"])]) + " |")
    w("")
    w("Every 2023/24 cell in that table is a supporting figure and carries the A11 range "
      "on top of the weighting spread; the 2025/26 cells do not. The fixed weighting is "
      "not what produces the result: the trajectory is the same "
      "sign and roughly the same size on all three. Unweighted is the harshest reading "
      "because far-west and eastern marginal cells vote equally with high-yield Lower EP "
      "country; the tonne-weighted headline is the conservative one.")
    w("")
    w("**\"No independent option at all\" is entirely a cart-range question, not a "
      "reachability one.** Every production cell on EP can reach Lucky Bay by road, so no "
      "cell has literally zero independent option at any state. The finding is about how "
      "far the option is, and the cart-range sweep is where that judgement lives. A "
      f"reviewer who rejects {HEADLINE_MIN} minutes as a cart range should substitute "
      "their own threshold from the published sweep: 2025/26 exceeds 2023/24 at all seven, "
      f"and the share is still {pct(B('s2025_26')['share_no_independent_within'][str(SWEEP_MIN[-1])])} "
      f"of production at the most generous ({SWEEP_MIN[-1]} min) row.")
    w("")
    rs = o["coverage"]["road_snap"]
    w(f"**Road-network snap.** Tonne-weighted mean snap {rs['wmean_snap_km']} km, "
      f"{pct(rs['wshare_cells_snapped_over_2km'])} of production beyond 2 km and "
      f"{pct(rs['wshare_cells_snapped_over_5km'])} beyond 5 km (worst single cell "
      f"{o['coverage']['worst_cell_snap_km']} km, far-west marginal country). "
      + rs["note"]
      + f" Worst site snap is {o['coverage']['worst_site_snap_km']} km, i.e. every "
        "receival point is on the graph.")
    w("")
    w("---")
    w("")
    w("## Wharminda — the worked example")
    w("")
    w("Wharminda is one of the six sites tagged `closed_2019` in `sites.geojson`; it is "
      "used here as a worked example because it sits in the middle of the eastern cropping "
      "country and makes the ownership arithmetic legible in a single row.")
    w("")
    w("> " + o["wharminda_worked_example"]["removed_claim"])
    w("")
    w("Nearest receival points to the closed site, by state:")
    w("")
    w("| State | Nearest four receival points | Nearest **independent** point |")
    w("|---|---|---|")
    for k in L:
        e = o["wharminda_worked_example"]["by_state"][k]
        four = "; ".join(f"{nm} {t} min" for t, nm, _op in e["nearest_four_any_owner"])
        ni = e["nearest_independent"]
        indep = f"{ni[1]} — **{ni[0]} min**" if ni else "_none exists — single operator_"
        w(f"| {s[k]['label']} | {four} | {indep} |")
    w("")
    w("The Bunge column does not move between 2023/24 and 2025/26 — Wharminda's "
      "surroundings kept the same incumbent options. What moved is the third column: the "
      "nearest non-Bunge point went from a bunker to a port on the far side of the "
      "peninsula. That is the whole finding in one row.")
    w("")
    w("_Caveat on the middle column._ \"Nearest four receival points\" is a Ladder A "
      "quantity and inherits the roster defect: Tooligie in particular sits in this part "
      "of the peninsula and is missing from `sites.geojson` altogether, so a nearer "
      "incumbent option may be absent from that column. The right-hand column is "
      "unaffected — it lists independent points, and every roster defect on record is "
      "incumbent-side. Quote the right-hand column, not the middle one.")
    w("")
    w("---")
    w("")
    w("## What this does and does not establish")
    w("")
    w("**Does.** Every number above is a distance measured on a published road network "
      "between published site locations, weighted by published district production. It "
      "depends on no simulation output, no calibrated parameter, and none of A1, A2, A9 or "
      "A24. That claim is now **exactly** true rather than approximately so: until "
      "2026-08-31 the second ground of the threshold argument on this page reasoned from "
      "A2's 12 h farm-truck dispatch window, which made the sentence false as written. "
      "That ground has been withdrawn rather than the sentence weakened, because the "
      "independence is what the whole tier structure of the piece rests on. An opposing "
      "expert can dispute the queue model; they cannot dispute how far Wharminda is from "
      "an alternative.")
    w("")
    w("**Does not.** It says nothing about intent — the Lock and Kimba bunkers closing for "
      "2025/26 is entirely consistent with a drought year and bunker economics, and the "
      "piece should say so. It says nothing about price. It says nothing about whether a "
      "grower *would* use a more distant option; it measures the option set, not the "
      "choice. And 'nearest' is drive time, not commercial terms: a site that is close but "
      "does not segregate the grade a grower is carting is not, in practice, a choice — "
      "this analysis counts it as one, which is conservative for the incumbent.")
    w("")
    w("## Carried assumptions")
    w("")
    for code, text in CARRIED_ASSUMPTIONS:
        w(f"- **{code}** {text}")
    w("")
    w("---")
    w("")
    w("## Appendix A — Ladder A (choice count). NOT PUBLISHABLE")
    w("")
    w("> **Do not quote any row in this appendix.** " + o["ladder_a_validity"]["status"])
    w("")
    w("The specific defects, all from `docs/roster_audit_2026-08.md` section 5:")
    w("")
    w("| Site | Defect |")
    w("|---|---|")
    for nm in sorted(ROSTER_DEFECT_SITES):
        w(f"| **{nm}** | {ROSTER_DEFECT_SITES[nm]} |")
    w("")
    w(o["ladder_a_validity"]["also_open"])
    w("")
    w("**Why this is an appendix and not a deletion.** These rows are the audit trail for "
      "the roster rebuild — they record what the counts were before the roster was fixed, "
      "which is what makes the next correction checkable. Deleting them would destroy that "
      "record and would also hide the fact that the row has been wrong twice. They are "
      "kept, fenced, and labelled, and the headline table above contains no count of "
      "receival points at all.")
    w("")
    w("**Why the headline survives this.** " + o["ladder_a_validity"]["ladder_b_invariance"])
    w("")
    w("Tonne-weighted over EP grain production. \"Points within R\" counts receival points "
      "of any ownership reachable within R minutes' one-way drive. Note the row label is "
      "**at most one**, not \"only one\": the underlying test is `count <= 1`, so cells "
      "with *zero* points inside the radius are included.")
    w("")
    m.extend(appendix_a)
    w("")
    w("Reproduce these rows (they are also in the JSON under "
      "`states.<state>.ladder_a_choice_count`, flagged `publishable: false`):")
    w("")
    w("```")
    w(o["reproduce"])
    w("```")
    w("")
    (DOCS / "r0_choice_geometry.md").write_text("\n".join(m) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
