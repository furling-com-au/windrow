# Site roster audit — 2026-08-31

Triggered by the `ep-gate` workflow, which found the Tier-2 headline table half-wrong.
Ground truth throughout is the operator's own weekly harvest reports
(`data/processed/receivals_notes.jsonl`, 10 seasons, 2016/17–2025/26).

**Evidence rule, applied everywhere below:** a site named in a receival sentence
*operated* that season. Absence of a mention proves nothing — the reports name a site at
its first receival and when it is notable, not every week. All "operating" claims here are
lower bounds; no closure is inferred from silence.

## 1. Root cause

`pipeline/r1_build_sites.py:176`

    status = "active_2025_26" if commodities else ("dormant" if commodities == [] else "unknown")

`commodities` came from the live Bunge segregations table, read **2026-08-19 — off-season**
(the `_source` field records the date). A site between harvests correctly lists no
segregations. Reading that emptiness as a permanent status closed four operating sites.

Same class of error as the cash-price board listing zero EP sites outside harvest, already
recorded in the project notes. The provenance discipline captured the retrieval date; what
was missing was a check on the *inference* drawn from it.

## 2. Corrections applied

| Site | Was | Now | Evidence |
|---|---|---|---|
| Buckleboo | dormant | active_2025_26 | "Harvest kicked off at our Buckleboo, Elliston, Penong, Poochera and Warramboo sites" — wk 2025-11-16 |
| Elliston | dormant | active_2025_26 | same quote |
| Penong | dormant | active_2025_26 | same quote |
| Darke Peak | dormant | active_2025_26 | "Harvest has now kicked off at our Darke Peak, Streaky Bay, Yeelanna… bringing us to 40 sites receiving grain" — wk 2025-11-23 |
| Nunjikompita | dormant | **dormant (unchanged)** | last named 2023/24; no 2024/25 or 2025/26 mention. Weak evidence — silence is not closure |

Active 2025/26 Bunge sites: 18 → **22**.

`A12` in `data/ASSUMPTIONS.md` has been rewritten. It previously described per-season
re-enabling that **no code implemented** — nothing in the pipeline or the engine varied the
site set by season. `operating_seasons` and `operating_evidence` are now emitted per site
by `annotate_operating_seasons()`, so A12 is built rather than asserted.

## 3. Measured impact

Scenario set re-run on the corrected roster, fitted vector untouched:

- every headline moves <1 % except road-closure peak queue (+5.3 %) and Lucky Bay peak
  queue (−2.4 %)
- every ranking and every direction of effect unchanged
- operable 2025/26 storage 1.99 → 2.46 Mt (+24 %), which the network barely notices at
  baseline because it is not storage-constrained there
- site capacities unchanged — the A4 pool always included the dormant sites
- `npm --workspace packages/sim run test` — 17 passed

**Conclusion: no recalibration required.** The fitted vector reproduces the corrected
network without refitting.

## 4. Effect on the "One gateway" piece

| Row | Published | Corrected |
|---|---|---|
| **No independent receival point within 90 min** (Ladder B, the headline) | 20.3 % → 66.8 % | **20.3 % → 66.8 % — unchanged** |
| Nearest independent >60 min beyond nearest Bunge | 32.9 % → 74.4 % | 33.0 % → 77.3 % |
| Only one receival point within 45 min (Ladder A) | 9.5 → 13.7 → 25.4 % | **9.5 → 10.5 → 12.0 %** |
| Receival points on EP | 29 → 21 → 19 | **29 → 25 → 23** |

The **threshold** row is unchanged because every corrected site is Bunge-operated, and the
distance to the nearest *independent* point cannot move when a Bunge site is added. That is
why the headline survived a defect that destroyed the row beneath it.

**Correction (2026-08-31):** an earlier version of this paragraph claimed that invariance
for "Ladder B" as a whole. That is wrong, and the table above disproves it. It holds only
for the four *threshold* rows ("no independent point within X min"). It does **not** hold
for the *gap* rows ("nearest independent >60 min beyond nearest Bunge"), because the gap is
measured from the incumbent, so adding an incumbent site moves it — as it did here,
32.9 → 33.0 % and 74.4 → 77.3 %. Only the threshold rows may be described as invariant, and
the piece's headline must be one of them.

Ladder A was badly overstated. The corrected trajectory still rises but weakly, and no
longer supports a dramatic claim. It does not reverse, as one verifier projected — that
projection restored all five dormant sites; the evidence supports restoring four.

## 5. Outstanding — not fixed here

1. **Three EP sites are missing from the roster entirely.** All are named receiving grain
   in the operator's reports and none appears in `sites.geojson`:
   - **Tooligie** — 2022/23, 2023/24, 2024/25. *Inside the modelled season range, so this
     one affects sim outputs.* "Viterra's Tooligie, Kimba and Port Neill sites also
     received their first deliveries for the season" (2023-10-01).
   - **Cowell** — 2017/18, 2018/19. "The Western region received its first load on Friday,
     with grain delivered into our Cowell site" (2018-10-21).
   - **Mangalo** — 2018/19. "Darke Peak and Mangalo are now taking grain after opening for
     their first receivals" (2018-11-18).

   Adding them needs coordinates (OSM town nodes, as the closed sites use) and capacities.
   **Capacity is the entangling part**: A4 splits a fixed district total evenly between
   that district's sites, so adding any site changes every other site's estimated capacity
   in that district — and therefore the calibration. This is a deliberate stopping point,
   not an oversight.

1b. **Murdinga is absent from the roster entirely — as a closed site, not an operating one.**
   Bunge put six surplus SA bulk-handling sites to public tender through Elders on
   2026-07-07, binding offers due 2026-08-21: Bordertown, Tintinara, Coomandook (Upper
   South East), Geranium, Wunkar (Murray Mallee) and **Murdinga (Eyre Peninsula, 23,400 t,
   2.24 ha)**. Bunge's copy calls Murdinga a *"past site"* offering "flexibility for
   industrial or alternative rural development", and it has **zero mentions in all ten
   seasons** of weekly harvest reports — it has not taken grain since at least 2016/17.
   It belongs in the roster as a closed site, alongside the 2019 six.

   It does **not** create a second independent EP receival point: that would require a
   buyer to recommission a decade-dark site against marketing aimed at redevelopment. The
   tender outcome was unpublished as at 2026-08-31 and is a right-of-reply question for
   Bunge and Elders. Worth noting for context that Bordertown, also on the list, took grain
   as recently as 2024/25 — so the divestment is not purely of long-dead assets, though
   Bordertown is not on the Eyre Peninsula.

   Source: Grain Central, "Bunge to sell six surplus SA bulk-handling sites", 2026-07-07.

2. **Cungena is tagged `closed_2019` but received grain in 2022/23** — "…as well as
   Cungena, Elliston, Port Neill, Nunjikompita, Penong, Tumby Bay, Warramboo, Witera and
   Wirrulla in the Western region" (2022-11-13). The builder now emits a warning. It has no
   capacity assigned, so it is not currently simulable; resolving it has the same A4
   entanglement as item 1. Kyancutta was checked and is *not* contradicted — its only
   post-2019 mention is "east of Kyancutta", a paddock location, correctly rejected.

3. **`pipeline/r8_choice_geometry.py` still derives its historical network states from the
   single `status` field**, not from `operating_seasons`. Its 2023/24 column therefore omits
   Nunjikompita, which was named that season. Ladder B is unaffected (Nunjikompita is
   Bunge); Ladder A's middle column would shift slightly.

4. **The six `closed_2019` sites were never verified as closing in 2019.** Minnipa,
   Kielpa and Waddikee are never named in any of the ten seasons, which is consistent with
   closure but proves nothing under the evidence rule above. Wharminda is named once, in
   2016/17.
