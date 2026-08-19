/** Node-side bundle loader (the browser fetches the same files). */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Bundle } from "../src/types";

export function loadBundle(season: string, dataDir?: string): Bundle {
  const dir = dataDir ?? join(import.meta.dirname, "..", "..", "..", "app", "public", "data");
  const sid = season.replace("/", "-");
  const j = (name: string) => JSON.parse(readFileSync(join(dir, name), "utf-8"));
  let vessels = null;
  try {
    vessels = j(`vessels_${sid}.json`);
  } catch {
    vessels = null;
  }
  return {
    season,
    parcels: j("parcels.json").parcels,
    demand: j(`demand_${sid}.json`),
    matrix: j("matrix.json"),
    vessels,
    weather: j(`weather_${sid}.json`),
    observed: j(`observed_${sid}.json`),
  };
}
