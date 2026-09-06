# Gate findings — "One gateway" (EP competition piece)

Date: 2026-08-31. Inputs: R5 (`docs/r5_validation.md`), R0 (`docs/r0_choice_geometry.md`),
three adversarial verification passes. Working tree only — nothing committed.

## 1. VERDICT

**NO-GO. Publish on Tiers 1–2 only, and Tier 2 ships in reduced form.**

R5 failed the gate on its own terms and the verifier could not break that failure: Test A
(the 2019 six-site closure) cannot be run at all — there are no model inputs before
2022/23, and the finest observed geography in this repo is one weekly number for the whole
peninsula — while Test B's apparent match rests on two seasons that are both *calibration*
seasons, so the quantity that agrees with observed data agrees by construction and has zero
out-of-sample content. Worse, the gate did not only fail for Tier 3: a third verifier
independently reproduced R0's geometry and found that **Ladder A of the Tier-2 headline
table is wrong**, because five Bunge sites tagged `dormant` from an off-season 2026 web
scrape are shown taking harvest deliveries in Bunge's own weekly reports already sitting in
this repo. Ladder B — the ownership-distance headline, which is the number the piece is
actually built on — survived every attack unchanged and is publishable; Ladder A, the
"29 / 21 / 19 receival points" row and the EEP district claim must be pulled and rebuilt
before anything goes to a regulator or a right-of-reply round.

## 2. Headline geometry (Tier 2)

Tonne-weighted share of EP production, fixed 2022/23–2025/26 district-mean weights.

| Row | pre-2019 | 2023/24 | 2025/26 | status |
|---|---|---|---|---|
| **B.** No independent receival point within 90 min | _undefined — single operator_ | **20.3 %** | **66.8 %** (3.3x) | **HOLDS** — independently reproduced to 0.05 pp |
| **B.** Nearest independent >60 min beyond nearest Bunge | _undefined_ | 32.9 % | 74.4 % | direction holds; level moves to 33.0 % → 77.3 % on the corrected roster |
| **B.** No independent within 60 min | _undefined_ | 50.0 % | 87.4 % | holds |
| **B.** No independent within 120 min | _undefined_ | 13.9 % | 39.5 % | holds |
| **A.** Only one receival point within 45 min | 9.5 % | 13.7 % | 25.4 % | **WRONG** — corrected: 9.5 % → 8.3 % → 12.1 % |
| **A.** Mean drive to nearest point (min) | 17.5 | 20.3 | 20.5 | **WRONG** — corrected: 17.5 → 17.5 → 17.9 |
| Receival points on EP | 29 | 21 | 19 | **WRONG** — >=26 and >=23 on published receivals |

Ladder B is invariant to the site-roster defect by construction: the five mis-tagged sites
are all Bunge, and "distance to the nearest *independent* point" does not move when a Bunge
site is added. That is why one half of the table survives and the other does not.

Reproduce, from the repo root:

    .venv/Scripts/python.exe pipeline/r8_choice_geometry.py       # R0 as published
    npx tsx packages/sim/scripts/r5_validate.ts                   # R5, all four seasons
    npm --workspace packages/sim run test                         # 17 passed

Corrected-roster recomputation (independent reimplementation — own graph, own Dijkstra, own
weights; reproduces the published figures, then re-runs with the mis-tagged sites restored):

    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \
      "$TEMP/claude/C--Users-justi-grain-simulation/900d2be2-2d5a-4ac0-ba23-07386313efb0/scratchpad/verify4.py"

I re-ran that script myself for this verdict. It prints, one line each:
`2023/24 corrected pts=26 mean-nearest 17.5 <=1pt45 8.33% | no-ind-90 20.28% gap>60 33.04%`
and `2025/26 corrected pts=23 mean-nearest 17.9 <=1pt45 12.10% | no-ind-90 66.79% gap>60 77.30%`.
The script currently lives in a scratchpad and must be moved into `pipeline/` before it is
cited anywhere.

## 3. What the validation established, and what it did not

**Established.**

- The engine change is a genuine no-op at `networkState: null`: event-log hashes for all
  four seasons are byte-identical before and after (`811c9dc5`, `1708d201`, `213b5991`,
  `5a6455d1`), `calibrated.json` is untouched in the diff, and `docs/calibration_report.md`
  regenerates byte-identical. No knob was nudged to make anything pass.
- R0 uses no fitted parameter. It reads `roads.graph.json`, `sites.geojson`,
  `production_districts.parquet` and `parcels.json`, and nothing from `calibrated.json` or
  `engine.ts`. Tier 2's independence from the model is real.
- Ladder B's definitional handling is correct: pre-2019 emits `"defined": false` with a
  reason rather than a number, so the 2019 closure can never be read as an *improvement* in
  competitive choice. Ladder B is robust to reweighting (ha², √ha, equal-per-cell, dropping
  small cells: 3.1x–3.4x), and the times are genuinely routed, not straight-line.
- **Tier-1 observation that survives everything:** EP share of network total across the 2019
  boundary — pre-2019 mean 37.3 %, post-2019 mean 38.4 %. No detectable step. Publishable as
  stated. It validates nothing.

**Not established.**

- **Test A cannot be run.** Four independent blockers, any one of which is fatal:
  `production_districts.parquet` starts 2022/23 and `climate_daily.parquet` starts
  2020-09-01, so no pre-closure season has model inputs; observed receivals carry no
  geography below `region ∈ {total, western, central, eastern}` where *western is the whole
  peninsula*, so a site-level redistribution test has zero resolving power and there is no
  weaker valid version of it; the six closed-2019 sites are absent from `matrix.json` and
  carry `capacity_t: null`, and A4's capacity total is derived from post-closure receivals
  so re-deriving theirs is circular; and grain rail ceased May 2019 in the same season the
  sites closed, both EP-only, making the two **perfectly collinear** — a DiD against
  central/eastern returns one number for everything EP-specific in 2019 and cannot attribute
  any of it. Closing the data gap (fetching pre-2022/23 PIRSA and ERA5) would not reopen the
  gate; blockers 2 and 4 survive untouched. Only a site-level receival series would.
- **Test B has no out-of-sample content, structurally.** `CAL_SEASONS = ["2023/24",
  "2025/26"]`, `holdout: "2024/25"`. Both seasons with a *verified* bunker state are
  calibration seasons; the one held-out season's bunker state is A15's *assumption*. There
  is no season that is both held out and verified, and no amount of further running creates
  one. The model's between-season shift (+5.46 pp) matching observed (+5.35 pp) to 0.11 pp
  is trivial — both endpoints are fitted targets. The unfitted quantity (+6.40 pp, a
  within-2025/26 counterfactual) has no observational counterpart at all.
- **The held-out pass is circular.** 2024/25 is −9.1 % with bunkers open and −0.3 % with them
  closed; A15 was adopted partly *because* of that residual (its own note says the model
  "under-delivers ~8–10 % without it"). It is not evidence for the model.
- **The observed data do not order by treatment.** Bunge share of EP production: 2022/23
  open 78.73 %, 2023/24 open 72.02 %, 2024/25 closed-assumed 79.78 %, 2025/26 closed
  77.37 %. The open pair straddles the closed one — 2022/23 with bunkers *open* sits 1.4 pp
  above 2025/26 with them closed.
- **Confound that could not be separated (Test B).** T-Ports intake is bounded by physical
  throughput, so its *share* necessarily falls in a big crop year whether or not anything
  closed. 2022/23 is 4.149 Mt against 2025/26's 2.907 Mt. With n = 2 per arm, one of which
  is an assumption, this mechanism alone could produce the observed ordering with no
  behavioural content, and nothing in this repo separates it from the closure effect.
- **Redistribution topology is completely untested.** No site-level observed receivals exist
  in this repo at any granularity, structured or narrative. Every per-site Δ kt in R5's
  counterfactual table is unvalidated model output.
- **The one "robustness" range is not the range it is labelled as.** The sweep varies
  `luckyBayBias` alone with `retentionShare` frozen at 0.0553. A24's ridge *is* the
  retention↔luckyBayBias trade, so this runs across the ridge, not along it, and every swept
  point is an off-fit vector. The claim that the effect is "more robust than A24's warning
  implies" is not supported by what was run.

## 4. Outstanding defects — none of these are fixed

Listed as found. Nothing below has been repaired in this working tree.

### Blocking — Tier 2 (R0 and the site roster)

1. `pipeline/r1_build_sites.py:176` derives operating status from an empty
   `segregations_2025_26` list in `pipeline/manual_sites.json`, captured from a live
   bunge.com.au table on 2026-08-19 — off-season, eight months after the 2025/26 harvest. An
   empty off-season segregation table is being read as "this site did not operate".
2. `data/processed/receivals_notes.jsonl` refutes the tag directly. Week ending 2025-11-16:
   "Harvest kicked off at our Buckleboo, Elliston, Penong, Poochera and Warramboo sites";
   week ending 2025-11-23 adds Darke Peak. All five also took first 2023/24 loads (Penong
   08 Oct, Nunjikompita 15 Oct, Buckleboo + Elliston 22 Oct, Darke Peak 29 Oct 2023). So
   "19 operating points in 2025/26" is wrong (>=23), "21 in 2023/24" is wrong (>=26), and
   R0's caveat that the plan's "19 operating" *reconciles exactly* is false.
3. Consequences, reproduced above: Ladder A's headline row becomes 9.5 % → 8.3 % → 12.1 %,
   i.e. the 2023/24 column falls **below** pre-2019 and the monotone worsening disappears;
   mean nearest becomes 17.5 → 17.5 → 17.9; the EEP district claim "more than quadruples"
   (10.5 % → 46.1 %) becomes 9.1 % → 13.6 % and is essentially an artefact of Darke Peak
   being dropped.
4. `sites.geojson` omits **Tooligie** entirely, though `receivals_notes.jsonl` records it
   taking first deliveries in 2022/23, 2023/24 and 2024/25. **Mangalo** is likewise absent
   though it opened for first receivals in 2018/19, so pre-2019 is >=31 points, not 29 — the
   plan's "~30" was closer to right than the repo was. **Cungena** is tagged `closed_2019`
   but appears in the 2022/23 first-receivals list. The roster in `data/raw/operator_sites/`
   is a 23-entry August-2026 snapshot being used as a historical site list.
5. `pipeline/r8_choice_geometry.py:363` uses `c <= 1`, so cells with **zero** points inside
   the radius are counted in the "only one point within" rows. Pre-2019's 9.49 % is 6.30 %
   exactly-one plus 3.19 % zero. The row label must read "at most one".
6. `pipeline/r8_choice_geometry.py:880` discloses that the dormant sites are treated as
   *open* pre-2019 (with a sensitivity row) but never discloses the converse, load-bearing
   assumption — that they are treated as *closed* in 2023/24 and 2025/26. That is the
   assumption the repo's own receivals reports contradict, and it is unswept.

### Material — Tier 2 (R0 caveats that are themselves wrong or incomplete)

7. R0's caveat that "a uniform speed error largely cancels on Ladder B" is **false** for the
   rows actually published, because both are thresholded in absolute minutes. Scaling A5
   uniformly, the 90-min headline row reads 31.3 % → 77.2 % at x0.85 speeds and 16.7 % →
   54.5 % at x1.15, a multiple ranging 1.82x–3.29x. Direction survives; levels are materially
   A5-dependent and the caveat must say so.
8. 3.3x is the **maximum** of the disclosed cart-range sweep, and the chosen threshold sits
   exactly on the peak: 30 min 1.16x, 45 min 1.41x, 60 min 1.75x, 75 min 2.38x, 90 min 3.29x,
   105 min 3.22x, 120 min 2.85x. Levels rise at every threshold so the finding is safe, but
   "3.3x" is the single most favourable framing available; lead with a level, not the
   multiple.
9. `docs/r0_choice_geometry.md:161` asserts "Wharminda Road is named in the reporting as one
   of the roads that absorbed the extra truck traffic" with no outlet, date or URL, and no
   supporting source anywhere in the repo. This is the worked example the headline is built
   around. It cannot run unsourced in a piece that names Bunge.
10. Minor, verified non-material: the node snapper picks the nearest node in raw degree space
    with a 3x3 ring cutoff rather than in km globally; 327 of 5,324 cells resolve differently
    under an exact search, moving the headline <=0.05 pp. 44.3 % of production snaps >2 km to
    the graph and the snap leg is undriven, which understates absolute minutes in both columns
    of the 90-min row.

### Material — Tier 3 / R5 presentation

11. `docs/r5_validation.md` has **no carried-assumptions section at all**, yet every Tier-3
    number comes out of `chooseSite`, which weights candidates by A2's fitted bays and 12-min
    cycle (`engine.ts:878`) and gates them on A1's payload and A4's capacity (`engine.ts:869`,
    `:840`). A2 is the assumption plan §6 names as the biggest data gap in the project. R0
    carries an explicit assumptions section; R5 does not.
12. Tier-3 point estimates published where the plan requires ranges: +165 / +133 / +186 kt and
    +6.36 / +7.06 / +6.40 pp are bolded single values, and the 17-row per-site redistribution
    table gives Δ kt to 0.1 kt un-ranged. Only the 2025/26 Δ pp is ranged at all.
13. `packages/sim/scripts/r5_validate.ts:177` labels its sweep "across the A24 identification
    ridge"; line 192 varies `luckyBayBias` only. Mislabelled; the conclusion drawn from it
    (`r5_validation.md:251`) must be withdrawn or the sweep redone on paired values.
14. `r5_validate.ts:138` prints the 2024/25 closed arm as "(state matches observed)". That
    state is A15's assumption. The write-up says "assumed"; the script anyone re-runs prints
    "observed".
15. `r5_validation.md:230` calls "384 kt port + 290 kt bunkers" a **throughput** bound. Those
    are published *storage* tonnages (A4); A24 records ~16 Lucky Bay shipments a season at
    ~26 kt, i.e. ~0.42 Mt already moving through a 384 kt store. The sentence is load-bearing
    — it is the mechanical alternative offered against the observed season ordering — so it
    must be restated as a storage-turnover argument or dropped.
16. The counterfactual table ranks 17 named sites by modelled Δ tonnage and singles out two
    Bunge sites by name. Plan §6 forbids "any ranking of individual site performance", and
    A4's own known limit says every site inside a district carries the same modelled capacity,
    so ordering among same-district sites is an allocation artefact.
17. `docs/calibration_search.json` stores only `calSeasons`, `holdout`, `ranges`,
    `evaluations: 600`, `best`, `bestScore` — **no per-evaluation records**. R1 as written
    ("the paired LB value from `docs/calibration_search.json`") cannot be executed. R1 needs a
    re-run of the search with evaluation logging, or a different pairing rule.

## 5. Required changes to `docs/analysis_plan_ep_competition.md`

Described, not made — the plan is not edited under this workflow's ground rules.

- **§2, line 46 — remove a Tier-3 output from the Tier-1 opening.** "They ran in 2023/24
  (0.511 Mt T-Ports intake)" states this model's own output as observed fact. The 2023/24
  bunkers-open run returns exactly 0.511 Mt; the figure's only other appearance is
  `data/ASSUMPTIONS.md:701`, where A24 explicitly calls it *modelled* and uses it to argue
  the fitted `luckyBayBias` sits at the top of what the evidence supports. Published T-Ports
  intake is listed in the plan's own §5 as an unclosed data gap. Delete the figure, or
  relabel it "modelled, Tier 3, A24".
- **§2, the site-inventory table (lines 26–34) — correct it.** The `dormant` row is wrong:
  those five sites received grain in 2023/24 and four of them in 2025/26 per Bunge's own
  weekly reports. Tooligie and Mangalo are missing from `sites.geojson` altogether and
  Cungena's `closed_2019` tag is contradicted. Restate as "32 features, roster derived from an
  Aug-2026 operator snapshot and **not** a per-season site list; corrected season sets
  pending".
- **§2, line 50 — withdraw "EP has gone from ~30 receival points to 19 operating ones".** On
  published receivals it is >=31 → >=23. That sentence is the plan's most quotable line and it
  is wrong in both terms.
- **§3, Tier 2 — narrow the headline to Ladder B.** Tier 2 currently promises drive time to
  the nearest Bunge point vs the nearest independent one (Ladder B, which holds), but the R0
  output people will read leads with a receival-point count and a choice-count ladder
  (Ladder A, which does not). State explicitly that the count ladder is out until the season
  site sets are rebuilt, and that Ladder B is undefined pre-2019 and must never be shown on
  the same axis as Ladder A.
- **§3, Tier 3 — restate from "publishable if R5 passes" to "not publishable".** R5 has run
  and failed. Tier 3 becomes a labelled sensitivity note only, with the reason on the page:
  no out-of-sample season exists, and none can be created from this repo.
- **§4, R5 — mark Test A closed-impossible, not pending.** Record the four blockers, and
  record that fetching pre-2022/23 PIRSA production and ERA5 weather would *not* reopen it.
  The only thing that would is a site-level receival series.
- **§4, R1 — fix the infeasible instruction.** The paired `retentionShare` / `luckyBayBias`
  values it calls for are not in `docs/calibration_search.json`. Either add evaluation logging
  and re-run the search, or specify a different pairing rule.
- **§5 — add A12 to the data-gaps list, at the top.** "Season site sets" is currently a
  one-line assumption whose stated sensitivity is "small re-routing effects in early seasons".
  It is in fact the load-bearing input to the Tier-2 count ladder, and it is contradicted by
  data already in the repo. Add A5 as well: the Ladder B *levels* are materially
  speed-dependent even though the direction is not.
- **§6 — add two prohibitions.** No unsourced press claim (the Wharminda Road line has no
  citation anywhere in the repo), and no reporting of the 3.3x multiple without the underlying
  levels and the threshold sweep beside it, since 90 minutes is the peak of that sweep.
- **§7 — the day-2 gate has been reached and the answer is no.** Days 3–5 (R1–R4) are Tier-3
  work and should be deferred behind the R0 roster rebuild, which is now the critical path for
  the piece that can actually be published.
