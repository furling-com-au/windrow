# Assumptions Register — Windrow

Every value used by the model that is **not** backed by a published source, with
reasoning. Data files mark these `"provenance": "assumed"`. Simulated outputs are never
presented as measured data.

## A1 — truck net payloads per configuration
- **Value**: semi-trailer 28 t; 9-axle B-double 42 t; A-double road train 55 t;
  AB-triple 68 t (net grain tonnes). Model blends: **farm→site 38 t**
  (`truckPayloadT`), **site→port line-haul 45 t** (`linehaulPayloadT`).
- **Used in**: truck agents (Phase 3 params). Both blends are exposed as assumption
  levers in the app.
- **Reasoning**: GTSN publishes gross combination masses only; tares are not published.
  Net ≈ 62–66 % of GCM. The two published anchors pull in different directions and are
  reconciled as follows:
  - ACCC FD p.67 records 72 t loads "being **allowed**" on EP — a *permitted ceiling*
    (≈ Type 1 AB-triple at HML), not an average.
  - Viterra's 2019 rail-replacement statement (48 loaded trucks/day moving
    ~2,100–2,200 t/day) implies **~45 t per line-haul load** in actual operation — this
    is the line-haul default.
  - SA average delivered load >29 t in 2016-17 (all regions, incl. small farm semis)
    bounds the farm→site blend from below; 38 t reflects EP's better road-train access.
- **Known gap (added after review)**: the GTSN **Truck Book** also lists **Type 2** road
  trains (53.5 m) that SA permits to **132.83 t CML / 142.28 t HML** — roughly 85 t net,
  nearly double the line-haul default. Whether EP highways are on SA's pre-approved
  53.5 m network is unresolved (data/trucks.md open question 7). Until it is, 45 t is
  the *operationally anchored* figure and 85 t the *legal ceiling*.
- **Sensitivity**: farm→site payload is linear on truck counts and largely absorbed by
  the fitted fleet size (see A1 note in docs/calibration_report.md). Line-haul payload is
  NOT absorbed: it drives truck-km directly, and the rail scenario's headline saving
  falls from ~2.2 M truck-km (45 t) to ~1.1 M (72 t) to ~0.8 M (85 t) on 2025/26. Loaded
  tonne-km — and therefore the freight dollar figures — barely move, since the same
  grain travels the same distance either way.
- **Upgrade path**: operator turnaround/weighbridge data; truck-spec tare sheets; RAVnet
  53.5 m network coverage for EP.

## A2 — receival site service times and bay counts
- **Value**: sample + weigh + tip cycle 12 min/truck/bay; **4 tipping bays at an upcountry
  site, 6 at a port terminal** (`countryBays`, `portBays`; both fitted). Since the #22
  refit both sit inside their search ranges; port bays previously fitted to 5, the floor
  of the physical band derived below, which said more about the bound than about the data.
- **Reasoning**: not published anywhere in minutes, so bounded empirically against the one
  published throughput anchor — the Port Lincoln site record of **13,148/13,512 t/day
  (Nov 2020) and 13,675 t/day (2022/23)** — by measuring what bay count reproduces it (see
  below), not by a back-of-envelope rate calculation. A rate calculation doesn't hold here:
  the engine gates farm trucks *dispatching* to a 12 h window (07:00–19:00, `engine.ts`
  `sitesOpenNow`), but bays servicing an already-queued truck are gated only by whether the
  site is open for the season, not by that daily window — they keep tipping past 19:00
  until the queue clears, so there is no single "receival day" length to divide the
  ~340 daily visits by. (An earlier version of this entry assumed a flat 14 h window and
  derived "≥5 bays" from it; that number happened to match measurement, but the arithmetic
  it came from didn't correspond to anything the code does.)
- **CORRECTED 2026-08-19 (was 2 bays upcountry / 4 at ports)**: the earlier values were
  never checked against that record. Measured, the 2/4 configuration peaks at
  **10,285 t/day** at Port Lincoln — 24 % below the published record, i.e. the model
  physically could not reproduce a documented day. At 4/6 it reaches **13,224 t/day**,
  inside the published band. Under-provisioned bays inflated queues (mean 120 min,
  peak 189 trucks), which in turn inflated truck cycle times and therefore the fitted
  fleet size: the calibrator was buying missing site throughput with imaginary trucks.
- **Sensitivity**: drives queue lengths at peak — a headline output — and, indirectly,
  the fitted fleet. Must stay marked assumed in the UI.
- **Bays are no longer what caps Port Lincoln (2026-08-31, issue #20).** They were, under
  the flat 120 kt upcountry capacities: the model's peak grower-receival day at Port
  Lincoln was 13,694 t, at the top of the published band, because Cummins and Tumby Bay
  saturated at 120,000 t and pushed carting past them to the port. Under A4's district
  allocation the lower-EP sites hold 162,900 t, stop being the binding constraint, and the
  peak day fell to **9,950 t** — and adding bays barely moved it (10,502 t at 6 port
  bays, 11,302 t at 7). So the model no longer reproduces the published daily record, and
  the reason is upcountry storage near the port, not tipping capacity at it. Recorded
  rather than tuned away: the earlier agreement rested on a capacity we now think wrong.
  **Re-measured after #22's refit** (which moved the fitted port bays 5 → 6): the peak day
  is **10,160 t**, and the bay count still barely touches it — 10,109 t at 5 bays, 10,160
  at 6, 10,180 at 7. A 2 % spread across the whole physical band is as clean a statement
  as this model can make that tipping capacity is not what caps that port.
  **Re-measured again after #24's fire-danger harvest rule** (A7; same fitted knobs):
  **10,710 t** at the fitted 6 bays — 10,282 t at 5, 10,239 t at 7. The peak day moved 5 %
  because the rule changes which days are lost, and the sweep is now not even monotone in
  bays (7 sits *below* 6, inside a 4 % band) — which if anything sharpens the point: adding
  tipping capacity does not reliably buy throughput here, so it is not the constraint. The
  finding now survives a change of weather mechanism as well as a change of parameter
  vector.
- **Related finding**: with bays under-provisioned the calibration objective is monotone
  in fleet size (more trucks always scored better, to 900+), and only the engine's own
  `QUEUE INSANE` invariant (>400 trucks at one site) bounded it. Fleet size is therefore
  **not identifiable from the weekly regional receivals alone** — it is pinned by site
  throughput and queue plausibility. See docs/calibration_report.md.
- **Queue ceilings (2026-08-31, issues #26/#27).** Three thresholds now bound a queue,
  and a grower who clears none of them leaves the load in the field bin for tomorrow —
  where `onFarmTonneDays` already tracks and prices it (A22):
  1. `queueBalkMin` **240 min** — the wait past which a grower drives to a different site.
     Unchanged: the worst turnaround ever reported on EP is ~4 h (Port Lincoln, Nov 2018
     rail-outage congestion).
  2. `queueBalkMaxMin` **720 min** — the wait past which they stop carting altogether.
     Reached only when *no* reachable site clears (1); one full receival day (07:00–19:00)
     is the longest stretch the model is willing to call a delivery decision.
  3. `siteQueueMaxTrucks` **250** — a physical stop, never relaxed: 250 waiting road trains
     is ~5 km of stationary traffic on a site access road. Not a behavioural number (a
     grower has already balked twice before it binds); it exists so that queue *length*
     cannot grow without bound the way queue *time* is bounded by (2).
  **What this replaced.** (1) was already here, but the site search's fallback pass — which
  ran whenever nothing cleared it — dropped the queue filter *entirely* rather than
  loosening it, so the balk rule bounded nothing precisely when it mattered (#27). Queues
  ran to 460–822 trucks and 15–22 h on lever settings the UI offers, and the
  `QUEUE INSANE` guard above then threw out of `sim.step()` and killed the app (#26).
  Measured over 105 preset/lever/season combinations, the ceilings hold peak queues to
  **≤ 226 trucks and ≤ 11 h**. At the calibrated defaults nothing changed at all: peak
  queues stay 49–105 trucks (1.9–3.5 h, under (1)), and the event-log hash for every
  calibration and held-out season is byte-identical to the pre-fix engine, so no refit
  was needed.
- **Sensitivity of the new ceilings**: none in the fitted seasons (they never bind);
  large in the stress scenarios, where they convert an unphysical queue into on-farm
  holding — which is the honest answer, but note it is the ceilings, not measurement,
  that set how much grain waits at the extremes.
- **Upgrade path**: operator site-cycle statistics (Viterra used to publish average site
  turnaround minutes in some harvest communications — none found archived).

## A3 — farm→site assignment geography
- **Value**: demand generated on CLUM cropping pixels, disaggregated from PIRSA district
  totals; each parcel's farm→site distance emerges from geography (no assumed constant).
- **Reasoning**: no published farm→site distances exist; only site→port (~144 km SA avg).
  District-level disaggregation is the spec's accepted v1 approach (pending operator
  answer to §9 Q2).
- **Sensitivity**: affects truck-km, not tonnage balances.

## A4 — upcountry site storage capacities (Bunge, EP)
- **Value**: the unpublished Bunge upcountry storage total — **2.54 Mt** (max Western
  season receivals 3.267 Mt, 2022/23, minus published Western port storage 0.732 Mt) —
  split between PIRSA districts in proportion to their long-run receivals share, then
  evenly between that district's Bunge upcountry sites:
  **WEP 72,700 t** each (10 sites), **LEP 162,900 t** (6), **EEP 166,200 t** (5).
  Of those 21 sites, the 16 operated in 2025/26 hold 1.985 Mt.
  Published capacities are used as published and are never scaled: Port Lincoln
  395,600 t, Thevenard 335,925 t, T-Ports Lucky Bay 384,000 / Lock 140,000 /
  Kimba 150,000 t.
- **Computed in**: `pipeline/r1_build_sites.py` (`allocate_capacities`), which writes
  `capacity_t`, `capacity_estimated` and `district` onto every feature of
  `sites.geojson`. Long-run share = mean PIRSA district production 2022/23–2025/26 —
  the same window A20 uses — and the district of a site is the LGA polygon containing
  its coordinate (A14, the same mapping and far-west fallback `r4_build_demand.py`
  applies to CLUM cropping cells). The engine reads `capacity_t` directly; the app
  labels every `capacity_estimated` site "(capacity estimated)".
- **Reasoning**: individual EP site capacities are not published; even ACCC redacted
  Viterra's EP storage total ("[c-i-c]"). What district shares add over a flat per-site
  figure is the *density* of the network: WEP grows 29 % of EP production across 10
  sites, EEP 33 % across 5 and LEP 39 % across 6, so a far-west siding is modelled at
  44 % of an eastern silo — which is the direction the ground truth runs (Wirrulla,
  Witera and Poochera against Kimba, Cummins and Rudall).
- **Known limit — within a district every site gets the same number.** Three PIRSA
  districts is the finest geography this repo has: Bunge's receivals reports are
  network-region only (western / central / eastern, where "western" is the whole
  peninsula), so there is nothing to allocate on below district level. Cummins and
  Kapinnie therefore carry the same modelled capacity, which they certainly do not in
  reality. 2025/26 segregation counts hint at the spread (Tumby Bay runs 5, Cummins 4,
  Kapinnie and Yeelanna 1 each) but count grades, not tonnes, so they are not used.
  Dormant sites are given their district's figure and included in the 2.54 Mt: the
  storage exists whether or not it is opened in a given season (A12).
- **Sensitivity**: **binding at the calibrated baseline, not only in bumper years.**
  Under the flat 120 kt guess this entry used to describe, 8 of the 16 operated sites
  peaked at 100–102 % of capacity in 2025/26 (a *reading*, not a target: over-100 %
  fills were possible until #29 — see the ceiling note below) while Kapinnie and Yeelanna peaked under
  10 %, and lifting `upcountryCapScale` to 1.5 on that baseline moved direct-to-port
  share 33.3 % → 24.2 % and peak queue 141 → 75. Direct-to-port share (A9) and T-Ports
  intake are both downstream of where this capacity sits, so the district allocation
  is a structural input and the knobs were refitted with it
  (docs/calibration_report.md). Moving the same 2.5 Mt from flat to district-allocated
  took the 2025/26 baseline from **33.1 % direct-to-port and a 139-truck peak queue to
  30.7 % and 135** (at #22's refit the same baseline reads **30.9 % and 105**, and
  `upcountryCapScale` 1.5 still moves it to 24.3 % and 42 — the lever's direction and
  rough size survive a complete change of parameter vector, and re-measured under #24's
  fire-danger harvest rule the same lever again lands on **24.3 % and 42**, and under
  #29's capacity ceiling on **24.4 % and 42** from a 31.0 % / 102 baseline), and right-sizes the far
  west: Witera, Streaky Bay, Wirrulla and
  Poochera go from 30–56 % peak fill to 64–98 %. It also costs the model Port Lincoln's
  published peak receival day — see A2.
- **These numbers are now a hard ceiling, not a target.** Whichever way a capacity is
  arrived at — published or allocated — the engine holds `stock <= capacityT` at every
  site at every tick (issue #29). It did not before: the storage gate in `chooseSite`
  tested on-site stock only, so any number of trucks could read the same nearly-full site
  as "room for me" in a single tick, all get dispatched, and all tip on arrival — nothing
  stops a truck once it has left the farm. Measured on 2025/26 seed 42: **six of the
  sixteen operated sites peaked at 100.1–100.9 % of capacity at the calibrated baseline,
  and eleven at 100.1–102.2 % under the +30 % bumper preset, ports included** (Thevenard
  102.2 %, Port Lincoln 101.8 %, Lucky Bay 101.0 %). Small overshoots, but published
  tonnages reported as exceeded, and the site panel showed them as such —
  "343,207 t of 335,925 t" — while the map's fill ring clamped at 100 % and hid it. A
  farm truck now reserves its load against the destination's storage when it is
  dispatched and releases the reservation when it tips, and line-haul checks that
  reservation before unloading at a port, so committed-but-undelivered tonnage counts
  against capacity exactly as tonnage on the ground does. Sites still fill to within one
  truckload of capacity — the constraint binds as hard as it did — they just no longer
  pass it. `Sim.capacityBreaches` counts any site-day above capacity and is asserted zero
  across the whole preset/lever regression sweep.
- **History**: until 2026-08-31 this entry described the allocation above but the engine
  implemented a flat 120,000 t for every Bunge site and 145,000 t for T-Ports
  (`engine.ts`), i.e. only the 2.5 Mt total was real — 21 × 120 kt = 2.52 Mt — and none
  of the district proportionality (issue #20). The flat constants survive only as a
  fallback for a bundle built before that fix.
- **Upgrade path**: operator data; or per-site bunker/silo footprint digitisation from
  aerial imagery — the one route to a genuine within-district spread.

## A5 — road speeds by class (loaded grain truck)
- **Value**: trunk/primary 90 km/h, secondary 80, tertiary 70, unclassified 60,
  residential 40; ±0 for empty legs (same).
- **Reasoning**: SA road-train limit 100 km/h (Eyre Hwy) / 90 km/h elsewhere (2011 DTEI
  guide, historical); loaded B-doubles practically cruise below limits on rural seal.
- **Sensitivity**: linear on cycle times; absorbed partly by fleet-size calibration.
- **Distances are routed, not inferred from these speeds**: `pipeline/p2_build_matrix.py`
  carries the OSM network distance along each fastest path out beside the minutes
  (`matrix.json` `site_km` / `cluster_site_km`), and the engine accumulates those km. Do
  not reintroduce a `km = minutes x speed` shortcut anywhere: until 2026-08-31 the engine
  used a single flat 75 km/h for exactly that (issue #10), which understated trunk
  line-haul ~15 % and overstated slow low-class farm legs by up to 25 %. Fixing it raised
  the measured road task ~12 % (baseline 2025/26: 300 -> 336 M tonne-km, 17.5 -> 19.5 M
  truck-km). Realised leg speeds now span 40-91 km/h, median ~82 (farm legs) / ~86
  (site->port). `travelTimeScale` is a speed lever and moves minutes only; a road-closure
  detour scales both, since a detour is longer as well as slower.
- **Road-closure corridors (scenario switch, `roadClosure`).** A closed corridor is a
  polyline traced along the highway's real OSM alignment, not a straight line between two
  towns (`packages/sim/src/corridors.ts`); a leg is scored on the share of its own routed
  path (`paths.json`) that falls within ~5 km of that alignment, and its minutes and km
  are scaled by `1 + share x (factor - 1)`. BOTH legs of the chain are scored — farm to
  site and silo to port. Until 2026-08-31 (issue #28) only the farm leg was, so silo->port
  road trains ran a closed corridor at full speed, and the test was whether a leg's
  straight-line MIDPOINT fell within 0.18 deg of a straight-line axis, which missed legs
  running the corridor end to end and caught legs that merely passed near its middle. The
  x2.5 factor itself remains an ASSUMED penalty on the closed stretch: the model
  identifies which legs used the road and how much of each did, but does not route the
  alternative path, so a detour's real cost is not measured.

## A6 — climate source: ERA5 (open-meteo) instead of SILO/BOM point data
- **Value**: daily rain/tmax/RH/wind at 8 district points from the open-meteo ERA5
  archive (CC-BY 4.0).
- **Reasoning**: SILO's API requires an identifying email; none could be supplied in an
  autonomous run. ERA5 reproduces the harvest-relevant signal (multi-day rain events,
  heat days) at district scale.
- **Sensitivity**: harvest-pause timing ±1 day vs station obs; acceptable for weekly
  calibration.
- **Upgrade path**: swap in SILO patched-point (same schema) when an operator email is
  provided — single fetch script change (`pipeline/r5_fetch_climate.py`).

## A7 — harvestable-day rule
Until 2026-08-31 this entry described a rain threshold and a flat hot-day cut, which was
roughly half of what the engine ran, and named a temperature mechanism the engine should
never have used (issue #24). It is now written against the code. Everything below is in
the `weatherFactor` block of `packages/sim/src/engine.ts`, except the maturity shift,
which is flagged as such.

**What the daily harvestable fraction actually is.** One number per district per day,
`0 … 1`, from the ERA5 district series of A6. It scales *two* things, not one: the
tonnes a parcel gives up that day, and — separately, at ~0.75 weight — the probability a
grower attempts a delivery at all. EP harvest is largely header-direct to site with
little on-farm buffering, so receivals track the weather with barely a lag; that second
use is why a wet week shows up in the published weekly receivals and not just in the
harvest curve.

- **Rain — stop (`rainStopMm`, default 5 mm; app lever)**: factor `0` if the day's rain
  ≥ 5 mm, or if the day plus the day before ≥ 10 mm.
- **Rain — half-rate band**: otherwise, factor `0.5` for a day of 2 mm to 5 mm
  (`0.4 × rainStopMm` up to the stop threshold). A shower costs a morning, not a day.
  *This band was never in the published entry.*
- **Rain — hangover**: then `× 0.3` if *yesterday* had ≥ 8 mm, else `× 0.5` if the day
  before that did (`1.6 × rainStopMm`). Paddocks stay too wet to carry a header after a
  real fall, and this is the rule that produces the multi-day dips in the weekly curve
  rather than single-day notches. *Also never in the published entry.* Every rain
  threshold scales off `rainStopMm`, so the app's one slider moves the whole rain rule
  coherently.
- **Fire danger — harvest ban** (replaced the flat tmax rule 2026-08-31): see below.
- **Spring-dryness maturity shift** — **not part of the harvestable fraction at all.**
  Total Sep–Oct district rain shifts every parcel's ripening date by
  `clamp((springRain − 45 mm) × 0.25 d/mm, −12, +10)` days: a dry spring ripens the crop
  early, a wet one holds it back. It is applied once, to `parcelMaturity`, and so moves
  *when* the season starts rather than what any given day yields. It has always been in
  the engine and has never appeared in this register; it is listed in
  docs/calibration_report.md's structural-features paragraph.

### The fire-danger harvest ban (replaces "cut 25 % when tmax ≥ 38 °C")
- **Value**: harvesting is suspended while the **McArthur Mark 4 Grassland Fire Danger
  Index exceeds 35** (`harvestBanGfdi`), evaluated at full curing from the day's
  temperature, humidity and wind.
- **Source of the threshold — published, not fitted**: CFS / PIRSA / Grain Producers SA
  **Grain Harvesting Code of Practice** (Sept 2023), *Required Practice 1*: "Suspend
  grain harvesting operations when the local actual GFDI exceeds 35." That code is the
  basis for the district harvesting codes EP growers actually operate under, and SA
  retained the 35 threshold at its most recent review. `harvestBanGfdi` is therefore an
  **assumption lever, deliberately not a calibration knob** — fitting it would throw away
  the one hard number in this entry.
- **Source of the index**: McArthur Mark 4 grassland meter in the equation form of
  Purton (1982), *Equations for the McArthur Mark 4 grassland fire danger meter*, BoM
  Meteorological Note 147 (the meters were first reduced to equations by Noble, Bary &
  Gill 1980, *Aust. J. Ecol.* 5:201–203):

  `GFDI = 2.0 exp(−23.6 + 5.01 ln C + 0.0281 T − 0.226 √RH + 0.633 √U)`

  with C = curing %, T = °C, RH = %, U = 10 m wind km/h. **C = 100 %** — a ripe crop
  standing ready for the header is fully cured by definition, and it is what the
  published cease-harvest tables assume.
- **Validation**: the district codes publish the threshold as a table of the wind speed
  at which to stop for a given temperature and humidity. This implementation reproduces
  the entries reported from it to within ~3 index points — 35 °C / 14 % RH / 26 km/h
  → **34**, and 40 °C / 15 % RH / 26 km/h → **38**, against the code's own **35**. The
  match is what confirms both the coefficients and the C = 100 choice; at any lower
  curing the index would fall far short of the published table.
- **Why the old rule was wrong, not merely coarse**: temperature alone is the weakest of
  the three inputs. Over the four modelled seasons the two rules disagree on **77 of the
  1,260 district-days** in the Oct 26 – Feb 7 window: **24 days at or above 38 °C carry no ban**
  (up to 41 °C with a 20 km/h breeze scores ~24 — a good harvest day, and growers treat
  it as one), and **53 ban days never reach 38 °C** (one is 22 °C with a 47 km/h wind
  over cured stubble, GFDI 36 — grassland fire danger is wind-driven). The old rule was
  taxing the wrong days.
- **How much of a day a ban costs**: the code *suspends* harvesting while the index is
  over the line; it does not write the day off, and growers get grain off early in the
  morning and again in the evening once the wind drops. GFDI traces a diurnal arc, near
  zero overnight and peaking mid-late afternoon. Approximating that arc as a cosine of
  peak height `g`, the share of it above the trigger `gb` is `(2/π)·acos(gb/g)`, and the
  factor is cut by that share. It is 0 for a day that only just touches the trigger,
  ⅓ at GFDI 40, ½ at 50, ⅔ at 70, → 1 for a catastrophic day. **This introduces no free
  constant beyond the published trigger.** It is, however, the one modelled shape in the
  rule rather than a measured one.
- **Inputs that were dead payload until now**: `rh_min_pct` and `wind_max_kmh` have
  shipped in `weather_*.json` since the bundle was first built and were read by nothing.
  They are now both load-bearing. The same wind series is what a Lucky Bay
  transshipment-downtime rule would need (backlog item, T-Ports' published >21 kn limit);
  it remains unused there.
- **Known biases, in the order they matter**:
  1. **Daily extremes, not simultaneous readings.** The code of practice means the
     *local actual* GFDI, from concurrent temperature, humidity and wind. The bundle carries daily tmax,
     daily minimum RH and daily maximum 10 m wind, so this computes the day's
     worst-case combination. Those three do broadly coincide in the afternoon of a hot
     north-westerly — which is when bans are called — but on other days the peak is
     overstated.
  2. **ERA5 wind is smooth.** A ~25 km reanalysis cell averaged again over the A6
     district points under-represents point wind speeds, and wind enters the index under
     a square root with the largest coefficient. This biases the index **low**, i.e.
     towards too few ban days, and pulls against bias 1.
  3. **Declared Total Fire Bans are not modelled.** On a TFB day harvesting is
     prohibited outright under the *Fire and Emergency Services Act 2005*, whatever the
     realised weather; here an extreme day is only ever a large partial loss. A TFB is a
     forecast decision over a whole fire-ban district and is not recoverable from
     reanalysis, so it is left out rather than guessed at.
  4. **GFDI itself is superseded.** AFDRS replaced it with the Grassland Fire Behaviour
     Index in 2022. The *harvesting* code still runs on GFDI 35, so GFDI is the correct
     index for this particular rule, but it will not match a modern fire-danger rating.
- **Realised in the model (measured 2026-08-31 over Nov 1 – Jan 31, all four seasons)**:
  **91 ban days in 1,104 district-days (8.2 %)**, 2–13 per district-season — the right
  order for EP, where growers report a handful to a dozen stopped days a year. Mean
  harvestable fraction over that window moves **0.863 → 0.846**, i.e. about **two extra
  lost days per district-season**.
- **The rule is fit-neutral, and that is the honest headline.** At an unchanged parameter
  set, swapping the temperature cut for this one moves the calibration objective
  1.0800 → 1.0829, season totals by ≤ 0.1 pt, and weekly RMSE by ≤ 1 point on every
  season (40 → 41 %, held-out 64 → 64 %, 66 → 66 %). It fixes *which* days are lost, and a
  ~90-day harvest window absorbs the redistribution of ~2 days. It was adopted because
  the mechanism is right, not because it fits better — and the refit it triggered was run
  and then **rejected** on held-out and A9 evidence. That whole decision is written up in
  docs/calibration_report.md and docs/PROGRESS.md; the fitted knobs are still #22's.
- **Sensitivity**: `rainStopMm` (2–10 mm) is the dominant lever — rain zeroes days
  outright while a ban costs part of one. `harvestBanGfdi` is exposed for sensitivity
  but is not in the app UI; lowering it towards 25 is the way to probe bias 2.
- **Upgrade path**: BoM station observations (Port Lincoln, Cleve, Minnipa, Ceduna AWS)
  at 3-hourly resolution would remove bias 1 and most of bias 2 and allow a true
  hours-above-threshold count instead of the cosine approximation; CFS Total Fire Ban
  declarations by fire-ban district — the EP districts map cleanly onto WEP/LEP/EEP —
  would close bias 3 with recorded fact instead of a formula.
- **Calibration status**: fitted, repeatedly — not "to be calibrated in Phase 3", which
  is what this entry's heading said until 2026-08-31 and had not been true since Phase 3
  closed; the model has since been refitted for #20 and #22 as well. Neither of this
  entry's own values is fitted: `rainStopMm` is a registered assumption and
  `harvestBanGfdi` is a published threshold. The knobs that absorb this rule
  (harvest-rate scale, maturity shift, ramp days) were re-searched for #24 and left at
  their #22 values — see the rejection above.

## A8 — AIS berth-visit derivation parameters
- **Value**: berth geofence = 400 m around the empirically-clustered berth point
  (-34.7155, 135.8700); stationary = ≤0.5 kn; visits merged across gaps ≤16 h; minimum
  visit 3 h / 2 pings; anchorage = stationary ≥1.5 km from berth within zone.
- **Reasoning**: berth cluster contains 7,746 stationary cargo pings; 16 h merge
  compensates the Feb–Apr 2024 half-day data gaps; monthly totals then agree ±1–2 with
  Flinders' official Dry Bulk call counts.
- **Sensitivity**: ±1 visit/month at margins; validated against official counts.

## A9 — direct-to-port share prior
- **Value**: 25 % of receivals direct to port (calibration prior, range 15–35 %).
- **Reasoning**: ESCOSA 2019: "~75 % of Viterra receivals go to upcountry sites". EP has
  a large port-adjacent catchment (lower EP), so Western share may be higher. Free
  parameter in calibration.
- **This is a prior on an OUTPUT, not on a knob.** Nothing in the model sets the share
  directly. `portAttractBias` is the fitted knob; the share falls out of it together with
  the A4 storage allocation and the Huff choice radius — which is why the A4 capacity
  lever moves it further than the attractiveness knob does.
- **Realised in the model (measured 2026-08-31 at the #22 parameter set, seed 42)**:
  2023/24 **26.6 %**, 2024/25 (held out) **24.4 %**, 2025/26 **30.9 %** — grower tips at
  the two Bunge port terminals as a share of all Bunge grower tips (line-haul deliveries
  are not receivals and are excluded). All three sit inside this entry's 15–35 % band;
  the two non-drought seasons sit above the 25 % central figure, in the direction this
  entry's own reasoning predicts. The numbers are stable across refits: they read
  26.2 / 24.4 / 30.7 % at the pre-#22 parameter set, i.e. they barely moved while eleven
  of twelve knobs did — and **26.6 / 24.4 / 30.9 %**, unchanged to the last digit, after
  #24 replaced the harvest-day weather rule at those same knobs. Under **#29's capacity
  ceiling** (again the same knobs) they read **26.6 / 24.5 / 31.0 %** — one tenth of a
  point on two of three, comfortably inside the band, which is the useful surprise given
  that #29 is a change to the storage constraint this entry names as the binding one.
  That binding constraint is
  A4 upcountry storage, not the
  attractiveness knob — `upcountryCapScale` 1.5 takes 2025/26 to 24.3 % (24.4 % under #29).
- **This band did the work of rejecting #24's refit.** Both of that issue's candidate
  parameter vectors pushed the realised share to **33–36 %**, i.e. 2025/26 out the top of
  this entry's 15–35 % range, while improving the calibration objective. Nothing in the
  objective function watches this share; this register entry is the only thing that does,
  which is the argument for recording priors on *outputs* and not only on knobs. See
  docs/calibration_report.md.

## A10 — Thevenard vessel calls: grain share
- **Value**: grain vessels at Thevenard identified by month-weighting AIS calls with
  Flinders' Thevenard monthly grain tonnage (port also ships gypsum/salt/mineral sands,
  which dominate call counts).
- **Reasoning**: AIS cannot distinguish cargo; Flinders Bulk Break gives the grain
  tonnes; grain-vessel count ≈ tonnes / typical parcel (~10–30 kt at 9.8 m draft).

## A11 — T-Ports inland site coordinates
- **Value**: town coordinates (Lock, Kimba); exact pads unpublished (Kimba pad is "east
  of the township").
- **Sensitivity**: ≤ 5 km error on two closed-in-2025/26 sites; negligible **for the
  simulation**, where these are two of 25 sites and the error is small against a cart leg.
- **NOT negligible for the ownership-gap geometry (`pipeline/r8_choice_geometry.py`).**
  Lock and Kimba are the only independent *inland* receival points that have ever existed
  on EP, so in the 2023/24 network state they alone set the "nearest independent point"
  distance for much of the peninsula. A displacement of 5 km — inside this assumption's own
  stated tolerance — moves the 2023/24 headline from 20.3 % to 24.6 % and cuts the
  2023/24 → 2025/26 multiple from 3.3× to 2.72×. The error is asymmetric in **size**, not
  in sign: the swept envelope runs 19.94–24.58 % against a published 20.3 %, so roughly
  +4.3 pp of upside against −0.3 pp of downside, about 13:1. (An earlier version of this
  entry claimed the error "can only ever make the baseline worse, never better"; the sweep
  finds a 19.9 % configuration, so that was too strong.)
- **Upgrade path**: the actual bunker pad coordinates, or an explicit sweep published
  alongside the headline. Until one exists, any figure quoting the 2023/24 level or the
  multiple must carry this range. The 2025/26 level (66.8 %) does not depend on it —
  both bunkers are closed in that state.

## A12 — season site sets
- **Value**: baseline network = the **22** active 2025/26 Bunge sites + 3 T-Ports sites.
  Every site carries `operating_seasons`, the set of seasons in which the operator's own
  weekly report names it receiving grain (`pipeline/r1_build_sites.py`,
  `annotate_operating_seasons`, from `data/processed/receivals_notes.jsonl`).
- **Reasoning**: per-season official site lists aren't archived in machine-readable
  form; ACCC records 21 EP upcountry sites in 2020-21, 25 in 2019-20.
- **Positive evidence only.** A mention establishes that a site OPERATED that season. The
  absence of a mention establishes nothing: reports name a site at its first receival and
  when it is notable, not every week. `operating_seasons` is a lower bound and must never
  be read as a roster. Sentences are required to carry a receival verb, and a name behind
  a locational preposition is rejected — "east of Kyancutta" locates a grower's paddock,
  it is not a receival at Kyancutta.
- **Corrected 2026-08-31 (was wrong in both directions).** This entry previously described
  per-season re-enabling that *no code implemented* — nothing in the pipeline or the engine
  varied the site set by season — and it listed Penong, Darke Peak, Buckleboo and Elliston
  as dormant. They are not: `segregations_2025_26` was read from the live Bunge table on
  2026-08-19, **off-season**, and a site between harvests correctly lists no segregations.
  `r1_build_sites.py` read that emptiness as "dormant" and closed four sites that Bunge's
  own reports name taking 2025/26 deliveries ("Harvest kicked off at our Buckleboo,
  Elliston, Penong, Poochera and Warramboo sites", week ending 2025-11-16; Darke Peak,
  week ending 2025-11-23). This is the same off-season trap already recorded for the cash-
  price board, which lists zero EP sites outside harvest. Only Nunjikompita remains
  dormant, on weak evidence: last named 2023/24, no mention since.
- **Sensitivity**: measured, not asserted. Re-running the v1 scenario set on the corrected
  roster moves every headline by <1 % except two queue figures (road closure +5.3 %, Lucky
  Bay −2.4 %); every ranking and direction of effect is unchanged, so the fitted parameter
  vector was NOT refitted. Operable 2025/26 storage rises ~0.48 Mt (1.99 → 2.46 Mt),
  which the network barely notices at baseline because it is not storage-constrained
  there. Site capacities themselves are unchanged: the A4 pool always included the
  dormant sites.
- **Known open**: `pipeline/r8_choice_geometry.py` still builds its historical network
  states from the single `status` field rather than from `operating_seasons`, so its
  2023/24 column omits Nunjikompita, which was named that season. See
  `docs/roster_audit_2026-08.md`.

## A14 — PIRSA district boundaries approximated by LGA composition
- **Value**: WEP = Ceduna + Streaky Bay + Elliston + Wudinna (+ unincorporated far-west
  cropping strip); EEP = Kimba + Cleve + Franklin Harbour; LEP = Lower Eyre Peninsula +
  Tumby Bay + City of Port Lincoln. LGA polygons: data.sa.gov.au (CC-BY).
- **Used in**: `pipeline/r4_build_demand.py` (district assignment of demand cells) and
  `pipeline/r1_build_sites.py` (district of each receival site, for the A4 capacity
  allocation). Both carry the same LGA→district map and the same far-west fallback;
  change one and change the other. All 31 EP sites resolve inside an LGA polygon except
  Penong, which the far-west fallback picks up.
- **Reasoning**: PIRSA does not publish machine-readable district boundaries. Validation
  against PIRSA sown areas: LEP ratio 1.04 (excellent), EEP 1.29, WEP 2.14 — WEP's CLUM
  cropping mask includes large opportunistically-sown marginal country, consistent with
  PIRSA sowing about half of WEP arable in a given year; allocation is proportional so
  totals are conserved exactly.
- **Sensitivity**: shifts tonnage between adjacent border cells only.

## A15 — T-Ports Lock/Kimba bunkers not operated in 2024/25
- **Value**: T-Ports inland bunker sites closed in the sim for 2024/25 (and 2025/26,
  which IS documented).
- **Reasoning**: 2025/26 closure is published (tports.com/harvest). 2024/25 is
  unverified; with WEP+EEP production at drought lows (0.41 + 0.57 Mt) and the observed
  Bunge Western share at 79.8 % of EP production, material T-Ports inland intake is
  arithmetically implausible.
- **Sensitivity**: without this, the sim under-delivers Bunge receivals ~8-10 % in
  2024/25.
- **Upgrade path**: T-Ports/operator confirmation of 2024/25 site operations.

## A16 — AIS-derived Lucky Bay vessel counts are an upper bound
- **Value**: "Lucky Bay anchorage stays" in `vessel_calls.parquet` (>24 h, cargo class)
  include vessels anchored in western Spencer Gulf for other reasons (e.g. awaiting
  Whyalla berths); they are not used as a calibration anchor.
- **Used in**: vessels_{season}.json (LB arrival schedule is indicative only).

## A17 — carry-in (opening) stocks
- **Value**: each season opens with stocks = that season's Oct+Nov grain shipments at
  Port Lincoln and Thevenard (Flinders statistics), +20 % assigned to upcountry sites;
  commodity split wheat 55 / barley 30 / lentils 15. Per season, Port Lincoln /
  Thevenard: 2022/23 0 / 23,930 t, 2023/24 320,504 / 81,956 t, 2024/25 60,334 / 0 t,
  2025/26 67,585 / 22,050 t.
- **Used in**: engine seeding; `observed_{season}.json.carry_in`.
- **Reasoning**: October–November vessels load almost entirely old crop (new-crop
  receivals only begin mid-October), so those shipments are a season-specific *lower
  bound* on the old crop the ports were holding on 1 October. It is not a stocktake and
  is not presented as one: it counts only old crop that left by ship inside a two-month
  window, so it misses stock still in the shed on 30 November and Flinders'
  separately-reported "Vegetables Legumes and Oilseeds" group — Port Lincoln shipped
  9,652 t of pulses/oilseeds in October 2025 that this figure excludes, even though the
  commodity split then assigns 15 % of carry-in to lentils. Reading it as a measured opening stock also has it
  backwards at the top end: 2023/24's 320,504 t is 81 % of Port Lincoln's published
  395,600 t storage on day one, whereas a real port is drawn *down* before harvest.
  Treat the lever (`carryInScale`) as the honest range, not the point estimate.
- **The seed is CLAMPED at each site's capacity, and the shortfall is reported.** 81 % of
  Port Lincoln on day one at ×1 becomes **162 %** at the lever's top of ×2 — 641,008 t of
  old crop in a shed holding 395,600 t. Until 2026-08-31 the engine seeded it anyway: the
  `seed()` closure had no capacity test of any kind, so a physically impossible opening
  stock went onto the map, into the fill rings and into every capacity-derived reading
  (issue #29). It is now capped at what the site can hold; the surplus (245,408 t in that
  example) is **dropped**, counted in `Sim.carryInClampedT`, and logged as a
  `carry_in_clamped` event naming the site and both tonnages. Only the tonnes actually
  placed enter `carryInT` and the mass balance, so nothing is created or silently lost.
  The overflow is deliberately **not** spilled to a neighbouring site: this figure's
  provenance is specifically *port-held* old crop shipped out of Port Lincoln and
  Thevenard, so relocating it upcountry would invent a location the source says nothing
  about. What a clamp actually reports is that the scaled figure is not physically
  realisable where A17 puts it — which is a finding about the lever's top end, and worth
  surfacing rather than absorbing. It cannot bind at the calibrated ×1 on any built
  season: the largest seed is 81 % of its site.
- **Source coverage**: a Flinders monthly workbook is one sheet covering every Flinders
  port, and the parser keeps only nonzero rows, so "port has no grain row" and "no
  workbook for that month" both arrive as a silent 0. `p2_build_observed.py` therefore
  checks month coverage before summing: a season missing either month falls back to a
  named prior (that port's mean Oct+Nov total over the fully-covered seasons) and says
  so in `carry_in.provenance` and `carry_in.basis`, rather than seeding zero. All four
  built seasons currently have both months present, so every figure above is observed;
  the zeros at Port Lincoln (Oct+Nov 2022) and Thevenard (Oct+Nov 2024) are observed
  zeros — the workbooks list those ports with other cargo but no grain, and Port
  Lincoln took no dry-bulk call at all in October 2022.
- **Sensitivity**: not inert, and not confined to shipping. Carry-in occupies storage
  the engine's capacity gates then police, so it pushes deliveries between sites and
  into the receivals series. Re-measured at the post-#22 calibrated knobs, `carryInScale`
  1 → 0: 2023/24 receivals 1.856 → 1.892 Mt, which moves the season-total error against
  the operator's published figure from −0.4 % to +1.5 % — several times the whole
  post-#22 residual on any season; direct-to-port 26.6 → 24.5 %, peak queue 57 → 39,
  mean vessel wait 28.8 → 31.1 h. 2025/26: 2.247 → 2.268 Mt (−0.1 % → +0.8 % error),
  direct-to-port 30.9 → 28.9 %, peak queue 105 → 80, wait unchanged at 27.7 h. Held-out
  2024/25 barely moves (1.502 → 1.503 Mt) because its carry-in is only 72 kt. The
  earlier claim here — "receivals calibration unaffected (carry-in is never
  'received')" — was false: carry-in is indeed never received, but it displaces what
  can be. (#21 first measured this at the post-#20 knobs, where the same A/B read
  +0.2 % → +2.4 % on 2023/24 and −0.6 % → +0.4 % on 2025/26; the effect survives a
  complete change of parameter vector, which is the point.) **Re-run under #24's
  fire-danger harvest rule** at the same knobs: 2023/24 −0.3 % → **+1.6 %**, direct-to-port
  26.6 → 24.5 %, peak queue 57 → 36; 2025/26 −0.1 % → **+0.9 %**, 30.9 → 29.0 %, 98 → 84;
  held-out 2024/25 still barely moves. Every digit within rounding of the line above — the
  effect now also survives a change of weather mechanism. **Re-run again under #29's
  capacity gates** (same knobs): 2023/24 −0.3 % → **+1.7 %**, direct-to-port 26.6 → 24.5 %,
  peak queue 59 → 38; 2025/26 −0.2 % → **+0.8 %**, 31.0 → 28.9 %, 102 → 86; held-out
  2024/25 1.504 → 1.503 Mt. Within rounding of both lines above, on a third change of
  mechanism — and the mechanism this time is the very one the sentence describes
  ("carry-in occupies storage the engine's capacity gates then police"), now that those
  gates actually hold.

## A18 — road grain freight rate (economics layer, indicative)
- **PUBLISHED SCHEDULE (corrected 2026-08-31 — this, not the app lever, is what may be
  published).** ESCOSA publishes a marginal road-cartage schedule for grain in South
  Australia. Verbatim: *"Only the marginal freight cost has been used, $0.12 ($/tonne-km)
  for up to 50 kilometres and $0.11 ($/tonne-km) for 50 to 250 kilometres."* — Essential
  Services Commission of South Australia, *Inquiry into the South Australian bulk grain
  export supply chain costs — Final Report*, 29 January 2019, Box 5.2 (p. 91). ESCOSA
  sources it to AEGIC, "verified against published Viterra freight rates"; its footnote 289
  attributes the ≤50 km figure to AEGIC, *Australia's grain supply chains: Costs, Risks and
  Opportunities*, October 2018, Note 2c to Figure 4, p. 18, and the 50–250 km figure to
  unpublished **"AEGIC advice"** — so only the first of the two rates traces to a public
  document. Registered as `escosa-marginal-trucking-rate-2019` in `data/SOURCES.md`.
  - **Reproduce**:
    `pdftotext -layout data/raw/reference/escosa_grain_supply_chain_2019.pdf - | sed -n '5405,5412p'`
- **What the rate covers. This is the part that most changes the answer, and it is read off
  the source rather than inferred.**
  - **Marginal, not average.** ESCOSA: *"This is on the basis that once the grower's truck
    is on the road, then only the additional (marginal) cost involved in travelling further
    to the next available site is relevant."* Everything that does not vary with the extra
    kilometres — truck ownership, loading, the trip that would have been made anyway — is
    outside it. It is a rate on the *extra* distance, which is exactly this project's
    question ("what does the missing alternative cost me"). It is **not** a full cartage
    price and must never be presented as one.
  - **One-way loaded kilometres; the empty return leg is not added.** ESCOSA measures "the
    distance between the `closure site' and Gladstone" from Google Maps and multiplies it
    once. All four of its own published results reproduce exactly on that reading and on no
    other: Caltowie 16.3 km → $1.96/t, Yongala 53.0 km → $5.83/t, Gulnare 31.7 km →
    $3.80/t, Jamestown 28.5 km → $3.42/t.
  - **The bands are flat, not tiered.** The rate is selected by the *whole* distance and
    applied to all of it. Yongala at 53.0 km is priced 53.0 × $0.11 = $5.83, not
    50 × $0.12 + 3 × $0.11 = $6.33. Do not build a cumulative tier.
  - **Reproduce both of the above**:
    `.venv/Scripts/python.exe pipeline/r9_escosa_rate_check.py`
  - **Time is excluded, and ESCOSA says so.** *"This case study has not addressed all
    potential costs, such as if the additional travel time resulted in the need for a
    grower to employ an additional truck."* It likewise sets aside site-side turnaround
    ("improving elevator speeds to enable faster truck turnaround"). Queueing, waiting and
    driver time are outside the rate.
  - **The source is SILENT on whether the empty return, loading or waiting sit INSIDE the
    underlying AEGIC cost line.** Searching the full report text for "return leg",
    "backload", "round trip", "one-way" and "empty" returns nothing on point. What is
    established is only that ESCOSA *applies* the rate to a one-way distance. Whether
    AEGIC built the cost line on a round-trip cycle is not stated in any document in this
    repo, and it is worth a factor of two. Report it as an open question; do not resolve it
    by assumption, and do not double the distance to "account for" the return.
- **Base year: 2018 dollars, nominal, and explicitly NOT deflated.** ESCOSA: *"The marginal
  trucking cost rates have not been deflated because it is not known how well the resulting
  deflated costs would reflect the actual costs of the time."* The rate therefore sits at
  the cost level of its AEGIC source (October 2018) as published in January 2019, and
  ESCOSA applies it unchanged to decisions dating back to 2010-11. Call it **2018–19 A$**.
  It is a point figure: no published range, no confidence interval, no per-configuration
  breakdown.
- **Seven years of inflation: publish in the source's own dollars and say so.** No
  indexation is applied here, for three reasons. (1) Escalating a marginal cost line by CPI
  or a road-freight PPI produces a number no publication supports — precisely the
  substitution this project has already had to withdraw twice. (2) The choice of index is
  load-bearing and unjustifiable from anything in this repo; fuel, wages and equipment have
  not moved together since 2018. (3) The one *more recent* published marginal increment
  that exists points the other way, not upward: the Australian Custom Harvesters
  recommended rate card, valid as at 1 February 2026, adds **$0.10/t excl GST per kilometre
  beyond the first 10 km** — below ESCOSA's 2018 $0.11–0.12 on a comparable marginal basis.
  Any indexed figure must be labelled a derived estimate, carry its index and its command,
  and never be the headline. **The headline number is 2018–19 A$/t-km.**
- **No band above 250 km.** The schedule stops there. Legs beyond 250 km — anything routed
  off the peninsula — fall outside it; applying $0.11 above 250 km is an extrapolation, not
  a citation, and must be labelled as one.
- **Used in**: from 2026-08-31, the Tier-2 cartage-dollars output
  `pipeline/r9_cartage.py` (writes `docs/r9_cartage.md` and `docs/r9_cartage.json`),
  which cites the ESCOSA schedule directly and imports its bands from
  `pipeline/r9_escosa_rate_check.py` rather than retyping them. The app takeaways panel still uses the flat working value below.
  **Never in the sim itself**; it carries no fitted parameter.
- **App lever (unchanged by this correction, and NOT a citation)**: A$0.10 per tonne-km
  (range 0.07–0.13), used for the app's indicative freight $ deltas and inside A23's
  premium translation. That is this project's own working value. It happens to sit just
  under the published schedule, which is worth stating as a coincidence rather than as
  evidence. Re-pointing the app at the published bands is a code change with its own
  verification and was not made in this pass. Anything quoted from the app stays
  "indicative"; anything published quotes ESCOSA.
- **What was wrong here, precisely.** This entry previously ended: "No single public EP
  $/t-km schedule exists." Split it in two.
  - **"a public $/t-km schedule ... exists" — WRONG.** One does; it is a regulator's final
    report; it was already cached in this repo at
    `data/raw/reference/escosa_grain_supply_chain_2019.pdf`; and this entry cited that very
    document for a different figure while denying the schedule inside it. Two withdrawn
    claims (`docs/r0_choice_geometry.md:48`, `:284`) quote the sentence as written, and
    their withdrawal does not depend on it — see the note below.
  - **"EP" — RIGHT, and it is the whole of what survives.** The schedule is **South
    Australia-wide**, and the case study behind it is the upper Central region (Gladstone
    catchment, ~16–53 km hauls), not the Eyre Peninsula. No EP-specific $/t-km schedule was
    found. EP differs in both directions — better road-train access (A1) argues for a lower
    marginal $/t-km, remoteness and the post-2019 all-road task for a higher one — and
    ESCOSA disaggregates neither. The accurate statement is now: *a public SA-wide marginal
    $/t-km schedule exists and is used here; no EP-specific one was found.*
  - **This does NOT reopen the 90-minute threshold.** `docs/r0_choice_geometry.md` withdrew
    the cartage ground for designating 90 minutes on two grounds, and only the weaker of
    them was "A18 is not published". The stronger one stands untouched: **a cost rate
    cannot justify a distance threshold**, whoever published it. The schedule is used here
    as what it is — a cost rate applied to distances that are chosen elsewhere.
- **Newer schedule: searched, none found.** Searched 2026-08-31 for any published $/t-km
  grain road-freight schedule postdating January 2019, SA or national. Checked: ESCOSA's
  inquiry page (no successor inquiry or update since the 29 Jan 2019 final report); AEGIC's
  publication listing and the *Australia's grain supply chains* report family (no edition
  later than October 2018 — the 2024 URLs are re-uploads of the 2018 report; aegic.org.au
  refuses automated fetches, so that is a search result, not a document read); ACCC bulk
  grain ports monitoring (ports and capacity only — the ACCC does not collect overland
  grain movements); ABS road freight. Two *more recent* published rate documents exist and
  neither replaces the schedule:
  - **Australian Custom Harvesters**, recommended cartage rates, valid 1 February 2026 —
    "up to 10 km – $16.50 per tonne (excl GST)", then "add $0.10 (excl GST) ... per tonne"
    per further kilometre; "These rates include demurrage"; "These rates are a guide only."
    National, contractor guidance, and a *full* charge with a large fixed component, not a
    regulator's marginal line.
  - **SAGIT / Ag Excellence Alliance, *2026 Farm Gross Margin and Enterprise Planning Guide
    for South Australia*** — "Freight Costs (as included in Gross Margins)": cereal grains
    **$35.00/tonne**, canola $35.00, lentils $38.00, triticale $28.00, on a delivered-port
    price basis. SA and current, but a single flat $/t with **no distance term at all**, so
    it cannot produce a per-district cartage figure.

  Used as a bracket at EP's ~144 km average site→port haul, the three show what the
  marginal rate leaves out: ESCOSA 144 × $0.11 = **$15.84/t** marginal; ACH $16.50 +
  134 × $0.10 = **$29.90/t** full commercial; SAGIT **$35.00/t** budgeted. The marginal
  rate is roughly half a delivered cartage price. That gap is the fixed and time cost the
  marginal rate deliberately excludes — it is not an error in it.
- **Cartage is only half a delivery decision.** Growers deliver where price *minus* cartage
  is best, and this project has no price data (13 days of off-season cash bids; see
  `operator-cash-prices-api` in `data/SOURCES.md`). Every figure derived from this rate must
  say so, and must never be presented as a total grower benefit or loss.
- **Sensitivity**: linear on displayed freight dollars. Between the two published bands the
  spread is 9 % ($0.11 vs $0.12); against the app's working 0.07–0.13 band it is a factor
  of 1.9. Distances are routed (A5), so a road-speed error does not move these dollars —
  only a distance error does.
- **Superseded reasoning (kept so the change is auditable).** This entry previously rested
  on a consistency check — "~144 km average site→port haul ⇒ ≈A$14/t cartage, sitting
  sensibly inside the published $60–75/t whole-of-chain cost at 200 km (AEGIC via ESCOSA
  2019)". The 144 km and 200 km distances are in the ESCOSA text and check out; the
  $60–75/t whole-of-chain figure **could not be re-verified** from the cached PDF, whose
  cost comparisons (Figures 4.3–4.5) are images that carry no extractable text. It is no
  longer load-bearing — the schedule above replaces it — and it should not be requoted
  until someone reads it off the AEGIC report itself.
- **Upgrade path**: an EP-specific or post-2019 published $/t-km schedule; the AEGIC
  October 2018 report itself (Note 2c to Figure 4, p. 18), which would settle whether the
  underlying cost line is one-way or round-trip; and any published EP farm-gate price
  series, without which a cartage figure stays one side of the ledger.

## A19 — vessel waiting cost (economics layer, indicative)
- **Value**: A$30,000 per vessel-day at anchor (≈US$15–25k/day demurrage-equivalent
  for handy-to-panamax bulk carriers, mid-range).
- **Used in**: app takeaways panel only. Labelled indicative; market rates vary widely.

## A20 — provisional 2026/27 live-season demand
- **Value**: district×crop production = mean of PIRSA 2022/23–2025/26 estimates
  (2.88 Mt EP total); carry-in = mean of prior two calendar years' (2024, 2025)
  Oct+Nov shipments.
- **Used in**: `demand_2026-27.json` etc. via `pipeline/p2_build_live.py`.
- **Source coverage**: since 2026-08-31 (#36) the carry-in mean applies the same
  month-level coverage check A17 does (`month_coverage`/`carry_in_window` in
  `p2_build_observed.py`, shared rather than reimplemented): a prior year missing an
  Oct or Nov Flinders workbook is dropped from the mean instead of being summed in as
  a silent 0, which would otherwise halve the estimate whenever this scheduled
  live-refresh job runs against a source gap. Before the fix the two years were
  divided by 2 unconditionally — correct only because both happened to be fully
  covered every time this has actually run.
- **Upgrade path**: replace automatically when PIRSA publishes 2026/27 estimates and
  as live receivals/shipments land (re-run the live builder).

## A21 — rail-reinstatement scenario parameters
- **Value**: 2 trainsets × 1,600 t net, serving only the historically rail-served silos
  (Cummins, Kimba, Wudinna) into Port Lincoln; no timetable — dispatch is demand-driven
  like the road shuttle; combined load/unload handling 4 h; line speed 40 km/h applied to
  the ROUTED distance of the leg (A5), so a trainset covers the same ground as the trucks
  it replaces at 40 km/h instead of that route's road speed — ~2.2× as long on these three
  lines (Cummins 63 km, Kimba 214 km, Wudinna 213 km); road line-haul fleet cut by
  one-third in the scenario. Cycle time = 2 × transit + 4 h handling, which works out at
  **~1.6 cycles/day on the Kimba and Wudinna lines and ~3.4 on the short Cummins run** — 1.4
  per trainset per active day as actually dispatched on 2025/26 (a demand-driven
  shuttle idles when port stocks are covered). There is no hard cycle cap: an earlier
  version of this entry claimed a "≈2 cycles/day ceiling" that the engine never
  enforced and, at road speeds, never observed.
- **Used in**: engine `railReinstated`; "Bring back the trains" scenario.
- **Reasoning**: anchored to the published replacement task — Viterra stated the closed
  railway's work equalled "48 loaded trucks a day" (~2,100–2,200 t/day; ABC, Feb 2019) —
  and ACCC's record that rail carried only the Cummins/Kimba/Wudinna lines. Consist
  size, trainset count, cycle handling time, line speed and the absence of
  track-capacity limits are modelling choices, not citations; the EP narrow gauge was
  slow and speed-restricted, and 40 km/h door to door is a judgement, not a measurement.
  Rail distance is proxied by the road matrix (no rail alignment lengths in the bundle).
  Before the #10 distance fix, train transit was derived from road MINUTES × 75/40, which
  made trainsets faster than 40 km/h on any route whose real road speed exceeded 75; they
  now run against real km, so the A5 road-speed lever no longer moves line speed.
- **Accounting**: trainset tonne-km accumulate in a separate `railTonneKm` counter and
  trainset kilometres are excluded from `truckKm`. Only ROAD tonne-km are priced at the
  A18 cartage rate — the road rate does not describe rail haulage, and the cost of
  rebuilding and operating the railway is not priced anywhere in the model. Trainset
  tonnes are likewise excluded from the corridor truck-flow heatmap, which shows road
  traffic only.
- **Sensitivity**: affects only the rail scenario's truck-km savings and queue relief —
  and those are dominated by the line-haul payload the trains displace (A1): the saving
  falls from ~2.4 M truck-km at 45 t/load to ~1.0 M at 85 t. Report it as a range.
- **Upgrade path**: a real reinstatement proposal (consist sizes, timetable, loop
  lengths) would replace all of this.

## A22 — on-farm holding cost (economics layer, indicative)
- **Value**: A$0.09 per tonne per day for harvested grain waiting on farm before
  delivery (≈ $380/t farm-gate value financed at ~9 % p.a. agricultural overdraft).
- **Used in**: app takeaways ("Grain waiting on farm" row/sentence), driven by the
  engine's cumulative on-farm tonne-days. Never affects sim behaviour.
- **Reasoning**: growers are not paid until grain is delivered/warehoused; delay is a
  financing cost (PIRSA's 2024/25 report notes extended overdrafts under exactly this
  pressure). Deliberately financing-ONLY: weather, insect and quality risks of on-farm
  holding are real but have no public price, so they are named in the UI as unpriced
  rather than guessed.
- **Sensitivity**: linear on the displayed holding dollars; labelled indicative.

## A23 — site-attractiveness ⇄ cash-premium translation (economics layer, indicative)
- **Value**: a Lucky Bay attractiveness multiplier m is displayed as an equivalent cash
  premium of `90 min × (1 − m^(−1/β)) × (80/60 km/min) × A18 freight rate` A$/t, with
  β the calibrated choiceBeta (**2.806** since #22). Default constants: representative
  eastern-EP haul 90 generalized minutes (drive + queue + service), 80 km/h effective
  speed. The "Lucky Bay share ×2.5" scenario sets the lever to an **absolute** 0.885 →
  2.5, i.e. m = 2.5 / calibrated `luckyBayBias` = **2.8×** the fitted baseline, worth
  **≈ +$4/t** at the default 10¢/t·km rate.
- **Two calibrated numbers sit inside this translation, and both move on every refit.**
  m is measured against the fitted `luckyBayBias`, and the exponent is the fitted
  `choiceBeta`; the app reads both from the calibrated set at runtime, so the displayed
  $/t figure changes with a recalibration even though the lever position does not. The
  same lever position computes to $6.67/t at the post-#20 parameter set (β 2.06, baseline
  0.469) and $7.28 at the pre-#20 one (β 1.965, baseline 0.40) — this entry's previous
  "≈ +$6/t" was itself a stale round-down. Treat the figure as an order of magnitude, not
  a price. What it is **not** is anchored
  to a knob clipped at its search bound: `luckyBayBias` fitted to the floor of its range
  (0.40) before #20, sat just above it (0.469) after, and now fits well inside it
  (0.885) — the F22 review's framing of this entry as resting on a pinned value was true
  when written and is no longer.
- **Used in**: app only (Lucky Bay lever readout, scenario story, About). Never affects
  sim behaviour — site choice stays `attract / cost^β` on minutes.
- **Reasoning**: in a Huff-style power-law choice, multiplying attractiveness by m is
  identical to shrinking generalized cost by the factor m^(−1/β); pricing that shrinkage
  at the road freight rate expresses the fitted bias in the units growers actually see
  (a $/t site premium). T-Ports' public launch pitch was precisely price/convenience
  incentives, so the translation direction is meaningful even though the representative
  haul is a modelling choice.
- **Sensitivity**: linear in the representative haul and freight rate; only the
  displayed $/t label changes.
- **Upgrade path**: v2 net-price site choice using the captured daily cash-bid series
  (data/processed/cash_prices/) once a harvest of EP bids exists — then premiums are
  data, not a translation.

## A24 — on-farm retention share (fitted; and what the residual actually leaves it)
- **Value**: `retentionShare` = **0.0553** (fitted; search range 0.05–0.28). The share of
  EP production that never reaches *either* receival network in the season — seed held
  back, on-farm stockfeed, and grain sold into channels the model does not represent
  (domestic mills, container packers).
- **Used in**: `engine.ts` harvest step (`retained = h * retentionShare`, removed before
  any truck sees it); exposed in the app as the "Crop kept on farm / sold elsewhere"
  assumption lever. It is the single largest lever on total network tonnage — the
  deliverable pool, and so season receivals, is linear in `1 − retentionShare`.
- **The 20–23 % residual is NOT this number.** `CALIBRATION.md` records a Western
  receivals ÷ EP production ratio of 0.77–0.80 and calls the residual "on-farm retention
  + T-Ports intake + domestic/container". Read as a check on this knob alone (as the F22
  review read it: "0.10 against an observed 20–23 %") that double-counts, because T-Ports
  intake is a *separately modelled flow* — its own sites, its own fitted `luckyBayBias`,
  its own accounting (`receivedLbT`), and deliberately outside `seasonReceivedT`, which
  is Bunge-only. The model also carries a season-end tail: grain harvested but still on
  farm or on a truck at day 365. Decomposing the observed residual against the run:

  | season | EP prod | obs Bunge receivals | residual | modelled T-Ports | season-end tail¹ | leaves |
  |---|---|---|---|---|---|---|
  | 2023/24 | 2.588 Mt | 1.864 Mt | 28.0 % | 19.7 pp | 2.9 pp | **5.5 pp** |
  | 2024/25 | 1.889 Mt | 1.507 Mt | 20.2 % | 11.7 pp | 3.1 pp | **5.5 pp** |
  | 2025/26 | 2.907 Mt | 2.249 Mt | 22.6 % | 14.3 pp | 2.9 pp | **5.5 pp** |

  ¹ net of A17 carry-in, which enters the same identity from the other side.
  So the honest comparison for this knob is single digits, not 20–23 %. At the *pre-#22*
  parameter set the same decomposition left 9.6–10.3 pp against a fitted 0.10 — which is
  why 0.10 clipped on the old search floor of exactly 0.10: the floor sat on top of the
  answer, not 10 points below it. The review's arithmetic was an oversimplification; the
  *symptom* it flagged was real.
- **Known limit — this knob and `luckyBayBias` are not separately identified.** The model
  obeys `production = retained + Bunge receivals + T-Ports receivals + tail − carry-in`,
  and only the Bunge term is fitted against data. Every tonne taken off retention has to
  reappear at Lucky Bay (or in the tail), so the objective can trade the two at almost no
  cost. Three parameter sets, all fitted the same way, on 2025/26:

  | parameter set | objective | `retentionShare` | T-Ports intake | Bunge total err | held-out 2024/25 |
  |---|---|---|---|---|---|
  | pre-#22 | 1.115 | 0.100 | 0.312 Mt (10.7 %) | −0.6 % | −0.4 % |
  | #22, 300 evals | 1.0802 | 0.069 | 0.407 Mt (14.0 %) | −1.1 % | −3.2 % |
  | #22, 600 evals (shipped) | 1.0800 | 0.055 | 0.416 Mt (14.3 %) | −0.2 % | −0.3 % |

  Down the table retention falls 10.0 → 5.5 % of production while T-Ports intake rises
  10.7 → 14.3 % — the trade, in the open. The last two rows are the sharper evidence: two
  searches over identical ranges, differing only in evaluation budget, reach the same
  objective to three decimals (1.080) at retention 0.069 and 0.055, with held-out errors
  of −3.2 % and −0.3 %. Widening the floor recovered a *direction* (the fit wants less
  retention than 0.10) but not an identified *value*, and the report now flags the knob as
  sitting near its floor rather than presenting 0.055 as a measurement.
- **Plausibility check on the other side of the trade.** Pushing retention down pushes
  T-Ports intake up, and that side does have an external anchor: ACCC records ~20 Lucky
  Bay shipments in 15 months (~16/season) and A16 bounds AIS anchorage stays at ~15/season
  (an upper bound — it includes non-grain anchor calls). 0.416 Mt over ~16 shipments is
  ~26 kt each, a credible transshipment parcel but **at the top of what that evidence
  supports**; 2023/24's 0.511 Mt (bunkers open, A15) is ~32 kt each and higher still. The
  fit is buying part of its Bunge match with T-Ports throughput that nothing in the
  calibration data constrains. Treat both knobs as a *pair* with a plausible joint range,
  not as two measurements.
- **Reasoning for the 0.05 search floor**: 0.10 had no published basis *as a floor* — it
  was the lower end of a plausibility guess, and using a plausibility guess as a hard
  bound is what produced the clipping. 0.05 is below seed plus on-farm stockfeed for a
  cereal-dominant system, so it cannot bind for a physical reason, and it matches the
  lower stop already offered on the app's own retention lever (0.05–0.25).
- **Sensitivity**: near-linear on season receivals — a 1 pp change is ~29 kt on 2025/26.
- **Upgrade path**: published T-Ports intake, or an ABARES/PIRSA on-farm-use estimate for
  EP — either one identifies the pair, because the identity then has only one unknown.

## A13 — vessel arrival schedules for seasons before stem coverage
- **Value**: for seasons where archived stem snapshots are sparse (2021/22–2023/24
  ≈ monthly snapshots), vessel arrivals derive from AIS-observed berth visits instead of
  the stem; stem used for names/tonnages where join succeeds (date-window matching).
- **Reasoning**: stems are rolling snapshots archived ~monthly (65 PDFs, 2021–2026);
  AIS is continuous. Identifier-stripped AIS cannot be joined to names except via dates.
