# R9 findings — cartage dollars by district, and the "$15 per tonne" claim

**(a) THE CARTAGE FIGURES: NOT PUBLISHABLE. (b) THE CLAIM TEST: NOT PUBLISHABLE.**

Both adversarial verifiers returned `refuted: true` at high confidence. Neither refutation
touches the arithmetic — both independently reproduced every figure, one of them from a
from-scratch reimplementation (own graph load, own snapper, own Dijkstra, own rate
function). What failed is what has failed every round on this project: presentation and
provenance.

- **(a) fails on three counts.** A marginal rate is applied to whole hauls to produce two
  *levels* that the page labels "the bill growers actually pay" and "the direct-to-port
  run"; the one note telling the reader how to discount those levels is calibrated at a
  144 km haul when the measure it governs has a 21 km mean, understating the shortfall by
  ~3.5x; and a row printed as an **upper bound** (D→C, +$0.22/t) is falsified by this
  repo's own roster audit — restoring Cowell and Mangalo takes it to +$0.45/t.
- **(b) fails at the first gate.** The claim under test has **no source in this repo**.
  `grep -rn -i arowana data/` returns nothing. There is no `SOURCES.md` entry, no cached
  page, no URL, no outlet, no retrieval date, and no evidence for the September 2021 date.
  The only occurrence of the quoted words anywhere outside the R10 scripts' own output is
  the orchestrating prompt at `.claude/workflows/ep-cartage.js:178`. Under
  `docs/ready_to_draft.md` D2 — *if it cannot be sourced, it cannot be written* — that
  ends it. The company's name is also misspelled ("Arrowana") in the fair-dealing section.

What survives, and should not be re-derived: the ESCOSA rate work is sound (`VERDICT: PASS`),
the one-way flat-band application rule is established by reproducing ESCOSA's own four
published results 4/4, the deltas between network states are legitimately marginal and
robust across cost functions, and the substantive conclusion of the claim test — supported
for a small eastern minority, not peninsula-wide — is probably right. It is the *page* that
cannot be printed, not the finding.

---

## 2. The headline table — cartage A$/t by district, four network states

**These numbers are reproducible and correct as arithmetic. They are NOT cleared for
publication.** M1 and M4 are levels produced by a marginal rate and must not be printed as
"the bill" (defect 1, below); the D column carries a falsified bound (defect 3).

Network states. **A** = Bunge network + Lucky Bay (23 points, 1 independent).
**B** = A + the Lock and Kimba bunkers (25, 3). **C** = Bunge alone (22, 0).
**D** = pre-2019: Bunge + the six sites closed June 2019 + Nunjikompita (29, 0).
Season labels are attributions, and the one that matters is unsourced — see defect 6.

### M1 — cartage to the nearest receival point of any owner (A$/t, marginal, one-way)

| District | A. Lucky Bay only | B. + bunkers | C. no independent | D. pre-2019 |
|---|---|---|---|---|
| **EP (all)** | **$2.52** | **$2.51** | **$2.66** | **$2.44** |
| WEP | $3.03 | $3.03 | $3.03 | $2.55 |
| EEP | $2.71 | $2.68 | $3.14 | $2.94 |
| LEP | $1.96 | $1.96 | $1.96 | $1.93 |

Mean one-way km behind those dollars, EP: 21.1 / 21.0 / 22.4 / 20.6 km.

### M2 — the toll: nearest independent minus nearest incumbent (A$/t)

| District | A. Lucky Bay only | B. + bunkers | C | D |
|---|---|---|---|---|
| **EP (all)** | **$16.48** | **$8.36** | *not a number* | *not a number* |
| WEP | $29.89 | $15.75 | *not a number* | *not a number* |
| EEP | $6.84 | $1.60 | *not a number* | *not a number* |
| LEP | $14.72 | $8.61 | *not a number* | *not a number* |

C and D are not a very large toll — there is no non-Bunge receival point at any price, so
there is nothing to deliver to at any premium. Printed blank, never as infinity.

**62.8 % of WEP production (18.0 % of EP) is beyond the schedule's 250 km ceiling**, so the
WEP toll — the largest figure here — is mostly extrapolation, not citation. Over the
production the schedule can actually price: WEP $17.83, EP $11.97.

### M4 — nearest export port of any owner (A$/t)

| District | A | B | C | D |
|---|---|---|---|---|
| **EP (all)** | $10.16 | $10.16 | $13.54 | $13.54 |
| WEP | $13.47 | $13.47 | $13.93 | $13.93 |
| EEP | $9.97 | $9.97 | $19.83 | $19.83 |
| LEP | $7.85 | $7.85 | $7.90 | $7.90 |

### What the gateway is worth, as a delta (signed A$/t; + = costs more)

| Step | EP | WEP | EEP | LEP |
|---|---|---|---|---|
| **C → A**, ΔM1 — the gateway, on cartage actually paid | **−0.14** | +0.00 | **−0.43** | +0.00 |
| **C → A**, ΔM4 — the gateway, on the direct-to-port run | **−3.38** | −0.46 | **−9.86** | −0.05 |
| **A → B**, ΔM2 — reopening the bunkers, on the toll | −8.12 | −14.14 | −5.24 | −6.11 |
| **D → C**, ΔM1 — losing the seven pre-2019 sites | +0.22 | +0.48 | +0.20 | +0.03 |

The deltas are the part that survives verification: they move only 2–9 % between cost
functions (C→A ΔM1 is −$0.140 at ESCOSA marginal, −$0.136 at a full commercial card),
whereas the levels move 7x. **The D→C row is the exception and is wrong as labelled.**

### Reproduce

```
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe pipeline/r9_cartage.py
.venv/Scripts/python.exe pipeline/r9_escosa_rate_check.py      # VERDICT: PASS
```

Byte-identical across runs. Writes `docs/r9_cartage.md` and `docs/r9_cartage.json`.

### Every dependency, named

| Dependency | What it does here |
|---|---|
| ESCOSA, *Inquiry into the SA bulk grain export supply chain costs — Final Report*, 29 Jan 2019, Box 5.2, p. 91 | The rate. $0.12/t-km ≤50 km, $0.11/t-km 50–250 km. Cached at `data/raw/reference/escosa_grain_supply_chain_2019.pdf`; registered in `data/SOURCES.md` as `escosa-marginal-trucking-rate-2019` |
| `data/processed/roads.graph.json` | The router (OSM, R6) |
| `data/processed/sites.geojson` + `pipeline/manual_sites.json` | The site roster — **the weak link, see defect 5** |
| `data/processed/parcels.json` (CLUM, 5,324 cells) | Where production sits |
| `data/processed/production_districts.parquet` | District tonnes, fixed 2022/23–2025/26 means |
| `pipeline/r8_choice_geometry.py` | Graph build, snapper, network states, weights — imported, not re-implemented |
| `pipeline/r9_escosa_rate_check.py` (`BANDS`) | The rate, imported not retyped |
| A5 — road speeds | Selects the least-time path, hence its kilometres. Does not price anything. A least-**distance** variant depending on no assumed speed runs 3–4 % below throughout |
| A11 — T-Ports inland coordinates | ≤5 km tolerance on Lock and Kimba, swept (289 configs) |
| A12 — season site sets | Defines states A–D |
| A14 — PIRSA districts by LGA composition | District attribution; **also carries an unstated uniform-yield-per-cropping-hectare split, see defect 13** |
| A18 — road grain freight rate | Rewritten this run; carries the rate, the base year and the not-indexed decision |
| A1, A2, A4, A9, A15, A24 | **NOT USED.** No payload, no bay count, no capacity, no fitted parameter |
| `packages/sim/src/calibrated.json`, `engine.ts`, `matrix.json` | **NOT READ.** Verified independently by the verifier |

Cross-check: the script reproduces R0's corrected 17.5 → 17.9 min drive figures, R0's B17
snap statistics exactly, and R0's B6 independent-point mix on a kilometre metric.

---

## 3. What a grower can take from this — one sentence each

**Drafted, not cleared. Each sentence inherits every defect below.**

- **Western Eyre Peninsula:** The new port changes nothing about where you tip a load —
  your nearest receival point is the same with it as without it — and taking grain there
  instead would cost you roughly **$30 a tonne** in extra running costs, so the buyer there
  would have to beat your local price by that much before the trip was worth making.
- **Eastern Eyre Peninsula:** You are the only district the gateway reaches: for about one
  seventh of eastern production it is now the closest place to tip, worth about **43 cents a
  tonne** averaged across the district, and about **$9.86 a tonne** if you cart straight to
  a port.
- **Lower Eyre Peninsula:** Port Lincoln is closer than Lucky Bay for effectively all of
  you, so the gateway is worth **nothing** on your cartage — using it instead would cost
  about **$14.72 a tonne** extra, which is what a buyer there would have to beat.

Every one of those sentences is **half the decision**. See section 5.

---

## 4. The claim test

**Claim tested:** "up to $15 per tonne in road freight savings for grain growers from the
Eyre Peninsula", attributed to Arowana / T-Ports, September 2021.

**Verdict: NOT PUBLISHABLE — and not because the test is wrong.** The test is careful,
enumerates eight readings, steelmans first, and reaches a defensible verdict
(*supported-for-some*). It cannot be printed because **the claim is unsourced**: no entry in
`data/SOURCES.md`, no cached page, no URL, no retrieval date, no evidence for the date. The
whole finding turns on the exact wording — "up to" as a maximum, "for grain growers" as
implying peninsula-wide, "road freight savings" as the testable half — and none of that
wording is verified. This project has already withdrawn two claims for exactly this
(`gate_findings.md` item 9; `ready_to_draft.md` D2). You cannot hold Bunge's press coverage
to a stricter standard than the sentence you are about to print beside a named company.

**The reading on which the claim holds:** a grower who would otherwise truck farm-direct to
Port Lincoln or Thevenard trucks farm-direct to Lucky Bay instead. Maximum **$19.45/t**; the
tonne-weighted mean inside Lucky Bay's own geometric catchment is **$16.01/t**, and 83.1 %
of that catchment clears $15/t. On that reading the claim is not merely reached — it is
conservative, since the rate is marginal.

**The reading on which it does not:** measured against the grower's nearest Bunge receival
point — what a grower would most naturally understand by "what will the new port save me on
carting my grain" — the saving reaches $15/t at **0.0 %** of EP production, with a maximum
anywhere on the peninsula of $6.56/t.

**Is it fair to print? Not as written.** Beyond the sourcing failure, five things must be
fixed first:

1. **An undisclosed sensitivity of ~70x on the primary answer.** Lucky Bay sits 12.1 km from
   Cowell, a site `roster_audit_2026-08.md` §5.1 records taking grain in 2017/18 and 2018/19
   and which is missing from `sites.geojson` with no established closure. Adding it collapses
   Lucky Bay's catchment from 4.52 % to 0.36 % of EP production and the headline realised
   saving from $0.140/t to $0.002/t. The published envelope ($0.136–$0.188) implies ±30 %
   uncertainty on a number that is uncertain by two orders of magnitude.
2. **"Up to" is being read as an average** in the two most quotable lines — "$0.14/t, that is
   0.9 % of the claimed $15" and "$3.38/t… 23 % of the claimed $15". Expressing a mean as a
   fraction of a claimed maximum is the misreading the script's own docstring forbids. A
   reader takes away "inflated 100x", which is not the finding.
3. **The 2021-contemporaneous scoping figure is more than double the one published.** At
   state B — the network with the bunkers, the one that existed nearest the claim date — the
   T-Ports catchment is 10.5 % of EP production, not 4.5 %. The 4.5 % is what carries the
   sentence about the honest shape of the finding.
4. **The 250 km ceiling caveat is dropped entirely from the claim test** while it asserts
   every figure is priced at ESCOSA's published schedule. 75.7 % of EP production is beyond
   250 km from Thevenard, so reading 3 and reading 8 are almost wholly extrapolation.
5. **No right of reply.** `docs/right_of_reply_letters.md` has no letter to Arowana, and none
   of the ten questions to T-Ports mentions $15/t. The test's own fairness note says the
   question must be put to them directly. It has not been.

Two counterfactuals nobody advanced should also come out or be labelled as such: "if every EP
grower delivered to Lucky Bay, freight kilometres would rise 37.1 km/t", and the site-by-site
list headed by Penong at −$44.58/t (405 km further). No one has proposed carting Penong grain
to Lucky Bay, and both lines will be quoted out of their qualifier.

**What survives and is rate-robust:** on the nearest-silo reading the maximum saved distance
anywhere on EP is 59.7 km, worth $6.56/t at ESCOSA one-way, $13.11/t doubled, and $14.50/t at
the most claimant-favourable rate in this repo. Under $15 at every published rate — but state
the margin, not "there is no farm on the Eyre Peninsula where it reaches $15", which reads as
a fact about the peninsula when it is a fact about the schedule.

---

## 5. What this does NOT show

1. **THERE IS NO PRICE DATA, AND PRICE IS THE OTHER HALF OF THE DECISION.** Growers deliver
   where **price minus cartage** is best. This project holds 13 days of off-season cash bids
   and nothing else. A toll of $16.48/t says the independent must be worth $16.48/t more at
   the weighbridge before the load moves; it does **not** say whether it was. Nothing here is
   a grower benefit, a grower loss, or a total. If a figure from this work is ever quoted as
   "what the gateway is worth to growers" without that sentence attached, it has been
   misquoted.
2. **These are marginal dollars — a floor, not a price.** ESCOSA's rate is the additional cost
   of travelling further once the truck is on the road. Truck ownership, loading, queueing,
   turnaround and driver time are outside it by design, and ESCOSA says so.
3. **2018–19 dollars, published unindexed**, on A18's recorded decision. Seven years old.
4. **The empty return leg is unresolved and worth a factor of two.** Established: ESCOSA
   applies the rate one-way. Not established: whether AEGIC's underlying cost line was built
   on a round-trip cycle. Settling it needs AEGIC Oct 2018, Note 2c to Figure 4, p. 18 — not
   cached in this repo.
5. **The 50–250 km band, which carries almost all of these dollars, is not itself published.**
   ESCOSA fn 289 traces the ≤50 km rate to a public AEGIC document and the 50–250 km rate to
   unpublished "AEGIC advice" to the Commission.
6. **SA-wide, not EP.** ESCOSA's case study is the Gladstone catchment, 16–53 km hauls. No
   EP-specific $/t-km schedule exists. EP arguments cut both ways and neither is quantified.
7. **The catchment is geometric, not observed.** No site-level receival series exists in this
   repo at any granularity (`gate_findings.md` §3). "Nearest" is also not "available": a site
   that does not segregate the grade being carted still counts as a choice here.
8. **This does not reopen the 90-minute threshold.** A cost rate cannot justify a distance
   threshold, whoever published it.

---

## 6. Outstanding defects the verifiers raised that are NOT fixed

Roughly by severity. 1–3 and 5–6 block (a); 7–11 block (b).

1. **A marginal rate is used to produce levels labelled as prices growers pay.** ESCOSA's
   rate has no intercept and cannot produce a level. Under the full commercial card the same
   page cites (ACH 2026: $16.50/t to 10 km, then $0.10/t-km) the identical 21.1 km hauls cost
   **$17.67/t, not $2.52/t — a factor of 7.0**; the 91.8 km port run costs $24.68/t, not
   $10.16/t. `docs/r9_cartage.md:103` heads the table "the bill growers actually pay". Fix:
   demote M1 and M4 to differences, or re-label them as marginal increments, never bills.
2. **The interpretation note is calibrated at the wrong haul length and mixes base years.**
   `r9_cartage.md:20` and `:344` bracket the rate at EP's ~144 km site→port haul ("roughly
   half a delivered cartage price"). M1's mean haul is 21.1 km, where the marginal rate is
   **14 %** of a delivered price, not ~50 %. The same bracket compares 2018–19 A$ against two
   2026-nominal comparators, with no base-year disclosure anywhere in the published page.
3. **A published "upper bound" is false.** `r9_cartage.md:225`, D→C = +$0.22/t, "READ IT AS AN
   UPPER BOUND". Restoring Cowell and Mangalo at town coordinates gives **+$0.452/t** (Cowell
   alone +$0.403, Mangalo alone +$0.382; +$0.412 to +$0.470 under a 10 km × 8-bearing sweep).
   Applying both known corrections at once still gives +$0.361. The true bracket is roughly
   +$0.12 to +$0.47 — a factor of 4 on a row printed as a single bounded number, and the same
   paragraph names the factor that breaks it.
4. **The primary measure is, numerically, the measure the page says it rejected.** M2 equals
   "cartage to the nearest independent point" minus a near-constant: $16.48 = $19.14 − $2.66
   exactly. corr = 0.9896 (A), 0.9803 (B); sd $11.58 vs $1.71; M2 is invariant to every
   incumbent-roster repair tested. Visible rather than hidden — the two-halves table is
   published — but reason (3) for choosing M2 as primary is not a real distinction.
   *Related:* the toll's band selection is not ESCOSA's (ESCOSA picks the band from the
   increment; R9 prices two whole hauls and subtracts). Worth ~1 %, conservative, but the
   claim to apply the schedule exactly as ESCOSA does is not exact for the primary measure.
5. **The site roster is known incomplete and nothing here is protected from it.** Tooligie,
   Cowell and Mangalo are absent from `sites.geojson`; Cungena's `closed_2019` tag is
   contradicted (`roster_audit_2026-08.md` §5). Every measure here is anchored on the
   incumbent side. Directions are known and asymmetric — M1 levels are upper bounds, the toll
   a lower bound, M3's catchment share an upper bound — and the contamination is uneven across
   states, so the deltas carry it. Fixing it entangles with A4 and hence the calibration.
   *Mitigating:* the C→A headline (−$0.139) is invariant to every roster repair the verifier
   could construct.
6. **The season labels are attributions and the load-bearing one is unsourced.** Calling state
   A "2025/26" rests on both bunkers being closed that season. There is no `tports.com/harvest`
   entry in `SOURCES.md`, no cached page, no retrieval date, and for **Kimba no closure
   evidence at all** — only a hand-typed note on Lock from the same off-season live read that
   `roster_audit` §1 identifies as the root cause of four wrongly closed Bunge sites. Read A
   and B as "Lucky Bay alone" and "Lucky Bay plus both bunkers".
7. **The claim under test has no source.** Blocking on its own. See section 4.
8. **The company's name is misspelled** ("Arrowana") in the fair-dealing section itself.
9. **The ~70x roster sensitivity on the claim test's primary answer** (Cowell), undisclosed,
   while a ±30 % coordinate envelope is published as if it were the uncertainty. Related: the
   best cell's description — "the cell containing Lucky Bay itself, 0.8 km from the port" — is
   an undriven-snap artefact; the centroid is 5.38 km from the registered coordinate and snaps
   4.86 km to the graph. Correcting it costs ~$0.55/t of the $19.45, so the finding holds and
   the sentence does not.
10. **Reading 5 is described as "the state that actually existed on the date of the claim" and
    is not.** Its incumbent side is the 2026 roster, and `manual_sites.json`'s own note says
    the Kimba bunker was "Built for 2021 harvest" — i.e. Nov/Dec 2021, after a September 2021
    release.
11. **The rate concession in the fairness note is arithmetically wrong.** "A promoter quoting a
    full delivered rate would get roughly double our dollars off identical kilometres" — on a
    *difference* of two one-way hauls at the same tonnage and load count, ACH's $16.50 fixed
    charge cancels, leaving a marginal $0.10/t-km, **below** ESCOSA's $0.11. Driver time is the
    genuine residual, and that is a much narrower concession than the one made.
12. **Lucky Bay's coordinate is registered in no assumption.** It is a town/hamlet OSM node —
    the precision class A11 gives Lock and Kimba a ≤5 km tolerance for. It is swept here (17
    configs, of which only 9 are distinct: bearings 45/90/135 point into Spencer Gulf and
    re-snap to the same node) but the `ASSUMPTIONS.md` edit was not made.
13. **A14's within-district allocation is unstated on the page.** District tonnes are split
    proportional to CLUM cropping hectares, i.e. uniform yield across cells. The carried-
    assumptions entry covers only "district boundaries approximated by LGA composition".
14. **`r8_choice_geometry.py`'s own A11 sweep locks the two bunker displacement magnitudes
    together** (129 configs, bearings only) while its method text claims true extremes over the
    grid. R9's sweep varies both independently (289 configs). R8's text defect stands.
15. **The $60–75/t whole-of-chain anchor A18 previously leaned on could not be re-verified**
    from the cached PDF (Figures 4.3–4.5 are images with no extractable text). Demoted to
    superseded in A18; if any other document cites it to ESCOSA 2019 it needs the same check.
16. **Comparator documents are not cached.** ACH and SAGIT are registered by URL and retrieval
    date only. If either page changes, $29.90/t and $35.00/t become unreproducible.
17. **The cached ESCOSA PDF is not listed in `data/raw/MANIFEST.sha256`** (sha256
    `f901b52cba57cddac955a3448767c3ebe1e99656a11775ffd0bc348bf027354c`, recorded in the new
    `SOURCES.md` entry instead). Someone must decide whether the manifest is regenerated.
18. **The AEGIC non-read.** Every "no newer edition" conclusion rests on search results plus
    ESCOSA's footnotes; `aegic.org.au` returned 404 to every automated fetch. Someone with
    browser access should confirm, and read Note 2c to Figure 4 p. 18 while there.

### Process

Nothing committed; working tree only. New files: `pipeline/r9_cartage.py`,
`pipeline/r9_escosa_rate_check.py`, `pipeline/r10_arowana_claim.py`,
`pipeline/r10b_arowana_detail.py`, `pipeline/r10c_export_select_check.py`,
`pipeline/r10d_lucky_bay_sweep.py`, `docs/r9_cartage.md`, `docs/r9_cartage.json`,
`docs/r10_arowana_claim.json`, and this file. Modified: `data/ASSUMPTIONS.md` (A18
rewritten), `data/SOURCES.md` (three new entries).

**Correction to the run report:** it states that `r8_choice_geometry.py` and
`r8a_coord_sensitivity.py` are untracked. Both are tracked — `git ls-files pipeline/` lists
them. Only the r9 and r10 scripts are untracked. They should be committed before review, so a
reviewer can confirm by diff what changed.
