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

- Held-out 2024/25: season total **−0.4 %** (spec ±5 % ✓); weekly RMSE 63 % of mean weekly
  (timing-dominated; the late-Nov 2024 rain collapse is missing from ERA5 at the A6
  points — documented). Vessel counts = AIS schedule by construction.
- 2023/24 **−1.6 %**, 2025/26 **−1.0 %** (calibration seasons; 2026-08-19 recalibration —
  all three seasons now inside ±2 %, against −2.5 %…+0.7 % before).
- Port Lincoln peak day 14,458 t vs published record 13,148–13,675 t — now reproducible
  (the pre-2026-08-19 bay settings topped out at 10,285 t, 24 % below the record).
- Mean vessel wait 28.3 h vs 26.8 h AIS-observed; peak network queue 139 trucks.
- 2022/23 bumper now exceeds the validity envelope entirely (A4 capacities fill; queue
  guard fires). Already excluded from the UI; recorded as skipped in the report.

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
