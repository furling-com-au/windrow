import { describe, expect, it } from "vitest";
import { DAY_TICKS, Sim } from "../src/engine";
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
 */
function checkCeilings(sim: Sim, params: Params, label: string) {
  const slotMin = Math.max(...sim.sites.map((s) => s.serviceMin / s.bays));
  expect(sim.queueCapBreaches, `${label}: join gate leaked`).toBe(0);
  expect(sim.peakQueue, `${label}: queue length ceiling`).toBeLessThanOrEqual(params.siteQueueMaxTrucks);
  expect(sim.peakQueueMin, `${label}: queue wait ceiling`).toBeLessThanOrEqual(params.queueBalkMaxMin + slotMin);
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
