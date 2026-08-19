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
dataset) [M]. Road-closure realism: currently a straight-line heuristic ×2.5; a routed
detour on the actual graph is straightforward in the pipeline [M].

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

| # | Item | Effort | Serves |
|---|---|---|---|
| 1 | ~~Ships waiting at anchor (AIS-linked)~~ **done this pass** | — | 7, 8, 10 |
| 2 | ~~Map legend~~ **done this pass** | — | 10, everyone |
| 3 | Commodity-level stock display (sites + ports) | Q | 2, 8 |
| 4 | Per-site drill-down panel (season curve, queue profile) | Q | 1, 2 |
| 5 | Berth-occupancy timeline + per-vessel wait table export | Q | 7, 8, 9 |
| 6 | Chart annotations (records, rain events, first delivery) + intro tour | Q | 10 |
| 7 | CSV export of run results; CITATION.cff | Q | 9 |
| 8 | Carry-in stocks at season start | M | 8, calibration |
| 9 | Corridor truck-km heatmap (§8 stretch) + DIT AADT cross-check | M | 4, 5 |
| 10 | LB transshipment weather downtime from ERA5 wind | M | 3 |
| 11 | Routed road-closure detours (replace straight-line heuristic) | M | 5 |
| 12 | Site-mention time series from report narratives (per-site anchors) | M | 1, 2 |
| 13 | Daily stem-derived vessel-program dataset from 75 archived PDFs | M | 8, 9 |
| 14 | Mobile layout pass | M | 10 |
| 15 | Operator data partnership (capacities, turnarounds) | L | 1, 2, absolute credibility |
| 16 | Sentinel-2 paddock segmentation (§8) | L | 1, 6 |

The theme across stakeholders: the *observed* spine is already trustworthy; the wants
cluster around (a) exposing more of what the sim already computes (quick wins 3–7),
(b) two structural model gaps (carry-in stocks, corridor heatmap), and (c) the one
thing public data cannot provide — operator-grade site parameters — which is a
partnership question, not an engineering one.
