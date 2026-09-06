export const meta = {
  name: 'ep-headline-cleanup',
  description: 'Clear the six blocking provenance defects, sweep A11 coordinates, and narrow the headline to the A11-independent 2025/26 level',
  whenToUse: 'Final pass before drafting the "One gateway" piece. Third and last defect-clearing round.',
  phases: [
    { title: 'Fix', detail: 'six blocking defects + A11 sweep + headline narrowing', model: 'opus' },
    { title: 'Verify', detail: 'adversarial re-check of every corrected claim', model: 'opus' },
    { title: 'Brief', detail: 'final go/no-go and the claim allowlist', model: 'opus' },
  ],
}

const CONTEXT = `
Repo: the Windrow EP grain supply-chain simulation (cwd is the repo root).
Read first: docs/ready_to_draft.md (the NOT-READY brief this run must clear),
docs/gate_findings.md, docs/roster_audit_2026-08.md, docs/r0_choice_geometry.md,
data/ASSUMPTIONS.md A2/A4/A11/A12/A18/A24, and data/SOURCES.md.

State of play: the dynamic (Tier 3) layer failed its validation gate and is out. The piece
rests on Tier 1 published facts plus ONE Tier 2 number from
pipeline/r8_choice_geometry.py, which uses no fitted parameter. Two adversarial rounds have
confirmed the number itself and refuted the way it is presented and sourced. This is the
last defect-clearing round.

ALREADY FIXED BY THE LEAD - do not redo, do not revert, do build on:
- data/ASSUMPTIONS.md A11 has been rewritten: the <=5 km coordinate error is NOT negligible
  for the ownership geometry, it moves 2023/24 20.3% -> 24.6% and the multiple 3.3x ->
  2.71x, it is asymmetric, and the 2025/26 level does not depend on it.
- docs/roster_audit_2026-08.md now carries a correction: invariance under adding an
  incumbent site holds for the THRESHOLD rows only, never the GAP rows.

Ground rules:
- Do NOT git commit or push.
- Never state a number without the command that reproduces it.
- If a claim cannot be sourced, delete it. A weaker or adjacent citation standing in for
  the one that was needed is the worst possible outcome.
`

const FIX = {
  type: 'object',
  additionalProperties: false,
  required: ['status', 'command', 'headline2025', 'defectsCleared', 'a11Sweep', 'headlineNarrowing', 'stillOpen'],
  properties: {
    status: { type: 'string', enum: ['done', 'partial', 'blocked'] },
    command: { type: 'string' },
    headline2025: { type: 'string', description: 'the 2025/26 no-independent-within-90-min figure after all changes; must still be 66.8%' },
    defectsCleared: { type: 'array', items: { type: 'string' }, description: 'one line per blocking defect, saying what was changed where' },
    a11Sweep: { type: 'string', description: 'the published A11 coordinate sweep as a markdown table' },
    headlineNarrowing: { type: 'string', description: 'what is now the headline, what was demoted, and where the demoted material lives' },
    stillOpen: { type: 'array', items: { type: 'string' } },
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

phase('Fix')
const fix = await agent(`${CONTEXT}

TASK: clear every blocking defect in docs/ready_to_draft.md section 1, run the A11 sweep,
and narrow the headline. You own all of: pipeline/r8_choice_geometry.py,
docs/r0_choice_geometry.md, docs/r0_choice_geometry.json, data/SOURCES.md and the notes in
pipeline/manual_sites.json. No other agent is running.

THE SIX BLOCKING DEFECTS

1. data/SOURCES.md says Cungena appears in "1 of 128" archived weekly reports. The corpus
   is 148 (data/processed/receivals_notes.jsonl: 148 records, 148 unique source_file;
   docs/r5_validation.md:121 already says 148). Fix it, and grep the repo for any other
   stale corpus count.

2. The "cannot move when an incumbent site is added or removed" paragraph appears three
   times in docs/r0_choice_geometry.md and as ladder_b_invariance in the JSON. It is true
   of the threshold rows and FALSE of the gap rows — the gap is measured from the
   incumbent, and this repo's own roster fix moved it 74.4% -> 77.3%. Restate it precisely
   everywhere it appears.

3. docs/r0_choice_geometry.json coverage.road_snap.note still ends at "It cannot manufacture
   an ownership gap..." with no threshold-row caveat. The .md was fixed and the .json was
   not. Make them agree — and check for any other .md/.json divergence while you are there.

4. A18's 0.07-0.13 A$/t-km is described as a "published range". A18 itself says "No single
   public EP $/t-km schedule exists." Worse, this is currently the SOLE surviving support
   for the 90-minute threshold. Correct the description, then either find a genuinely
   published basis for 90 minutes or stop designating it a priori and present the sweep
   without a privileged threshold. Do not manufacture a justification.

5. The page claims independence from "A1, A2, A9 or A24" while its second ground for the
   threshold rests on A2's 12-hour receival window. Either drop that ground or drop A2
   from the independence claim. The independence claim is load-bearing for the piece's
   whole tier structure, so it must be exactly true.

6. The Wharminda removal note gives as its reason "no outlet, date or URL anywhere in this
   repo", which is no longer true in its own tree. The deletion stays; reword the reason.

THE A11 SWEEP

A11 (now rewritten — read it) says Lock and Kimba are town centroids with <=5 km error.
They are the only independent inland receival points EP has ever had, so in the 2023/24
state they alone set the nearest-independent distance for much of the peninsula. Sweep
their coordinates over the tolerance — at minimum 0, 2.5 and 5 km, in the directions that
most and least favour the result — and publish the resulting range as a standing table.
The sweep must be reproducible from the script, not hand-computed.

THE HEADLINE NARROWING

The 2025/26 level is A11-independent (both bunkers are closed in that state), roster-
independent, and has survived three adversarial rounds unchanged. Make it the headline:

  "share of EP grain production with no independent receival point within 90 minutes'
   drive, 2025/26: 66.8%"

Demote the 2023/24 -> 2025/26 trajectory and the 3.3x multiple to a supporting section
where every figure carries the A11 range. Do not delete them — they are real, they are
just not load-bearing any more.

INVARIANT: the 2025/26 figure at 90 min and x1.00 speeds must still be 66.8% when you are
done. If it moves you have changed the method by accident — report that rather than
publishing a new number.

ALSO, for the record: docs/ready_to_draft.md notes that five of the six closed_2019
entries in pipeline/manual_sites.json cite the Farm Online syndicated copy alone, that
only Minnipa's note mentions rail, and that Waddikee's "rail-served until May 2019" is
contradicted by the same source that closes it. Correct those notes to match what the
sources actually support.`,
  { label: 'fix:cleanup', model: 'opus', effort: 'high', schema: FIX })

log(`Fix: ${fix ? fix.status : 'FAILED'} | 2025/26 headline: ${fix ? fix.headline2025 : '?'}`)

phase('Verify')
const verdicts = await parallel([
  () => agent(`${CONTEXT}

TASK: Try to REFUTE the cleanup. Default to refuted=true if uncertain.

${JSON.stringify(fix, null, 2)}

Run the reproduce command yourself. Then check, one at a time, that each of the six
blocking defects is ACTUALLY cleared in the file it lived in — not merely described as
cleared. Re-grep for the stale corpus count. Re-read every occurrence of the invariance
claim. Diff the .md against the .json for any remaining divergence.

Then attack the new work: is the A11 sweep computed by the script or hand-written into the
doc? Does it actually move the sites, or just scale a number? Is the headline still 66.8%?
Is the demoted trajectory carrying the A11 range everywhere it appears, including the JSON?
Is the independence claim now exactly true — check it against A1, A2, A4, A9, A11, A18,
A24 one by one? And did clearing defect 4 result in a genuinely sourced justification for
90 minutes, or a rationalisation?`,
    { label: 'verify:cleanup', phase: 'Verify', model: 'opus', effort: 'xhigh', schema: VERDICT }),

  () => agent(`${CONTEXT}

TASK: Fresh-eyes read of docs/r0_choice_geometry.md as a hostile subject-matter reader —
someone at Bunge or the ACCC seeing it for the first time, who has NOT followed this
project's history. Default to refuted=true if uncertain.

Ignore what the workflow says was fixed. Read the document as published and ask: does every
number carry a reproduce command and a source? Is any claim stated more strongly than its
evidence? Is any assumption relied on without being named? Does the tier structure hold —
is anything presented as unfitted geometry that actually touches a fitted parameter? Is
there a reading of this document under which its headline is misleading even though every
individual sentence is true?

Report what a hostile reader would attack first, and whether the document survives it.`,
    { label: 'verify:hostile-reader', phase: 'Verify', model: 'opus', effort: 'xhigh', schema: VERDICT }),
])

const live = verdicts.filter(Boolean)
const refuted = live.filter((v) => v.refuted).length
log(`Verify: ${refuted} of ${live.length} refuted.`)

phase('Brief')
const brief = await agent(`${CONTEXT}

TASK: Rewrite docs/ready_to_draft.md in place with the current state.

Cleanup result:
${JSON.stringify(fix, null, 2)}

Adversarial verdicts:
${JSON.stringify(live, null, 2)}

Sections:
1. READY / NOT READY in the first line. NOT READY if either verifier refuted, or if the
   2025/26 headline moved off 66.8%.
2. THE ALLOWLIST — the exact claims the piece may make. Each with: tier, number, reproduce
   command, source, and the assumptions it depends on. Nothing outside this list goes in
   the draft. This is the section I will write from, so it must be complete and literal.
3. What was cut across all three rounds, and why. A reader of the draft should never be
   able to ask "why isn't X in here" without this section answering it.
4. The opening: the verified hook sentence, or a statement that the piece opens on the
   2025/26 level instead.
5. Outstanding defects a hostile reader could still raise, each with its one-line answer.
   Be honest about the ones that have no good answer.

Blunt and short. If it is not ready, the first line says so and section 5 says what would
make it ready.`,
  { label: 'brief:final', model: 'opus', effort: 'high' })

return {
  status: fix ? fix.status : null,
  headline2025: fix ? fix.headline2025 : null,
  refuted,
  totalChecks: live.length,
  stillOpen: fix ? fix.stillOpen : null,
  brief,
}
