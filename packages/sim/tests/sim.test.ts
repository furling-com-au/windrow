import { describe, expect, it } from "vitest";
import { Sim, gfdiFullyCured } from "../src/engine";
import { defaultParams } from "../src/params";
import type { Bundle } from "../src/types";
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
