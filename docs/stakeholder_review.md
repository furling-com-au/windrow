# Stakeholder review — what would each audience want from Windrow?

A structured walk through the people who care about the EP grain chain, what Windrow
v1 already gives them, and what it would need before they'd rely on it. Backlog items
are tagged [Q] quick win, [M] medium effort, [L] large / needs data partnerships.

A general note that applies to almost everyone below: Windrow's *observed* layers
(weekly receivals, port statistics, vessel schedules, production) are solid published
data, but its *operational* outputs — queue lengths, site stocks, cycle times — inherit
assumptions A1–A4. They are honest as relative indicators between scenarios and
seasons, and labelled as such; no stakeholder should read them as measurements.

---

## 1. Growers and farm advisors

**They'd ask:** "When will queues be worst at my site? Which site should I cart to this
week? What happens if Lock doesn't open next year?"

**Already useful:** the season replay makes the system legible — where grain flows,
when the peak hits each district, how weather pauses propagate into receivals; the
site-closure logic (dormant sites, T-Ports seasons) mirrors the real network; the
Lucky Bay scenario shows catchment shifts.

**Missing for them:**
- Per-site drill-down: click a site → its season receivals curve, busiest simulated
  days, queue profile by hour [Q — data already in the sim, needs a panel].
- Historical anchors per site: the reports name busiest sites weekly; extracting
  site-mention time series from `receivals_notes.jsonl` would ground per-site patterns
  in something published [M].
- Absolute queue-time credibility: needs published or operator turnaround data (the
  biggest single data gap in the whole project — A2) [L].

## 2. Bunge (network operator)

**They'd ask:** "Does this misrepresent our operations?" first, then "can we use it for
segregation planning, outage contingency, and site-investment cases?"

**Already useful:** a public, provenance-disciplined mirror of what their own reports
say, with disclaimers; scenario machinery (outage, bumper) is exactly the shape of
their contingency questions; the calibration shows how much of network behaviour is
recoverable from public data alone (a compliment and a warning).

**Missing for them:**
- Commodity-level stocks in the UI (the sim tracks six commodities; the panel shows
  totals) — segregation is their daily problem [Q].
- Real site capacities, receival hours, and cycle times under NDA would convert queue
  outputs from indicative to plannable [L — data partnership].
- Sensitivity view: which assumptions drive an output (e.g. queue = f(service time
  A2)) so they can see what's model vs data [M].

**Risk to manage:** the app must never look like it leaks operational data or ranks
their sites' performance. The "simulation, not operational data" framing needs to stay
loud, and vessel name joins are heuristic — a wrong name against a real ship is the
most likely complaint. (Names are flagged as candidates in the About page; consider an
in-UI "(name from stem, heuristic)" tooltip [Q].)

## 3. T-Ports (and any future Port Spencer proponent)

**They'd ask:** "What's our catchment under different attractiveness assumptions?
What would reopening Lock/Kimba do? What does weather downtime cost us?"

**Already useful:** the Lucky Bay share scenario is literally their business question;
A15 documents the bunker-season logic transparently.

**Missing:** transshipment weather downtime — their published limits (wind > 21 kn,
swell > 2.5 m) could gate the LB loading rate using the ERA5 wind series already in
the bundle [M]. Per-catchment origin maps of LB intake [Q — sim has cluster origins].

## 4. Road transport operators / carriers

**They'd ask:** "Truck numbers, not tonnes: how many trucks, how many cycles, which
corridors, what harvest-labour peak?"

**Already useful:** fleet size is a calibrated (not assumed) 589 at peak; cycle counts
and truck-km proxies exist internally; corridor closure scenario shows re-routing.

**Missing:** the §8 truck-flow heatmap (truck-km by highway segment) is the single
most valuable output for this group and for DIT [M — the sim already knows each trip's
path key; aggregate trips × path polylines into a corridor intensity export].
Per-day truck movement counts at ports (compare to the published "48 trucks/day rail
replacement" figure) [Q].

## 5. SA Department for Infrastructure and Transport / infrastructure planners

**They'd ask:** "Corridor loadings for the EP Grain Export Supply Chain Planning Study
space: AADT-comparable harvest truck volumes, rail counterfactuals, port resilience."

**Already useful:** the rail-reinstatement scenario with explicit trainset assumptions;
outage and road-closure scenarios; everything reproducible and citable.

**Missing:** corridor heatmap (above) with absolute movement counts and a validation
hook against traffic counts (DIT publishes AADT for state roads — a joinable open
dataset) [M]. Road-closure realism: which legs use a closed corridor, and how much of
each one does, is now read off the real routed paths (#28), but the ×2.5 detour penalty
itself is still assumed rather than routed on the graph [M].

## 6. PIRSA / agricultural policy

**They'd ask:** "Does it respect our production estimates? Can it explore drought
response, on-farm storage growth, harvest weather risk?"

**Already useful:** their district tables are the demand backbone (spot-verified);
the drought season is the held-out validation; retention share is an explicit lever.

**Missing:** an on-farm-storage scenario (retention ↑ over years is a real trend) [Q —
it's one parameter]; climate-scenario runs (re-run seasons under shifted weather) [M].

## 7. Flinders Ports / marine side

**They'd ask:** "Berth occupancy, anchorage congestion, interaction with non-grain
trade and cruise calls."

**Already useful (and improved in this pass):** vessels now arrive at the Boston Bay
anchorage at AIS-observed times and hold until their berth slot — baseline mean wait
28.3 h reproduces the AIS-observed 26.8 h median. Berth panel + waiting counts; AIS
berth stays validated against their own published Dry Bulk call counts.

**Missing:** berth-occupancy timeline chart (% occupied by week — the data exists in
the event log) [Q]; non-grain berth traffic (fuel, fishing-industry vessels) is out of
scope but could be noted in the About page so the berth panel isn't read as the whole
port [Q]; cruise-season loading stoppages (published in the stem's closure notes)
as schedule constraints [M].

## 8. Grain exporters / marketers

**They'd ask:** "Is the shipping program feasible? Where will stocks be when my vessel
arrives? What's my demurrage exposure in a drought?"

**Already useful:** the drought scenario is precisely the program-infeasibility story
(vessels starving at anchor, short-loading); stem-derived names/tonnages give the port
panel real texture.

**Missing:** carry-in stocks (season starts empty → early-season vessels under-loaded;
top model gap) [M]; per-vessel wait/demurrage-proxy table export [Q]; commodity-level
port stock display (again) [Q].

## 9. Researchers and analysts (AEGIC-type, universities)

**They'd ask:** "Can I trust it, extend it, and cite it?"

**Already strong — this is the audience v1 serves best:** full provenance chain
(SOURCES/ASSUMPTIONS/CALIBRATION), deterministic replays with hashed event logs,
held-out validation honestly reported including the ERA5 rain-event miss, one-command
regeneration, MIT-able code with clearly licensed data (one NC layer flagged).

**Missing:** CSV/JSON export of sim results from the app [Q]; a CITATION.cff and a
tagged release [Q]; the archived stem PDFs parsed to a daily vessel-program dataset —
a genuinely novel public dataset if done thoroughly [M].

## 10. Media and local community (Port Lincoln, EP councils)

**They'd ask:** "What am I looking at, and what's the story?" — harvest progress,
record weeks, why the highway is full of road trains in November.

**Already useful (improved in this pass):** the map legend now explains every symbol;
the money chart tells the sim-vs-reality story at a glance.

**Missing:** a guided intro tour (3–4 captions: paddocks → trucks → silos → ships)
[Q]; event annotations on the chart (first delivery, record week, rain events —
all already in the data) [Q]; mobile layout polish (panels overlap on small screens —
spec's degrade-gracefully item is only partly done) [M].

---

## Prioritised backlog distilled from the above

| # | Item | Effort | Serves | Status |
|---|---|---|---|---|
| 1 | Ships waiting at anchor (AIS-linked) | — | 7, 8, 10 | **done** |
| 2 | Map legend | — | 10, everyone | **done** |
| 3 | Commodity-level stock display (site drill-down) | Q | 2, 8 | **done** |
| 4 | Per-site drill-down panel (click a site) | Q | 1, 2 | **done** |
| 5 | Berth-occupancy sparkline (PL panel) | Q | 7, 8, 9 | **done** (wait-table export pending) |
| 6 | Chart annotations + guided intro tour | Q | 10 | **done** |
| 7 | CSV export; CITATION.cff; public GitHub repo | Q | 9 | **done** |
| 8 | Carry-in stocks at season start (A17) | M | 8, calibration | **done** |
| 9 | Corridor truck-flow heatmap (in-app toggle) | M | 4, 5 | **done** (DIT AADT cross-check pending) |
| — | Interactive what-if levers + plain-language takeaways with indicative $ (A18–A19) | M | everyone | **done** |
| — | Live 2026/27 season machinery + weekly refresh workflow | M | everyone | **done** (provisional until harvest) |
| 10 | LB transshipment weather downtime from ERA5 wind | M | 3 | open |
| 11 | Routed road-closure detours (replace the assumed ×2.5 penalty) | M | 5 | partial (#28: corridor assignment now uses the routed paths; the detour itself is still assumed) |
| 12 | Site-mention time series from report narratives (per-site anchors) | M | 1, 2 | open |
| 13 | Daily stem-derived vessel-program dataset from 75 archived PDFs | M | 8, 9 | open |
| 14 | Mobile layout pass (panel collapses; legend hidden < 800 px) | M | 10 | partial |
| 15 | Operator data partnership (capacities, turnarounds) | L | 1, 2 | open |
| 16 | Sentinel-2 paddock segmentation (§8) | L | 1, 6 | open |

The theme across stakeholders: the *observed* spine is already trustworthy; the wants
cluster around (a) exposing more of what the sim already computes (quick wins 3–7),
(b) two structural model gaps (carry-in stocks, corridor heatmap), and (c) the one
thing public data cannot provide — operator-grade site parameters — which is a
partnership question, not an engineering one.

---

## Fresh-eyes usability review (2026-08-19, post-sprint)

Walked the deployed site as a first-time lay visitor. Findings → fixes, all shipped:

1. **The dashboard was dead on arrival** — date frozen at 1 Oct, every KPI 0.00,
   "berth idle" ×3 behind the tour. A static screen reads as broken. → The season now
   **auto-plays at 1 day/second** on load and after every scenario/season change; the
   end state offers "↺ Replay season".
2. **Jargon on the first screen** — "held-out", "sim vs observed", "Western region
   receivals", "Lucky Bay pull 0.7×", "deltas vs baseline", "PL outage". → Plain-language
   pass everywhere: "drought year", "simulated vs actual", "Grain delivered", "Grain
   drawn to Lucky Bay", "What changed", "Port Lincoln closed a week". Technical terms
   survive only in docs and tooltips.
3. **One panel for every audience** was overwhelming. → **Two view modes** (persisted):
   **Simple** (default) = map + play + KPIs + chart + scenario stories + "What changed"
   takeaways; **Advanced** adds the lever sliders, truck-flow heatmap and CSV export.
   Scenario presets remain the lay person's what-if instrument — the takeaways panel
   works identically in both modes.

**On "different views for different users":** two modes, not five role dashboards.
The role-specific *content* differences (grower vs planner vs port) are already served
by where you look (site drill-down vs heatmap vs port panel) and would fragment a
single-page tool if split further; the real divide observed was depth-of-control, which
the Simple/Advanced toggle captures. Revisit only if a specific audience (e.g. DIT)
requests a dedicated corridor view.
