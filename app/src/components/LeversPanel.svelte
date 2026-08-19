<script lang="ts">
  import { DEMURRAGE_PER_DAY, FARMGATE_PER_T, FREIGHT_PER_T_KM, HOLDING_PER_T_DAY, fmtMoney } from "../lib/economics";
  import { DEFAULT_LEVERS, SCENARIOS, app } from "../state.svelte";

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
    if (Math.abs(d) < 0.03) return "our best estimate of the real fleet";
    return `${Math.abs(d * 100).toFixed(0)}% ${d > 0 ? "more trucks than" : "fewer trucks than"} that estimate`;
  });

  /** one line naming exactly what differs from the real season */
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
    tip?: string;
  }

  const ROW_TIPS: Record<string, string> = {
    "Grain delivered": "Grain farmers delivered into the main network's silos and ports this season, vs the real season at the same date.",
    "→ to Lucky Bay instead": "Deliveries that went to the competing T-Ports Lucky Bay system — grain that left the main network.",
    "Shipped out": "Grain loaded onto ships at all three ports (Port Lincoln, Thevenard, Lucky Bay).",
    Trucking: "Loaded truck travel. When grain can't go straight to port it gets double-handled — farm to silo now, silo to port later — which adds kilometres and cost (10¢/t·km, A18).",
    "Worst silo queue": "The most trucks waiting to unload at any ONE silo at any single moment this season, this what-if vs the real season. The absolute number rests on an assumed unloading time (A2) — read it as relative.",
    "Delivery pace": "How many days earlier or later this what-if reaches the same delivered tonnage as the real season. Slower logistics (e.g. fewer trucks) shows up here — grain waits on farm, a cost the freight dollars don't price.",
    "Grain waiting on farm": "Extra tonne-days harvested grain spends in field bins before delivery, vs the real season. Priced as financing only — ~9¢/t/day (grain value at overdraft rates, A22). Weather, insect and quality risk of holding grain on farm are real but not publicly priceable, so NOT included.",
    "Ships waiting": "Average hours each ship spends at anchor waiting for a berth or for grain, costed at a demurrage-like ~A$30k per ship-day (A19).",
    "Crop value (farm gate)": "The changed harvest tonnage valued at PIRSA-derived farm-gate prices (~$380/t).",
  };
  let fixedRows = $derived.by((): Row[] => {
    const d = deltas;
    const s = app.snap;
    if (!d || !s) return [];
    const kt = (t: number) => `${t > 0 ? "+" : "−"}${Math.abs(t / 1000).toFixed(0)}k t`;
    const mk = (label: string, delta: number, thr: number, val?: string, money?: string): Row => ({
      label,
      val: Math.abs(delta) > thr ? (val ?? kt(delta)) : "≈ no change",
      money: Math.abs(delta) > thr ? money : undefined,
      dim: Math.abs(delta) <= thr,
      dir: Math.abs(delta) <= thr ? "flat" : delta > 0 ? "up" : "down",
    });
    const rows: Row[] = [
      mk("Grain delivered", d.dRec, 20000),
      mk("→ to Lucky Bay instead", d.dLb, 10000),
      mk("Shipped out", d.dShip, 20000),
      mk(
        "Trucking",
        d.freight,
        150000,
        `${d.dTkm > 0 ? "+" : "−"}${Math.abs(d.dTkm / 1e6).toFixed(1)}M t·km`,
        `${d.freight > 0 ? "+" : "−"}${fmtMoney(Math.abs(d.freight))} freight`,
      ),
      {
        label: "Worst silo queue",
        val: `${s.kpi.peakQueue} vs ${d.baseQ} trucks`,
        dim: Math.abs(s.kpi.peakQueue - d.baseQ) <= 15,
        dir: Math.abs(s.kpi.peakQueue - d.baseQ) <= 15 ? "flat" : s.kpi.peakQueue > d.baseQ ? "up" : "down",
      },
      {
        label: "Delivery pace",
        val:
          Math.abs(d.paceLagDays) < 2
            ? "keeping pace"
            : `~${Math.abs(d.paceLagDays)} days ${d.paceLagDays > 0 ? "behind" : "ahead of"} the real season`,
        dim: Math.abs(d.paceLagDays) < 2,
        dir: Math.abs(d.paceLagDays) < 2 ? "flat" : d.paceLagDays > 0 ? "up" : "down",
      },
      mk(
        "Grain waiting on farm",
        d.holding,
        150000,
        `${d.dOnFarmTd > 0 ? "+" : "−"}${Math.abs(d.dOnFarmTd / 1e6).toFixed(1)}M tonne-days`,
        `${d.holding > 0 ? "+" : "−"}${fmtMoney(Math.abs(d.holding))} financing`,
      ),
      mk(
        "Ships waiting",
        d.demurrage,
        200000,
        `${Math.round(d.waitNow)} h vs ${Math.round(d.waitBase)} h each`,
        `${d.demurrage > 0 ? "+" : "−"}${fmtMoney(Math.abs(d.demurrage))} waiting cost`,
      ),
    ];
    if (d.farmgate !== 0)
      rows.unshift({
        label: "Crop value (farm gate)",
        val: `${d.farmgate > 0 ? "+" : "−"}${fmtMoney(Math.abs(d.farmgate))}`,
        dim: false,
        dir: d.farmgate > 0 ? "up" : "down",
      });
    return rows;
  });

  interface Takeaway {
    text: string;
    money?: string;
    dir: "up" | "down" | "flat";
  }

  /** how the simulation tracks the published actuals (shown on the baseline) */
  let simVsActual = $derived.by(() => {
    const s = app.snap;
    const o = app.observed;
    if (!s || !o) return null;
    const start = Date.UTC(parseInt(app.season.slice(0, 4), 10), 9, 1);
    let act: number | null = null;
    for (const w of o.weekly_receivals) {
      const d = Math.round((Date.parse(w.week_ending + "T00:00:00Z") - start) / 86400000);
      if (d <= s.day && w.western?.cum_t != null) act = w.western.cum_t;
    }
    if (act == null || act < 5000) return { ready: false as const };
    return { ready: true as const, sim: s.kpi.receivedT, act, rel: (s.kpi.receivedT - act) / act };
  });

  /** raw deltas vs the baseline run at the same simulated day */
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
    const freight = dTkm * FREIGHT_PER_T_KM;
    const baseQ = b.queueByDay[i] ?? 0;
    const dQrel = baseQ > 20 ? (s.kpi.peakQueue - baseQ) / baseQ : 0;
    const waitDays = (s.kpi.meanWaitH * s.kpi.vesselsArrived) / 24;
    const baseWaitDays = ((b.waitByDay[i] ?? 0) * (b.arrivedByDay[i] ?? 0)) / 24;
    const demurrage = (waitDays - baseWaitDays) * DEMURRAGE_PER_DAY;
    let farmgate = 0;
    if (app.levers.productionScale !== 1.0 && app.observed) {
      const prod = Object.values(app.observed.district_production_t ?? {}).reduce((a, v) => a + v, 0);
      farmgate = (app.levers.productionScale - 1) * prod * (FARMGATE_PER_T[app.season] ?? 380);
    }
    // delivery pace: how many days ahead/behind the baseline reached this cumulative tonnage
    let paceLagDays = 0;
    if (s.kpi.receivedT > 80000) {
      let j = 0;
      while (j < b.receivedByDay.length && (b.receivedByDay[j] ?? 0) < s.kpi.receivedT) j++;
      paceLagDays = s.day - j; // positive = behind the real season
    }
    const dOnFarmTd = s.kpi.onFarmTd - (b.onFarmTdByDay?.[i] ?? 0);
    const holding = dOnFarmTd * HOLDING_PER_T_DAY;
    return { i, baseRec, dRec, relRec: baseRec > 50000 ? dRec / baseRec : 0, dLb, dShip, dTkm, freight, baseQ, dQrel, demurrage, farmgate, waitNow: s.kpi.meanWaitH, waitBase: b.waitByDay[i] ?? 0, paceLagDays, dOnFarmTd, holding };
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
    if (!d || app.scenario === "baseline") return null;
    const lines: string[] = [];

    if (d.farmgate !== 0) {
      lines.push(
        `A crop ${pct(app.levers.productionScale - 1)} ${app.levers.productionScale > 1 ? "bigger" : "smaller"} is worth about ${fmtMoney(Math.abs(d.farmgate))} ${d.farmgate > 0 ? "more" : "less"} to farmers at the gate.`,
      );
    }
    if (Math.abs(d.relRec) >= 0.02 && Math.abs(d.dRec) > 20000) {
      lines.push(`${tonnes(d.dRec)} ${d.dRec > 0 ? "more" : "less"} grain reaches the silos and ports (${d.dRec > 0 ? "+" : "−"}${pct(d.relRec)}).`);
    }
    if (Math.abs(d.dLb) > 10000) {
      lines.push(
        d.dLb > 0
          ? `${tonnes(d.dLb)} of deliveries shift to the rival Lucky Bay port instead.`
          : `${tonnes(d.dLb)} of deliveries shift away from Lucky Bay back to the main network.`,
      );
    }
    if (Math.abs(d.freight) > 300000) {
      lines.push(
        d.freight > 0
          ? `Trucks travel further overall — grain gets double-handled (farm to silo now, silo to port later) — roughly ${fmtMoney(Math.abs(d.freight))} extra in freight.`
          : `Trucks travel less overall — roughly ${fmtMoney(Math.abs(d.freight))} saved in freight.`,
      );
    }
    if (Math.abs(d.dQrel) >= 0.15) {
      lines.push(`Queues at the busiest silo peak about ${pct(d.dQrel)} ${d.dQrel > 0 ? "longer" : "shorter"} than the real season.`);
    }
    if (Math.abs(d.paceLagDays) >= 3) {
      lines.push(
        d.paceLagDays > 0
          ? `Deliveries run about ${d.paceLagDays} days behind the real season.`
          : `Deliveries run about ${-d.paceLagDays} days ahead of the real season.`,
      );
    }
    if (Math.abs(d.holding) > 250000) {
      lines.push(
        d.holding > 0
          ? `Grain waits longer on farm — roughly ${fmtMoney(Math.abs(d.holding))} in financing while growers wait to deliver (weather and quality risk on top, unpriced).`
          : `Grain spends less time waiting on farm — roughly ${fmtMoney(Math.abs(d.holding))} less financing.`,
      );
    }
    if (Math.abs(d.demurrage) > 500000) {
      lines.push(
        `Ships wait about ${Math.round(d.waitNow)} hours each at anchor (normally ~${Math.round(d.waitBase)}) — roughly ${fmtMoney(Math.abs(d.demurrage))} in ${d.demurrage > 0 ? "extra" : "avoided"} waiting costs.`,
      );
    }
    if (Math.abs(d.dShip) > 50000) {
      lines.push(`${tonnes(d.dShip)} ${d.dShip > 0 ? "more" : "less"} grain gets shipped out by season's end.`);
    }

    // verdict: lead with the shape of the outcome, not a number
    let verdict: string;
    if (d.farmgate !== 0) {
      verdict =
        app.levers.productionScale > 1
          ? "A bigger crop gets through — but watch the queues and where the surplus goes."
          : "A smaller crop: the pain is in what farmers don't harvest, not in moving it.";
    } else if (Math.abs(d.relRec) < 0.02) {
      const costs: string[] = [];
      if (d.dQrel >= 0.15) costs.push("longer queues");
      if (d.freight > 300000) costs.push("extra trucking");
      if (d.demurrage > 500000) costs.push("ships waiting");
      verdict = costs.length
        ? `The system absorbs this: almost the same grain gets through — the price is ${costs.join(" and ")}.`
        : "Barely any difference from the real season.";
    } else if (d.relRec <= -0.02) {
      verdict = `The main network handles ${pct(d.relRec)} less grain${d.dLb > 10000 ? " — much of it goes to Lucky Bay instead" : ""}.`;
    } else {
      verdict = `The network handles ${pct(d.relRec)} more grain than the real season.`;
    }
    return { verdict, lines: lines.slice(0, 4) };
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
    <div class="fine how">Drag a lever and the whole season instantly re-runs with that change. “What changed” below compares it against the real season.</div>
    <label title="Scales how much grain grows on every paddock. 100% = what was really harvested.">
      <span>How big is the crop? <b>{Math.round(app.levers.productionScale * 100)}%{cropMt ? ` ≈ ${cropMt.toFixed(1)} million t` : ""}</b></span>
      <input type="range" min="0.5" max="1.4" step="0.05" value={app.levers.productionScale}
        oninput={(e) => set("productionScale", parseFloat(e.currentTarget.value))} />
    </label>
    <label title="Nobody publishes the real fleet size. 589 is FITTED: it's the fleet that makes the simulated weekly deliveries match the published ones (av. load ~38 t, from industry mass limits — see About). Fewer trucks = grain waits on farm; more = longer silo queues.">
      <span>How many trucks working the harvest? <b>{Math.round(app.levers.fleetTrucks)} — {fleetDesc}</b></span>
      <input type="range" min="300" max="800" step="10" value={app.levers.fleetTrucks}
        oninput={(e) => set("fleetTrucks", parseFloat(e.currentTarget.value))} />
    </label>
    <label title="How strongly the competing T-Ports Lucky Bay system attracts nearby farmers (price incentives, service). Push it up and eastern-peninsula grain drains away from the main network.">
      <span>Lucky Bay's pull on farmers: <b>{strength(app.levers.luckyBayBias, 0.651)}</b></span>
      <input type="range" min="0.2" max="3" step="0.1" value={app.levers.luckyBayBias}
        oninput={(e) => set("luckyBayBias", parseFloat(e.currentTarget.value))} />
    </label>
    <label title="How willing farmers are to drive past their local silo and cart directly to the port. More direct carting = longer farm trips but less double-handling.">
      <span>Carting straight to port: <b>{strength(app.levers.portAttractBias, 0.8)}</b></span>
      <input type="range" min="0.4" max="2.5" step="0.1" value={app.levers.portAttractBias}
        oninput={(e) => set("portAttractBias", parseFloat(e.currentTarget.value))} />
    </label>
    <div class="toggles">
      <button class:on={app.levers.rail} title="Two 1,600 t trainsets return to the railway closed in 2019 (Cummins/Kimba/Wudinna into Port Lincoln), replacing a third of the road shuttle. No timetable — they run when port stocks need topping up, max ~2 cycles/day (assumption A21)." onclick={() => set("rail", !app.levers.rail)}>bring back trains</button>
      <button class:on={app.levers.outage} title="Close the Port Lincoln terminal for 7 days at harvest peak (mid-December)" onclick={() => set("outage", !app.levers.outage)}>port closed 1 wk</button>
      <button class:on={app.levers.roadClosure} title="Make the Tod Highway (the peninsula's central spine) impassable — detours take 2.5x as long" onclick={() => set("roadClosure", !app.levers.roadClosure)}>Tod Hwy closed</button>
    </div>
  {:else}
    <div class="fine hint">Pick a scenario above to change the season — or switch to <b>Advanced</b> (top of panel) to drag the levers yourself.</div>
  {/if}

  {#if app.scenario === "baseline"}
    <div class="tk">
      <div class="tkt">Reality check</div>
      {#if simVsActual?.ready}
        <p class="verdict">
          The model has delivered {(simVsActual.sim / 1e6).toFixed(2)} million t so far, vs
          {(simVsActual.act / 1e6).toFixed(2)} actually reported — {Math.abs(simVsActual.rel * 100).toFixed(0)}%
          {simVsActual.rel > 0 ? "ahead of" : "behind"} reality.
        </p>
      {:else}
        <p class="verdict soft">You're watching the season as it really ran. Weekly "actual" figures appear once harvest starts (mid-October).</p>
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
      {#if changeSummary}<div class="uchg">Comparing the real season against: <b>{changeSummary}</b></div>{/if}
      {#if !app.baseline}
        <div class="fine">Computing the real-season baseline…</div>
      {:else}
        {#each fixedRows as r}
          <div class="row {r.dir}" class:dim={r.dim} title={ROW_TIPS[r.label] ?? ""}>
            <span class="rl">{r.label}<span class="q">?</span></span>
            <span class="money">{r.val}{r.money ? ` · ${r.money}` : ""}</span>
          </div>
        {/each}
        {#if app.levers.fleetTrucks < DEFAULT_LEVERS.fleetTrucks * 0.92 && (deltas?.freight ?? 0) < -200000}
          <div class="fine">Why cheaper with fewer trucks? Shorter queues mean trucks stop driving past the nearest silo — fewer kilometres. The cost moved into time: see “Delivery pace” and “Grain waiting on farm” (which prices the financing, but not the weather/quality risk).</div>
        {/if}
        <div class="fine">Values keep updating as the season plays. Indicative dollars: 10¢/t·km cartage, ~A$30k per ship-day waiting, ~$380/t farm-gate (A18–A19).</div>
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
    color: #f0b46a;
  }
  .row.down {
    color: #7dd3a8;
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
