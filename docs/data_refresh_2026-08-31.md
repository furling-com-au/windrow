# Data refresh — 2026-08-31

Run in answer to "do we need to update our data?". Every dataset was re-checked against its
upstream, the four pre-publication status facts in `docs/prepublication_review.md` §5 were
re-checked, and provenance was written back into `data/SOURCES.md`. Nothing that feeds the
calibrated baseline moved.

## 1. Datasets

| Source | Upstream state as at 2026-08-31 | Action |
|---|---|---|
| Weekly/monthly receivals (Bunge news API) | Live listing item-for-item identical to the cached `getarticles_p01.json`; newest item 2026-08-18, newest receivals report 2026-08-04 | none needed |
| PIRSA district production | 2025/26 final is the latest published report | none needed; `demand_2026-27.json` stays A20 provisional |
| Flinders Port Holdings monthly stats | Listing still ends at `07-Statistics-July-26.xlsx` | none needed |
| AMSA/AODN AIS | S3 partition still ends at May 2026 — Jun, Jul **and** Aug 2026 all absent | fetch window extended to 2026-08; gap recorded as upstream cadence |
| Bunge shipping stem + loading statement | **New**: 31 Aug 2026 stem and loading statement published | fetched and cached |
| Open-Meteo climate | Archive runs to ~4 days behind real time; our window stopped at 2026-02-28 | **extended to 2026-08-27** (+1,440 rows) |
| Operator cash bids | Daily capture running; 14 days held, 0 EP bids (off-season) | none needed |
| Site roster / press corpus | Re-pulled earlier today | none needed |

### Climate — the one real staleness, now cleared

`pipeline/r5_fetch_climate.py` had `END` hardcoded at `2026-02-28`, and `wlib.fetch` treats
an existing cache file as final, so re-running it could never advance the series. Each
fetched window is now cached under its own filename (`openmeteo_{station}__to{END}.json`),
leaving raw files immutable, and `r5_parse_climate.py` keeps the latest window per station.

`climate_daily.parquet`: 16,056 → 17,496 rows, 2020-09-01 → **2026-08-27**.

**Diff against the previous parquet over the 16,056 overlapping rows**: `rain_mm`, `tmax_c`,
`tmin_c`, `wind_max_kmh`, `gust_max_kmh`, `rh_mean_pct` and `rh_min_pct` are bit-identical.
`et0_mm` changed on **15,514 of 16,056** rows by order 0.01–0.1 mm — an upstream model
revision. `et0_mm` is carried in the parquet and read by nothing (`grep -rn "et0"` returns
only the fetch and parse scripts), so no engine input moved and the calibration is untouched.

The refresh does **not** populate the 2026/27 live season: `p2_build_misc.py` reads
Sep 1 – Mar 31 windows, and 2026/27 starts tomorrow. `p2_build_live.py:89` self-arms on
**2026-09-02**, so the first weekly cron after that (Monday 2026-09-07) will fetch real
2026/27 weather and the rain gate stops being silently off — no code change needed.

### Shipping stem — new operational facts

The 31 Aug stem carries, verbatim: "THE TERMINAL WILL BE CLOSED FOR SHIPPING DUE TO
MAINTENANCE BETWEEN 1 - 30 SEPTEMBER 2026" for **Port Lincoln** (Outer Harbor: 1–15
September), plus Port Lincoln loading closures on **24 November 2026**, **28 February 2027**
and **21 March 2027** for cruise-ship arrivals.

The Port Lincoln section has **no vessel rows** — the 18 Aug line-up (PORT VERA CRUZ, 55,000 t
wheat for Brahman Commodities) has sailed. `stem_entries.parquet` is therefore unchanged at
428 rows over 42 snapshots: an empty section, not a parse failure. The landing page now links
the stem at a version-less `shipping-stem.ashx`.

## 2. The four §5 status re-checks

1. **T-Ports harvest page — has it rolled to 26/27?** **No.** The page cached today still
   reads `Site closed for 25/26 season` under both LOCK and KIMBA, and Lucky Bay/Wallaroo
   show off-season "By Appt." hours. The only "2026/27" on the page is the *Grain for Good*
   program label.

   **But the archive check that came with it clears D2's substance.** The Internet Archive
   (offline for most of this session, reachable late) holds 46 snapshots of the page. The one
   taken **14 January 2026 — mid-harvest, inside the 2025/26 season** — carries
   `Site closed for 25/26 season` under **both** LOCK and KIMBA while LUCKY BAY and WALLAROO
   carry `By Appt.` hours **and live segregation lists**. That is positive in-season evidence
   from a third-party archive, not an off-season read, and it supplies the **Kimba** evidence
   that `docs/ready_to_draft.md` D2 records as missing entirely.

   The **16 September 2025** snapshot demonstrates the failure mode in the same page: all four
   sites, Lucky Bay included, read `Closed` with no segregations — exactly the state
   `docs/roster_audit_2026-08.md` §1 diagnoses on the incumbent's side.

   Both snapshots are cached and in the manifest, and registered under `tports-site-status` in
   `data/SOURCES.md`. `pipeline/manual_sites.json` now cites the January snapshot on both
   bunker records. What remains open in D2 is the fresh Wayback capture of the *current* page
   (archive was 429/offline; see §3) and putting the closure to T-Ports in the reply round.
2. **Murdinga tender outcome.** Binding offers were due **21 August 2026** (Elders public
   tender for six surplus Bunge sites: Bordertown, Tintinara, Coomandook, Geranium, Wunkar,
   Murdinga — Murdinga 2.24 ha, 23,400 t). **No outcome published** as at 2026-08-31, ten days
   after close.
3. **Has T-Ports been sold?** **No completion published.** Nothing later than the December 2025
   position (offered as a package with Australian Grain Export, unsold, adviser Nash Advisory
   reporting advanced discussions).
4. **Wheat Port Code against the 1 October 2026 sunset.** **This one changed the picture.**
   The ACCC page (retrieved today) still says the code runs to 1 October 2026 "unless the
   Australian Government makes a decision to either remake or repeal the code at an earlier
   date", and no decision is published. But in **July 2026** the government released a **draft
   streamlined remake** for a three-year term, consulted for three weeks via DAFF's Have Your
   Say. So the piece cannot describe a bare sunset. Registered as `wheat-port-code-2026` in
   `data/SOURCES.md` with all three pages cached.

## 3. Not done

**The Wayback archival of `tports.com/harvest`** that D2's fix requires. The Internet Archive
was returning `429` and then serving its "Internet Archive services are temporarily offline"
page throughout this session, for both the CDX API and the availability API. The local cache
(`data/raw/press/tports_harvest__20260831.html`, in the manifest) stands; the third-party
archive copy still has to be made before the 2025/26 state is publishable.

This also blocks the Wayback halves of `r2_fetch_receivals.py`, `r2b_fetch_bunge_pages.py`
and `r3_fetch_stems.py`. Only their live-source halves were run today, which is why the
Bunge news and current-stem checks above were done directly rather than through those scripts.

## 4. Verification that nothing moved

- `npm --workspace packages/sim run test` — **17/17 pass**, determinism/event-log-hash test
  included, after the climate rebuild.
- Historical app bundles are byte-identical before and after (`observed_2022-23` …
  `observed_2026-27`, `weather_2022-23`, `weather_2023-24`, `weather_2024-25`,
  `weather_2026-27`). The single exception is **`weather_2025-26.json`**, which grows from
  181 to 212 days per district: the season window is Sep 1 – Mar 31 and the old series
  stopped at 28 February, so March 2026 was previously missing. Every pre-existing value is
  identical — the change is append-only, and those days fall outside the ~123-day harvest
  window the engine gates on.
- `pipeline/r1_build_sites.py` rebuild: the only changes in `data/processed/sites.geojson`
  are the `notes` and `sources` strings on Lock and Kimba. No geometry, status, capacity or
  district moved on any of the 32 features.
- `pipeline/r8_choice_geometry.py` re-run: **`no independent within 90 min: 66.8% <-- HEADLINE`**,
  sweep `30:97.1% 45:93.2% 60:87.4% 75:78.2% 90:66.8% 105:53.2% 120:39.5%`, speeds
  `x0.85:77.2% x1.00:66.8% x1.15:54.5%`, A11 sweep 66.8% at all 129 configurations —
  identical to `docs/ready_to_draft.md`. `r8_choice_geometry.py`, `r8a_coord_sensitivity.py`
  and `docs/r0_choice_geometry.json` are all git-clean after the re-run.

## 5. A defect the refresh exposed — `p2_stem_names.py` was not deterministic

Rebuilding the bundles produced a diff in `vessels_2023-24/2024-25/2025-26.json` that the
new data could not explain (`stem_entries.parquet` is unchanged at 428 rows). Running the
script twice on **identical inputs** produced **different files both times**: vessel
`name_candidate` / `stem_volume_t` / `stem_commodity` labels swapped between overlapping
port calls.

Cause, in `main()`:

- `ent.unique(subset=["vessel", "mon"], keep="first")` — polars' `unique()` does not
  preserve order unless asked, so "first" was whichever row the hash table happened to
  yield; and
- the greedy match kept `if best is None or score < best[0]` over `ent.iter_rows()`, so
  equal-gap candidates were resolved by that same unstable iteration order.

Fixed by giving the candidates a total order: sort by
`["vessel", "mon", "date_min", "date_max", "source_file"]`, dedupe with
`maintain_order=True`, and score on `(day gap, vessel, mon)` instead of the gap alone.

The heuristic itself is unchanged — same window (±6 days), same greedy assignment, same
match counts (45/86, 36/53, 30/51). Only the tie-breaking is now reproducible. Some labels
therefore differ from `HEAD`: the previous values were one arbitrary draw, and these are the
deterministic one.

Verified: three consecutive runs on unchanged inputs now produce **byte-identical**
`vessels_*.json` (the same check produced three different files before the fix).

The same unstable-`unique()` pattern was about to be introduced in `r5_parse_climate.py`
by this refresh — the new multi-window de-duplication used `keep="last"` without
`maintain_order=True`, where "last" is meant to mean "from the newest window". Fixed there
too before it could bite.

Worth noting where this sat: the names are documented as "garnish for the UI", so the defect
never touched a number — but it meant any rebuild of the published bundles produced a
spurious diff, on a project whose case rests on being reproducible from raw.
