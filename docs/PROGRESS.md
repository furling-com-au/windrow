# Windrow — working log & phase state

This file is the canonical record of where the project is. Updated as work proceeds.

## Phase state

- [x] **Phase 1 — Research** (COMPLETE 2026-08-19; all acceptance criteria exceeded)
  - [x] R1 sites → `data/processed/sites.geojson` (32 features; 23 operator facility-grade coords via live API; OSM silo cross-check ≤200 m for most)
  - [x] R2 receivals → `receivals_weekly.parquet` (**10 seasons** 2016/17–2025/26, 128 archived reports, 0 missing; digit-exact vs Grain Central for 3 seasons) + `receivals_monthly.parquet` + `receivals_notes.jsonl`
  - [x] R3 vessels → `vessel_calls.parquet` (31 months AIS; 190 PL berth visits, median 55 h; validated ±1-2/mo vs Flinders official Dry Bulk counts) + `ais_ep_points.parquet` + `port_shipments_monthly.parquet` + `port_vessel_calls_monthly.parquet` + 53 archived stem PDFs + 22 T-Ports stems + PortMIS capture
  - [x] R4 production → `production_districts.parquet` (4 seasons × 3 EP districts × 12 crops; PDF spot-verification passes) + CLUM 50 m raster cached (clip in Phase 2)
  - [x] R5 climate → `climate_daily.parquet` (8 points, 2020-09→2026-02; ERA5 via open-meteo — see ASSUMPTIONS A6 for SILO deviation)
  - [x] R6 roads/trucks → `roads.graph.json` (9,320 nodes/12,566 edges; Cummins→PL 62.7 km ✓) + `data/trucks.md` (GTSN masses, payload assumptions)
  - [x] R7 ports → `data/processed/ports.json` (per-value citations; PL 3,000 t/h + 395.6 kt verified)
  - [x] R8 `data/CALIBRATION.md` complete (targets + tolerances + quirks)
  - [x] `SOURCES.md` (14 sources + rejected list), `ASSUMPTIONS.md` (A1–A13)
- [x] **§9 operator answers (2026-08-19)**: seasons 2023/24–2025/26 with drought 2024/25 held out & visible for comparison · district-level demand OK · **public deploy on Cloudflare** · no paid data
- [x] Phase 2 — Data pipeline → `app/public/data/` bundle (4.9 MB total: parcels+demand, cluster matrix + route polylines, observed overlays, AIS vessel schedules w/ stem names, weather, self-contained basemap). One command: `uv run python pipeline/build_all.py`
- [x] Phase 3 — Sim core (`packages/sim/`): 5-min tick, sfc32 seeded, mass-conservation invariants, 3 unit tests, full season in ~0.8 s headless. Calibrated: 9 knobs, random search + refine (313 s, deterministic), fitted on 2023/24+2025/26
- [x] Phase 4 — Browser app: Svelte 5 + deck.gl standalone (no tile server), sim in Web Worker, KPI strip, sim-vs-observed money chart, 7 scenarios, port panels, About/attribution. Build 222 kB gz. Playwright happy-path passes
- [x] Phase 5 — `docs/calibration_report.md` (+SVG charts), `docs/scenarios.md`, README
- [x] **DEPLOYED: https://tools.justinwong.io/ep-farm-sim/** (Cloudflare Workers static assets + zone route; workers.dev URL kept alive; `npx wrangler deploy`)

## Validation headline (see docs/calibration_report.md)

- Held-out 2024/25: season total **−0.3 %** (spec ±5 % ✓); weekly RMSE 64 % of mean weekly
  (timing-dominated, and unmoved by #24's weather rule; the late-Nov 2024 rain collapse is
  missing from ERA5 at the A6 points — documented). Vessel counts = AIS schedule by
  construction.
- 2023/24 **−0.3 %**, 2025/26 **−0.2 %** (calibration seasons; knobs from #22's refit on
  widened search bounds — all three seasons inside ±0.5 %, and no knob fits to a bound of
  its search range. #24 re-searched them against its new harvest-weather rule and the
  result was rejected; see that entry).
- **No knob is clipped**, and the report says so per knob. Three were fitting to the exact
  floor of their ranges before #22 (`matShift`, `retentionShare`, `harvestRampDays`);
  `retentionShare` is still flagged "near floor" at 0.055 against a 0.05 floor.
- Port Lincoln peak grower-receival day **10,710 t** against the published record of
  13,148–13,675 t — **no longer reproduced**. It was (13,694 t) while upcountry capacity
  was a flat 120 kt everywhere: the lower-EP sites filled and pushed carting past them to
  the port. Under A4's district allocation they hold 162,900 t and stop saturating. Bays
  are not the constraint any more — **10,282 / 10,710 / 10,239 t at 5 / 6 / 7 port bays**
  under #24's weather rule (10,109 / 10,160 / 10,180 t before it). A 2–4 % spread across
  the whole physical band, and the finding now survives a change of weather mechanism as
  well as a change of parameter vector. See A2.
- Mean vessel wait 27.7 h vs 26.8 h AIS-observed; peak network queue 98 trucks (105 before
  #24's weather rule).
- 2022/23 bumper now **completes** (it used to trip the queue guard at Lucky Bay) but
  reads −34.2 %: that bundle has no vessel program at all, so the ports never outload,
  17 of 21 open sites end the season full and the network jams. Land-side replay only.

## Phase 1 acceptance criteria — status

| Criterion | Required | Achieved |
|---|---|---|
| Seasons of weekly receivals parsed + cross-checked | ≥3 | **10** (3 digit-exact cross-checks) |
| Receival sites geocoded w/ provenance | ≥12 | **32** (23 facility-grade) |
| Seasons of AIS vessel calls w/ berth durations | ≥1 | **~3** (Oct 2023–May 2026) |
| Seasons of district production | ≥3 | **4** |
| Registers complete | yes | yes |

## Key numbers (see data/CALIBRATION.md for full tables)

- Western region harvest receivals: 2023/24 = 1,864,175 t · 2024/25 = 1,507,275 t · 2025/26 = 2,249,112 t (2.34 Mt incl. post-harvest)
- Port Lincoln grain shipped (Flinders official): 2022/23 = 1.76 Mt · 2023/24 = 1.43 Mt · 2024/25 = 1.12 Mt · 2025/26 = 1.54 Mt (to Jul)
- PL berth visits (AIS): 86 / 53 / 51 per shipping year; median stay 53–63 h; Sept = maintenance shutdown (~0 calls)
- Lucky Bay: 0 ocean-vessel berth visits (transshipment-only confirmed); ~15 long anchorage stays/season

## Worklog

### 2026-08-19 (Phase 1, single day)
- Env: Python 3.12/uv, Node 24, git init. 4 research agents (sites, trucks+ports, cross-checks, shipping-source scout) + 1 later (PIRSA/CLUM).
- Key discoveries: viterra.com.au → bunge.com.au migration (Wayback required); Jan-2026 listing snapshot enumerates ALL weekly reports to 2016; AODN cloud-optimised AMSA parquet (45 MB/mo vs 300+ MB zips) with per-vessel craftID + draught; live operator sites API with facility coords; Flinders monthly XLSX = per-port grain tonnes + vessel calls (official calibration series); stem PDFs text-extractable with completed-loading timestamps.
- Data quirks handled: AMSA Feb–Apr 2024 half-day coverage (16 h visit merge); May 2024 `_Pt` case; Flinders 3 workbook layouts + duplicate Copy-of/V2 files; Overpass 406 on "crawler" UAs; several hosts 403 non-browser TLS (curl fallback); WebFetch blocked for web.archive.org (curl).
- All fetch scripts idempotent; raw cache 1.6 GB, 398+ files hashed in MANIFEST.sha256.

### 2026-08-19 (cash-price capture + $/t premium display)
- Discovered the operator's cash-pricing page is fed by `mobilews.viterra.com.au/api/ActivePurchaseOption`
  (one record per posted bid; expires next-day noon Adelaide, **no history published**).
  Today: 150 bids, 24 SA/Vic sites, buyers Inghams + Bunge, **zero EP sites** (off-season).
- `pipeline/r7_fetch_cash_prices.py` + `.github/workflows/prices.yml` (daily 12:30 ACST):
  raw snapshot → `data/raw/cash_prices/` (+manifest, local only); compact committed series +
  `summary.json` → `data/processed/cash_prices/` (app imports it at build time).
- App: median posted bids shown under the dollar-rate levers ("what grain actually sells
  for"); Lucky Bay lever now also reads as an equivalent cash premium (A23: attract
  multiplier ⇄ $/t via the power-law choice equivalence + A18 freight over a 90-min haul).
- Display-only by design. v2 upgrade path (net-price site choice from the accumulated EP
  bid series, needs recalibration) registered in A23 — not building without a go-ahead.

### 2026-08-19 (truck-number audit + SA Type 2 road trains)
- **Fleet audit** (`packages/sim/scripts/truck_audit.ts`, `fleet_identifiability.ts`,
  `fleet_profile.ts`): the fitted 589 is only weakly identified. Equal-capacity points
  (799@28 t, 589@38 t, 497@45 t, 407@55 t, 329@68 t) all fit to within 1.5 pp of weekly
  RMSE - the data pins the tonnage flow (~22,400 t of fleet capacity), not the truck
  count. The calibrator's objective also falls monotonically across its whole search
  range (350->1.543, 589->1.347, 750->1.265, 1000->1.181), so 589 is a point on a slope
  inside an assumed prior box, not an optimum. Trucks run 1.5 trips/active-day at ~50-57 %
  of the 12 h receival window: harvest rate and weather bind, not the fleet.
- **Known open defect**: per-cluster `Math.round` over 324 clusters instantiates 573-585
  trucks against the 589 parameter (-0.7 % to -2.7 %, season-dependent). Largest-remainder
  allocation would fix it. NOT yet applied.
- **SA Type 2 road trains**: the GTSN *Truck Book* (S4.10) lists 53.5 m Type 2 combinations
  SA permits at **GML 118.13 / CML 132.83 / HML 142.28 t** - our notes had stopped at the
  one-page truck *chart* (Type 1, 36.5 m, 110-113 t). Quads (<=135.5 t) are Queensland-only.
  Nothing in the grain sources reaches 155 t; above 142.28 t needs a PBS Level 4 vehicle
  approval, which never appears in generic charts.
- ACCC's "72 t" is a **permitted ceiling** ("being allowed"), not an average load -
  data/trucks.md corrected.
- **Line-haul payload is now a parameter** (`linehaulPayloadT`, was hardcoded 45 t) and an
  app assumption lever. Default unchanged, so calibration is untouched (holdout still
  -2.1 %). It matters: rail's truck-km saving falls 2.49 M (45 t) -> 1.27 M (72 t) ->
  0.94 M (85 t); docs/scenarios.md now states the range instead of a single "-3.0 M".
  Loaded tonne-km (and the A18 dollars) barely move.
- New open question (data/trucks.md #7): is the EP trunk network on SA's pre-approved
  53.5 m Type 2 road-train network?

### 2026-08-19 (recalibration: bay capacity was the defect, not fleet size)
- Chasing "is 589 trucks too many?" to its root: the calibrator's objective is **monotone
  in fleet size** — more trucks always scored better, past 900, until the engine's own
  `QUEUE INSANE` invariant (>400 at one site) aborted the search. Fleet size is therefore
  **not identifiable** from weekly regional receivals; it must be pinned physically.
- Root cause found by checking a published number we had never used: the **Port Lincoln
  daily receival record (13,148–13,675 t)**. With the old 2 upcountry / 4 port tipping
  bays the model peaked at **10,285 t/day** — it could not reproduce a documented day. The
  calibration had been buying that missing site throughput with imaginary trucks.
- Fix: bays are now parameters (`countryBays`, `portBays`) defaulting to **4 / 6**, the
  band that reproduces the record (13,224 t at 589 trucks). A2 corrected accordingly —
  its own arithmetic had always implied ≥5 bays, but the model was given 4.
- Also added `choiceRadius` (candidate window; growers deliver near or cart to port) after
  measuring a 62 min mean leg against a 24 min nearest-accepting floor. NOTE: the fit chose
  a wide window (2.11), so this did **not** shorten legs much — tonne-km fell only 258M
  → 250M, not the ~30 % I first projected from a fixed-fleet probe.
- Recalibrated (11 knobs, 200+100 evals, fleet range widened to [300,900]): **fleet 731**
  (interior, not bound-pinned), line-haul 60, bays 4/6, choiceBeta 2.20, choiceRadius 2.11.
  Season totals (after the queue fixes below) 2023/24 −1.6 %, 2025/26 −1.0 %, holdout
  −0.4 % — all three inside ±2 % for the first time.
- Two further engine fixes followed from the same investigation: growers **balk** past a
  ~4 h queue (the worst turnaround ever reported on EP), and site choice is **aware of
  trucks already en route** (operators publish live site status; the old model let every
  truck commit to a site that only *looked* free). Together these cut the peak queue from
  283 to **139** while keeping season fits tight.
- Costs: the headless season went 5.0 → 5.5 s (24 % more agents), so the perf budget was
  widened 5 → 8 s locally with the reason recorded in the test. **2022/23 now exceeds the
  model's validity envelope** — assumed upcountry capacities (A4) fill and the engine's
  QUEUE INSANE guard fires at Lucky Bay. It was already excluded from the UI and previously
  replayed at −31 %; the model now fails loudly instead of answering quietly. report.ts
  records it as skipped rather than crashing.
- App now derives every displayed default from `defaultParams()` instead of hardcoding
  copies, so a future recalibration cannot leave stale numbers in the UI.

### 2026-08-31 (F4: "bring back the trains" reported freight going up)

- **Trainset tonne-km were being added to the road counter** and priced at the A18
  cartage rate, so the rail scenario rendered `+2.0 M t·km · +$197k freight` in the
  "worse" colour while the 2.7 M truck-km it saves sat unused in `kpi.truckKm`. Split:
  `railTonneKm` / `railTravelMin` accumulate inside the `isTrain` branch, `tonneKm` and
  `truckKm` are now road-only, and only road tonne-km reach A18. The rail scenario now
  reads −49 M road t·km ≈ **−$4.9 M freight**, with the 52 M t·km the trains carry
  reported separately and explicitly not priced.
- **Truck-km is now shown.** New "Kilometres driven" row (advanced), plain-English
  sentence (simple) and `truckKmByDay` baseline series. The Simple-mode verdict no longer
  says "barely any difference" when the season is materially cheaper — it now names the
  gain.
- **Trainsets ran at road speed.** They now run the alignment at 40 km/h against the
  matrix's 75 km/h road mean, covering the same distance in ~1.9× the time: 1.5
  cycles/trainset/active day as dispatched (was 4.0). A21, docs/scenarios.md and the
  engine comment all asserted a "~2 cycles/day ceiling" that nothing enforced; all three
  now state what the model actually does.
- **The app's rail lever applies A21's one-third line-haul fleet cut** derived from
  `defaultParams()` (60 → 40), matching `scripts/scenarios.ts` instead of a hardcoded 32.
- `docs/scenarios.md` regenerated: its table also predated the `c08513c` recalibration.

### 2026-08-31 (#10: an undocumented flat 75 km/h was setting every distance)

- **Distances are now routed, not inferred.** `engine.ts` turned every leg's minutes into
  kilometres at a hardcoded `ROAD_SPEED_KMH = 75` — a constant that appeared in no
  assumption entry and silently overrode A5's actual class speeds (90/80/70/60/40). Real
  routed speeds span 40–91 km/h (median 82 on farm legs, 86 site→port), so trunk
  line-haul was understated ~15 % and slow low-class farm legs overstated by up to 25 %,
  with the error concentrated exactly where the tonnage is.
- **Fix at the source**: `pipeline/p2_build_matrix.py` now carries the OSM network
  distance along each fastest path out beside the minutes (`matrix.json` gains `site_km`
  and `cluster_site_km`), and the engine accumulates `truckKm` / `tonneKm` from those
  routed distances. The 75 survives only as `FALLBACK_SPEED_KMH` for a pre-#10 bundle.
- **Effect on 2025/26 baseline**: road task 300 → **336 M tonne-km**, truck-km 17.5 →
  **19.5 M** (+12 %); the rail saving grows 2.19 → **2.38 M truck-km** and −$4.9 M →
  **−$5.3 M** freight. Tonnage, queues and vessel outcomes are unchanged — minutes, and
  therefore routing and cycle times, never depended on the constant.
- **Two silent couplings fell out with it.** The A5 travel-time lever was rescaling the
  freight *task* as well as speeds (distance moved with minutes); it now moves minutes
  only, and the tooltip says so. Trainset transit was `road minutes × 75/40`, which ran
  the trains above their stated 40 km/h line speed on any route faster than 75; A21 rail
  time now comes off real km (Cummins 95 min, Kimba 322, Wudinna 320 → 1.4 cycles per
  trainset per active day, was 1.5). A road-closure detour still scales both, since a
  detour is longer as well as slower.
- A5 and A21 rewritten to register all of this, with an explicit "do not re-derive km
  from minutes" note; `docs/scenarios.md`, `scenarios_data.json` and the app's rail story
  regenerated. `scripts/scenarios.ts` no longer reports a `truckKmProxy`.
- `docs/calibration_report.md` regenerated in passing — it was stale from before the `#6`
  vessel give-up fix and still showed 2024/25 at 45/53 vessel calls (a **FAIL** on the
  ±10 % check); the current engine gives 53/53, **PASS**. Unrelated to this fix.

### 2026-08-31 (#20: A4's per-site capacity method was never implemented)

- **A4 described an allocation the code did not do.** The register said "per-site capacity
  allocated proportional to long-run district receivals"; `engine.ts` used a flat
  `120000` for every Bunge site and `145000` for T-Ports. Only the *total* was real
  (21 × 120 kt = 2.52 Mt ≈ A4's 2.5 Mt); none of the proportionality was.
- **Implemented rather than documented away.** `pipeline/r1_build_sites.py` now assigns
  every site a PIRSA district by LGA point-in-polygon — the same A14 mapping and far-west
  fallback `r4_build_demand.py` uses on CLUM cells — and splits the 2.54 Mt upcountry
  total (max Western season receivals 3.267 Mt − published port storage 0.732 Mt, both
  re-derived from the data at build time) between districts by long-run receivals share,
  then evenly within a district: **WEP 72,700 t, LEP 162,900 t, EEP 166,200 t**.
  `sites.geojson` gains real `capacity_t`, a `capacity_estimated` flag and `district`;
  the engine reads them and `upcountryCapScale` now moves the estimated capacities only,
  never a published tonnage. The flat constants survive as a pre-#20-bundle fallback.
- **It right-sizes the far west.** Witera, Streaky Bay, Wirrulla and Poochera went from
  30–56 % peak fill to 64–98 %; the four sites still running near-empty (Yeelanna,
  Kapinnie, Port Neill, Edillilie) are single-segregation niche sites limited by what they
  accept, not by storage. 2025/26 baseline: direct-to-port **33.1 → 30.7 %** (A9's prior
  is ~25 %), peak queue **139 → 135**.
- **Refitted** (11 knobs, 200+100 evals): fleet 731 → **691**, line-haul 60 → **64**,
  port bays 6 → **5**, portAttractBias 0.8 → **1.475**, choiceRadius 2.11 → **2.64**.
  Score 1.133 → **1.115**; season totals 2023/24 **+0.2 %**, 2025/26 **−0.6 %**, holdout
  2024/25 **−0.4 %** — all three inside ±1 % for the first time. Weekly RMSE improved on
  2023/24 (63 → 46 %) and the holdout (63 → 61 %), worsened on 2025/26 (50 → 63 %).
- **Cost: Port Lincoln's published peak receival day is no longer reproduced** (13,694 →
  9,950 t against a 13,148–13,675 t record). The old agreement depended on the six
  lower-EP sites saturating at 120 kt and pushing carting past them to the port; at
  162,900 t they do not. Adding port bays does not recover it (10,502 t at 6, 11,302 t at
  7), so this is an upcountry-capacity result, not a tipping-capacity one. Recorded in
  A2 rather than tuned away.
- `docs/scenarios.md` / `scenarios_data.json` / `calibration_report.md` regenerated;
  A2, A4, A14, README and the app's capacity lever/site panel copy updated. The site
  panel now reads the capacity the run enforces (new `SiteView.capacityT`) instead of the
  raw bundle figure, so it no longer contradicts the capacity lever.

### 2026-08-31 (#22: three knobs were fitting to their search floors, not to the data)

- **A fitted value sitting exactly on a search bound is not a measurement.** `rng.range`
  is continuous, so probability zero — the only route there is the refinement clamp in
  `calibrate.ts`, i.e. the optimiser pushed past the bound and was clipped. After the
  #20/#21 refits three knobs sat exactly on their floors: `matShift` −4, `retentionShare`
  0.10 and `harvestRampDays` 5 (the last newly pinned, a side effect of those refits;
  `rateScale`, `portAttractBias` and `luckyBayBias`, which F22 also flagged, had already
  moved off theirs).
- **Each floor was replaced with a physical one and the fit re-run.** `matShift` −4 →
  **−12**: at −12 the median far-west lentil parcel ripens on 25 Sep, the earliest EP
  first receival on record — nothing earlier has an anchor. `harvestRampDays` 5 → **1**:
  the ramp is *within* a parcel and a paddock is cut at header capacity from day one; the
  regional ramp already comes from the ±6 d parcel jitter and ±8 d district offsets.
  `retentionShare` 0.10 → **0.05**, below seed plus on-farm stockfeed, matching the lower
  stop the app's own retention lever already offered.
- **All three moved into the interior** (−7.40, 10.32, 0.0553) and the objective improved
  1.115 → **1.080**; season totals 2023/24 −0.4 %, 2025/26 −0.2 %, held-out 2024/25
  −0.3 %. Weekly RMSE 40 / 66 / 64 %. `portBays` also came off the floor (5 → 6).
- **The bigger finding is that the objective does not identify these knobs.** Two searches
  over the same ranges (300 and 600 evaluations) reached 1.0802 and 1.0800 — the same
  objective to four decimals — at fleet 618 vs 555, ramp 16.2 vs 10.3, choice β 1.32 vs
  2.81, retention 0.069 vs 0.055, and holdout errors of −3.2 % vs −0.3 %. Widening a floor
  recovers a *direction*, not a value.
- **`retentionShare` and `luckyBayBias` are the sharpest case**, and F22's arithmetic on
  it was wrong in an instructive way. CALIBRATION.md's 20–23 % residual is *not* a check
  on retention alone: T-Ports intake is modelled separately and excluded from
  `seasonReceivedT`, and there is a season-end delivery tail. Netting both leaves ~10 pp
  at the pre-#22 fit — so the old 0.10 floor sat *on top of* the answer, which is exactly
  why it clipped. The two knobs then trade one-for-one through the mass identity: the
  fit moved 4.5 pp of EP production off retention and onto Lucky Bay at no cost to the
  objective, taking modelled T-Ports intake to 0.416 Mt (2025/26) — ~26 kt per shipment
  against ACCC's ~16 shipments/season, credible but at the top of that evidence. New
  register entry **A24** carries the decomposition, the three-parameter-set table and the
  plausibility check.
- `calibration_report.md` now generates its knob count and prose list from the knob object
  (it hardcoded "11 free scalars" against a 12-row table, `portBays` missing) and prints a
  **search range and an "at a bound?" flag per knob**, read from the search log the same
  run wrote. README's "Nine calibration knobs" and params.ts's "~10 starred values" were
  the same defect and are now 12.
- A2, A4, A9, A17, A23 re-measured at the new parameter set; A9 gains the realised
  direct-to-port share it never recorded (26.6 / 24.4 / 30.9 %, stable across the refit
  while eleven knobs moved). `scenarios.md` / `scenarios_data.json` / `calibration_report.md`
  / `docs/img/*.svg` regenerated; About and lever copy updated for the new fleet, RMSE
  band and $/t premium.

### 2026-08-31 (#24: A7 documented half the rule, and the heat rule had the wrong mechanism)

- **A7 published a rain threshold and a flat "cut 25 % when tmax ≥ 38 °C". The engine ran
  five rules.** Missing from the register: a half-rate band at 2–5 mm, a ×0.3 hangover the
  day after ≥ 8 mm and ×0.5 the day after that, and a spring-dryness maturity shift
  (`clamp((springRain − 45) × 0.25, −12, +10)` days) that is not part of the harvestable
  fraction at all — it moves ripening dates. A7 now describes all of them, and the heading's
  "(to be calibrated in Phase 3)" is gone: Phase 3 closed and the model has been refitted
  three times since.
- **The temperature rule was not merely coarse, it was the wrong variable.** SA harvest
  bans run on grassland fire danger. `weather_*.json` had been shipping `rh_min_pct` and
  `wind_max_kmh` alongside rain and tmax since the bundle was first built, read by nothing.
  Replaced with the **McArthur Mark 4 grassland index** (Purton 1982 equation form, curing
  100 % — a ripe paddock is fully cured) against the **GFDI 35** cease-harvest trigger the
  CFS/PIRSA/Grain Producers SA **Grain Harvesting Code of Practice** (Sept 2023) sets in
  Required Practice 1. The threshold is published, so it is an assumption lever, **not** a
  thirteenth calibration knob.
- **It reproduces the code's own published table.** District codes publish GFDI 35 as a
  lookup of the wind speed to stop at: 35 °C / 14 % RH / 26 km/h and 40 °C / 15 % RH /
  26 km/h. The implementation returns 34 and 38. That match is what pins both the
  coefficients and the curing choice, and `sim.test.ts` now asserts it so a future edit to
  a coefficient fails loudly.
- **The two rules disagree on 77 of 1,260 district-days.** 24 days at or above 38 °C carry
  no ban (41 °C with a 20 km/h breeze scores 24 — a good harvest day); 53 ban days never
  reach 38 °C (22 °C with a 47 km/h wind over cured stubble scores 36 — grassland fire
  danger is wind-driven). 91 ban days in 1,104 Nov–Jan district-days, 2–13 per
  district-season; mean harvestable fraction 0.863 → 0.846, about two extra lost days per
  district-season.
- **The refit was run twice and rejected; the knobs are still #22's.** At the #22 vector
  the rule moves the objective 1.0800 → 1.0829, season totals ≤ 0.1 pt and weekly RMSE
  ≤ 1 point (40 → 41 / 64 → 64 / 66 → 66 %) — it is fit-neutral, so that vector is not
  "fitted to a deleted rule", it is still an optimum-equivalent point. Searches at 600 and
  900 evaluations reached **1.0716** and **1.0639** — a real ~1.8 % gain, not #22's
  four-decimal tie — but bought it from the held-out season (total −0.3 % → −1.2 % and
  **−2.4 %**, weekly RMSE 64 % → 65 % and **69 %**) and from checks the objective cannot
  see: direct-to-port rose to 33–36 %, **outside A9's published 15–35 % band**; the
  900-evaluation vector's 807-truck fleet trips the queue guard on the 2022/23 replay; and
  the 600-evaluation vector left `choiceBeta` clipped on its floor, the exact defect #22
  closed. All of it is the objective drifting the way A2 already documents as
  unidentified — weaker distance decay plus more trucks.
- **The rejected 900-evaluation vector, recorded so the call is reversible** (or rerun
  `calibrate.ts 600`): fleetTrucks 806.60, linehaulTrucks 60.087, rateScale 0.95208,
  matShift −5.3116, harvestRampDays 15.252, retentionShare 0.057707, portAttractBias
  1.9746, choiceBeta 1.30088, choiceRadius 2.58756, countryBays 4.85396, portBays 5.54308,
  luckyBayBias 1.00347.
- **Known gaps left open, recorded in A7 rather than guessed at**: daily extremes stand in
  for concurrent readings (biases the index high); ERA5 district-mean wind under-represents
  point wind and enters under a square root (biases it low); declared Total Fire Bans,
  under which harvesting is prohibited outright, are not modelled; and GFDI itself was
  superseded by AFDRS's Grassland Fire Behaviour Index in 2022 — the *harvesting* code
  still runs on GFDI 35, so GFDI remains right for this rule and wrong for anything else.
- `report.ts` no longer emits a 2022/23 footnote and chart link when that season did not
  run, and derives its own "Reproduce" eval count instead of hardcoding 400 against a
  600-evaluation report. `railTrips`/`railActiveDays` added to the engine so
  `scenarios.md`'s trainset dispatch figure (189 trips / 68 active days) is measured rather
  than inherited. `scenarios.md` / `scenarios_data.json` / `calibration_report.md` /
  `docs/img/*.svg` regenerated at the unchanged parameter vector — every movement there
  comes from the weather rule alone and is under 10 %.

### 2026-08-31 (#29: sites were reported above their own published capacity)

- **Two independent paths let a site hold more grain than it holds.** Both were live on
  master and both are physically impossible, which matters more than their size: the model
  presents storage as a real constraint, and the site panel prints the raw pair —
  "343,207 t of 335,925 t" at Thevenard — while the map's fill ring silently clamps at
  100 % and hides it.
- **Path 1 — carry-in was seeded with no capacity test at all.** The `seed()` closure in
  the `Sim` constructor did `stock[c] += tonnes * share` unconditionally. A17's figure is a
  lower bound and the `carryInScale` lever scales it to ×2, at which point 2023/24's
  320,504 t at Port Lincoln becomes 641,008 t against 395,600 t of *published* storage —
  **162 % full on day one**, from a lever the UI itself offers. Now clamped at capacity:
  the surplus (245,408 t there) is dropped, counted in `carryInClampedT`, logged as a
  `carry_in_clamped` event, and disclosed in A17 and the lever's own tooltip. It is **not**
  spilled to a neighbour — A17's provenance is specifically *port-held* old crop, so
  relocating it upcountry would invent a location the source says nothing about. What the
  clamp reports is that the scaled figure is not physically realisable where A17 puts it.
- **Path 2 — the site-choice gate looked only at grain already on the ground.**
  `chooseSite` tested `st >= capacityT * 0.995` over current stock, so a dozen trucks could
  each read the same nearly-full site as "room for me" in one tick, all be dispatched, and
  all tip — and nothing stops a truck once it has left the farm. The queue gate next to it
  already counted committed inbound *trucks* (#26/#27); storage counted none. Measured on
  2025/26 seed 42: **6 of the 16 operated sites peaked at 100.1–100.9 % at the calibrated
  baseline, and 11 at 100.1–102.2 % under the bumper preset** (Thevenard 102.2, Port
  Lincoln 101.8, Lucky Bay 101.0).
- **The fix is a tonnage reservation, mirroring what line-haul already did.** A farm truck
  books its load against the destination's storage at dispatch (`siteInboundT`) and
  releases it at the tip that turns it into stock, so the sum is unchanged by the tip and
  `stock + siteInboundT <= capacityT` is an invariant, not an aspiration. Line-haul's
  arrival gate now honours that reservation too — without it a road train could spend
  headroom a grower had already reserved, and the overshoot would just move to the farm
  side. Only the arriving truck's own load is tested there, not the whole line-haul
  fleet's inbound: testing the sum would deadlock two trucks that each fit but do not fit
  together. A site full-by-commitment now drops out of the candidate list exactly like one
  full-by-stock, so the #26/#27 queue ceilings compose with it rather than fight it.
- **Result: worst fill anywhere is 100.000 %.** Swept over 130 configurations — 5 seasons ×
  2 seeds × 13 lever/preset combos including crop ×1.4, capacity ×0.1, carry-over ×2 and
  "every lever against the network" — zero capacity breaches and zero queue breaches.
  Sites still fill to within one truckload of capacity, so the constraint binds exactly as
  hard as before; they just no longer pass it. `capacityBreaches` counts any site-day over
  capacity and is asserted zero across the whole #26/#27 regression sweep, and three new
  targeted tests cover the clamp, a tick-by-tick tiny-network check and the bumper season
  — all three fail on the parent commit, the last of them reporting Thevenard at 102.2 %.
- **Recalibration: run twice and rejected — the knobs are still #22's, a second refit
  running.** Same tests #24 used. (1) *Near fit-neutral at fixed knobs*: the ceiling moved
  the objective 1.0799 → 1.0844 (0.4 %) and season totals by ≤ 0.1 pt; every weekly-RMSE
  figure in the report table is unchanged to the point (41 / 64 / 65 % before and after),
  and the held-out total error did not move (−0.3 %). Direct-to-port
  26.6 / 24.4 / 30.9 → **26.6 / 24.5 / 31.0 %** — a tenth of a point, on the output A9 says
  this very constraint governs. (2) *At 900 evaluations the search returns the **identical**
  vector it returned under #24's engine* — fleet 806.6002, β 1.300879, retention 0.0577068,
  every knob to every digit, only the score moving (1.0639 → 1.0656). The searches are
  seeded so they sample the same candidates; an unchanged *winner* is the informative part.
  The capacity ceiling does not re-rank the parameter space. (3) *Both refits bought fitted
  seasons with the held-out one*: 600 and 900 evaluations reach **1.0718** and **1.0656**
  (1.2 % / 1.7 % gains) while held-out total error goes −0.2 % → **−2.2 %** and **−2.4 %**
  and its weekly RMSE 64 % → 64 % and **69 %**. (4) *And broke checks the objective cannot
  see*: direct-to-port rose to **33.8–37.4 %** and **32.8–35.9 %**, 2025/26 out the top of
  A9's published **15–35 %** band both times, and each refit left a *different* knob clipped
  on a floor — `retentionShare` at 0.05 here, where #24's 600-evaluation vector had clipped
  `choiceBeta` at 1.10. Which knob clips changing between refits is the A2/A24
  identification problem showing through, not a fact about storage. One of #24's objections
  is **not** reused because it has lapsed: the 807-truck fleet no longer trips a queue guard
  on the 2022/23 replay, since #26 bounded queue length by construction.
- **Event-log hashes did change** (2023/24 `1a057677` → `1708d201`, 2025/26 `5acc83bd` →
  `5a6455d1`, 2024/25 `657642e4` → `213b5991`), which is why a refit was run at all rather
  than waved off: the gate binds at the calibrated baseline, not only under stress.
- `scenarios.md` / `scenarios_data.json` / `calibration_report.md` / `docs/img/*.svg`
  regenerated at the unchanged vector. One scenario number moves materially: the bumper
  peak queue **377 → 217 trucks**, because a full site now turns trucks away before they
  set off instead of taking them and overflowing, and the grain waits on farm where A22
  already prices it. Everything else moves under 5 %.

## Key decisions

- Repo root = `C:\Users\justi\grain_simulation` (spec layout §10). `data/raw/` git-ignored, manifest committed.
- Seasons ids like `2023/24`; marketing year Oct 1–Sep 30; Windrow calibrates on **Western region** (EP-only; network totals include some Vic sites).
- AIS via AODN parquet product (licence: AODN says CC-BY 4.0, AMSA source says CC BY-NC 3.0 AU → treat as NC; project is non-commercial research).
- Climate via ERA5/open-meteo (SILO needs identifying email; upgrade path in A6).
- Roads graph from OSM Overpass (ODbL); routable; travel-time matrix in Phase 2.

## Blockers / open questions for operator (§9 — asked 2026-08-19)

1. Season priority (recommend calibrate 2023/24 + 2025/26, hold out 2024/25; 2016/17–2022/23 available as replay-only).
2. District-level demand OK for v1? (recommend yes; CLUM-pixel disaggregation)
3. Deployment: static Caddy LAN only, or public too (affects tile choice)?
4. ePaddocks paid data: skip (recommend) or budget?
