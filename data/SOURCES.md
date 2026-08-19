# Data Sources Register — Windrow

Every dataset used by Windrow. Raw downloads are cached immutably under `data/raw/`
(git-ignored; sha256 integrity manifest committed at `data/raw/MANIFEST.sha256`, 398+
files, ~1.6 GB). Nothing in `data/raw/` is edited in place. Retrieval scripts:
`pipeline/r*_fetch_*.py` (idempotent; polite ≥2 s/host unless stated).

## Context note — Viterra → Bunge domain migration
Bunge completed its acquisition of Viterra 2025-07-02. `viterra.com.au` **pages** now 302
to `bunge.com.au`, but the Viterra AEM **document store** (`viterra.com.au/dam/jcr:...`)
still serves files, and the mobile API (`mobilews.viterra.com.au`) is still live.
Historical pages are only on the Wayback Machine. Checked 2026-08-19.

---

## wayback-viterra-weekly-reports
- **What**: 128 weekly/fortnightly harvest report pages, seasons 2016/17–2025/26 (10
  seasons), each with a table of network total + Western/Central/Eastern weekly and
  cumulative receivals, plus narrative naming busiest sites.
- **URL**: `https://web.archive.org/web/<ts>id_/https://www.viterra.com.au/media/Receivals-reports/Weekly-harvest-reports/<slug>`
  (slugs enumerated from 22 archived listing-page snapshots; latest snapshot per page).
- **Retrieved**: 2026-08-19 · **Licence**: publisher content via Internet Archive;
  research/attribution use. **Cadence**: static archive (weekly during harvest, live).
- **Format**: HTML → `data/processed/receivals_weekly.parquet` + `receivals_notes.jsonl`
- **Notes**: zero pages missing from Wayback. Parsed totals match Grain Central
  re-publications digit-for-digit (3 seasons checked).
- **Local cache**: `data/raw/viterra_reports/`

## bunge-news-api
- **What**: post-migration news/report listing + 26 report article pages (2025/26 weekly
  reports under Bunge branding, monthly receivals reports with shipping statements).
- **URL**: `https://www.bunge.com.au/sitecore/api/ssc/Controllers/Search/1/getarticles?...`
  + article pages. **Retrieved**: 2026-08-19 · **Licence**: publisher content, cited.
- **Format**: JSON + HTML. **Cadence**: monthly (weekly in harvest).
- **Local cache**: `data/raw/bunge_news/`

## operator-sites-api
- **What**: live Bunge/Viterra "Western region" site roster (23 sites) + per-site detail
  (facility lat/lon, manager, harvest hours/status messages).
- **URL**: `https://mobilews.viterra.com.au/api/Sites/GeographicalRegion/Western`,
  `/api/Sites/{guid}`. **Retrieved**: 2026-08-19 · **Licence**: operator-published data
  backing bunge.com.au public pages; used for coordinates/status with attribution.
- **Format**: JSON → `data/processed/sites.geojson` (with `pipeline/manual_sites.json`
  for T-Ports/closed sites + 2025/26 segregations read from the public segregations page).
- **Local cache**: `data/raw/operator_sites/`

## operator-cash-prices-api
- **What**: live daily cash bids ("active purchase options") posted by buyers at
  Bunge/Viterra receival sites — site × commodity × grade × buyer × price × payment
  terms, with `startDate`/`endDate` (bids expire next-day 12:00, so the feed is
  **ephemeral**; no history is published). Backs the public page
  `bunge.com.au/agriculture/delivering-to-sa-vic-sites/cash-pricing`.
- **URL**: `https://mobilews.viterra.com.au/api/ActivePurchaseOption` (plus
  `/api/Commodity`, `/api/SiteGrade` for lookups).
- **Retrieved**: 2026-08-19 (150 bids, 24 sites, buyers Inghams + Bunge; **no Eyre
  Peninsula sites carried an active bid on this off-season date** — EP sites exist in
  `/api/Sites` but had no bids). **Licence**: operator-published data backing a public
  page; indicative prices, attribute Bunge.
- **Used for**: indicative price display in the app (econ panel context line, A23
  Lucky Bay premium translation). Never affects sim behaviour (that's the v2 upgrade
  path in A23). Captured **daily** by `.github/workflows/prices.yml` →
  `pipeline/r7_fetch_cash_prices.py`, because each day's board cannot be re-fetched
  later; compact committed series in `data/processed/cash_prices/`.
- **Format**: JSON. **Local cache**: `data/raw/cash_prices/`

## amsa-cts-aodn-parquet
- **What**: AMSA Craft Tracking System vessel positions (speed, course, draught, type,
  length, anonymised per-vessel `craftID`), monthly files, Oct 2023 – May 2026 (32
  months; Jun/Jul 2026 not yet published upstream).
- **URL**: `https://aodn-cloud-optimised.s3.ap-southeast-2.amazonaws.com/aggregated_amsa_nonqc.parquet/`
  ("Australian SAR Region Vessel Tracking — Aggregated data product", NESP MaC 5.9 /
  IMOS / AODN; metadata uuid 2a5739e7-0cb8-444a-b83b-b2bc841b0c).
- **Retrieved**: 2026-08-19 · **Licence**: AODN/IMOS publish under **CC-BY 4.0**;
  the underlying AMSA monthly extracts carry **CC BY-NC 3.0 AU** on AMSA's own portal.
  ⚠ Treat the combined product as **non-commercial** until clarified; Windrow is
  non-commercial research. Attribution: AMSA + IMOS/AODN.
- **Format**: Parquet (~45 MB/month national) → `data/processed/ais_ep_points.parquet`,
  `vessel_calls.parquet`.
- **Restrictions/notes**: vessel identities (MMSI/IMO/name/callsign) deleted at source;
  positions thinned to ≥60 min/vessel; **Feb–Apr 2024 files cover only ~half of each UTC
  day** (documented in CALIBRATION.md); May 2024 file has a case-variant name.
- **Local cache**: `data/raw/amsa_cts/`

## bunge-shipping-stem (current + Wayback history)
- **What**: daily-updated SA shipping stem PDF (per-terminal vessel queue: capacity ref,
  vessel, nominated/accepted, volume, ETA/slot, ETB/EDL/ETD, commodity, exporter, agent)
  and daily **Loading Statement** PDF (incl. completed loadings with timestamps).
- **URLs**: landing `bunge.com.au/agriculture/client-storage-and-handling-information/shipping`;
  stem `delivery.bunge.com/.../{yymmdd}-shipping-stem.ashx`; statement
  `.../loading-statement.ashx` (stable). History: Wayback snapshots of two Viterra DAM
  UUIDs (`375b51d1…` Nov 2021–Oct 2024, `ec53083b…` Oct 2024–present) — 53 unique PDFs,
  ≈ monthly granularity.
- **Retrieved**: 2026-08-19 · **Licence**: published by Bunge Operations "in accordance
  with the Port Terminal Access (Bulk Wheat) Code of Conduct"; public disclosure docs.
- **Format**: PDF (text-extractable; parse in Phase 2). **Cadence**: each business day.
- **Notes**: `delivery.bunge.com` serves 403 to non-browser TLS fingerprints; fetched
  via curl with a desktop UA (no robots.txt exists on either bunge host).
- **Local cache**: `data/raw/stems/wayback/`, `data/raw/stems/current/`

## tports-shipping-stem
- **What**: T-Ports Lucky Bay/Wallaroo shipping stem ("Loading Statement for Web
  Portal") — 22 archived PDFs 2021–2026 + current (terminals closed for maintenance
  15 Aug – 31 Oct 2026).
- **URL**: `tports.com/wp-content/uploads/{YYYY}/{MM}/Loading-Statement-for-Web-Portal-{YYYYMMDD}.pdf`
  (+ Wayback). **Retrieved**: 2026-08-19 · **Licence**: public disclosure documents.
- **Local cache**: `data/raw/stems/tports/`

## flinders-port-statistics
- **What**: Flinders Port Holdings monthly statistics workbooks 2022–2026 (55 monthly +
  8 annual archives): per-port bulk cargo tonnes by commodity (incl. Grain
  wheat/barley/etc.) and per-port monthly vessel calls by class.
- **URL**: `https://www.flindersportholdings.com.au/port-statistics/` →
  `/wp-content/uploads/...xlsx`. **Retrieved**: 2026-08-19 · **Licence**: publicly
  published statistics; attribution. robots.txt allows all with `Crawl-delay: 10`
  (honoured; curl with desktop UA — site WAF rejects non-browser TLS).
- **Format**: XLSX (3 layout generations, all handled) →
  `data/processed/port_shipments_monthly.parquet`, `port_vessel_calls_monthly.parquet`.
- **Local cache**: `data/raw/flinders_stats/`

## flinders-portmis
- **What**: PortMIS public shipping schedule (Tidalis PortControl): Expected/Actual
  Ship Movements, In Port — schema + one-off capture (37 rows incl. Port Lincoln berth
  moves "4/5 BTH PLO"). No public history exists; grids are XHR-loaded (browser capture).
- **URL**: `https://portmis.flindersports.com.au/` · **Retrieved**: 2026-08-19 ·
  **Terms**: `flindersportholdings.com.au/wp-content/uploads/2021/11/PORTMISTermsandConditions1.pdf`
- **Local cache**: `data/raw/flinders_portmis/expected_movements_20260819.json`

## pirsa-crop-pasture-reports
- **What**: PIRSA Crop and Pasture Report final editions, seasons 2022/23–2025/26; EP
  district (WEP/LEP/EEP) area + production by crop, SA totals.
- **URL**: `https://pir.sa.gov.au/crops-and-plants/grains-and-crops/crop-and-pasture-reports`
  (PDFs under `/__data/assets/pdf_file/...`). **Retrieved**: 2026-08-19 ·
  **Licence**: © Government of South Australia; cited statistics.
- **Format**: PDF → `data/processed/production_districts.parquet` (values transcribed
  and spot-verified verbatim against PDF text by `pipeline/r4_build_production.py`;
  build fails on mismatch).
- **Notes**: 2025/26 final = January "Crop Performance Summary" (no post-harvest edition
  was published for that season).
- **Local cache**: `data/raw/pirsa/`

## abares-clum-landuse
- **What**: Catchment-scale land use of Australia, Update Dec 2023 v2 — national 50 m
  GeoTIFF (SA clipped in pipeline; cropping classes → demand pixels).
- **URL**: `https://www.agriculture.gov.au/sites/default/files/documents/clum_50m_2023_v2.zip`
  (DOI 10.25814/2w2p-ph98). **Retrieved**: 2026-08-19 · **Licence**: CC BY 4.0
  (attribution: ABARES). **Format**: GeoTIFF in zip (158 MB).
- **Local cache**: `data/raw/abares_clum/clum_50m_2023_v2.zip`

## osm-roads-silos
- **What**: EP drivable classified road network (7,874 ways: trunk→residential) and 136
  silo features, bbox (-35.25, 131.0, -31.0, 137.65).
- **URL**: `https://overpass-api.de/api/interpreter` · **Retrieved**: 2026-08-19 ·
  **Licence**: **ODbL — © OpenStreetMap contributors** (attribution required in app).
- **Format**: Overpass JSON → `data/processed/roads.graph.json` (9,320 nodes / 12,566
  edges, largest component, site-snap ≤ 648 m, Cummins→Pt Lincoln 62.7 km).
- **Notes**: overpass-api.de rejects UAs containing "crawler" (406) — plain UA used.
- **Local cache**: `data/raw/osm/`

## open-meteo-climate
- **What**: daily rain, tmax/tmin, RH mean/min, wind/gusts, ET0 for 8 EP district points,
  2020-09-01 → 2026-02-28 (ERA5-family reanalysis).
- **URL**: `https://archive-api.open-meteo.com/v1/archive?...` · **Retrieved**: 2026-08-19
  · **Licence**: CC BY 4.0 (open-meteo.com; underlying Copernicus ERA5 — attribution:
  "Contains modified Copernicus Climate Change Service information").
- **Format**: JSON → `data/processed/climate_daily.parquet`.
- **Notes**: used instead of SILO point data (SILO API requires an identifying email —
  see ASSUMPTIONS A6 for the deviation + upgrade path).
- **Local cache**: `data/raw/climate/`

## reference-documents
- **What**: load-bearing published references cached for provenance: ACCC Final
  Determinations Port Lincoln & Thevenard (2021; port specs Table 3.1/3.2, catchments),
  Bunge Port Loading Protocols (eff. 14 Oct 2025), GTSN SA truck chart + truck book
  (Sept 2025; mass limits, harvest concession), T-Ports Port Loading Protocols 2024/25 +
  2025/26, ESCOSA bulk grain supply chain inquiry final report (2019).
- **Licences**: publicly released regulatory/industry documents; cited.
- **Local cache**: `data/raw/reference/` (7 PDFs)

## not-used / rejected sources
- **MarineTraffic / VesselFinder**: ToS prohibit automated collection; not scraped.
- **AMSA portal CSV zips**: superseded by the AODN parquet mirror (10× smaller); the
  portal's per-download terms acceptance + Feb 2023 gap documented by scouting.
- **data.gov.au CKAN**: 403s this environment; AMSA/AODN used directly.
- **CSIRO ePaddocks** (paid): flagged as operator option only — not purchased.
- **GTA shipping stems**: GTA does not republish stems (404).
- **SILO point API**: needs identifying email (see A6).
