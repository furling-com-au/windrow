# Scenario results — Windrow v1

Season 2025/26, calibrated parameters, seed 42 (deterministic). Raw numbers in
`scenarios_data.json`; regenerate with `npx tsx packages/sim/scripts/scenarios.ts 2025/26`.
All scenarios keep the observed vessel program fixed unless noted — that is the point:
they show how the *land side* copes, and where the fixed export program breaks.

| scenario | Bunge received (Mt) | T-Ports intake (Mt) | PL shipped (Mt) | peak site queue | mean vessel wait | peak week (kt) |
|---|---|---|---|---|---|---|
| Baseline replay | 2.19 | 0.35 | 1.22 | 195 | ~0 h | 366 |
| Bumper (+30 %) | 2.80 | 0.51 | 1.22 | 223 | ~0 h | 396 |
| Drought (−40 %) | 1.40 | 0.13 | 0.99 | 93 | 2,456 h† | 260 |
| Rail reinstated | 2.19 | 0.35 | 1.22 | **178** | ~0 h | 366 |
| Lucky Bay share ×2.5 | **2.08** | **0.46** | 1.22 | 152 | ~0 h | 355 |
| PL outage (7 d @ day 70) | 2.17 | 0.37 | 1.22 | **235** | 0.5 h | 366 |
| Tod Hwy closure (×2.5) | 2.18 | 0.36 | 1.22 | 164 | ~0 h | 363 |

† Mean across all vessels including those that waited weeks for grain that never came —
see Drought below.

## Readings

**Bumper (+30 %).** The extra 0.7 Mt is absorbed, but peak-site queues rise ~15 %
(195 → 223 trucks at the worst site-hour) and more grain spills to the T-Ports system
(+0.16 Mt) as Bunge sites cap out. Port Lincoln shipping is unchanged — the vessel
program, not the land side, is the export bottleneck in a big year. (Real-world
response would be more vessels; the fixed program isolates the landside effect.)

**Drought (−40 %).** The land side relaxes (queues halve), but the *fixed* export
program becomes infeasible: Port Lincoln ships 0.99 Mt against a 1.54 Mt program, and
vessels sit at anchor for weeks waiting for grain before short-loading (the sim's
5-day starvation guard). This mirrors 2024/25 reality, where the program itself shrank.

**Rail reinstated.** Two 1,600 t trainsets on the old Cummins/Kimba/Wudinna alignments
(with the road line-haul fleet cut by a third) keep port stocks equally well supplied
while trimming the peak queue 195 → 178 and cutting road line-haul truck-kilometres —
the effect is real but modest, consistent with why the 2019 closure was absorbed by
~48 trucks/day.

**Lucky Bay share ×2.5.** T-Ports intake grows 0.35 → 0.46 Mt; Bunge Western receivals
drop ~0.11 Mt, concentrated in eastern-EP clusters (Cowell/Cleve/Kimba catchments), and
Bunge peak queues ease. Port Lincoln shipping is unaffected at this scale — the grain
that leaves the Bunge system was upcountry surplus, not port feed.

**Port Lincoln outage (7 days at harvest peak).** Receivals barely drop (−0.02 Mt) but
the buffer does its job at a price: the worst site queue spikes to 235 trucks as
direct-to-port deliveries redirect to Cummins/Tumby Bay, and line-haul catches up
afterwards. Vessels ride it out at anchor (+0.5 h mean wait).

**Tod Highway closure.** With cluster→site travel times ×2.5 along the corridor, trucks
re-sort to Lincoln-Highway-side sites; total receivals are almost unchanged but the
spatial pattern shifts and corridor truck-kilometres rise. (Corridor assignment is a
straight-line heuristic — see engine comment; a routed-detour version is future work.)

## Caveats

- Vessel programs are held at observed 2025/26 arrivals in every scenario.
- Queue counts inherit the site service-time assumption (A2); treat them as relative
  indicators between scenarios, not absolute truck counts.
- No carry-in stocks at season start (README limitations), so absolute PL shipped
  figures sit below the observed shipping year in all scenarios.
