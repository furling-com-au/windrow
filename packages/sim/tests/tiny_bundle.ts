import type { Bundle } from "../src/types";

/** Hand-checkable micro scenario: 1 cluster, 1 parcel, 1 site + 1 port, 2 trucks. */
export function tinyBundle(): Bundle {
  return {
    season: "2025/26",
    parcels: [{ id: 0, lon: 135.7, lat: -34.0, district: "LEP", cropping_ha: 400, cluster_id: 0 }],
    demand: { season: "2025/26", parcels: [{ id: 0, crops: { wheat: 10000 } }] },
    matrix: {
      sites: [
        { id: 0, name: "Testville", role: "upcountry", operator: "Bunge (ex-Viterra)", status: "active_2025_26", lon: 135.8, lat: -34.0, capacity_t: 50000, commodities: ["WH", "BA", "CA"] },
        { id: 1, name: "Port Lincoln", role: "port", operator: "Bunge (ex-Viterra)", status: "active_2025_26", lon: 135.87, lat: -34.72, capacity_t: 395600, commodities: ["WH", "BA", "CA"] },
      ],
      site_minutes: [
        [0, 60],
        [60, 0],
      ],
      clusters: [{ id: 0, lon: 135.7, lat: -34.0, cropping_ha: 400, district: "LEP", n_parcels: 1 }],
      cluster_site_minutes: { "0": { "0": 15, "1": 70 } },
    },
    vessels: {
      season: "2025/26",
      port_lincoln_berth_visits: [{ craft_id: 1, arrive: "2025-12-10T00:00:00", berth_hours: 40, est_cargo_t: 6000 }],
      lucky_bay_anchorage_stays: [],
      thevenard_berth_visits_all_cargo: [],
    },
    weather: {
      season: "2025/26",
      districts: {
        WEP: { start: "2025-09-01", rain_mm: new Array(370).fill(0), tmax_c: new Array(370).fill(25), rh_min_pct: new Array(370).fill(30), wind_max_kmh: new Array(370).fill(20) },
        LEP: { start: "2025-09-01", rain_mm: new Array(370).fill(0), tmax_c: new Array(370).fill(25), rh_min_pct: new Array(370).fill(30), wind_max_kmh: new Array(370).fill(20) },
        EEP: { start: "2025-09-01", rain_mm: new Array(370).fill(0), tmax_c: new Array(370).fill(25), rh_min_pct: new Array(370).fill(30), wind_max_kmh: new Array(370).fill(20) },
      },
    },
    observed: {
      season: "2025/26",
      first_delivery: "2025-10-13",
      weekly_receivals: [
        { week_ending: "2025-11-16", fortnight: false, western: { weekly_t: 100, cum_t: 100 } },
        { week_ending: "2026-01-04", fortnight: false, western: { weekly_t: 100, cum_t: 200 } },
      ],
      port_lincoln_shipments_monthly: [],
      district_production_t: { LEP: 10000 },
    },
  };
}
