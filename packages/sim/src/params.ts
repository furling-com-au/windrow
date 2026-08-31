import type { Params } from "./types";

/**
 * Default parameter set. The 12 starred values are the calibration free parameters
 * (fitted headless against data/CALIBRATION.md targets); the rest are scenario switches.
 * `harvestRatePerDay` and `maturityDayOffset` each carry ONE knob (a scale and a shift
 * over a fixed prior), so twelve knobs cover more than twelve numbers here.
 * Assumption ids reference data/ASSUMPTIONS.md.
 */
export function defaultParams(): Params {
  // Values marked * were FITTED by packages/sim/scripts/calibrate.ts (search log in
  // docs/calibration_search.json; fitted on 2023/24 + 2025/26, 2024/25 held out).
  return {
    fleetTrucks: 555, // * regional farm-truck fleet at harvest peak (weakly identified: see A2)
    linehaulTrucks: 57, // * site->port outloading fleet
    truckPayloadT: 38, // A1 blended net payload (farm -> site)
    linehaulPayloadT: 45, // A1 line-haul net payload; anchored to Viterra's 2019 rail
    //   replacement statement (48 loaded trucks/day ~ 2,100-2,200 t/day => ~45 t/load).
    //   SA permits far heavier road trains (Type 2, up to 142.28 t HML) - see data/trucks.md.
    harvestRatePerDay: {
      // * per-commodity daily harvest fraction of a parcel (good-weather day); prior
      //   ratios scaled by the fitted rateScale 0.818
      wheat: 0.027343,
      barley: 0.032842,
      canola: 0.027343,
      lentils: 0.036474,
      beans: 0.029159,
      other: 0.029159,
    },
    maturityDayOffset: {
      // * days after 1 Oct when harvest can start (prior + fitted matShift of -7.4 d);
      //   a per-season spring-dryness shift is applied on top (engine, A7)
      lentils: 2.6,
      barley: 6.6,
      other: 14.6,
      beans: 20.6,
      canola: 26.6,
      wheat: 28.6,
    },
    districtStartOffset: { WEP: -8, EEP: 0, LEP: 8 }, // far west starts first
    harvestRampDays: 10.32, // *
    siteServiceMin: 12, // A2 (assumed)
    travelTimeScale: 1.0, // A5 speeds as built into the matrix
    rainStopMm: 5, // A7 (assumed threshold)
    carryInScale: 1.0, // A17 as measured from Oct-Nov shipments
    upcountryCapScale: 1.0, // A4 estimated capacities as allocated (see sites.geojson)
    choiceBeta: 2.806, // * Huff travel-time decay
    choiceRadius: 2.579, // * candidate window (nearest x r + 10 min); ports always eligible
    countryBays: 4, // * A2: tipping bays per upcountry site
    portBays: 6, // * A2: tipping bays per port terminal
    queueBalkMin: 240, // A2: growers balk past ~4 h (worst reported EP turnaround)
    queueBalkMaxMin: 720, // A2: ...and past one full receival day (07:00-19:00) they stop
    //   carting altogether and the load stays in the field bin (#27)
    siteQueueMaxTrucks: 250, // A2/#26: physical stop — ~5 km of stationary road train
    portAttractBias: 2.213, // * direct-to-port pull (A9)
    retentionShare: 0.0553, // * on-farm retention + non-network channels (A24; trades off
    //   against luckyBayBias one-for-one and is not separately identified - see A24)
    luckyBayBias: 0.885, // * T-Ports market-share multiplier
    productionScale: 1.0,
    railReinstated: false,
    outage: null,
    roadClosure: null,
  };
}
