export const meta = {
  name: 'ep-headline-fixes',
  description: 'The four pre-draft fixes to the surviving Tier-2 headline: pin sources, demote Ladder A, publish the threshold sweep, publish the speed sensitivity',
  whenToUse: 'Run after the roster fix and before drafting the "One gateway" piece. Every change is presentation and provenance — the Ladder B headline must NOT move.',
  phases: [
    { title: 'Fix', detail: 'source verification (web) + r8 rework, on disjoint files', model: 'opus' },
    { title: 'Verify', detail: 'adversarial check on the citation and on the regenerated numbers', model: 'opus' },
    { title: 'Ready', detail: 'consolidated go-to-draft note', model: 'opus' },
  ],
}

const CONTEXT = `
Repo: the Windrow EP grain supply-chain simulation (cwd is the repo root).
Read first: docs/gate_findings.md (the NO-GO verdict and the 17 outstanding defects),
docs/roster_audit_2026-08.md (what was just corrected and what is still wrong),
docs/analysis_plan_ep_competition.md sections 3 and 6, and data/ASSUMPTIONS.md A4/A12/A24.

The state of play: the dynamic (Tier 3) layer FAILED its validation gate and is not
publishable. The piece now rests on Tier 1 (published facts) and one Tier 2 number —
"share of EP production with no independent receival point within 90 minutes", 20.3 %
(2023/24) -> 66.8 % (2025/26), computed by pipeline/r8_choice_geometry.py with no fitted
parameter. These four fixes harden that number's presentation before drafting.

Ground rules:
- Do NOT git commit or push. Leave changes in the working tree.
- These are PRESENTATION and PROVENANCE changes. The Ladder B headline must still read
  20.3 % -> 66.8 % at 90 min and default speeds when you are done. If it moves, you have
  changed the method by accident: report that as a defect, do not accept the new number.
- Never state a number without the command that reproduces it.
- If a claim cannot be sourced, the correct answer is "drop the claim" — never a weaker
  or adjacent citation standing in for the one that was needed.
`

const SOURCE_RESULT = {
  type: 'object',
  additionalProperties: false,
  required: ['roadClaim', 'closureClaim', 'cungena', 'sourcesMdUpdated', 'notes'],
  properties: {
    roadClaim: {
      type: 'object',
      additionalProperties: false,
      required: ['verdict', 'citation', 'quote', 'recommendation'],
      properties: {
        verdict: { type: 'string', enum: ['verified', 'partly-verified', 'unverified'] },
        citation: { type: 'string', description: 'publication, headline, date, URL — or NONE' },
        quote: { type: 'string', description: 'the exact sentence naming the roads, or NONE' },
        recommendation: { type: 'string', enum: ['keep-hook', 'reword-hook', 'drop-hook'] },
      },
    },
    closureClaim: {
      type: 'object',
      additionalProperties: false,
      required: ['verdict', 'citation', 'howManySites', 'tiedToRail'],
      properties: {
        verdict: { type: 'string', enum: ['verified', 'partly-verified', 'unverified'] },
        citation: { type: 'string' },
        howManySites: { type: 'string', description: 'how many closures statewide and how many on EP, per the source' },
        tiedToRail: { type: 'string', description: 'does the source itself attribute the closures to freight/rail redirection? quote it' },
      },
    },
    cungena: { type: 'string', description: 'the published list says closed-2019; the operator report has it receiving in 2022/23. State what the sources actually support and how the piece should handle it.' },
    sourcesMdUpdated: { type: 'boolean' },
    notes: { type: 'string' },
  },
}

const R8_RESULT = {
  type: 'object',
  additionalProperties: false,
  required: ['status', 'command', 'headlineUnchanged', 'headline', 'sweep', 'speedSensitivity', 'ladderAHandling', 'caveats'],
  properties: {
    status: { type: 'string', enum: ['done', 'partial', 'blocked'] },
    command: { type: 'string' },
    headlineUnchanged: { type: 'boolean', description: 'does Ladder B still read 20.3% -> 66.8% at 90 min / default speeds?' },
    headline: { type: 'string' },
    sweep: { type: 'string', description: 'the 30-120 min sweep as a markdown table' },
    speedSensitivity: { type: 'string', description: 'headline at x0.85 / x1.00 / x1.15 travel speeds' },
    ladderAHandling: { type: 'string', description: 'exactly what was done with Ladder A and where it now lives' },
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

// ------------------------------------------------------------------ Fix
// Two agents, disjoint files: A owns data/SOURCES.md, B owns pipeline/r8_choice_geometry.py
// and the docs it generates. Neither touches the other's.

const [sources, r8] = await parallel([
  () => agent(`${CONTEXT}

TASK — FIX 1: verify the two published claims the piece's opening rests on, using the web.

(a) THE ROAD CLAIM — the piece's hook. The assertion is that Wharminda Road (and the Tod
    and Lincoln Highways, Balumbah-Kinnaird and Western Approach roads) are named in
    published reporting as roads that absorbed extra truck traffic after the Eyre
    Peninsula rail closure of May 2019. This entered our notes from a search snippet and
    was NEVER verified or recorded. Find the actual source — a Port Lincoln Times piece on
    an EP freight study is the likely candidate — read it, and quote the sentence that
    names the roads. Related figures to check while you are there: ~64,000 60-tonne truck
    movements a year through Port Lincoln; 40-50 truck movements replacing one train;
    ~$25m federal roads funding; the $220m Aurizon/Viterra reopening proposal; the RAA
    survey of 1,300+ EP road users with road maintenance the top concern for 76%.

(b) THE 2019 CLOSURE CLAIM. pipeline/manual_sites.json cites two stories for the
    closed_2019 tags: farmonline "Freight redirection behind Viterra's 17 silo closures"
    and Stock Journal "Northern EP to lose six silos". Read both. Confirm how many
    closures there were statewide and on EP, exactly which sites, and whether the SOURCE
    ITSELF attributes them to freight/rail redirection — that attribution is what lets the
    piece connect the closures to the rail shutdown without imputing motive.

(c) THE CUNGENA CONTRADICTION. manual_sites.json records Cungena as "closed permanently
    2019", yet Bunge's own weekly report for week ending 2022-11-13 lists it among Western
    region sites taking first deliveries of the season. Establish what the published
    sources actually support and recommend how the piece should handle it.

Record every verified source in data/SOURCES.md in the format that file already uses
(dataset/claim, publisher, URL, retrieval date, licence where relevant). You own
data/SOURCES.md — do NOT edit pipeline/r8_choice_geometry.py or anything under docs/,
another agent is working there concurrently.

If the road claim cannot be verified, say so and recommend dropping the hook. An
unverifiable hook is a better loss than a sourced-looking guess.`,
    { label: 'fix:sources', phase: 'Fix', model: 'opus', effort: 'high', schema: SOURCE_RESULT }),

  () => agent(`${CONTEXT}

TASK — FIXES 2, 3 and 4: rework how pipeline/r8_choice_geometry.py PRESENTS its results.
Read that script fully before changing it. You own it and the docs/r0_choice_geometry.*
files it writes; do NOT edit data/SOURCES.md, another agent owns it concurrently.

FIX 2 — Demote Ladder A. The receival-point-count rows ("29 -> 25 -> 23 points", "only one
point within 45 min", "mean drive to nearest point") must come OUT of the headline table.
They have been wrong twice, and docs/roster_audit_2026-08.md section 5 shows the roster is
still incomplete — Tooligie (operating 2022/23-2024/25), Cowell and Mangalo are missing
entirely, and Cungena's closure tag is contradicted. Any count-of-points row is invalid
while that is true. Move them to an appendix under an explicit caveat naming those four
sites, or cut them. State which you did and why.

FIX 3 — Publish the sweep, not its peak. The 3.3x headline ratio is the exact maximum of
the script's own 30-120 minute threshold sweep, which is the first thing an opposing expert
will notice. Publish the FULL sweep as a table. Designate 90 minutes as the a priori
threshold and justify it on grounds that have nothing to do with the result it gives —
cart economics, a working day's round trip, the A18 freight rate, whatever the repo already
supports. If no principled justification exists, say so plainly and present the sweep
without a designated headline threshold.

FIX 4 — Speed sensitivity as a first-class output. Both published rows are minute-
thresholded, so travel-speed error does NOT cancel — the script currently claims it does
and that claim is false. Emit the headline at x0.85, x1.00 and x1.15 travel speeds as a
standing row of the results table, not a footnote.

INVARIANT: after your changes the headline at 90 min and x1.00 speeds must still read
20.3 % -> 66.8 %. These are presentation changes. If that number moves you have altered
the method by accident — report it as a defect rather than publishing the new figure.

Regenerate docs/r0_choice_geometry.md and .json and state the reproduce command.`,
    { label: 'fix:r8-presentation', phase: 'Fix', model: 'opus', effort: 'high', schema: R8_RESULT }),
])

log(`Fix: sources ${sources ? sources.roadClaim.verdict : 'FAILED'} | r8 ${r8 ? r8.status : 'FAILED'} | headline unchanged: ${r8 ? r8.headlineUnchanged : '?'}`)

// ------------------------------------------------------------------ Verify
const verdicts = await parallel([
  () => agent(`${CONTEXT}

TASK: Try to REFUTE the source verification. Default to refuted=true if uncertain.

${JSON.stringify(sources, null, 2)}

Independently fetch the cited URLs yourself. Does each source say what it is claimed to
say? Is the publication, headline and date right? Does the road-claim quote actually name
the roads, or is it an adjacent claim being made to stand in? Is the rail-redirection
attribution the SOURCE's, or has our agent supplied it? Check the numeric claims (64,000
movements, 40-50 per train, $25m, $220m, 76% of 1,300+) against their sources and flag any
that were recorded without one. Finally: read data/SOURCES.md and confirm the entries match
that file's existing conventions and that nothing unsourced was added.`,
    { label: 'verify:sources', phase: 'Verify', model: 'opus', effort: 'xhigh', schema: VERDICT }),

  () => agent(`${CONTEXT}

TASK: Try to REFUTE the r8 presentation rework. Default to refuted=true if uncertain.

${JSON.stringify(r8, null, 2)}

Run the reproduce command yourself. Then attack:
- Does the headline STILL read 20.3 % -> 66.8 % at 90 min / x1.00? If not, the method was
  changed and this is a blocking defect.
- Is the "a priori" 90-minute threshold genuinely justified independently of the answer it
  produces, or is it the sweep's peak wearing a new label? Check whether 90 min is in fact
  the peak of the published sweep — if it is, the justification has to be extremely good or
  the framing is still cherry-picking.
- Is the full 30-120 sweep actually published, including the thresholds least favourable
  to the piece?
- Is the speed sensitivity computed by genuinely rescaling travel times, or approximated?
  Re-derive at least one figure.
- Does any count-of-points row survive anywhere it could be read as a headline?
- Does the output anywhere still assert that speed error cancels?
- Does the result depend on any fitted parameter? It must not.`,
    { label: 'verify:r8', phase: 'Verify', model: 'opus', effort: 'xhigh', schema: VERDICT }),
])

const live = verdicts.filter(Boolean)
const refuted = live.filter((v) => v.refuted).length
log(`Verify: ${refuted} of ${live.length} refuted.`)

// ------------------------------------------------------------------ Ready
const ready = await agent(`${CONTEXT}

TASK: Write docs/ready_to_draft.md — the brief I will write the piece from.

Source verification:
${JSON.stringify(sources, null, 2)}

r8 rework:
${JSON.stringify(r8, null, 2)}

Adversarial verdicts:
${JSON.stringify(live, null, 2)}

Sections:
1. READY / NOT READY in the first line. NOT READY if either verifier refuted, or if the
   headline moved.
2. The exact claims the piece may make, each with its tier, its number, its reproduce
   command, and its source. This is the allowlist — nothing outside it goes in the draft.
3. The claims that were CUT and why (Ladder A, the 3.3x framing, anything unsourced).
4. The hook: keep, reword or drop, with the verified citation if kept.
5. Outstanding defects a reader could still raise, and the one-line answer to each.

Be blunt and short. If the hook did not verify, say the piece opens differently and
suggest how.`,
  { label: 'ready:brief', model: 'opus', effort: 'high' })

return {
  roadClaim: sources ? sources.roadClaim.verdict : null,
  hook: sources ? sources.roadClaim.recommendation : null,
  headlineUnchanged: r8 ? r8.headlineUnchanged : null,
  refuted,
  totalChecks: live.length,
  ready,
}
