export const meta = {
  name: 'ep-gate',
  description: 'R5 retrospective validation + R0 choice geometry — the go/no-go gate for the EP competition piece',
  whenToUse: 'Run first, before any other EP-competition analysis. Decides whether the dynamic (Tier 3) layer is publishable.',
  phases: [
    { title: 'Scout', detail: 'map engine site-gating and what per-site observed receivals actually exist', model: 'sonnet' },
    { title: 'Build', detail: 'R0 geometry script + R5 network-state override and validation', model: 'opus' },
    { title: 'Verify', detail: 'adversarial refutation of both headline claims', model: 'opus' },
    { title: 'Decide', detail: 'gate verdict written to docs/gate_findings.md', model: 'opus' },
  ],
}

const CONTEXT = `
Repo: the Windrow EP grain supply-chain simulation (cwd is the repo root).
Read docs/analysis_plan_ep_competition.md FIRST — it defines the piece, the claims ladder,
and the runs R0 and R5. Also read data/ASSUMPTIONS.md entries A1, A2, A4, A15, A24.

Ground rules for every agent in this workflow:
- Do NOT git commit, git push, or create branches. Leave changes in the working tree.
- Do NOT edit docs/analysis_plan_ep_competition.md.
- Every number you produce must be reproducible by a command you state.
- If something in the plan turns out to be impossible or wrong, SAY SO plainly and return
  that as the finding. A negative result here is valuable, not a failure.
`

const SCOUT_ENGINE = {
  type: 'object',
  additionalProperties: false,
  required: ['openRule', 'injectionPoint', 'filesToEdit', 'canInjectNetworkState', 'notes'],
  properties: {
    openRule: { type: 'string', description: 'exactly how the engine decides a site is open/closed today, with file:line' },
    injectionPoint: { type: 'string', description: 'the cleanest place to inject an arbitrary network state (which sites operate), with file:line' },
    filesToEdit: { type: 'array', items: { type: 'string' }, description: 'repo-relative paths that a network-state override would have to touch' },
    canInjectNetworkState: { type: 'boolean' },
    notes: { type: 'string', description: 'gotchas: season gating, dormant vs closed_2019 vs closed_2025_26_season, capacity nulls, load_bundle behaviour' },
  },
}

const SCOUT_DATA = {
  type: 'object',
  additionalProperties: false,
  required: ['perSiteObserved', 'granularity', 'seasonsCovered', 'r5Feasible', 'r5FallbackDesign', 'notes'],
  properties: {
    perSiteObserved: { type: 'boolean', description: 'do we hold OBSERVED receivals broken down per site, or only per region/network?' },
    granularity: { type: 'string', description: 'the finest observed breakdown that actually exists, named precisely' },
    seasonsCovered: { type: 'string' },
    r5Feasible: { type: 'boolean', description: 'can R5 validate redistribution at the level the plan assumes?' },
    r5FallbackDesign: { type: 'string', description: 'if not per-site, the strongest validation design the available granularity DOES support' },
    notes: { type: 'string' },
  },
}

const BUILD_RESULT = {
  type: 'object',
  additionalProperties: false,
  required: ['status', 'script', 'command', 'headline', 'numbers', 'caveats'],
  properties: {
    status: { type: 'string', enum: ['done', 'partial', 'blocked'] },
    script: { type: 'string', description: 'repo-relative path of the script written' },
    command: { type: 'string', description: 'exact command that reproduces the numbers' },
    headline: { type: 'string', description: 'one sentence: the single most important number and what it means' },
    numbers: { type: 'string', description: 'the full result table as markdown' },
    caveats: { type: 'array', items: { type: 'string' }, description: 'what would make these numbers wrong' },
  },
}

const VERDICT = {
  type: 'object',
  additionalProperties: false,
  required: ['refuted', 'confidence', 'reasoning', 'specificErrors'],
  properties: {
    refuted: { type: 'boolean', description: 'true if the claim does NOT hold as stated' },
    confidence: { type: 'string', enum: ['low', 'medium', 'high'] },
    reasoning: { type: 'string' },
    specificErrors: { type: 'array', items: { type: 'string' }, description: 'concrete defects with file:line or a number that is wrong' },
  },
}

// ---------------------------------------------------------------- Scout
log('Scouting the engine and the observed data before building anything.')

const [engineScout, dataScout] = await parallel([
  () => agent(`${CONTEXT}

TASK: Map how site opening/closing works in the sim engine.

The piece needs to run the sim against ARBITRARY historical network states:
  (a) pre-2019: the 6 closed_2019 sites (Minnipa, Kyancutta, Cungena, Waddikee, Kielpa,
      Wharminda) OPEN alongside everything else
  (b) 2023/24: T-Ports Lock and Kimba bunkers OPEN (see A15)
  (c) 2025/26: the network as currently modelled

Read packages/sim/src/engine.ts, packages/sim/src/params.ts, packages/sim/src/types.ts,
packages/sim/scripts/load_bundle.ts and data/processed/sites.geojson.

Determine: how "open" is decided today (engine.ts around line 376 gates on status ===
"dormant"); what happens to sites with status closed_2019 and closed_2025_26_season; what
load_bundle does with them; whether the 6 closed_2019 sites even have the capacity and
coordinate data needed to simulate them (their capacity_t is null — say what that breaks
and what a defensible capacity would be, citing A4's method for the other sites).

Return the implementation spec. Do NOT write code in this task.`,
    { label: 'scout:engine', phase: 'Scout', model: 'sonnet', effort: 'medium', schema: SCOUT_ENGINE }),

  () => agent(`${CONTEXT}

TASK: Establish what OBSERVED receival data actually exists, at what granularity.

This is the single most important unknown in the whole plan. R5 assumes we can compare
simulated redistribution against observed receivals AT SURVIVING NEIGHBOUR SITES. If the
published receivals are only broken down by region (e.g. Viterra's "Western" region) and
not per site, that per-site validation is impossible and R5 must be redesigned.

Inspect data/processed/receivals_weekly.parquet, receivals_monthly.parquet and
receivals_notes.jsonl (use python via the Bash tool; pandas/pyarrow should be available —
if not, say so). Report the actual columns, the actual breakdown keys, and the seasons
covered. Check whether receivals_notes.jsonl names individual sites (the stakeholder
review says the reports "name busiest sites weekly") and whether that could be turned into
a per-site signal.

Then state plainly: is R5 feasible as planned? If not, design the strongest validation the
available granularity DOES support, and say how much weaker it is.

Do NOT write analysis code beyond throwaway inspection.`,
    { label: 'scout:data', phase: 'Scout', model: 'sonnet', effort: 'medium', schema: SCOUT_DATA }),
])

log(`Scout: per-site observed receivals = ${dataScout ? dataScout.perSiteObserved : 'unknown'}; R5 feasible as planned = ${dataScout ? dataScout.r5Feasible : 'unknown'}`)

const engineSpec = engineScout ? JSON.stringify(engineScout, null, 2) : '(engine scout failed — work it out yourself)'
const dataSpec = dataScout ? JSON.stringify(dataScout, null, 2) : '(data scout failed — work it out yourself)'

// ---------------------------------------------------------------- Build
// R0 and R5 run concurrently on DISJOINT files. R5 owns packages/sim/src/**; R0 must not
// touch it. No worktrees needed as long as that boundary holds.

const [r0, r5] = await parallel([
  () => agent(`${CONTEXT}

TASK — R0: ownership choice-set geometry. THIS IS THE HEADLINE OF THE PIECE.

Write ONE new standalone script that computes, with NO simulation and NO fitted parameter:
for each grain-production cell on the Eyre Peninsula, the drive time to the nearest
Bunge-operated receival point versus the nearest INDEPENDENTLY OWNED one.

Inputs: data/processed/sites.geojson (has an 'operator' field: "Bunge (ex-Viterra)",
"T-Ports", "ex-Viterra"), data/processed/roads.graph.json, and
data/processed/production_districts.parquet. Reuse whatever routing/travel-time code the
sim already has (look at packages/sim/src/corridors.ts and how load_bundle builds any
travel matrix) rather than inventing a second router — but note the constraint below.

HARD CONSTRAINT: you must NOT edit anything under packages/sim/src/. Another agent owns
those files concurrently. Import from them read-only, or copy the small amount of routing
logic you need into your new script. Put your script at
packages/sim/scripts/choice_geometry.ts (a NEW file) or pipeline/r8_choice_geometry.py —
your call, whichever reuses more existing code.

Compute at THREE network states:
  1. pre-2019  — the 6 closed_2019 sites open, T-Ports not yet existing
  2. 2023/24   — current Bunge network + T-Ports Lucky Bay + Lock and Kimba bunkers open
  3. 2025/26   — current Bunge network + T-Ports Lucky Bay only

Outputs for each state:
  - tonne-weighted share of EP production whose nearest INDEPENDENT receival point is
    >30 / >60 / >90 minutes beyond its nearest Bunge point
  - tonne-weighted share with NO independent option at all within a plausible cart range
  - the trajectory across the three states (this is the headline number)

Definitional care, and be explicit about your choice in the output: "independent" means
not operated by the incumbent. In state 1 the pre-2019 network was ALL one operator
(ex-Viterra) — so the honest framing there is not "independent alternatives" but "number
of receival choices", and the two must not be silently conflated. Handle this properly and
document it; a reviewer will attack exactly this.

Write results to docs/r0_choice_geometry.md plus a machine-readable JSON alongside it.
State the exact reproduce command.`,
    { label: 'build:R0-geometry', phase: 'Build', model: 'opus', effort: 'high', schema: BUILD_RESULT }),

  () => agent(`${CONTEXT}

TASK — R5: retrospective validation. THIS IS THE GO/NO-GO GATE.

Engine scout findings:
${engineSpec}

Data scout findings:
${dataSpec}

If the data scout reports that per-site observed receivals do NOT exist, adopt its
fallback design instead of the plan's design, and say clearly in your result that you did
so and what was lost.

Build: a way to run the sim at an arbitrary historical network state (which sites operate),
then test whether the model reproduces redistribution that ACTUALLY HAPPENED:

  Test A (primary): the 2019 closure of 6 sites. Ten seasons of weekly receivals
  (2016/17-2025/26) straddle it. Run the pre-2019 network, close the 6, and compare
  simulated redistribution against observed receivals at the granularity that exists.
  IMPORTANT CONFOUND you must address head-on: grain trains ceased in May 2019, the same
  year. Site closure and rail closure are simultaneous, so a naive comparison cannot
  attribute the shift to either one. Say how you separate them, or say that you cannot —
  "cannot separate" is an acceptable and important finding.

  Test B (secondary): the T-Ports Lock/Kimba bunker closure, 2023/24 (open) vs 2025/26
  (closed). Note A15: the 2024/25 closure is ASSUMED, not verified — do not treat it as
  observed.

You own packages/sim/src/** for this run; another agent is concurrently writing a
standalone geometry script and will not touch those files.

Run npm --workspace packages/sim run test after any engine change and report the result.
The existing calibration must not regress: check docs/calibration_report.md targets still
hold, and say so explicitly.

CRITICAL — the failure mode to avoid: it is easy to "validate" by tuning until the model
matches. Do NOT refit any calibrated parameter to make this pass. Run at the existing
fitted vector. If it does not reproduce the observed shift, REPORT THAT. A failed gate is
a real and useful result: it means the piece publishes on Tiers 1-2 only.

Write results to docs/r5_validation.md. State the exact reproduce command.`,
    { label: 'build:R5-validation', phase: 'Build', model: 'opus', effort: 'xhigh', schema: BUILD_RESULT }),
])

log(`Build: R0 ${r0 ? r0.status : 'FAILED'} | R5 ${r5 ? r5.status : 'FAILED'}`)

// ---------------------------------------------------------------- Verify
// Skeptics are as strong as the builders on purpose. Cheap verifiers rubber-stamp.

const r0Text = r0 ? `${r0.headline}\n\n${r0.numbers}\n\nCaveats: ${(r0.caveats || []).join('; ')}\n\nScript: ${r0.script}` : 'R0 produced nothing.'
const r5Text = r5 ? `${r5.headline}\n\n${r5.numbers}\n\nCaveats: ${(r5.caveats || []).join('; ')}\n\nScript: ${r5.script}` : 'R5 produced nothing.'

const verdicts = await parallel([
  () => agent(`${CONTEXT}

TASK: Try to REFUTE the R0 geometry result. Default to refuted=true if you are uncertain.

The claim:
${r0Text}

Read the script it names and re-derive at least two of its headline numbers independently.
Attack specifically: is production correctly tonne-weighted, or is it counting cells?
Is the operator tagging right — are the 5 'dormant' Bunge sites and the 6 'closed_2019'
'ex-Viterra' sites handled correctly and not silently counted as operating? Is
"independent" defined consistently across the three network states, and is the pre-2019
state (single operator) being illegitimately compared with the later ones? Are travel
times real routed times or straight-line? Does the result depend on any fitted parameter —
it must not; if it does, that is a fatal defect for the piece's claims ladder.`,
    { label: 'verify:R0', phase: 'Verify', model: 'opus', effort: 'xhigh', schema: VERDICT }),

  () => agent(`${CONTEXT}

TASK: Try to REFUTE the R5 validation result. Default to refuted=true if you are uncertain.

The claim:
${r5Text}

Read the script and the changed engine code. Attack specifically: was any parameter
refit or nudged to make the validation pass (check git diff on packages/sim/src/calibrated.json
and params.ts)? Is the 2019 rail-closure confound genuinely addressed or waved at? Is the
comparison out-of-sample, or is it testing on data the model was calibrated on (the fit
used 2023/24 + 2025/26 with 2024/25 held out — so validating on those seasons is NOT
out-of-sample)? Are the capacities invented for the 6 closed_2019 sites doing the work?
Does A15's assumed 2024/25 closure get treated as observed anywhere?

Then answer the question that actually matters: does this result justify publishing
Tier 3 (dynamic) claims, or not?`,
    { label: 'verify:R5', phase: 'Verify', model: 'opus', effort: 'xhigh', schema: VERDICT }),

  () => agent(`${CONTEXT}

TASK: Compliance check against the piece's own constraints.

Read section 6 "What we must not claim" of docs/analysis_plan_ep_competition.md, then read
everything produced in this run: docs/r0_choice_geometry.md, docs/r5_validation.md, and
the git diff of the working tree.

Refute if ANY of these hold: a forbidden claim is made or implied; a Tier 3 (dynamic)
number is stated as a point estimate where A24 requires a range; an assumption (A1, A2,
A4, A15, A24) is relied on without being cited; intent is imputed to any company for the
Lock/Kimba or 2019 closures; individual site performance is ranked; the cash-price series
is used as price evidence.

Also check the prose is defensible for publication naming a real company: statements of
fact must be attributable to a published source or to a stated model run.`,
    { label: 'verify:compliance', phase: 'Verify', model: 'opus', effort: 'high', schema: VERDICT }),
])

const live = verdicts.filter(Boolean)
const refutedCount = live.filter((v) => v.refuted).length
log(`Verify: ${refutedCount} of ${live.length} checks refuted the work.`)

// ---------------------------------------------------------------- Decide
const decision = await agent(`${CONTEXT}

TASK: Write the gate verdict to docs/gate_findings.md.

R0 result:
${r0Text}

R5 result:
${r5Text}

Adversarial verdicts:
${JSON.stringify(live, null, 2)}

Write a short, honest document with these sections:
1. VERDICT — one of: GO (Tier 3 publishable), PARTIAL (Tier 3 as ranged sensitivity only),
   or NO-GO (publish on Tiers 1-2 only). Justify in three sentences.
2. The headline geometry numbers, as a table, with the reproduce command.
3. What the validation did and did not establish, including any confound that could not
   be separated.
4. Defects the verifiers found that are still OUTSTANDING — do not quietly fix or
   dismiss them, list them.
5. What changes in docs/analysis_plan_ep_competition.md as a result (describe the edits;
   do NOT make them).

Be blunt. If the verifiers refuted the work, the verdict is NO-GO or PARTIAL and the
document says so in the first line. Do not write a document that reads like the work
succeeded if it did not.`,
  { label: 'decide:gate', phase: 'Decide', model: 'opus', effort: 'high' })

return {
  r0: r0 ? { status: r0.status, headline: r0.headline, script: r0.script } : null,
  r5: r5 ? { status: r5.status, headline: r5.headline, script: r5.script } : null,
  refutedCount,
  totalChecks: live.length,
  decision,
}
