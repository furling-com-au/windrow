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
    fleetTrucks: 731, // * regional farm-truck fleet at harvest peak (weakly identified: see A2)
    linehaulTrucks: 60, // * site->port outloading fleet
    truckPayloadT: 38, // A1 blended net payload (farm -> site)
    linehaulPayloadT: 45, // A1 line-haul net payload; anchored to Viterra's 2019 rail
    //   replacement statement (48 loaded trucks/day ~ 2,100-2,200 t/day => ~45 t/load).
    //   SA permits far heavier road trains (Type 2, up to 142.28 t HML) - see data/trucks.md.
    harvestRatePerDay: {
      // * per-commodity daily harvest fraction of a parcel (good-weather day); prior
      //   ratios scaled by the fitted rateScale 0.723
      wheat: 0.03794,
      barley: 0.04557,
      canola: 0.03794,
      lentils: 0.05061,
      beans: 0.04046,
      other: 0.04046,
    },
    maturityDayOffset: {
      // * days after 1 Oct when harvest can start (prior - fitted matShift of 4 d);
      //   a per-season spring-dryness shift is applied on top (engine, A7)
      lentils: 14,
      barley: 18,
      other: 26,
      beans: 32,
      canola: 38,
      wheat: 40,
    },
    districtStartOffset: { WEP: -8, EEP: 0, LEP: 8 }, // far west starts first
    harvestRampDays: 8.475, // *
    siteServiceMin: 12, // A2 (assumed)
    travelTimeScale: 1.0, // A5 speeds as built into the matrix
    rainStopMm: 5, // A7 (assumed threshold)
    carryInScale: 1.0, // A17 as measured from Oct-Nov shipments
    upcountryCapScale: 1.0, // A4 assumed capacities as-is
    choiceBeta: 2.199, // * Huff travel-time decay
    choiceRadius: 2.105, // * candidate window (nearest x r + 10 min); ports always eligible
    countryBays: 4, // * A2: tipping bays per upcountry site
    portBays: 6, // * A2: tipping bays per port terminal
    queueBalkMin: 240, // A2: growers balk past ~4 h (worst reported EP turnaround)
    portAttractBias: 0.8, // * direct-to-port pull (A9)
    retentionShare: 0.1, // * on-farm retention + non-network channels
    luckyBayBias: 0.4, // * T-Ports market-share multiplier
    productionScale: 1.0,
    railReinstated: false,
    outage: null,
    roadClosure: null,
  };
}
