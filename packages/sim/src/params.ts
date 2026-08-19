import { Params } from "./types";

/**
 * Default parameter set. The ~10 starred values are the calibration free parameters
 * (fitted headless against data/CALIBRATION.md targets); the rest are scenario switches.
 * Assumption ids reference data/ASSUMPTIONS.md.
 */
export function defaultParams(): Params {
  return {
    fleetTrucks: 450, // * regional farm-truck fleet at harvest peak
    linehaulTrucks: 40, // * site->port outloading fleet
    truckPayloadT: 38, // A1 blended net payload
    harvestRatePerDay: {
      // * per-commodity daily harvest fraction of a parcel (good-weather day)
      wheat: 0.075,
      barley: 0.09,
      canola: 0.075,
      lentils: 0.1,
      beans: 0.08,
      other: 0.08,
    },
    maturityDayOffset: {
      // days after 1 Oct when harvest can start (lentils/barley lead, wheat peak)
      lentils: 22,
      barley: 26,
      other: 34,
      beans: 40,
      canola: 46,
      wheat: 48,
    },
    districtStartOffset: { WEP: -8, EEP: 0, LEP: 8 }, // far west starts first
    harvestRampDays: 10,
    choiceBeta: 1.8, // * Huff travel-time decay
    portAttractBias: 1.6, // * direct-to-port pull (A9)
    retentionShare: 0.18, // * on-farm retention + non-network channels
    luckyBayBias: 1.0, // * T-Ports market-share multiplier
    productionScale: 1.0,
    railReinstated: false,
    outage: null,
    roadClosure: null,
  };
}
