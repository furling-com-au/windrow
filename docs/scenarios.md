# Scenario results — Windrow v1

Season 2025/26, calibrated parameters, seed 42 (deterministic). Raw numbers in
`scenarios_data.json`; regenerate with `npx tsx packages/sim/scripts/scenarios.ts 2025/26`.
All scenarios keep the observed vessel program fixed unless noted — that is the point:
they show how the *land side* copes, and where the fixed export program breaks.

| scenario | Bunge received (Mt) | T-Ports intake (Mt) | PL shipped (Mt) | peak site queue | mean vessel wait | truck-km (M) | peak week (kt) |
|---|---|---|---|---|---|---|---|
| Baseline replay | 2.23 | 0.33 | 1.19 | 139 | 27.7 h | 19.53 | 433 |
| Bumper (+30 %) | 2.79 | 0.54 | 1.20 | **450** | 27.7 h | 22.38 | 432 |
| Drought (−40 %) | 1.40 | 0.13 | 1.15 | 59 | 109.4 h | 13.97 | 262 |
| Rail reinstated | 2.23 | 0.32 | 1.20 | 112 | 27.7 h | **17.14** | 433 |
| Lucky Bay share ×2.5 | **2.09** | **0.47** | 1.20 | 123 | 27.7 h | 20.15 | 412 |
| PL outage (7 d @ day 70) | 2.20 | 0.35 | 1.20 | **182** | 28.1 h | 20.53 | 433 |
| Tod Hwy closure (×2.5) | 2.22 | 0.33 | 1.19 | 140 | 27.7 h | 21.00 | 431 |

(Numbers include A17 carry-in stocks; regenerated 2026-08-31 on the vessel-program
give-up fix of `#6` — a vessel waiting more than 15 days at anchor with no grain coming
is now re-nominated rather than held forever, which also removed a small amount of
phantom port demand that was skewing routing even at baseline. The truck-km column is
ROAD vehicle-kilometres only — trainset kilometres are tracked separately and excluded.
Every kilometre figure on this page is ~12 % higher than the pre-`#10` version: distances
now come from the OSM routing step instead of being back-derived from drive minutes at a
flat 75 km/h, which had understated the fast trunk hauls that dominate the task.)

Baseline vessel waiting is anchored to reality: vessels arrive at the Boston Bay
anchorage at their AIS-observed times and hold until their berth slot, so the baseline
mean wait (28.3 h) reproduces the AIS-observed median anchorage stay (26.8 h). Scenario
deltas on top of that (e.g. the outage's +0.5 h) are simulated stock/berth effects.

## Readings

**Bumper (+30 %).** The extra 0.56 Mt is absorbed, but with carry-in stock already
occupying storage the worst site-hour queue more than triples (139 → 450 trucks) and more
grain spills to the T-Ports system (+0.21 Mt) as Bunge sites cap out. Port Lincoln shipping is unchanged — the vessel
program, not the land side, is the export bottleneck in a big year. (Real-world
response would be more vessels; the fixed program isolates the landside effect.)

**Drought (−40 %).** The land side relaxes (worst queue 139 → 59 trucks), but the *fixed* export
program becomes infeasible: Port Lincoln ships 1.15 Mt against a 1.54 Mt program. Vessels
wait well above baseline (mean 109.4 h vs 27.7 h) while grain fails to arrive, but the sim
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
trainset per active day** as actually dispatched over 2025/26 (199 trips on 69 active
days) — the shuttle idles whenever port stocks are covered. (Earlier revisions asserted a
"≤~2 cycles/day" ceiling that nothing in the engine enforced; at road speeds trainsets
reached 4.0. Until `#10` the transit was derived from road *minutes* × 75/40 rather than
from distance, which quietly ran the trains above 40 km/h on every route whose real road
speed beat 75.)

Rail tonne-km are accounted separately from road tonne-km. On the 45 t default the
trains take **56 M t·km** off the road task (336 → 283 M road t·km), which is what makes
the freight line a **saving of ~$5.3 M** at the A18 rate rather than a cost. That figure
prices only the cartage the trucks no longer do: rebuilding and operating the railway is
not costed anywhere in this model, and the road cartage rate does not describe rail
haulage.

**How big that saving is depends entirely on how big the trucks it displaces are** — the
single most consequential open assumption in this scenario (A1; data/trucks.md open
question 7). Measured on 2025/26:

| silo→port load | road truck-km | with rail | rail saves |
|---|---|---|---|
| **45 t** (default; Viterra's 2019 rail-replacement statement) | 19.53 M | 17.14 M | **2.38 M** (−12 %) |
| 72 t (ACCC's EP *permitted* load size) | 17.69 M | 16.48 M | **1.21 M** (−7 %) |
| 85 t (SA Type 2 road train at CML 132.83 t) | 17.20 M | 16.20 M | **1.00 M** (−6 %) |

So the headline saving falls by **more than half** if EP line-haul runs the
heavier road trains SA law permits — i.e. the case for rail is *weakest* under the most
permissive road rules, and the earlier single-figure "−3.0 M truck-km" overstated it.
Total loaded tonne-km barely move across this range, because the same grain travels the
same distance regardless of how it is split across trucks; what changes is the
vehicle-kilometre count — and with it road wear, emissions and driver demand — plus how
much of the tonne-km task sits on rail rather than road (56 / 43 / 41 M t·km at 45 / 72 /
85 t). Against any of these figures, a reinstatement capital case would
still have to stack up.

**Lucky Bay share ×2.5.** T-Ports intake grows 0.33 → 0.47 Mt; Bunge Western receivals
drop ~0.14 Mt, concentrated in eastern-EP clusters (Cowell/Cleve/Kimba catchments), and
Bunge peak queues ease. Port Lincoln shipping is unaffected at this scale — the grain
that leaves the Bunge system was upcountry surplus, not port feed.

**Port Lincoln outage (7 days at harvest peak).** Receivals barely drop (−0.03 Mt) but
the buffer does its job at a price: the worst site queue spikes to 182 trucks as
direct-to-port deliveries redirect to Cummins/Tumby Bay, and line-haul catches up
afterwards (+1.00 M truck-km). Vessels ride it out at anchor (+0.5 h mean wait over
baseline).

**Tod Highway closure.** With cluster→site travel times ×2.5 along the corridor, trucks
re-sort to Lincoln-Highway-side sites; total receivals are almost unchanged but the
detours add **+1.5 M truck-km** (+8 %, ≈ a few hundred thousand dollars of cartage at
A18 rates). (Corridor assignment is a
straight-line heuristic — see engine comment; a routed-detour version is future work.)

## Caveats

- Vessel programs are held at observed 2025/26 arrivals in every scenario.
- Queue counts inherit the site service-time assumption (A2); treat them as relative
  indicators between scenarios, not absolute truck counts.
- No carry-in stocks at season start (README limitations), so absolute PL shipped
  figures sit below the observed shipping year in all scenarios.
