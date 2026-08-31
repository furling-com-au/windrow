# Analysis plan — "One gateway": competitive choice on the Eyre Peninsula

Status: draft plan, 2026-08-31. Not yet commissioned. Companion to
`stakeholder_review.md`; this one names a single publishable piece, the model runs
behind it, and what we must not claim.

## 1. Why now

Five dated facts create the window:

| Date | Fact |
|---|---|
| 2021 | ACCC exempted Viterra's Port Adelaide terminals from parts of the Bulk Wheat Code but **refused** exemption for Port Lincoln and Thevenard — the regulator has already found EP ports lack competitive constraint |
| Oct–Dec 2024 | Viterra agreed to buy five Grainflow sites + a mobile ship loader; ACCC informal review opened 10 Oct; opposition from T-Ports, GPSA (grower survey) and EP growers; **withdrawn 16 Dec** rather than face a decision |
| Aug 2025 | Bunge completed the Viterra acquisition; Viterra Operations Pty Ltd renamed **Bunge Operations Pty Ltd** |
| Dec 2025 → now | **T-Ports is for sale** (~$250m, Nash Advisory, packaged with Australian Grain Export). Tipped buyers include GrainCorp, CBH, Qube, Louis Dreyfus — and Bunge. Unsold at last report |
| 2024 → 2026 | Wheat Port Code sunsetted on ACCC advice; revised exposure draft out for consultation; grower groups split |

The 2024 fight was argued with a survey and opinion letters. The ACCC's actual test is
quantitative — catchment substitution. Nobody on the grower/competition side has that
capacity. That is the gap this piece fills.

## 2. What the repo already has that we had not noticed

**Ownership and closure history are already tagged in `data/processed/sites.geojson`.**
32 features:

| Operator | Status | n | Sites |
|---|---|---|---|
| Bunge (ex-Viterra) | active 2025/26 | 18 | incl. Port Lincoln, Thevenard |
| Bunge (ex-Viterra) | dormant | 5 | Penong, Nunjikompita, Darke Peak, Buckleboo, Elliston |
| ex-Viterra | **closed 2019** | 6 | Minnipa, Kyancutta, Cungena (WEP); Waddikee, Kielpa, **Wharminda** (EEP) |
| T-Ports | active | 1 | Lucky Bay (port, 384 kt) |
| T-Ports | closed 2025/26 season | 2 | Lock bunker (140 kt), Kimba bunker (150 kt) |

The competition analysis is therefore directly computable, not a data-collection project.

**Two observed contractions, both already in the data, no counterfactual required:**

1. **2019.** Six receival sites closed — the same year grain trains ceased (May 2019).
   One of them is **Wharminda**, and Wharminda Road is named in the reporting as one of
   the roads that absorbed the extra truck traffic after the rail closure. The site shut
   and the road took the trucks: a directly citable pairing.
2. **2025/26.** The only two places T-Ports competed with Bunge *inland* are Lock and
   Kimba — Bunge operates active sites at both towns — and both T-Ports bunkers are closed
   for the season (published, tports.com/harvest; A15). They ran in 2023/24 (0.511 Mt
   T-Ports intake). That is 290 kt of independent inland receival capacity, roughly two to
   four Bunge upcountry sites' worth, out of the market.

Net: EP has gone from ~30 receival points to 19 operating ones, and from two independent
inland options to effectively one operator plus a single competing port.

**This reframes the piece.** Lead with what has already happened to competitive choice on
the peninsula. Use the T-Ports sale as the forward-looking section, not the headline.
Observed beats hypothetical in front of a regulator and in front of an editor.

## 3. The claims ladder

Everything in the piece sits in one of three tiers, and the tier is stated on the page.
This is the whole defence: an opposing expert will attack the dynamic layer, so the
headline must not live there.

**Tier 1 — published, no model.** Site network and ownership; the bunker closures; ten
seasons of weekly receivals (Wayback-recovered, digit-identical to independent
re-publication); AIS vessel calls (within 1–2/month of Flinders' official Dry Bulk
counts); the ACCC and merger record above. Unattackable.

**Tier 2 — geometry. Roads and site locations only; no fitted parameter. THE HEADLINE.**
For each production cell, drive time to the nearest Bunge receival point vs the nearest
*independently owned* one. Depends on `roads.graph.json`, `sites.geojson`,
`production_districts.parquet` — and on none of A1–A4, A24, or any calibrated knob. An
opposing expert can dispute our queue model; they cannot dispute how far Wharminda is
from an alternative.

**Tier 3 — dynamic, reported as ranges, never as point estimates.** Absorption capacity,
truck-km, corridor loading, queues. Every figure ranged across the A24 identification
ridge and labelled indicative.

## 4. Model runs

Ordered by execution. R5 is a go/no-go gate — run it first.

**R5 — Retrospective validation (do this first, ~1–1.5 days). The credibility anchor.**
Two closures already happened, and we hold ten seasons of weekly receivals (2016/17–2025/26)
that straddle both:

- **2019 closure of six sites** — three pre-closure seasons and six after. Feed the model
  the pre-2019 network, close the six, and check the simulated redistribution against
  observed receivals at the surviving neighbours. This is a genuine out-of-sample test of
  exactly the mechanism the piece rests on: where does grain go when a receival point
  disappears.
- **2023/24 → 2025/26 bunker closure** — same test, smaller and more recent, with the A15
  caveat on 2024/25.

If the model reproduces both, the counterfactual machinery has a published track record
and Tier 3 is publishable — and that track record is itself worth a paragraph in the
piece. If it does not, say so, cut Tier 3 to a sensitivity note, and publish on Tiers 1–2
alone. **The piece survives either way**, which is why this is the gate rather than a
risk.

**R0 — Ownership choice-set geometry (~1 day). No sim.**
Per production cell, sorted drive times to all operating sites tagged by operator. Outputs:
(a) tonne-weighted share of EP production whose nearest independent receival point is
>30 / >60 / >90 min beyond its nearest Bunge point; (b) a single-operator catchment map;
(c) the same computed at three network states — pre-2019 (30 points), 2023/24 (bunkers
open), 2025/26 (bunkers closed). The trajectory across those three *is* the headline
number, and none of it depends on a fitted parameter.

**R1 — Gateway removal, ranged over A24 (~1 day).**
`luckyBayBias → 0` (`engine.ts:866` already gates T-Ports attractiveness on this) swept
across the retention/LB ridge at `retentionShare` ∈ {0.055, 0.069, 0.100, 0.143} with the
paired LB value from `docs/calibration_search.json`. Outputs: where the 0.42–0.51 Mt goes,
which Bunge sites hit the hard capacity ceiling (#29), resulting queue and truck-km.
**Report as a range.** A24 states these two knobs are not separately identified and that
the fit buys part of its match with T-Ports throughput that nothing in the calibration
data constrains — publishing a point estimate here would be the single most attackable
thing we could do.

**R2 — The relief-valve test (~0.5 day once R1 exists). Likely the strongest dynamic finding.**
Bumper (+30%) × T-Ports removed. The existing bumper run already shows Bunge sites capping
out and +0.14 Mt spilling *to* T-Ports (0.42 → 0.56 Mt) — so T-Ports is not only a price
competitor, it is the network's surge capacity. Remove the valve in the same year and
report tonnes with nowhere to go and the extra distance they travel.

**R3 — Post-merger rationalisation (~1 day). Needs a new `siteClosures: string[]` param.**
Close the N most marginal Bunge upcountry sites (rank by simulated throughput per unit
capacity). Anchored, not invented: the same network has done this twice — six sites closed
in 2019, five more sit dormant — so N and the selection rule can be calibrated against
which sites actually got closed rather than assumed. Frame strictly as "what
rationalisation of this shape would do", never as a prediction.

**R4 — Corridor freight delta (~0.5 day).**
Per-corridor truck-km for baseline / T-Ports removed / rationalised, as a CSV. Feeds the
roads angle: rail ceased May 2019, ~64,000 60-tonne truck movements a year through Port
Lincoln, ~$25m of federal road money against Aurizon and Viterra's $220m ask to reopen
Port Lincoln–Cummins, Wudinna and Kimba, and an RAA survey of 1,300+ EP road users with
road maintenance the top concern for 76%. Every party quotes a headline truck number;
none publishes corridor-level movements.

## 5. Data gaps to close before publishing

- **A15**: the 2024/25 bunker closure is *assumed*, not verified. One email to T-Ports —
  who are also a right-of-reply contact.
- **A24**: published T-Ports intake, or an ABARES/PIRSA on-farm-use estimate for EP,
  collapses the range to a point. One email each. Worth trying; publish ranged if refused.
- **A4**: all 23 upcountry capacities are estimated. R2's capacity findings inherit this
  and must say so on the page.

## 6. What we must not claim

- Absolute queue or turnaround times (A2 — the biggest data gap in the project).
- That the Lock and Kimba closures were strategic. A drought year and bunker economics
  are entirely plausible explanations and the piece should **say so explicitly**. The
  claim is about the *effect on grower choice*, which is measurable, not about intent,
  which is not.
- That any particular merger will happen.
- Any farm-gate price effect. 13 days of off-season cash-bid capture is nowhere near
  enough; the series is corroboration for later, not evidence now.
- Any ranking of individual site performance.

## 7. Effort and schedule

~10 working days.

| Days | Work |
|---|---|
| 1–2 | R5 validation + R0 geometry. **Go/no-go gate at end of day 2.** |
| 3–5 | R1, R2, R3, R4 |
| 6–8 | Writing, maps, charts, provenance appendix |
| 9–10 | Right-of-reply round, fact-check, publish |

## 8. Right of reply — which is also the customer discovery

Send the draft with a five-working-day deadline to: Bunge (media), T-Ports (CEO Nathan
Kent) and Nash Advisory, Grain Producers SA, DIT and RDA Eyre Peninsula, and the ACCC
mergers team as a courtesy. This is standard practice for a piece naming a company, and it
puts the model in front of every candidate customer with a professional reason to read it
and reply. If the answer to "is there a customer" is yes, it arrives in that inbox round.

## 9. Distribution

Grain Central and Stock Journal cover this beat closely; InDaily ran the 2024 backlash
piece; ABC Rural covered the rail campaign. Time publication to the Wheat Port Code
consultation window and the live T-Ports sale.
