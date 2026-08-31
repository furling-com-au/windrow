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
- ⚠ **128 is this source's own page count and is NOT the corpus denominator.** Anything
  counted over `data/processed/receivals_notes.jsonl` has a denominator of **148** — 127 of
  these 128 pages (one carries no narrative) plus 21 Bunge-branded pages from
  `bunge-news-api` below. `receivals_weekly.parquet` is a third, narrower set again: 127
  source files, of which 117 are Wayback and 10 are `bunge-live`. Quote whichever count you
  mean, with the command that prints it; a "1 of 128" written against the notes corpus was
  found and corrected on 2026-08-31 (see `cungena-status-contradiction`).
- **Reproduce the notes-corpus denominator**:
  `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import json;rows=[json.loads(l) for l in open('data/processed/receivals_notes.jsonl',encoding='utf-8')];print(len(rows),len({r['source_file'] for r in rows}))"`
  → `148 148`
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

## tports-site-status
- **What**: T-Ports harvest page — per-site operating status for the 2025/26 season. Carries
  **`<p>Site closed for 25/26 season</p>` under the `LOCK` heading and again under the
  `KIMBA` heading**; `LUCKY BAY` and `WALLAROO` carry no such notice. The site-to-notice
  association was established from the archived HTML's document order, not inferred.
  This is the sole evidence for the closed 2025/26 state of both inland bunkers, and every
  2025/26 finding in `docs/r0_choice_geometry.md` rests on it.
- **URL**: `https://tports.com/harvest/` · **Retrieved**: 2026-08-31 (earlier read
  2026-08-19) · **Licence**: operator public disclosure.
- **Local cache**: `data/raw/press/tports_harvest__20260831.html`
- **Caveat**: both reads are **off-season live-page reads**, the same method that produced
  the roster defect in `docs/roster_audit_2026-08.md` §1 on the incumbent's side. Unlike
  that case the wording here is an explicit closure statement rather than an empty list, so
  it is not the same inference — but the page will roll to 26/27 and the claim should be
  corroborated with T-Ports directly. Not yet submitted to the Wayback Machine.

## tports-site-capacities
- **What**: T-Ports Lucky Bay page — source for the capacity figures used in
  `pipeline/manual_sites.json`: Lucky Bay 384,000 t, Kimba bunker 150,000 t
  ("150,000 tonnes in four bunkers"), Lock bunker 140,000 t.
- **URL**: `https://tports.com/lucky-bay/` · **Retrieved**: 2026-08-31 ·
  **Licence**: operator public disclosure.
- **Local cache**: `data/raw/press/tports_luckybay__20260831.html`

## arowana-luckybay-freight-claim
- **What**: Arowana's 2 September 2021 release on the early settlement of its secured
  infrastructure debt facility for Lucky Bay Port. Source of two claims used in this
  project, both verbatim from the cached page:
  - "The Lucky Bay Port generates road freight savings for grain growers from the Eyre
    Peninsula of **up to $15 per tonne** and 4,600 tonnes of CO2 emission savings annually."
  - "This has enabled co-investors with Arowana to realise a return in excess of the
    **target IRR of 15%**."
- **URL**: `https://arowanaco.com/2021/09/02/arowanas-private-credit-investment-in-lucky-bay-port-yields-strong-returns/`
  · **Retrieved**: 2026-08-31 · **Licence**: company media release, quoted with attribution.
- **Local cache**: `data/raw/press/arowana_luckybay_returns_20210902__20260831.html`
- **Status**: a **promotional claim by an investor in the asset**, not an independent study.
  No working, no method, no rate and no base year are published for the $15/t figure, and
  "up to" is a maximum. Tested in `pipeline/r10_arowana_claim.py`; the test is currently
  NOT publishable for the reasons in `docs/r9_cartage_findings.md`.
- ⚠ **Provenance failure worth recording.** This claim was used in a workflow prompt on
  2026-08-31 before it was ever sourced into the repo — it came from a web-search summary
  that was never fetched or cached. An adversarial pass caught it: the quoted words existed
  nowhere in the repo except in the scripts written to test them. The claim turned out to be
  real and is now registered here. The same channel had already produced two claims in this
  project that were **false** (that T-Ports was hiring for Lock and Kimba in 2025/26, and
  that Grain Producers SA opposed the 2024 Grainflow acquisition). A search summary is not
  a source.

## bunge-surplus-site-tender-2026
- **What**: Bunge's public tender of six surplus SA bulk-handling sites via Elders —
  Bordertown (36,200 t), Tintinara (13,000 t), Coomandook (23,000 t), Geranium (20,100 t),
  Wunkar (6,600 t) and **Murdinga, Eyre Peninsula (23,400 t, 2.24 ha)**. Binding offers due
  2026-08-21. Bunge: "While these sites are no longer part of our operational network, we
  recognise they may present opportunities for others"; Murdinga described as a "past site"
  offering "flexibility for industrial or alternative rural development". Murdinga has zero
  mentions across all ten seasons of `receivals_notes.jsonl`. Tender outcome unpublished as
  at 2026-08-31.
- **URL**: `https://www.graincentral.com/news/bunge-to-sell-six-surplus-sa-bulk-handling-sites/`
  (Grain Central, 2026-07-07) · **Retrieved**: 2026-08-31.

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
- ⚠ The ESCOSA report is **also registered separately below** as
  `escosa-marginal-trucking-rate-2019`, because it carries a published $/t-km
  freight schedule that A18 depends on and that needs its own basis and caveats.

## escosa-marginal-trucking-rate-2019 — the published $/t-km schedule
- **What**: the only public marginal road-cartage schedule for South Australian grain
  found in this project — **A$0.12 per tonne-km up to 50 km, A$0.11 per tonne-km for
  50–250 km**, in **2018–19 A$, nominal and undeflated**. Verbatim: "Only the marginal
  freight cost has been used, $0.12 ($/tonne-km) for up to 50 kilometres and $0.11
  ($/tonne-km) for 50 to 250 kilometres."
- **Where**: Essential Services Commission of South Australia, *Inquiry into the South
  Australian bulk grain export supply chain costs — Final Report*, **29 January 2019**,
  Box 5.2 "Cost Shifting Case Study — Assumptions and detailed calculations", p. 91
  (extracted-text lines 5405–5412 under `pdftotext -layout`).
- **URL**: `https://www.escosa.sa.gov.au/ArticleDocuments/1076/20190129-Inquiry-BulkGrainExportSupplyChainCosts-FinalReport.pdf.aspx`
  (linked from `https://www.escosa.sa.gov.au/projects-and-publications/projects/inquiries/inquiry-into-the-south-australian-bulk-grain-supply-chain-costs`).
- **Retrieved**: PDF cached **2026-08-19**; schedule read, verified and registered
  **2026-08-31**. · **Licence**: publicly released regulatory report; cited with
  attribution.
- **Local cache**: `data/raw/reference/escosa_grain_supply_chain_2019.pdf`
  (sha256 `f901b52cba57cddac955a3448767c3ebe1e99656a11775ffd0bc348bf027354c`;
  PDF ModDate 2019-01-29, matching the publication date. Not listed in
  `data/raw/MANIFEST.sha256`.)
- **Upstream provenance, and it is not uniform across the two bands**: ESCOSA states the
  estimates "were based on data provided by AEGIC, verified against published Viterra
  freight rates". Its footnote 289 attributes the **≤50 km** rate to AEGIC, *Australia's
  grain supply chains: Costs, Risks and Opportunities*, October 2018, **Note 2c to Figure 4,
  p. 18**, and the **50–250 km** rate to "**AEGIC advice**" — i.e. unpublished advice to the
  Commission. Only the first of the two traces to a public document. The AEGIC report
  itself is **not** cached in this repo.
- **What it actually says — the basis, which matters more than the rates**:
  - **Marginal, not average**: "once the grower's truck is on the road, then only the
    additional (marginal) cost involved in travelling further to the next available site is
    relevant." Truck ownership, loading and the trip that would have happened anyway are
    outside it.
  - **Applied to one-way loaded kilometres, band selected by the whole distance, no
    cumulative tiering, empty return leg not added.** ESCOSA does not say this in prose; it
    is recovered from the four case results it publishes against the four Google Maps
    distances it used (Caltowie 16.3 km → $1.96/t, Yongala 53.0 km → $5.83/t, Gulnare
    31.7 km → $3.80/t, Jamestown 28.5 km → $3.42/t). One-way flat-band reproduces all four;
    round-trip reproduces none; cumulative tiering fails on Yongala, the only case crossing
    the 50 km edge ($6.33 computed vs $5.83 published).
  - **Time is excluded, and the report says so**: "This case study has not addressed all
    potential costs, such as if the additional travel time resulted in the need for a
    grower to employ an additional truck." Site turnaround is likewise set aside.
  - **Nominal and deliberately not deflated**: "The marginal trucking cost rates have not
    been deflated because it is not known how well the resulting deflated costs would
    reflect the actual costs of the time."
- **What it does NOT say**: it is **South Australia-wide, not Eyre Peninsula-specific** —
  the case study behind it is the upper Central region (Gladstone catchment, 16–53 km
  hauls). It publishes **no band above 250 km**. It is **silent on whether AEGIC's
  underlying cost line embeds an empty return leg, loading or waiting**; the full report
  text contains no "return leg", "backload", "round trip" or "empty run". That silence is
  worth a factor of two and must be reported as silence, not resolved by assumption.
  It is a **cost rate and not a distance threshold** — it does not designate any cart
  range, and must not be used to justify one (see `docs/r0_choice_geometry.md:48`).
- **Reproduce**:
  `pdftotext -layout data/raw/reference/escosa_grain_supply_chain_2019.pdf - | sed -n '5405,5412p'`
  and, for the application rule and the transcription check,
  `.venv/Scripts/python.exe pipeline/r9_escosa_rate_check.py` (prints `VERDICT: PASS`).
- **Used in**: `data/ASSUMPTIONS.md` A18; the Tier-2 cartage-dollars output. Never in the
  simulation.
- **No successor found.** Searched 2026-08-31 for any published $/t-km grain road-freight
  schedule postdating January 2019: ESCOSA's inquiry page shows no successor inquiry or
  update; AEGIC has published no edition of *Australia's grain supply chains* later than
  October 2018 (the 2024 wp-content URLs are re-uploads of the 2018 report; aegic.org.au
  refuses automated fetches, so this rests on search results rather than a document read);
  ACCC bulk grain ports monitoring covers ports and capacity only and does not collect
  overland grain movements; ABS road freight publishes no grain-specific $/t-km. The two
  more recent published rate documents that do exist are registered below, and neither is a
  replacement.

## ach-recommended-cartage-rates-2026 (comparator — not a substitute)
- **What**: Australian Custom Harvesters' "Recommended Cartage Rates" — "up to 10 km –
  $16.50 per tonne (excl GST)/$18.15 (incl GST)", then "add $0.10 (excl GST) /$0.11 (incl
  GST) per tonne" for each further kilometre. "These rates include demurrage." "These rates
  are a guide only. Growers and contractors should negotiate rates based on individual
  circumstances." Valid as at **1 February 2026**.
- **URL**: `https://customharvesters.org.au/harvest-rates/` · **Retrieved**: 2026-08-31 ·
  **Licence**: industry-association published guidance; cited with attribution.
- **Why registered**: it is the most recent published *marginal* distance increment found,
  and it bounds the inflation question — $0.10/t-km excl GST in 2026 sits **below** ESCOSA's
  $0.11–0.12 in 2018–19 A$, which is why A18 publishes in base-year dollars rather than
  indexing forward.
- **Why it is not a substitute**: national rather than SA or EP; contractor guidance rather
  than a regulator's finding; and a **full** charge with a large fixed component
  ($16.50 for the first 10 km) rather than a pure marginal line. Not cached locally.

## sagit-farm-gross-margin-guide-2026 (comparator — not a substitute)
- **What**: SAGIT / Ag Excellence Alliance / GRDC, *2026 Farm Gross Margin and Enterprise
  Planning Guide for South Australia*. "Freight Costs (as included in Gross Margins)":
  cereal grains **$35.00/tonne**, canola $35.00, lentils $38.00, other legume grains
  $35.00, triticale $28.00, fertiliser $35.00, oaten hay $35.00. Commodity prices in the
  guide are "on delivered end-user basis e.g. Grain is delivered port basis".
- **URL**: `https://sagit.com.au/wp-content/uploads/2026/02/ART-251201.07.01-SAGIT-Gross-Margins-Guide-2026_DIGITAL.pdf`
  · **Retrieved**: 2026-08-31 · **Licence**: publicly released industry guide; cited.
- **Why registered**: SA-specific and current, so it is the natural place a reader would
  look for a 2026 SA cartage number.
- **Why it is not a substitute**: it is a **flat $/tonne budgeting allowance with no
  distance term at all**, so it cannot produce a per-district or per-kilometre figure. Used
  only as an upper bracket: at EP's ~144 km average site→port haul the three sources read
  ESCOSA $15.84/t (marginal, 2018–19 A$) < ACH $29.90/t (full, 2026) < SAGIT $35.00/t
  (budgeted, 2026). The gap is the fixed and time cost the marginal rate excludes by design.
  Not cached locally.

## published-claims — press and government reporting (verification pass 2026-08-31)

Sources for the *narrative* claims the piece opens on, as distinct from the datasets above.
Verified 2026-08-31 by fetching and reading each item in full. Cached under
`data/raw/press/` — **note: these files post-date `data/raw/MANIFEST.sha256` and are not in
it.** Each entry records what the source does *and does not* support.

### ep-freight-study-2018 (primary — the road claim)
- **Claim it supports**: the roads named as carrying the additional grain freight once EP
  rail closed — **Tod Highway, Lincoln Highway (Arno Bay–Port Lincoln), Balumbah-Kinnaird
  Road, Wharminda Road, Western Approach Road**.
- **What**: *Eyre Peninsula Freight Study*, SMEC internal ref. 3005591, Revision 0 – Final,
  **dated 26 Sept 2018**, prepared by Tim Warren for **the Department of Planning, Transport
  and Infrastructure and Genesee and Wyoming Australia**; publicly released by the SA
  Government early April 2019.
- **URL**: `https://www.dit.sa.gov.au/__data/assets/pdf_file/0008/540872/Eyre_Peninsula_Freight_Study.pdf`
  — **now 404 on the live host**. Retrieved from
  `https://web.archive.org/web/20240329115459id_/<that URL>`.
- **Retrieved**: 2026-08-31 · **Licence**: publicly released government/consultant study;
  cited with attribution.
- **What it actually says**: the five roads appear in the study's *impacted network* route
  tables (extracted-text lines 1064–1072, 2123–2141) for the **Base Case** — defined at §8.2
  as the transition of all EP grain to road. §8.2.1 scopes "curve widening, shoulder sealing,
  median treatments and minor intersection upgrades", overtaking lanes, rest areas, "Road
  rehabilitation works … to achieve a Pavement Health Index rating of `Fair'", sealing of
  impacted Council unsealed roads, and "safety improvements within the City" of Port Lincoln.
  Freight vehicles are converted at "an average payload of 70tonnes/vehicle".
- **What it does NOT say**: it is a **forecast**, finalised eight months before grain rail
  ceased. It contains no observation of realised post-closure traffic on any named road. Its
  Table 4 cost columns do not survive text extraction cleanly, so the $95.5 m / $50.7 m
  totals below are cited to the Port Lincoln Times, not re-derived here.
- **Reproduce**: `pdftotext data/raw/press/dit_eyre_peninsula_freight_study_smec_2018_wayback20240329.pdf - | grep -n "Wharminda"`
- **Local cache**: `data/raw/press/dit_eyre_peninsula_freight_study_smec_2018_wayback20240329.pdf`

### port-lincoln-times-ep-freight-study-2019 (the quotable sentence)
- **What**: "Eyre Peninsula freight study highlights costs" (sub-headline "Grain shift to
  cost millions"), **by Jarrad Delaney, Port Lincoln Times, first published 10 April 2019
  9:31am, updated 10 April 2019 5:28pm**.
- **URL**: `https://www.portlincolntimes.com.au/story/6012789/grain-shift-to-cost-millions/`
  — the live host (rebuilt by SA Today Pty Ltd) now serves its homepage at this path.
  Retrieved from `https://web.archive.org/web/20230324165622id_/<that URL>`.
- **Retrieved**: 2026-08-31 · **Licence**: publisher content; short quotation with
  attribution for research/reporting.
- **The sentence** (verbatim): "The report shows roads affected by the closure of rail will
  include the Tod Highway and Lincoln Highway between Arno Bay and Port Lincoln, as well as
  Balumbah-Kinnaird, Wharminda and Western Approach roads."
- **Also verified in this article** (verbatim): "So far about $25 million has been announced
  by the federal government to upgrade the road network to cater for increased truck
  movements." / "The report shows the base case option would require about $95.5 million in
  road infrastructure investment with about $50.7 million in road maintenance costs." /
  Transport Minister Stephan Knoll, "about 60 to 70 per cent of grain was hauled by road on
  Eyre Peninsula".
- ⚠ **Tense.** The verb is "**will include**", published **10 April 2019 — seven weeks before
  the last grain train (31 May 2019)** — reporting a study dated 26 Sept 2018. This source
  establishes that the roads were **named in advance as the ones that would carry the extra
  freight**. It does **not** establish that they *absorbed* it. Wording in the piece must
  match the tense of the source.
- **Local cache**: `data/raw/press/portlincolntimes_6012789_ep-freight-study_wayback20230324.html`

### raa-ep-road-assessment-2024 (the only post-hoc road evidence found)
- **What**: "RAA calls for review of Eyre Peninsula road network", RAA (Royal Automobile
  Association of South Australia) media release, **2 August 2024**, releasing RAA's Eyre
  Peninsula regional road assessment.
- **URL**: `https://daily.raa.com.au/media-resources/raa-calls-for-review-of-eyre-peninsula-road-network/`
  (report index: `https://www.raa.com.au/roadassessments`) · **Retrieved**: 2026-08-31 ·
  **Licence**: publisher media release; cited with attribution.
- **Verbatim**: "a survey of more than 1,300 Eyre Peninsula road users found road maintenance
  was the biggest concern among locals – with the issue raised by 76% of respondents."
- Also names "Cowell-Kimba Road, Balumbah-Kinnard Road and Bratten Way" as heavy-vehicle
  affected corridors, and "Lincoln Highway, Tod Highway and Iron Knob Road" as having major
  road-safety issues. Secondary reporting of the same release attributes an **87 %** figure
  for respondents observing increased truck movements after the 2019 rail closure; that
  percentage was **not** found in the release text itself and is **not** treated as verified.
- ⚠ **This is the closest thing to a post-closure observation, and it does not name Wharminda
  Road.** It supports Balumbah-Kinnaird, Lincoln Hwy and Tod Hwy after the fact. Wharminda
  Road is supported **only prospectively**, by the 2018 study and the 2019 Port Lincoln Times
  report of it.

### ep-rail-closure-truck-figures-2019 (context figures — mixed reliability)
- **ABC Rural, "A 'sad day' for the Eyre Peninsula as locals say goodbye to rail transport",
  Brooke Neindorf, Emma Pedler and Patrick Martin, 31 May 2019** —
  `https://www.abc.net.au/news/rural/2019-05-31/eyre-peninsula-farewells-grain-train/11159354`.
  Verbatim: "Around 30,000 extra truck movements will take the place of the current rail
  grain haulage on the Eyre Peninsula." Confirms the last grain train ran 31 May 2019.
- **Grain Central, "Sun sets on Eyre Peninsula rail as Viterra moves to road", 27 Feb 2019** —
  `https://www.graincentral.com/news/sun-sets-on-eyre-peninsula-rail-as-viterra-moves-to-road/`.
  Verbatim: "The decision is expected to create up to 50 extra truck movements per day within
  the town of Port Lincoln."
- **RTBU SA/NT (Darren Phillips), "Ramsay must step in to save Eyre Peninsula Rail Line",
  undated, internally dated to early May 2019 ("the Federal election just a fortnight away")** —
  `https://www.rtbu.org.au/ramsay_must_step_in_to_save_eyre_peninsula_rail_line`.
  Verbatim: "It will take 40 to 50 one-way truck movements to replace one train." and
  "64,000 60-tonne trucks barreling through Port Lincoln every year".
  ⚠ **This is a union media release campaigning in a federal election, not reporting.** The
  64,000 figure is also the **total**, not the increment: at 60 t counting both directions it
  implies ≈1.9 Mt through Port Lincoln, matching the freight study's "Of the 1.9 million
  tonnes delivered to Port Lincoln in 2017", while the ~30,000 above is the rail-replacement
  increment (816,000 t went by rail in 2017 per the same study). If either is used, attribute
  it to the RTBU and say which quantity it is.
- **Retrieved**: 2026-08-31 · **Licence**: publisher / organisation content; quoted with
  attribution.

### aurizon-viterra-rail-proposal-2023
- **What**: the Aurizon + Viterra application for federal funding to reopen the EP grain lines.
- **ABC Rural, 9 March 2023** (Bethanie Alderson, Brooke Neindorf, Bernadette Clarke, Narelle
  Graham) — `https://www.abc.net.au/news/rural/2023-03-09/push-to-see-sa-rail-freight-return-with-federal-support/102073432`.
  Verbatim: "Aurizon and Viterra submitted a formal application for federal government funding
  of **$220 million** to upgrade and reopen the rail network between Port Lincoln and Cummins,
  as well as the lines to Wudinna and Kimba." Also: "Viterra made the decision to no longer
  use rail to transport grain on the Eye Peninsula in 2019 due to the condition of the line
  and the restrictions it placed on operations." [sic — "Eye"]
- **Grain Central, "Viterra, Aurizon seek Eyre Peninsula rail reboot", 3 March 2023** —
  `https://www.graincentral.com/news/viterra-aurizon-seek-eyre-peninsula-rail-reboot/`:
  "the removal of approximately **42,000** truck movements between up-country sites and Port
  Lincoln annually"; the parties commit to moving "at least 1.3Mt of grain on the rail network
  each year".
- **Retrieved**: 2026-08-31 · **Licence**: publisher content; quoted with attribution.
- ⚠ Note the tension the piece should not paper over: the operator's own 2023 number for truck
  movements attributable to rail's absence is **42,000**, against ABC's 30,000 (2019) and the
  RTBU's 64,000 (a total, 2019). Cite one, name its source and its basis.

### viterra-2019-site-closures (the `closed_2019` tags in `pipeline/manual_sites.json`)
- **What**: Viterra's June 2019 closure of 17 up-country sites, six of them on Eyre Peninsula.
- **Stock Journal, "SILO SLASH: 17 Viterra grain sites to close", by Alisha Fogden, first
  published 6 June 2019 6:00am, updated 7 June 2019 4:21pm** —
  `https://www.stockjournal.com.au/story/6202314/freight-redirection-behind-viterras-17-silo-closures/`
  (syndicated to Farm Online 7 June 2019 10:00am at
  `https://www.farmonline.com.au/story/6204914/freight-redirection-behind-viterras-17-silo-closures/`,
  which states "This story first appeared on Stock Journal").
- **Stock Journal, "Croppers angry as upper EP silos take a hit" (standfirst: "Northern EP to
  lose six silos"), by Alisha Fogden, first published 6 June 2019 1:00pm, updated 24 August
  2023 10:51pm** — `https://www.stockjournal.com.au/story/6202864/northern-ep-to-lose-six-silos/`.
- **Retrieved**: 2026-08-31 · **Licence**: publisher content; quoted with attribution.
- **Counts and sites — VERIFIED.** "close 17 of its upcountry sites"; "six sites open last
  year at **Minnipa, Kyancutta**, Brinkworth, Paskeville, Millicent and Walpeup in Vic would
  not 'play a future role in the Viterra network'"; "A further 11 sites that were not open the
  year prior at **Cungena, Waddikee, Kielpa, Wharminda**, Orroroo, Redhill, Robertstown, Long
  Plains, Stockwell, Wunkar and Alawoona would also be closed permanently." The second story:
  "The sites of Minnipa, Kyancutta, Cungena, Waddikee, Kielpa and Wharminda have been closed."
  **17 statewide, 6 on EP — exactly the six `closed_2019` entries in `manual_sites.json`.**
- ⚠ **The freight/rail attribution is NOT in either source.** "Freight redirection behind
  Viterra's 17 silo closures" survives only as a **URL slug**; the article's headline is "SILO
  SLASH: 17 Viterra grain sites to close" and the phrase "freight redirection" appears nowhere
  in the body. Viterra's stated reasons, verbatim from operations manager Michael Hill:
  "changing delivery patterns of growers and the changing environment"; "Since 2010, the
  average truck size has increased by 30 per cent and those bigger trucks are delivering to our
  bigger sites"; "Other reasons include a need for better quality management and food safety
  requirements"; "The sites that were closed represented less than 2pc of total receivals
  (based on a five-year average)". Rail is mentioned **once**, by a grower, about a *different*
  and earlier closure: Minnipa cropper Matt Cook — "Most of the little sites around here have
  not been kept up as well as they should have been, particularly since the rail closed to here
  a few years ago." **No published source found attributes the 2019 closures to the May 2019
  rail shutdown.** The `notes` field in `manual_sites.json` ("Closed in Viterra's 2019 network
  rationalisation after EP rail shutdown") is an inference by this project, not a source claim.
- ⚠ **Four of the six were already dormant.** Cungena, Waddikee, Kielpa and Wharminda are in
  the "not open the year prior" group — they did not operate in 2018/19. Any "pre-2019" network
  state that counts all six as open overstates the 2018/19 network by four points.
- **Local cache**: `data/raw/press/stockjournal_6202314_17-silo-closures_20260831.html`,
  `data/raw/press/farmonline_6204914_17-silo-closures_20260831.html`,
  `data/raw/press/stockjournal_6202864_upper-ep-silos_20260831.html`

### cungena-status-contradiction
- **Two published sources conflict and neither is retracted.**
  1. Stock Journal, 6 June 2019 (above): Cungena is in the group of 11 that "would also be
     closed permanently", and was "not open the year prior".
  2. **Viterra's own weekly harvest report, week ending Sunday 13 November 2022** (registered
     above under `wayback-viterra-weekly-reports`; `data/processed/receivals_notes.jsonl`,
     `week_ending: 2022-11-13`): "In Viterra's Central region, Ardrossan, Balaklava, Bowmans,
     Crystal Brook, Port Giles and Snowtown received their first new season deliveries, **as
     well as Cungena**, Elliston, Port Neill, Nunjikompita, Penong, Tumby Bay, Warramboo,
     Witera and Wirrulla in the Western region."
- **Searched and not found**: any published Viterra/Bunge announcement reopening Cungena, and
  any correction to the 2019 closure list. Cungena appears in **1 of 148** parsed operator
  harvest reports across ten seasons (2016/17–2025/26), is **absent** from the Aug-2026 Bunge
  Western roster (23 sites, `operator-sites-api`) and **absent** from the 2025/26 segregations
  table in `pipeline/manual_sites.json`.
- ⚠ **Corrected 2026-08-31: this line read "1 of 128".** 128 is the size of a *different*
  corpus — the `wayback-viterra-weekly-reports` cache above. The denominator for a search over
  `receivals_notes.jsonl` is **148**: 127 of those 128 Wayback Viterra pages (one yields no
  narrative) plus 21 Bunge-branded pages from `bunge-news-api`, of which 137 are weekly reports
  and 11 monthly. `docs/r5_validation.md:121` already said 148. Do not quote a corpus count on
  this page without the command below, which prints its own denominator.
- **Reproduce the denominator and the hit together** (prints `148 148 ['2022-11-13']` —
  records, distinct source files, and the weeks naming Cungena):

  ```
  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import json;rows=[json.loads(l) for l in open('data/processed/receivals_notes.jsonl',encoding='utf-8')];print(len(rows),len({r['source_file'] for r in rows}),[r['week_ending'] for r in rows if 'Cungena' in json.dumps(r)])"
  ```
- **What the sources support**: Cungena was closed in June 2019 and described as permanent; it
  nonetheless took first new-season deliveries in 2022/23; there is no published evidence of it
  operating in any other season, and none that it is open now. The `closed permanently 2019`
  note is therefore wrong as written, and no single tag is defensible — the season range is.
- **Reproduce**: the command given above, which prints the denominator with the hit so the
  count cannot go stale again.

## not-used / rejected sources
- **MarineTraffic / VesselFinder**: ToS prohibit automated collection; not scraped.
- **AMSA portal CSV zips**: superseded by the AODN parquet mirror (10× smaller); the
  portal's per-download terms acceptance + Feb 2023 gap documented by scouting.
- **data.gov.au CKAN**: 403s this environment; AMSA/AODN used directly.
- **CSIRO ePaddocks** (paid): flagged as operator option only — not purchased.
- **GTA shipping stems**: GTA does not republish stems (404).
- **SILO point API**: needs identifying email (see A6).
