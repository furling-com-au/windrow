/**
 * Independent audit of the fitted farm-truck fleet (A1 payload x fleetTrucks).
 *
 * Reports, per season: observed peak-week/day receivals, the loads/day those imply at
 * the assumed payload, and what the SIMULATED fleet actually does (trips per truck per
 * active day, busy-time utilisation, cycle-time breakdown). The point is to check
 * whether 589 trucks is a physically sensible fleet or just a fitted multiplier.
 *
 * Run: npx tsx packages/sim/scripts/truck_audit.ts
 */
import { DAY_TICKS, Sim, TICK_MIN } from "../src/engine";
import { defaultParams } from "../src/params";
import { loadBundle } from "./load_bundle";

const SEASONS = ["2023/24", "2025/26"];

for (const season of SEASONS) {
  const bundle = loadBundle(season);
  const p = defaultParams();

  // ---- observed side: peak week/day from the published weekly receivals ----
  const wk = bundle.observed.weekly_receivals ?? [];
  let peakWeekT = 0;
  let prev = 0;
  for (const w of wk) {
    const cum = w.western?.cum_t ?? 0;
    const inc = cum - prev;
    if (inc > peakWeekT) peakWeekT = inc;
    prev = cum;
  }
  const seasonT = prev;

  // ---- simulated side: instrument the fleet ----
  const sim = new Sim(bundle, p, 42) as any;
  const farmTrucks: any[] = sim.trucks.filter((t: any) => t.kind === 0);
  const nFarm = farmTrucks.length;

  // per-truck: ticks spent non-idle, and completed trips (count TIP completions)
  const busyTicks = new Float64Array(nFarm);
  const trips = new Float64Array(nFarm);
  const idxOf = new Map<number, number>();
  farmTrucks.forEach((t, i) => idxOf.set(t.id, i));
  const prevState = new Int8Array(nFarm);

  let peakDayT = 0;
  let dayStartRec = 0;
  const dailyT: number[] = [];
  const dailyActiveTrucks: number[] = [];

  const totalTicks = 365 * DAY_TICKS;
  for (let d = 0; d < 365; d++) {
    const tripsAtDayStart = trips.slice();
    for (let k = 0; k < DAY_TICKS; k++) {
      sim.step(1);
      for (const t of sim.trucks) {
        if (t.kind !== 0) continue;
        const i = idxOf.get(t.id)!;
        if (t.state !== 0) busyTicks[i]!++;
        // TIP(4) -> RETURN(5) transition marks one completed delivery
        if (prevState[i] === 4 && t.state === 5) trips[i]!++;
        prevState[i] = t.state;
      }
    }
    const rec = sim.receivedBungeT + sim.receivedLbT;
    const dayT = rec - dayStartRec;
    dayStartRec = rec;
    dailyT.push(dayT);
    if (dayT > peakDayT) peakDayT = dayT;
    let active = 0;
    for (let i = 0; i < nFarm; i++) if (trips[i]! > tripsAtDayStart[i]!) active++;
    dailyActiveTrucks.push(active);
  }

  const totalTrips = trips.reduce((a, b) => a + b, 0);
  const totalBusyTicks = busyTicks.reduce((a, b) => a + b, 0);
  // "active days" = days where the fleet moved meaningful tonnage
  const activeDays = dailyT.filter((t) => t > 1000).length;
  const peakIdx = dailyT.indexOf(peakDayT);
  const peakActive = dailyActiveTrucks[peakIdx] ?? 0;

  // peak-day trips: recompute over the peak day window
  const tripsPerTruckPeak = peakDayT / p.truckPayloadT / Math.max(1, peakActive);

  console.log(`\n=== ${season} ===`);
  console.log(`OBSERVED  season ${(seasonT / 1e6).toFixed(2)} Mt · peak week ${Math.round(peakWeekT).toLocaleString()} t`);
  console.log(`          peak week => ${Math.round(peakWeekT / 7).toLocaleString()} t/day => ${Math.round(peakWeekT / 7 / p.truckPayloadT).toLocaleString()} loads/day at ${p.truckPayloadT} t`);
  console.log(`SIM       fleet ${nFarm} farm trucks (+${p.linehaulTrucks} line-haul)`);
  console.log(`          season delivered ${((sim.receivedBungeT + sim.receivedLbT) / 1e6).toFixed(2)} Mt in ${Math.round(totalTrips).toLocaleString()} trips`);
  console.log(`          peak sim day ${Math.round(peakDayT).toLocaleString()} t · ${peakActive} trucks moved · ${tripsPerTruckPeak.toFixed(1)} trips/truck that day`);
  console.log(`          mean trips/truck/active-day (${activeDays} active days): ${(totalTrips / nFarm / Math.max(1, activeDays)).toFixed(2)}`);
  console.log(`          fleet busy-time utilisation over active days: ${((totalBusyTicks / (nFarm * activeDays * DAY_TICKS)) * 100).toFixed(1)}% of the 24 h day, ${((totalBusyTicks / (nFarm * activeDays * DAY_TICKS)) * 200).toFixed(1)}% of the 12 h receival window`);
  console.log(`          implied mean cycle time: ${((totalBusyTicks * TICK_MIN) / Math.max(1, totalTrips)).toFixed(0)} min/trip`);
  void totalTicks;
}
