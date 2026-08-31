# Windrow — Eyre Peninsula Grain Supply Chain Simulation

**Live app: https://tools.justinwong.io/ep-farm-sim/** (also at https://windrow.justinjywong.workers.dev)

An agent-level, browser-based simulation of the Eyre Peninsula (South Australia) grain
supply chain: weather-gated paddock harvest → farm trucks → receival sites → line-haul →
port storage → ship loading at Port Lincoln, with Thevenard and T-Ports Lucky Bay as
alternative gateways. Built entirely on open or freely published data and calibrated
against published weekly receivals and official port statistics. Vessels arrive at the
Boston Bay anchorage at their AIS-observed times and hold for their berth slot, so
ships visibly wait in the ocean exactly as the data shows they did.

**Interact with it:** pick a scenario or drag the what-if levers (crop size, truck
fleet, Lucky Bay pull, port outage, rail reinstated, highway closure); the takeaways
panel translates every change into plain terms — tonnes, queues, ship waiting — and
indicative dollars (freight at 10¢/t·km, demurrage at ~A$30k/vessel-day, farm-gate
value at PIRSA-derived $/t; assumptions A18–A19). A guided tour opens on first visit;
click any site for a drill-down; toggle the truck-flow heatmap for corridor loadings;
export any run as CSV.

> **This is a simulation, not operational data.** Truck movements, queues, site stocks
> and vessel loading progress are modelled. Observed overlays (weekly receivals, port
> statistics, vessel schedules) come from published data; everything else is simulated.
> Every value that is not backed by a published source is registered in
> [`data/ASSUMPTIONS.md`](data/ASSUMPTIONS.md).

## What's in the box

| Piece | Where | What |
|---|---|---|
| Evidence base | `data/` | `SOURCES.md` (14 datasets, licences, retrieval dates), `ASSUMPTIONS.md` (A1–A16), `CALIBRATION.md` (targets + tolerances), `trucks.md`, processed parquet/geojson |
| Data pipeline | `pipeline/` | Python (uv): scrapers + builders, idempotent, polite (≥2 s/host, robots.txt honoured) |
| Sim core | `packages/sim/` | Pure deterministic TypeScript: 5-minute tick engine, seeded sfc32 RNG, daily mass-conservation invariants, unit tests |
| Browser app | `app/` | Svelte 5 + Vite + deck.gl (self-contained vector basemap — no tile server), sim in a Web Worker |
| Write-ups | `docs/` | `PROGRESS.md`, `calibration_report.md`, `scenarios.md` |

Ten seasons of weekly receivals (2016/17–2025/26) were recovered from the Internet
Archive and parse digit-identically to independent re-publications. AIS-derived vessel
calls at Port Lincoln match Flinders Port Holdings' official monthly Dry Bulk counts
within ±1–2 calls/month.

## Run it

```bash
# app (uses the committed data bundle in app/public/data)
npm install
npm --workspace app run dev        # dev server
npm --workspace app run build      # static build -> app/dist

# sim tests + headless season
npm --workspace packages/sim run test
npx tsx packages/sim/scripts/run_headless.ts 2025/26 42

# calibration search (writes packages/sim/src/calibrated.json)
npx tsx packages/sim/scripts/calibrate.ts 100

# scenarios sweep
npx tsx packages/sim/scripts/scenarios.ts 2025/26
```

## Regenerate the data

```bash
uv sync
uv run python pipeline/build_all.py           # rebuild from the raw cache
uv run python pipeline/build_all.py --fetch   # re-fetch everything first (idempotent)
```

Raw downloads are cached immutably in `data/raw/` (git-ignored, ~1.6 GB;
sha256 manifest committed). Every source's URL, retrieval date, licence, and quirks are
in [`data/SOURCES.md`](data/SOURCES.md).

## Deploy (Cloudflare)

The app is a static bundle (no backend, no external APIs at runtime — the basemap is
bundled Natural Earth land + OSM roads, so no tile server either):

```bash
npm --workspace app run build
npx wrangler deploy        # Workers static assets, config in wrangler.jsonc
```

Any static host works: copy `app/dist/` wherever you like.

## What $-shaped questions can it (indicatively) address?

The physical model produces tonnes, kilometres, hours and queues; the app converts
scenario *differences* into dollars using cited or registered unit rates (A18–A19 —
indicative, not a costing model):

- **Freight task**: Δ tonne-km × ~10¢ — e.g. what does a Tod Highway closure or a
  Lucky Bay share shift add to the region's cartage bill? What does rail save?
- **Demurrage exposure**: Δ vessel-days at anchor × ~A$30k — e.g. what does a drought
  against an unchanged export program cost in ship waiting?
- **Farm-gate value at stake**: Δ production × PIRSA-derived $/t (~$375–405) — the
  headline size of a bumper or drought year (a −40 % season ≈ −$440 m farm-gate on
  2025/26 volumes).
- **Not addressed** (needs operator data): storage/handling fees, site operating
  costs, per-grower freight differentials, port charges.

## Live season (2026/27)

The bundle includes a provisional 2026/27 season (A20: 4-season-mean demand, stem-fed
vessel schedule). Refresh it any time — and weekly during harvest — with:

```bash
uv run python pipeline/p2_build_live.py && npm --workspace app run build && npx wrangler deploy
```

`.github/workflows/live.yml` does this on a Monday cron once the repo has a
`CLOUDFLARE_API_TOKEN` secret; PIRSA 2026/27 estimates replace the provisional demand
when published.

## Model in one paragraph

Harvest demand comes from PIRSA district production disaggregated onto ABARES CLUM
cropping pixels (2.5 km parcels, 324 logistics clusters). Each day, weather (ERA5)
gates how much of each ripened crop can be harvested; grain accumulates on-farm, and a
fleet of farm trucks chooses receival sites Huff-style (attractiveness ÷ (travel +
queue time)^β, seeded-random tie-breaks) over a precomputed OSM travel-time matrix,
with queue feedback. Sites have tipping bays, service times, and storage caps;
line-haul trucks keep port stocks ahead of the vessel program; vessels (from AIS-derived
schedules with stem-joined names) berth, load at published shiploader rates, and sail.
Nine calibration knobs are fitted headless against 2023/24 + 2025/26 weekly Western
receivals; 2024/25 (the drought year) is held out for validation.

## Known limitations

- AMSA CTS positions are anonymised and thinned to ≥60 min — berth timings ±1 h; the
  Feb–Apr 2024 extracts cover only ~half of each day (visits merged across gaps).
- Upcountry site storage capacities are not published — each is estimated from its PIRSA
  district's share of long-run receivals, so sites within a district share one figure (A4).
- District-level demand (not paddock-level) in v1; Sentinel-2 segmentation is a stretch goal.
- Vessel names are heuristic date-window joins from ~monthly archived stem snapshots.
- Site service times and truck cycle details are assumptions calibrated in aggregate.
- No carry-in stocks: each season starts empty, so early-season (Oct–Nov) vessels load
  from new-crop only and the simulated shipping year under-ships by roughly the real
  carry-over (~0.2–0.3 Mt).
- The AMSA-derived vessel layer carries a **CC BY-NC 3.0 AU** licence at source — this
  project is non-commercial research; keep it that way or replace that layer.

## Licences & attribution

Roads/facility locations © OpenStreetMap contributors (ODbL). Land polygons: Natural
Earth (public domain). Climate: ERA5 via open-meteo (CC BY 4.0; contains modified
Copernicus Climate Change Service information). Land use: ABARES CLUM (CC BY 4.0).
Vessel traffic: AMSA CTS via AODN/IMOS (CC BY-NC 3.0 AU at source). Receivals reports ©
Viterra/Bunge (via Internet Archive); port statistics © Flinders Port Holdings; crop
reports © Government of South Australia (PIRSA); port determinations © ACCC/ESCOSA.
No affiliation with any of these organisations.
