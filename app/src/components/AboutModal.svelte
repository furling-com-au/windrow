<script lang="ts">
  let { onclose }: { onclose: () => void } = $props();
</script>

<div
  class="backdrop"
  onclick={onclose}
  onkeydown={(e) => e.key === "Escape" && onclose()}
  role="button"
  tabindex="-1"
>
  <div class="modal" onclick={(e) => e.stopPropagation()} role="dialog" tabindex="-1" onkeydown={() => {}}>
    <h2>About Windrow</h2>
    <p>
      Windrow is an <strong>agent-level simulation</strong> of the Eyre Peninsula (South Australia) grain
      supply chain: weather-gated paddock harvest, farm trucks choosing receival sites, site
      storage, line-haul to port, and ship loading at Port Lincoln, with Thevenard and T-Ports Lucky
      Bay as alternative gateways. It is built entirely on open or freely published data and is
      calibrated against published weekly receivals and port statistics.
    </p>
    <p class="warn">
      <strong>This is a simulation, not operational data.</strong> Truck movements, queues, site
      stocks and vessel loading progress are modelled. The dashed gold series (observed receivals)
      and the vessel arrival schedule derive from published data; everything else is simulated.
      Site storage capacities for upcountry sites and truck cycle parameters are assumptions —
      see ASSUMPTIONS.md in the repository.
    </p>
    <h3>How well does it match reality?</h3>
    <p>
      Season totals are close: on the held-out 2024/25 season the simulation's total
      tonnage was within <strong>0.4%</strong> of published receivals, and Port Lincoln
      vessel call counts matched exactly. The weaker spot is
      <strong>within-season timing</strong> — weekly RMSE runs 46–63% of the mean weekly
      tonnage, mostly because the exact week the harvest peak lands in can shift by a
      week or more even when the season's shape is right. Full numbers are in
      <code>docs/calibration_report.md</code> in the repository.
    </p>
    <h3>How do we know the truck numbers?</h3>
    <p>
      We don't count trucks — nobody publishes the fleet. The <strong>~730-truck fleet is
      fitted</strong>: it's the size that makes the simulated weekly deliveries match the
      operator's published weekly figures across two seasons (validated on a third,
      held-out season). The <strong>~38&nbsp;t average load is an assumption</strong> built
      from published anchors: the industry's own truck mass charts (SA road trains reach
      142&nbsp;t gross), a 72&nbsp;t load ceiling allowed on Eyre Peninsula, and a
      ~29&nbsp;t all-deliveries state average.
    </p>
    <p>
      Treat that count as <strong>weakly identified</strong> and read it together with the
      load size. What the published data really pins down is the <em>flow</em>: the peak week
      moved ~490,000&nbsp;t, about 1,850 loads a day. Fleet size and average load trade off
      almost exactly, so ~900 small trucks, ~730 average ones or ~500 road trains all
      reproduce the same season. The fleet is bounded below by what it takes to move that
      peak week, and above by queues staying believable — not by the fit, which keeps
      improving as trucks are added.
    </p>
    <h3>How the dollar figures are estimated</h3>
    <p>
      The "what this changes" figures are rough, order-of-magnitude estimates: trucking at
      ~10¢ per tonne-kilometre, ship waiting at ~A$30,000 per vessel-day, grain waiting on
      farm at ~9¢ per tonne per day (financing only — weather and quality risk are real
      but unpriced), and farm-gate value at ~$375–405 per tonne derived from PIRSA's
      published seasonal totals. They are meant for comparing scenarios, not for costing
      anything (assumptions A18–A19, A22 in the repository).
    </p>
    <p>
      For a reality anchor, the assumptions panel also shows the median of the <b>real cash
      bids</b> buyers post daily on the operator's public site-pricing board (per site,
      commodity and grade). Those bids expire the next day and no history is published, so
      this project captures the board once a day into its open dataset. Off-season the
      bids cover mid-north SA and Victorian sites only; buyers post at Eyre Peninsula
      sites around harvest. The "Lucky Bay pull" lever is also translated into an
      equivalent cash premium: making a site more attractive in the model works like
      shortening a farm's effective trip, and that saving is priced at the freight rate
      over a typical 90-minute eastern-peninsula haul (A23). Indicative only — the
      simulation itself moves tonnes, not money.
    </p>
    <h3>Key data sources</h3>
    <ul>
      <li>Weekly harvest reports — Viterra/Bunge (2016/17–2025/26, via the Internet Archive)</li>
      <li>Monthly per-port cargo statistics &amp; vessel calls — Flinders Port Holdings</li>
      <li>Vessel movements — AMSA Craft Tracking System via AODN/IMOS (CC BY-NC 3.0 AU at source; anonymised)</li>
      <li>District crop production — PIRSA Crop and Pasture Reports</li>
      <li>Land use — ABARES Catchment-scale Land Use (CC BY 4.0)</li>
      <li>Port parameters — ACCC/ESCOSA determinations, Bunge &amp; T-Ports port loading protocols</li>
      <li>Roads &amp; facility locations — © OpenStreetMap contributors (ODbL)</li>
      <li>Land polygons — Natural Earth (public domain); climate — ERA5 via open-meteo (CC BY 4.0)</li>
    </ul>
    <p class="fine">
      Full provenance (URLs, retrieval dates, licences) lives in <code>data/SOURCES.md</code>;
      every assumed value is registered in <code>data/ASSUMPTIONS.md</code>; calibration targets and
      tolerances in <code>data/CALIBRATION.md</code>. Vessel names are heuristic joins from archived
      shipping stems and may be wrong for overlapping calls. Non-commercial research project;
      no affiliation with Bunge, Viterra, T-Ports, or Flinders Ports.
    </p>
    <button onclick={onclose}>Close</button>
  </div>
</div>

<style>
  .backdrop {
    position: absolute;
    inset: 0;
    background: rgba(4, 8, 14, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 20;
  }
  .modal {
    width: min(620px, 92vw);
    max-height: 84vh;
    overflow-y: auto;
    background: #101c2c;
    border: 1px solid #31465e;
    border-radius: 12px;
    padding: 18px 22px;
    color: #dfe7ef;
    font-size: 13px;
    line-height: 1.5;
  }
  h2 {
    margin: 0 0 8px;
  }
  h3 {
    margin: 12px 0 4px;
    font-size: 13px;
    color: #9db1c5;
  }
  ul {
    margin: 4px 0;
    padding-left: 18px;
  }
  .warn {
    background: #1d2a3d;
    border-left: 3px solid #e8c568;
    padding: 8px 10px;
    border-radius: 4px;
  }
  .fine {
    color: #8fa3b8;
    font-size: 11.5px;
  }
  code {
    background: #17263a;
    padding: 1px 4px;
    border-radius: 3px;
  }
  button {
    background: #2b578a;
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 7px 14px;
    cursor: pointer;
  }
</style>
