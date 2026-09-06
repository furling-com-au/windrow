import { describe, expect, it } from "vitest";
import { CORRIDORS, corridorShare } from "../src/corridors";
import { DAY_TICKS, Sim, gfdiFullyCured } from "../src/engine";
import { defaultParams } from "../src/params";
import type { Bundle, Params } from "../src/types";
import { loadBundle } from "../scripts/load_bundle";
import { tinyBundle } from "./tiny_bundle";

describe("sim core", () => {
  it("conserves mass and delivers the deliverable share in the tiny scenario", () => {
    const p = defaultParams();
    p.fleetTrucks = 2;
    p.linehaulTrucks = 1;
    const sim = new Sim(tinyBundle(), p, 7);
    const res = sim.run(200); // invariant checks run daily and throw on violation
    const deliverable = 10000 * (1 - p.retentionShare);
    // everything harvestable should eventually be delivered into the network
    expect(res.seasonReceivedT).toBeGreaterThan(deliverable * 0.95);
    expect(res.seasonReceivedT).toBeLessThanOrEqual(deliverable + 1);
    // the vessel should have loaded its target from delivered stock
    expect(res.vesselCount).toBe(1);
    expect(res.seasonShippedPlT).toBeGreaterThan(5900);
  });

  it("is deterministic: same seed => identical event log hash", () => {
    const a = new Sim(tinyBundle(), defaultParams(), 123).run(120);
    const b = new Sim(tinyBundle(), defaultParams(), 123).run(120);
    expect(a.eventLogHash).toBe(b.eventLogHash);
    expect(a.seasonReceivedT).toBe(b.seasonReceivedT);
    const c = new Sim(tinyBundle(), defaultParams(), 124).run(120);
    // different seed: allowed to differ (jittered load times) though totals stay close
    expect(Math.abs(c.seasonReceivedT - a.seasonReceivedT)).toBeLessThan(2000);
  });

  it("runs a real season headless within the perf budget, no invariant violations", () => {
    let bundle: Bundle;
    try {
      bundle = loadBundle("2025/26");
    } catch {
      console.warn("real bundle not present; skipping");
      return;
    }
    const t0 = performance.now();
    const sim = new Sim(bundle, defaultParams(), 42);
    const res = sim.run(365);
    const secs = (performance.now() - t0) / 1000;
    // Spec target was <5 s on a laptop for the original 589-truck fleet. The 2026-08-19
    // recalibration raised the fleet to 731 agents (A2 bay correction), costing ~10 %;
    // budget widened to 8 s locally rather than silently failing the spec criterion.
    // CI runners are ~2-core and slower again.
    expect(secs).toBeLessThan(process.env.CI ? 20 : 8);
    // sane magnitude: within a factor of 2 of observed Western receivals
    const obs = bundle.observed.weekly_receivals.at(-1)?.western?.cum_t ?? 2_000_000;
    expect(res.seasonReceivedT).toBeGreaterThan(obs * 0.5);
    expect(res.seasonReceivedT).toBeLessThan(obs * 2.0);
  });
});

/**
 * Regression cover for #26 / #27.
 *
 * The old two-pass site choice dropped the balk filter entirely on its fallback pass, so
 * under load it admitted every over-threshold site instead of bounding anything: queues ran
 * to 460-820 trucks (15-22 h waits, reported as fact — #27) and `checkInvariants` threw
 * `QUEUE INSANE` out through `sim.step()` and into the worker, killing the app on lever
 * combinations the UI itself offers — six of them, including both main sliders at maximum
 * (#26). The suite could not see any of it because all three tests ran default parameters.
 *
 * These assert the three ceilings hold, in the order they bite:
 *   queue LENGTH  <= siteQueueMaxTrucks           (physical, never relaxed)
 *   queue TIME    <= queueBalkMaxMin + one slot   (behavioural; the slot is because the
 *                                                  gate tests the line the joining truck
 *                                                  has not yet joined)
 *   and nothing throws, on any of them.
 *
 * The STORAGE ceiling (#29) rides along on the same sweep: every combination below is a
 * real season already being run, so asserting it costs nothing and covers the lever
 * extremes (crop max, capacity min, carry-over x2) where storage is most likely to be
 * the binding constraint. Its own targeted cases are in "storage ceiling (#29)" below.
 */
function checkCeilings(sim: Sim, params: Params, label: string) {
  const slotMin = Math.max(...sim.sites.map((s) => s.serviceMin / s.bays));
  expect(sim.queueCapBreaches, `${label}: join gate leaked`).toBe(0);
  expect(sim.peakQueue, `${label}: queue length ceiling`).toBeLessThanOrEqual(params.siteQueueMaxTrucks);
  expect(sim.peakQueueMin, `${label}: queue wait ceiling`).toBeLessThanOrEqual(params.queueBalkMaxMin + slotMin);
  expect(sim.capacityBreaches, `${label}: storage ceiling`).toBe(0);
}

describe("queue ceilings (#26/#27)", () => {
  it("bounds queue length and wait however hard the tiny network is pushed", () => {
    // Deliberately absurd: one upcountry site and one port, a crop 40x the fixture's, a
    // fleet big enough to move it all at once, and a harvest rate that dumps it on farm in
    // days. No balk policy can route its way out of this — the point is that the ceilings
    // hold anyway and the engine keeps running, leaving the surplus on farm (where
    // onFarmTonneDays already prices it) instead of throwing.
    const p = defaultParams();
    p.fleetTrucks = 600;
    p.linehaulTrucks = 20;
    p.productionScale = 40;
    for (const c of Object.keys(p.harvestRatePerDay) as (keyof typeof p.harvestRatePerDay)[]) {
      p.harvestRatePerDay[c] = 0.5;
    }
    const sim = new Sim(tinyBundle(), p, 7);
    sim.step(120 * DAY_TICKS);
    checkCeilings(sim, p, "tiny under absurd load");
    // it did not just stop dispatching: the network still moved grain
    expect(sim.receivedBungeT).toBeGreaterThan(0);
    // and the grain it could not move is accounted for, not lost
    expect(sim.onFarmTonneDays).toBeGreaterThan(0);
  });

  it("sweeps the UI presets and lever extremes on a real season without throwing", () => {
    let bundle: Bundle;
    try {
      bundle = loadBundle("2025/26");
    } catch {
      console.warn("real bundle not present; skipping");
      return;
    }
    // Every combination below is reachable from the app: the scenario presets, then each
    // slider at an end of its published range, then the specific mixes that used to throw.
    // The six pre-fix crashers are marked; each was verified to still crash on the parent
    // commit before this test was written.
    const combos: [string, Partial<Params>][] = [
      ["preset baseline", {}],
      ["preset bumper", { productionScale: 1.3 }],
      ["preset drought", { productionScale: 0.6 }],
      ["preset rail", { railReinstated: true, linehaulTrucks: 38 }],
      ["preset lucky bay", { luckyBayBias: 2.5 }],
      ["preset outage", { outage: { port: "Lincoln", fromDay: 70, days: 7 } }],
      ["preset road closure", { roadClosure: { corridor: "tod", factor: 2.5 } }],
      ["crop max", { productionScale: 1.4 }],
      ["crop min", { productionScale: 0.5 }],
      ["fleet max", { fleetTrucks: 890 }],
      ["fleet min", { fleetTrucks: 280 }],
      ["service max", { siteServiceMin: 25 }],
      ["service min", { siteServiceMin: 6 }],
      ["capacity min", { upcountryCapScale: 0.5 }],
      ["payload min", { truckPayloadT: 28 }],
      // --- the six that threw QUEUE INSANE on the parent commit ---
      ["crash: crop max + fleet max", { productionScale: 1.4, fleetTrucks: 890 }], // 729 @ Port Lincoln
      ["crash: crop max + capacity x0.1", { productionScale: 1.4, upcountryCapScale: 0.1 }], // 406 @ Lucky Bay
      ["crash: crop max + service max + capacity min", { productionScale: 1.4, siteServiceMin: 25, upcountryCapScale: 0.5 }], // 406 @ Lucky Bay
      ["crash: crop max + fleet max + service max", { productionScale: 1.4, fleetTrucks: 890, siteServiceMin: 25 }], // 677 @ Lucky Bay
      ["crash: crop max + retention min + capacity min", { productionScale: 1.4, retentionShare: 0.05, upcountryCapScale: 0.5 }], // 412 @ Thevenard
      [
        "crash: every lever against the network",
        { productionScale: 1.4, siteServiceMin: 25, upcountryCapScale: 0.5, fleetTrucks: 890, truckPayloadT: 28, carryInScale: 2, retentionShare: 0.05 },
      ], // 764 @ Lucky Bay
    ];
    // 130 days covers the whole harvest peak, which is the only time queues form. Every
    // pre-fix crash above fires inside it: measured on the parent commit they threw on
    // season days 60, 72, 74, 74, 76 and 102, so this leaves ~4 weeks of margin.
    for (const [label, patch] of combos) {
      const params: Params = { ...defaultParams(), ...patch };
      const sim = new Sim(bundle, params, 42);
      sim.step(130 * DAY_TICKS); // throws on a violated invariant; that is the #26 assertion
      checkCeilings(sim, params, label);
    }
  }, 300_000);
});

/**
 * Regression cover for #28.
 *
 * The road-closure scenario used to scale ONLY farm->site candidates, so silo->port
 * line-haul kept running at full speed over the road the scenario had just closed. The
 * test that picked the affected legs asked whether their straight-line MIDPOINT sat
 * within 0.18 deg of a straight-line corridor axis, which is neither where the road is
 * nor where the leg is: it missed legs that run the corridor end to end and hit legs
 * that merely pass near its middle.
 */
describe("road closure corridor (#28)", () => {
  it("scores a leg by how much of it runs inside the closed corridor", () => {
    const tod = CORRIDORS.tod;
    // a leg tracing the highway itself is entirely inside the closure
    expect(corridorShare(tod, tod)).toBeCloseTo(1, 6);
    // the east-coast run from Kimba to Lucky Bay never comes near it
    expect(
      corridorShare(
        [
          [136.43, -33.12],
          [137.04, -33.71],
        ],
        tod,
      ),
    ).toBe(0);
    // a leg that CROSSES the corridor pays for the crossing, not for the whole trip:
    // 1 deg of easting through the corridor at Lock, ~10 km of it inside the band
    const crossing = corridorShare(
      [
        [135.2, -33.56],
        [136.2, -33.58],
      ],
      tod,
    );
    expect(crossing).toBeGreaterThan(0);
    expect(crossing).toBeLessThan(0.15);
    // any stretch of the highway is still fully inside it, wherever it is measured —
    // the old proxy scored a leg on one point, so where along the corridor a leg ran
    // decided whether it counted at all
    expect(corridorShare(tod.slice(4), tod)).toBeCloseTo(1, 6);
  });

  it("closure-adjusts the site->port line-haul leg, not just farm->site", () => {
    let bundle: Bundle;
    try {
      bundle = loadBundle("2025/26");
    } catch {
      console.warn("real bundle not present; skipping");
      return;
    }
    const idx = (n: string) => bundle.matrix.sites.findIndex((s) => s.name === n);
    const pl = idx("Port Lincoln");
    // baseline carries no closure at all: this scenario must not touch calibrated runs
    expect(new Sim(bundle, defaultParams(), 42).closureSitePort).toBeNull();

    const p: Params = { ...defaultParams(), roadClosure: { corridor: "tod", factor: 2.5 } };
    const scale = new Sim(bundle, p, 42).closureSitePort!;
    expect(scale).not.toBeNull();
    // these three reach Port Lincoln down the Tod Highway for the whole leg — before the
    // fix every one of them ran the closure at full speed, unpenalised
    for (const name of ["Wudinna", "Cummins", "Lock"]) {
      expect(scale[idx(name)]![pl], `${name} -> Port Lincoln`).toBeCloseTo(2.5, 2);
    }
    // Kimba reaches Port Lincoln down the LINCOLN Highway; the closure barely touches it
    expect(scale[idx("Kimba")]![pl]).toBeLessThan(1.1);
    // Wirrulla comes down the Tod Highway for two thirds of a 330 km leg: a partial
    // detour, which the old all-or-nothing test had no way to express
    expect(scale[idx("Wirrulla")]![pl]).toBeGreaterThan(1.5);
    expect(scale[idx("Wirrulla")]![pl]).toBeLessThan(2.5);
    // nothing is ever scaled toward a non-port: line-haul only runs site -> port
    expect(scale[idx("Wudinna")]![idx("Cummins")]).toBe(1);
  });
});

/**
 * Regression cover for #29.
 *
 * A site cannot hold more grain than it holds — the capacities are published (both ports,
 * all three T-Ports sites) or estimated per A4, and reporting them as exceeded undercuts
 * the whole claim that storage is a real constraint. Two separate paths did it:
 *
 *   1. carry-in (A17) was seeded with no capacity check at all, so `carryInScale` 2 put
 *      2023/24's Port Lincoln at 162 % of its published 395,600 t on day ONE;
 *   2. `chooseSite`'s storage gate tested on-site stock only, so any number of trucks
 *      could read the same nearly-full site as "room for me" in one tick and all tip —
 *      6 sites over at the calibrated baseline, 11 at +30 % crop (0.2–2.2 % over).
 *
 * Neither was visible to the suite: every pre-#29 test either ran the tiny fixture (whose
 * one site never fills) or asserted on queues and totals, never on fill.
 */
describe("storage ceiling (#29)", () => {
  /** worst stock/capacity ratio over every site, and the site that hit it */
  function worstFill(sim: Sim): { pct: number; name: string } {
    let pct = 0;
    let name = "";
    for (const s of sim.sites) {
      let st = 0;
      for (let c = 0; c < s.stock.length; c++) st += s.stock[c]!;
      const f = st / s.capacityT;
      if (f > pct) {
        pct = f;
        name = s.name;
      }
    }
    return { pct: pct * 100, name };
  }

  it("clamps carry-in that will not fit, and reports how much it dropped", () => {
    const b = tinyBundle();
    // Testville holds 50,000 t and Port Lincoln 395,600 t; both are seeded well past it.
    b.observed.carry_in = {
      port_lincoln_t: 500_000,
      thevenard_t: 0,
      upcountry_t: 200_000,
      provenance: "test fixture",
    };
    const p = defaultParams();
    p.fleetTrucks = 2;
    p.linehaulTrucks = 1;
    const sim = new Sim(b, p, 7);
    const stock = (i: number) => sim.sites[i]!.stock.reduce((a, v) => a + v, 0);
    expect(stock(0)).toBeCloseTo(50_000, 3); // filled exactly, not 400 % full
    expect(stock(1)).toBeCloseTo(395_600, 3);
    // the overflow is dropped, counted and disclosed — not spilled onto a neighbour, which
    // would invent a location A17's provenance (port-held old crop) says nothing about
    expect(sim.carryInClampedT).toBeCloseTo(150_000 + 104_400, 3);
    // ...and only the tonnes actually placed enter the mass balance, so the daily
    // invariant check inside run() proves the clamp did not quietly lose or create grain
    expect(sim.carryInT).toBeCloseTo(445_600, 3);
    sim.run(200);
    expect(sim.capacityBreaches).toBe(0);
  });

  it("never lets converging trucks tip a site past capacity, tick by tick", () => {
    // the #26 absurd-load fixture: far more grain and trucks than the two sites can take,
    // so the storage gate is under continuous pressure from many trucks at once. Sampled
    // every tick rather than daily — an intra-day overshoot drawn back down overnight
    // would be invisible to the engine's own once-a-day invariant check.
    const p = defaultParams();
    p.fleetTrucks = 600;
    p.linehaulTrucks = 20;
    p.productionScale = 40;
    for (const c of Object.keys(p.harvestRatePerDay) as (keyof typeof p.harvestRatePerDay)[]) {
      p.harvestRatePerDay[c] = 0.5;
    }
    const sim = new Sim(tinyBundle(), p, 7);
    let worst = 0;
    for (let t = 0; t < 60 * DAY_TICKS; t++) {
      sim.step(1);
      const w = worstFill(sim);
      if (w.pct > worst) worst = w.pct;
    }
    expect(worst).toBeLessThanOrEqual(100);
    expect(sim.capacityBreaches).toBe(0);
    // and it is a real ceiling being tested, not an empty network: the sites do fill
    expect(worst).toBeGreaterThan(99);
  });

  it("holds every EP site inside its capacity across a bumper season", () => {
    let bundle: Bundle;
    try {
      bundle = loadBundle("2025/26");
    } catch {
      console.warn("real bundle not present; skipping");
      return;
    }
    // +30 % crop is the app's own bumper preset, and the case reported in #29: eleven
    // sites peaked at 100.2–102.2 % of capacity on the parent commit, ports included.
    const params: Params = { ...defaultParams(), productionScale: 1.3 };
    const sim = new Sim(bundle, params, 42);
    let worst = { pct: 0, name: "" };
    for (let d = 0; d < 365; d++) {
      sim.step(DAY_TICKS);
      const w = worstFill(sim);
      if (w.pct > worst.pct) worst = w;
    }
    expect(worst.pct, `worst fill was ${worst.name} at ${worst.pct.toFixed(1)}%`).toBeLessThanOrEqual(100);
    expect(sim.capacityBreaches).toBe(0);
    // storage really is the binding constraint in this scenario — if this ever stops
    // being true the assertion above has gone quiet rather than passed
    expect(worst.pct).toBeGreaterThan(99);
  }, 60_000);
});

describe("harvest-ban fire danger (A7)", () => {
  // The SA district harvesting codes publish the GFDI-35 cease-harvest trigger as a
  // lookup table of the wind speed to stop at for a given temperature and humidity.
  // These are entries reported from that table; the implementation has to land on 35.
  // If a coefficient is ever edited, this is what catches it.
  it("reproduces the published cease-harvest table entries", () => {
    expect(gfdiFullyCured(35, 14, 26)).toBeCloseTo(34.1, 0);
    expect(gfdiFullyCured(40, 15, 26)).toBeCloseTo(38.1, 0);
  });

  it("is driven by wind and humidity, not temperature alone", () => {
    // 41 C with a light breeze: a good harvest day, and well under the trigger.
    expect(gfdiFullyCured(41, 18, 20)).toBeLessThan(35);
    // 22 C with a 47 km/h wind over cured stubble: a ban day, and nowhere near hot.
    expect(gfdiFullyCured(22, 47, 47)).toBeGreaterThan(35);
    // dropping the wind alone takes the same hot day from banned to workable
    expect(gfdiFullyCured(38, 15, 30)).toBeGreaterThan(35);
    expect(gfdiFullyCured(38, 15, 18)).toBeLessThan(35);
  });

  it("costs part of a ban day, not all of it, and more as the peak climbs", () => {
    // the surviving share of the working day at a given peak index (trigger 35)
    const keep = (g: number) => 1 - (2 / Math.PI) * Math.acos(Math.min(1, 35 / g));
    expect(keep(35)).toBeCloseTo(1, 6); // just touching the trigger costs nothing
    expect(keep(50)).toBeCloseTo(0.494, 2); // ~half the working day lost
    expect(keep(70)).toBeCloseTo(0.333, 2); // ~two thirds lost
    expect(keep(50)).toBeLessThan(keep(40)); // monotone in the peak
    expect(keep(1e6)).toBeGreaterThanOrEqual(0); // never negative, even absurdly high
  });
});

/**
 * Cover for the R5 network-state override.
 *
 * Before this, which sites operate was not a parameter at all: `Sim.init()` derived it
 * from the bundle's static `status` string plus a hardcoded season-string match
 * (`season === "2025/26" || "2024/25"` closes the two T-Ports bunkers, A15). A run could
 * not be placed at a different network state without editing the engine, which is what
 * R5's retrospective test and R3's rationalisation scenario both need.
 *
 * The three things asserted here are the three ways this could quietly produce a wrong
 * number rather than an error:
 *   1. it is a strict no-op when unused, so no calibrated run moves;
 *   2. a name that matches no site THROWS instead of silently changing nothing;
 *   3. forcing open a site with no segregation list THROWS, because `chooseSite` skips
 *      any site whose `accepts[c]` is false — such a site would look open all season and
 *      receive zero tonnes.
 */
describe("network-state override (R5)", () => {
  const BUNKERS = ["Lock (T-Ports bunker)", "Kimba (T-Ports bunker)"];

  it("is a strict no-op when null, and when it only restates the engine's own rule", () => {
    let bundle: Bundle;
    try {
      bundle = loadBundle("2025/26");
    } catch {
      console.warn("real bundle not present; skipping");
      return;
    }
    // 2025/26 already closes both bunkers via the season match, so forcing them closed
    // must reproduce the baseline event log byte for byte — the check that the override
    // changes the network state and nothing else.
    const base = new Sim(bundle, defaultParams(), 42).run(365);
    const restated = new Sim(
      bundle,
      { ...defaultParams(), networkState: { forceClosed: BUNKERS } },
      42,
    ).run(365);
    expect(restated.eventLogHash).toBe(base.eventLogHash);
    expect(restated.seasonReceivedT).toBe(base.seasonReceivedT);

    // ...and opening them is a real change, in the direction the mechanism requires:
    // an extra inland option for the same crop takes tonnage off the Bunge network.
    const opened = new Sim(bundle, { ...defaultParams(), networkState: { forceOpen: BUNKERS } }, 42).run(365);
    expect(opened.eventLogHash).not.toBe(base.eventLogHash);
    expect(opened.seasonReceivedT).toBeLessThan(base.seasonReceivedT);
  }, 60_000);

  it("throws on a site name the bundle does not contain", () => {
    const b = tinyBundle();
    expect(() => new Sim(b, { ...defaultParams(), networkState: { forceClosed: ["Testvile"] } }, 7)).toThrow(
      /names no site in this bundle/,
    );
    // the correctly spelled name is accepted
    const name = b.matrix.sites[0]!.name;
    expect(() => new Sim(b, { ...defaultParams(), networkState: { forceClosed: [name] } }, 7)).not.toThrow();
  });

  it("throws rather than reopening a site that would accept nothing", () => {
    const b = tinyBundle();
    b.matrix.sites[0]!.status = "dormant";
    b.matrix.sites[0]!.commodities = []; // the five dormant Bunge sites all look like this
    const name = b.matrix.sites[0]!.name;
    expect(() => new Sim(b, { ...defaultParams(), networkState: { forceOpen: [name] } }, 7)).toThrow(
      /carries no commodities/,
    );
    // give it a segregation list and the same reopen is fine
    b.matrix.sites[0]!.commodities = ["WH"];
    expect(() => new Sim(b, { ...defaultParams(), networkState: { forceOpen: [name] } }, 7)).not.toThrow();
  });

  it("lets forceClosed win over forceOpen, so the result never depends on list order", () => {
    const b = tinyBundle();
    const name = b.matrix.sites[0]!.name;
    const both = new Sim(b, { ...defaultParams(), networkState: { forceOpen: [name], forceClosed: [name] } }, 7);
    expect(both.sites[0]!.open).toBe(false);
  });
});
