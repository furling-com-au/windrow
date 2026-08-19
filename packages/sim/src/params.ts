import type { Params } from "./types";

/**
 * Default parameter set. The ~10 starred values are the calibration free parameters
 * (fitted headless against data/CALIBRATION.md targets); the rest are scenario switches.
 * Assumption ids reference data/ASSUMPTIONS.md.
 */
export function defaultParams(): Params {
  // Values marked * were FITTED by packages/sim/scripts/calibrate.ts (search log in
  // docs/calibration_search.json; fitted on 2023/24 + 2025/26, 2024/25 held out).
  return {
    fleetTrucks: 589, // * regional farm-truck fleet at harvest peak
    linehaulTrucks: 48, // * site->port outloading fleet
    truckPayloadT: 38, // A1 blended net payload
    harvestRatePerDay: {
      // * per-commodity daily harvest fraction of a parcel (good-weather day); prior
      //   ratios scaled by the fitted rateScale 0.723
      wheat: 0.0542,
      barley: 0.0651,
      canola: 0.0542,
      lentils: 0.0723,
      beans: 0.0578,
      other: 0.0578,
    },
    maturityDayOffset: {
      // * days after 1 Oct when harvest can start (prior - fitted matShift of 4 d);
      //   a per-season spring-dryness shift is applied on top (engine, A7)
      lentils: 18,
      barley: 22,
      other: 30,
      beans: 36,
      canola: 42,
      wheat: 44,
    },
    districtStartOffset: { WEP: -8, EEP: 0, LEP: 8 }, // far west starts first
    harvestRampDays: 7, // *
    choiceBeta: 1.965, // * Huff travel-time decay
    portAttractBias: 0.8, // * direct-to-port pull (A9)
    retentionShare: 0.1, // * on-farm retention + non-network channels
    luckyBayBias: 0.651, // * T-Ports market-share multiplier
    productionScale: 1.0,
    railReinstated: false,
    outage: null,
    roadClosure: null,
  };
}
