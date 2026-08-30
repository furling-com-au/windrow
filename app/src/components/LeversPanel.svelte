<script lang="ts">
  import { CASH_BIDS, FARMGATE_PER_T, biasToPremiumPerT, fmtMoney } from "../lib/economics";
  import { DEFAULT_ASSUMP, DEFAULT_ECON, DEFAULT_LEVERS, FLEET_MAX, FLEET_MIN, SCENARIOS, app } from "../state.svelte";

  let showAssump = $state(false);

  function setA<K extends keyof typeof app.assump>(k: K, v: (typeof app.assump)[K]) {
    app.assump = { ...app.assump, [k]: v };
    onchange();
  }
  function setE<K extends keyof typeof app.econ>(k: K, v: (typeof app.econ)[K]) {
    app.econ = { ...app.econ, [k]: v }; // display-only: no re-run needed
  }
  function resetAssump() {
    app.assump = { ...DEFAULT_ASSUMP };
    app.econ = { ...DEFAULT_ECON };
    onchange();
  }

  let { onchange }: { onchange: () => void } = $props();

  function set<K extends keyof typeof app.levers>(k: K, v: (typeof app.levers)[K]) {
    app.levers = { ...app.levers, [k]: v };
    app.scenario = "custom";
    onchange();
  }

  function reset() {
    app.levers = { ...DEFAULT_LEVERS };
    app.scenario = "baseline";
    onchange();
  }

  let story = $derived(
    SCENARIOS.find((s) => s.id === app.scenario)?.story ??
      "Custom what-if — you moved the levers. The takeaways below compare your version of the season against the normal one.",
  );

  /** true when any assumption lever deviates from its registered default */
  let assumpDirty = $derived(
    (Object.keys(DEFAULT_ASSUMP) as (keyof typeof DEFAULT_ASSUMP)[]).some((k) => app.assump[k] !== DEFAULT_ASSUMP[k]),
  );

  // human-readable lever readouts (raw multipliers mean nothing to a reader)
  let cropMt = $derived.by(() => {
    const prod = Object.values(app.observed?.district_production_t ?? {}).reduce((a, v) => a + v, 0);
    return prod > 0 ? (prod * app.levers.productionScale) / 1e6 : null;
  });
  const strength = (v: number, normal: number): string => {
    const r = v / normal;
    if (r < 0.55) return "much weaker than reality";
    if (r < 0.85) return "weaker than reality";
    if (r <= 1.2) return "as in reality";
    if (r <= 2) return "stronger than reality";
    return "much stronger than reality";
  };
  let fleetDesc = $derived.by(() => {
    const d = app.levers.fleetTrucks / DEFAULT_LEVERS.fleetTrucks - 1;
    if (Math.abs(d) < 0.03) return "the fitted fleet (weakly identified — see About)";
    return `${Math.abs(d * 100).toFixed(0)}% ${d > 0 ? "more trucks than" : "fewer trucks than"} that estimate`;
  });

  /** one line naming exactly what differs from the modelled normal season */
  let changeSummary = $derived.by(() => {
    const l = app.levers;
    const parts: string[] = [];
    if (l.productionScale !== 1) parts.push(`crop at ${Math.round(l.productionScale * 100)}%`);
    if (Math.abs(l.fleetTrucks - DEFAULT_LEVERS.fleetTrucks) > 15)
      parts.push(`${l.fleetTrucks > DEFAULT_LEVERS.fleetTrucks ? "more" : "fewer"} trucks (${Math.round(l.fleetTrucks)})`);
    if (l.luckyBayBias / DEFAULT_LEVERS.luckyBayBias > 1.2) parts.push("Lucky Bay pull stronger");
    if (l.luckyBayBias / DEFAULT_LEVERS.luckyBayBias < 0.85) parts.push("Lucky Bay pull weaker");
    if (l.portAttractBias / DEFAULT_LEVERS.portAttractBias > 1.2) parts.push("more direct-to-port carting");
    if (l.portAttractBias / DEFAULT_LEVERS.portAttractBias < 0.85) parts.push("less direct-to-port carting");
    if (l.rail) parts.push("trains running");
    if (l.outage) parts.push("Port Lincoln closed 1 wk (mid-Dec)");
    if (l.roadClosure) parts.push("Tod Hwy closed");
    const a = app.assump;
    if (a.payloadT !== DEFAULT_ASSUMP.payloadT) parts.push(`farm payload ${a.payloadT} t`);
    if (a.lhPayloadT !== DEFAULT_ASSUMP.lhPayloadT) parts.push(`silo→port load ${a.lhPayloadT} t`);
    if (a.serviceMin !== DEFAULT_ASSUMP.serviceMin) parts.push(`unload ${a.serviceMin} min`);
    if (a.travelScale !== DEFAULT_ASSUMP.travelScale) parts.push(`travel ×${a.travelScale.toFixed(2)}`);
    if (a.rainStopMm !== DEFAULT_ASSUMP.rainStopMm) parts.push(`rain stops harvest at ${a.rainStopMm} mm`);
    if (a.retention !== DEFAULT_ASSUMP.retention) parts.push(`${Math.round(a.retention * 100)}% kept on farm`);
    if (a.carryInScale !== DEFAULT_ASSUMP.carryInScale) parts.push(`carry-over ×${a.carryInScale.toFixed(1)}`);
    if (a.capScale !== DEFAULT_ASSUMP.capScale) parts.push(`silo capacity ×${a.capScale.toFixed(1)}`);
    return parts.join(" · ");
  });

  /** Advanced mode: a FIXED table — same rows every frame, values change, nothing pops
   *  in or out. Quiet rows are dimmed as "≈ no change" instead of disappearing. */
  interface Row {
    label: string;
    val: string;
    money?: string;
    dim: boolean;
    dir: "up" | "down" | "flat";
    goodWhenUp: boolean;
    tip?: string;
  }

  const colorClass = (dir: "up" | "down" | "flat", goodWhenUp: boolean): string => {
    if (dir === "flat") return "flat";
    return (dir === "up") === goodWhenUp ? "up" : "down";
  };

  const ROW_TIPS: Record<string, string> = {
    "Grain delivered": "Grain farmers delivered into the main network's silos and ports this season, vs the modelled normal season at the same date.",
    "→ to Lucky Bay instead": "Deliveries that went to the competing T-Ports Lucky Bay system — grain that left the main network.",
    "Shipped out": "Grain loaded onto ships at all three ports (Port Lincoln, Thevenard, Lucky Bay).",
    Trucking: "Loaded travel BY ROAD. When grain can't go straight to port it gets double-handled — farm to silo now, silo to port later — which adds kilometres and cost (10¢/t·km, A18). Tonnes moved by rail are counted separately and are NOT charged at the road rate — nor is the cost of running the railway.",
    "Kilometres driven": "Truck-kilometres on the road, loaded and empty. Tonne-km measure the freight task; this counts the vehicle trips behind it — the number that drives road wear, emissions and driver demand. A bigger silo-to-port payload, or a trainset taking the load, removes truck trips without changing how far the grain travels.",
    "Worst silo queue": "The most trucks waiting to unload at any ONE silo at any single moment this season, this what-if vs the modelled normal season. The absolute number rests on an assumed unloading time (A2) — read it as relative.",
    "Delivery pace": "How many days earlier or later this what-if reaches the same delivered tonnage as the modelled normal season. Slower logistics (e.g. fewer trucks) shows up here — grain waits on farm, a cost the freight dollars don't price.",
    "Grain waiting on farm": "Extra tonne-days harvested grain spends in field bins before delivery, vs the modelled normal season. Priced as financing only — ~9¢/t/day (grain value at overdraft rates, A22). Weather, insect and quality risk of holding grain on farm are real but not publicly priceable, so NOT included.",
    "Ships waiting": "Average hours each ship spends at anchor waiting for a berth or for grain, costed at a demurrage-like ~A$30k per ship-day (A19).",
    "Crop value (farm gate)": "The changed harvest tonnage valued at PIRSA-derived farm-gate prices (~$380/t).",
  };
  let fixedRows = $derived.by((): Row[] => {
    const d = deltas;
    const s = app.snap;
    if (!d || !s) return [];
    const kt = (t: number) => `${t > 0 ? "+" : "−"}${Math.abs(t / 1000).toFixed(0)}k t`;
    const mk = (label: string, delta: number, thr: number, goodWhenUp: boolean, val?: string, money?: string): Row => ({
      label,
      val: Math.abs(delta) > thr ? (val ?? kt(delta)) : "≈ no change",
      money: Math.abs(delta) > thr ? money : undefined,
      dim: Math.abs(delta) <= thr,
      dir: Math.abs(delta) <= thr ? "flat" : delta > 0 ? "up" : "down",
      goodWhenUp,
    });
    const rows: Row[] = [
      mk("Grain delivered", d.dRec, 20000, true),
      mk("→ to Lucky Bay instead", d.dLb, 10000, true),
      mk("Shipped out", d.dShip, 20000, true),
      mk(
        "Trucking",
        d.freight,
        150000,
        false,
        `${d.dTkm > 0 ? "+" : "−"}${Math.abs(d.dTkm / 1e6).toFixed(1)}M t·km`,
        `${d.freight > 0 ? "+" : "−"}${fmtMoney(Math.abs(d.freight))} freight`,
      ),
      mk(
        "Kilometres driven",
        d.dTruckKm,
        250000,
        false,
        `${d.dTruckKm > 0 ? "+" : "−"}${Math.abs(d.dTruckKm / 1e6).toFixed(2)}M truck-km`,
      ),
      {
        label: "Worst silo queue",
        val: `${s.kpi.peakQueue} vs ${d.baseQ} trucks`,
        dim: Math.abs(s.kpi.peakQueue - d.baseQ) <= 15,
        dir: Math.abs(s.kpi.peakQueue - d.baseQ) <= 15 ? "flat" : s.kpi.peakQueue > d.baseQ ? "up" : "down",
        goodWhenUp: false,
      },
      {
        label: "Delivery pace",
        val:
          d.paceLagDays === null
            ? "not comparable"
            : Math.abs(d.paceLagDays) < 2
              ? "keeping pace"
              : `~${Math.abs(d.paceLagDays)} days ${d.paceLagDays > 0 ? "behind" : "ahead of"} the modelled normal season`,
        dim: d.paceLagDays === null || Math.abs(d.paceLagDays) < 2,
        dir: d.paceLagDays === null || Math.abs(d.paceLagDays) < 2 ? "flat" : d.paceLagDays > 0 ? "up" : "down",
        goodWhenUp: false,
      },
      mk(
        "Grain waiting on farm",
        d.holding,
        150000,
        false,
        `${d.dOnFarmTd > 0 ? "+" : "−"}${Math.abs(d.dOnFarmTd / 1e6).toFixed(1)}M tonne-days`,
        `${d.holding > 0 ? "+" : "−"}${fmtMoney(Math.abs(d.holding))} financing`,
      ),
      mk(
        "Ships waiting",
        d.demurrage,
        200000,
        false,
        `${Math.round(d.waitNow)} h vs ${Math.round(d.waitBase)} h each`,
        `${d.demurrage > 0 ? "+" : "−"}${fmtMoney(Math.abs(d.demurrage))} waiting cost`,
      ),
    ];
    return rows;
  });

  interface Takeaway {
    text: string;
    money?: string;
    dir: "up" | "down" | "flat";
  }

  const WK_MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const fmtWeekEnding = (iso: string) => {
    const d = new Date(iso + "T00:00:00Z");
    return `${d.getUTCDate()} ${WK_MON[d.getUTCMonth()]}`;
  };

  /**
   * How the simulation tracks the published actuals (shown on the baseline).
   * The observed cumulative only exists on its week-ending date — comparing on any other
   * day means dividing a continuously-advancing sim total by a stale weekly figure (up to
   * six days / ~490,000 t old), which swings the displayed % wildly day to day. So this
   * only reports a comparison on days that are themselves a week-ending date.
   */
  let simVsActual = $derived.by(() => {
    const s = app.snap;
    const o = app.observed;
    if (!s || !o) return null;
    const start = Date.UTC(parseInt(app.season.slice(0, 4), 10), 9, 1);
    const w = o.weekly_receivals.find(
      (w) => Math.round((Date.parse(w.week_ending + "T00:00:00Z") - start) / 86400000) === s.day,
    );
    const act = w?.western?.cum_t;
    if (act == null) return { ready: false as const };
    // too small a denominator for a % to mean anything (early-season reports are a few thousand tonnes)
    const rel = act >= 50000 ? (s.kpi.receivedT - act) / act : null;
    return { ready: true as const, weekEnding: w!.week_ending, sim: s.kpi.receivedT, act, rel };
  });

  /** raw deltas vs the baseline run at the same simulated day */
  /** Lucky Bay lever expressed as an equivalent cash premium vs today's calibrated pull (A23) */
  let lbPremium = $derived(biasToPremiumPerT(app.levers.luckyBayBias / DEFAULT_LEVERS.luckyBayBias, app.econ.freightPerTKm));

  let deltas = $derived.by(() => {
    const s = app.snap;
    const b = app.baseline;
    if (!s || !b || b.receivedByDay.length === 0) return null;
    const i = Math.max(0, Math.min(s.day - 1, b.receivedByDay.length - 1));
    const baseRec = b.receivedByDay[i] ?? 0;
    const dRec = s.kpi.receivedT - baseRec;
    const dLb = s.kpi.receivedLbT - (b.lbByDay[i] ?? 0);
    const dShip = s.kpi.shippedT - (b.shippedByDay[i] ?? 0);
    const dTkm = s.kpi.tonneKm - (b.tonneKmByDay[i] ?? 0);
    const freight = dTkm * app.econ.freightPerTKm;
    // vehicle-km, not tonne-km: what actually changes when a trainset replaces truck trips
    const dTruckKm = s.kpi.truckKm - (b.truckKmByDay?.[i] ?? 0);
    const baseQ = b.queueByDay[i] ?? 0;
    const dQrel = baseQ > 20 ? (s.kpi.peakQueue - baseQ) / baseQ : 0;
    const waitDays = (s.kpi.meanWaitH * s.kpi.vesselsArrived) / 24;
    const baseWaitDays = ((b.waitByDay[i] ?? 0) * (b.arrivedByDay[i] ?? 0)) / 24;
    const demurrage = (waitDays - baseWaitDays) * app.econ.shipDayCost;
    let farmgate = 0;
    if (app.levers.productionScale !== 1.0 && app.observed) {
      const prod = Object.values(app.observed.district_production_t ?? {}).reduce((a, v) => a + v, 0);
      farmgate = (app.levers.productionScale - 1) * prod * (FARMGATE_PER_T[app.season] ?? 380);
    }
    // delivery pace: how many days ahead/behind the baseline reached this cumulative tonnage
    let paceLagDays: number | null = 0;
    if (s.kpi.receivedT > 80000) {
      let j = 0;
      while (j < b.receivedByDay.length && (b.receivedByDay[j] ?? 0) < s.kpi.receivedT) j++;
      // baseline never reaches this cumulative (scenario outran the season total, or the
      // baseline plateaued below it) — there's no day to compare against, so don't guess one
      paceLagDays = j >= b.receivedByDay.length ? null : s.day - j; // positive = behind the modelled normal season
    }
    const dOnFarmTd = s.kpi.onFarmTd - (b.onFarmTdByDay?.[i] ?? 0);
    const holding = dOnFarmTd * app.econ.holdingPerTDay;
    return { i, baseRec, dRec, relRec: baseRec > 50000 ? dRec / baseRec : 0, dLb, dShip, dTkm, freight, dTruckKm, baseQ, dQrel, demurrage, farmgate, waitNow: s.kpi.meanWaitH, waitBase: b.waitByDay[i] ?? 0, paceLagDays, dOnFarmTd, holding };
  });

  const tonnes = (t: number) => {
    const a = Math.abs(t);
    if (a >= 950000) return `${(a / 1e6).toFixed(1)} million tonnes`;
    return `${(Math.round(a / 1000) * 1000).toLocaleString()} tonnes`;
  };
  const pct = (f: number) => `${Math.abs(f * 100).toFixed(Math.abs(f) < 0.02 ? 1 : 0)}%`;

  /** plain-English sentences for Simple mode, most important first */
  let sentences = $derived.by((): { verdict: string; lines: string[] } | null => {
    const d = deltas;
    if (!d || (app.scenario === "baseline" && !assumpDirty)) return null;
    const lines: { key: string; weight: number; text: string }[] = [];

    if (d.farmgate !== 0) {
      lines.push({
        key: "farmgate",
        weight: Infinity, // headline number always leads
        text: `A crop ${pct(app.levers.productionScale - 1)} ${app.levers.productionScale > 1 ? "bigger" : "smaller"} is worth about ${fmtMoney(Math.abs(d.farmgate))} ${d.farmgate > 0 ? "more" : "less"} to farmers at the gate.`,
      });
    }
    if (Math.abs(d.relRec) >= 0.02 && Math.abs(d.dRec) > 20000) {
      lines.push({
        key: "relRec",
        weight: Math.abs(d.relRec) / 0.02,
        text: `${tonnes(d.dRec)} ${d.dRec > 0 ? "more" : "less"} grain reaches the silos and ports (${d.dRec > 0 ? "+" : "−"}${pct(d.relRec)}).`,
      });
    }
    if (Math.abs(d.dLb) > 10000) {
      lines.push({
        key: "dLb",
        weight: Math.abs(d.dLb) / 10000,
        text:
          d.dLb > 0
            ? `${tonnes(d.dLb)} of deliveries shift to the rival Lucky Bay port instead.`
            : `${tonnes(d.dLb)} of deliveries shift away from Lucky Bay back to the main network.`,
      });
    }
    if (Math.abs(d.freight) > 300000) {
      lines.push({
        key: "freight",
        weight: Math.abs(d.freight) / 300000,
        text:
          d.freight > 0
            ? `Trucks travel further overall — grain gets double-handled (farm to silo now, silo to port later) — roughly ${fmtMoney(Math.abs(d.freight))} extra in freight.`
            : `Trucks travel less overall — roughly ${fmtMoney(Math.abs(d.freight))} saved in freight.`,
      });
    }
    if (Math.abs(d.dTruckKm) > 250000) {
      lines.push({
        key: "dTruckKm",
        weight: Math.abs(d.dTruckKm) / 250000,
        text:
          d.dTruckKm < 0
            ? `About ${(Math.abs(d.dTruckKm) / 1e6).toFixed(1)} million fewer truck-kilometres are driven on the peninsula's roads.`
            : `About ${(d.dTruckKm / 1e6).toFixed(1)} million extra truck-kilometres are driven on the peninsula's roads.`,
      });
    }
    if (Math.abs(d.dQrel) >= 0.15) {
      lines.push({
        key: "dQrel",
        weight: Math.abs(d.dQrel) / 0.15,
        text: `Queues at the busiest silo peak about ${pct(d.dQrel)} ${d.dQrel > 0 ? "longer" : "shorter"} than the modelled normal season.`,
      });
    }
    if (d.paceLagDays !== null && Math.abs(d.paceLagDays) >= 3) {
      lines.push({
        key: "paceLagDays",
        weight: Math.abs(d.paceLagDays) / 3,
        text:
          d.paceLagDays > 0
            ? `Deliveries run about ${d.paceLagDays} days behind the modelled normal season.`
            : `Deliveries run about ${-d.paceLagDays} days ahead of the modelled normal season.`,
      });
    }
    if (Math.abs(d.holding) > 250000) {
      lines.push({
        key: "holding",
        weight: Math.abs(d.holding) / 250000,
        text:
          d.holding > 0
            ? `Grain waits longer on farm — roughly ${fmtMoney(Math.abs(d.holding))} in financing while growers wait to deliver (weather and quality risk on top, unpriced).`
            : `Grain spends less time waiting on farm — roughly ${fmtMoney(Math.abs(d.holding))} less financing.`,
      });
    }
    if (Math.abs(d.demurrage) > 500000) {
      // a multi-week wait means the fixed vessel program should have been re-issued for
      // the smaller/delayed crop rather than held open — say so at the point the big
      // number appears, not just in docs/scenarios.md (#6)
      const reissueNote = d.waitNow > 200 ? " (in reality the program would be re-issued for a smaller crop, not held open)" : "";
      lines.push({
        key: "demurrage",
        weight: Math.abs(d.demurrage) / 500000,
        text: `Ships wait about ${Math.round(d.waitNow)} hours each at anchor (normally ~${Math.round(d.waitBase)}) — roughly ${fmtMoney(Math.abs(d.demurrage))} in ${d.demurrage > 0 ? "extra" : "avoided"} waiting costs${reissueNote}.`,
      });
    }
    if (Math.abs(d.dShip) > 50000) {
      lines.push({
        key: "dShip",
        weight: Math.abs(d.dShip) / 50000,
        text: `${tonnes(d.dShip)} ${d.dShip > 0 ? "more" : "less"} grain gets shipped out by season's end.`,
      });
    }

    // verdict: lead with the shape of the outcome, not a number
    let verdict: string;
    const pinnedKeys = new Set<string>();
    if (d.farmgate !== 0) {
      verdict =
        app.levers.productionScale > 1
          ? "A bigger crop gets through — but watch the queues and where the surplus goes."
          : "A smaller crop: the pain is in what farmers don't harvest, not in moving it.";
      pinnedKeys.add("farmgate"); // headline number, keep first (weight Infinity within the pinned tier)
      if (app.levers.productionScale > 1) {
        pinnedKeys.add("dQrel"); // "watch the queues"
        pinnedKeys.add("dLb"); // "where the surplus goes"
      } else {
        pinnedKeys.add("demurrage"); // a smaller crop leaves ships waiting at anchor
      }
    } else if (Math.abs(d.relRec) < 0.02) {
      const costs: string[] = [];
      if (d.dQrel >= 0.15) {
        costs.push("longer queues");
        pinnedKeys.add("dQrel");
      }
      if (d.freight > 300000) {
        costs.push("extra trucking");
        pinnedKeys.add("freight");
      }
      if (d.demurrage > 500000) {
        costs.push("ships waiting");
        pinnedKeys.add("demurrage");
      }
      // the same tonnage can still be a materially better season — say so instead of
      // reporting "no difference" over a multi-million-kilometre change (F4)
      const gains: string[] = [];
      if (d.dTruckKm < -250000) {
        gains.push(`${(Math.abs(d.dTruckKm) / 1e6).toFixed(1)}M fewer truck-kilometres`);
        pinnedKeys.add("dTruckKm");
      }
      if (d.freight < -300000) {
        gains.push(`${fmtMoney(Math.abs(d.freight))} less freight`);
        pinnedKeys.add("freight");
      }
      if (d.dQrel <= -0.15) {
        gains.push("shorter queues");
        pinnedKeys.add("dQrel");
      }
      // only the first two gains are named in the sentence — don't pin ones left unmentioned
      if (!costs.length) {
        const namedGainKeys = new Set<string>();
        if (d.dTruckKm < -250000) namedGainKeys.add("dTruckKm");
        if (d.freight < -300000) namedGainKeys.add("freight");
        if (d.dQrel <= -0.15) namedGainKeys.add("dQrel");
        const named = [...namedGainKeys].slice(0, 2);
        pinnedKeys.clear();
        named.forEach((k) => pinnedKeys.add(k));
      }
      verdict = costs.length
        ? `The system absorbs this: almost the same grain gets through — the price is ${costs.join(" and ")}.`
        : gains.length
          ? `The same grain gets through, for less: ${gains.slice(0, 2).join(" and ")}.`
          : "Barely any difference from the modelled normal season.";
    } else if (d.relRec <= -0.02) {
      verdict = `The main network handles ${pct(d.relRec)} less grain${d.dLb > 10000 ? " — much of it goes to Lucky Bay instead" : ""}.`;
      if (d.dLb > 10000) pinnedKeys.add("dLb");
    } else {
      verdict = `The network handles ${pct(d.relRec)} more grain than the modelled normal season.`;
    }

    // rank by effect relative to each row's own threshold, but keep whatever the
    // verdict sentence names on top so slicing to 4 can't drop the line it points at (#5)
    const ranked = [...lines].sort((a, b) => {
      const ap = pinnedKeys.has(a.key) ? 1 : 0;
      const bp = pinnedKeys.has(b.key) ? 1 : 0;
      if (ap !== bp) return bp - ap;
      return b.weight - a.weight;
    });
    return { verdict, lines: ranked.slice(0, 4).map((l) => l.text) };
  });

  /** compact metric rows for Advanced mode */
  let takeaways = $derived.by((): Takeaway[] => {
    const d = deltas;
    if (!d) return [];
    const out: Takeaway[] = [];
    const kt = (t: number) => `${t > 0 ? "+" : "−"}${Math.abs(t / 1000).toFixed(0)} kt`;
    if (Math.abs(d.dRec) > 20000) out.push({ text: `Grain delivered ${kt(d.dRec)} vs baseline`, dir: d.dRec > 0 ? "up" : "down" });
    if (Math.abs(d.dLb) > 10000) out.push({ text: `Lucky Bay (T-Ports) intake ${kt(d.dLb)}`, dir: d.dLb > 0 ? "up" : "down" });
    if (Math.abs(d.dShip) > 20000) out.push({ text: `Shipped out ${kt(d.dShip)}`, dir: d.dShip > 0 ? "up" : "down" });
    if (Math.abs(d.freight) > 150000)
      out.push({
        text: `Trucking task ${d.dTkm > 0 ? "+" : "−"}${Math.abs(d.dTkm / 1e6).toFixed(1)}M tonne-km`,
        money: `${d.freight > 0 ? "+" : "−"}${fmtMoney(Math.abs(d.freight))} freight`,
        dir: d.freight > 0 ? "up" : "down",
      });
    if (Math.abs(d.dTruckKm) > 250000)
      out.push({
        text: `Truck-km on the road ${d.dTruckKm > 0 ? "+" : "−"}${Math.abs(d.dTruckKm / 1e6).toFixed(2)}M`,
        dir: d.dTruckKm > 0 ? "up" : "down",
      });
    if (app.snap && Math.abs(app.snap.kpi.peakQueue - d.baseQ) > 15)
      out.push({ text: `Peak site queue ${app.snap.kpi.peakQueue} vs ${d.baseQ} trucks`, dir: app.snap.kpi.peakQueue > d.baseQ ? "up" : "down" });
    if (Math.abs(d.demurrage) > 200000)
      out.push({
        text: `Vessel wait ${Math.round(d.waitNow)} h vs ${Math.round(d.waitBase)} h`,
        money: `${d.demurrage > 0 ? "+" : "−"}${fmtMoney(Math.abs(d.demurrage))} demurrage-equiv.`,
        dir: d.demurrage > 0 ? "up" : "down",
      });
    if (d.farmgate !== 0)
      out.push({
        text: `Crop ${app.levers.productionScale > 1 ? "+" : "−"}${pct(app.levers.productionScale - 1)}`,
        money: `${d.farmgate > 0 ? "+" : "−"}${fmtMoney(Math.abs(d.farmgate))} farm-gate`,
        dir: d.farmgate > 0 ? "up" : "down",
      });
    return out;
  });
</script>

<div class="levers">
  <div class="head">
    <span class="t">{app.viewMode === "advanced" ? "What-if levers" : "What-if"}</span>
    {#if app.scenario !== "baseline"}<button class="reset" onclick={reset}>back to normal</button>{/if}
  </div>
  <p class="story">{story}</p>

  {#if app.viewMode === "advanced"}
    <div class="fine how">Drag a lever and the whole season instantly re-runs with that change. “What changed” below compares it against the modelled normal season.</div>
    <label title="Scales how much grain grows on every paddock. 100% = what was really harvested.">
      <span>How big is the crop? <b>{Math.round(app.levers.productionScale * 100)}%{cropMt ? ` ≈ ${cropMt.toFixed(1)} million t` : ""}</b></span>
      <input type="range" min="0.5" max="1.4" step="0.05" value={app.levers.productionScale}
        oninput={(e) => set("productionScale", parseFloat(e.currentTarget.value))} />
    </label>
    <label title="Nobody publishes the real fleet size. ~730 is FITTED: the fleet that makes simulated weekly deliveries match the published ones at an assumed ~38 t average load. It is only WEAKLY identified — fleet size and load size trade off, so ~900 small trucks or ~500 road trains fit the same data equally well. What is really pinned down is the flow: ~1,850 loads/day at the peak. Fewer trucks = grain waits on farm; more = longer silo queues.">
      <span>How many trucks working the harvest? <b>{Math.round(app.levers.fleetTrucks)} — {fleetDesc}</b></span>
      <input type="range" min={FLEET_MIN} max={FLEET_MAX} step="10" value={app.levers.fleetTrucks}
        oninput={(e) => set("fleetTrucks", parseFloat(e.currentTarget.value))} />
    </label>
    <label title="How strongly the competing T-Ports Lucky Bay system attracts nearby farmers (price incentives, service). Push it up and eastern-peninsula grain drains away from the main network. The $/t figure translates the pull into an equivalent cash premium for a typical eastern-peninsula farm (90 min generalized haul, priced at the freight rate — A23).">
      <span>Lucky Bay's pull on farmers: <b>{strength(app.levers.luckyBayBias, DEFAULT_LEVERS.luckyBayBias)}{Math.abs(lbPremium) >= 0.5 ? ` ≈ ${lbPremium > 0 ? "+" : "−"}$${Math.abs(lbPremium).toFixed(0)}/t premium` : ""}</b></span>
      <input type="range" min="0.2" max="3" step="0.1" value={app.levers.luckyBayBias}
        oninput={(e) => set("luckyBayBias", parseFloat(e.currentTarget.value))} />
    </label>
    <label title="How willing farmers are to drive past their local silo and cart directly to the port. More direct carting = longer farm trips but less double-handling.">
      <span>Carting straight to port: <b>{strength(app.levers.portAttractBias, DEFAULT_LEVERS.portAttractBias)}</b></span>
      <input type="range" min="0.4" max="2.5" step="0.1" value={app.levers.portAttractBias}
        oninput={(e) => set("portAttractBias", parseFloat(e.currentTarget.value))} />
    </label>
    <div class="toggles">
      <button class:on={app.levers.rail} title="Two 1,600 t trainsets return to the railway closed in 2019 (Cummins/Kimba/Wudinna into Port Lincoln), replacing a third of the road shuttle. No timetable — they run when port stocks need topping up, at narrow-gauge line speed rather than road speed, which works out at ~1.5 cycles a day each (assumption A21). How much trucking this saves depends strongly on the silo-to-port load assumption (see Model assumptions)." onclick={() => set("rail", !app.levers.rail)}>bring back trains</button>
      <button class:on={app.levers.outage} title="Close the Port Lincoln terminal for 7 days at harvest peak (mid-December)" onclick={() => set("outage", !app.levers.outage)}>port closed 1 wk</button>
      <button class:on={app.levers.roadClosure} title="Make the Tod Highway (the peninsula's central spine) impassable — detours take 2.5x as long" onclick={() => set("roadClosure", !app.levers.roadClosure)}>Tod Hwy closed</button>
    </div>

    <button class="assump-toggle" onclick={() => (showAssump = !showAssump)}>
      {showAssump ? "▾" : "▸"} Model assumptions — stress-test them
    </button>
    {#if showAssump}
      <div class="assump">
        <div class="fine">
          These don't change the world — they change the model's <i>guesses</i>. If a conclusion
          flips when you nudge one, treat it with care. Defaults are the registered assumptions
          (A-numbers in ASSUMPTIONS.md). <button class="reset mini" onclick={resetAssump}>reset all</button>
        </div>
        <label title="A1: average net tonnes per farm-truck load. Not published — built from industry mass-limit charts and load-size studies.">
          <span>Average truck load <b>{app.assump.payloadT} t</b></span>
          <input type="range" min="28" max="48" step="1" value={app.assump.payloadT} oninput={(e) => setA("payloadT", parseFloat(e.currentTarget.value))} />
        </label>
        <label title="A1: average net tonnes per silo-to-port road-train load. Our 45 t is anchored to Viterra's 2019 rail-replacement statement (48 loaded trucks/day for ~2,100-2,200 t/day). SA law permits much heavier: Type 2 road trains run to 142 t gross (~85 t net) where highways are on the pre-approved 53.5 m network. Raising this shrinks the trucking a railway would save.">
          <span>Silo-to-port road-train load <b>{app.assump.lhPayloadT} t</b></span>
          <input type="range" min="40" max="90" step="5" value={app.assump.lhPayloadT} oninput={(e) => setA("lhPayloadT", parseFloat(e.currentTarget.value))} />
        </label>
        <label title="A2: minutes to sample, weigh and tip one truck at a silo bay. Nowhere published — the single most influential guess behind queue numbers.">
          <span>Silo unload cycle <b>{app.assump.serviceMin} min</b></span>
          <input type="range" min="6" max="25" step="1" value={app.assump.serviceMin} oninput={(e) => setA("serviceMin", parseFloat(e.currentTarget.value))} />
        </label>
        <label title="A5: scales every drive time (default speeds: 90 km/h highways down to 60 on minor roads).">
          <span>Travel times <b>×{app.assump.travelScale.toFixed(2)}</b></span>
          <input type="range" min="0.8" max="1.3" step="0.05" value={app.assump.travelScale} oninput={(e) => setA("travelScale", parseFloat(e.currentTarget.value))} />
        </label>
        <label title="A7: daily rain that halts harvest (and, scaled, the day-after hangover).">
          <span>Rain that stops harvest <b>{app.assump.rainStopMm} mm</b></span>
          <input type="range" min="2" max="10" step="0.5" value={app.assump.rainStopMm} oninput={(e) => setA("rainStopMm", parseFloat(e.currentTarget.value))} />
        </label>
        <label title="A12 (fitted): share of the crop that never enters this network — seed, feed, on-farm storage, other buyers.">
          <span>Crop kept on farm / sold elsewhere <b>{Math.round(app.assump.retention * 100)}%</b></span>
          <input type="range" min="0.05" max="0.25" step="0.01" value={app.assump.retention} oninput={(e) => setA("retention", parseFloat(e.currentTarget.value))} />
        </label>
        <label title="A17: opening stocks measured from Oct-Nov shipments; scale them to test sensitivity.">
          <span>Last season's carry-over <b>×{app.assump.carryInScale.toFixed(1)}</b></span>
          <input type="range" min="0" max="2" step="0.1" value={app.assump.carryInScale} oninput={(e) => setA("carryInScale", parseFloat(e.currentTarget.value))} />
        </label>
        <label title="A4: country silo capacities are unpublished (assumed ~120,000 t each). Published port and T-Ports capacities are NOT scaled.">
          <span>Assumed silo capacities <b>×{app.assump.capScale.toFixed(1)}</b></span>
          <input type="range" min="0.5" max="1.5" step="0.1" value={app.assump.capScale} oninput={(e) => setA("capScale", parseFloat(e.currentTarget.value))} />
        </label>
        <div class="econ-head">Dollar rates (display only — the sim doesn't use money)</div>
        <label title="A18: road grain freight rate.">
          <span>Freight <b>{(app.econ.freightPerTKm * 100).toFixed(0)}¢ /t·km</b></span>
          <input type="range" min="0.07" max="0.13" step="0.005" value={app.econ.freightPerTKm} oninput={(e) => setE("freightPerTKm", parseFloat(e.currentTarget.value))} />
        </label>
        <label title="A19: cost of a ship waiting per day (demurrage-equivalent).">
          <span>Ship waiting <b>A${(app.econ.shipDayCost / 1000).toFixed(0)}k /day</b></span>
          <input type="range" min="15000" max="45000" step="1000" value={app.econ.shipDayCost} oninput={(e) => setE("shipDayCost", parseFloat(e.currentTarget.value))} />
        </label>
        <label title="A22: financing cost of harvested grain waiting on farm.">
          <span>On-farm holding <b>{(app.econ.holdingPerTDay * 100).toFixed(0)}¢ /t/day</b></span>
          <input type="range" min="0.05" max="0.15" step="0.005" value={app.econ.holdingPerTDay} oninput={(e) => setE("holdingPerTDay", parseFloat(e.currentTarget.value))} />
        </label>
        {#if CASH_BIDS}
          <div class="fine" title="Median of the buyers' posted site bids on the operator's public cash-pricing board (captured daily — see About). Off-season these are mid-north SA / Mallee / Vic sites; buyers post at Eyre Peninsula sites around harvest.">
            What grain actually sells for — posted cash bids, {CASH_BIDS.date}
            ({CASH_BIDS.bids} bids{CASH_BIDS.epBids > 0 ? `, ${CASH_BIDS.epBids} at EP sites` : ", none at EP sites off-season"}):
            {Object.entries(CASH_BIDS.medianPerT).map(([c, v]) => `${c.toLowerCase()} ~$${Math.round(v)}/t`).join(" · ")}.
          </div>
        {/if}
        <div class="fine">Not adjustable (baked into the data): district boundaries (A14), climate source (A6), demand spreading (A3), AIS geofences (A8) — see ASSUMPTIONS.md.</div>
      </div>
    {/if}
  {:else}
    <div class="fine hint">Pick a scenario above to change the season — or switch to <b>Advanced</b> (top of panel) to drag the levers yourself.</div>
  {/if}

  {#if app.scenario === "baseline" && !assumpDirty}
    <div class="tk">
      <div class="tkt">Reality check</div>
      <p class="verdict">Season totals land within 1.6% of the operator's published figures, across three simulated seasons.</p>
      {#if simVsActual?.ready}
        <p class="verdict soft">
          As at week ending {fmtWeekEnding(simVsActual.weekEnding)}: {(simVsActual.sim / 1e6).toFixed(2)} million t
          modelled vs {(simVsActual.act / 1e6).toFixed(2)} reported
          {#if simVsActual.rel != null}
            — {Math.abs(simVsActual.rel * 100).toFixed(0)}% {simVsActual.rel > 0 ? "ahead of" : "behind"} reality.
          {:else}
            (too early in the season for a meaningful %).
          {/if}
        </p>
      {:else}
        <p class="verdict soft">You're watching the season as it really ran. A week-by-week comparison appears each Sunday once harvest starts (mid-October).</p>
      {/if}
      <div class="fine">Pick a scenario above{app.viewMode === "advanced" ? ", or drag a lever," : ""} to ask "what if?".</div>
    </div>
  {:else if app.viewMode === "simple"}
    <div class="tk">
      <div class="tkt">What this changes <span class="live">· updates as the season plays</span></div>
      {#if changeSummary && app.scenario === "custom"}<div class="uchg">Your change: <b>{changeSummary}</b></div>{/if}
      {#if !app.baseline}
        <p class="verdict soft">Working out the normal season to compare against…</p>
      {:else if sentences}
        <p class="verdict">{sentences.verdict}</p>
        {#if sentences.lines.length}
          <ul class="plain">
            {#each sentences.lines as l}<li>{l}</li>{/each}
          </ul>
          <div class="fine">Dollar figures are rough, order-of-magnitude estimates — see “About” for how they're worked out.</div>
        {:else}
          <div class="fine">No meaningful differences yet — most appear once harvest gets going (mid-October to January).</div>
        {/if}
      {/if}
    </div>
  {:else}
    <div class="tk">
      <div class="tkt">What changed <span class="live">· running comparison{app.snap && app.snap.day < 360 ? `, to ${app.snap.dateIso}` : " — full season"}</span></div>
      {#if changeSummary}<div class="uchg">Comparing the modelled normal season against: <b>{changeSummary}</b></div>{/if}
      {#if !app.baseline}
        <div class="fine">Computing the modelled normal season baseline…</div>
      {:else}
        {#each fixedRows as r}
          <div class="row {colorClass(r.dir, r.goodWhenUp)}" class:dim={r.dim} title={ROW_TIPS[r.label] ?? ""}>
            <span class="rl">{r.label}<span class="q">?</span></span>
            <span class="money">{r.val}{r.money ? ` · ${r.money}` : ""}</span>
          </div>
        {/each}
        {#if deltas && deltas.farmgate !== 0}
          <div class="tkt" style="margin-top:8px">Season total <span class="live">· not a running total — the whole crop's value, whatever the date</span></div>
          <div class="row {colorClass(deltas.farmgate > 0 ? 'up' : 'down', true)}" title={ROW_TIPS["Crop value (farm gate)"]}>
            <span class="rl">Crop value (farm gate)<span class="q">?</span></span>
            <span class="money">{deltas.farmgate > 0 ? "+" : "−"}{fmtMoney(Math.abs(deltas.farmgate))}</span>
          </div>
        {/if}
        {#if (app.snap?.kpi.railTonneKm ?? 0) > 0}
          <div class="fine">Trains carried {((app.snap?.kpi.railTonneKm ?? 0) / 1e6).toFixed(0)}M t·km of that task. The freight figure counts only what the trucks no longer do — rebuilding and running the railway is not priced here.</div>
        {/if}
        {#if app.levers.fleetTrucks < DEFAULT_LEVERS.fleetTrucks * 0.92 && (deltas?.freight ?? 0) < -200000}
          <div class="fine">Why cheaper with fewer trucks? Shorter queues mean trucks stop driving past the nearest silo — fewer kilometres. The cost moved into time: see “Delivery pace” and “Grain waiting on farm” (which prices the financing, but not the weather/quality risk).</div>
        {/if}
        <div class="fine">Values keep updating as the season plays. Indicative dollars: {(app.econ.freightPerTKm * 100).toFixed(0)}¢/t·km cartage, ~A${(app.econ.shipDayCost / 1000).toFixed(0)}k per ship-day, {(app.econ.holdingPerTDay * 100).toFixed(0)}¢/t/day holding, ~$380/t farm-gate (A18–A19, A22 — adjustable under “Model assumptions”).</div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .levers {
    margin-top: 10px;
    background: #101c2c;
    border: 1px solid #223650;
    border-radius: 8px;
    padding: 8px 10px;
  }
  .head {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .t {
    font-weight: 700;
    font-size: 12px;
  }
  .reset {
    background: none;
    border: 1px solid #31465e;
    color: #9db1c5;
    border-radius: 5px;
    font-size: 10px;
    padding: 2px 7px;
    cursor: pointer;
  }
  .story {
    color: #8fa3b8;
    font-size: 11px;
    margin: 6px 0 8px;
    line-height: 1.4;
  }
  label {
    display: block;
    margin-top: 6px;
    font-size: 11px;
    color: #9db1c5;
  }
  label b {
    color: #dfe7ef;
  }
  label input {
    width: 100%;
    margin-top: 2px;
  }
  .toggles {
    display: flex;
    gap: 6px;
    margin-top: 8px;
  }
  .toggles button {
    flex: 1;
    background: #17263a;
    border: 1px solid #31465e;
    color: #9db1c5;
    border-radius: 6px;
    padding: 4px 0;
    font-size: 11px;
    cursor: pointer;
  }
  .toggles button.on {
    background: #7a4a1d;
    border-color: #b06f2c;
    color: #ffe3bd;
  }
  .tk {
    margin-top: 10px;
    border-top: 1px solid #223650;
    padding-top: 7px;
  }
  .tkt {
    font-size: 11px;
    font-weight: 700;
    color: #cfdbe8;
    margin-bottom: 4px;
  }
  .row {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    font-size: 11.5px;
    padding: 2px 0;
  }
  .row.up {
    color: #7dd3a8;
  }
  .row.down {
    color: #f0b46a;
  }
  .row.dim {
    color: #5b6d80;
  }
  .live {
    color: #64788c;
    font-weight: 400;
    font-size: 9.5px;
  }
  .uchg {
    font-size: 10.5px;
    color: #9db1c5;
    margin: 2px 0 6px;
    line-height: 1.4;
  }
  .uchg b {
    color: #cfdbe8;
  }
  .row .money {
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }
  .row .q {
    display: inline-block;
    margin-left: 4px;
    width: 11px;
    height: 11px;
    line-height: 11px;
    text-align: center;
    border-radius: 50%;
    background: #223650;
    color: #7d93a9;
    font-size: 8px;
    vertical-align: 1px;
    cursor: help;
  }
  .fine {
    color: #64788c;
    font-size: 9.5px;
    margin-top: 5px;
    line-height: 1.35;
  }
  .hint b {
    color: #9db1c5;
  }
  .how {
    margin: 0 0 6px;
  }
  .assump-toggle {
    width: 100%;
    margin-top: 10px;
    background: #0d1826;
    border: 1px dashed #31465e;
    color: #9db1c5;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 11px;
    text-align: left;
    cursor: pointer;
  }
  .assump {
    border: 1px dashed #31465e;
    border-top: none;
    border-radius: 0 0 6px 6px;
    padding: 8px 10px;
    background: #0d1826;
  }
  .assump label {
    margin-top: 7px;
  }
  .econ-head {
    margin-top: 10px;
    font-size: 10.5px;
    color: #8fa3b8;
    font-weight: 700;
    border-top: 1px solid #223650;
    padding-top: 7px;
  }
  .reset.mini {
    font-size: 9px;
    padding: 1px 6px;
    margin-left: 4px;
  }
  .verdict {
    margin: 2px 0 6px;
    font-size: 12.5px;
    line-height: 1.45;
    color: #ffe9c2;
    font-weight: 600;
  }
  .verdict.soft {
    color: #9db1c5;
    font-weight: 400;
  }
  label input {
    accent-color: #3e73b3;
  }
  ul.plain {
    margin: 0;
    padding-left: 16px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  ul.plain li {
    font-size: 11.5px;
    line-height: 1.45;
    color: #c8d4e0;
  }
</style>
