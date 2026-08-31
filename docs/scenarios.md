# Scenario results — Windrow v1

Season 2025/26, calibrated parameters, seed 42 (deterministic). Raw numbers in
`scenarios_data.json`; regenerate with `npx tsx packages/sim/scripts/scenarios.ts 2025/26`.
All scenarios keep the observed vessel program fixed unless noted — that is the point:
they show how the *land side* copes, and where the fixed export program breaks.

| scenario | Bunge received (Mt) | T-Ports intake (Mt) | PL shipped (Mt) | peak site queue | mean vessel wait | truck-km (M) | peak week (kt) |
|---|---|---|---|---|---|---|---|
| Baseline replay | 2.25 | 0.41 | 1.20 | 105 | 27.7 h | 18.84 | 372 |
| Bumper (+30 %) | 2.90 | 0.56 | 1.20 | **387** | 27.7 h | 21.18 | 374 |
| Drought (−40 %) | 1.38 | 0.21 | 1.15 | 39 | 84.4 h | 14.82 | 226 |
| Rail reinstated | 2.25 | 0.41 | 1.20 | 100 | 27.7 h | **16.67** | 373 |
| Lucky Bay share ×2.5 | **2.17** | **0.49** | 1.20 | 84 | 27.7 h | 18.93 | 362 |
| PL outage (7 d @ day 70) | 2.23 | 0.43 | 1.20 | **122** | 28.1 h | 19.33 | 372 |
| Tod Hwy closure (×2.5) | 2.23 | 0.43 | 1.20 | 101 | 27.7 h | 20.05 | 364 |

(Numbers include A17 carry-in stocks; regenerated 2026-08-31 on the `#22` refit — three
knobs had been fitting to the exact floor of their search ranges, the floors were widened
to physically motivated ones, and all twelve knobs were refitted. Every number on this
page moved, because eleven of the twelve knobs did. The truck-km column is ROAD
vehicle-kilometres only — trainset kilometres are tracked separately and excluded. Every
kilometre figure on this page is ~12 % higher than the pre-`#10` version: distances now
come from the OSM routing step instead of being back-derived from drive minutes at a flat
75 km/h, which had understated the fast trunk hauls that dominate the task.)

**How much of this survives a refit?** The `#22` refit changed the whole parameter vector
(fleet 691 → 555, port bays 5 → 6, choice decay β 2.06 → 2.81, retention 0.100 → 0.055),
so it is a fair robustness test on the *scenario* conclusions rather than on the fitted
numbers. Every ranking below is unchanged and every direction of effect is unchanged; the
magnitudes move by 10–25 % (e.g. the outage's peak queue 226 → 122, the rail saving
2.14 → 2.17 M truck-km). Read the scenario deltas as robust and the absolute levels as
carrying the identification caveats in A2 (fleet), A4 (storage) and A24 (retention ⇄
Lucky Bay).

Baseline vessel waiting is anchored to reality: vessels arrive at the Boston Bay
anchorage at their AIS-observed times and hold until their berth slot, so the baseline
mean wait (27.7 h) sits close to the AIS-observed median anchorage stay (26.8 h). Across
the land-side scenarios the wait barely moves (27.7–28.1 h — a single marginal vessel
crossing a berth slot is worth ~3 h on a 51-ship mean); only the drought, where the fixed
export program outruns the crop, moves it materially.

## Readings

**Bumper (+30 %).** The extra 0.65 Mt is absorbed, but with carry-in stock already
occupying storage the worst site-hour queue nearly quadruples (105 → 387 trucks) and more
grain spills to the T-Ports system (+0.14 Mt) as Bunge sites cap out. Port Lincoln shipping is unchanged — the vessel
program, not the land side, is the export bottleneck in a big year. (Real-world
response would be more vessels; the fixed program isolates the landside effect.)

**Drought (−40 %).** The land side relaxes (worst queue 105 → 39 trucks), but the *fixed* export
program becomes infeasible: Port Lincoln ships 1.15 Mt against a 1.54 Mt program. Vessels
wait well above baseline (mean 84.4 h vs 27.7 h) while grain fails to arrive, but the sim
now caps this realistically: a vessel that has sat at anchor for 15 days with no grain
coming is treated as re-nominated — in reality the charterer would re-issue the program for
a smaller crop rather than leave a ship waiting indefinitely — so it leaves rather than
accumulating demurrage forever. (Earlier revisions let this wait grow unbounded, producing
a mean of 1,093–1,505 h and a nonsensical multi-hundred-million-dollar "ships waiting"
figure; see `engine.ts`'s `VESSEL_GIVEUP_TICKS`.) This mirrors 2024/25 reality, where the
program itself shrank.

**Rail reinstated.** Two 1,600 t trainsets on the old Cummins/Kimba/Wudinna alignments
(demand-dispatched; road line-haul fleet cut by a third — A21) keep port stocks equally
well supplied while removing truck-kilometres from the roads. Receival and shipping
outcomes are unchanged, consistent with why the 2019 closure was absorbable by ~48
trucks/day.

Trainsets run the alignment at a 40 km/h line speed against the leg's real routed
distance, so a cycle is 2 × transit + 4 h handling: ~1.6 cycles/day on the long Kimba
(214 km) and Wudinna (213 km) runs, ~3.4 on the short Cummins one (63 km), and **1.4 per
trainset per active day** as actually dispatched over 2025/26 (191 trips on 68 active
days) — the shuttle idles whenever port stocks are covered. (Earlier revisions asserted a
"≤~2 cycles/day" ceiling that nothing in the engine enforced; at road speeds trainsets
reached 4.0. Until `#10` the transit was derived from road *minutes* × 75/40 rather than
from distance, which quietly ran the trains above 40 km/h on every route whose real road
speed beat 75.)

Rail tonne-km are accounted separately from road tonne-km. On the 45 t default the
trains take **49 M t·km** off the road task (318 → 269 M road t·km), which is what makes
the freight line a **saving of ~$4.9 M** at the A18 rate rather than a cost. That figure
prices only the cartage the trucks no longer do: rebuilding and operating the railway is
not costed anywhere in this model, and the road cartage rate does not describe rail
haulage.

**How big that saving is depends entirely on how big the trucks it displaces are** — the
single most consequential open assumption in this scenario (A1; data/trucks.md open
question 7). Measured on 2025/26:

| silo→port load | road truck-km | with rail | rail saves |
|---|---|---|---|
| **45 t** (default; Viterra's 2019 rail-replacement statement) | 18.84 M | 16.67 M | **2.17 M** (−12 %) |
| 72 t (ACCC's EP *permitted* load size) | 17.05 M | 15.93 M | **1.12 M** (−7 %) |
| 85 t (SA Type 2 road train at CML 132.83 t) | 16.54 M | 15.72 M | **0.82 M** (−5 %) |

So the headline saving falls by **more than half** if EP line-haul runs the
heavier road trains SA law permits — i.e. the case for rail is *weakest* under the most
permissive road rules, and the earlier single-figure "−3.0 M truck-km" overstated it.
Total loaded tonne-km barely move across this range, because the same grain travels the
same distance regardless of how it is split across trucks; what changes is the
vehicle-kilometre count — and with it road wear, emissions and driver demand — plus how
much of the tonne-km task sits on rail rather than road (49 / 38 / 35 M t·km at 45 / 72 /
85 t). Against any of these figures, a reinstatement capital case would
still have to stack up.

**Lucky Bay share ×2.5.** T-Ports intake grows 0.41 → 0.49 Mt; Bunge Western receivals
drop ~0.08 Mt, concentrated in eastern-EP clusters (Cowell/Cleve/Kimba catchments), and
Bunge peak queues ease. Port Lincoln shipping is unaffected at this scale — the grain
that leaves the Bunge system was upcountry surplus, not port feed. Note the baseline this
is a multiple *of*: the lever moves `luckyBayBias` to an absolute 2.5, which is 2.8× the
fitted 0.885, and the fitted value itself is not separately identified from the retention
share (A24). The direction and rough size are robust; the exact split is not.

**Port Lincoln outage (7 days at harvest peak).** Receivals barely drop (−0.02 Mt) but
the buffer does its job at a price: the worst site queue spikes to 122 trucks as
direct-to-port deliveries redirect to Cummins/Tumby Bay, and line-haul catches up
afterwards (+0.49 M truck-km).

**Tod Highway closure.** With cluster→site travel times ×2.5 along the corridor, trucks
re-sort to Lincoln-Highway-side sites; total receivals are almost unchanged but the
detours add **+1.21 M truck-km** (+6 %, ≈ a few hundred thousand dollars of cartage at
A18 rates). (Corridor assignment is a
straight-line heuristic — see engine comment; a routed-detour version is future work.)

## Caveats

- Vessel programs are held at observed 2025/26 arrivals in every scenario.
- Queue counts inherit the site service-time assumption (A2); treat them as relative
  indicators between scenarios, not absolute truck counts.
