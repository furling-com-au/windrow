# Pre-publication review — "One Gateway" (docs/piece_one_gateway.html)

**VERDICT: HOLD. Do not publish.** Thirteen blocking defects, several of them factual errors about named third parties that are contradicted by primary documents this repository already holds, and one — the tipped-buyer sentence naming Bunge — that is defamation-sensitive and sourced to nothing. The draft also publishes, as its headline, a count the project's own pre-publication gate withdrew as not quotable, and publishes its Tier 2 figure without the three companion rows `docs/ready_to_draft.md` marks mandatory.

Reviewed: draft of 31 August 2026 against `docs/analysis_plan_ep_competition.md` §3 and §6, `docs/ready_to_draft.md`, `docs/r0_choice_geometry.md`, `docs/r5_validation.md`, `docs/gate_findings.md`, `docs/roster_audit_2026-08.md`, `data/SOURCES.md`, `data/ASSUMPTIONS.md`, and the cached primaries under `data/raw/`.

Two structural notes before the list.

**The timeline is the weakest section of the piece and carries the strongest implied authority.** Every dated fact in "Why it matters this year" entered the project through web-search summaries. Five of them are wrong or materially incomplete against the primary record: the Grainflow withdrawal date, the Bunge completion date, the Wheat Port Code characterisation, the ACCC 2021 gloss, and the T-Ports sale date and price. Four of the five entries sit on `ready_to_draft.md` §2's "no citation exists in this repo" list. The method section badges this material "Tier 1 — a published fact"; it is the least sourced material on the page.

**Where the piece is strong, it is very strong, and none of that is at risk.** The Tier 2 geometry uses no calibrated parameter and reads no value from `calibrated.json` — the tier label is correct. The Lucky Bay coordinate envelope (61.5–67.3 %) reproduces exactly from `pipeline/r8a_coord_sensitivity.py`. The capacity figures are published operator and ACCC numbers. The Cungena contradiction is real and reproducible. The disclosure of the Tier 3 validation failure is genuine credit. Almost every fix below makes the piece harder to answer, not weaker.

---

## 1. Blocking issues

Each must be fixed, cut, or downgraded before the draft goes to right of reply. Ordered by exposure.

### B1 — "Buyer" is not the thing that was measured

**Where:** h1 ("one independent grain **buyer** left"), standfirst, the Tier 2 sentence ("more than 90 minutes from an independent **buyer**").

Every number behind those sentences counts **receival points and who operates them**. Nothing in this repository counts buyers, and the repo carries direct evidence against the buyer reading: `data/SOURCES.md` → `operator-cash-prices-api` describes the incumbent's own public feed as `site × commodity × grade × BUYER × price` and records the 2026-08-19 capture returning "buyers Inghams + Bunge" — a third party posting bids at Bunge sites. Warehousing plus title transfer is the standard structure of the Australian grain trade; A24 further records that 20.2–28.0 % of EP production never reaches Bunge receivals at all (domestic mills, container packers, on-farm use). A grower 16 minutes from a Bunge site can sell to a trader, a mill, a packer or a feedlot without any independent receival point existing. Storage-and-handling concentration is not buyer concentration, and the Code itself distinguishes port and handling services from grain acquisition. This is the first objection Bunge's lawyers will make and the fastest one the ACCC will make. No supporting document in the repo addresses the distinction anywhere.

**Fix.** Replace "buyer" with "receival point" or "non-Bunge place to deliver" in the h1, the standfirst, the section heading and the 90-minute sentence. Add a limits bullet in the same voice as the others: this measures the set of physical delivery points by owner, not the set of buyers; growers also sell to traders and end users through warehoused and delivered-site contracts at Bunge sites, hold grain on farm, and sell into container and domestic channels that no receival point in this count represents. None of that is measured here.

### B2 — The tipped-buyer sentence naming Bunge

**Where:** standfirst ("the dominant handler is on the list of tipped buyers") and the timeline row "Dec 2025 →" ("Tipped buyers include GrainCorp, CBH, Qube, Louis Dreyfus — **and Bunge**", bolded).

Asserted twice in the piece's own voice, in the present tense, unattributed, about a named company's M&A intentions, inside an argument adverse to that company. The claim traces to one syndicated agribusiness-briefs column: Stock Journal / The Land, Quinton McCallum and Andrew Marshall, 8 August 2025 — "Big-name local and international grain logistics and trading companies such as GrainCorp, CBH, Qube, Bunge and Louis Dreyfus are tipped to top the potential buyers' list." That is unattributed journalistic speculation, thirteen months old at the draft date, and it does not survive corroboration: The Land's parallel version of the same brief writes *Viterra*, not *Bunge*; Grain Central's launch story (Liz Wells, 29 July 2025) names no buyers at all, only "commodity/grain traders, private equity firms, sovereign wealth funds"; and the most recent reporting on the process (Grain Central, Emma Alsop, 3 December 2025) names Louis Dreyfus, Olam Agri and AGT Foods Australia and **does not mention Bunge**. The vendor's adviser has named no party. `ready_to_draft.md` §2 lists the T-Ports sale among the items for which "no citation exists in this repo… Source them or leave them out. An adjacent citation is not an option." The "No prediction" limits bullet does not cover this: it disclaims forecasting who will buy T-Ports, not the assertion that Bunge is on a list. The same search-summary channel has already produced one false claim in this project.

**Fix.** Delete the standfirst clause and the bolded "— and Bunge". If the buyer list is mentioned at all, attribute and date it in text and disclose the contradiction: "In August 2025 the Stock Journal reported that GrainCorp, CBH, Qube, Bunge and Louis Dreyfus were tipped to top the potential buyers' list. No company has confirmed interest, the vendor's adviser has named no party, and the most recent reporting on the sale (Grain Central, 3 December 2025) names Louis Dreyfus, Olam Agri and AGT Foods Australia." Register all three articles in `data/SOURCES.md` with retrieval dates and local caches. Put the question to Bunge and to Nash Advisory in the reply round before any version runs.

### B3 — The T-Ports harvest page is unarchived, unregistered and load-bearing

**Where:** the table's "Closed for season" cells, the quotation "Both bunkers are listed as 'Site closed for 25/26 season' on T-Ports' own harvest page", the 22/1 count, the standfirst and the 66.8 % headline.

The fact is **true** — `tports.com/harvest` today carries "Site closed for 25/26 season" against both Lock and Kimba, with Lucky Bay and Wallaroo operating — and it is the single most load-bearing fact on the page. It has no provenance: no `tports.com/harvest` entry in `data/SOURCES.md` (the only T-Ports entry is `tports-shipping-stem`, a different artefact), no cache anywhere under `data/raw/`, no Wayback capture, no retrieval date or URL on the page. The whole evidentiary basis is two hand-typed notes in `pipeline/manual_sites.json`: Lock, "per tports.com/harvest (2026-08-19)"; Kimba, verified 2026-08-31, its own note recording that until that date the site carried the closed status **with no closure evidence at all** while every 2025/26 finding depended on it. `ready_to_draft.md` records this as blocking defect D2 and marks row T13 "WITHDRAWN pending D2 — B1, B2, B3, B5, B6, B7, B11, B15 and B16 all sit on this row."

Two aggravating features. Both reads are **off-season live-page reads** — the exact method `docs/roster_audit_2026-08.md` §1 identifies as the root cause of four Bunge sites being wrongly recorded closed ("A site between harvests correctly lists no segregations. Reading that emptiness as a permanent status closed four operating sites"). The project corrected that error on the incumbent's side and has not tested for it on the entrant's side, where a single unarchived page read generates the entire finding. And the page will roll to 26/27 within weeks, at which point a lawyer checking the quotation finds nothing.

**Fix.** Before publication: capture the page to `data/raw/press/` and submit it to the Wayback Machine; register it in `data/SOURCES.md` with the URL, a retrieval date and the verbatim wording **for Lock and for Kimba separately**; lift the T13 withdrawal; cite it on the page with the retrieval date ("…when retrieved on 31 August 2026"); put the same retrieval date on the Kimba entry in `pipeline/manual_sites.json`. Corroborate with T-Ports directly (they are already a reply recipient) and, if possible, against the 2025/26 shipping stem. If the phrase can only be evidenced for Lock, do not write "both bunkers are listed as". Until the page is archived and registered, the 2025/26 network state is not publishable and neither is anything built on it. Archive `tports.com/lucky-bay` at the same time — it is the source for every capacity figure in the table and is equally unregistered.

### B4 — The 23/22 count is the row the project's own gate withdrew

**Where:** the finding box ("Of the 23 grain receival points operating on the Eyre Peninsula in the 2025/26 season, 22 are operated by Bunge"), badged **Tier 1 · published record**, and the "22" and "1" tiles.

The arithmetic checks out — `data/processed/sites.geojson` holds exactly 22 features tagged operator "Bunge (ex-Viterra)" / status `active_2025_26` (20 upcountry + Port Lincoln + Thevenard) plus Lucky Bay. The problem is that this is a count-of-receival-points row, and `ready_to_draft.md` §3 cuts "Ladder A in its entirety… Every count-of-receival-points row: '29 → 25 → 23 points'… the roster is an Aug-2026 operator snapshot used as a historical site list… The row has been wrong twice. It survives in Appendix A of `r0_choice_geometry.md` as the audit trail; it is not quotable." Appendix A itself carries "Do not quote any row in this appendix. NOT PUBLISHABLE." `data/ASSUMPTIONS.md` A12 is equally explicit: "`operating_seasons` is a lower bound and must never be read as a roster." The primary status field comes from a live segregations table read off-season on 2026-08-19 — the exact read that wrongly closed four operating sites.

The roster is demonstrably incomplete, and by more than the draft admits:

- **Tooligie** — named receiving grain in 2022/23, 2023/24 and 2024/25 (latest 2024-10-27), absent from `sites.geojson`.
- **Cowell** (2017/18, 2018/19) and **Mangalo** (2018/19) — same, absent.
- **Murdinga** — Eyre Peninsula, 23,400 t, **not in `sites.geojson` at all and not on the draft's known-defect list**. Bunge put it to public tender through Elders on 7 July 2026, binding offers due 21 August 2026 (Grain Central, "Bunge to sell six surplus SA bulk-handling sites"; the six are Bordertown, Coomandook, Tintinara, Geranium, Wunkar and Murdinga). That tender closed **ten days before this draft's date**, and a sale to anyone other than Bunge puts a second non-Bunge EP receival site into existence, directly against the headline.
- **Kapinnie** — inside the 22 with **no 2025/26 operating evidence**. Its `operating_seasons` end at 2024/25; its `active_2025_26` status rests solely on `commodities_2025_26: ["FB"]` from the off-season segregations read. That is the inverse of the roster_audit §1 trap and it has not been checked.
- **Nunjikompita** — excluded from the 22 on silence alone, which is the outcome the page's own stated rule promises not to produce (see S2).

**Fix.** Either restore the count ladder properly — audit the roster against a per-season operator source, incumbent **and** independent side — or stop publishing a count. The ownership finding survives without it: "we have found no receival point on the peninsula outside Bunge's network in 2025/26 other than T-Ports' Lucky Bay" is defensible; "there are 23 and 22 are Bunge's" is not. If a number is kept it must be stated as a floor **in the tile itself**, not only in a limits box further down the page ("at least 22 Bunge sites and one independent, on the operator's own weekly harvest reports for 2025/26; three further sites the operator has named in earlier seasons are not in our list"), the "Tier 1 · published record" chip must come off it, and the source must sit beside it (`data/processed/sites.geojson`, `pipeline/r1_build_sites.py`, plus the archived T-Ports page). Add Murdinga to the known-defect list and report the tender outcome or state that it was unresolved as at the draft date. Corroborate Kapinnie from a 2025/26 weekly report or state the count as 21 evidenced + 1 on the segregations table. Worth pre-empting the obvious challenge in the same breath: the ACCC's 2021 determination treats on-farm storage and T-Ports' direct-to-ship accumulation as live constraints, so say the count is of receival points, not of every route to market.

### B5 — "Today there is one" is an absolute negative the project cannot support

**Where:** h1, standfirst, finding box, the "1" tile, "the twenty-third is T-Ports' Lucky Bay", and "the only independent inland receival capacity the peninsula **has ever had**".

`ready_to_draft.md` §5 sets the rule for exactly these sentences: "Nothing in this repo audits the independent side. An unlisted non-Bunge receival point would move 66.8 % down. Weak answer: say 'we have not found one', never 'there is none'." The roster is the incumbent's own site API plus a hand-maintained T-Ports file; there has been no systematic search for other non-Bunge receival capacity (grower- or trader-owned sites, commercial on-farm storage taking third-party grain, container packers, feed mills, private bunkers). The "ever had" claim is worse: its only support anywhere is an assertion inside `data/ASSUMPTIONS.md` A11, with no published source — an "ever" claim over the whole history of a region is the least defensible form of the argument from absence. Compounding it, the geometry is clipped to an EP study-area bbox (`osm-roads-silos` in `data/SOURCES.md`) that the piece never discloses, so any option just off the peninsula — including T-Ports' own Wallaroo terminal, which is registered in `SOURCES.md` and never mentioned — is excluded by construction rather than by evidence.

**Fix.** Convert every absolute to a search result: "we have found one independent receival point operating on the peninsula in 2025/26"; "the only independent inland receival capacity we have found any record of". Add to the method section: the study-area boundary, that options outside it (including T-Ports Wallaroo) are excluded by the geometry rather than assessed, that no systematic audit of non-Bunge receival points was performed, and that an unlisted non-Bunge site would lower the 66.8 % figure.

### B6 — The headline geometry is printed alone, and its stated range is not its range

**Where:** the Tier 2 block, "roughly two-thirds… more than 90 minutes"; "The central estimate is 66.8 %… the defensible range is 61.5 % to 67.3 %. Any use of this number should carry the range."

Three mandatory companion rows are missing, all computed and sitting in `docs/r0_choice_geometry.md`:

| Row | Value | Status in `ready_to_draft.md` |
|---|---|---|
| **B4** — tonne-weighted drive to nearest **Bunge** point, 2025/26 | mean 18.7 min · median 16.5 · p90 33.2 · p99 58.3 | "Mandatory beside B1 — without it B1 carries no information about the incumbent" |
| **B2** — full threshold column, 2025/26 | 30 min 97.1 % · 45 93.2 % · 60 87.4 % · 75 78.2 % · **90 66.8 %** · 105 53.2 % · 120 39.5 % | Mandatory beside B1 |
| **B3** — travel-speed band at 90 min | ×0.85 **77.2 %** · ×1.00 66.8 % · ×1.15 **54.5 %** | "Mandatory beside B1"; `r0_choice_geometry.md` calls it "a standing row, not a footnote" |

The repo states the attack and concedes it: "Your headline is a distance to one port. It would be identical if Bunge ran 3 EP sites or 200 — No good answer, and it is the strongest attack on the piece… If the piece ever prints B1 alone it misleads." B1 is a pure function of the drive to Lucky Bay; it rises when the **entrant** closes sites and is unchanged by anything the incumbent does. Printed bare under the heading "How far is the alternative", it reads to a lay reader as a measure of Bunge's reach.

Separately, calling 61.5–67.3 % "the defensible range" is an affirmative misstatement. That band covers the Lucky Bay **coordinate** only (a 5.8 pp spread, asymmetric: 66.8 sits 0.5 pp below the top and 5.3 pp above the bottom, so it is the published-coordinate value, not a "central estimate"). The repo's own reproducible band on the same row, from the road-speed sensitivity, is 54.5–77.2 % — 22.7 pp. At 54.5 % "roughly two-thirds" is not true. `r0_choice_geometry.md` states in terms that "a uniform error in A5's road speeds does NOT cancel out of the published rows" and "any number quoted from this page carries that dependence". The sentence "Any use of this number should carry the range" converts the omission into a representation that the stated range is complete.

**Fix.** In the same visual block as the headline, print: B4 in the same sentence ("…against a median 16.5-minute run to the nearest Bunge site and a 99th percentile of 58.3"); the full 30–120-minute column, with the note that no threshold was designated a priori and both earlier justifications for 90 minutes were withdrawn on 2026-08-31, and that the finding survives at every row (still 39.5 % at the most generous); and both sensitivity bands, labelled — "66.8 % at the published coordinates; 61.5–67.3 % over the ±5 km tolerance on Lucky Bay's town-level coordinate; 54.5–77.2 % if the assumed road speeds are 15 % out either way", with the disclosure that a **non-uniform** speed error is not bounded by that band. State in the text that the figure is a distance to one port and is therefore insensitive to how many sites Bunge operates. Call 66.8 % the value at the published coordinates, not a central estimate, and drop "the defensible range" for a single sensitivity. If one sentence is wanted: "about two-thirds on our published road speeds, between roughly a half and three-quarters across the speed and coordinate sensitivities we tested."

### B7 — The 2019 closures: an attribution no source makes, welded to a cause the sources refuse

**Where:** "The published reporting at the time attributed the closures to freight redirection, in the same year grain trains ceased running on the peninsula."

`data/SOURCES.md` → `viterra-2019-site-closures` states it flatly: "The freight/rail attribution is NOT in either source… 'freight redirection' survives only as a URL slug… No published source found attributes the 2019 closures to the May 2019 rail shutdown." `pipeline/manual_sites.json` carries the same in capitals on all six site records. `ready_to_draft.md` §3 cuts "Any causal link between the May 2019 rail shutdown and the June 2019 closures". Re-checked against the cached primary (`data/raw/press/stockjournal_6202314_17-silo-closures_20260831.html`): "freight redirection" appears only in the `og:title`, `twitter:title` and JSON-LD `alternativeHeadline` — SEO metadata, a discarded headline — and nowhere in the article body. The printed headline is "SILO SLASH: 17 Viterra grain sites to close". Rail is mentioned once across both stories, by Minnipa grower Matt Cook, about a different and earlier local closure.

The company's published explanation is in the repo and absent from the draft. Operations manager Michael Hill, verbatim: "Since 2010, the average truck size has increased by 30 per cent and those bigger trucks are delivering to our bigger sites"; also changing delivery patterns, quality-management and food-safety requirements, and "The sites that were closed represented less than 2pc of total receivals (based on a five-year average)." Omitting a named company's own published account of its own decision while asserting a different, unsourced one is the specific thing that turns a competition piece into a legal problem. `gate_findings.md` also records that the rail closure and the site closures are perfectly collinear — both EP-only, same season — so nothing in this project could attribute either way even if it wanted to, and the piece does not disclose that either.

**Fix.** Delete the sentence. Replace with Viterra's stated reasons, quoted and attributed to Alisha Fogden, Stock Journal, 6 June 2019, including the sub-2 per cent receivals share. Keep the May 2019 rail cessation as bare chronology, in its own sentence, and say plainly that no published source connects the two and that the two events cannot be separated in this data. If the slug is mentioned at all, say what it is: a discarded headline in page metadata, not the article's account. Worth adding T11 while the paragraph is open — EP's share of network receivals shows no step across the 2019 boundary (pre-2019 mean 37.3 %, post 38.4 %) — because a piece that presents the incumbent's own explanation and the null result and *still* lands its finding is far harder to answer than one that omits both.

### B8 — "Six sites closed in 2019", unqualified, twice

**Where:** body text ("Six sites closed in 2019: Minnipa, Kyancutta, Cungena, Waddikee, Kielpa and Wharminda") and the standalone "**6** — Sites closed in 2019" tile.

`ready_to_draft.md` T2: "'Six EP sites closed in 2019', written unqualified, overstates the 2018/19 network by four sites. **Never write it unqualified.**" The cached source says only six sites "open last year" statewide were dropped — on EP, Minnipa and Kyancutta — while Cungena, Waddikee, Kielpa and Wharminda were among eleven "that were not open the year prior". Written in a section headed "What left the market, and when", the sentence reads as six delivery points removed from growers in one act; it was two. The tile is worse, because no qualification can travel with a bare numeral, and it is the element that gets screenshotted. Two further omissions: the piece names Cungena among the six and then, three sentences later, shows Cungena taking grain in 2022 — its own count is contradicted on its own page; and the source's own framing, that this was a statewide rationalisation of 17 Viterra sites of which six fell on EP, is dropped, which materially changes the inference that the peninsula was singled out. `roster_audit_2026-08.md` §4 also records that Minnipa, Kielpa and Waddikee were never verified as closing in 2019 under the repo's evidence rule.

**Fix.** "In June 2019 Viterra announced the closure of 17 up-country sites statewide, six of them on Eyre Peninsula. Two of the six — Minnipa and Kyancutta — had operated the previous season; the other four had not. Five stayed closed; a sixth, Cungena, took deliveries again in 2022/23." Either drop the "6" tile or relabel it "2 — Sites closed in 2019 that were operating the year before (Minnipa, Kyancutta)". Cite both Stock Journal stories of 6 June 2019 by author and date.

### B9 — The 2019 material reads as Bunge's conduct

**Where:** "The earlier contraction" section throughout; the table caption "Non-Bunge receival points" over a 2023/24 column.

The 2019 closures were Viterra's, six years before Bunge acquired the company. The draft never names Viterra in that passage — the actor is "the operator" and "the published closure list" — while every other operator reference on the page is "Bunge", and the section sits under "What left the market, and when". A reader, and Bunge's lawyers, will take the piece to be attributing a 2019 rationalisation to Bunge. The table compounds it by labelling a 2023/24 column against Bunge ownership that did not exist until July 2025. Imputing a predecessor's conduct to an acquirer without saying so is a fairness failure independent of whether the underlying facts are right.

**Fix.** Name Viterra as the operator throughout the 2019 and 2023/24 material; state once and plainly that Bunge acquired Viterra in 2025 and had no part in the 2019 decisions; and re-caption the table so the ownership label matches the season each column describes.
### B10 — Timeline: five dated facts wrong or materially incomplete

None of these is registered in `data/SOURCES.md`; `ready_to_draft.md` §2 lists four of the five under "Off the allowlist, no citation exists in this repo… Source them or leave them out. An adjacent citation is not an option." Each needs a primary document downloaded, cached under `data/raw/`, registered with a retrieval date, and cited on the page.

**(a) 2021 — the ACCC determinations.** The gloss "a finding that the peninsula's ports lack competitive constraint" is not what the ACCC found, and the primary document is already in the repo (`data/raw/reference/accc_final_determinations_2021.pdf`). It says the opposite in part: "Viterra's Port Lincoln facility likely faces a material level of competitive constraint from T-Ports Pty Ltd's (T-Ports) Lucky Bay facility in certain regions of its catchment area. However the constraint imposed in other regions is likely limited, in particular most of the Lower Eyre Peninsula"; for Thevenard, "Lucky Bay likely imposes limited competitive constraint" — limited, not absent. The determinations also record that "the level of competition in the SA market has increased in recent seasons" and that Lucky Bay "has yet to operate for a complete shipping year". The refusal turns on the subclause 5(3) matters and detriment to exporters, not on a finding of absent constraint. The entry further omits that the same April 2021 round refused Wallaroo and Port Giles, which makes the EP refusals look more singular than they were, and it merges two determinations dated 27 April and 20 July 2021.

*Fix:* "On 27 April 2021 the ACCC exempted Viterra's two Port Adelaide terminals from Parts 3–6 of the Bulk Wheat Code and refused exemption for Wallaroo and Port Giles; on 20 July 2021 it refused Port Lincoln and Thevenard, which remain subject to the full Code." Then quote what actually helps, verbatim from the executive summary: "Viterra has a dominant position upcountry on the Eyre Peninsula, where it owns the vast majority of storage." Delete the gloss, and carry the ACCC's own caveat that "distance, while important, is only one factor" — it cuts against the piece and it is better disclosed than discovered. Cite the cached PDF, extend its `SOURCES.md` entry beyond "port specs Table 3.1/3.2, catchments" to cover the determination outcome, and correct row T12 in `ready_to_draft.md`, which carries the same over-gloss.

**(b) Oct–Dec 2024 — Grainflow.** Two errors. The withdrawal date is wrong: the ACCC's public informal merger reviews register ("Viterra Operations Pty Ltd – Cargill Australia Limited and AWB Grainflow Pty Ltd") reads "10 Oct 2024 — ACCC commenced informal review"; "24 Oct 2024 — Closing date for submissions"; "13 Dec 2024 — ACCC is awaiting information from the merger parties…"; "17 Dec 2024 — ACCC discontinued its public review after Viterra Operations advised that the Proposed Acquisition would not be proceeding", outcome "Withdrawn on 17 December 2024". There is no 16 December entry — that is the trade-press announcement date, and it is the one date the register does not give, in a piece the ACCC may read. The draft also compresses two distinct acts (parties abandoning the transaction; the regulator discontinuing) onto it. And "Grain Producers SA… oppose it" is false: Stock Journal (Quinton McCallum, 23 Oct 2024) and Grain Central (23 Oct 2024) both record GPSA as explicitly neutral pending a grower survey — CEO Brad Perry: "Based on the feedback received, we'll be putting forward a submission to the ACCC on what we've heard." The register records no third-party submissions and no opposition at all. Only T-Ports is verifiable as an opponent (CEO Nathan Kent: "A return to the Viterra monopoly will be bad for competition and bad for growers, families and communities"). Asserting that a named industry body opposed a merger on which it publicly declined to take a position is a false statement about a third party — and GPSA is both a reply recipient and a target customer.

*Fix:* "The ACCC commenced an informal review on 10 October 2024 and discontinued it on 17 December 2024, after Viterra advised on 13 December that the acquisition would not proceed; no findings were announced. T-Ports lodged a submission opposing the acquisition; Grain Producers SA surveyed growers and put the concerns raised with it to the ACCC without taking a position." Also state that **none of the five sites is on the Eyre Peninsula** — Maitland (Yorke Peninsula), Crystal Brook (Mid North), Mallala (Adelaide Plains), Pinnaroo (Murray-Mallee), Dimboola (western Victoria), with the mobile ship loader at Port Adelaide Inner Harbour — and say why EP parties engaged anyway: the acquirer's statewide position, not assets on the peninsula. As drafted, placement in an EP piece invites the reader to assume the peninsula's own network was in play. Cache the register page and the Market Inquiries Letter of 10 October 2024 (ref IM-72702).

**(c) Aug 2025 — Bunge/Viterra.** The completion date is wrong by seven weeks. Bunge Global SA's press release, filed as Exhibit 99.1 to its Form 8-K: "Bunge and Viterra Complete Merger", dateline "ST. LOUIS, MO – July 2, 2025". The August date belongs to the rename only: the ACCC's own Wheat Port Code page states "On 21 August 2025, the name of Viterra Operations Pty Ltd changed to Bunge Operations Pty Ltd", and ABN Lookup for ABN 88 007 556 256 shows the record last updated 22 Aug 2025. `data/SOURCES.md`'s own context note already says 2025-07-02, so the draft contradicts the repository as well as the record. Getting the completion date of the named company's largest transaction wrong discredits the timeline whatever else it gets right.

*Fix:* split into two rows — "2 July 2025 — Bunge completes its merger with Viterra (the acquisition was assessed and not opposed by the ACCC on 21 December 2023)" and "21 August 2025 — Viterra Operations Pty Ltd is renamed Bunge Operations Pty Ltd". Cite the SEC exhibit and the ACCC rename page (a primary regulator source, and worth citing by name since the piece leans on the ACCC record elsewhere); cache both under `data/raw/reference/`.

**(d) Dec 2025 → — the T-Ports sale.** Date, price and status are composited from three reports. The sale launched in **July 2025**, not December: Grain Central, Liz Wells, 29 July 2025, "Sites with a ship for sale as unique T-Ports hits market" — the board "engaged Nash Advisory to lead the reinvestment process". The $250m is second-hand: Grain Central's own wording is "other media has reported T-Ports could fetch $250M" and, in December, "In July, other media reports had T-Ports valued at $250M"; Stock Journal (8 Aug 2025) gives "offers of more than $200 million have been floated". No vendor or adviser figure has been published. The Australian Grain Export packaging comes from Grain Central, Emma Alsop, 3 December 2025, which also gives combined EBITDA of $72M (AGE $40M, T-Ports $20M) — so the $250m does not clearly attach to the package the draft attaches it to. "Unsold at last report" is supported by that piece ("advanced discussions" with "a couple of parties") but the draft names no report and no date, which makes it an unsourced assertion about a named company's ownership roughly nine months downstream of the last reporting it rests on.

*Fix:* "July 2025 — T-Ports goes to market through Nash Advisory; media reports put the value at about $250m, unconfirmed by the vendor or its adviser, and a separate report cites offers of more than $200 million. December 2025 — the business is offered as a package with Australian Grain Export; as at 3 December 2025 it was unsold, with the adviser reporting advanced discussions with a couple of unnamed parties." Register all three articles. Re-check immediately before publication and again after the reply round; ask T-Ports and Nash Advisory directly, since both are already on the reply list.

**(e) 2024 → 2026 — the Wheat Port Code.** Three errors in one sentence, on a regulatory fact the ACCC itself would be reading. (i) The Code was **not** sunsetted; its sunsetting was **deferred by 24 months**. Primary source: Legislation (Deferral of Sunsetting — Competition and Consumer (Industry Code—Port Terminal Access (Bulk Wheat)) Regulation) Certificate 2024, F2024L01138, explanatory statement registered 12 September 2024 — the sunsetting date moves "from 1 October 2024 to 1 October 2026". The ACCC's own page: "The code will remain in operation until 1 October 2026, unless the Australian Government makes a decision to either remake or repeal the code at an earlier date." The Code is in force today. (ii) "On ACCC advice" inverts the record: the certificate was issued by the Attorney-General on written application from the Minister for Agriculture, with DAFF having "consulted with Treasury and the Australian Competition and Consumer Commission"; the ACCC's own submission argued the other way — "the ACCC considers that on balance (and absent a clear case for the Code's retention being established via this review), the Code should be allowed to sunset". The ACCC advised sunsetting; the government deferred it. (iii) No "revised exposure draft" was located; what went to consultation (DAFF, "Have your say on the future of the Wheat Port Code", 7 November 2024) is the review report and its recommendation that Grain Trade Australia develop an industry-managed code, with a government review in five years.

*Fix:* "September 2024 — the Wheat Port Code's automatic sunset is deferred 24 months, from 1 October 2024 to 1 October 2026, to let DAFF finish its second review. The ACCC had submitted that the Code 'should be allowed to sunset'. DAFF's review found the Code no longer fit for purpose and recommended an industry-managed code developed by Grain Trade Australia; consultation opened 7 November 2024." Cite F2024L01138 (explanatory statement), the ACCC submission and the DAFF news item; register all three. On "grower groups remain split", see S13 — it is sourceable but must be attributed.

### B11 — "3 independent sites operating 2023/24" rests on a Tier 3 model output

**Where:** the "3" tile, the standfirst's "three receival points", and the table's "2023/24 — Operating" cells for Lock and Kimba.

No published evidence that either inland bunker received grain in 2023/24 exists anywhere in this repo. All three T-Ports features in `sites.geojson` carry `operating_seasons: []` and `operating_evidence: null` — necessarily, because the only per-season operating evidence the project holds is Viterra/Bunge's weekly harvest reports, which never name a competitor's sites. `docs/r0_choice_geometry.md:172` asserts the bunkers "ran that season" with no citation. The only place the assertion is quantified is `docs/analysis_plan_ep_competition.md:46` — "They ran in 2023/24 (0.511 Mt T-Ports intake)" — and `r5_validation.md:289-292`, `gate_findings.md:213-215` and `ready_to_draft.md:253` all record that 0.511 Mt is **this model's own 2023/24 bunkers-open run**; A24 uses it to argue the fitted `luckyBayBias` sits at the top of what the evidence supports. Neither `tports_plp_2425.pdf` nor `tports_plp_2526.pdf` mentions Lock, Kimba or bunkers. The site notes do not close the gap either: Lock's reads "operated prior seasons from 2019" with nothing in its `sources` array; Kimba's says only "Built for 2021 harvest". So the 2023/24 state is inferred backwards from a single `status` field, which is precisely what A12's positive-evidence rule forbids — and a Tier 3 output is propping up a Tier 1 table cell, a count tile and the standfirst. It also falsifies the limits box's "not used for any claim on this page".

**Fix.** Obtain and register a published or operator-confirmed statement that the bunkers took 2023/24 deliveries — a T-Ports harvest page from that season, a Wayback capture, or a statement from T-Ports in the reply round — and cite it. Failing that, change the cells to what is known (the sites existed with published capacities; T-Ports publishes no season-by-season intake), mark them unverified, drop the "3" tile and the standfirst's "three", and note that every 2023/24 geometry figure inherits the same treatment. Whatever is decided must travel to the tile and the standfirst, not only to the table.

### B12 — The reproducibility undertaking does not run

**Where:** "Figures reproduce from `pipeline/r8_choice_geometry.py` and the site roster in `data/processed/sites.geojson`."

Three defects. (i) Both scripts are **untracked** — `git status` shows `?? pipeline/r8_choice_geometry.py` and `?? pipeline/r8a_coord_sensitivity.py` — and `sites.geojson` is modified in the working tree, so nothing is pinned to a commit. `ready_to_draft.md` §5: "Commit them, or no reviewer can check by diff that the method was not touched." A reproduction pointer to a file that exists in nobody's repository is not a citation, and reproducibility is the entire defence of the Tier 2 headline. (ii) The cited script **does not produce the published range and contradicts it**: at `r8_choice_geometry.py:810` the 2025/26 independent set is pinned (`ni25 = fixed_ind_min`), so r8 returns 66.8 % at all 129 sweep configurations by construction — and `r0_choice_geometry.md` advertises that invariance, calling the figure "A11-independent". The 61.5–67.3 % band comes only from `pipeline/r8a_coord_sensitivity.py` CHECK 1 ("ENVELOPE over all 17 configurations, 90 min: 61.52 % – 67.29 %"), which the page never names; r8a's own docstring says the r8 result is "true by construction of the sweep, not a demonstration that the level is coordinate-independent". A reader who follows the draft's only citation lands on a document asserting the figure is coordinate-independent, beside a draft asserting a 5.3 pp coordinate band. (iii) The stated inputs are incomplete: the figures also depend on `app/public/data/parcels.json` (production cells and tonne weights, `r8_choice_geometry.py:493`), `data/processed/roads.graph.json`, and the PIRSA district production behind the weights. Note also (D5) that the "independent reimplementation" the geometry partly rests on lives in a session scratchpad, is in no commit, and shares the same graph, speed dictionary, snapper and weights — an independent coding, not an independent data path.

**Fix.** Commit both scripts and the corrected roster; cite the commit hash the published figures were produced at, with the exact commands. Cite `r8a_coord_sensitivity.py` for the coordinate envelope and `r8_choice_geometry.py` for the level, and say plainly that r8's own A11 sweep holds the 2025/26 independent set fixed and therefore cannot test the coordinate. List all four inputs. Strike the surviving "A11-independent" and "66.8 % at every one of the 129 configurations" language from `r0_choice_geometry.md` so the two documents do not contradict each other in a reviewer's hands. Add an `ASSUMPTIONS.md` entry for the Lucky Bay coordinate in A11's structure — the ±5 km tolerance, the 61.5–67.3 % consequence, and the fact that the whole 2025/26 headline rests on one site's location — since A11 covers only the Lock and Kimba bunkers and D1 requires that registration before the number is quotable. If the repository will not be published, drop the reproducibility claim to what is true: figures are reproducible in an internal repository available on request.

### B13 — The pre-2019 column is omitted, and it is the counter-story

**Where:** standfirst ("Two years ago… three… Today there is one"); the counts device.

The piece makes 2023/24 its baseline without disclosing that 2023/24 is the **historical maximum** for independent capacity on the peninsula. `r0_choice_geometry.md:100` prints the pre-2019 cell of the headline row as "undefined — single operator", precisely so the record cannot be misread, and :108 gives distinct operators 1 → 2 → 2. On the repo's own numbers the peninsula went from no independent option ever, to three, to one — still one more operator than it had for its entire prior history, and the entrant is still there. A reader given only "three → one" is shown the downslope of a curve whose left half the author has seen and not printed. This is the first thing a Bunge response, or a sceptical editor, will lead with.

**Fix.** Print the pre-2019 column beside the other two, blank in the headline row with the words "undefined — one operator, nothing independent to be far from", and add the operator count 1 → 2 → 2. Say in the text that independent capacity on EP peaked in 2023/24 and that the comparison is against that peak, not against a long-run norm. It costs the piece nothing it can defend and removes the single easiest rebuttal.
---

## 2. Serious issues, ranked

**S1 — The piece never says who closed the two independent points.** They were T-Ports' own sites, closed by T-Ports, on T-Ports' own assets. Bunge neither owned nor operated them and had no part in the decision. Instead the headline says the peninsula has one independent buyer "left", the standfirst leads with "the region's dominant handler", the counts box sets "3 independent 2023/24" beside "6 sites closed in 2019", and the closure paragraph is followed immediately by a Bunge sentence. `ready_to_draft.md` §5 concedes the mechanism: the headline number "rises when the entrant closes sites". This is the clearest imputation-by-arrangement in the draft. *Fix:* one sentence, in body text, at the point the closures are reported — the fall from three independent receival points to one was T-Ports' decision about its own sites, and the incumbent had no role in it. Before the disclaimer, not inside it.

**S2 — A one-season status is written as a market exit.** The table records "Closed for season" and quotes "Site closed for 25/26 season". Everything around it converts that into a structural exit: "What left the market", "withdrew in two steps", "has one independent grain buyer left", "Today there is one". The existing note defends against an *intent* reading; the objection is *permanence*. A bunker idled for one drought season, with the operator for sale, is not an exit, and 2025/26 was a smaller crop (EP production 2.907 Mt against 4.149 Mt in 2022/23, per A24). *Fix:* "closed for the 2025/26 season" throughout, plus a sentence saying the closures are seasonal on the published wording, that whether they are permanent is unknown, and that the peninsula's independent inland capacity is therefore currently out of the market rather than gone from it.

**S3 — The computed results that cut against the finding are all omitted.** Three exist and all three flatter the piece's honesty: **B12**, the share of production nearer to the independent point than to Bunge — 12.2 % (2023/24) → 4.6 % (2025/26), annotated in the repo "print it; it works against the finding"; **B14**, the weighting sensitivity (own-season harvest weights 20.2 % → 64.7 %; unweighted 35.8 % → 73.7 %), which is the answer to "you've called a drought a monopoly"; and **B17**, road-snap coverage (tonne-weighted mean 1.99 km, 44.3 % of production >2 km from the graph), the answer to "your grid is coarse", where the error understates drive times and so works against the finding. *Fix:* add a short "what cuts the other way" block carrying all three with a line of interpretation each. In a piece going to a regulator, the presence of a counterweight section is itself evidence of method.

**S4 — The stated operating-status rule is not the rule applied.** The method note says status is derived from the operator's weekly narratives on a positive-evidence rule and that "the absence of a mention is not treated as closure". In fact `pipeline/r1_build_sites.py:267` sets status from the live Bunge segregations table (`active_2025_26 if commodities else dormant`), read off-season on 2026-08-19; `annotate_operating_seasons()` (line 122) then only ever upgrades dormant → active where 2025/26 receival evidence exists. A site with no narrative mention keeps the off-season status — which is how Nunjikompita is excluded from the 22 on silence alone, the outcome the stated rule promises not to produce. Line 90 filters T-Ports sites out of narrative matching entirely, so the Lock and Kimba statuses come from a live web page, not from the corpus at all. The piece therefore states a strict rule, breaches it once against the incumbent, and applies a much weaker one to the entrant, where it generates the headline. `roster_audit_2026-08.md` also states "All 'operating' claims here are lower bounds; no closure is inferred from silence", while the draft presents 22 and 23 as exact counts. *Fix:* describe the actual chain — "Bunge site status comes from the operator's public segregations table, read off-season, corrected upward where the operator's own weekly harvest reports name a site receiving grain in 2025/26; T-Ports site status comes from T-Ports' harvest page. A site named as receiving grain operated that season; absence of a mention is not treated as closure, so every operating count here is a lower bound." Then either evidence Nunjikompita's 2025/26 status or state that one further Bunge site's status is undetermined.

**S5 — The Tier 3 validation sentence misdescribes `r5_validation.md` in both directions.** "Tested against two real network changes and failed validation" is false for the first test: Test A (the 2019 closure) "cannot be run at all. Not 'runs and fails' — cannot be run", on four independent blockers — no model inputs for any pre-closure season (`production_districts.parquet` starts 2022/23, `climate_daily.parquet` starts 2020-09-01); no observed geography below the whole peninsula; the six sites absent from the engine's input with `capacity_t: null` and A4's total derived circularly from post-closure receivals; and perfect collinearity with the rail shutdown. It is also false for the second: Test B ran, "the mechanism behaves correctly and consistently", conserved exactly against T-Ports and stable across three seasons differing by 54 % in crop, with the observed shift "the same sign and the same order of magnitude" — verdict "a coherence check that passes, not a validation". Its binding problem is structural (both seasons with a verified bunker state are calibration seasons; the held-out season's state is A15's unverified assumption, adopted partly for the residual it explains, which the gate calls circular), not the single reason the draft gives. The regional-total geography is one of Test A's four blockers and the last of five for Test B; as written it reads as a fixable data-granularity issue that an operator email could close. Claiming to have run a test that could not be run is checkable against this file in one read, and the piece is trading on the disclosure ("documented rather than omitted"). *Fix:* "A third tier — simulated queues, truck movements and site stocks — did not clear its validation gate. One of the two intended tests, the 2019 closure, could not be run at all: the model has no inputs for any season before 2022/23, and the peninsula's published receivals are reported as a single regional total, so a redistribution among its sites is invisible by construction. The second test ran and the model behaved coherently, but both seasons with a verified network state are seasons the model was fitted on, so it carries no out-of-sample content. No data in this project can validate the redistribution mechanism, and closing the identified data gaps would not change that. Nothing from that tier appears here." Cite `docs/r5_validation.md` by name.

**S6 — "Built on published data only" and "road distances and site locations only" overstate the evidentiary basis.** `ready_to_draft.md` §5 already rules the equivalent sentence in `r0_choice_geometry.md:273` "False as the page words it… it should be deleted." Three inputs are not published data: the measure is drive **time**, which requires the assumed A5 road-class speed schedule (trunk 90, primary 90, secondary 80, tertiary 70, unclassified 60), never mentioned on the page; the tonne weighting is a modelling step (PIRSA district tonnage distributed by CLUM cropping-hectare share, A14), and the piece never tells the reader the figure is production-weighted at all; and the site coordinates are not all published — Lucky Bay's is a "Nominatim/OSM 'Lucky Bay, South Australia' hamlet node" at `coord_precision: town`, which is why the coordinate sensitivity exists, and the draft discloses that one sentence later, so the clause contradicts itself on the page. A credibility claim a company can disprove damages every claim beside it. *Fix:* keep "no simulation and no fitted parameter" — it is sound and worth keeping — and restate the rest: "road-network drive times over OpenStreetMap roads at assumed class speeds (A5), between site coordinates and production cells weighted by district tonnage and cropping area (A14), with town-level coordinates for the independent sites." Change the byline to "built from published records and open data, with assumptions listed".

**S7 — "The region's dominant handler" is a competition-law characterisation asserted in the piece's own voice.** Neutral wording carries exactly the same information the piece has established, and the strong word is available as a sourced quotation: ACCC, 2021 — "Viterra has a dominant position upcountry on the Eyre Peninsula, where it owns the vast majority of storage." *Fix:* "the operator of 22 of the peninsula's 23 receival points", or "the region's largest handler", and quote the ACCC where the stronger word is wanted.

**S8 — "Not a substitute for a local silo in any practical sense" is an unsourced substitutability conclusion inside a Tier 1 block.** Substitutability is the ACCC's own legal test, and the determinations the piece relies on two sections earlier found the opposite in part — Lucky Bay imposes "a material level of competitive constraint… in certain regions" of the Port Lincoln catchment — and caution that "distance, while important, is only one factor". The piece cites the ACCC where the ACCC helps it and contradicts the ACCC, silently, where it does not. The measurements that actually support the point are computed and unused: **B15**, the district cut for 2025/26 — WEP 98.6 %, LEP 79.7 %, EEP 23.8 % — and **B7**, mean drive to the nearest independent point 124.6 min. The physical description around it is fine and verified (24,000 t at the berth, 360,000 t in ten bunkers, the TSV *MV Lucky Eyre* shuttling to deep water five nautical miles out; the coordinate at 137.044 E is on the eastern shore). *Fix:* move the conclusion out of the Tier 1 block and replace it with the district figures — on the west coast 98.6 % of production has no independent receival point inside 90 minutes, on lower EP 79.7 %, on the east coast where Lucky Bay sits 23.8 % (print the east-coast figure even though it works against the headline) — plus the ACCC's contrary finding and its caveat. Note also that Lucky Bay does take grower deliveries into 360,000 t of bunkers: say it is a port that also receives from farm, at port distances, rather than "not an upcountry silo at all".

**S9 — The port treatment is asymmetric and both halves push the same way.** Two of the 22 counted on the incumbent's side are export terminals (Port Lincoln, Thevenard), while the one point on the independent side is discounted in the text precisely for being a port. If a port is not a practical alternative to a local silo it does not count on either side of the ledger; if it is, Lucky Bay counts too. A hostile reader will use the draft's own Lucky Bay sentence to make the point. *Fix:* lead with the upcountry-only comparison — 20 Bunge upcountry receival points against no independent upcountry receival point in 2025/26 — and treat the three ports as their own line.

**S10 — Third parties' positions are characterised without any quoted published statement.** Three instances: "T-Ports, Grain Producers SA and Eyre Peninsula growers oppose it" (false as to GPSA — see B10b); "Grower groups remain split on the replacement" (sourceable but uncited: Stock Journal, Gregor Heard, 8 July 2026, "Federal Government: Wheat Port Code draft splits grower groups" — GrainGrowers' Zach Whale for reform, Grain Producers Australia's Andrew Weidemann against a full move to a voluntary code; note that GPA is a different body from the piece's contact, Grain Producers SA); and "The 2024 opposition was argued with a grower survey and letters", which is both wrong on form — they were formal submissions to the ACCC's consultation — and disparaging, since it is the setup for a contrast in the author's favour ("the question a regulator actually has to answer is narrower and quantitative"). The ACCC register publishes no third-party submissions, so nobody here has read them and their contents cannot be characterised from the public record. GPSA is a reply recipient and a prospective customer; T-Ports owns the single site the whole piece rests on. *Fix:* quote the published submission or statement, with date and outlet, for each position attributed, or cut the attribution. Name which groups take which position rather than leaving "grower groups" undefined. Drop the comparative framing: the point can be made positively — that no party to the 2024 consultation published a quantitative catchment-substitution measure, which is a claim about the public record rather than about anyone's competence — and ask T-Ports and GPSA for their submissions in the reply round.

**S11 — "Two years ago" is wrong and steps over an unverified season.** Dated 31 August 2026, "two years ago" is 2024/25, and A15 records the repo's own position on that season: the bunkers did not operate. So on the project's own assumption there was one independent receival point two years ago, not three — and the piece's own counts tile correctly labels the three-site state 2023/24. The 2024/25 state is also *assumed*, not verified, and `gate_findings.md` §3 records that the observed data do not order by treatment across the four seasons (Bunge share of EP production: 2022/23 open 78.73 %, 2023/24 open 72.02 %, 2024/25 closed-assumed 79.78 %, 2025/26 closed 77.37 %). *Fix:* "In the 2023/24 season" or "Three harvests ago", matching the counts device; either add a 2024/25 column marked "assumed, not verified (A15)" or say in the text that the intervening season's bunker status could not be established and is excluded. Do not let a two-year frame imply a continuous trajectory with an unverified hole in the middle.

**S12 — No author, no affiliation, no interest disclosure.** The piece names a large company in a competition context under three mono lines and no byline. The undisclosed interest is material and is written down in the project's own plan: §8 heads the reply round "Right of reply — which is also the customer discovery", and says sending the draft "puts the model in front of every candidate customer with a professional reason to read it and reply." The candidate customers include parties adverse to Bunge. A piece that is simultaneously an analysis of a company and a sales approach to that company's opponents must say so. As it stands the easiest attack on standing is: an anonymous author, with an undisclosed commercial motive, reasoning about a business whose real capacities, cycle times and contract terms are confidential, has published a claim of monopsony without ever contacting the company. *Fix:* named author and affiliation, and a short disclosure of who funded or commissioned the work and what commercial interest the author has in the parties named.

**S13 — The right-of-reply notes are incomplete, faint, and become false at publication.** "Right of reply not yet sought" and the closing note record an absence; neither describes an offer, a deadline, a response or a non-response — the elements a reader needs to judge fairness and a court looks for. The list is narrower than §8 (Nash Advisory, DIT and RDA Eyre Peninsula are missing; Nash Advisory's omission matters specifically, because the sale and tipped-buyer claims are theirs and Bunge's to answer). And the closing note sits in the `.note` style — italic, `--step--1`, `--ink-faint`, the smallest and lowest-contrast text on the page — which is where the single most important editorial warning on the draft should not be. It also implies a reply round is the only remaining gate; it is not, since every timeline error in B10 must be corrected whether or not anyone replies. *Fix:* move the notice to the masthead at body size and weight; name the full §8 list and the five-working-day deadline; and replace both notes at publication with a standing paragraph giving who was written to, when, and each party's response in its own words or "did not respond by the deadline". Add one line making clear the reply round is in addition to, not instead of, verifying every dated claim against a primary source.

**S14 — "Principal sources" is simultaneously over- and under-inclusive, which is the one thing a provenance section must not be.** No URLs, no retrieval dates, no document identifiers, on a page whose whole defence is "Tier 1 is a published record". Listed but supporting no claim: Flinders Port Holdings monthly statistics, AMSA AIS vessel positions. Listed but not held: there is **no ACCC merger determination** anywhere — the Grainflow review was discontinued without one, and `data/raw/reference/` holds only the 2021 Bulk Wheat Code determinations. Listed but unregistered: "T-Ports site capacities and harvest-season status" (D2, still open). Load-bearing but unlisted: the ABARES CLUM land-use raster, which supplies the `cropping_ha` term behind the tonne weights (`r8_choice_geometry.py:429-431`, A3/A14); the two 2019 Stock Journal reports; the SMEC Eyre Peninsula Freight Study; and the assumption register itself (A5, A11/Lucky Bay coordinate, A12, A14). Five cached primaries under `data/raw/reference/` appear unconsulted, most consequentially **`escosa_grain_supply_chain_2019.pdf`** — ESCOSA's 2019 inquiry into the SA bulk grain supply chain, the most recent published regulatory examination of exactly this market, which the piece does not mention exists; also `bunge_port_loading_protocols_2025.pdf` (the incumbent's own regulated access disclosure, effective 14 Oct 2025) and the two T-Ports Port Loading Protocols. A competition piece that reaches a regulator without engaging the regulator's own prior findings on the same market will be read as not having looked. Licence obligations are also unmet: OpenStreetMap is ODbL with attribution required, and the AODN/IMOS AIS product is CC-BY over AMSA extracts at CC BY-NC 3.0 AU, flagged in the register as "treat the combined product as non-commercial until clarified". *Fix:* rewrite as a provenance list with publisher, document title or endpoint, retrieval date and link or archive reference per item — `data/SOURCES.md` already holds this for the datasets. Drop "merger" from the sources line and drop Flinders and AMSA, or say what they support. Add CLUM (with DOI and CC-BY attribution), the press sources, and the four assumption identifiers. Read ESCOSA 2019 and engage its EP findings explicitly, including where they cut against the piece. Carry "© OpenStreetMap contributors" and resolve the non-commercial flag before publishing commercially.

**S15 — The limits box's rescue sentence is arithmetically false.** "A fuller roster would change point counts, though not the ownership ratio, since all four are incumbent sites" — adding incumbent sites is exactly what changes the ratio: 22:1 becomes 25:1 or 26:1, and "23 receival points" becomes 26 or 27. The direction runs against the company, so the error does not favour the piece, but it is a plainly wrong statement in the section a lawyer reads most closely. What is actually invariant is narrower and is documented in `roster_audit_2026-08.md` §4: the distance-to-nearest-independent **threshold** rows cannot move when an incumbent site is added; the gap rows do move (32.9 → 33.0 %, 74.4 → 77.3 % on the same correction). The list is also imprecise: Cungena is *in* `sites.geojson` tagged `closed_2019`, not absent, so "all four" folds it in with three that are genuinely missing; and none of Tooligie (last 2024/25), Cowell (2018/19) or Mangalo (2018/19) is evidenced in 2025/26, so a fuller roster would mostly change the earlier columns. And the reassurance "since all four are incumbent sites" is itself an argument from absence the project's rules forbid. *Fix:* "Three receival points named in the operator's own reports — Tooligie, Cowell and Mangalo — are missing from our site list, and a fourth, Cungena, is tagged closed in 2019 but took deliveries in 2022/23. A fifth, Murdinga, is absent entirely. All are Bunge sites, so a fuller roster would raise the incumbent count in the earlier seasons and leave the independent count at one; the distance-to-nearest-independent figures cannot move at all, because adding an incumbent site cannot change how far the nearest independent one is. Every roster defect we have found is incumbent-side, and we have not audited the independent side. Every count on this page is a lower bound." Drop "not the ownership ratio".

**S16 — The counts device fuses two ladders the analysis says must never be added.** `r0_choice_geometry.md` builds its definitional section around Ladder A (how many points can this paddock reach, whoever owns them) and Ladder B (how much further is the nearest non-incumbent point), and warns specifically that scoring the pre-2019 state on the ownership ladder makes "the 2019 closure of six sites read as an improvement in competitive choice". The strip puts a Ladder A count (6 closed in 2019, all incumbent sites, in a period with no independent on the peninsula at all) beside two Ladder B counts (3 and 1) under one visual rule, and the surrounding prose — "The peninsula's independent capacity did not erode gradually… The earlier contraction" — invites the reader to count an incumbent rationalisation as the first step in the withdrawal of independent capacity. T-Ports did not exist in 2019 and every one of the six was a Viterra site. *Fix:* split the device or drop the 2019 tile from it; wherever the 2019 closures appear, say in terms that they were incumbent sites closing inside a single-operator market. Consider adding a "Bunge sites operating 2023/24" tile so the device shows the incumbent side flat and the independent side falling 3 → 1, which is the actual finding and is stronger for being narrower.

**S17 — "It arrived in 2019 and withdrew in two steps" is wrong on arrival.** `pipeline/manual_sites.json` dates the Kimba bunker "Built for 2021 harvest", so independent capacity accumulated across 2019–2021. The repo also holds two unreconciled Lucky Bay opening dates: "Transshipment port opened 2019" in `manual_sites.json` against the ACCC's "T-Ports commenced operations at its Lucky Bay facility in March 2020". *Fix:* reconcile the opening date against a primary source and correct the arrival to 2019–2021.

**S18 — The piece is a geometry argument with no geometry shown.** `analysis_plan_ep_competition.md` §4 R0 lists deliverable (b) as "a single-operator catchment map"; it was never produced (`docs/img/` holds four calibration SVGs). A reader cannot see where Lucky Bay is relative to the west coast, cannot see the 90-minute contour, and cannot check that the one remaining independent point is on the wrong side of the peninsula. For lawyers and a regulator, a map is also the fastest way to show the study-area boundary and the roster the numbers rest on. *Fix:* produce the R0 map — production cells shaded by drive time to the nearest independent point, incumbent and independent sites marked, study-area boundary drawn, 2023/24 and 2025/26 side by side, and the Lucky Bay marker labelled with its coordinate precision (town, ±5 km), which makes the D1 sensitivity legible instead of a footnote.

**S19 — The two obvious scenario runs are missing, and both are Tier 2 and free.** The piece's forward-looking section is the T-Ports sale and it never computes what the sale would do to its own headline: drop Lucky Bay from the independent set and 2025/26 collapses to the pre-2019 state the repo already knows how to report — one operator, headline undefined, zero independent receival points. The reverse run matters more for fairness: if Lock and Kimba reopen for 2026/27 the headline reverts to roughly its 2023/24 level (~20 %), which means 66.8 % is a statement about one season's site status, not a structural feature. The machinery exists in `pipeline/r8_choice_geometry.py`. *Fix:* run both and publish them as geometry, not prediction — "if the one remaining independent point changed hands, this measure would have nothing left to measure"; and "if the bunkers reopen, the figure reverts to about its 2023/24 level" — the second pre-empts the charge that a drought-season closure has been dressed up as a market structure.

**S20 — No tonnage context anywhere.** The piece gives site counts and three capacities and nothing else, so the reader cannot size the alternative in either direction. On the incumbent side, A4 estimates Bunge's EP upcountry storage at 2.54 Mt with published port storage of 395,600 t (Port Lincoln) and 335,925 t (Thevenard), and `roster_audit_2026-08.md` §3 gives operable 2025/26 storage of 2.46 Mt — against which Lucky Bay's 384,000 t is a materially larger share than "1 site in 23" conveys. On the independent side, the share of EP grain actually delivered to T-Ports is not published (A24's open data gap) and the only figure in the repo, 0.511 Mt, is barred model output. *Fix:* add a storage-share line with the A4 caveat that Bunge's per-site capacities are estimated, not published — the ACCC redacted Viterra's EP storage total as commercial-in-confidence, which is worth saying because it explains the gap — and then state plainly that the tonnage share delivered to the independent is not published, that this analysis does not estimate it, and that a site count is not a volume share.

**S21 — The capacity column invites a throughput reading and the status columns have no evidentiary footing.** 384,000 t is confirmed by ACCC 2021 Table 3.1 and by `tports.com/lucky-bay`, but the ACCC is explicit that "only 24,000 tonnes of T-Ports' storage is directly connected to its port terminal infrastructure", with 360,000 t in bunkers 2 km inland, and its footnotes record three different T-Ports totals in circulation (524,000 / 537,000 / 542,000 t) depending on the source. A bare "Capacity (t)" column beside a narrative about where a grower can deliver invites the throughput reading — the conflation `gate_findings.md` §4 item 15 already flagged elsewhere (A24 records only ~0.42 Mt actually moving through Lucky Bay in a season). Meanwhile the "Operating / Operating" cells have no backing in any processed dataset: `sites.geojson` gives Lucky Bay `operating_seasons: []`, and `stem_entries.parquet` contains zero T-Ports rows. The raw stems do carry it — TP0083 "Red Cosmos", Lucky Bay, nominated 23/02/2024 (2023/24); TP0149 "V Pegasus" and TP0151 "Ince Ilgaz", Lucky Bay, April–May 2026 (2025/26). *Fix:* retitle the column "Storage capacity (t)", footnote the Lucky Bay split citing ACCC 2021 Table 3.1, and cite the T-Ports shipping stems (`data/raw/stems/tports/tports_20240417002918.pdf`, `tports_20260511114109.pdf`) plus the archived harvest page for the status cells; register them in `SOURCES.md`, and ideally parse the T-Ports stems into `stem_entries.parquet` so the row has the same footing as the Bunge sites.

**S22 — The Cungena paragraph is framed as the project correcting the company's record.** It is not: the 2019 "closure list" is Stock Journal's report of Viterra's statement, not a company-published list, so the contradiction is between a newspaper's 2019 reporting and the company's 2022 weekly report. The paragraph also drops the qualifications the repo records and which cut the other way — one mention across 148 parsed weekly reports, no published reopening announcement found, and no evidence of operation in any other season. *Fix:* attribute each side precisely — "Viterra told growers in June 2019 that Cungena would be 'closed permanently' (Stock Journal, 6 June 2019); its own weekly harvest report for the week ending 13 November 2022 lists Cungena among sites taking first new-season deliveries. It appears in no other season, and in one of the 148 weekly reports we hold." Drop "correction to that record" for "the two published records disagree".

**S23 — The Lock and Kimba co-location sentence has no stated purpose.** "Both sat in towns where Bunge also operates a site" is accurate — the Bunge sites are ~0.9 km and ~2.3 km from the T-Ports pads, both with 2025/26 first-receival quotes in the operator's weekly reports — but placed immediately after the closure with no analytic purpose, its only work in the paragraph is to invite an inference about Bunge. The legitimate purpose is in the plan §2: those were the only two places an independent competed with the incumbent inland, which is why their closure removes *choice* rather than merely capacity, and the ACCC's 2021 determination independently records T-Ports at Lock as the only alternate upcountry provider on the peninsula. *Fix:* state the purpose and move the sentence ahead of the closure fact — "Lock and Kimba were the only two towns on the peninsula where a grower could choose between an independent bunker and a Bunge site at the same location" — then report the closures. Cite `sites.geojson` and the two weekly-report quotes, and state the ±5 km town-centroid precision (A11) rather than leaving "in the same town" to be inferred.

**S24 — The protective notes are typographically marked as asides.** Both the "no motive" note and the closing right-of-reply note use the `.note` class: italic, smallest step, faintest ink, immediately beneath material running at full body size and contrast. A qualification the company's lawyers will be told is the piece's protection should not be the least visible element on the page. *Fix:* set both at body size and body colour, or fold them into the preceding paragraphs. The "no motive" note should also record that T-Ports' own explanation was sought, and give it or record the non-response.

---

## 3. Minor issues — checklist

- [ ] **290,000 t is a floor.** `tports.com/lucky-bay` gives Lock "140,000 tonnes in six bunkers" (exact) but Kimba "more than 150,000 tonnes". Write "at least 290,000 tonnes", or footnote Kimba with the operator's wording.
- [ ] **Badge the capacity table Tier 1 with its sources named.** These are published operator and ACCC figures (`manual_sites.json` `capacity_source`) — one of the few places the piece is fully covered, and the obvious "A4 is estimated" attack simply fails. Say so.
- [ ] **"The operator's own weekly reports" is plural for a single report** in the Cungena paragraph — 1 of 148. Use the singular with the date and the denominator.
- [ ] **Make the cash-bid exclusion concrete.** It is the strongest exclusion on the page and carries the least detail. "Bids are published daily and expire the next day; no operator publishes a history. Our own capture is 13 off-season days (2026-08-19 to 2026-08-31) and no Eyre Peninsula site carried a bid on the first of them. That is corroboration for later work, not evidence now." Cite `data/SOURCES.md` `operator-cash-prices-api`.
- [ ] **Give seasons for the missing sites** in the limits box (Tooligie 2022/23–2024/25; Cowell 2017/18–2018/19; Mangalo 2018/19) and say which bear on the 2025/26 count.
- [ ] **Say where the five Grainflow sites were** (see B10b) — a reader cannot otherwise judge why an EP piece leads with that deal.
- [ ] **Note the regulatory gap.** The Bulk Wheat Code and its proposed successor cover *port terminals*; the piece's finding is about upcountry receival points, which sit outside that regime entirely. That is arguably the piece's most useful policy observation and it is unstated.
- [ ] **Give the 2026/27 position.** The draft is dated the week before harvest planning and speaks in the present tense, but says nothing about whether Lucky Bay or the bunkers open for 2026/27; `data/SOURCES.md` records T-Ports' terminals closed for maintenance 15 Aug – 31 Oct 2026. State the coming season's status or that it was sought and not obtained.
- [ ] **Carry the licence attributions** — "© OpenStreetMap contributors" (ODbL), and the AMSA + IMOS/AODN attribution — and resolve the AIS non-commercial flag before any commercial publication.
---

## 4. The right-of-reply pack

**Send order.** Fix B2, B7, B8, B9 and B10 *before* sending. Those are claims that must be
cut or corrected whether or not anyone replies, and sending a draft containing a factual
error you already know about — particularly the tipped-buyer sentence and the
freight-redirection attribution — converts a fairness process into a further publication of
it. B3, B4, B5, B6, B11, B12 and B13 can be flagged in the covering note as open and
under revision.

**Deadline.** Five working days from the date of sending, stated as a date and a time, not
a duration. On a Monday 7 September 2026 send that is **5pm ACST, Monday 14 September
2026**. Move the deadline with the send date. Say what happens either way: responses will
be quoted in the piece in the party's own words, or the piece will record "did not respond
by the deadline". Offer a call. Attach the draft and the assumption register
(`data/ASSUMPTIONS.md`) rather than describing them.

**Tone.** These letters are the customer-discovery round as well as the fairness round.
Every question below is answerable in a sentence, none contains an accusation, and each one
is a question the analyst genuinely does not know the answer to. Ask for facts, not
reactions.

---

### 4.1 Bunge — media / corporate affairs

*Claims in the piece that concern Bunge:* the 22-of-23 receival-point count and the site
roster behind it; the 2025/26 operating status of each site; the 66.8 % drive-time finding;
the 2019 Viterra closures and the reasons given for them; the corporate timeline
(completion date, entity rename); the Murdinga tender; and the reported buyer list for
T-Ports.

1. We count 22 grain receival points operated by Bunge on the Eyre Peninsula in the
   2025/26 season — 20 upcountry sites plus the terminals at Port Lincoln and Thevenard —
   built from Bunge's published segregations table and its weekly harvest reports. Is that
   count correct, and is there a site we have missed or included in error? We would take a
   corrected list in any form.
2. Our list does not include Tooligie, Cowell, Mangalo or Murdinga, although Viterra or
   Bunge weekly reports name the first three receiving grain in earlier seasons. Did any of
   them receive grain in 2025/26?
3. Kapinnie appears in Bunge's segregations table but we found no 2025/26 weekly-report
   mention of it. Did Kapinnie receive grain in 2025/26? Same question for Nunjikompita.
4. On 7 July 2026 Bunge offered six surplus South Australian bulk-handling sites for tender
   through Elders, including Murdinga (23,400 t) on the Eyre Peninsula, with binding offers
   due 21 August 2026. Has that tender concluded, and has Murdinga been sold? If so, does
   the buyer intend to operate it as a receival site?
5. Bunge's own statement described those sites as no longer part of its operational
   network. Is that the correct wording, and would Bunge like to expand on it?
6. In June 2019 Viterra announced the closure of 17 up-country sites, six of them on the
   Eyre Peninsula. The reasons reported at the time were increased average truck size,
   quality-management and food-safety requirements, and those sites representing less than
   2 per cent of total receivals on a five-year average. Is that a complete and accurate
   statement of the reasons? Does Bunge wish to add anything about the decision, which was
   taken before it acquired Viterra?
7. We date the completion of the Bunge/Viterra merger to 2 July 2025 and the renaming of
   Viterra Operations Pty Ltd to Bunge Operations Pty Ltd to 21 August 2025. Are both dates
   correct?
8. In August 2025 the Stock Journal reported that GrainCorp, CBH, Qube, Bunge and Louis
   Dreyfus were "tipped to top the potential buyers' list" for T-Ports. Has Bunge made, or
   is Bunge considering, any offer or approach for T-Ports or Australian Grain Export? A
   "no" or "we don't comment on market speculation" will be reported as given.
9. Our measure is drive time from production cells to the nearest receival point by owner.
   On our figures, the tonne-weighted drive to the nearest Bunge point on the peninsula in
   2025/26 is a median 16.5 minutes and a 99th percentile of 58.3. Does that match Bunge's
   own understanding of its catchment, and is there a published or shareable figure we
   should be using instead?
10. Is there anything in the enclosed draft that Bunge considers factually wrong? We will
    correct it.

### 4.2 T-Ports — CEO Nathan Kent

*Claims that concern T-Ports:* the 2025/26 closure of the Lock and Kimba bunkers and the
quoted wording; the 2023/24 operating status of both bunkers; site capacities; Lucky Bay's
description and location; the sale process; and the characterisation of T-Ports' 2024
submission to the ACCC.

1. T-Ports' harvest page currently shows "Site closed for 25/26 season" against both Lock
   and Kimba, with Lucky Bay and Wallaroo operating. Is that correct for both sites for the
   2025/26 season?
2. Did the Lock and Kimba bunkers receive grain in 2023/24? In 2024/25? We have found no
   published record either way, and our 2024/25 position is currently an assumption we
   would rather replace with a fact.
3. Will either bunker open for the 2026/27 season? Will Lucky Bay?
4. We use 384,000 t for Lucky Bay (24,000 t at the terminal, 360,000 t in ten bunkers),
   140,000 t for Lock and "more than 150,000 t" for Kimba, from your website and the ACCC's
   2021 determinations. Are those the right figures?
5. Is there anything you would want said about *why* the bunkers are closed for 2025/26?
   The draft states expressly that the reason is not established and that a drought year and
   bunker economics are sufficient explanations, and we would rather publish your account
   than leave the question open.
6. What share of Eyre Peninsula grain does T-Ports receive in a normal season? Nothing is
   published, and we have declined to publish our model's estimate. A figure, or a range,
   would replace an acknowledged gap.
7. The sale process: is the business still for sale as at today's date, and is the reported
   figure of about $250 million, or "offers of more than $200 million", one T-Ports or Nash
   Advisory recognises?
8. In October 2024 T-Ports lodged a submission to the ACCC opposing Viterra's proposed
   acquisition of the Grainflow sites. Would you provide a copy? We would rather describe
   what it argued than characterise it from press reports.
9. Our figures put the mean drive from an Eyre Peninsula production cell to Lucky Bay at
   about 125 minutes, and record its coordinate only to town precision. If you can give us
   the facility coordinate, we will use it and republish the sensitivity.
10. Is anything in the enclosed draft wrong about T-Ports?

### 4.3 Nash Advisory

*Claims that concern Nash Advisory:* that it is running the T-Ports sale; the ~$250m
figure; the December 2025 packaging with Australian Grain Export; the "unsold at last
report" status; and the reported list of tipped buyers.

1. Is Nash Advisory still running the sale of T-Ports, and is the business still for sale
   as at today's date?
2. Reporting from July 2025 attributes a value of about $250 million to "other media
   reports", and a separate report refers to offers of more than $200 million. Has any
   price been published by the vendor or by Nash Advisory? If not, we will say so.
3. Is T-Ports still offered as a package with Australian Grain Export?
4. In August 2025 a trade column named GrainCorp, CBH, Qube, Bunge and Louis Dreyfus as
   companies tipped to top the buyers' list; reporting in December 2025 named Louis Dreyfus,
   Olam Agri and AGT Foods Australia. We do not intend to publish any list we cannot
   source. Is there anything you can say on the record about whether any named party has
   made an approach — including a simple statement that the adviser does not name parties?
5. Would you correct anything in the enclosed draft's account of the sale process?

### 4.4 Grain Producers SA

*Claims that concern GPSA:* the characterisation of its role in the 2024 Grainflow
consultation, and the characterisation of the 2024 opposition as "a grower survey and
letters". Both are being corrected in the draft you are being sent, and we would like your
account before we finalise.

1. Our earlier draft said that GPSA opposed Viterra's proposed acquisition of the Grainflow
   sites. On the reporting we have since read, GPSA surveyed its growers and put the
   concerns raised to the ACCC without taking a position of its own. Is that a fair
   description, and is there a better form of words?
2. Would you provide GPSA's submission to the ACCC, or a summary of it? We would rather
   describe what it argued than characterise it second-hand.
3. What did the grower survey find? If any of it is publishable we would like to report it,
   attributed.
4. Does GPSA have a position on the Wheat Port Code review and the proposal for an
   industry-managed code developed by Grain Trade Australia? Reporting in July 2026
   described grower groups as split, naming GrainGrowers and Grain Producers Australia; we
   do not want to attribute either position to GPSA by proximity.
5. The piece measures how far Eyre Peninsula production sits from a receival point not
   operated by Bunge. Is distance to an alternative receival point the thing growers
   actually raise with you, or is the live issue something else — price transparency,
   segregation availability, delivery windows, queue times? We are asking because the next
   piece should measure what matters rather than what is easiest to compute.
6. Is anything in the enclosed draft wrong or unfair?

### 4.5 Department for Infrastructure and Transport (SA) / RDA Eyre Peninsula

*Claims that concern you:* nothing in the current draft is attributed to either body. You
are being sent it because the piece's subject — where Eyre Peninsula grain can be delivered,
and how far it travels — bears directly on the road network you fund and plan, and because
we would rather be corrected before publication than after.

1. Since the end of grain rail on the peninsula in May 2019, does either body hold
   corridor-level truck movement counts for grain freight — as against the peninsula-wide
   figures that circulate publicly?
2. Do you hold, or can you point to, any published receival or throughput data for Eyre
   Peninsula sites at finer geography than the single regional total in the operator's
   weekly harvest reports? The absence of that geography is the reason a whole tier of this
   analysis could not be validated, and it is stated as such in the piece.
3. Is there a current position on the roads named in the 2018 freight study, and on the
   corridors that absorbed traffic after the rail cessation?
4. Would either body find a corridor-level model of grain truck movements useful, and in
   what form?
5. Is anything in the enclosed draft wrong about the peninsula's freight task?

### 4.6 ACCC — mergers team (courtesy)

*Claims that concern the ACCC:* the account of the 2021 Bulk Wheat Code determinations, the
2024 Grainflow informal review, and the status of the Wheat Port Code. This is sent as a
courtesy and to check the regulatory record, not to invite a comment on any party.

1. We describe the determinations as follows: on 27 April 2021 the ACCC exempted Viterra's
   Port Adelaide Inner Harbour and Outer Harbor terminals from Parts 3–6 of the Bulk Wheat
   Code and refused exemption for Wallaroo and Port Giles; on 20 July 2021 it refused
   exemption for Port Lincoln and Thevenard, which remain subject to the full Code. Is that
   accurate?
2. We have removed an earlier characterisation of the July 2021 refusals as a finding that
   the peninsula's ports lack competitive constraint, on the basis that the determinations
   record Lucky Bay as imposing "a material level of competitive constraint" in parts of the
   Port Lincoln catchment and "limited" constraint on Thevenard. Is the corrected
   description fair?
3. For the Grainflow review we take from the public register: review commenced 10 October
   2024; Viterra advised on 13 December 2024 that the acquisition would not proceed; the
   ACCC discontinued the review on 17 December 2024; no findings were announced. Correct?
4. The register publishes the Market Inquiries Letter but no third-party submissions. Are
   any submissions to that review publicly available?
5. We describe the Wheat Port Code as in force, its sunsetting deferred 24 months from 1
   October 2024 to 1 October 2026 by certificate F2024L01138, with the ACCC having submitted
   that the Code should be allowed to sunset and DAFF's review recommending an
   industry-managed code. Is that an accurate statement of the current position?
6. A general question, on which we would welcome guidance rather than comment on any
   party: our measure is tonne-weighted drive time from production cells to the nearest
   receival point by owner, at a range of thresholds. Is that a form of catchment
   substitution evidence the Commission finds useful, and is there a published methodology
   we should be aligning to? We are conscious that the 2021 determinations say distance is
   only one factor, and the piece quotes that.
7. Is anything in the enclosed draft wrong about the regulatory record?

---

## 5. What to re-check immediately before publication

> **All five checked 2026-08-31 — results and evidence in `docs/data_refresh_2026-08-31.md` §2.**
> Summary: the page has **not** rolled to 26/27, but a mid-harvest Internet Archive snapshot
> (14 Jan 2026) now carries the closure line for **both** bunkers beside live segregations at
> Lucky Bay and Wallaroo; no Murdinga tender outcome is published (offers closed 21 Aug 2026);
> no T-Ports sale completion is published; and the Wheat Port Code is **not** a bare sunset —
> a three-year streamlined **remake was drafted and consulted on in July 2026** and no
> remake/repeal decision is published (`wheat-port-code-2026` in `data/SOURCES.md`). The three
> pinned files are git-clean and the headline re-runs at 66.8%. Re-check items 2–4 again on the
> day: all three can move between now and 1 October.

- The T-Ports harvest page (archived copy vs live), and whether it has rolled to 26/27.
- The Murdinga tender outcome.
- Whether T-Ports has been sold.
- The Wheat Port Code's status against the 1 October 2026 sunset date — this piece may be
  published in the last weeks before it.
- `git status` clean on `pipeline/r8_choice_geometry.py`, `pipeline/r8a_coord_sensitivity.py`
  and `data/processed/sites.geojson`, with the published commit hash cited on the page.
