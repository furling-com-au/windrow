# Ready to draft — "One gateway" (EP competition piece)

Date: 2026-08-31 (round 3). Working tree only, nothing committed. Inputs:
`docs/gate_findings.md`, `docs/roster_audit_2026-08.md`, `docs/r0_choice_geometry.md` +
`.json`, `data/ASSUMPTIONS.md` (A2/A4/A5/A11/A12/A14/A18/A24), `data/SOURCES.md`, three
adversarial verification rounds.

## 1. Verdict

**NOT READY.** Both round-3 verifiers returned `refuted: true` at high confidence, and I
reproduced the substance of both refutations myself before writing this.

**The headline did not move.** Re-run for this brief:

```
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe pipeline/r8_choice_geometry.py
```

still prints `no independent within 90 min: 66.8% <-- HEADLINE`, the 2025/26 sweep
`30:97.1% 45:93.2% 60:87.4% 75:78.2% 90:66.8% 105:53.2% 120:39.5%`, and speeds
`x0.85:77.2% x1.00:66.8% x1.15:54.5%`. The arithmetic is sound. Round 3 was a presentation
and provenance round, and it is the presentation and provenance that failed again.

What round 3 got right and must not be undone: the 148-notes corpus fix in
`data/SOURCES.md`, the threshold-vs-gap invariance split, the md/json single-constant
sweep, the withdrawal of both a priori grounds for 90 minutes, the withdrawal of the A2
dependence, and the reworded Wharminda deletion. All six round-2 defects are genuinely
cleared. Six new ones opened.

### Blocking — none of these may be drafted around

**D1. The headline is not coordinate-independent, and the sweep that says it is cannot see
the site that sets it.** In the 2025/26 state Lucky Bay is the **only** independent
receival point (`states.s2025_26.ladder_b_ownership_gap.nearest_independent_mix =
{"Lucky Bay (T-Ports port)": 1.0}`), so its coordinate alone determines 66.8 %. That
coordinate is `coord_precision: "town"`, `coord_source: "Nominatim/OSM 'Lucky Bay, South
Australia' hamlet node (facility adjoins hamlet)"` — the identical precision class A11
gives Lock and Kimba a ≤5 km tolerance for. It is registered in **no** assumption (A11 is
titled "T-Ports inland site coordinates") and disclosed nowhere on the page, in
`ASSUMPTIONS.md` or in `SOURCES.md`. Worse, r8's A11 grid loop sets `ni25 = fixed_ind_min`
*inside* the loop — the 2025/26 independent set is held constant by construction — so
"66.8 % at every one of the 129 configurations… computed, not asserted" demonstrates
nothing about coordinate sensitivity. Running the page's own displace → re-snap →
fresh-Dijkstra machinery on Lucky Bay over the same 0/2.5/5 km × 8-bearing grid moves the
headline to **61.5 %–67.3 %** (65.1 %–67.3 % at 2.5 km alone). Reproduce:

```
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe pipeline/r8a_coord_sensitivity.py
```

*Fix:* register Lucky Bay's coordinate precision in an assumption, publish that envelope
beside the headline, and delete every sentence that generalises A11-invariance into
coordinate-independence — `r0_choice_geometry.md` lines 21 and 24 ("survives every
objection on record but one"), the "(A11-independent)" labels at :100, :104 and :144, and
the carried-assumptions A11 entry. The same undisclosed dependence carries the 2025/26 gap
row 77.3 % and Wharminda's 74.6 min.

**D2. The fact the entire 2025/26 state rests on has no provenance, and half of it has no
evidence at all.** "Both bunkers closed for the season (published, tports.com/harvest)"
appears four times and is what makes 2025/26 contain one independent point. There is no
`tports.com/harvest` entry in `data/SOURCES.md` (the only T-Ports entry is
`tports-shipping-stem`, a different artefact), no cached page under `data/raw/`, no
retrieval date on the page, and no reproduce command.
`data/raw/reference/tports_plp_2526.pdf` is the port loading protocol and mentions neither
Lock nor Kimba (`pdftotext … | grep -ci "lock\|kimba"` → `0`). The only record in the repo
is a hand-typed note on **Lock** in `pipeline/manual_sites.json`: `"'Site closed for 25/26
season' per tports.com/harvest (2026-08-19)"`. **Kimba is tagged
`status: "closed_2025_26_season"` with no closure evidence recorded anywhere** — its
`notes` field reads only "Built for 2021 harvest". And 2026-08-19 is the same off-season
live-page read that `docs/roster_audit_2026-08.md` §1 identifies as the root cause of the
four wrongly-closed Bunge sites. *Fix:* archive the page (Wayback + local cache) and
register it with a retrieval date, or the 2025/26 state is not publishable. Until then the
ground rule applies: if it cannot be sourced, it cannot be written.

**D3. The only surviving justification for quoting 90 minutes is arithmetically false.**
`r0_choice_geometry.md:44` and `r0_choice_geometry.json` `threshold.status`: "The
90-minute row is the one the headline quotes because it is **the middle of the published
grid**". `SWEEP_MIN = (30, 45, 60, 75, 90, 105, 120)` — 90 is the fifth of seven, and the
midpoint of 30–120 is also 75. The page discloses two paragraphs later that 90 min is where
the ratio peaks. A false neutrality claim replaced two withdrawn grounds. *Fix:* delete the
clause. "One legible row, no row privileged, whole column printed beside it" needs no
justification bolted on. Source: `pipeline/r8_choice_geometry.py:110` and
`THRESHOLD_STATUS`.

**D4. The A11 sweep's method text is false and one published envelope cell is wrong.** The
page claims "Lock and Kimba are displaced independently, so every combination of the two
bearings is evaluated and the reported extremes are the true extremes over the grid".
`pipeline/r8_choice_geometry.py:804-806` filters **both** sites to `offset_km == d`, so the
two *magnitudes* are locked together — only bearings vary, hence 129 = 1 + 2·8·8 rather
than 289 = 17·17. Mixed configurations (Lock 5 km, Kimba 2.5 km — both inside A11's own
tolerance) are never evaluated. Run properly (`r8a_coord_sensitivity.py`, CHECK 2), the
published 45-minute floor **65.8 % is wrong; the true floor is 65.09 %** — in the table
captioned "for a reader who rejects 90 minutes". The 90-minute envelope survives unchanged
(19.94 %–24.58 %). *Fix:* uncouple the offsets in the code, or restate the method as
"bearings independent, magnitudes locked" and stop claiming true extremes.

**D5. The cited independent verification does not exist in the repo, and is not
independent.** `r0_choice_geometry.md:24` rests the headline partly on "an independent
reimplementation with its own graph, Dijkstra and weights". That script (`verify4.py`)
lives only in a session scratchpad, is in no commit (`ls pipeline/verify4.py` → absent),
and the page gives no path and no command — against this repo's own instruction at
`docs/gate_findings.md:52`: "The script currently lives in a scratchpad and must be moved
into `pipeline/` before it is cited anywhere." It also loads the same
`data/processed/roads.graph.json`, the same hardcoded A5 `SPEED` dict, the same snapper and
the same `production_districts.parquet`. It is an independent *coding*, not an independent
data path; a shared-input error reproduces identically. *Fix:* move it into `pipeline/`,
print its command, and relabel it "independent reimplementation of the algorithm over the
same inputs" — or delete the clause.

**D6. `data/ASSUMPTIONS.md` A11 still contradicts the page that cites it.** A11:429-431
still reads "it can only ever make the 2023/24 baseline worse, never better"; the page's
own sweep finds a 19.9 % configuration against a published 20.3 % and says so. A11 also
still says the multiple falls "3.3× → **2.71×**" where the reproducible swept extreme is
**2.72×** (`a11_coordinate_sweep.multiple_range_at_headline_min = [2.72, 3.35]`); **no
command in this repo prints 2.71×**, which breaks this round's own rule. A11 also calls
20.3 % "the 2023/24 headline" while the page's headline is 66.8 %. *Fix:* narrow A11 to the
asymmetry-in-size statement the page already proves (+4.3 pp against −0.3 pp, ≈13:1) and
correct 2.71× to 2.72×.

### Blocking before publication, not before drafting

- `pipeline/r8_choice_geometry.py` and `pipeline/r8a_coord_sensitivity.py` are both
  untracked (`??`). No reviewer can confirm by diff that any round was presentation-only.
  Commit them.
- Two stale corpus counts of the class round 3 fixed elsewhere: `data/CALIBRATION.md:11`
  "parsed from 128 Wayback-archived pages" and `docs/PROGRESS.md:9` "128 archived reports".
  `receivals_weekly.parquet` holds **127** unique `source_file` values = 117 `wayback` + 10
  `bunge-live`. Reproduce:
  `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import polars as pl; df=pl.read_parquet('data/processed/receivals_weekly.parquet'); print(df.group_by('source').agg(pl.col('source_file').n_unique()), df['source_file'].n_unique())"`
  Two one-line fixes.
- `pipeline/manual_sites.json` now carries corrected `closed_2019` notes and sources, but
  `data/processed/sites.geojson` and `app/public/data/sites.geojson` still carry the old
  notes and the Farm-Online-only source arrays. Needs a `pipeline/r1_build_sites.py` re-run.
  R8 is unaffected — it reads only name/operator/role/status/district/coordinates.

## 2. The allowlist — the exact claims the piece may make

Nothing outside this list goes in the draft. Commands run from the repo root.

**R8** = `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe pipeline/r8_choice_geometry.py`
(writes `docs/r0_choice_geometry.md` and `.json`).
**R8A** = `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe pipeline/r8a_coord_sensitivity.py`
(read-only; imports R8's own graph, snapper, Dijkstra and weights).

Every Tier-2 row depends on **A5** (road class speeds), **A14** (district boundaries by LGA
composition, for the tonne weighting) and the **A12** roster in its incumbent-side form.
None depends on A1, A2, A4, A9, A15, A18 or A24 — that independence is exact as of
2026-08-31 and is the whole basis of the tier structure. Extra per-row dependencies are in
the last column.

### Tier 2 — geometry. No simulation, no fitted parameter.

| # | Claim | Number | Command | Also depends on |
|---|---|---|---|---|
| **B1** | **HEADLINE.** Tonne-weighted share of EP grain production with no independent receival point within a 90-minute one-way drive, 2025/26, fixed 2022/23–2025/26 district-mean weights | **66.8 %** — **conditional (D1, D2)**: quotable only as "66.8 %, 61.5 %–67.3 % over the ±5 km tolerance on the Lucky Bay coordinate", and only once the 2025/26 bunker closure is archived | R8; range from R8A CHECK 1 | Lucky Bay coordinate precision (unregistered); T-Ports 2025/26 closure (unsourced) |
| **B2** | **Mandatory beside B1.** The whole 2025/26 threshold column | 30 min 97.1 % · 45 93.2 % · 60 87.4 % · 75 78.2 % · **90 66.8 %** · 105 53.2 % · 120 39.5 % | R8 | as B1. R8A CHECK 1 gives each row's Lucky Bay envelope (60 min 84.1–88.0 %, 120 min 35.2–39.8 %) |
| **B3** | **Mandatory beside B1.** Travel-speed sensitivity, 2025/26 at 90 min | ×0.85 **77.2 %** · ×1.00 **66.8 %** · ×1.15 **54.5 %**; full 3×7 table is on the page | R8 | A5. A *uniform* error is bounded by this band; a non-uniform one is not — say so |
| **B4** | **Mandatory beside B1** — without it B1 carries no information about the incumbent. Tonne-weighted drive to the nearest **Bunge** point, 2025/26 | mean 18.7 min · median 16.5 · p90 33.2 · **p99 58.3** | R8 | — |
| **B5** | Share whose nearest independent point is a **port** | 12.4 % (2023/24) → **100.0 %** (2025/26) | R8 | the mechanism in one row |
| **B6** | Which independent point is nearest, by tonne share | 2023/24: Lock 70.2 % · Kimba 17.4 % · Lucky Bay 12.4 %. 2025/26: **Lucky Bay 100.0 %** | R8 | this row *is* the D1 disclosure — print it |
| **B7** | Mean drive to the nearest independent point | 71.3 min (2023/24) → 124.6 min (2025/26) | R8 | A11 on the 2023/24 leg; Lucky Bay coordinate on both |
| **B8** | 2023/24 level, same row as B1 — supporting, **never bare** | **20.3 %**, A11 range **19.9 %–24.6 %** (published 129-config sweep) or **19.94 %–24.58 %** (289-config, R8A) | R8; R8A CHECK 2 | **A11.** Never quote without the range |
| **B9** | The trajectory | 20.3 % (19.9–24.6) → 66.8 % (61.5–67.3) | R8 + R8A | A11 **and** Lucky Bay. Demoted; the piece leads on B1 |
| **B10** | The multiple | 3.29× published; **2.72×–3.35×** across A11, 2.47×–3.29× across speeds, 1.16×–3.29× across thresholds, with 90 min at the top of that last range | R8 | Three sensitivities each move it by more than a third of its own size. If it appears at all, all three ranges appear with it. Never write "3.3×" |
| **B11** | Gap rows — nearest independent beyond nearest Bunge | >30 min 65.9 % → 91.1 % · **>60 min 33.0 % → 77.3 %** · >90 min 16.6 % → 51.4 % | R8 | **Not roster-invariant** — read 74.4 % before the 2026-08-31 roster fix. Quote only as "on the roster as corrected 2026-08-31". The 2023/24 >60 cell carries A11 range 32.8–38.4 % |
| **B12** | Counterweight — share where the independent point is **nearer** than Bunge | 12.2 % (2023/24) → 4.6 % (2025/26) | R8 | print it; it works against the finding |
| **B13** | Distinct operators on the peninsula | 1 → 2 → 2 | R8 | pre-2019 Ladder B is **undefined**, not 100 % — print it blank and say why |
| **B14** | Weighting sensitivity (the headline is not an artefact of the weights) | own-season 20.2 % → 64.7 % · unweighted 35.8 % → 73.7 % | R8 | tonne-weighted fixed-mean is the conservative reading; the 2023/24 cells also carry the A11 range |
| **B15** | District cut, **Ladder B only**, 2025/26 no independent within 90 min | WEP 98.6 % · LEP 79.7 % · EEP 23.8 % | R8 | Ladder A district columns are barred |
| **B16** | Wharminda worked example, **independent column only** | Lock (T-Ports bunker) **59.4 min** (2023/24) → Lucky Bay (T-Ports port) **74.6 min** (2025/26) | R8 | A11 on the 59.4; Lucky Bay coordinate on the 74.6. Do **not** quote the "nearest four receival points" column — Ladder A, and Tooligie is missing from exactly this country |
| **B17** | Road-snap coverage, for the "your grid is coarse" objection | tonne-wt mean 1.99 km · 44.3 % of production >2 km · 1.3 % >5 km · worst cell 9.47 km · worst **site** 0.65 km | R8 | it cancels out of gap rows and *flatters* threshold rows |

### Tier 1 — published, no model.

| # | Claim | Command / locator | Source |
|---|---|---|---|
| **T1** | Viterra closed **17 up-country sites** statewide in June 2019, **six on Eyre Peninsula**: Minnipa, Kyancutta, Cungena, Waddikee, Kielpa, Wharminda | `data/raw/press/stockjournal_6202314_17-silo-closures_20260831.html`, `..._6202864_upper-ep-silos_20260831.html`; `SOURCES.md` → `viterra-2019-site-closures` | Alisha Fogden, "SILO SLASH: 17 Viterra grain sites to close", *Stock Journal*, 6 Jun 2019 6:00am (upd. 7 Jun 4:21pm); "Croppers angry as upper EP silos take a hit", 6 Jun 2019 1:00pm. Verbatim: "close 17 of its upcountry sites"; "The sites of Minnipa, Kyancutta, Cungena, Waddikee, Kielpa and Wharminda have been closed." Cite the *Stock Journal* originals; the Farm Online copy is the 7 Jun 2019 syndicated reprint |
| **T2** | **Only two of the six were operating the year before** (Minnipa, Kyancutta). Cungena, Waddikee, Kielpa and Wharminda are in the group of 11 "that were not open the year prior" | same cache | same. "Six EP sites closed in 2019", written unqualified, overstates the 2018/19 network by four sites. Never write it unqualified |
| **T3** | Of the six, **five stayed closed; Cungena took first new-season deliveries in 2022/23** on the operator's own weekly report — 1 of 148 parsed operator harvest reports | `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import json;rows=[json.loads(l) for l in open('data/processed/receivals_notes.jsonl',encoding='utf-8')];print(len(rows),len(rows),[r['week_ending'] for r in rows if 'Cungena' in json.dumps(r)])"` → `148 148 ['2022-11-13']` | Viterra weekly harvest report, wk ending 13 Nov 2022; `SOURCES.md` → `cungena-status-contradiction`. Defensible phrasing: *"five EP sites closed in 2019 and stayed closed; a sixth, Cungena, reopened for one season."* **148 is the notes corpus** — not the 128 Wayback page count, not the 127 `receivals_weekly.parquet` source files |
| **T4** | Viterra's **stated reasons**: bigger trucks going to bigger sites; the closed sites were a very small share of receivals | same cache | Operations manager Michael Hill, **direct quotes only**: "Since 2010, the average truck size has increased by 30 per cent and those bigger trucks are delivering to our bigger sites"; "The sites that were closed represented less than 2pc of total receivals (based on a five-year average)". ⚠ "changing delivery patterns of growers" is the journalist's indirect speech — paraphrase, never quote |
| **T5** | The **last grain train ran 31 May 2019** | `SOURCES.md` → `ep-rail-closure-truck-figures-2019` | ABC Rural, Neindorf/Pedler/Martin, 31 May 2019. **Chronology only** — see §3 |
| **T6** | Five roads were named **in advance** as those that would carry the extra grain freight: Tod Hwy, Lincoln Hwy (Arno Bay–Port Lincoln), Balumbah-Kinnard, Wharminda and Western Approach roads | `pdftotext data/raw/press/dit_eyre_peninsula_freight_study_smec_2018_wayback20240329.pdf - \| grep -n "Wharminda"`; `SOURCES.md` → `ep-freight-study-2018`, `port-lincoln-times-ep-freight-study-2019` | *Eyre Peninsula Freight Study*, SMEC ref. 3005591 Rev 0 Final, 26 Sept 2018, for DPTI + Genesee and Wyoming Australia (Table 2; Base Case = all grain to road). Reported by Jarrad Delaney, *Port Lincoln Times*, 10 Apr 2019: the roads affected "**will include**…". ⚠ Future tense, seven weeks before the last train. Match the tense. (The study spells it "Balumbah-Kinnard") |
| **T7** | **~$25 m** of federal road money announced; base case ~$95.5 m investment + ~$50.7 m maintenance | `data/raw/press/portlincolntimes_6012789_ep-freight-study_wayback20230324.html` | *Port Lincoln Times*, 10 Apr 2019, verbatim: "So far about $25 million has been announced by the federal government…". The $95.5 m / $50.7 m totals are cited **to the newspaper**, not to the study — the study's Table 4 cost columns do not survive text extraction |
| **T8** | **RAA**: survey of **more than 1,300** EP road users; road maintenance the biggest concern for **76 %** | `SOURCES.md` → `raa-ep-road-assessment-2024` | RAA media release, 2 Aug 2024, verbatim. The only *post-hoc* road evidence found. Names Cowell-Kimba Rd, Balumbah-Kinnard Rd, Bratten Way, Lincoln Hwy, Tod Hwy, Iron Knob Rd. It does **not** name Wharminda Road |
| **T9** | **$220 m** Aurizon + Viterra application for federal funding to upgrade and reopen Port Lincoln–Cummins and the lines to Wudinna and Kimba | `SOURCES.md` → `aurizon-viterra-rail-proposal-2023` | ABC Rural, 9 Mar 2023, verbatim |
| **T10** | Truck movements attributed to rail's absence — **pick exactly one and name its basis** | `SOURCES.md` → `ep-rail-closure-truck-figures-2019` | Recommended: the operator's own **42,000** "between up-country sites and Port Lincoln annually" (Grain Central, 3 Mar 2023). ABC's **30,000** (31 May 2019) is the 2019 increment. Grain Central, 27 Feb 2019: "up to 50 extra truck movements per day within the town of Port Lincoln" |
| **T11** | EP share of network total across the 2019 boundary: pre-2019 mean **37.3 %**, post-2019 mean **38.4 %** — no detectable step | `npx tsx packages/sim/scripts/r5_validate.ts` | Observed weekly receivals. It validates nothing; use it as the honest counterweight |
| **T12** | ACCC 2021 refused a Bulk Wheat Code exemption for **Port Lincoln and Thevenard** | `data/raw/reference/accc_final_determinations_2021.pdf` | The regulator has already found EP ports lack competitive constraint. The same determinations put Lucky Bay 177 km from Port Lincoln and 412 km from Thevenard and say expressly that "distance, while important, is only one factor" — do **not** stretch them into a cart-range threshold |
| **T13** | **WITHDRAWN pending D2** — the 2025/26 Lock and Kimba bunker closures | — | Listed in round 2 as "published, not assumed". It is not: no `SOURCES.md` entry, no cache, no retrieval date, and no closure evidence at all for Kimba. Restore only when the page is archived and registered. **B1, B2, B3, B5, B6, B7, B11, B15 and B16 all sit on this row.** |

**Off the allowlist, no citation exists in this repo:** the Oct–Dec 2024 Grainflow
acquisition and its 16 Dec withdrawal; the T-Ports sale (~$250 m, Nash Advisory); the Wheat
Port Code sunset and consultation; "Bunge completed the Viterra acquisition Aug 2025". All
four are in the plan; none is registered in `data/SOURCES.md`. Source them or leave them
out. An adjacent citation is not an option.

**Off the allowlist by explicit decision:** ESCOSA's 2019 SA bulk grain supply chain report
does publish a marginal trucking schedule (A$0.12/t-km to 50 km, A$0.11/t-km 50–250 km,
from AEGIC data; `data/raw/reference/escosa_grain_supply_chain_2019.pdf`, text line ~2536).
It is SA-wide rather than EP-specific and it is a **cost rate, not a cart-range threshold**.
It must not be used to re-designate 90 minutes or to rehabilitate A18 — that is exactly the
adjacent-citation substitution the ground rules forbid. Recorded here so nobody rediscovers
it and reaches for it. A18's flat "No single public EP $/t-km schedule exists" could be
worded more precisely, but that is an `ASSUMPTIONS.md` edit, not a licence.

## 3. Cut across all three rounds, and why

**Ladder A in its entirety.** Every count-of-receival-points row: "29 → 25 → 23 points",
"at most one point within 30/45/60 min", mean/median/p99 drive to the nearest point, mean
points within R, the 2nd-nearest rows, the per-district Ladder A columns, the Wharminda
"nearest four receival points" column, and the plan's most quotable sentence, "EP has gone
from ~30 receival points to 19 operating ones". Reason: the roster is an Aug-2026 operator
snapshot used as a historical site list. Tooligie, Cowell and Mangalo are absent from
`sites.geojson` altogether and Cungena's `closed_2019` tag is contradicted
(`roster_audit_2026-08.md` §5). The row has been wrong twice. It survives in Appendix A of
`r0_choice_geometry.md` as the audit trail; it is not quotable.

**All of Tier 3.** R5 failed its gate and cannot be re-run into a pass. Test A has no
pre-2022/23 model inputs and no observed geography finer than "the whole peninsula"; Test
B's two verified seasons are both calibration seasons; the held-out season's bunker state is
A15's assumption; the "A24 ridge" sweep varies `luckyBayBias` alone and so runs *across* the
ridge, not along it. Cut +165 / +133 / +186 kt, +6.36 / +7.06 / +6.40 pp, the 17-row
per-site redistribution table, and every site-level ranking (plan §6 forbids it, and A4
gives every site in a district the same capacity anyway).

**"3.3×" as a headline.** 90 min is the argmax of the ratio across the published grid
(1.16× / 1.41× / 1.75× / 2.38× / **3.29×** / 3.22× / 2.84×) and the repo holds no record of
the threshold being registered before the sweep was run. Demoted to B10, and never without
its three ranges.

**Any a priori designation of 90 minutes.** Both grounds withdrawn 2026-08-31: the cartage
ground rested on A18's 0.07–0.13 A$/t-km described as a "published range" when A18's own
entry says no such schedule exists; the working-day ground rested on A2's 12 h dispatch
window, a fitted simulation parameter that would have falsified the tier-independence claim.
Nothing replaced them, and **nothing may** — see D3. 90 minutes survives only as the row the
headline quotes, with the whole column printed beside it.

**Any causal link between the May 2019 rail shutdown and the June 2019 closures.** Neither
*Stock Journal* story attributes the closures to rail or freight redirection; "freight
redirection" survives only in a URL slug. Rail is mentioned once across both stories, by a
grower, about an earlier local closure. Chronology is sourceable; causation is not.
Minnipa's "after EP rail shutdown" clause has been withdrawn from `manual_sites.json` as
unsourced, and Waddikee's "rail-served until May 2019" deleted — Waddikee was not open the
year prior and is not among the freight study's rail stations (Wudinna, Kyancutta,
Warramboo, Lock, Murdinga, Tooligie, Yeelanna; "Waddikee Road" there is a road name).

**"Wharminda Road absorbed the extra truck traffic."** The 2018 study and the 10 Apr 2019
report name it **prospectively** — a forecast finalised eight months before rail ceased,
verb "will include", published seven weeks before the last train. The only post-closure
survey (RAA, 2 Aug 2024) does not name it. A prospective citation may not stand in for the
post-hoc one the sentence needed. Deleted.

**"0.511 Mt T-Ports intake in 2023/24."** Model output, not an observation — A24 says so
explicitly. Delete, or relabel Tier 3.

**The RAA "87 % observed more trucks" figure.** Not in the release text. Unverified.

**"384 kt port + 290 kt bunkers" as a throughput bound.** Those are published *storage*
tonnages (A4). Restate as storage turnover, or drop.

**The RTBU numbers, unless attributed.** "40 to 50 one-way truck movements to replace one
train" and "64,000 60-tonne trucks" come from a union media release campaigning a fortnight
out from a federal election. 64,000 is also the **total** through Port Lincoln (≈1.9 Mt,
matching the study's own 2017 figure), not the rail-replacement increment.

**Intent, price and queue claims.** No claim that the Lock/Kimba closures were strategic — a
drought year and bunker economics are entirely plausible, and the piece should say so. No
farm-gate price effect. No absolute queue or turnaround times (A2).

## 4. The opening

**The piece opens on the 2025/26 level — B1 — and cannot open on it yet.** D1 and D2 both
sit upstream of the first sentence: the number needs its Lucky Bay range attached, and the
network state behind it needs a source. Draft the rest; leave the lede until they clear.

The 2019/rail hook is dead and stays dead (§3) — and Wharminda is one of the four sites that
were **not** operating the year prior, so "the site shut in 2019" is the wrong tense as well
as the wrong claim.

The shape that survives, once D1 and D2 clear, opens on the geometry and needs no press
citation. Start at Wharminda with B16 — the nearest place a grower there can deliver to
somebody other than Bunge went from a bunker 59 minutes away to a port 75 minutes away on
the far side of the peninsula — then widen to B1 **paired with B4 in the same breath**,
because B1 alone carries no information about the incumbent: two thirds of EP grain
production has no non-Bunge option inside 90 minutes, against a median 16.5-minute run to
the incumbent and a 99th percentile of 58.3. Use the road study as a second beat, in its own
tense, never as the hook.

## 5. Defects a hostile reader can still raise — and the answer

| Defect | Answer |
|---|---|
| **"Your headline is a distance to one port. It would be identical if Bunge ran 3 EP sites or 200"** | **No good answer, and it is the strongest attack on the piece.** It is arithmetically correct: B1 is a pure function of the drive to Lucky Bay, which is *why* it is roster-invariant, and it rises when the **entrant** closes sites. The only mitigation is discipline — B4 travels with B1 in every quotation, so the level is always read against a median 16.5-minute run to the incumbent, and the definitional section already says the finding is about the option set, not intent. If the piece ever prints B1 alone it misleads, and the page's current instruction ("the only number on this page that needs to be quoted") invites exactly that. Fix the instruction. |
| **"Your headline moves 5 pp if Lucky Bay's coordinate is 5 km out, and you never said so"** | **No answer until D1 is fixed.** True as the page stands: 61.5 %–67.3 % (R8A). Publish the envelope, register the precision, drop the coordinate-independence language. Then the answer is "we swept it and published the band." |
| **"Where is the source for the bunkers being closed?"** | **No answer until D2 is fixed.** There isn't one: a hand-typed note from a live off-season page read, no archive, and nothing at all for Kimba. Archive and register it, or do not publish the 2025/26 state. |
| **"90 minutes was chosen because it flatters you"** | Two thirds right. No threshold is designated a priori — both grounds were withdrawn and none replaced them — and the full 30–120 sweep is published, still 39.5 % at the most generous row. But the page's replacement reason is false (D3) and 90 min *is* the argmax of the ratio. Delete the false clause and the honest answer stands: one legible row, no privilege, whole column beside it. |
| **"Your A11 sweep didn't sweep what it says it swept"** | Correct on method (D4): magnitudes are locked, 129 not 289, and the published 45-minute floor is 65.8 % where the true one is 65.09 %. The 90-minute envelope is unaffected. Fix the loop or fix the sentence — do not leave a "true extremes" claim the code does not support. |
| **"Your 'independent reimplementation' isn't in the repo"** | Correct (D5), and it shares the graph, the speed dict and the weights, so it is an independent coding, not an independent data path. Move it or delete the clause. |
| **"Your own assumption file says the opposite of your page"** | Correct (D6). A11 still says "never better" and "2.71×". Narrow A11. |
| **"Your road speeds are assumed"** | They are (A5), the levels are materially speed-dependent, and ×0.85 / ×1.00 / ×1.15 is a standing row, not a footnote. Direction and sign survive. A **non-uniform** speed error is not bounded by that band — say so. |
| **"Your site roster is wrong"** | It is, and the count ladder is withdrawn entirely because of it. Threshold rows measure distance to an *independent* point and every roster defect **on record** is incumbent-side — but that is an argument from absence, and `roster_audit_2026-08.md` sets its own rule that absence proves nothing. Nothing in this repo audits the independent side. An unlisted non-Bunge receival point would move 66.8 % down. Weak answer: say "we have not found one", never "there is none". |
| **"Surely the gap row is roster-invariant too"** | No, and the page now says so: the gap is measured **from** the incumbent, and the 2026-08-31 correction moved it 74.4 % → 77.3 % (2025/26) and 32.9 % → 33.0 % (2023/24). Quote B11 only with its roster date. |
| **"44 % of your production cells snap more than 2 km to the road graph"** | True, tonne-weighted mean 1.99 km. It cancels out of the gap rows, and on the threshold rows an understated drive time makes a cell **more** likely to sit inside 90 minutes — it flatters the network, working against the finding. |
| **"Pre-2019 looks better than 2025/26 on your own chart"** | Ladder B is *undefined* pre-2019: one operator, nothing independent to be far from. Printed blank, never as 100 %, precisely so the 2019 closures cannot read as an improvement in choice. |
| **"You've called a drought a monopoly"** | Production is held fixed at the 2022/23–2025/26 district mean; on each state's own harvest it is 20.2 → 64.7 % and unweighted 35.8 → 73.7 %. And the piece says plainly that the bunker closures are consistent with a drought year and bunker economics. The claim is about grower choice, not intent. |
| **"Nearest is not available"** | Correct, and conservative for the incumbent: a site that does not segregate the grade being carted is still counted here as a choice. This is drive time, not commercial terms. |
| **"The 2024/25 bunker closure is an assumption"** | It is (A15), and it is not one of the three states. 2023/24 is published; 2025/26 is D2. |
| **"Your Cungena claim contradicts your own source"** | Both sources are real, published, unretracted and contradictory, and we print the contradiction: closed June 2019 and described as permanent; first new-season deliveries in 2022/23 on the operator's own report; no evidence of operation in any other season. |
| **"The 2019 closures were caused by the rail shutdown"** | Not according to either source. The company gave truck size and a sub-2 % receivals share. We report the chronology and refuse the causation. |
| **"Every number is measured between published site locations"** | **False as the page words it** (`r0_choice_geometry.md:273`) and it should be deleted. Lock, Kimba and Lucky Bay are all town/hamlet nodes, and the cell-level weighting is a modelling step (district tonnage × CLUM cropping-ha share, A14), not a published quantity. |
| **"Show me the code"** | `pipeline/r8_choice_geometry.py` and `pipeline/r8a_coord_sensitivity.py` are both untracked today. Commit them, or no reviewer can check by diff that the method was not touched. |

### What would make it READY

D1 and D2 cleared — Lucky Bay's envelope published and its coordinate precision registered
in an assumption; the T-Ports 2025/26 closure archived, registered with a retrieval date and
evidenced for Kimba as well as Lock. The false sentences at D3, D4 and D5 deleted or
corrected. A11 narrowed at D6. Both pipeline scripts committed. Nothing else in §2 is
disqualified by the refutations. The number is sound; the page around it is not yet.
