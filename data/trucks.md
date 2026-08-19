# Grain trucks on the Eyre Peninsula — research notes (R6)

Compiled 2026-08-19. Every figure cites its source; unknowns are listed at the end and
mirrored in `data/ASSUMPTIONS.md`.

## Configurations and mass limits

Source: **GTSN Truck Chart — South Australia, Sept 2025** (Bunge/Grain Transport Safety
Network, doc 7629/3.1): <https://www.viterra.com.au/dam/jcr:41eda0be-952a-4fcf-9bab-4014c2cccd7e/SA---Viterra-grain-transport-safety-network-truck-chart.pdf>
Gross combination masses (t) under General / Concessional / Higher Mass Limits:

| Config (GTSN code) | Max length | GML | CML | HML |
|---|---|---|---|---|
| 6-axle semi-trailer (12) | 19.0 m | 42.5 | 43.5 | 45.5 |
| 3-axle truck + 4-axle dog (76) | 19–23 m | 42.5 (48–59 under 2025 SA notices) | — | — |
| 7-axle B-double (83) | 26.0 m | 55.5 | 57.0 | 57.0 |
| 9-axle B-double (68) | 26.0 m | 62.5 | 64.5 | 68.0 |
| 11-axle A-double road train (28) | 36.5 m | 79.0 | 81.0 | 85.0 |
| 12-axle A-double road train (91) | 36.5 m | 82.5 | 84.5 | 90.5 |
| 14-axle AB-triple + 2-axle dolly (88) | 36.5 m | 99.0 | 101.0 | 107.5 |
| 15-axle AB-triple + 3-axle dolly (96) | 36.5 m | 102.5 | 104.5 | 110.0 (113.0 with NHVR permit) |

The table above is the one-page GTSN **truck chart**, which covers **Type 1** road trains
(36.5 m). The full GTSN **Truck Book** (v5.0, Sept 2025, section 4.10) also lists **Type 2**
road trains (53.5 m), which SA permits at materially higher masses:

| Type 2 combination (Truck Book §4.10) | SA GML | SA CML | SA HML |
|---|---|---|---|
| 18-axle road train + 3-axle dolly (89) | 118.13 | 132.83 | **142.28** |
| 17-axle road train (90) | 124.95 | 128.10 | 136.50 |
| 16-axle road train + 2-axle dolly (74) | — | 124.43 | 130.73 |
| 15-axle road train (80) | — | 120.75 | 124.95 |
| 14-axle road train (78) | — | 121.28 | 119.18 |

- Truck Book footnotes 240/242: "**South Australia requires a NHVR permit unless operating
  on the pre-approved 53.5 m network.**" Whether EP trunk highways are on that network is
  **unresolved** — see open question 7 below.
- Type 2 **quads** (ABB-/BAB-quad, up to 135.50 t) are listed **Queensland-only**; the SA
  rows are blank, so they are not evidence for EP operations.
- Nothing in the GTSN grain sources reaches 155 t. Above 142.28 t in SA would require a
  PBS (Performance Based Standards) Level 4 combination running on an individual NHVR
  Vehicle Approval, which by construction does not appear in a generic mass chart — so
  such vehicles may exist without being verifiable from published grain-industry sources.

- **SA harvest concession**: Farm Gate Grain Transport Mass Exemption Notice 2025 — up to
  **105 %** of the mass limit for the first and second loads from a paddock each day,
  farm → receiver (expires Feb 2030). Source: GTSN Truck Book v5.0 Sept 2025 §3.17.5,
  <https://www.viterra.com.au/dam/jcr:efaf8bb1-f13e-4899-a7eb-5afaf8c4c5a9/GTSN---Truck-book.pdf>

## Payloads (published evidence)

- Trucks "with a load size of **72 tonnes** being **allowed** on the Eyre Peninsula, versus
  44" — ACCC Final Determinations p.67 (verbatim; listed among reasons EP freight rates run
  below eastern SA). NOTE: this is a **permitted maximum**, not an observed average load —
  earlier drafts of this file read it as a typical load. 72 t net ≈ a Type 1 AB-triple at
  HML (110-113 t gross at ~65 % net), so it is good evidence for the *class* of vehicle EP
  line-haul can use, not for what an average load weighs.
- Average SA delivered load grew from ~24.5 t (2009-10) to **>29 t** (2016-17) — AEGIC via
  ACCC FD p.68 (state-wide average across all deliveries incl. small farm trucks).
- Tare masses are **not published** in the GTSN chart → net payloads are an assumption
  (see ASSUMPTIONS: payload ≈ 60 % of GCM for semis, ~65 % for road trains).

## Network access

- Above 42.5 t / 19 m = Restricted Access Vehicle; road-train routes published via SA
  **RAVnet** (<https://maps.sa.gov.au/ravnet/index.html>) and the NHVR National Class 2
  Road Train Authorisation Notice 2026. Interactive maps only — no machine-readable route
  list (assumption: trunk EP highways Lincoln/Tod/Flinders/Birdseye/Eyre are road-train
  rated, consistent with Viterra's 2019 rail-replacement plan running road trains on
  Lincoln and Tod Highways: ABC 26 Feb 2019,
  <https://www.abc.net.au/news/rural/2019-02-26/viterra-to-switch-from-rail-to-road-eyre-peninsula/10850900>).
- Road-train speed limit 100 km/h on Eyre Hwy west of Port Augusta, 90 km/h on other
  roads (DTEI Information Guide for Road Trains, 2011 — historical).

## Flows and cycle behaviour

- **EP rail closed 31 May 2019**; pre-closure rail carried grain only from Kimba and
  Wudinna lines (~60-70 % of EP grain was already road) — ACCC FD pp.24, 66-67.
- Rail replacement = "**48 loaded trucks a day** on average Mon-Fri, 12 on Lincoln Hwy
  and 36 on Tod Hwy" (Viterra 2019, ABC above) ≈ 30,000 extra movements/yr.
- Average upcountry-site → port road distance in SA: **~144 km** (AEGIC via ESCOSA Final
  Report p.27, Jan 2019).
- **~75 % of receivals go to upcountry sites; ~25 % direct-to-port** (ESCOSA p.22, 2019
  - a free parameter to calibrate around).
- Site turnaround times in minutes: **not published**. One extreme anecdote: 4-hour
  turnaround during the Nov-2018 rail-outage congestion at Port Lincoln (ABC 2019).
- Daily site records give an upper bound on receival throughput: Port Lincoln
  13,148 t / 13,512 t (Nov 2020), 13,675 t (2022-23) — farmonline/Stock Journal;
  statewide biggest days >200,000-250,000 t.

## Distances between ports (road)

- Lucky Bay ↔ Port Lincoln 177 km; Lucky Bay ↔ Thevenard 412 km (ACCC FD p.39).

## Not published → modelled as assumptions (see ASSUMPTIONS.md)

1. Typical farm → site distance on EP (only site → port averages exist).
2. On-farm loading time (chaser bin / field bin / auger rates).
3. Site tip + turnaround minutes.
4. Trucks-per-day counts at sites (only tonnage records).
5. Tare masses / net payloads per configuration.
6. Machine-readable RAV route list (RAVnet is interactive-only).
7. **Is the EP trunk network (Lincoln/Tod/Eyre Hwy) on SA's pre-approved 53.5 m Type 2
   road-train network?** This decides whether silo->port line-haul runs at ~45 t net
   (Viterra's 2019 rail-replacement statement: 48 loaded trucks/day for ~2,100-2,200 t/day)
   or at ~85 t net (Type 2 at SA CML 132.83 t). The simulation's rail scenario is highly
   sensitive to it: the truck-km a railway would save falls from ~2.5 M (at 45 t) to
   ~0.9 M (at 85 t) - see ASSUMPTIONS A1/A21 and docs/scenarios.md.
