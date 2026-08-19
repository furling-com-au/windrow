/**
 * Live narrator: turns the current sim state into one plain-English sentence so a
 * first-time viewer always knows what they're looking at. Pure function of state —
 * deterministic, no randomness.
 */
import type { BundleSite, ObservedFile, Snapshot } from "@windrow/sim";

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

function when(dateIso: string): string {
  const d = new Date(dateIso + "T00:00:00Z");
  const day = d.getUTCDate();
  const part = day <= 10 ? "Early" : day <= 20 ? "Mid" : "Late";
  return `${part} ${MONTHS[d.getUTCMonth()]}`;
}

export function narrate(
  snap: Snapshot,
  observed: ObservedFile | null,
  sites: BundleSite[],
  dailyReceived: number[],
): string {
  const day = snap.day;
  const t = when(snap.dateIso);

  // context signals
  const recent = snap.kpi.receivedT - (dailyReceived[Math.max(0, day - 7)] ?? 0); // ~week of deliveries
  const maxWeekObs = Math.max(200000, ...(observed?.weekly_receivals ?? []).map((w) => w.western?.weekly_t ?? 0));
  const rainNow = (observed?.annotations ?? []).some((a) => a.kind === "rain" && Math.abs(a.day - day) <= 1);
  const berthed = snap.vessels.find((v) => v.state === 2);
  const port = berthed ? sites[berthed.port] : null;
  const shipClause = berthed
    ? ` ${berthed.name ? `The ${berthed.name}` : "A ship"} is loading ${Math.round(berthed.targetT / 1000)},000 t at ${port?.name.replace(" (T-Ports port)", "") ?? "port"}.`
    : "";
  const started = snap.kpi.receivedT > 3000;
  const harvestOver = day > 110 && recent < 8000 && snap.kpi.harvestedT > 100000;

  if (!started) {
    if (rainNow) return `${t}: rain over the paddocks — harvest is waiting on the weather.${shipClause}`;
    return `${t}: paddocks are ripening. Harvest starts in the far west around mid-October — the map will come alive then.${shipClause}`;
  }
  if (harvestOver) {
    if (day > 240)
      return `${t}: the quiet months. The last of the crop ships out to the world before it all begins again in October.${shipClause}`;
    return `${t}: harvest is done — ${(snap.kpi.receivedT / 1e6).toFixed(1)} million tonnes delivered. Silos now empty out through the port, ship by ship.${shipClause}`;
  }
  if (rainNow) {
    return `${t}: rain has pulled headers out of the paddocks — watch this week's deliveries dip.${shipClause}`;
  }
  if (recent > maxWeekObs * 0.55) {
    const q = snap.kpi.queueTrucks;
    return `${t}: peak harvest. Grain is pouring in${q > 30 ? ` — ${q} trucks are queued at silos right now` : ""}.${shipClause}`;
  }
  if (snap.kpi.receivedT < 120000) {
    return `${t}: harvest is underway — the first loads (lentils and barley) are reaching silos in the far west.${shipClause}`;
  }
  if (day > 75 && recent < maxWeekObs * 0.25) {
    return `${t}: harvest is winding down — most paddocks are stripped and trucks shift to carting silo stocks to port.${shipClause}`;
  }
  return `${t}: harvest is building. Headers run all day; trucks shuttle grain from paddock to the nearest silo.${shipClause}`;
}
