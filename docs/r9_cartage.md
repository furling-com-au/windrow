# R9 - What the independent gateway is worth to growers, in cartage dollars

Generated 2026-08-31 by `pipeline/r9_cartage.py`.

**Tier 2 (geometry over road distances and site locations) x Tier 1 (a published rate schedule). No simulation, no fitted parameter, no calibrated knob. Nothing here reads `packages/sim/src/calibrated.json`, `engine.ts` or `matrix.json`.**

**Reproduce**

```
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe pipeline/r9_cartage.py
.venv/Scripts/python.exe pipeline/r9_escosa_rate_check.py   # VERDICT: PASS
```

---

## Read this first

1. **CARTAGE IS HALF OF A DELIVERY DECISION. Growers deliver where PRICE MINUS CARTAGE is best. This project has no price data - 13 days of off-season cash bids and nothing else (data/SOURCES.md, operator-cash-prices-api). Every figure on this page is one side of that ledger. A toll of $X/t says the independent must be worth $X/t more at the weighbridge before the load moves; it does NOT say whether it was, and nothing here is a total grower benefit or loss.**

2. **THESE ARE MARGINAL DOLLARS AND THEREFORE A FLOOR. ESCOSA's rate is explicitly the additional cost of travelling further once the truck is on the road. Truck ownership, loading, queueing, turnaround and driver time are outside it BY DESIGN, and ESCOSA says so. The size of that gap depends on haul length, and this note must be read at the haul length of the measure it governs. At EP's ~144 km site-to-port haul the same rate gives $15.84/t against a 2026 commercial rate card's $29.90/t and a 2026 SA budget guide's $35.00/t - about half a delivered price. But M1's mean haul is **21.1 km, not 144 km**, and on a haul that short the excluded fixed costs dominate: there the marginal rate understates a delivered price by roughly **7x, not 2x**. Calibrating this note at 144 km against a 21 km measure understated the shortfall by about 3.5x and has been corrected. A grower reading '$X/t more' here is reading the extra fuel-and-running cost of the extra kilometres, not the extra cost of running the extra trips.**

3. **Base year.** The rate is 2018-19 A$ and is published here unindexed, on A18's recorded decision. Seven years old. This must sit next to every figure, not in a footnote.

---

## The answer, in three lines

1. **In cartage that growers actually pay, the gateway is worth very little, and that is the finding.** Adding the peninsula's one independent receival point to the network cuts the tonne-weighted EP cartage bill by **$0.14/t** ($2.66 -> $2.52), because only **4.5 %** of EP production has it as the closest place to tip a load. In EEP, where that share is 13.8 %, the cut is $0.43/t. In WEP and LEP it is zero to the cent.

2. **What it is worth is an option, and the option has a price.** To take a load to the independent point instead of the nearest Bunge site costs a grower **$16.48/t** on average across EP - **$29.89/t** in WEP, **$6.84/t** in EEP, **$14.72/t** in LEP. That is the price premium the independent has to beat, per tonne, before the load is worth moving. With the two inland bunkers open it is **$8.36/t** EP-wide (WEP $15.75, EEP $1.60, LEP $8.61). With no independent point at all it is not a larger number - it is **not a number**, because there is nothing to deliver to at any premium. **The WEP figure is mostly not a citation**: 62.8 % of WEP production is further from Lucky Bay than the published schedule's 250 km ceiling, so above that the rate is extrapolated. Over the WEP production the schedule can actually price, the toll is $17.83/t.

3. **Where it does show up is the direct-to-port run.** For a grower carting straight to an export port, Lucky Bay takes EEP from $19.83/t to $9.97/t - a 9.86 A$/t difference, the largest single figure on this page, and the one place where the gateway changes a real cartage bill rather than an option price.

All figures marginal, one-way loaded, 2018-19 A$, unindexed. **None of them is a grower benefit**: this project has no price data, and cartage is one side of a two-sided decision. Read the three notes above before quoting any of it.

---

## The measure, and why

PRIMARY: M2, the TOLL - cartage to the nearest independent receival point minus cartage to the nearest incumbent one, A$/t, tonne-weighted by district. Chosen for three reasons. (1) It is the only one of the four measures that is a grower DECISION variable: it converts directly into the price premium, per tonne, that the independent has to beat before a load is worth moving, which is the same unit a grower reads a basis quote in. (2) It is the quantity the network change actually moved. At state C the toll is not a large number, it is NOT A NUMBER - there is no non-Bunge receival point on the peninsula at any price. State A gives it a value; state B roughly halves it. (3) The obvious alternative, 'cartage to the nearest independent point', is not a cost anybody pays: it is a distance to a place most growers never go. REPORTED BESIDE IT, AND NOT OPTIONAL: M1, the bill actually paid (cartage to the cheapest point of any owner), because M1 is what moves growers' real costs and it BARELY MOVES between states - that is a finding, not an omission, and a reader given M2 alone would wrongly infer that every grower pays the toll. M3, the share of production for which the independent point genuinely is the cheapest or near-cheapest destination, because that share is what M1's movement is made of. M4, direct-to-port cartage, because that is the delivery pattern in which Lucky Bay's position does the most work and it is the task's 'nearest export-capable destination' measure made honest.

### Definitions

| | Measure | Definition | Defined at |
|---|---|---|---|
| **M1** | the bill | cartage to the fewest-kilometre receival point of **any owner**, A$/t | all four states |
| **M2** | **the toll (primary)** | cartage to the nearest **independent** point minus cartage to the nearest **incumbent** point, A$/t | A and B only |
| **M3** | the catchment | tonne share whose toll is <= $0 / $1 / $2 / $5 per tonne | A and B only |
| **M4** | the port run | cartage to the nearest **export port** of any owner, A$/t | all four states |

### Measures considered and not made the headline

- **cartage to the nearest INDEPENDENT point, published bare** - Rejected as a headline. It is a distance to a place most EP growers have never delivered to, priced. It is reported here as an input to the toll and as a level (so a reader can see what using the gateway costs outright) but it is not 'what the gateway is worth', and quoting it alone would read as a cost growers bear.
- **cartage to the nearest EXPORT-CAPABLE destination, over all points** - Rejected as it collapses onto M1 exactly. Every receival point on this roster feeds an export chain: a Bunge upcountry silo feeds Port Lincoln and Thevenard, a T-Ports bunker feeds Lucky Bay. Making the test 'export-capable' therefore excludes nothing and adds no information. What does not collapse is DIRECT-TO-PORT delivery, which is M4.
- **the difference in cartage for the subset that uses the independent point** - Not rejected - it is M3, and it is published. But it cannot be the headline on its own: it is a saving conditional on a delivery choice this project cannot observe. There is no site-level receival series in this repo at any granularity (docs/gate_findings.md section 3), so who actually delivered where is not known and M3's catchment is a geometric catchment, not an observed one.
- **total cartage dollars saved across the peninsula** - Rejected. Multiplying $/t by district tonnage produces a large headline number that implies a measured aggregate benefit. It would be a product of two modelled quantities (the cell weighting, A14 x CLUM, and a geometric delivery choice) priced at a marginal rate that is explicitly not a full cartage price, with no price data on the other side of the ledger. The per-tonne figure is what a grower can check against their own farm; the aggregate is what a press release would quote.

### The structural point about Lucky Bay

Lucky Bay is a PORT, not an upcountry silo. T-Ports' model had growers delivering either to the Lock and Kimba bunkers or direct to Lucky Bay, and in every case the grower's truck does one loaded one-way run from farm to a place where it tips and is paid, and stops. Whatever moves the grain onward - T-Ports shuttling bunker grain to Lucky Bay, Bunge line-hauling silo grain to Port Lincoln or Thevenard - is the OPERATOR's cost and is outside every number here. That is what makes it coherent to put a port and a silo in the same nearest-destination comparison. It does NOT make them commercially equivalent: a port and an upcountry silo differ in segregations, receival standards, opening hours, queueing and the contract on offer, none of which this page can see. And it is why state A's toll is as large as it is - with both bunkers shut, the only non-Bunge place to tip a load is a port on the far side of the peninsula.

### Choosing the destination

ESCOSA's bands are FLAT and selected by the whole distance, so the priced cost is not monotone in distance across the 50 km edge: 49 km prices at $5.88 and 51 km at $5.61. The destination here is chosen by MINIMUM KILOMETRES and then priced, because that is what a truck does; choosing by minimum dollars would let a pricing convention pick a farther silo. The share of production where the two choices differ, and what it is worth, is measured below rather than assumed away.

---

## The rate

ESCOSA, Inquiry into the South Australian bulk grain export supply chain costs - Final Report, 29 January 2019, Box 5.2, p. 91: "Only the marginal freight cost has been used, $0.12 ($/tonne-km) for up to 50 kilometres and $0.11 ($/tonne-km) for 50 to 250 kilometres."

Applied as: **one-way loaded kilometres; band selected by the whole distance; no cumulative tiering; empty return not added**. Base year **2018-19 A$ (nominal, deliberately not indexed - A18)**. Verified by `.venv/Scripts/python.exe pipeline/r9_escosa_rate_check.py`.

- ESCOSA footnote 289 traces the <=50 km $0.12 to a public AEGIC document but the 50-250 km $0.11 to unpublished 'AEGIC advice'. Most EP hauls to an independent point fall in the second band, so the weaker-provenance rate carries most of the dollars on this page.
- The schedule is South Australia-wide and the case study behind it is the upper Central region (Gladstone catchment, 16-53 km hauls), not the Eyre Peninsula. No EP-specific $/t-km schedule was found. EP arguments cut both ways and neither is quantified.
- THE EMPTY RETURN LEG IS UNRESOLVED AND IS WORTH A FACTOR OF TWO. Established: ESCOSA APPLIES the rate to a one-way distance - all four of its own published results reproduce on that reading and on no other. Not established: whether AEGIC's underlying cost line was itself built on a round-trip cycle. The report is silent. The distance is NOT doubled here, because doubling would double-count if the cost line already embeds the return. The doubled figures are reported once, as a labelled UPPER BOUND on the open question, and are not a published result. Settling it needs AEGIC, Australia's grain supply chains, October 2018, Note 2c to Figure 4, p. 18, which is not cached in this repo.

---

## The four network states

| | State | Receival points | of which independent | Ports | Attribution |
|---|---|---|---|---|---|
| **A** | Lucky Bay only | 23 | 1 | 3 | 2025/26 as it stands (attribution UNSOURCED - see caveat) |
| **B** | Lucky Bay + Lock + Kimba bunkers | 25 | 3 | 3 | the 2023/24 network; equivalently, the bunkers reopened |
| **C** | no independent point at all | 22 | 0 | 2 | counterfactual - Lucky Bay unavailable |
| **D** | pre-2019 | 29 | 0 | 2 | before T-Ports existed and before the June 2019 closures |

**THE SEASON LABELS ARE ATTRIBUTIONS AND ONE OF THEM IS UNSOURCED. The four states are defined by their CONTENT - which points exist - and every number here follows from that content alone. The attribution of state A to 2025/26 rests on the claim that both T-Ports bunkers were closed for that season, and that claim has no source in this repo: there is no tports.com/harvest entry in data/SOURCES.md, no cached page under data/raw/, no retrieval date, and for KIMBA no closure evidence at all (its status field is set with a notes field reading only 'Built for 2021 harvest'). The only record is a hand-typed note on LOCK in pipeline/manual_sites.json citing a live read of tports.com/harvest on 2026-08-19 - the same off-season live read that docs/roster_audit_2026-08.md section 1 identifies as the root cause of four wrongly closed Bunge sites. Read A and B as 'Lucky Bay alone' and 'Lucky Bay plus both bunkers'. Do not publish either season label until the page is archived and registered.**

### The one structural fact that shapes every table below

THE TWO INLAND BUNKERS ARE NOT IN NEW COUNTRY; THEY ARE BESIDE BUNGE'S OWN SITES. The T-Ports Lock bunker is 0.91 km from Bunge's Lock silo and the T-Ports Kimba bunker is 2.31 km from Bunge's Kimba silo. That single fact explains the shape of every table below. Reopening them moves the BILL by about a cent a tonne, because no grower has to drive anywhere new; it roughly halves the TOLL, because for a large part of the peninsula the second buyer is standing in the yard the grower was already driving to. The bunkers were never a cartage improvement. They were a competition one, at locations that had already been chosen. Lucky Bay is the opposite case: 49.93 km from the nearest active Bunge site, a genuinely new place to tip a load, and a port.

| T-Ports point | nearest active Bunge site | straight-line km |
|---|---|---|
| Lock (T-Ports bunker) | Lock | 0.91 km |
| Kimba (T-Ports bunker) | Kimba | 2.31 km |
| Lucky Bay (T-Ports port) | Arno Bay | 49.93 km |

---

## M1 - marginal cartage to the nearest receival point of any owner, A$/t

> **Not "the bill growers actually pay."** An earlier revision of this page carried that
> heading and it was wrong. These are ESCOSA *marginal* dollars — the extra running cost of
> extra kilometres — and at this measure's own mean haul of 21.1 km they understate a
> delivered cartage price by roughly 7x, because on a short haul the fixed costs the
> marginal rate excludes (loading, turnaround, waiting, driver time) dominate. Read the
> LEVELS in this table as a floor of unknown depth. Read the DELTAS between states as the
> result: they move only 2-9 % across cost functions, whereas the levels move 7x.

Tonne-weighted mean marginal cartage to the nearest receival point of any owner. This is the measure that is defined at **all four** states, including pre-2019 where R0's ownership ladder is undefined.

| District | A. Lucky Bay only | B. Lucky Bay + Lock + Kimba bunkers | C. no independent point at all | D. pre-2019 |
|---|---|---|---|---|
| **EP (all)** | $2.52 | $2.51 | $2.66 | $2.44 |
| WEP (Western Eyre Peninsula) | $3.03 | $3.03 | $3.03 | $2.55 |
| EEP (Eastern Eyre Peninsula) | $2.71 | $2.68 | $3.14 | $2.94 |
| LEP (Lower Eyre Peninsula) | $1.96 | $1.96 | $1.96 | $1.93 |

Mean one-way kilometres behind those dollars:

| District | A. Lucky Bay only | B. Lucky Bay + Lock + Kimba bunkers | C. no independent point at all | D. pre-2019 |
|---|---|---|---|---|
| **EP (all)** | 21.1 km | 21.0 km | 22.4 km | 20.6 km |
| WEP | 25.5 km | 25.5 km | 25.5 km | 21.4 km |
| EEP | 22.7 km | 22.4 km | 26.9 km | 25.2 km |
| LEP | 16.4 km | 16.4 km | 16.4 km | 16.1 km |

---

## M2 - the toll: what it costs to use the independent option, A$/t

Cartage to the nearest independent receival point **minus** cartage to the nearest incumbent one. Equivalently: the price premium, per tonne, the independent has to beat before the load is worth moving. **Undefined at C and D** - there is no non-Bunge receival point in either state, so there is no alternative to price at any premium.

| District | A. Lucky Bay only | B. bunkers reopened | B - A |
|---|---|---|---|
| **EP (all)** | $16.48 | $8.36 | -8.12 |
| WEP (Western Eyre Peninsula) | $29.89 | $15.75 | -14.14 |
| EEP (Eastern Eyre Peninsula) | $6.84 | $1.60 | -5.24 |
| LEP (Lower Eyre Peninsula) | $14.72 | $8.61 | -6.11 |

**How much of that is actually priced by the published schedule.** ESCOSA's schedule stops at 250 km. Where the haul to the independent point is longer, the $0.11/t-km applied above the ceiling is an **extrapolation, not a citation** (A18). The right-hand columns give the toll over the smaller population whose independent haul is inside the schedule - a different population, not a corrected number.

| District | A: production over the 250 km ceiling | A: toll within the schedule | B: over the ceiling | B: toll within the schedule |
|---|---|---|---|---|
| **EP (all)** | 18.0 % | $11.97 | 6.7 % | $6.71 |
| WEP | 62.8 % | $17.83 | 23.3 % | $11.00 |
| EEP | 0.0 % | $6.84 | 0.0 % | $1.60 |
| LEP | 0.0 % | $14.72 | 0.0 % | $8.61 |

Coordinate envelopes on those tolls (site displaced <=5 km on eight bearings, re-snapped and re-routed):

| District | A, over the Lucky Bay coordinate | B, over the A11 Lock/Kimba tolerance |
|---|---|---|
| **EP (all)** | $15.75 - $16.57 | $8.34 - $8.87 |
| WEP | $29.16 - $29.98 | $15.42 - $16.63 |
| EEP | $6.11 - $6.92 | $1.54 - $2.05 |
| LEP | $13.98 - $14.81 | $8.31 - $9.49 |

**STATE A RESTS ENTIRELY ON ONE COORDINATE. With both bunkers shut, Lucky Bay is the only independent receival point on the peninsula, so the toll at state A is a pure function of the road distance to a single point. That point is registered in sites.geojson at a TOWN/HAMLET node ('Lucky Bay, South Australia' hamlet node, facility adjoins hamlet) - the same precision class A11 gives Lock and Kimba a <=5 km tolerance for, and it is registered in no assumption. It is swept here rather than asserted: the site is displaced 0 / 2.5 / 5 km on eight bearings, RE-SNAPPED to the road graph and RE-ROUTED with a fresh Dijkstra, and the envelope is published beside every state-A figure.**

### The toll's two halves, so a reader can see where it comes from

| District | nearest incumbent, A$/t | nearest independent, A$/t | independent haul, km | = toll |
|---|---|---|---|---|
| *A. Lucky Bay only* | | | | |
| **EP (all)** | $2.66 | $19.14 | 174 km | $16.48 |
| WEP | $3.03 | $32.93 | 299 km | $29.89 |
| EEP | $3.14 | $9.98 | 90 km | $6.84 |
| LEP | $1.96 | $16.68 | 152 km | $14.72 |
| *B. Lucky Bay + Lock + Kimba bunkers* | | | | |
| **EP (all)** | $2.66 | $11.01 | 99 km | $8.36 |
| WEP | $3.03 | $18.78 | 170 km | $15.75 |
| EEP | $3.14 | $4.74 | 41 km | $1.60 |
| LEP | $1.96 | $10.57 | 96 km | $8.61 |

Which independent point is the nearest one, by tonne share:

| State | mix |
|---|---|
| A. Lucky Bay only | Lucky Bay (T-Ports port) 100.0 % |
| B. Lucky Bay + Lock + Kimba bunkers | Lock (T-Ports bunker) 70.7 % - Kimba (T-Ports bunker) 16.9 % - Lucky Bay (T-Ports port) 12.4 % |
| C. no independent point at all | none - no independent point in this state |
| D. pre-2019 | none - no independent point in this state |

---

## M3 - the catchment: who would actually use it

Tonne share of district production whose toll falls at or below each level. The first column is the share for which the independent point is the **closest receival point of any owner** - the only production for which the gateway changes the cartage bill at all.

**A. Lucky Bay only**

| District | independent is nearest | toll <= $1/t | <= $2/t | <= $5/t |
|---|---|---|---|---|
| **EP (all)** | 4.5 % | 5.4 % | 6.1 % | 9.4 % |
| WEP | 0.0 % | 0.0 % | 0.0 % | 0.0 % |
| EEP | 13.8 % | 16.5 % | 18.7 % | 28.8 % |
| LEP | 0.0 % | 0.0 % | 0.0 % | 0.0 % |

**B. Lucky Bay + Lock + Kimba bunkers**

| District | independent is nearest | toll <= $1/t | <= $2/t | <= $5/t |
|---|---|---|---|---|
| **EP (all)** | 10.4 % | 18.1 % | 21.5 % | 36.9 % |
| WEP | 2.9 % | 9.7 % | 10.6 % | 20.3 % |
| EEP | 29.3 % | 46.8 % | 56.3 % | 86.4 % |
| LEP | 0.0 % | 0.0 % | 0.0 % | 7.1 % |

---

## M4 - the direct-to-port run, A$/t

Cartage to the nearest **export port** of any owner. On EP that is Port Lincoln and Thevenard (Bunge) at every state, plus Lucky Bay (T-Ports) at A and B. This is the task's 'nearest export-capable destination' measure made honest: an export-capable test over *all* receival points excludes nothing, because every upcountry silo on this roster feeds a port, so it collapses exactly onto M1.

| District | A. Lucky Bay only | B. Lucky Bay + Lock + Kimba bunkers | C. no independent point at all | D. pre-2019 |
|---|---|---|---|---|
| **EP (all)** | $10.16 | $10.16 | $13.54 | $13.54 |
| WEP (Western Eyre Peninsula) | $13.47 | $13.47 | $13.93 | $13.93 |
| EEP (Eastern Eyre Peninsula) | $9.97 | $9.97 | $19.83 | $19.83 |
| LEP (Lower Eyre Peninsula) | $7.85 | $7.85 | $7.90 | $7.90 |

---

## The deltas between states

Signed A$/t, positive = costs more. Each row is one step of a ladder; the last row is the end-to-end comparison and is contaminated, as noted.

### D -> C: pre-2019 -> no independent point at all

The cartage cost of losing the seven sites that went from the pre-2019 network to the current one - the six closed in June 2019 plus Nunjikompita, since gone dormant - holding OWNERSHIP constant, because both states are incumbent-only and no gateway effect is mixed in. **READ IT AS A BRACKET, NOT AN UPPER BOUND.** An earlier revision printed +$0.22/t as an
upper bound; that is falsified by this repo's own roster audit and has been corrected. Two
errors pull in opposite directions and neither is resolved. Only two of the six 2019 sites
(Minnipa and Kyancutta) were operating the year before; the other four are in the group the
operator described as 'not open the year prior' (Stock Journal, 6 June 2019), so treating
all six as open overstates the pre-2019 network by four sites and **overstates** this delta.
Pulling the other way, Cowell and Mangalo were receiving grain pre-2019 and are missing from
`sites.geojson` entirely (`docs/roster_audit_2026-08.md` §5); restoring them takes the EP
figure to **+$0.452/t**, which **understates** it. The defensible bracket for EP is therefore
roughly **+$0.12 to +$0.47/t**, and no single figure in this row should be quoted as a bound
in either direction until the roster is completed.

| District | delta M1 (marginal, floor) | delta M4 (port run) | delta M2 (the toll) |
|---|---|---|---|
| **EP (all)** | +0.22 *(bracket +0.12 to +0.47)* | +0.00 | - |
| WEP | +0.48 | +0.00 | - |
| EEP | +0.20 | +0.00 | - |
| LEP | +0.03 | +0.00 | - |

### C -> A: no independent point at all -> Lucky Bay only

WHAT THE GATEWAY IS WORTH in cartage actually paid: the change in the bill when the peninsula's one independent point is added to the network. This is the delta the task asks for, and the honest answer is that it is small, concentrated in EEP, and zero in WEP and LEP - because outside EEP nobody's nearest place to tip a load changes.

| District | delta M1 (the bill) | delta M4 (port run) | delta M2 (the toll) |
|---|---|---|---|
| **EP (all)** | -0.14 | -3.38 | - |
| WEP | +0.00 | -0.46 | - |
| EEP | -0.43 | -9.86 | - |
| LEP | +0.00 | -0.05 | - |

### A -> B: Lucky Bay only -> Lucky Bay + Lock + Kimba bunkers

What reopening the two inland bunkers would be worth on top of Lucky Bay. Note the shape: the toll roughly halves while the bill does not move, because the bunkers sit beside Bunge's own Lock and Kimba sites (see the co-location table). They add a buyer, not a destination.

| District | delta M1 (the bill) | delta M4 (port run) | delta M2 (the toll) |
|---|---|---|---|
| **EP (all)** | -0.01 | +0.00 | -8.12 |
| WEP | +0.00 | +0.00 | -14.14 |
| EEP | -0.03 | +0.00 | -5.24 |
| LEP | +0.00 | +0.00 | -6.11 |

### D -> A: pre-2019 -> Lucky Bay only

Pre-2019 to now, end to end. CONTAMINATED - it mixes the 2019 closures, the arrival of T-Ports and two different roster-defect sets. Decompose it with the two rows above rather than quoting it.

| District | delta M1 (the bill) | delta M4 (port run) | delta M2 (the toll) |
|---|---|---|---|
| **EP (all)** | +0.08 | -3.38 | - |
| WEP | +0.48 | -0.46 | - |
| EEP | -0.23 | -9.86 | - |
| LEP | +0.03 | -0.05 | - |

---

## Sensitivities

### Routing on least distance instead of least time (depends on no assumed speed)

| State | M1 bill | M2 toll | M4 port run |
|---|---|---|---|
| A. Lucky Bay only | $2.46 | $15.88 | $9.82 |
| B. Lucky Bay + Lock + Kimba bunkers | $2.45 | $8.18 | $9.82 |
| C. no independent point at all | $2.61 | - | $13.19 |
| D. pre-2019 | $2.41 | - | $13.19 |

### The 250 km ceiling

| State | production whose independent haul exceeds 250 km | longest independent haul |
|---|---|---|
| A. Lucky Bay only | 18.0 % | 622 km |
| B. Lucky Bay + Lock + Kimba bunkers | 6.7 % | 491 km |
| C. no independent point at all | - | - |
| D. pre-2019 | - | - |

Above 250 km the schedule stops. Applying $0.11/t-km there is an extrapolation, not a citation.

### The band inversion

| State | production where the cheapest point is not the nearest | mean A$/t forgone | worst cell |
|---|---|---|---|
| A. Lucky Bay only | 0.2 % | $0.000 | $0.26 |
| B. Lucky Bay + Lock + Kimba bunkers | 0.2 % | $0.001 | $0.34 |
| C. no independent point at all | 0.2 % | $0.001 | $0.37 |
| D. pre-2019 | 0.3 % | $0.000 | $0.22 |

### Weighting

| State | M1, tonne-weighted | M1, unweighted cells | M2, tonne-weighted | M2, unweighted cells |
|---|---|---|---|---|
| A. Lucky Bay only | $2.52 | $2.90 | $16.48 | $20.78 |
| B. Lucky Bay + Lock + Kimba bunkers | $2.51 | $2.89 | $8.36 | $10.62 |
| C. no independent point at all | $2.66 | $3.05 | - | - |
| D. pre-2019 | $2.44 | $2.75 | - | - |

### Cross-check against R0

R0 (pipeline/r8_choice_geometry.py) routes the same journeys on the same graph with the same weights and reports them in MINUTES. M1 is those journeys priced in KILOMETRES. The implied mean speed is printed so an inconsistency between the two scripts would be visible. This is a routing check, not a publication of R0's Ladder A, which is not quotable (docs/gate_findings.md).

| State | mean minutes to the nearest point of any owner | mean km | implied mean speed |
|---|---|---|---|
| A. Lucky Bay only | 17.9 min | 21.1 km | 70.8 km/h |
| B. Lucky Bay + Lock + Kimba bunkers | 17.8 min | 21.0 km | 70.8 km/h |
| C. no independent point at all | 18.7 min | 22.4 km | 71.7 km/h |
| D. pre-2019 | 17.5 min | 20.6 km | 70.5 km/h |

### The road snap

Tonne-weighted mean cell snap 1.99 km; 44.3 % of production snaps more than 2 km; worst site snap 0.65 km.

A cell is routed from its nearest node on the OSM graph and the snap leg itself is not driven, so a large snap understates that cell's kilometres to EVERY destination equally. On the LEVELS (M1, M4, the bare independent level) it understates the dollars. On the TOLL it very largely cancels, because the toll is a difference of two hauls that share the same snap - it survives only through the band edge, where the two hauls can fall in different bands. Tonne-weighted mean snap and the share of production snapping more than 2 km are printed with it so the size of it is visible.

### The unresolved return leg

THE EMPTY RETURN LEG IS UNRESOLVED AND IS WORTH A FACTOR OF TWO. Established: ESCOSA APPLIES the rate to a one-way distance - all four of its own published results reproduce on that reading and on no other. Not established: whether AEGIC's underlying cost line was itself built on a round-trip cycle. The report is silent. The distance is NOT doubled here, because doubling would double-count if the cost line already embeds the return. The doubled figures are reported once, as a labelled UPPER BOUND on the open question, and are not a published result. Settling it needs AEGIC, Australia's grain supply chains, October 2018, Note 2c to Figure 4, p. 18, which is not cached in this repo.

| State | published (one-way) toll | upper bound if the return leg is real and not already in the cost line |
|---|---|---|
| A. Lucky Bay only | $16.48 | $32.96 |
| B. Lucky Bay + Lock + Kimba bunkers | $8.36 | $16.72 |
| C. no independent point at all | - | - |
| D. pre-2019 | - | - |

The right-hand column is **not a published result**. It is the size of an open question.

---

## Caveats

- **Cartage is half the decision** - CARTAGE IS HALF OF A DELIVERY DECISION. Growers deliver where PRICE MINUS CARTAGE is best. This project has no price data - 13 days of off-season cash bids and nothing else (data/SOURCES.md, operator-cash-prices-api). Every figure on this page is one side of that ledger. A toll of $X/t says the independent must be worth $X/t more at the weighbridge before the load moves; it does NOT say whether it was, and nothing here is a total grower benefit or loss.
- **These are marginal dollars, so they are a floor** - THESE ARE MARGINAL DOLLARS AND THEREFORE A FLOOR. ESCOSA's rate is explicitly the additional cost of travelling further once the truck is on the road. Truck ownership, loading, queueing, turnaround and driver time are outside it BY DESIGN, and ESCOSA says so. The size of that gap depends on haul length, and this note must be read at the haul length of the measure it governs. At EP's ~144 km site-to-port haul the same rate gives $15.84/t against a 2026 commercial rate card's $29.90/t and a 2026 SA budget guide's $35.00/t - about half a delivered price. But M1's mean haul is **21.1 km, not 144 km**, and on a haul that short the excluded fixed costs dominate: there the marginal rate understates a delivered price by roughly **7x, not 2x**. Calibrating this note at 144 km against a 21 km measure understated the shortfall by about 3.5x and has been corrected. A grower reading '$X/t more' here is reading the extra fuel-and-running cost of the extra kilometres, not the extra cost of running the extra trips.
- **The site roster is known incomplete** - EVERY MEASURE ON THIS PAGE EXCEPT THE BARE INDEPENDENT LEVEL DEPENDS ON THE SITE ROSTER, AND THE ROSTER IS KNOWN INCOMPLETE. R0's threshold rows survive a roster defect because they are a function of the drive to the nearest INDEPENDENT point alone and every roster defect on record is incumbent-side. M1, M3 and M4 are not protected that way, and neither is the toll M2, because the toll is measured FROM the incumbent. docs/roster_audit_2026-08.md section 5: Tooligie (received 2022/23, 2023/24, 2024/25), Cowell (2017/18, 2018/19) and Mangalo (2018/19) are absent from sites.geojson altogether, and Cungena is tagged closed_2019 but received grain in 2022/23. THE DIRECTIONS ARE KNOWN AND ARE NOT SYMMETRIC. Missing incumbent sites raise the modelled cost to the nearest incumbent point, so: M1 levels are UPPER BOUNDS at every state; the toll M2 is a LOWER BOUND (a nearer real Bunge site would make the independent option relatively dearer); M3's catchment share is an UPPER BOUND. And the contamination is not even across states - Cowell and Mangalo bear on pre-2019 only, Tooligie on the 2023/24-attributed state and probably the current ones, Cungena on all three post-2019 states - so the state-to-state DELTAS carry it too. This is the single biggest defect in these numbers and it is not fixed here: fixing it means coordinates and capacities for three sites, and A4's capacity split entangles that with the calibration (roster_audit section 5).
- **State A rests on one coordinate** - STATE A RESTS ENTIRELY ON ONE COORDINATE. With both bunkers shut, Lucky Bay is the only independent receival point on the peninsula, so the toll at state A is a pure function of the road distance to a single point. That point is registered in sites.geojson at a TOWN/HAMLET node ('Lucky Bay, South Australia' hamlet node, facility adjoins hamlet) - the same precision class A11 gives Lock and Kimba a <=5 km tolerance for, and it is registered in no assumption. It is swept here rather than asserted: the site is displaced 0 / 2.5 / 5 km on eight bearings, RE-SNAPPED to the road graph and RE-ROUTED with a fresh Dijkstra, and the envelope is published beside every state-A figure.
- **The season labels are attributions, and one is unsourced** - THE SEASON LABELS ARE ATTRIBUTIONS AND ONE OF THEM IS UNSOURCED. The four states are defined by their CONTENT - which points exist - and every number here follows from that content alone. The attribution of state A to 2025/26 rests on the claim that both T-Ports bunkers were closed for that season, and that claim has no source in this repo: there is no tports.com/harvest entry in data/SOURCES.md, no cached page under data/raw/, no retrieval date, and for KIMBA no closure evidence at all (its status field is set with a notes field reading only 'Built for 2021 harvest'). The only record is a hand-typed note on LOCK in pipeline/manual_sites.json citing a live read of tports.com/harvest on 2026-08-19 - the same off-season live read that docs/roster_audit_2026-08.md section 1 identifies as the root cause of four wrongly closed Bunge sites. Read A and B as 'Lucky Bay alone' and 'Lucky Bay plus both bunkers'. Do not publish either season label until the page is archived and registered.
- **The empty return leg is unresolved** - THE EMPTY RETURN LEG IS UNRESOLVED AND IS WORTH A FACTOR OF TWO. Established: ESCOSA APPLIES the rate to a one-way distance - all four of its own published results reproduce on that reading and on no other. Not established: whether AEGIC's underlying cost line was itself built on a round-trip cycle. The report is silent. The distance is NOT doubled here, because doubling would double-count if the cost line already embeds the return. The doubled figures are reported once, as a labelled UPPER BOUND on the open question, and are not a published result. Settling it needs AEGIC, Australia's grain supply chains, October 2018, Note 2c to Figure 4, p. 18, which is not cached in this repo.
- **Base year** - The rate is 2018-19 A$ and is published here unindexed, on A18's recorded decision. Seven years old. This must sit next to every figure, not in a footnote.

---

## Carried assumptions

- **A18** - the ESCOSA marginal cartage schedule, used as published. This is the ONLY place a dollar enters this page. The app's flat A$0.10/t-km working lever is NOT used and must not be confused with it.
- **A5** - road class speeds - used only to CHOOSE the path (least time), not to price it. The kilometres are then read off that path, never derived as minutes x speed. A least-DISTANCE routing variant is published as a standing sensitivity and it depends on no assumed speed at all.
- **A11** - the Lock and Kimba town-centroid coordinates, <=5 km tolerance. Bears on state B only. Swept, with magnitudes and bearings both varied independently.
- **A12** - season site sets. Load-bearing here in a way it is not for R0's threshold rows - see the roster caveat. This script inherits r8_choice_geometry's status-field state construction, including its known omission of Nunjikompita from the 2023/24-attributed state.
- **A14** - district boundaries approximated by LGA composition - used for the tonne weighting only, not for routing.
- **Lucky Bay coordinate** - a hamlet node, registered in no assumption. Swept here. It should be registered in ASSUMPTIONS.md.
- **A1/A2/A4/A9/A15/A24** - NOT USED. No payload, no bay count, no capacity, no fitted parameter enters any number on this page. A cart leg is priced per tonne, so the truck configuration cancels out of it entirely.

