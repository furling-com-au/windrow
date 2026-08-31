# R0 — Ownership choice-set geometry, Eyre Peninsula

Generated 2026-08-31 by `pipeline/r8_choice_geometry.py`.

**Tier 2 (geometry): roads + site locations only. No simulation, no fitted parameter, no calibrated knob.**

**Reproduce**

```
.venv/Scripts/python.exe pipeline/r8_choice_geometry.py
```

---

## Headline

> **share of EP grain production with no independent receival point within 90 minutes' drive, 2025/26: 66.8 %**

That is the only number on this page that needs to be quoted. It is a level, not a trajectory and not a multiple, and it is the one figure here that survives every objection on record but one — A5 road speeds, disclosed immediately below:

- **It does not depend on A11.** Neither T-Ports bunker is a receival point in 2025/26 — both are closed for the season (published, tports.com/harvest) — so the ≤5 km tolerance on the Lock and Kimba town centroids cannot reach it. The A11 sweep below recomputes this row under all 129 displaced configurations and returns 66.8 % every time. Demonstrated, not asserted.
- **It does not depend on the site roster.** It is a *threshold* row — a function of the drive to the nearest independent point alone — and every roster defect on record is incumbent-side. The 2026-08-31 roster correction left it at exactly this value while moving the *gap* row 74.4 % → 77.3 %.
- **It does not depend on a privileged threshold.** No threshold on this page is designated a priori (see the next section). The whole sweep column for 2025/26 is printed below: 30 min 97.1 % · 45 min 93.2 % · 60 min 87.4 % · 75 min 78.2 % · 90 min 66.8 % · 105 min 53.2 % · 120 min 39.5 %. Read whichever row you find defensible; the lowest of them is 39.5 %.
- **It has survived three adversarial verification rounds unchanged**, including an independent reimplementation with its own graph, Dijkstra and weights.

What it *does* depend on is A5 road speeds, which are assumed. At the headline threshold this row reads 77.2 % at ×0.85 speeds, 66.8 % at ×1.00 speeds, 54.5 % at ×1.15 speeds. That band is a standing row, not a footnote — see below.

| 2025/26 — no independent receival point within R minutes | 30 min | 45 min | 60 min | 75 min | 90 min | 105 min | 120 min |
|---|---|---|---|---|---|---|---|
| ×0.85 travel speeds | 98.2 % | 95.0 % | 91.4 % | 85.7 % | 77.2 % | 67.3 % | 55.7 % |
| **×1.00 (published A5) — the headline row** | 97.1 % | 93.2 % | 87.4 % | 78.2 % | **66.8 %** | 53.2 % | 39.5 % |
| ×1.15 travel speeds | 96.1 % | 90.8 % | 82.1 % | 69.7 % | 54.5 % | 38.9 % | 27.8 % |

**Everything else on this page is supporting material.** The 2023/24 → 2025/26 trajectory and the 3.3× multiple (which is 2.72×–3.35× once A11 is swept) are real, and they are kept — in a supporting section further down, where every figure carries its A11 range. They are not load-bearing any more, because both run through the 2023/24 column and that column moves inside A11's own stated tolerance.

**This page is Ladder B only.** Every count-of-receival-points row that used to sit here has been moved to Appendix A and must not be quoted — see [Appendix A](#appendix-a--ladder-a-choice-count-not-publishable).

---

## The threshold — no privileged value

**Designation: none - no threshold on this page is privileged.**

NO THRESHOLD ON THIS PAGE IS DESIGNATED A PRIORI. Earlier drafts designated 90 minutes on two grounds; both have been withdrawn (see below) and nothing has replaced them. The full 30-120 minute sweep is published instead and no row in it is privileged: a reader who prefers 60 minutes, or 120, should read that row. The 90-minute row is the one the headline quotes because it is the middle of the published grid and gives one legible number, not because it was selected or justified.

The two withdrawn grounds, kept on the page so the withdrawal is checkable:

- WITHDRAWN 2026-08-31, ground 1 (cartage cost). This ground read 90 minutes as 105-135 km at A5 speeds and priced it at A$7-18/t using what the page called A18's 'published range' of A$0.07-0.13/t-km. That description was false. A18 is an INDICATIVE REPO ASSUMPTION, not a published schedule: its own entry in data/ASSUMPTIONS.md states in terms, 'No single public EP $/t-km schedule exists', and the 0.07-0.13 band is this project's own tolerance around a A$0.10/t-km working value, consistency-checked against published anchors rather than read off a published rate card. A threshold cannot be designated a priori on a number this repo made up, however reasonable that number is.
- WITHDRAWN 2026-08-31, ground 2 (a working day's round trip). This ground derived a four-loads-a-day cap from A2's 12 h farm-truck dispatch window (07:00-19:00, engine.ts sitesOpenNow). A2's bays and service times are FITTED simulation parameters, and this page's whole standing rests on depending on none of A1, A2, A9 or A24. Leaning the threshold on A2 would have made that independence claim false. The ground is withdrawn rather than the independence claim, because the independence claim is exactly true without it and is load-bearing for the tier structure of the piece.

Searched for a genuinely published basis for any cart-range threshold on EP, and none was found. data/ASSUMPTIONS.md A18 records that no public EP $/t-km schedule exists. The ACCC's 2021 Port Lincoln and Thevenard Final Determinations discuss grain catchments qualitatively and in port-to-port kilometres (Lucky Bay 177 km from Port Lincoln, 412 km from Thevenard) and state expressly that 'distance, while important, is only one factor'; they publish no grower cart-range threshold. The 2018 Eyre Peninsula Freight Study contains no cart-range figure either. Rather than stand a designation on an adjacent citation, the designation is dropped.

Disclosed against interest, and it no longer bites the headline: 90 min is where the 2025/26-to-2023/24 RATIO of this row peaks across the sweep, and the repo holds no record of the threshold being registered before the sweep was run. That objection is an objection to the MULTIPLE, which is no longer the headline - it has been demoted to the supporting section. The headline is a single 2025/26 LEVEL, and the whole 2025/26 sweep column is printed beside it so that no choice of threshold is being made on the reader's behalf: the 2025/26 level is 97.1 % at 30 min and still 39.5 % at the most generous 120-minute row. Separately, note the direction of generosity: a WIDER threshold is generous to the INDEPENDENT side of the comparison, because it counts a more distant alternative as a live option, so reading the 90-minute row rather than the 60-minute one understates the finding.

The full sweep, tonne-weighted share of EP production with **no independent receival point within R minutes**. The ratio between the two columns is *not* shown here: it is a supporting quantity, it depends on the 2023/24 column, and it is published in the supporting section below with its A11 range attached.

| R (min, one way) | 2023/24 (carries the A11 range — see the A11 sweep) | **2025/26 — the headline column** |
|---|---|---|
| **30** | 83.6 % (83.2 %–86.0 %) | 97.1 % |
| **45** | 66.3 % (65.8 %–70.8 %) | 93.2 % |
| **60** | 50.0 % (50.0 %–56.1 %) | 87.4 % |
| **75** | 32.9 % (31.9 %–39.9 %) | 78.2 % |
| **90** **(quoted by the headline)** | 20.3 % (19.9 %–24.6 %) | **66.8 %** |
| **105** | 16.5 % (16.2 %–17.2 %) | 53.2 % |
| **120** | 13.9 % (13.7 %–15.4 %) | 39.5 % |

Pre-2019 has no column here: with a single operator there is no independent point to be within any radius of, at any threshold.

---

## Travel-speed sensitivity — a standing row, not a footnote

**A uniform error in A5's road speeds does NOT cancel out of the published rows.** It would cancel out of a *ratio* of two drive times, but both published rows are thresholded in **absolute minutes**, so a speed error moves the threshold. Any claim to the contrary is false and must not appear in the piece.

Method: A uniform scaling of every A5 class speed by f divides every routed minute by f and cannot change which path is least-time, so the scaled network is obtained exactly by scaling minutes rather than re-routing.

Share of production with **no independent point within R minutes**, by travel speed:

| Travel speeds | 30 min | 45 min | 60 min | 75 min | 90 min | 105 min | 120 min |
|---|---|---|---|---|---|---|---|
| _2023/24_ |  |  |  |  |  |  |  |
| &nbsp;&nbsp;x0.85 | 87.4 % | 74.4 % | 59.8 % | 46.8 % | 31.3 % | 20.7 % | 16.9 % |
| &nbsp;&nbsp;x1.00 (published A5) | 83.6 % | 66.3 % | 50.0 % | 32.9 % | 20.3 % | 16.5 % | 13.9 % |
| &nbsp;&nbsp;x1.15 | 78.7 % | 59.1 % | 39.4 % | 23.1 % | 16.7 % | 13.8 % | 10.6 % |
| _2025/26_ |  |  |  |  |  |  |  |
| &nbsp;&nbsp;x0.85 | 98.2 % | 95.0 % | 91.4 % | 85.7 % | 77.2 % | 67.3 % | 55.7 % |
| &nbsp;&nbsp;x1.00 (published A5) | 97.1 % | 93.2 % | 87.4 % | 78.2 % | 66.8 % | 53.2 % | 39.5 % |
| &nbsp;&nbsp;x1.15 | 96.1 % | 90.8 % | 82.1 % | 69.7 % | 54.5 % | 38.9 % | 27.8 % |

At the 90-minute threshold the headline row reads 31.3 % → 77.2 % at x0.85 speeds, 20.3 % → 66.8 % at published A5 speeds, and 16.7 % → 54.5 % at x1.15. The multiple ranges 2.47×–3.29× across that band. **Direction and sign survive; the levels are materially A5-dependent, and any number quoted from this page carries that dependence.**

---

## Supporting — the 2023/24 → 2025/26 trajectory and the multiple

**Demoted 2026-08-31. Not load-bearing, and not the headline.** These figures are real and are not withdrawn. They are moved here because every one of them runs through the 2023/24 column, and the 2023/24 column moves inside A11's own stated ≤5 km tolerance on the Lock and Kimba coordinates. Each figure below is therefore printed with its A11 range, and **no figure from this section may be quoted without that range**.

| Row | pre-2019 | 2023/24 (A11 range) | 2025/26 |
|---|---|---|---|
| No independent point within 90 min | _undefined — single operator_ | 20.3 % (**19.9 %–24.6 %**) | **66.8 %** (A11-independent) |
| &nbsp;&nbsp;same row, ×0.85 travel speeds | _undefined_ | 31.3 % | 77.2 % |
| &nbsp;&nbsp;same row, **×1.00 (A5 as published)** | _undefined_ | 20.3 % | 66.8 % |
| &nbsp;&nbsp;same row, ×1.15 travel speeds | _undefined_ | 16.7 % | 54.5 % |
| Nearest independent >60 min beyond nearest Bunge (**gap row — not roster-invariant, see the note below**) | _undefined_ | 33.0 % (**32.8 %–38.4 %**) | 77.3 % (A11-independent) |
| &nbsp;&nbsp;same row, ×0.85 travel speeds | _undefined_ | 42.8 % | 84.5 % |
| &nbsp;&nbsp;same row, **×1.00 (A5 as published)** | _undefined_ | 33.0 % | 77.3 % |
| &nbsp;&nbsp;same row, ×1.15 travel speeds | _undefined_ | 22.3 % | 69.7 % |
| Distinct operators on the peninsula | 1 | 2 | 2 |

The trajectory as a sentence, with the range that must travel with it: **between 2023/24 and 2025/26 the share of EP grain production with no independent receival point inside a 90-minute cart went from 20.3 % — anywhere in 19.9 %–24.6 % once A11's coordinate tolerance is swept — to 66.8 %**, driven by two site closures. The pre-2019 cell of that row is blank on purpose: there was nothing independent to be far from.

**The multiple.** On the published coordinates it is 3.29×. Across the A11 sweep it ranges **2.72×–3.35×**. Across the travel-speed band it ranges 2.47×–3.29×, and across the threshold sweep 1.16×–3.29×, with 90 min sitting at the top of that last range. Three separate sensitivities each move it by more than a third of its own size. That is why it is here and not at the top of the page. What does not move: the 2025/26 level exceeds the 2023/24 level at every threshold in the sweep, at every travel speed tested and at every A11 configuration.

**The gap row is not roster-invariant.** The invariance holds for the THRESHOLD rows only, and is FALSE of the gap rows. All four roster-defect sites are INCUMBENT-operated (Tooligie, Cowell, Mangalo and Cungena are all ex-Viterra/Bunge). A THRESHOLD row ('no independent point within R minutes') is a function of the drive to the nearest INDEPENDENT point alone, so it cannot move when an incumbent site is added or removed: that is a structural invariance, not a coincidence, and it is why the headline survives a roster defect that destroys Ladder A. A GAP row ('nearest independent more than R minutes beyond nearest Bunge') is NOT protected that way. The gap is measured FROM the incumbent, so adding an incumbent site moves it - and this repo's own roster correction of 2026-08-31 did move it, from 74.4 % to 77.3 % at 2025/26 and from 32.9 % to 33.0 % at 2023/24 (docs/roster_audit_2026-08.md section 4, correction note). Every gap row on this page must therefore be quoted as 'on the roster as corrected 2026-08-31', and the piece's headline must be a threshold row.

---

## A11 — the Lock and Kimba coordinate sweep (standing table)

A11 gives the Lock and Kimba T-Ports bunker coordinates a <=5 km tolerance (town centroids; exact pads unpublished). Both sites are displaced over that tolerance and every published row is recomputed.

**Method.** For each offset the site is moved to a new lon/lat, RE-SNAPPED to the nearest OSM node and RE-ROUTED with a fresh Dijkstra tree. Minutes are not scaled or interpolated. Lock and Kimba are displaced independently, so every combination of the two bearings is evaluated and the reported extremes are the true extremes over the grid. Offsets 0.0, 2.5, 5.0 km; bearings 0, 45, 90, 135, 180, 225, 270, 315°; 129 configurations in all, every one of them in the JSON under `a11_coordinate_sweep.grid`. "Most favourable" means lower 2023/24 share (larger multiple against the fixed 2025/26 level).

| Lock/Kimba displacement | Direction (Lock°, Kimba°) | 2023/24: no independent within 90 min | 2023/24: gap >60 min | 2025/26: no independent within 90 min | multiple |
|---|---|---|---|---|---|
| **0 km** — published coordinates | — (as published) | 20.3 % | 33.0 % | 66.8 % | 3.29× |
| **2.5 km** — most favourable | 180°, 0° | 19.9 % | 32.8 % | 66.8 % | 3.35× |
| **2.5 km** — least favourable | 45°, 0° | 21.8 % | 33.9 % | 66.8 % | 3.06× |
| **5 km** — most favourable | 180°, 0° | 20.5 % | 33.5 % | 66.8 % | 3.25× |
| **5 km** — least favourable | 0°, 0° | 24.6 % | 38.4 % | 66.8 % | 2.72× |

The extremes above are selected on the 90-minute threshold row. The gap column shows that same configuration's gap value, not the gap row's own extreme; across the whole sweep the 2023/24 gap >60 min row runs 32.8 %–38.4 % against a published 33.0 %.

**Range over the whole sweep.** The 2023/24 90-minute row runs 19.9 %–24.6 % against a published 20.3 %; the multiple runs 2.72×–3.35× against a published 3.29×. The 2025/26 row is 66.8 % at every one of the 129 configurations. Neither Lock nor Kimba is a receival point in this state - both bunkers are closed for 2025/26 (published, tports.com/harvest) - so no displacement of either can reach it. Computed under all 129 configurations rather than asserted.

**A11's asymmetry claim, tested.** A11's own entry claims the error 'can only ever make the 2023/24 baseline worse, never better'. This sweep is where that claim is tested rather than repeated. On this sweep the 2023/24 90-minute share moves **−0.3 pp / +4.3 pp** around its published 20.3 %. So the claim is **too strong as A11 words it**: a 19.9 % configuration exists, and the share can fall as well as rise. What survives is the weaker statement, which is the one that matters — the error is strongly asymmetric in SIZE. The movement that raises the 2023/24 share (+4.3 pp) is about 13× the movement that lowers it (−0.3 pp), so a reader who wants a single number rather than a range should take the pessimistic end, 24.6 %, not the published 20.3 % — and the trajectory and multiple should be read from there. **A11's own wording should be narrowed from 'never better' to this.**

The 2023/24 envelope across the whole threshold sweep, for a reader who rejects 90 minutes:

| R (min) | 30 | 45 | 60 | 75 | 90 | 105 | 120 |
|---|---|---|---|---|---|---|---|
| 2023/24, published coordinates | 83.6 % | 66.3 % | 50.0 % | 32.9 % | 20.3 % | 16.5 % | 13.9 % |
| 2023/24, A11 envelope | 83.2 %–86.0 % | 65.8 %–70.8 % | 50.0 %–56.1 % | 31.9 %–39.9 % | 19.9 %–24.6 % | 16.2 %–17.2 % | 13.7 %–15.4 % |
| 2025/26 (A11-independent) | 97.1 % | 93.2 % | 87.4 % | 78.2 % | 66.8 % | 53.2 % | 39.5 % |

---

## The definitional problem, handled up front

The brief asks for "nearest independent receival point" at three network states. At the first state that quantity does not exist. Pre-2019 the entire EP receival network — every point on it, however many that was — was operated by a single company (Viterra, since Aug 2025 Bunge Operations Pty Ltd). There was no independent option anywhere on the peninsula, at any distance. That statement is about *ownership*, and it does not depend on the site count, which is why it survives the roster defect that invalidates Ladder A.

That is not a large ownership gap. It is an undefined one, and the difference matters in the wrong direction: if you score pre-2019 as "100 % of production has no independent option within cart range" and then score 2025/26 the same way, the 2019 closure of six sites reads as an *improvement* in competitive choice. It was not. It was a reduction in the number of places to deliver, inside a monopoly.

So this analysis reports two ladders and never adds them:

| | Ladder A — **choice count** | Ladder B — **ownership gap** |
|---|---|---|
| Question | How many receival points can this paddock reach, whoever owns them? | How much further is the nearest *non-incumbent* point than the nearest incumbent one? |
| Defined at | all three states | 2023/24 and 2025/26 only |
| What moved it | the 2019 closure of six sites | T-Ports' entry, then the 2025/26 bunker closures |
| Status | **NOT PUBLISHABLE** — roster incomplete, see Appendix A | **publishable**, with a split: the *threshold* rows are invariant to the roster defect, the *gap* rows are **not** — the gap is measured from the incumbent, and the 2026-08-31 roster correction moved it 74.4 % → 77.3 % at 2025/26 |

**Incumbent** = `Bunge (ex-Viterra)` plus the pre-rename tag `ex-Viterra`, treated as one owner throughout. **Independent** = anything else — on EP today, T-Ports alone. Merging the two Viterra/Bunge tags is the conservative choice for this piece: keeping them apart would have counted the six 2019-closed sites as a second "operator" and manufactured competition that never existed.

---

## Network states

| State | Independent points | Distinct operators | Composition |
|---|---|---|---|
| **pre-2019** | 0 | 1 | the 6 sites that closed in 2019 still open; the 22 currently-active Bunge sites plus the 1 now-dormant one(s) treated as open (A12); T-Ports does not yet exist |
| **2023/24** | 3 | 2 | current Bunge network (22 active) + T-Ports Lucky Bay + the Lock and Kimba bunkers, which ran that season |
| **2025/26** | 1 | 2 | current Bunge network (22 active) + T-Ports Lucky Bay only; both inland bunkers closed for the season (published, tports.com/harvest) |
| _pre-2019 (sensitivity: dormant excluded)_ | 0 | 1 | as pre-2019 but without the 1 site(s) still tagged dormant, in case they were already idle before 2019 |

Membership is taken from the published `status` field of `sites.geojson` — no per-site judgement. **The total receival-point count of each state is deliberately not shown here**; it is a Ladder A quantity and the roster it comes from is incomplete (Appendix A). The *independent* count is shown because it is a count of T-Ports sites only, and every roster defect on record is on the incumbent side. Composition text is generated from the file, not typed, so a roster correction cannot leave a stale description behind it.

---

## Ladder B — incumbent vs independent (2023/24 and 2025/26 only)

Gap = drive time to the nearest independent point **minus** drive time to the nearest Bunge point.

**Read the row types differently.** The *threshold* rows ("no independent point within R min") are invariant to the site-roster defect. The *gap* rows ("nearest independent >R min beyond nearest Bunge") are **not** — they are measured from the incumbent, so they move when the roster does, and they must be quoted as "on the roster as corrected 2026-08-31". The 2023/24 column of every row here additionally carries the A11 range.

The gap rows were computed twice — once counting cells with no independent point at all as beyond every threshold, once dropping them — to bracket the answer. **The two are identical**, because every EP production cell can reach Lucky Bay by road, so no cell has literally zero independent option at either state. Only one set of rows is shown.

| Metric | 2023/24 | 2025/26 |
|---|---|---|
| Independent receival points | 3 | 1 |
| Mean drive to nearest Bunge point (min) | 18.7 | 18.7 |
| Mean drive to nearest independent point (min) | 71.3 | 124.6 |
| Share with nearest independent >30 min beyond nearest Bunge | 65.9 % | 91.1 % |
| Share with nearest independent >60 min beyond nearest Bunge | 33.0 % | 77.3 % |
| Share with nearest independent >90 min beyond nearest Bunge | 16.6 % | 51.4 % |
| Share with **no** independent point within 90 min (full 30–120 min sweep above; **only the 2025/26 cell is the headline**) | 20.3 % (A11 range 19.9 %–24.6 %) | **66.8 %** |
| Share whose nearest independent point is a **port** | 12.4 % | 100.0 % |
| _Counterweight:_ share where the independent point is **nearer** than Bunge | 12.2 % | 4.6 % |

Which independent point is nearest, by tonne share:

- **2023/24** — Lock (T-Ports bunker) 70.2 %; Kimba (T-Ports bunker) 17.4 %; Lucky Bay (T-Ports port) 12.4 %
- **2025/26** — Lucky Bay (T-Ports port) 100.0 %

Pre-2019 has no row here. See the definitional note above.

**Plausible cart range.** No published EP figure exists for how far a grower will cart before the delivery stops being worth making, and this analysis refuses to borrow the sim's fitted `choiceRadius` — that would put a calibrated knob inside a Tier-2 number. Nor is any threshold designated a priori — two earlier grounds for designating 90 minutes were withdrawn on 2026-08-31 and nothing replaced them. The 30–120-minute sweep above is published in full instead, with no row privileged. The geometry that bounds it: in 2025/26 the tonne-weighted drive to the nearest **Bunge** point is a median 16.5 min, 90th percentile 33.2 min, 99th percentile 58.3 min — so a 90-minute range is roughly five times the trip an EP grower actually makes to the incumbent, and is generous to the independent side of the comparison.

---

## By district

Ladder B only. The per-district Ladder A columns (`wmean_nearest_min`, `share_only_one_within_45`) are still emitted to the JSON for the roster rebuild but are **not shown here and not publishable** — see Appendix A. A district cut of a count-of-points row inherits the roster defect in full, and concentrates it: a missing site distorts its own district more than it distorts the peninsula.

**2023/24**

| District | wmean_nearest_independent_min | share_no_independent_within_90 | share_gap_over_60_incl_none |
|---|---|---|---|
| WEP | 118.5 | 61.7 % | 62.8 % |
| LEP | 69.3 | 6.8 % | 39.0 % |
| EEP | 32.4 | 0.0 % | 0.0 % |

**2025/26**

| District | wmean_nearest_independent_min | share_no_independent_within_90 | share_gap_over_60_incl_none |
|---|---|---|---|
| WEP | 206.9 | 98.6 % | 99.9 % |
| LEP | 110.6 | 79.7 % | 91.8 % |
| EEP | 69.0 | 23.8 % | 40.4 % |

---

## Sensitivity — what would have to be wrong

**The tonne weighting.** The headline holds production fixed at the 2022/23–2025/26 district mean so the trajectory is a network effect, not a weather effect. Re-run under each state's own harvest, and unweighted (one vote per production cell):

| Weighting | 2023/24 gap >60 min | 2023/24 no indep. within 90 min | 2025/26 gap >60 min | 2025/26 no indep. within 90 min |
|---|---|---|---|---|
| fixed mean 2022/23–2025/26 (**headline**) | 33.0 % | 20.3 % | 77.3 % | 66.8 % |
| each state's own season | 34.0 % | 20.2 % | 75.7 % | 64.7 % |
| unweighted cells (one vote per cell) | 42.6 % | 35.8 % | 80.7 % | 73.7 % |

Every 2023/24 cell in that table is a supporting figure and carries the A11 range on top of the weighting spread; the 2025/26 cells do not. The fixed weighting is not what produces the result: the trajectory is the same sign and roughly the same size on all three. Unweighted is the harshest reading because far-west and eastern marginal cells vote equally with high-yield Lower EP country; the tonne-weighted headline is the conservative one.

**"No independent option at all" is entirely a cart-range question, not a reachability one.** Every production cell on EP can reach Lucky Bay by road, so no cell has literally zero independent option at any state. The finding is about how far the option is, and the cart-range sweep is where that judgement lives. A reviewer who rejects 90 minutes as a cart range should substitute their own threshold from the published sweep: 2025/26 exceeds 2023/24 at all seven, and the share is still 39.5 % of production at the most generous (120 min) row.

**Road-network snap.** Tonne-weighted mean snap 1.99 km, 44.3 % of production beyond 2 km and 1.3 % beyond 5 km (worst single cell 9.47 km, far-west marginal country). A cell is routed from its nearest node on the OSM graph; the snap leg itself is not driven, so a large snap UNDERSTATES that cell's drive time to everything equally. It cannot manufacture an ownership GAP, because a gap row is a difference of two times that share the same snap. IT DOES BEAR ON THE THRESHOLD ROWS, exactly as a speed error does: 'no independent point within R minutes' is an absolute-minute test, so an understated drive time makes a cell more likely to pass it. The snap therefore FLATTERS the network on the headline row rather than the reverse - it works against the finding, not for it. Worst site snap is 0.65 km, i.e. every receival point is on the graph.

---

## Wharminda — the worked example

Wharminda is one of the six sites tagged `closed_2019` in `sites.geojson`; it is used here as a worked example because it sits in the middle of the eastern cropping country and makes the ownership arithmetic legible in a single row.

> Removed 2026-08-31: this paragraph previously asserted that 'Wharminda Road is named in the reporting as one of the roads that absorbed the extra truck traffic' after grain rail ceased in May 2019. Reworded 2026-08-31 - the earlier reason given here, that no outlet, date or URL supported the sentence anywhere in this repo, is no longer true of its own tree: data/SOURCES.md now registers two, the Eyre Peninsula Freight Study (SMEC ref. 3005591 Rev 0 Final, 26 Sept 2018) and Jarrad Delaney's report of it in the Port Lincoln Times, 10 Apr 2019. THE DELETION STANDS, on a different and stronger ground: both sources are PROSPECTIVE. The study is a forecast finalised eight months before grain rail ceased, the newspaper's verb is 'will include', and it was published 10 Apr 2019, seven weeks before the last grain train on 31 May 2019. Neither observes what any road actually carried afterwards, and the only post-closure survey on record (RAA, 2 Aug 2024) names Balumbah-Kinnard Road, Lincoln Highway and Tod Highway but does NOT name Wharminda Road. So the roads were named in advance as the ones that WOULD carry the freight; that they DID absorb it is unsourced, and a prospective citation may not stand in for the post-hoc one the sentence needed. The geometry below stands on its own and needs no press citation.

Nearest receival points to the closed site, by state:

| State | Nearest four receival points | Nearest **independent** point |
|---|---|---|
| pre-2019 | Wharminda (closed) 0.0 min; Port Neill 21.1 min; Rudall 29.1 min; Arno Bay 32.5 min | _none exists — single operator_ |
| 2023/24 | Port Neill 21.1 min; Rudall 29.1 min; Arno Bay 32.5 min; Tumby Bay 38.3 min | Lock (T-Ports bunker) — **59.4 min** |
| 2025/26 | Port Neill 21.1 min; Rudall 29.1 min; Arno Bay 32.5 min; Tumby Bay 38.3 min | Lucky Bay (T-Ports port) — **74.6 min** |

The Bunge column does not move between 2023/24 and 2025/26 — Wharminda's surroundings kept the same incumbent options. What moved is the third column: the nearest non-Bunge point went from a bunker to a port on the far side of the peninsula. That is the whole finding in one row.

_Caveat on the middle column._ "Nearest four receival points" is a Ladder A quantity and inherits the roster defect: Tooligie in particular sits in this part of the peninsula and is missing from `sites.geojson` altogether, so a nearer incumbent option may be absent from that column. The right-hand column is unaffected — it lists independent points, and every roster defect on record is incumbent-side. Quote the right-hand column, not the middle one.

---

## What this does and does not establish

**Does.** Every number above is a distance measured on a published road network between published site locations, weighted by published district production. It depends on no simulation output, no calibrated parameter, and none of A1, A2, A9 or A24. That claim is now **exactly** true rather than approximately so: until 2026-08-31 the second ground of the threshold argument on this page reasoned from A2's 12 h farm-truck dispatch window, which made the sentence false as written. That ground has been withdrawn rather than the sentence weakened, because the independence is what the whole tier structure of the piece rests on. An opposing expert can dispute the queue model; they cannot dispute how far Wharminda is from an alternative.

**Does not.** It says nothing about intent — the Lock and Kimba bunkers closing for 2025/26 is entirely consistent with a drought year and bunker economics, and the piece should say so. It says nothing about price. It says nothing about whether a grower *would* use a more distant option; it measures the option set, not the choice. And 'nearest' is drive time, not commercial terms: a site that is close but does not segregate the grade a grower is carting is not, in practice, a choice — this analysis counts it as one, which is conservative for the incumbent.

## Carried assumptions

- **A5** road class speeds - the only assumed input to the routing, and THE LEVELS ON THIS PAGE ARE MATERIALLY SENSITIVE TO IT, because every published row is thresholded in absolute minutes. Swept at x0.85/x1.00/x1.15 as a standing row. A5 error does NOT cancel; earlier drafts of this page said it largely did, and that was wrong.
- **A11** T-Ports Lock/Kimba coordinates are town centroids, not the exact pads (<=5 km tolerance). Both sites are in the 2023/24 state only. A11 as rewritten 2026-08-31 records that this error is NOT negligible for this page, and it is now SWEPT rather than argued about - see the A11 sweep table. Every 2023/24 figure and every multiple on this page carries that range. The 2025/26 headline does not: neither bunker is in that state, and the sweep demonstrates the level does not move.
- **A12** season site sets. Load-bearing for Ladder A and the reason Ladder A is not publishable: the roster is an operator snapshot, not a per-season site list. The known defects are named in Appendix A. This script still builds its states from the single `status` field rather than from `operating_seasons`.
- **A14** district boundaries approximated by LGA composition - used for the tonne weighting, not for routing.
- **A15** is NOT used: the 2025/26 bunker closure is published (tports.com/harvest), and 2024/25 is not one of the three states.
- **A18** road grain freight rate. NO LONGER USED FOR ANYTHING ON THIS PAGE. It formerly supplied the cost argument that designated the 90-minute threshold a priori; that ground is withdrawn, because A18 is an indicative repo assumption and not a published rate schedule - A18's own entry says 'No single public EP $/t-km schedule exists'. It enters no computed number here and no longer supports any designation.
- **A4** capacities are not used at all. This analysis is geometry; no site's capacity enters any number on this page.
- **A2** is NOT used, and must not be. An earlier draft leaned the threshold argument on A2's 12 h farm-truck dispatch window; that ground is withdrawn, so this page's independence from A1, A2, A9 and A24 is exact rather than approximate.

---

## Appendix A — Ladder A (choice count). NOT PUBLISHABLE

> **Do not quote any row in this appendix.** NOT PUBLISHABLE. Every row on Ladder A is a count of receival points, and the site roster this count is taken from is known to be incomplete: Tooligie, Cowell and Mangalo are missing from sites.geojson altogether and Cungena's closed_2019 tag is contradicted by the operator's own weekly reports (docs/roster_audit_2026-08.md section 5). All four bear on at least one of the three states reported here: Cowell and Mangalo were receiving grain before 2019 and are absent from the pre-2019 state; Tooligie was receiving grain in 2023/24 and is absent from that state; Cungena's closed_2019 tag is contradicted by a 2022/23 receival, so it is wrongly excluded from the post-2019 states. The rows have been wrong twice already. They are retained in an appendix as the audit trail for the roster rebuild, under this caveat, and must not be quoted.

The specific defects, all from `docs/roster_audit_2026-08.md` section 5:

| Site | Defect |
|---|---|
| **Cowell** | operated 2017/18 and 2018/19; absent from sites.geojson entirely |
| **Cungena** | tagged closed_2019 but named receiving grain in 2022/23; the tag is contradicted by the operator's own report |
| **Mangalo** | opened for first receivals 2018/19; absent from sites.geojson entirely |
| **Tooligie** | operated 2022/23, 2023/24 and 2024/25 per the operator's weekly reports; absent from sites.geojson entirely |

This script still builds its network states from the single `status` field rather than from `operating_seasons`, so the 2023/24 state omits Nunjikompita, which was named receiving that season. Ladder B is unaffected (Nunjikompita is Bunge).

**Why this is an appendix and not a deletion.** These rows are the audit trail for the roster rebuild — they record what the counts were before the roster was fixed, which is what makes the next correction checkable. Deleting them would destroy that record and would also hide the fact that the row has been wrong twice. They are kept, fenced, and labelled, and the headline table above contains no count of receival points at all.

**Why the headline survives this.** The invariance holds for the THRESHOLD rows only, and is FALSE of the gap rows. All four roster-defect sites are INCUMBENT-operated (Tooligie, Cowell, Mangalo and Cungena are all ex-Viterra/Bunge). A THRESHOLD row ('no independent point within R minutes') is a function of the drive to the nearest INDEPENDENT point alone, so it cannot move when an incumbent site is added or removed: that is a structural invariance, not a coincidence, and it is why the headline survives a roster defect that destroys Ladder A. A GAP row ('nearest independent more than R minutes beyond nearest Bunge') is NOT protected that way. The gap is measured FROM the incumbent, so adding an incumbent site moves it - and this repo's own roster correction of 2026-08-31 did move it, from 74.4 % to 77.3 % at 2025/26 and from 32.9 % to 33.0 % at 2023/24 (docs/roster_audit_2026-08.md section 4, correction note). Every gap row on this page must therefore be quoted as 'on the roster as corrected 2026-08-31', and the piece's headline must be a threshold row.

Tonne-weighted over EP grain production. "Points within R" counts receival points of any ownership reachable within R minutes' one-way drive. Note the row label is **at most one**, not "only one": the underlying test is `count <= 1`, so cells with *zero* points inside the radius are included.

| Metric | pre-2019 | 2023/24 | 2025/26 |
|---|---|---|---|
| Receival points in network | 29 | 25 | 23 |
| Mean drive to nearest point (min) | 17.5 | 17.8 | 17.9 |
| Median drive to nearest point (min) | 15.2 | 16.3 | 16.5 |
| 99th pct drive to nearest point (min) | 58.3 | 43.8 | 43.8 |
| Mean points within 30 min | 2.07 | 1.83 | 1.7 |
| Mean points within 45 min | 4.06 | 3.57 | 3.3 |
| Mean points within 60 min | 6.23 | 5.48 | 4.99 |
| Share with **at most one** point within 30 min | 35.8 % | 41.8 % | 48.3 % |
| Share with **at most one** point within 45 min | 9.5 % | 10.5 % | 12.0 % |
| Share with **at most one** point within 60 min | 3.2 % | 2.4 % | 2.4 % |
| Share whose 2nd-nearest point is >30 min beyond the 1st | 4.3 % | 7.0 % | 7.0 % |
| Share whose 2nd-nearest point is >60 min beyond the 1st | 0.0 % | 0.0 % | 0.0 % |
| Share whose 2nd-nearest point is >90 min beyond the 1st | 0.0 % | 0.0 % | 0.0 % |

Reproduce these rows (they are also in the JSON under `states.<state>.ladder_a_choice_count`, flagged `publishable: false`):

```
.venv/Scripts/python.exe pipeline/r8_choice_geometry.py
```

