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
    <h3>How the dollar figures are estimated</h3>
    <p>
      The "what this changes" figures are rough, order-of-magnitude estimates: trucking at
      ~10¢ per tonne-kilometre, ship waiting at ~A$30,000 per vessel-day, and farm-gate
      value at ~$375–405 per tonne derived from PIRSA's published seasonal totals. They are
      meant for comparing scenarios, not for costing anything (assumptions A18–A19 in the
      repository).
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
