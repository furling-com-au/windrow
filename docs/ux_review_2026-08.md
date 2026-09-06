# UX / UI and assumption review — Windrow

**Reviewed 2026-08-27 at rev `c08513c`.** Styled version of this document:
`docs/ux_review_2026-08.html`.

Method: seven independent audit lenses (first-run flow, levers/takeaways, sim-vs-actual
honesty, assumptions sanity, engine-vs-claims, a11y/responsive, copy/comprehension), each
adversarially verified against the source — 67 findings survived, 0 refuted — consolidated
here into 35 items. Every finding was reproduced in the running app, by instrumenting the
real bundles headlessly (seed 42), or by redoing the arithmetic. Nothing was changed in the
working tree.

## Verdict

**The model is better than the app says, and the app says things the model doesn't
support.** Two separate problems that compound: the physics calibrates to ~1% on season
totals, and the presentation layer then manufactures errors that aren't there while
asserting conclusions the engine contradicts.

| | |
|---|---|
| Season-total accuracy | **−1.0%** — 2025/26 finishes 2.227 Mt sim vs 2.249 Mt observed; −0.4% to −1.6% across three seasons incl. the held-out one. The app never leads with this. |
| What the default screen says | **1771%** — "Reality check", 3 Nov, nothing touched. The same unchanged model reads +252% one day and +82% the next. |
| Rail scenario freight | **+$197k** — "Bring back the trains" promises ~2.5M truck-km saved; the only trucking figure shown says freight got *worse*. |
| Clicks to a hard crash | **2** — bumper + Lucky Bay, default season, throws `QUEUE INSANE at Thevenard: 408`. |
| Touch targets at 44px | **0 / 24** — at 393px, with 56% of the panel hidden and type down to 7px. |
| Fitted params pinned at a bound | **5 / 12** — rateScale, matShift, retentionShare, portAttractBias, luckyBayBias. |

---

## Theme 1 — The app is its own worst reviewer

### F1 (critical) "Reality check" compares a continuous curve against a week-stale step

`app/src/components/LeversPanel.svelte:181-192` (`simVsActual`), rendered `:456-461` ·
`app/src/App.svelte:238-249` (KPI "actual")

Both loops keep the last weekly report whose `week_ending <= sim.day`, then divide by it.
The simulated cumulative advances every tick; the observed cumulative only exists on
Sundays. During peak harvest that denominator can be six days and ~490,000 t old.

```
Default view, 2025/26, "The season as it happened", untouched:
   3 Nov 2025   "0.16 million t ... vs 0.01 reported  —  1771% ahead of reality"
   6 Dec 2025   "1.44 million t ... vs 0.78 reported  —    86% ahead of reality"
  ~day 140      "2.23 million t ... vs 2.25 reported  —     1% behind reality"

Arithmetic at 6 Dec:
  observed cum, week ending 30 Nov     776,461 t   <- what the app divides by
  observed cum, week ending  7 Dec   1,222,446 t
  implied rate                           63,712 t/day
  interpolated to 6 Dec              1,158,734 t
  sim 1.44 Mt vs 776,461     ->  +85%  (displayed)
  sim 1.44 Mt vs 1,158,734   ->  +24%  (like-for-like)
```

At day 62 the split measures ~29 points real, ~21 points artefact. Because the denominator
jumps weekly, the same model reads **+252% one day and +82% the next**.

**Fix.** Compare only at week-ending dates, labelled "as at week ending 30 Nov". Suppress
the percentage while the denominator is small. Lead with what is actually good: season
totals inside 1.6% on three seasons.

### F2 (major) The real weakness — intra-season timing — is never disclosed

`docs/calibration_report.md` vs `app/src/components/AboutModal.svelte` · `Tour.svelte:21`

```
weekly Western receivals, 2025/26 (sim vs observed, kt)
  19 Oct   sim  31   obs   1        <- harvest starts ~2-3 weeks early
   9 Nov   sim 171   obs  24
  30 Nov   sim 299   obs 331
  14 Dec   sim 291   obs 487        <- and finishes early
   4 Jan   sim  36   obs  76
  season   sim 2.228 Mt  obs 2.249 Mt   = -0.9%

calibration_report.md, held-out 2024/25 vs acceptance criteria:
  season total error     -0.4%     +/-5%        PASS
  weekly RMSE / mean       63%     <=15% band   "see note"
  vessel call count      -15.1%    +/-10%       FAIL
```

The report prints its own FAIL — to its credit. The app surfaces neither that nor the
50–63% weekly RMSE, and tour step 4 calls the chart gap "the honest measure of the model"
without saying which axis is weak.

### F3 (major) Everything labelled "vs the real season" is measured against a second simulation run

`LeversPanel.svelte` (`ROW_TIPS`, `sentences`, "Delivery pace") vs
`app/src/worker/sim.worker.ts:83-113` (`computeBaseline`, `defaultParams()`)

The baseline lifecycle is sound — always `defaultParams()` for the loaded season, nulled on
season change, season-checked on receipt, cached with correct invalidation. The problem is
purely the words: *"~7 days behind the real season"*, *"30% longer than the real season"*,
*"vs the real season at the same date"*. Say "the modelled normal season".

---

## Theme 2 — The flagship scenarios report the opposite of their own stories

### F4 (critical) "Bring back the trains" reports freight going up

`packages/sim/src/engine.ts:842` (trains share `tonneKm`) · priced at
`LeversPanel.svelte:208-209`, rendered `:127-133`

```
engine.ts:842   this.tonneKm += (minutes / 60) * 75 * load;
                 // in stepLinehaul — taken by trainsets too; isTrain (:800)
                 // only redirects routing and handling, never the counter

rail patch (railReinstated + linehaulTrucks 32), 2025/26:
  tonneKm    302,307,208 -> 304,279,214    +1.97M (+0.65%)
  renders    "+2.0M t.km  ·  +$197k freight"   in the amber "worse" colour
  truckKm     17,636,975 ->  14,896,096    -2.74M truck-km saved
  kpi.truckKm exists (engine.ts:1038) — grep app/src: zero uses

Simple mode, day 364, rail scenario:
  "Barely any difference from the real season."  +  "No meaningful differences yet"
```

The story card promises "about 2.5 million truck-km", the lever tooltip repeats it, A21
documents it. The 2.74M saving the model produces matches that promise and is never shown.
Two related defects compound it: trainsets run on the **road** travel-time matrix at road
speeds, reaching **4.0 cycles/trainset/day (12,800 t/day)** against the "~2 cycles/day
ceiling" asserted in A21, `docs/scenarios.md` and the engine's own comment; and A21's "road
line-haul fleet cut by one-third" is applied only by `scripts/scenarios.ts`, not by the
app's rail lever.

**Fix.** Split the counter (a `railTonneKm` incremented inside the `isTrain` branch), price
only road tonne-km at A18, and add a truck-km row driven by `kpi.truckKm` plus a new
baseline series. Then either give trains a rail transit time or enforce the stated cycle
cap, and correct the "~2 cycles/day" claim in all three places.

### F5 (major) Simple mode's four-line cap cuts exactly the effect each story tells you to watch

`LeversPanel.svelte:313` (`lines.slice(0, 4)`), push order `:245-291`

```
Bumper +30%, day 365 — the four bullets that fit:
  1 crop value   +$873m      2 grain delivered  +557k t (+25%)
  3 Lucky Bay    +210k t     4 freight          +$5.41m
  5 queues       139 -> 450 trucks (+224%)      CUT

  ...printed directly above it, the verdict:
  "A bigger crop gets through — but watch the queues and where the surplus goes."

Drought -40%: same four slots fill; the ships-waiting line is 5th and cut,
  under a story ending "ships sit at anchor waiting for grain that never comes".
```

Simple mode is the default. The two most-clicked scenarios are the two whose punchline is
silently dropped. **Fix:** rank lines by |effect| relative to each row's threshold, or pin
the row the verdict names.

### F6 (major) The drought scenario's $158.5m of ship waiting is an artefact of a program that never cancels

`LeversPanel.svelte:212-214` · root cause `engine.ts:889-908` (V_ANCHOR has no give-up)

```
Drought (-40%), 2025/26:
  mean vessel wait   day 90:  20 h    day 250: 358 h    day 364: 1,093.5 h
  baseline                                             day 364:      28.3 h
  119 arrivals  ->  (1093.5 - 28.3) x 119 / 24 x $30,000 = +$158.5m
  whole-season simulated cartage bill  ~$30m
```

The largest dollar figure the app can produce is 5× the freight task, and it means "46
demurrage days per ship, and nobody re-issued the program". `docs/scenarios.md` carries the
real explanation; nothing at the point of display does.

### F7 (major) "Crop value (farm gate)" is a whole-season total at the top of a strictly to-date table

`LeversPanel.svelte:215-220`, `unshift`-ed to the top at `:164-170`; header at `:487`

```
farmgate = (productionScale - 1) x prod x FARMGATE_PER_T   // no reference to s.day

Bumper +30%, before pressing play, on 1 October:
  table header   "running comparison, to 2025-10-01"
  row 1          "Crop value (farm gate)  +$331m"     <- full-season figure
  every other row  "= no change"
```

Identical for all 365 days, so nothing tells the reader it is not accruing.

### F8 (polish) The comparison table paints good outcomes amber and bad outcomes green

`LeversPanel.svelte:590-595` (`.row.up` amber / `.row.down` green); `dir` is pure sign, set
at `:121` and `:169`

```
Drought:  "Crop value -$442m"  and  "Grain delivered -824k t"   -> green
Bumper:   "Crop value +$331m"  and  "Grain delivered +557k t"   -> amber
```

5 of 9 rows have up = worse; the tonnage and farm-gate rows invert it.

---

## Theme 3 — Numbers in the takeaways panel that are simply wrong

### F9 (critical) "Delivery pace" prints hundreds of days of nonsense

`LeversPanel.svelte:221-226`, rendered `:141-148` and `:270-276`

```
while (j < b.receivedByDay.length && (b.receivedByDay[j] ?? 0) < s.kpi.receivedT) j++;
paceLagDays = s.day - j;      // no bound, no fallback

(a) run exceeds the baseline's season total -> j runs to 365:
    rail   day 140 -> -225   day 200 -> -165   day 300 -> -65
(b) baseline stops receiving at day 96, so j freezes for ~270 days:
    fleet 500  day 364 -> +273      drought  day 364 -> +299

Rendered: "~299 days behind the real season" / "~275 days ahead".

Worst case: at day 200 the rail scenario clears no other threshold, so its ONE
bullet under "Barely any difference from the real season." is
  "Deliveries run about 165 days ahead of the real season."
```

**Fix.** Return null when the search hits the end of the array or the baseline has
plateaued; render as "not comparable".

### F10 (major) An undocumented flat 75 km/h converts minutes into every kilometre and dollar reported

`engine.ts:747, :842, :1038` · vs `data/ASSUMPTIONS.md` A5

```
engine.ts:747   const km = (tr.legMin / 60) * 75;   // "mean 75 km/h (A5-derived)"
engine.ts:842   this.tonneKm += (minutes / 60) * 75 * load;
engine.ts:1038  truckKm: Math.round((this.truckTravelMin / 60) * 75)

The matrix carries ONLY minutes, built at A5's class speeds:
  trunk/primary 90 · secondary 80 · tertiary 70 · unclassified 60 · residential 40
75 contradicts every one of them; grep '75 km' over data/ docs/ README: nothing.

Worked: Wudinna -> Port Lincoln is 143.3 matrix minutes, reported as 179 km
  where the 90 km/h network implies ~215 km.
Trunk line-haul understated ~17%, low-class farm legs overstated up to 25%
  (of 17.6M truck-km: 13.3M farm->site, 4.4M line-haul — net sign indeterminate).
What IS understated ~17% is the rail saving, all trunk line-haul — including the
  "2.5 million truck-km" a reader sees in the scenario story.
```

**Fix.** Export leg distances from the OSM routing step and accumulate real km. If
deferred, register the constant and state which displayed figures lean which way.

### F11 (major) The travel-time slider fabricates $7.9m of freight although no truck drives an extra kilometre

`engine.ts:747-748, :842` (time-derived km) · slider at `LeversPanel.svelte:406-409`

```
"tonne-km" is really tonne-HOURS x 75, and legMin is already scaled by travelTimeScale.

travel times x1.30  ->  "+79.2M t.km  ·  +$7.9m freight"   deliveries move -1,992 t
travel times x0.80  ->  "-51.8M t.km  ·  -$5.2m freight"   deliveries move   +209 t

Simple mode: "Trucks travel further overall — grain gets double-handled (farm to
silo now, silo to port later) — roughly $7.9m extra in freight."
Both halves false: same roads, and deliveries changed by 2,000 t out of 2.23M.
```

This is the panel whose own instruction is *"if a conclusion flips when you nudge one,
treat it with care"*. **Fix:** divide `travelTimeScale` back out at the two km conversions
and at `truckKm`.

### F12 (major) Mid-season deltas compare a mid-day live snapshot against a midnight baseline entry

`LeversPanel.svelte:203` (`i = s.day - 1`) feeding every delta `:204-232`

```
The index is CORRECT at midnight — but the worker emits ~30 snapshots per sim-day
while i stays fixed, so each delta ramps up over the day and snaps back.

Tod Hwy closed, day 63 (a peak day: 65,450 t and 6.31M t.km):
  tick +0    dRec  -1,428 t   freight +$1.01m      <- true same-instant answer
  tick +144  dRec +30,872 t   freight +$1.44m
  tick +287  dRec +64,352 t   freight +$1.70m      <- 68% overstated
```

Pause or screenshot mid-day and Simple mode asserts "64,000 tonnes more grain reaches the
silos and ports (+5%)" when the correct answer is a small decrease. Self-correcting at
every midnight, on any scrub, and at season end.

### F13 (major) Assumption levers never mark the run as a what-if

`LeversPanel.svelte:7-10` (`setA` omits `scenario = "custom"`), `:28-32` (`reset` ignores
`assump`), `:352`, `:470` · `App.svelte:148, :158` (CSV)

```
Nudge "Crop kept on farm" 10% -> 5%:
  dRec +100,384 t (+4.5%) and +$1.68m freight against a default-assumption baseline

  Scenario dropdown still reads   "The season as it happened"
  Story still reads               "Real crop sizes ... and the network as it ran"
  "back to normal" button         hidden (scenario is still "baseline")
  Switch to Simple and the        "Your change:" line is suppressed
  Export CSV                      windrow_2025-26_baseline.csv, header "scenario baseline"
```

**Fix.** Add `app.scenario = "custom"` to `setA`, extend `reset()` to the assumption and
econ levers, gate the reset button on `assumpDirty` too.

---

## Theme 4 — The living map isn't living by the time anyone looks at it

### F14 (critical) The season plays out underneath the intro overlay

`App.svelte:190-192` (worker `"ready"` → `app.playing = true`) · `Intro.svelte`

```
t = 10s   sim already at  9 Oct 2025  — intro still covering the map
t = 57s   dismissed intro at 25 Nov 2025 — 8 weeks in, past the "first delivery"
          marker the chart annotates
full season ~190s wall-clock (130 d at 1 d/s, then 4 d/s)

Also observed: intro never dismissed, sim reached 1 Oct 2026 — season over,
0 trucks on the road — with the overlay still up.
```

57 seconds is a brisk read of a ~120-word card, and the alternative button offers a
"1-minute tour" of six dense steps whose step 3 says "The season is already playing at one
day per second". This is the direct cost of the fix logged in `stakeholder_review.md` ("the
dashboard was dead on arrival … the season now auto-plays"): auto-play was added without
pausing for the modals on top of it.

**Fix.** Don't start the clock until the intro and tour are dismissed, or seek back to day
0 on dismissal.

### F15 (critical) After any scrub, the narrator asserts "peak harvest" for the rest of the year

`App.svelte:43-49, 66-71, 78` (`resetHistories` + backfill) ·
`app/src/lib/narrator.ts:27, 36, 50-52`

```
On a jump, resetHistories() empties dailyReceived and the backfill loop starts at
snap.day exactly — so every lower index is a HOLE. Then:

narrator.ts:27  recent = snap.kpi.receivedT - (dailyReceived[day - 7] ?? 0)
                -> the hole makes `recent` the FULL CUMULATIVE (~2.2 Mt), not ~0
maxWeekObs = 486,931 (2025/26)  ->  threshold  recent > 267,812  is ALWAYS true
harvestOver = day > 110 && recent < 8000       can NEVER fire
```

A farmer follows the tour's instruction to "drag the date slider to jump anywhere", lands
on a frozen April frame with no headers and no trucks, and the largest text on screen reads
*"Mid April: peak harvest. Grain is pouring in."*

**Fix.** Backfill instead of clearing — have the worker's `seek` step day-by-day (the
pattern `computeBaseline` already uses) and post the series with the snapshot.

### F16 (critical) Dragging the date slider queues one full-season re-simulation per input event

`App.svelte:298-304` (`oninput`, no debounce), `:105-108` · `sim.worker.ts:161-175`
(uncapped; contrast the cap at `:66`)

```
Each seek rebuilds from scratch: new Sim(...) then sim.step(day * DAY_TICKS), synchronous.
  day 30   192 ms      day 90   473 ms      day 180  726 ms      day 364  1,347 ms

The slider spans 365 values in ~220 px, so a one-second drag emits 30-60 input events
-> 20-60 s of grinding after the user's hand stops. The thumb also fights the cursor,
because value={app.snap?.day} is re-applied from every arriving snapshot.
app.loading is only set in initSim(), so no indicator appears at all.
```

Tour step 3 tells every first-time visitor to do exactly this. **Fix:** commit on release
(`onchange`) with a local `scrubDay` driving the thumb; stamp seeks with an id in the worker
and skip superseded targets; show the existing loading line.

### F17 (major) The worker blocks ~1.4s computing the baseline immediately after telling the UI to start playing

`sim.worker.ts:83-113` (synchronous 365-day loop), scheduled `:135`, frame interval only
created `:146` · `App.svelte:190-192`

```
computeBaseline: 365 days + snapshot = 1,371 ms on desktop -> 4-7 s on a mid-range phone

Meanwhile App.svelte:190-192 has already set playing = true, so the button reads
"Pause" throughout the stall, and queued play/speed/seek messages cannot be serviced.
app.loading was cleared before the stall. Recurs on every season change.
```

The code comment above the autoplay reads "the map should live immediately — a frozen
dashboard reads as broken". The stall produces exactly that.

### F18 (major) Three time-control defects that leave the user stuck

```
CHART   After any scrub the simulated line disappears — verified, the sim path
        collapsed to a 10-character `d` attribute while the gold observed line and
        the y-axis still spanned the season. Past day 140 it stays gone for the run.

DONE    seek() never clears app.done, and {#if app.done} replaces play/pause with
        "Replay season". So once finished, dragging back to day 200 leaves no play
        control at all — the only button jumps to day 0.

SPEED   At day >= 130 the app sets 345,600 (4 d/s), not one of the four SPEEDS values,
        so no button is highlighted (verified: activeSpeeds []). It then persists into
        Replay and every later scenario — while the tour says "one day per second".
```

---

## Theme 5 — The season labelled "live" is empty, and the copy calls it real

### F19 (critical) 2026/27 has no weather, no ships and no production data

`app/public/data/{observed,weather,vessels,demand}_2026-27.json` · `state.svelte.ts:44,
:106, :111` · `LeversPanel.svelte:463` · `engine.ts:210-230`

```
observed_2026-27.json   weekly_receivals: []      district_production_t: {}
weather_2026-27.json    "source": "pre-season placeholder"
                        rain_mm: []   tmax_c: []   for WEP / LEP / EEP
vessels_2026-27.json    all three visit arrays empty
demand_2026-27.json     "A20 PROVISIONAL: mean of PIRSA 2022/23-2025/26"

Run to day 365:  received 1,999,165 t   shipped 0   vesselsArrived 0
engine.ts:212-230 iterates an empty rain_mm, so weatherFactor stays 1 —
  the rain gating the Intro sells as "driven by real weather" is off.

What the copy says for this season:
  dropdown   "2026/27 — live (forecast)"     (the newest, most tempting entry)
  story      "Real crop sizes, the real shipping program, and the network as it ran"
  panel      "You're watching the season as it really ran."
  ports      "berth idle" for twelve months
```

**Fix.** Give the live season its own story and reality-check copy ("a placeholder crop, no
weather yet, no shipping program — this fills in as the season lands"), and either hide the
port panel's berth state or label it "no schedule yet".

---

## Theme 6 — The register has drifted from the model it documents

### F20 (critical) A4's receivals-proportional allocation was never built, and the flat guess that replaced it drives three headline outputs

`data/ASSUMPTIONS.md:72-74, :78` · `engine.ts:275-277`, gates at `:598, :615` ·
`SiteDetail.svelte:11, :38` · `app/public/data/sites.geojson`

```
A4 documents: "per-site capacity allocated proportional to long-run district
              receivals, scaled so Western upcountry total = 2.5 Mt"

engine.ts:275  capacityT = s.capacity_t ?? (isTports ? 145000 : 120000) * capScale
sites.geojson  every Bunge upcountry feature has capacity_t: null
               16 active Bunge upcountry sites x 120,000 = 1.92 Mt, not 2.5 Mt,
               with no proportionality to anything

2025/26 calibrated baseline, per-site peak fill:
  8 of 16 pegged — Warramboo, Tumby Bay, Kimba, Cummins, Lock, Arno Bay,
  Wudinna 101% · Rudall 102%     ...while Kapinnie peaks at 5%, Yeelanna 9%

A4:78 says storage "matters only when sites fill (bumper scenarios)". Falsified —
raising upcountryCapScale to 1.5x on the CALIBRATED BASELINE moves:
  direct-to-port share   33.1% -> 24.1%
  peak site queue          139 -> 78
  T-Ports intake        326 kt -> 229 kt
```

A grower clicks Kapinnie (a faba-bean siding) and Wudinna (a major Tod Highway silo) and
both read "… t of 120,000 t (capacity assumed)". The register then tells them capacities
were allocated proportionally and only matter in bumper years. Both false, and the invented
number is what sets the peak-queue headline.

**Fix.** Either write real per-site `capacity_t` (the district receivals series is already
parsed), or rewrite A4 to state what the code does, delete the 3.27 − 0.73 derivation that
mixes season receivals with peak inventory, and replace the sensitivity line with the
measured figures above.

### F21 (critical) A17: carry-in is not a measurement — it is two months of vessel scheduling and spreadsheet coverage

`data/ASSUMPTIONS.md:174-182` · `pipeline/p2_build_observed.py:91-107` (no coverage guard) ·
`engine.ts:321-327`

```
carry_in.port_lincoln_t as built:
  2022/23  0 t          <- observed_2022-23.json has NO Oct 2022 and NO Nov 2022 row
                           (the Thevenard sheet in the same file DOES carry 2022-11)
  2023/24  320,504 t    <- vs Port Lincoln's published 395,600 t capacity
  2024/25   60,334 t
  2025/26   67,585 t    <- again no Oct 2025 row

2023/24: Port Lincoln's seasonal peak fill is 81%, on day one, before a tonne is
harvested — the opposite of real practice, where ports are run down pre-harvest.

A17:181 claims "receivals calibration unaffected (carry-in is never received)".
Falsified — 2023/24 with carryInScale 1 vs 0:
  Bunge receivals   1.832 Mt -> 1.922 Mt  (+4.9%)
  direct-to-port      29.9% -> 24.2%       peak queue  91 -> 69
The seed propagates into receivals through the capacity gates at :615 and :854.
```

**Fix.** Add a coverage check in the builder — if a port has no Oct or Nov row, don't emit
0; fall back to a named prior and record the gap in the provenance string. Call Oct+Nov
shipments a lower bound on the port-held share of carry-over, not a measurement.

### F22 (major) Five of twelve fitted parameters sit exactly on their lower search bound

`packages/sim/src/calibrated.json:3-15` · `scripts/calibrate.ts:85-98, :132` ·
`docs/calibration_report.md:6-8, :18-32`

```
search range              fitted value      other knobs carry 15 significant figures
  rateScale       [0.7, 2.2]    -> 0.7
  matShift        [-4,   16]    -> -4
  retentionShare  [0.1, 0.28]   -> 0.1
  portAttractBias [0.8,  2.8]   -> 0.8
  luckyBayBias    [0.4,  2.2]   -> 0.4

rng.range(lo,hi) hits a bound with probability zero, so the only path to these is the
refinement clamp at calibrate.ts:132 — the optimiser pushed past the floor and was
clipped. Those five carry no information about the data, only about the range chosen.

The report also says "11 free scalars" against a 12-row table (portBays missing from
the prose list), and marks no knob as pinned.

Downstream: realised direct-to-port share is 33.1% (2025/26) and 29.9% (2023/24)
against A9's stated 25% and ESCOSA's ~75/25 anchor — and the binding constraint is
the A4 storage cap, not the bias floor. retentionShare is pinned at 0.10 against
CALIBRATION.md's observed 20-23% residual. A23's whole $/t translation is anchored
to luckyBayBias's pinned 0.40.
```

### F23 (major) A2's bay arithmetic can't be reproduced from the code, and the per-site intake rate is dead code

`data/ASSUMPTIONS.md:38-44` · `engine.ts:287, :293, :655, :687-694`

```
A2 derives its bay counts from a "14 h" receival day.
engine.ts:655   sitesOpenNow = hourOfDay >= 7 && hourOfDay < 19    -> a 12 h window
engine.ts:687   the bay-service loop is guarded only by `if (!s.open)`
                -> bays keep tipping around the clock

Under the code's own 12 h window, A2's own step (340 visits / 12 h / 5 per bay-hour
= 5.7) gives 6 upcountry bays, not the 4 it settles on.

engine.ts:293 assigns intakeTph (4000 Lincoln / 1400 Thevenard / 1000 port / 600
upcountry). grep over all .ts and .svelte: never read. Dead code.

(Throughput itself checks out: measured Port Lincoln peak 13,845 t/day at 4/6 bays
 and 9,300 at 2/4, reproducing A2's conclusion if not its stated arithmetic.)
```

### F24 (major) A7's published rule omits most of the rules the engine runs, and the heat rule has the wrong mechanism

`data/ASSUMPTIONS.md` A7 · `engine.ts:219-229` · `app/public/data/weather_*.json`

```
bundle carries, per district:  rain_mm  tmax_c  rh_min_pct  wind_max_kmh
                              (181 days x 8 districts, every season)
engine reads:                 rain_mm  tmax_c    — the other two are dead payload

A7's stated rule is rain >= 5mm (or >= 10 over 2 days) and a 25% cut at tmax >= 38 C.
The engine also runs a half-rate band at rain >= 0.4*rs, a x0.3 hangover at
rain[-1] >= 1.6*rs and x0.5 at rain[-2], plus a spring-dryness maturity shift —
none of which appear in A7.
```

SA harvest bans track grassland fire danger — wind, humidity, temperature and fuel curing
together, not temperature alone. Hot days are often *good* harvest days; it is the
accompanying wind and low humidity that stop headers. Both missing inputs are already in
the bundle, and the same wind series would serve open backlog item #10 (Lucky Bay
transshipment downtime against T-Ports' published wind > 21 kn limit).

### F25 (major) docs/scenarios.md no longer reproduces from the code, and contradicts itself about carry-in

`docs/scenarios.md:11-17` (table), `:30-32` (prose), `:18` vs `:88` · `README.md:135-137` ·
ground truth in `docs/scenarios_data.json`

```
                     scenarios.md      scenarios_data.json / my runs
baseline received       2.18 Mt      ->  2.228 Mt
peak site queue            189      ->  139
truck-km                16.6 M      ->  17,636,975
peak week               366 kt      ->  433 kt
bumper peak queue          285      ->  450   (a 3x gap on the flagship metric)

Same file, twenty lines apart:
  :18  "(Numbers include A17 carry-in stocks; regenerated 2026-08-19.)"
  :88  "No carry-in stocks at season start (README limitations)"
README.md:135-137 still lists "No carry-in stocks: each season starts empty" as a
limitation — while carry-in is implemented, displayed, and exposed as a lever.
```

**Fix.** Regenerate the table from `scenarios_data.json` (the script already writes it) or
add a CI check that they match. Delete the stale carry-in bullets in both files.

---

## Theme 7 — Where the engine falls over, or produces numbers it shouldn't

### F26 (critical) Two clicks crash the engine on the default season

`engine.ts:576` → `sim.worker.ts` → `App.svelte` (`{app.error}`)

```
Six of twelve UI-reachable combinations throw. Shortest path is two interactions
on the DEFAULT season:

2025/26  bumper +30%  +  more grain to Lucky Bay   -> QUEUE INSANE at Thevenard: 408
2026/27  bumper +30%  +  unload cycle 20 min       -> QUEUE INSANE at Lucky Bay: 416
2025/26  max crop     +  30 min unload             -> QUEUE INSANE at Port Lincoln: 468
2025/26  max crop     +  silo capacity x0.1        -> QUEUE INSANE at Lucky Bay: 553
2025/26  max crop     +  max direct-to-port        -> QUEUE INSANE at Lucky Bay: 416
2025/26  rail         +  max crop                  -> QUEUE INSANE at Lucky Bay: 402
The crop slider alone at 135-140% also trips it.

The visitor sees the map stop and a line of red text: "Error: QUEUE INSANE at
Thevenard: 408". No reset, no explanation, no indication which lever did it. And
because the invariant is sampled daily while the peak is tracked every tick, whether
a given combination dies depends on when the spike lands — so it looks random.
```

The project already knows this wall: `docs/calibration_report.md` excludes a whole real
season for it — *"Outside the model's validity envelope (not run): 2022/23 — QUEUE INSANE at
Lucky Bay: 431"* — and the season dropdown quietly omits 2022/23. The test suite's 3 tests
only exercise default parameters.

**Fix.** Make the guard a soft cap: refuse further joins at a site and let grain back up on
farm, which is what actually happens — and which the engine already tracks and prices. Then
catch the worker error, revert the offending lever, and say something true: "at this crop
size the model can't keep queues physical, so it stops rather than show you a number it
doesn't believe." Add a test that sweeps the presets and lever extremes.

### F27 (major) "Worst silo queue" reaches 22 hours, past the model's own balking tolerance, and is reported as fact

`engine.ts:616-622` (balk filter and its fallback pass), `:696`

```
2025/26 baseline                peak queue at one site   139 trucks
2025/26 bumper +30% (a preset)  peak queue at one site   450 trucks
2026/27 bumper +30%                                      485 trucks

450 trucks / (4 bays x 5 trucks/h) = 22.5 hours of queue
model's own tolerance (A2, queueBalkMin) = 4 hours
  — "the worst turnaround ever reported on EP is ~4 h"

The balk filter drops sites over 240 min, but if NO site clears the threshold a
second pass admits them all — so balking delays the pile-up instead of bounding it.
```

A2's own correction note describes this exact failure once before. It is compounded by F20:
the flat capacity cap is what pushes the queue there.

### F28 (major) The "impassable spine" leaves every silo→Port Lincoln haul at its normal drive time

`engine.ts:342-370` (closure applied to `clusterCand` only) vs `:825` (line-haul reads an
untouched `matrix.site_minutes`) · `state.svelte.ts:50`

```
roadClosure is read in exactly three places, all inside the cluster-candidate build:
  if (near(c.lon, c.lat, s.lon, s.lat)) cand.minutes *= params.roadClosure.factor;
Line-haul at :825 has no closure term at all.

2025/26 baseline: silo->port line-haul moves 716 kt, of which 209 kt (Warramboo,
Wudinna, Lock -> Port Lincoln) the engine's OWN near() test would flag — yet all
716 kt run at normal minutes with the corridor "closed".

So "Tod Highway closed" returns +1.4M truck-km, all of it farm-to-silo. The traffic
the Tod actually carries into Port Lincoln is modelled as unaffected.
(Kimba->Port Lincoln isn't even caught by near(): its straight-line midpoint falls
outside the 0.18 deg proxy — so the fix has to be sharper than reusing that test.)
```

The in-app story says "detours = 2.5x travel time" with no caveat; only
`docs/scenarios.md` admits the straight-line heuristic.

### F29 (major) Ports and silos store more grain than their capacity

`engine.ts:598, :615, :854` (capacity gates)

```
bumper +30%, peak stock vs capacity:
  Port Lincoln   411,260 t  /  395,600 t  (published)   104%
  Thevenard      351,693 t  /  335,925 t  (published)   105%
  Lucky Bay      389,403 t  /  384,000 t  (published)   101%
  8 upcountry sites in the CALIBRATED baseline           101-102%
```

The gates stop trucks *choosing* a site at >= 99.5% full and reject a line-haul load that
would overshoot, but direct-to-port farm tips and seeded carry-in still push past. Small
physically; it matters because these are published figures, and because the bumper story is
"watch silos fill toward their limits".

---

## Theme 8 — Accessibility and mobile

Backlog #14 records this as "partial", so it is known. Worth restating why it outranks its
current priority: the primary audience is Eyre Peninsula growers and local community —
phone-first, on rural bandwidth — and the first load is ~3.2 MB of uncompressed JSON for
one season (`paths.json` alone is 1.7 MB).

### F30 (major) On a phone the panel covers the map, the narrator covers the panel, and 56% of the content is hidden

`App.svelte:703-713` (the only <=800px rule) · `:552-560` (narrator <=1100px) · legend
button and site-detail card unmoved

```
Measured at 393 x 851:
  panel               473 px tall, holding 1092 px of content  -> 56% hidden
                      behind an unindicated inner scroll, over a pan/zoom canvas
  narrator overlay    overlaps the panel 334 x 75 px — covers the app title, the
                      tagline, the Simple/Advanced toggle and the "?" tour button
  map-key button      overlaps the panel 81 x 29 px
  usable map          collapses to roughly a 100 px strip between the two panels
  panel width         calc(100vw - 24px) with left:12px -> 18 px wider than the
                      viewport, pushing its right padding and scrollbar off-screen

  tap targets         0 of 24 controls reach 44 px tall
                      modes 20 px · sliders 16 px · About link 14 px · help "?" 24 px
  type sizes in use   7 px (x4) · 7.5 px (x5) · 8.5 px · 9 px (x5) · 9.5 px
  contrast            .fine and .phases ~3.92:1 (AA needs 4.5:1), over a translucent
                      panel whose effective ground varies with the map
```

**Fix.** Restructure rather than shrink: a bottom sheet with a drag handle at two heights
(peek = date + KPIs, expanded = everything), so the map keeps the top two-thirds; suppress
the narrator when expanded; move the map key inside. Then a floor of 12 px on type, 44 px
on controls, 4.5:1 on the smallest text.

### F31 (major) The app contains no ARIA at all, and its core interactions are mouse-only

The only `role`/`tabindex` in the codebase is `AboutModal.svelte:9-12`.

```
SLIDERS   all five expose no accessible name:
          textbox "58"  <- the date scrubber, announcing a bare day index
          textbox "1"   textbox "730"   textbox "0.4"   textbox "0.8"

MODALS    0 elements with role="dialog" / aria-modal at load
          Intro:  Escape does not close it; focus never moves in; the first Tab
                  lands on the deck.gl canvas, then walks 12 controls BEHIND the
                  overlay before reaching "Watch the season"
          About:  its Escape handler sits on a tabindex="-1" backdrop that never
                  receives focus, so Escape doesn't close that either; the backdrop
                  is exposed as a button whose accessible name is the entire About text

MAP       the deck.gl canvas is the FIRST tab stop (mjolnir.js sets tabIndex 0), with
          no name, and it swallows arrow keys. All 26 site names, stocks and queue
          counts exist only as WebGL glyphs. Sites are pickable with onClick and no
          keyboard equivalent, so SiteDetail is unreachable without a pointer —
          while the legend says "click it for detail".

NARRATOR  a bare div, no aria-live, so the running commentary is never re-announced.

TITLE=""  12 attributes carry load-bearing explanation (KPI definitions, provenance,
          scenario mechanics) — invisible on touch, unreachable by keyboard.
```

`svelte-check` reports 0 errors and 0 warnings partly because `role="button"` and
`onkeydown={() => {}}` were added to the About backdrop to satisfy the lint rather than to
make it work.

**Fix.** Highest value per line changed: `aria-label` and `aria-valuetext` on the five
sliders (the scrubber should announce the date); `role="dialog" aria-modal="true"`,
autofocus, focus trap and working Escape on the three modals; a keyboard route to site
selection — a site listbox would help pointer users find a specific silo on a dense map
too; and move the 12 `title` explanations into visible text or a tap-friendly popover.

### F32 (polish) Four smaller access defects

```
COLOUR ONLY   truck load colours (wheat #ebc85a, barley #d6a864, canola #fadc28) are
              not colour-blind safe and carry no second channel — the legend depends
              entirely on hue discrimination across five similar yellows.
INTRO CARD    no max-height or overflow, so its headline clips off the top of short
              viewports.
MOTION        no prefers-reduced-motion handling, on an app whose default state is a
              continuously animating map.
REDRAW        every snapshot rebuilds a 5,324-object parcel array (and the land
              polygons), forcing deck.gl to re-upload geometry that never moves.
```

---

## Theme 9 — Claims and provenance at the point of display

### F33 (major) Tour step 1 claims everything modelled is checked against reality

`Tour.svelte:7` vs `Tour.svelte:27` and `AboutModal.svelte:22-26`

```
Tour step 1: "It's built only from public data, and everything modelled is checked
             against what really happened."
About:       "Truck movements, queues, site stocks and vessel loading progress are
             modelled ... everything else is simulated. Site storage capacities ...
             and truck cycle parameters are assumptions."
Tour step 6: repeats the honest version.
```

What is actually validated: weekly Western receival totals, the AIS median anchorage stay,
and the Port Lincoln daily record. **No per-site tonnage, queue count or tonne-km figure
has been compared with any published number.**

### F34 (major) Real vessel names are shown loading specific tonnages, with the caveat buried in About

`app/src/lib/narrator.ts:33` · `PortPanel.svelte:62` (tooltip "planned cargo") · caveat at
`AboutModal.svelte:82`

```
The largest text on the map, on a real date:
  "The Star Jeannette is loading 5,000 t at Port Lincoln."

The name is a date-window join from ~monthly archived stem PDFs. The tonnage is a
monthly port total divided across that month's calls. The loading progress is
simulated. The PortPanel tooltip calls that allocation "planned cargo" — asserting
knowledge of a commercial shipping plan the project does not have.
```

This is the single most checkable statement in the app for a Flinders Ports or Bunge
reader, and the project's own docs flag a wrong name against a real ship as "the most
likely complaint".

**Fix.** Hedge at the point of display — "A ship (likely *Star Jeannette*) is loading —
about 5,000 t modelled" — and change the tooltip to "modelled cargo, allocated from the
monthly port total".

### F35 (polish) Precision, units and raw enums

```
FALSE PRECISION   fmtMoney renders one decimal at $m scale: "$441.9m", "$159.4m" —
                  two lines from the app calling these "rough, order-of-magnitude
                  estimates". Round to 2 s.f. above $1m and keep a leading "~".

FIVE FORMATS      on one screen: "2.23 million t" · "+35k t" · "824,000 tonnes" ·
                  "stock 47 kt / 120 kt" · "delivered here this season (sim):
                  236,412 t" (tonne-exact, 16 lines below a figure rounded to the
                  nearest 100 t). Pick one convention.

PROVENANCE GAP    SiteDetail flags "(capacity assumed)"; the map hover shows the same
                  invented "120 kt" with no flag at all.

RAW ENUMS         SiteDetail renders "Bunge (ex-Viterra) · upcountry · active 2025 26"
                  and commodity chips "WH BA" — two lines above the same component's
                  own legend spelling out "wheat 12k t". The fallback "no 25/26
                  segregations" is hardcoded, so it fires on 2023/24 too.

KPI CAPTION       "0.01 million t shipped out / incl. 0.11 carry-over" — prints total
                  opening stock as though it were inside the shipped figure.

JARGON            "Windrow" — the app's own name — is never explained anywhere in the
                  app, and nothing in the modelled chain involves windrowing. Also
                  unglossed on first use: line-haul, upcountry, segregations, t.km,
                  tonne-days, carry-over, cash bids.

FARM-GATE vs BIDS "$380/t" farm-gate sits in the same panel as posted bids of "wheat
                  ~$268/t · barley ~$238/t" under the heading "What grain actually
                  sells for" — with no reconciliation, and those bids are explicitly
                  "none at EP sites off-season". A grower will notice.
```

---

## Assumptions: the arithmetic, checked

Every load-bearing calculation in the register, recomputed against the published anchors it
cites and against what the code measurably does.

| A# | Claim | Check | Verdict |
|---|---|---|---|
| A1 | 48 trucks/day ≈ 2,100–2,200 t/day implies ~45 t per line-haul load | 48 × 45 = 2,160 t/day, inside the cited band. 72 t ≈ 65% of an AB-triple at 110 t HML; 85 t ≈ 64% of Type 2 CML 132.83 t. Internally coherent. | **Holds** |
| A2 | PL's 13,148 t/day record requires ≥5 bays; 4 upcountry / 6 port | throughput reproduces (measured PL peak 13,845 t/day at 4/6, 9,300 at 2/4) — but the derivation assumes a 14 h receival day where the code dispatches 12 h and never closes the bays; under the code's own window A2's step gives 6 upcountry bays, not 4 (F23) | Conclusion ok, derivation unreproducible |
| A2 | Bay counts registered as an *assumption* | `calibrate.ts` fits them (countryBays 4.404, portBays 5.699); the "stress-test the assumptions" panel doesn't expose them | Category confusion |
| A4 | ≈2.5 Mt = 3.27 − 0.73; allocated proportional to district receivals; "matters only when sites fill" | subtraction right but mixes *season throughput* with *peak inventory*. Allocation never built: flat 120,000 t × 16 = **1.92 Mt**. Binds at 8 of 16 sites in the calibrated baseline and drives direct-to-port, peak queue and T-Ports intake (F20) | **Not implemented; sensitivity false** |
| A5 | Loaded trucks at 90 km/h trunk/primary, per class below | at the legal maximum, and A5's own reasoning says trucks "cruise below limits". Worse: an undocumented flat **75 km/h** converts minutes into every km and dollar shown (F10) | **Overridden by an unregistered constant** |
| A7 | Rain ≥ 5 mm stops harvest; 25% cut at tmax ≥ 38 °C | engine also runs a half-rate band, two hangover multipliers and a spring-dryness shift, none registered. Heat rule attributed to harvest bans, which track grassland fire danger — both inputs ship in the bundle unread (F24) | Incomplete; wrong driver |
| A9 | ~25% direct-to-port, per ESCOSA's "~75% to upcountry" | realised share measures **33.1%** (2025/26), 29.9% (2023/24), driven by the A4 cap. So the line-haul task the rail scenario exists to displace is understated ~10% | **Model runs 33%, not 25%** |
| A17 | Carry-in = observed Oct+Nov shipments; "receivals calibration unaffected" | 2022/23 emits 0 t from two missing spreadsheet rows; 2023/24 opens PL 81% full on day one. carryInScale 1 vs 0 moves 2023/24 receivals 1.832 → **1.922 Mt (+4.9%)** (F21) | **Not a measurement; sensitivity false** |
| A21 | 2 trainsets × 1,600 t, 4 h handling ⇒ "~2 cycles/day"; road fleet cut a third | trains use the *road* matrix at road speeds, reaching **4.0 cycles/trainset/day (12,800 t/day)** — ~6× Viterra's published replacement task. The fleet cut is applied only by `scripts/scenarios.ts` (F4) | **Ceiling not enforced** |
| A18 | 10¢/t·km ⇒ ≈$14/t over the 144 km average haul | 144 × 0.10 = $14.40, a fifth to a quarter of the cited $60–75/t whole-of-chain at 200 km. Sound as a level; but payload-invariant, so the register's finding that heavier road trains leave freight dollars unchanged is a property of the cost function, not a result | Level holds; inference doesn't |
| A19 | A$30k/vessel-day at anchor | consistent with US$15–25k/day for handy-to-panamax. The problem is the quantity it multiplies: anchorage is unbounded, giving 1,093 h/ship in drought (F6) | **Rate holds** |
| A22 | 9¢/t/day = ~$380/t at ~9% p.a. | 380 × 0.09 ÷ 365 = 9.4¢, and the register explicitly refuses to price weather, insect and quality risk rather than guessing | **Holds** |
| A23 | Lucky Bay premium at β = 1.965; "2.5× ≈ +$6/t" | code has `choiceBeta: 2.199`. The scenario sets 2.5 against a fitted default of 0.4, i.e. **6.25×**, and the app displays **$6.79/t** — so "$6/t" roughly survives and "2.5×" does not | Stale β, wrong multiplier |
| — | `stakeholder_review.md`: fleet is "589 at peak" | current fitted value is **731** | Stale |

---

## Verified as claimed — and genuinely good

Everything here was checked, not assumed.

```
5-minute tick        288/day, 105,120 ticks/season, full season in ~1.4 s      OK
seeded sfc32         no Math.random, no Date.now anywhere                      OK
determinism          two runs -> identical event-log hash 21dd3f75             OK
                     bulk-step equals day-by-day step, so seek is faithful     OK
mass conservation    the invariant is real, includes carry-in correctly, and
                     never fired in any run made during this review            OK
Huff site choice     attract / (minutes + queue + service)^beta, beta from
                     calibrated.json                                          OK
weather gating       rain gating, harvest ramp, spring-dryness shift,
                     per-commodity maturity — all as documented                OK
berth parameters     Port Lincoln 2 berths / 3,000 t.h, Thevenard 1,000 —
                     match ports.json                                         OK
like-for-like scope  kpi.receivedT is receivedBungeT only, so the KPI's claim
                     that Lucky Bay is counted separately is correct           OK
carry-in isolation   seeding touches s.stock and carryInT, never
                     cumReceivedT — it does not leak into "delivered"          OK
baseline alignment   i = s.day - 1 correctly matches the worker's post-step
                     push (exact at every midnight)                           OK
```

Worth protecting:

- **The assumptions panel's framing.** *"These don't change the world — they change the
  model's guesses. If a conclusion flips when you nudge one, treat it with care."* That is
  the correct instruction for a sensitivity control, in one sentence, in plain English — and
  the honest split between adjustable assumptions and the "not adjustable (baked into the
  data)" list is exactly right. It is also why F11 stings: the panel currently manufactures
  one of those flipped conclusions itself.
- **"How do we know the truck numbers?"** volunteers its own weakness — fleet fitted not
  counted, weakly identified, with the trade-off stated (~900 small trucks, ~730 average or
  ~500 road trains all reproduce the season). Very few models tell you which of their
  numbers not to trust.
- **Two places the project refuses to answer a question it can't.** The rail story gives the
  saving as a payload-dependent range and states it counts no rail capital or operating
  cost. A22 prices financing only and names weather, insect and quality risk as unpriced.
- **A2's correction note** documents the project's own past error — that 2/4 bays could not
  physically reproduce a published record day, and that the calibrator had been "buying
  missing site throughput with imaginary trucks". It also diagnoses F27 in advance.
- **Craft details that are easy to get wrong:** the fixed-shape comparison table (quiet rows
  dim to "≈ no change"); lever readouts in human units; well-written narrator sentences that
  are a pure function of state; a sound baseline lifecycle; a self-contained basemap with no
  tile server; hashed event logs, a held-out season, one-command regeneration.

---

## Suggested order of work

Sequenced by damage per unit of work. The first four are mostly small diffs with outsized
effect on whether a reader trusts anything else.

1. **F1 — the reality-check comparison.** Highest damage, smallest diff. The app is
   currently its own worst reviewer, and the honest numbers are better than the ones it
   prints.
2. **F4 — the rail scenario's freight sign, and surface `truckKm`.** The flagship policy
   scenario contradicts its own story. The number that vindicates it is already computed and
   discarded.
3. **F9, F13, F7 — the wrong numbers in the takeaways.** Delivery pace printing "299 days
   behind", assumption runs labelled "the season as it happened", a full-season figure at
   the top of a to-date table. All local fixes.
4. **F19 + F33 + F25 — the honesty pass.** Mostly copy: give the live season its own text,
   fix the tour's step-1 overclaim, regenerate `scenarios.md`, delete the stale carry-in
   limitation in two files.
5. **F14, F15, F16, F17, F18 — first run and time controls.** Pause behind the intro;
   backfill history on seek so the narrator stops lying; commit the scrubber on release;
   chunk the baseline; clear `done`.
6. **F26 + F27 — soften the queue guard.** Engine change plus a designed failure message.
   Until this lands, the Advanced mode built for exploration punishes exploring.
7. **F20, F21, F22, F10 — reconcile the register with the code.** Either build A4's
   allocation or document the flat constant; guard the carry-in builder; widen the pinned
   search bounds and refit; register the 75 km/h constant. This is the credibility spine.
8. **F31 — the accessibility floor.** Slider labels, three working modals, a keyboard route
   to site selection. Roughly a day for a large share of the benefit.
9. **F30 — mobile as a bottom sheet.** The largest job here, and the one that decides
   whether the intended audience can use this at all.
10. **F5, F6, F12, F23, F24, F28, F29, F32, F34, F35.** Mostly independent; several are
    one-line copy or constant changes.

---

Live measurements taken in-browser at viewports 1280×720, 750×1624, 393×851, 375×812,
667×375 and 358×506. Engine behaviour reproduced by instrumenting the real bundles
headlessly across seasons 2023/24, 2024/25, 2025/26 and 2026/27, seed 42. Arithmetic
recomputed from `data/ASSUMPTIONS.md`, `data/CALIBRATION.md`, `docs/calibration_report.md`,
`docs/scenarios_data.json` and the shipped `app/public/data` JSON.

`npm --workspace packages/sim run test` — 3 passed. `npm --workspace app run check` — 0
errors, 0 warnings. Working tree otherwise unchanged by this review.
