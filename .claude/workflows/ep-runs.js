export const meta = {
  name: 'ep-runs',
  description: 'R1-R4: gateway removal, relief-valve test, rationalisation and corridor freight deltas for the EP competition piece',
  whenToUse: 'ONLY after ep-gate returns GO or PARTIAL. If the gate was NO-GO these runs are not publishable and should not be run.',
  phases: [
    { title: 'Extend', detail: 'add siteClosures param + per-corridor truck-km export to the engine', model: 'opus' },
    { title: 'Run', detail: 'R1 A24 sweep, R2 relief valve, R3 rationalisation, R4 corridor deltas', model: 'opus' },
    { title: 'Verify', detail: 'adversarial check per run', model: 'opus' },
    { title: 'Synthesize', detail: 'consolidated findings doc', model: 'opus' },
  ],
}

const CONTEXT = `
Repo: the Windrow EP grain supply-chain simulation (cwd is the repo root).
Read docs/analysis_plan_ep_competition.md, docs/gate_findings.md, and data/ASSUMPTIONS.md
entries A1, A2, A4, A15, A24 before doing anything.

Ground rules:
- Do NOT git commit or push. Leave changes in the working tree.
- Never publish a Tier 3 (dynamic) number as a point estimate. A24 states retentionShare
  and luckyBayBias are NOT separately identified. Ranges only, with the ridge stated.
- Do NOT refit any calibrated parameter. Run at the existing fitted vector.
- Every number must be reproducible by a command you state.
- Honour docs/analysis_plan_ep_competition.md section 6, "What we must not claim".
`

const RESULT = {
  type: 'object',
  additionalProperties: false,
  required: ['run', 'status', 'command', 'headline', 'numbers', 'range', 'caveats'],
  properties: {
    run: { type: 'string' },
    status: { type: 'string', enum: ['done', 'partial', 'blocked'] },
    command: { type: 'string' },
    headline: { type: 'string' },
    numbers: { type: 'string', description: 'markdown table' },
    range: { type: 'string', description: 'the reported range and the identification ridge it spans, or "n/a — not a Tier 3 number"' },
    caveats: { type: 'array', items: { type: 'string' } },
  },
}

const VERDICT = {
  type: 'object',
  additionalProperties: false,
  required: ['refuted', 'confidence', 'reasoning', 'specificErrors'],
  properties: {
    refuted: { type: 'boolean' },
    confidence: { type: 'string', enum: ['low', 'medium', 'high'] },
    reasoning: { type: 'string' },
    specificErrors: { type: 'array', items: { type: 'string' } },
  },
}

// ------------------------------------------------- Extend (barrier: everything needs it)
phase('Extend')
const extended = await agent(`${CONTEXT}

TASK: Extend the sim engine with two capabilities the R1-R4 runs need. This is the only
task in this workflow permitted to edit packages/sim/src/** — every later agent depends
on your changes, so keep them minimal, typed and tested.

1. A 'siteClosures' parameter: string[] of site names that are forced closed for the run,
   on top of the existing status gating (engine.ts around line 376). Add it to
   Params in types.ts and defaultParams() in params.ts (default: empty array).

2. Per-corridor loaded truck-km accumulation, exported as a table. The truck-flow heatmap
   already knows each trip's path key — find that machinery (packages/sim/src/corridors.ts
   and the heatmap code in app/) and expose a per-corridor aggregate on the run result
   rather than building a second one.

Run 'npm --workspace packages/sim run test' and report the result. The existing scenario
numbers in docs/scenarios.md must be UNCHANGED for the baseline with default params —
verify this by running 'npx tsx packages/sim/scripts/scenarios.ts 2025/26' and diffing
against the committed docs/scenarios_data.json. If anything moved, you have introduced a
regression: fix it or report blocked.

Return a short plain-text description of exactly what you added and how a later agent
should call it.`,
  { label: 'extend:engine', model: 'opus', effort: 'high' })

log(`Engine extended. ${extended ? 'Proceeding to runs.' : 'Extend FAILED — later runs may be blocked.'}`)

const API = extended || '(the extend step failed; work out the API yourself from the source)'

const RUNS = [
  {
    id: 'R1',
    model: 'opus',
    effort: 'high',
    prompt: `TASK — R1: gateway removal, ranged over the A24 identification ridge.

Set luckyBayBias to 0 (engine.ts:866 already gates T-Ports attractiveness on it, so this
removes T-Ports from grower choice) and sweep across the retention/Lucky-Bay ridge at
retentionShare in {0.055, 0.069, 0.100, 0.143}, pairing each with the corresponding
luckyBayBias value from docs/calibration_search.json where the search log provides one.

Report, AS A RANGE across the ridge: where the 0.42-0.51 Mt of T-Ports intake goes; which
Bunge sites hit the hard capacity ceiling (the #29 change made capacity a hard ceiling);
the resulting peak site queue and road truck-km.

A24 is explicit that these two knobs trade off one-for-one and are not separately
identified, and that the fit buys part of its match with T-Ports throughput nothing
constrains. A point estimate here is the most attackable number in the entire piece.
Write docs/r1_gateway_removal.md.`,
  },
  {
    id: 'R2',
    model: 'opus',
    effort: 'high',
    prompt: `TASK — R2: the relief-valve test. Likely the strongest dynamic finding in the piece.

The existing bumper scenario (productionScale 1.3) shows Bunge sites capping out and
+0.14 Mt SPILLING TO T-Ports (0.42 -> 0.56 Mt). So T-Ports is not only a price competitor,
it is the network's surge capacity.

Run bumper x T-Ports-removed (productionScale 1.3, luckyBayBias 0), across the same A24
ridge as R1. Report: tonnes that end up with nowhere to go (on-farm retention / balked
loads — see the queueBalk params and the #27 change), the extra cart distance for grain
that does get delivered, and which sites bind.

Then answer the question a reader actually has: in a big year, what does the network do
without the relief valve? Range, not point. Write docs/r2_relief_valve.md.`,
  },
  {
    id: 'R3',
    model: 'opus',
    effort: 'high',
    prompt: `TASK — R3: post-merger rationalisation.

Using the new siteClosures param:
${API}

Close the N most marginal Bunge upcountry sites and measure the catchment shift, extra
cart distance and corridor loading.

Do NOT invent the selection rule. The same network has rationalised twice already: 6 sites
closed in 2019 (Minnipa, Kyancutta, Cungena, Waddikee, Kielpa, Wharminda) and 5 sit
dormant (Penong, Nunjikompita, Darke Peak, Buckleboo, Elliston). Rank sites by simulated
throughput per unit capacity at baseline, check whether that ranking RETRODICTS the 11
sites that actually got closed or mothballed, and report how well it does. If the rule
retrodicts poorly, say so — that bounds how much weight the forward-looking scenario can
carry, and that caveat belongs in the piece.

Then apply the rule forward for N in {3, 5}. Frame every output as "what rationalisation
of this shape would do", never as a prediction. Write docs/r3_rationalisation.md.`,
  },
  {
    id: 'R4',
    model: 'sonnet',
    effort: 'high',
    prompt: `TASK — R4: per-corridor freight deltas for the roads angle.

Using the new per-corridor export:
${API}

Produce a per-corridor loaded truck-km table (CSV + markdown) for: baseline, T-Ports
removed (R1 central case), and rationalised (R3, N=5). Name the real corridors — Tod
Highway, Lincoln Highway, Birdseye Highway, Flinders Highway and the Wharminda/Balumbah
roads named in the rail-closure reporting.

Context this feeds, for the framing only — do not restate as your own findings: rail
ceased May 2019; ~64,000 60-tonne truck movements a year through Port Lincoln; ~$25m of
federal road money against a $220m Aurizon/Viterra ask to reopen Port Lincoln-Cummins,
Wudinna and Kimba; an RAA survey of 1,300+ EP road users with road maintenance the top
concern for 76%.

Truck-km are a Tier 3 output and inherit A1 (payload) — state that prominently: the
headline is the RELATIVE corridor shift, not the absolute vehicle count.
Write docs/r4_corridor_freight.md and the CSV alongside it.`,
  },
]

// Pipeline, not a barrier: R1's verification starts while R3 is still running.
const results = await pipeline(
  RUNS,
  (r) => agent(`${CONTEXT}\n\n${r.prompt}`, { label: `run:${r.id}`, phase: 'Run', model: r.model, effort: r.effort, schema: RESULT }),
  (res, r) => {
    if (!res) return null
    return agent(`${CONTEXT}

TASK: Try to REFUTE run ${r.id}. Default to refuted=true if uncertain.

The claim:
${res.headline}

${res.numbers}

Reported range: ${res.range}
Caveats offered: ${(res.caveats || []).join('; ')}
Reproduce command: ${res.command}

Re-run the command yourself and check the numbers match. Then attack: is a Tier 3 number
stated as a point estimate anywhere? Was any calibrated parameter altered (check
git diff on packages/sim/src/calibrated.json and params.ts)? Does the conclusion survive
at BOTH ends of the A24 ridge, or only at the convenient end? Is an assumption relied on
without citation? Is intent imputed to any company? Does the baseline still reproduce
docs/scenarios_data.json?`,
      { label: `verify:${r.id}`, phase: 'Verify', model: 'opus', effort: 'xhigh', schema: VERDICT })
      .then((v) => ({ run: r.id, result: res, verdict: v }))
  },
)

const done = results.filter(Boolean)
log(`${done.length}/${RUNS.length} runs completed; ${done.filter((d) => d.verdict && d.verdict.refuted).length} refuted by verification.`)

phase('Synthesize')
const synthesis = await agent(`${CONTEXT}

TASK: Write docs/r1_r4_findings.md consolidating these runs.

${JSON.stringify(done, null, 2)}

Sections:
1. What survived verification, and what did not — outstanding defects listed, not fixed
   or dismissed.
2. The findings that are strong enough to publish, each with its tier, its range, and its
   reproduce command.
3. The findings that are NOT strong enough, and why — be specific.
4. Which sections of the piece each surviving finding supports.

If verification refuted a run, that run does not appear in section 2. Be blunt; a short
honest document beats a long confident one.`,
  { label: 'synthesize:runs', model: 'opus', effort: 'high' })

return { runs: done.map((d) => ({ run: d.run, status: d.result.status, headline: d.result.headline, refuted: d.verdict ? d.verdict.refuted : null })), synthesis }
