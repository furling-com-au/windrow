export const meta = {
  name: 'ep-cartage',
  description: 'What the independent gateway is worth to growers in cartage dollars, by district, across four network states — and an independent test of the public "$15/t" claim',
  whenToUse: 'After the roster fix and the headline cleanup. Produces the first output of this project a grower could use directly.',
  phases: [
    { title: 'Rate', detail: 'verify and register the published freight schedule; correct A18', model: 'opus' },
    { title: 'Build', detail: 'cartage cost per cell and district across four network states', model: 'opus' },
    { title: 'Claim', detail: 'test the public $15/t freight-saving claim under every fair reading', model: 'opus' },
    { title: 'Verify', detail: 'adversarial pass on the cost method and on the fairness of the claim test', model: 'opus' },
    { title: 'Report', detail: 'findings doc', model: 'opus' },
  ],
}

const CONTEXT = `
Repo: the Windrow EP grain supply-chain simulation (cwd is the repo root).
Read first: docs/gate_findings.md, docs/roster_audit_2026-08.md, docs/ready_to_draft.md,
docs/r0_choice_geometry.md, and data/ASSUMPTIONS.md A1, A4, A5, A11, A12, A18, A24.

State of play. The simulation's dynamic tier FAILED validation and is excluded from
everything published. What survives is Tier 1 (published fact) and Tier 2 (geometry over
road distances and site locations, using no fitted parameter). This run adds a new Tier 2
output: what the peninsula's one independent gateway is worth to growers in CARTAGE
DOLLARS, by district.

Why this matters: every published figure so far has been a share or a distance. A grower
cannot act on "two-thirds of production is more than 90 minutes from an alternative". They
can act on dollars per tonne where they farm. This is intended to be the first output of
the project a farmer could use.

Ground rules:
- Do NOT git commit or push. Leave changes in the working tree.
- Do NOT use the simulation engine, any fitted parameter, or anything from
  packages/sim/src/calibrated.json. If a number you need only exists there, the answer is
  that the number cannot be published, not that you should use it.
- Never state a number without the command that reproduces it.
- Cartage is only HALF of a delivery decision. Growers deliver where price minus cartage is
  best, and this project has NO price data (13 days of off-season cash bids, nothing else).
  Every output must say so. Do not imply a total grower benefit.
`

const RATE = {
  type: 'object',
  additionalProperties: false,
  required: ['found', 'rates', 'basis', 'baseYear', 'inflationTreatment', 'newerSchedule', 'a18Correction', 'caveats'],
  properties: {
    found: { type: 'boolean' },
    rates: { type: 'string', description: 'the published schedule verbatim, with units and distance bands' },
    basis: { type: 'string', description: 'what the rate covers: marginal or average? loaded km or round trip? does it include loading, waiting, or return legs? quote the source' },
    baseYear: { type: 'string' },
    inflationTreatment: { type: 'string', description: 'the treatment chosen and its justification, or a recommendation to publish in base-year dollars' },
    newerSchedule: { type: 'string', description: 'any more recent published schedule found, or "none found" with what was searched' },
    a18Correction: { type: 'string', description: 'the precise correction to A18, which currently claims no public EP $/t-km schedule exists' },
    caveats: { type: 'array', items: { type: 'string' } },
  },
}

const BUILD = {
  type: 'object',
  additionalProperties: false,
  required: ['status', 'script', 'command', 'measure', 'results', 'caveats'],
  properties: {
    status: { type: 'string', enum: ['done', 'partial', 'blocked'] },
    script: { type: 'string' },
    command: { type: 'string' },
    measure: { type: 'string', description: 'exactly what was computed, and why that is the right measure of a grower-facing cartage cost' },
    results: { type: 'string', description: 'markdown table: $/t by district for each of the four network states' },
    caveats: { type: 'array', items: { type: 'string' } },
  },
}

const CLAIM = {
  type: 'object',
  additionalProperties: false,
  required: ['readings', 'bestCase', 'tonneWeighted', 'whereZero', 'verdict', 'fairnessNote'],
  properties: {
    readings: { type: 'string', description: 'every plausible reading of the claim, enumerated, with what each would mean arithmetically' },
    bestCase: { type: 'string', description: 'the reading and location most favourable to the claim, and what our figures give there' },
    tonneWeighted: { type: 'string', description: 'the tonne-weighted average across EP under the most defensible reading' },
    whereZero: { type: 'string', description: 'where the saving is nil or negative, and for what share of production' },
    verdict: { type: 'string', enum: ['supported', 'supported-for-some', 'not-supported', 'cannot-test'] },
    fairnessNote: { type: 'string', description: 'whether the claimant would have a legitimate complaint about how this was tested' },
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

// ---------------------------------------------------------------- Rate
phase('Rate')
const rate = await agent(`${CONTEXT}

TASK: Establish a publishable freight rate, from a published source, and correct A18.

The pre-publication review found that ESCOSA's 2019 SA grain supply chain report publishes
a marginal trucking schedule — approximately A$0.12/t-km up to 50 km and A$0.11/t-km for
50-250 km, from AEGIC data verified against published Viterra freight rates. It is cached
at data/raw/reference/escosa_grain_supply_chain_2019.pdf, around text line 2536.

Read the actual document. Establish:
- the rates verbatim, with units and distance bands
- what the rate COVERS. This is the part that most affects the result and is easiest to
  get wrong: is it marginal or average? Loaded kilometres or round trip? Does it include
  loading, waiting time, or the empty return leg? Quote the source rather than inferring.
- the base year, and whether the figures are real or nominal
- whether any more recent published schedule exists (search; state what you searched)
- how to handle seven years of inflation, or whether the honest answer is to publish in
  2019 dollars and say so

Then correct A18 in data/ASSUMPTIONS.md. It currently states "No single public EP $/t-km
schedule exists." Be PRECISE, not sweeping: the ESCOSA schedule is SA-wide rather than
EP-specific, so A18's claim is partly right and partly wrong. Say exactly which part, and
do not overstate what has been found. Register the source in data/SOURCES.md in that
file's existing format, with a retrieval date.

A prior agent deliberately declined to use this schedule to justify the 90-minute drive
threshold, because a cost rate cannot justify a distance threshold. That was correct and
still stands. You are using it as a cost rate, which is what it is. Do not reopen the
threshold question.`,
  { label: 'rate:escosa', model: 'opus', effort: 'high', schema: RATE })

log(`Rate: ${rate ? (rate.found ? 'found' : 'NOT FOUND') : 'FAILED'}`)

// ---------------------------------------------------------------- Build
phase('Build')
const build = await agent(`${CONTEXT}

TASK: Compute what the independent gateway is worth to growers in cartage dollars.

Freight rate established by the previous step:
${rate ? JSON.stringify(rate, null, 2) : '(rate step failed — read the ESCOSA PDF yourself)'}

Write a new script (pipeline/r9_cartage.py, reusing r8_choice_geometry.py's graph, snapper
and parcel weights rather than building a second router). Compute, for each production cell
and aggregated by PIRSA district (WEP / EEP / LEP), the cartage cost of getting grain to a
receival point under FOUR network states:

  A. 2025/26 as it stands — Lucky Bay the only independent point, Lock and Kimba closed
  B. bunkers reopened — Lock and Kimba operating alongside Lucky Bay
  C. no independent at all — Lucky Bay unavailable
  D. pre-2019 — the network before T-Ports existed

FIRST, decide and justify the measure, because this is the crux and it is easy to get
wrong. "Distance to the nearest independent point" is NOT a cartage cost: a grower carts to
whichever point is best for them, which is usually the nearest one of any owner. The
gateway's cartage value is only realised by growers who actually use it. Consider at least:
cost to the nearest point of ANY owner (this is what most growers actually pay, and it
barely moves between states); cost to the nearest EXPORT-CAPABLE destination; and the
difference for the subset of production for which an independent point is genuinely the
nearest or near-nearest. State which you chose and why, and report more than one if the
choice is arguable.

Note a real structural subtlety: Lucky Bay is a PORT, not an upcountry silo, and T-Ports'
model had growers delivering to the Lock and Kimba bunkers or direct to Lucky Bay. Whatever
measure you choose has to be coherent about what a grower's truck actually does.

Report $/t by district for each state, plus the deltas between states. Write
docs/r9_cartage.md and a machine-readable JSON. State the reproduce command.`,
  { label: 'build:cartage', model: 'opus', effort: 'high', schema: BUILD })

log(`Build: ${build ? build.status : 'FAILED'}`)

// ---------------------------------------------------------------- Claim
phase('Claim')
const claim = await agent(`${CONTEXT}

TASK: Independently test a public claim.

Arowana's September 2021 release about its Lucky Bay investment states that the port
"generates road freight savings for grain growers from the Eyre Peninsula of up to $15 per
tonne". No working is published. It is repeated in circulation and nobody has checked it.

Our computation:
${build ? JSON.stringify(build, null, 2) : '(build step failed)'}

Freight rate:
${rate ? JSON.stringify(rate, null, 2) : '(rate step failed)'}

The claim is AMBIGUOUS and you must not test only the reading that is easiest to refute.
Enumerate every plausible reading and test each. At minimum consider: saving against
carting to Port Lincoln; against Thevenard; against the nearest Bunge upcountry site;
line-haul saved by the operator rather than by the grower; and whether "up to" means the
single most-favoured production cell (which is the natural reading of "up to", and the one
most favourable to the claimant).

Report: the reading and location where the claim is strongest and what our figures give
there; the tonne-weighted average across the peninsula under the most defensible reading;
where the saving is nil or negative and for what share of production; and a verdict.

FAIRNESS REQUIREMENT. We are publicly checking a company's promotional claim using our own
model. Steelman it first. If any fair reading supports it, say so plainly and lead with
that. If the claim holds for some growers and not others, that is the finding — "up to" is
a maximum, and a maximum being reached by few growers is not the same as the claim being
false. State explicitly whether Arowana or T-Ports would have a legitimate complaint about
how this was tested. If the honest answer is that the claim cannot be tested from published
data, say that instead of manufacturing a verdict.`,
  { label: 'claim:15pt', model: 'opus', effort: 'high', schema: CLAIM })

// ---------------------------------------------------------------- Verify
const verdicts = await parallel([
  () => agent(`${CONTEXT}

TASK: Try to REFUTE the cartage computation. Default to refuted=true if uncertain.

${JSON.stringify(build, null, 2)}

Rate used:
${JSON.stringify(rate, null, 2)}

Run the command yourself. Then attack the method specifically. Is a MARGINAL rate being
applied to full hauls as though it were an average? Is the rate applied to loaded
kilometres when the source describes something else — and is the empty return leg handled
consistently with what the source covers? Are the tonne weights the same ones r8 uses, and
are they right? Is the chosen measure actually a grower-facing cost, or has it silently
become a distance-to-independent-point statistic wearing a dollar sign? Does state D
(pre-2019) use a roster the repo can support, given roster_audit_2026-08.md records
Tooligie, Cowell, Mangalo and Murdinga as missing and Cungena as contradicted? Does
anything touch a fitted parameter? Is the inflation treatment stated and defensible?`,
    { label: 'verify:method', phase: 'Verify', model: 'opus', effort: 'xhigh', schema: VERDICT }),

  () => agent(`${CONTEXT}

TASK: You are Arowana's or T-Ports' adviser, reading our test of their $15/t claim before
it is published. Find everything unfair or wrong in it. Default to refuted=true if uncertain.

${JSON.stringify(claim, null, 2)}

Attack: has the most favourable fair reading actually been tested, or a convenient one? Is
"up to" being treated as an average, which would be a straightforward misreading? Is the
2021 claim being tested against a 2025/26 network — when the bunkers were open in 2021 and
are closed now — and if so is that disclosed as a difference in the world rather than an
error by the claimant? Is a 2019 freight schedule being applied to a 2021 claim without
saying so? Would a reader come away with a false impression even if every sentence is true?

Then answer the question that decides publication: is our test fair enough to print beside
a named company's claim?`,
    { label: 'verify:fairness', phase: 'Verify', model: 'opus', effort: 'xhigh', schema: VERDICT }),
])

const live = verdicts.filter(Boolean)
const refuted = live.filter((v) => v.refuted).length
log(`Verify: ${refuted} of ${live.length} refuted.`)

// ---------------------------------------------------------------- Report
phase('Report')
const report = await agent(`${CONTEXT}

TASK: Write docs/r9_cartage_findings.md.

Rate: ${JSON.stringify(rate, null, 2)}
Build: ${JSON.stringify(build, null, 2)}
Claim test: ${JSON.stringify(claim, null, 2)}
Adversarial verdicts: ${JSON.stringify(live, null, 2)}

Sections:
1. PUBLISHABLE / NOT in the first line, separately for (a) the cartage figures and (b) the
   claim test — they can differ, and the cartage work may stand while the claim test does not.
2. The headline table: $/t by district across the four states, with the reproduce command
   and every dependency named.
3. What a grower in each district can take from this, in one sentence each. Plain language,
   no jargon — this is the part intended to be usable.
4. The claim test: verdict, the reading tested, and whether it is fair to print.
5. What this does NOT show — lead with the absence of price data, which is half the
   decision and which we do not have.
6. Outstanding defects the verifiers raised that are not fixed.

If a verifier refuted, that section is NOT publishable and the first line says so. Be blunt
and short.`,
  { label: 'report:cartage', model: 'opus', effort: 'high' })

return {
  rateFound: rate ? rate.found : null,
  buildStatus: build ? build.status : null,
  claimVerdict: claim ? claim.verdict : null,
  refuted,
  totalChecks: live.length,
  report,
}
