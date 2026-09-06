# R5 — retrospective validation (the go/no-go gate)

Run 2026-08-31 against `docs/analysis_plan_ep_competition.md` §4. Nothing here was
refitted: every simulated number is produced at the existing fitted vector
(`{...defaultParams(), ...packages/sim/src/calibrated.json.params}` — the same
construction `docs/calibration_report.md` uses), seed 42, 365 days.

## Verdict

**NO-GO on R5 as specified. Publish on Tiers 1–2.**

- **Test A (2019 closure of six sites) cannot be run at all.** Not "runs and fails" —
  cannot be run. Four independent blockers, any one of which is sufficient (§2). The rail
  confound the plan flags is real, but it is not the binding problem: the binding problem
  is that the model has no inputs for any pre-closure season and the observed series has
  no geography below "the whole Eyre Peninsula".
- **Test B (T-Ports Lock/Kimba bunkers) runs, and the model behaves correctly, but the
  test has no out-of-sample content and its observed side does not order by treatment**
  (§3). It is a coherence check that passes, not a validation.

The plan's own fallback therefore applies verbatim: *"cut Tier 3 to a sensitivity note,
and publish on Tiers 1–2 alone."* Tier 3 ranges produced here are usable as a labelled
sensitivity note; they are not a track record.

One further finding that affects the piece directly, independent of the gate: **the
"0.511 Mt T-Ports intake" the plan cites in §2 as a fact about 2023/24 is a model output,
not an observation** (§5). It must not be cited as evidence.

## What was built

`Params.networkState: { forceOpen?: string[]; forceClosed?: string[] } | null`
(`packages/sim/src/types.ts`), defaulted to `null` (`params.ts`), consulted in the
site-build loop (`engine.ts`, after the existing `status`/season rules, which it
overrides).

Before this, which sites operate was not a parameter at all. `Sim.init()` derived it from
the bundle's static `status` string plus a **hardcoded season-string match** —
`season === "2025/26" || season === "2024/25"` closes the two T-Ports bunkers (A15) — so
"season" was two different things wearing one label: which demand/weather/observed bundle
to load, and which sites exist. A run could not ask "this season's crop against a
different network" without editing the engine. R3's `siteClosures` (plan §4) is now
`networkState.forceClosed`.

Two deliberate hard failures, because both silent alternatives produce a plausible-looking
number for a network state that was never applied — the defect class of #20 and #29:

1. a name matching no site in the bundle **throws**;
2. `forceOpen` on a site with an empty segregation list **throws**. `chooseSite` skips any
   site whose `accepts[c]` is false, so such a site would sit in the network looking open
   and receive zero tonnes all season. This is the normal case, not an edge one: the
   dormant Bunge site and all six closed-2019 sites carry `commodities: []`. Reopening
   any of them needs an assumed segregation list in the **data** first (A12-style).
   *(Amended 2026-09-06: the check now applies to every open non-port site, not only the
   `forceOpen` path. When this document was written the A12 roster correction had
   reopened four Bunge sites by `status` with exactly this empty list, so the engine
   opened them, routed nothing to them, and seeded them carry-in — the defect this rule
   describes, reached by the other door. Every arm in the grid below was run against
   that network; see A12 in `data/ASSUMPTIONS.md`.)*

`forceClosed` beats `forceOpen`, so the result never depends on list order.

### Regression status — explicit

- `npm --workspace packages/sim run test` → **17 passed** (13 pre-existing, unchanged, +4
  new for the override). Baseline before the change was 13 passed.
- **Every calibrated run is byte-identical.** Event-log hashes at `defaultParams()`,
  seed 42, before and after the engine change: 2022/23 `811c9dc5`, 2023/24 `1708d201`,
  2024/25 `213b5991`, 2025/26 `5a6455d1`. Unchanged in all four.
- **`docs/calibration_report.md` regenerates byte-identical** (`npx tsx
  packages/sim/scripts/report.ts`, then `diff` against the committed file — no content
  difference; the regenerated copy was reverted so the working tree carries no spurious
  change). All targets in it still hold: 2023/24 −0.4 %, held-out 2024/25 −0.3 % (±5 %
  criterion: PASS), 2025/26 −0.2 %, vessel counts ±0.0 % (PASS).

## §2 — Test A: why it cannot be run

The plan asks for the pre-2019 network, the six sites closed, and the simulated
redistribution checked against observed receivals at surviving neighbours. Four blockers,
in order of how fatal they are:

**1. There are no model inputs for any pre-closure season.** The sim needs
`demand_{season}.json` and `weather_{season}.json`. Both exist only for 2022/23–2026/27:

| season | demand | weather | observed | runnable |
|---|---|---|---|---|
| 2016/17 … 2021/22 | no | no | no | **no** |
| 2022/23 – 2025/26 | yes | yes | yes | yes |

Upstream: `production_districts.parquet` covers **2022/23–2025/26 only** (the PIRSA crop
and pasture reports in `data/raw/pirsa/` start at 2022/23), and `climate_daily.parquet`
starts **2020-09-01**. The three pre-closure seasons the test needs (2016/17, 2017/18,
2018/19) have an observed *target* and no *inputs*. Building them is a data-collection
project (ERA5 re-fetch is mechanical; pre-2022/23 PIRSA district production is not in the
repo at all), not a modelling one.

**2. The observed series has no geography below the whole peninsula.** `region` in
`receivals_weekly.parquet` takes four values — `total`, `western`, `central`, `eastern` —
and `western` **is** the Eyre Peninsula (`data/CALIBRATION.md`: *"Western is EP-only"*).
All six closed sites and every surviving neighbour sit inside that one bucket, so the
redistribution the test is about is invisible by construction. This also disposes of the
data scout's proposed region-level fallback: aggregating simulated redistribution to
western/central/eastern has **zero** resolving power here, because the entire redistribution
happens *within* `western`. There is no weaker-but-still-valid version of Test A; there is
no version.

**3. The six sites are not in the engine's input.** `sites.geojson` carries 32 features;
`matrix.json` carries 26. The six `closed_2019` sites (Minnipa, Kyancutta, Cungena,
Waddikee, Kielpa, Wharminda) are dropped by `pipeline/p2_build_matrix.py`. Adding them
back is not just a pipeline edit: they carry `capacity_t: null` and `commodities: []`, so
they need an invented capacity and an invented segregation list. The capacity is worse
than invented — it is **circular**. A4's storage total is derived from *max Western season
receivals (2022/23) minus published Western port storage*, i.e. from a network that had
already lost these six sites for three seasons. Spreading that same total over a 27–32
site pre-2019 network systematically understates what that network held.

**4. The rail confound, as the plan anticipated — and it is unresolvable here.** Grain
trains ceased May 2019, between the 2018/19 and 2019/20 harvests; the six sites closed the
same year. Both treatments are EP-only and land on the same season boundary, so in the one
observed series that exists they are **perfectly collinear**: there is no estimator, not a
weak one. A difference-in-differences against central/eastern SA (where rail continued)
removes common weather and price shocks but still returns a single number for
*everything EP-specific that changed in 2019* — it cannot attribute any of it to site
closure rather than rail. And the model cannot supply the missing arm, because of blocker 1.

**Cannot separate. That is the finding**, and it stands independently of blockers 1–3.

**No qualitative fallback either.** `receivals_notes.jsonl` (148 weekly-report narratives,
2016/17 on) mentions the six closed sites essentially never: Kyancutta 2 (one of them
*after* closure), Cungena 1 (2022/23, after closure), Wharminda 1 (2016/17), and Minnipa,
Waddikee and Kielpa **zero times each**. There is no anecdotal spot-check set.

**What was deliberately not done, and why.** I did not rebuild the pipeline to include the
six sites. It cannot make Test A feasible (blockers 1, 2 and 4 all survive it), it would
require two invented data fields plus a circular capacity, and `matrix.json` is not
season-keyed so it would change every season's run. Re-adding them for **R0** is a
different and much better-founded proposition — R0 is pure geometry and needs only
coordinates, which those six sites have (town-level, A11-style, ≤5 km).

### One Tier-1 observation that survives (no model)

EP's share of the Viterra/Bunge network total, straddling 2019:

| season | western t | network total t | western share |
|---|---|---|---|
| 2016/17 | 3,210,369 | 8,915,725 | 36.0 % |
| 2017/18 | 1,491,641 | 5,394,958 | 27.6 % |
| 2018/19 | 1,820,684 | 3,758,161 | 48.4 % |
| **— six sites close, rail ceases May 2019 —** | | | |
| 2019/20 | 1,517,124 | 3,621,169 | 41.9 % |
| 2020/21 | 1,755,138 | 5,800,852 | 30.3 % |
| 2021/22 | 1,986,890 | 5,644,875 | 35.2 % |
| 2022/23 | 3,266,811 | 8,725,162 | 37.4 % |
| 2023/24 | 1,864,175 | 5,411,487 | 34.4 % |
| 2024/25 | 1,507,275 | 3,239,644 | 46.5 % |
| 2025/26 | 2,249,112 | 5,325,317 | 42.2 % |

Pre-2019 mean 37.3 % (range 27.6–48.4), post-2019 mean 38.4 % (range 30.3–46.5). **No
step is detectable** against season-to-season variation that large. That is publishable as
stated — EP kept delivering about the same share of the network after losing six receival
points — but it is consistent with redistribution to neighbours *and* with several other
stories, and it validates nothing.

## §3 — Test B: what it can and cannot establish

Ran the full season × bunker-state grid, with both states **forced explicitly** through
`networkState` rather than inherited from the season hack.

### Observed (Tier 1, no model)

| season | bunker state | EP production Mt | observed Bunge Mt | Bunge / production |
|---|---|---|---|---|
| 2022/23 | **open** (Lock from 2019, Kimba built for the 2021 harvest) | 4.149 | 3.267 | 78.73 % |
| 2023/24 | **open** | 2.588 | 1.864 | 72.02 % |
| 2024/25 | closed — **ASSUMED, A15, unverified** | 1.889 | 1.507 | 79.78 % |
| 2025/26 | **closed** (published, tports.com/harvest) | 2.907 | 2.249 | 77.37 % |

### Simulated at the fitted vector

| season | state | Bunge Mt | T-Ports Mt | Bunge / prod | error vs observed |
|---|---|---|---|---|---|
| 2022/23 | open | 2.139 | 0.674 | 51.55 % | −34.5 % (state matches observed) |
| 2022/23 | closed | 2.129 | 0.384 | 51.30 % | counterfactual arm |
| 2023/24 | open | 1.857 | 0.511 | 71.73 % | **−0.4 %** (state matches observed) |
| 2023/24 | closed | 2.021 | 0.347 | 78.09 % | counterfactual arm |
| 2024/25 | open | 1.370 | 0.355 | 72.51 % | counterfactual arm (−9.1 % vs observed) |
| 2024/25 | closed | 1.503 | 0.221 | 79.57 % | **−0.3 %** (state matches assumed) |
| 2025/26 | open | 2.058 | 0.604 | 70.79 % | counterfactual arm |
| 2025/26 | closed | 2.244 | 0.418 | 77.19 % | **−0.2 %** (state matches observed) |

> **Addendum 2026-09-06 — this table was run on a roster that had not actually changed.**
> The four Bunge sites the A12 correction reopened (Penong, Darke Peak, Buckleboo,
> Elliston) carried an empty segregation list, so the engine opened them and routed
> nothing to them (A12, "Corrected again"). With the assumed lists in place the same grid
> at the same fitted vector reads: 2022/23 open 2.649 Mt (−18.9 % vs observed, was
> −34.5 %); 2023/24 open 1.954 Mt (**+4.8 %**, was −0.4 %); 2024/25 closed 1.533 Mt
> (**+1.7 %**, was −0.3 %); 2025/26 closed 2.342 Mt (**+4.1 %**, was −0.2 %). The
> near-zero errors above were the fitted vector reproducing the roster it was fitted on;
> the vector has not been refitted since, so those three matched arms now sit 2–5 % high.
> The bunker effect at frozen parameters is essentially unchanged (2023/24 +160 kt / +6.17
> pp, 2024/25 +109 kt / +5.75 pp, 2025/26 +178 kt / +6.13 pp), and nothing about the
> verdict moves: it rests on the observed straddle, which is model-free. Full run in the
> repo history at this commit (`npx tsx packages/sim/scripts/r5_validate.ts`).

2022/23 is unusable and is reported only for completeness: its bundle carries no vessel
program, so the ports never outload, the network jams and the season truncates
(`calibration_report.md` documents this; the −34.5 % row measures the jam). Its bunker
effect (−0.24 pp) is an artefact of the jam, not a result.

### The model's own bunker effect, at frozen parameters

| season | Δ Bunge kt | Δ T-Ports kt | Δ Bunge share pp |
|---|---|---|---|
| 2023/24 | +165 | −165 | **+6.36** |
| 2024/25 | +133 | −133 | **+7.06** |
| 2025/26 | +186 | −186 | **+6.40** |

**What passes.** The mechanism behaves correctly and consistently: closing 290 kt of
independent inland capacity moves 133–186 kt onto the Bunge network, conserved exactly
against T-Ports, and the effect size is stable across three seasons that differ by 54 % in
crop (+6.4, +7.1, +6.4 pp). The observed 2023/24→2025/26 shift is **+5.35 pp**, the same
sign and the same order of magnitude. Nothing in the calibration objective constrains the
counterfactual arms — the objective is Bunge weekly receivals and Port Lincoln shipping,
so where the model puts grain when a competitor's site shuts is unfitted output.

**What fails, and why this is not a validation.**

1. **No out-of-sample season exists.** 2023/24 and 2025/26 are both *calibration* seasons,
   so the state-matching arms match by construction (−0.4 %, −0.2 %). The held-out season
   is 2024/25 — and its bunker state is **assumed** (A15), not observed. There is no
   season that is both held out and has a verified bunker state. This is structural, not
   fixable by more runs.
2. **The 2024/25 pass is circular.** The model under-delivers 2024/25 by **−9.1 %** with
   the bunkers open and by −0.3 % with them closed. A15's own sensitivity note says the
   same thing ("without this the sim under-delivers ~8–10 %"). So the held-out season's
   headline pass rests on an unverified closure that the model's own residual is part of
   the reason for believing. A15 also carries an independent arithmetic-plausibility
   argument, which is why this is circular rather than viciously so — but it is not
   evidence *for* the model.
3. **The observed side does not order by treatment.** Across the four seasons with EP
   production data, the open-bunker seasons read 78.73 % and 72.02 %; the closed ones read
   79.78 % (assumed) and 77.37 %. **2022/23, with both bunkers open, sits above the closed
   2025/26 season.** The two open observations straddle the closed one. If the closure
   really lifted the Bunge share ~6 pp, 2022/23 should sit well below 2025/26; it sits
   1.4 pp above.
4. **n = 2, and both are confounded.** The observed +5.35 pp is a difference between two
   seasons that differ in production (2.588 vs 2.907 Mt), weather, carry-in and vessel
   program — not only in bunker state. The model attributes +6.40 pp of it to the bunkers,
   which requires everything else to net to −1.05 pp. Nothing available checks that. A
   simple mechanical alternative explains the ordering without any behavioural claim:
   T-Ports' intake is bounded by its physical throughput (384 kt port + 290 kt bunkers),
   so its *share* falls in a big year whether or not anything closed.
5. **The redistribution topology is untested.** Site-level observed receivals do not exist
   in any form (§2, blocker 2), so *which* sites absorbed the tonnage — the actual claim
   Tier 3 rests on — has nothing to check against in either test.

### Ranged, not a point estimate (A24)

`luckyBayBias` is the knob that sets how attractive the T-Ports system is, and A24 records
that it and `retentionShare` are not separately identified. Swept over its own published
search range with every other knob frozen (no refitting):

| luckyBayBias | Bunge open Mt | Bunge closed Mt | Δ pp | error vs obs: open / closed |
|---|---|---|---|---|
| 0.400 | 2.145 | 2.305 | +5.53 | −4.6 % / +2.5 % |
| 0.600 | 2.101 | 2.274 | +5.96 | −6.6 % / +1.1 % |
| **0.885 (fitted)** | 2.059 | 2.247 | **+6.48** | −8.5 % / −0.1 % |
| 1.200 | 2.028 | 2.223 | +6.74 | −9.9 % / −1.1 % |
| 1.600 | 2.000 | 2.201 | +6.93 | −11.1 % / −2.1 % |
| 2.200 | 1.969 | 2.177 | +7.17 | −12.5 % / −3.2 % |

The effect is **+5.5 to +7.2 pp** across a 5.5× range of the knob — more robust than A24's
identification warning would suggest, and worth saying. It is still a range, and the
observed +5.35 pp sits just *below* its bottom.

### Counterfactual redistribution, 2025/26 (Tier 3 — NOT validated)

Where the model sends the tonnage when the bunkers close, Δ kt received, closed − open:

| site | Δ kt |
|---|---|
| Lucky Bay (T-Ports port) | +90.3 |
| Port Lincoln | +70.6 |
| Thevenard | +56.4 |
| Kimba (Bunge) | +24.2 |
| Edillilie | +10.5 |
| Rudall | +8.4 |
| Port Neill | +6.5 |
| Witera | +5.7 |
| Wirrulla | +5.2 |
| Warramboo | +4.9 |
| Streaky Bay | +3.5 |
| Poochera | +2.1 |
| Yeelanna | +1.2 |
| Arno Bay | −5.0 |
| Wudinna | −8.0 |
| Lock (T-Ports bunker) | −126.3 |
| Kimba (T-Ports bunker) | −150.0 |

Two things in here are worth the piece's attention even though neither is validated: a
third of the displaced tonnage (**+90 kt**) stays inside the T-Ports system by going
direct to Lucky Bay rather than transferring to Bunge — the grower keeps the independent
option, at a much longer haul; and two Bunge sites (Arno Bay, Wudinna) *lose* tonnage in
the reshuffle, so "closure pushes grain to the nearest Bunge silo" is too simple even
inside the model.

## §5 — a plan correction that matters more than the gate

`docs/analysis_plan_ep_competition.md` §2 states, as a fact supporting the piece: *"They
ran in 2023/24 (0.511 Mt T-Ports intake)."*

**That figure is this model's output, not an observation.** The 2023/24 bunkers-open run
above returns T-Ports intake of **0.511 Mt**. Its only prior appearance in the repo is
`data/ASSUMPTIONS.md` A24, where it is explicitly a *modelled* quantity (A24's own
decomposition table gives modelled T-Ports at 19.7 pp of 2.588 Mt = 0.510 Mt), used there
to argue that the fitted `luckyBayBias` is *at the top of what the external evidence
supports*. Published T-Ports intake is listed in the plan's own §5 as a data gap still to
be closed, and in A24's upgrade path.

Citing it in §2 as an observed fact would put a Tier-3 model output into the Tier-1 opening
of the piece, sourced to nothing, in support of the very mechanism the model is meant to be
tested on. Not editing the plan (per the ground rules) — flagging it.

## Reproduce

```bash
# everything simulated in this document (Parts 1-3), deterministic, writes nothing:
npx tsx packages/sim/scripts/r5_validate.ts

# regression: 17 passed, and the calibrated seasons byte-identical
npm --workspace packages/sim run test
npx tsx packages/sim/scripts/run_headless.ts 2025/26 42   # hash 5a6455d1, unchanged
npx tsx packages/sim/scripts/report.ts                    # regenerates calibration_report.md identically

# the two observed tables (§2 straddle, §3 EP production), from the parquets:
./.venv/Scripts/python -c "import polars as pl; t=pl.read_parquet('data/processed/receivals_weekly.parquet'); s=t.group_by(['season','region']).agg(pl.col('cum_t').max().alias('c')).pivot(values='c',index='season',on='region').sort('season'); [print(r['season'], r['western'], r['total'], round(100*r['western']/r['total'],1)) for r in s.iter_rows(named=True)]"
./.venv/Scripts/python -c "import polars as pl; p=pl.read_parquet('data/processed/production_districts.parquet'); print(p.filter(pl.col('crop')=='TOTAL').group_by('season').agg(pl.col('production_t').sum()).sort('season'))"

# input coverage (blocker 1):
./.venv/Scripts/python -c "import polars as pl; print(pl.read_parquet('data/processed/climate_daily.parquet')['date'].min())"   # 2020-09-01
```

## Recommendation

1. **Publish Tiers 1–2.** The plan's §3 headline (drive-time geometry, no fitted
   parameter) is untouched by any of this and remains the strongest thing in the piece.
2. **Cut Tier 3 to a labelled sensitivity note**, using the §3 ranges: closing the two
   bunkers moves +5.5 to +7.2 pp of EP production onto the Bunge network in the model,
   against an observed season-to-season shift of +5.35 pp that has n = 2 and is
   confounded by crop size. Say that it is a model coherence check, not a validated
   prediction, and say that the observed 2022/23 point runs the other way.
3. **Do not claim a validation track record.** The paragraph the plan hoped for ("the
   counterfactual machinery has a published track record") cannot be written from this.
4. **Remove or re-source the 0.511 Mt figure** in plan §2 (§5 above).
5. Two data gaps, if the gate is ever to be reopened: pre-2022/23 PIRSA district
   production (blocker 1) and any site-level receival series at all (blocker 2). The
   second is the one that matters — without it no closure, past or future, is testable at
   the resolution Tier 3 claims.
