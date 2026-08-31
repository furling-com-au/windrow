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
    fleetTrucks: 691, // * regional farm-truck fleet at harvest peak (weakly identified: see A2)
    linehaulTrucks: 64, // * site->port outloading fleet
    truckPayloadT: 38, // A1 blended net payload (farm -> site)
    linehaulPayloadT: 45, // A1 line-haul net payload; anchored to Viterra's 2019 rail
    //   replacement statement (48 loaded trucks/day ~ 2,100-2,200 t/day => ~45 t/load).
    //   SA permits far heavier road trains (Type 2, up to 142.28 t HML) - see data/trucks.md.
    harvestRatePerDay: {
      // * per-commodity daily harvest fraction of a parcel (good-weather day); prior
      //   ratios scaled by the fitted rateScale 0.881
      wheat: 0.033428,
      barley: 0.040151,
      canola: 0.033428,
      lentils: 0.044591,
      beans: 0.035648,
      other: 0.035648,
    },
    maturityDayOffset: {
      // * days after 1 Oct when harvest can start (prior - fitted matShift of 4 d);
      //   a per-season spring-dryness shift is applied on top (engine, A7)
      lentils: 10,
      barley: 14,
      other: 22,
      beans: 28,
      canola: 34,
      wheat: 36,
    },
    districtStartOffset: { WEP: -8, EEP: 0, LEP: 8 }, // far west starts first
    harvestRampDays: 5, // *
    siteServiceMin: 12, // A2 (assumed)
    travelTimeScale: 1.0, // A5 speeds as built into the matrix
    rainStopMm: 5, // A7 (assumed threshold)
    carryInScale: 1.0, // A17 as measured from Oct-Nov shipments
    upcountryCapScale: 1.0, // A4 estimated capacities as allocated (see sites.geojson)
    choiceBeta: 2.06, // * Huff travel-time decay
    choiceRadius: 2.64, // * candidate window (nearest x r + 10 min); ports always eligible
    countryBays: 4, // * A2: tipping bays per upcountry site
    portBays: 5, // * A2: tipping bays per port terminal
    queueBalkMin: 240, // A2: growers balk past ~4 h (worst reported EP turnaround)
    portAttractBias: 1.475, // * direct-to-port pull (A9)
    retentionShare: 0.1, // * on-farm retention + non-network channels
    luckyBayBias: 0.469, // * T-Ports market-share multiplier
    productionScale: 1.0,
    railReinstated: false,
    outage: null,
    roadClosure: null,
  };
}
