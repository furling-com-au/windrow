export const meta = {
  name: 'ep-prepublication',
  description: 'Pre-publication review of the EP competition piece: fact-check every claim, steelman the incumbent, defamation-care pass, right-of-reply pack',
  whenToUse: 'After a full draft of the piece exists. This does NOT write the piece — prose and voice stay in the main session.',
  phases: [
    { title: 'Extract', detail: 'pull every checkable factual claim out of the draft', model: 'sonnet' },
    { title: 'Check', detail: 'fact-check claim groups against their sources', model: 'opus' },
    { title: 'Adversary', detail: 'steelman the incumbent, defamation-care pass, completeness critic', model: 'opus' },
    { title: 'Report', detail: 'blocking issues and the right-of-reply pack', model: 'opus' },
  ],
}

const DRAFT = (typeof args === 'string' && args) || 'docs/piece_one_gateway.html'

const CONTEXT = `
Repo: the Windrow EP grain supply-chain simulation (cwd is the repo root).
The draft under review is ${DRAFT}.
Supporting material: docs/analysis_plan_ep_competition.md (esp. section 3 "claims ladder"
and section 6 "What we must not claim"), docs/gate_findings.md, docs/r0_choice_geometry.md,
docs/r5_validation.md, docs/r1_r4_findings.md, data/SOURCES.md, data/ASSUMPTIONS.md.

This piece names a real, large company (Bunge, formerly Viterra) in a competition context
and will be read by that company's lawyers, by Grain Producers SA, and possibly by the
ACCC. Hold it to that standard.

*** HIGHEST-RISK CLASS — CHECK THESE FIRST AND HARDEST ***
Every date and event in the draft's "Why it matters this year" timeline entered this
project through WEB-SEARCH RESULT SUMMARIES, not primary sources, and NONE has been
verified against an original document. Nothing in this repo backs any of them. They are:
  - the ACCC's 2021 Bulk Wheat Code determinations: Port Adelaide exempted, Port Lincoln
    and Thevenard REFUSED (check the actual determinations on accc.gov.au)
  - the Viterra/Grainflow acquisition: five sites plus a mobile ship loader, ACCC review
    opened 10 October 2024, withdrawn 16 December 2024 (check the ACCC public register)
  - Bunge completing the Viterra acquisition and the renaming of Viterra Operations Pty
    Ltd to Bunge Operations Pty Ltd, notified August 2025
  - the T-Ports sale: ~A$250m, Nash Advisory, packaged with Australian Grain Export, and
    the tipped-buyer list that INCLUDES BUNGE - this one is defamation-sensitive, because
    naming a company as a bidder it may never have been is a factual assertion about it
  - the Wheat Port Code being sunsetted on ACCC advice in 2024 and a revised exposure
    draft going to consultation, with grower groups split
  - who opposed the Grainflow deal (T-Ports, Grain Producers SA, EP growers) and any
    quoted words attributed to them
  - the 2019 closures being attributed to freight redirection by the published reporting
A search-engine summary has ALREADY produced one false claim in this project (that T-Ports
was hiring for its Lock and Kimba sites in 2025/26, contradicted by the operator's own
harvest page). Treat every one of the above as unverified until you have read the primary
document yourself. If a primary source cannot be reached, say so and mark the claim
unverified rather than accepting the secondary report.

Do NOT edit the draft. Report findings; the author fixes them.
`

const CLAIMS = {
  type: 'object',
  additionalProperties: false,
  required: ['claims'],
  properties: {
    claims: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['id', 'text', 'tier', 'citedSource'],
        properties: {
          id: { type: 'string' },
          text: { type: 'string' },
          tier: { type: 'string', enum: ['1-published', '2-geometry', '3-dynamic', 'uncategorised'] },
          citedSource: { type: 'string', description: 'the source or model run the draft cites, or "NONE"' },
        },
      },
    },
  },
}

const FINDINGS = {
  type: 'object',
  additionalProperties: false,
  required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['severity', 'claimId', 'problem', 'fix'],
        properties: {
          severity: { type: 'string', enum: ['blocking', 'serious', 'minor'] },
          claimId: { type: 'string' },
          problem: { type: 'string' },
          fix: { type: 'string' },
        },
      },
    },
  },
}

phase('Extract')
const extracted = await agent(`${CONTEXT}

TASK: Read the draft and extract EVERY checkable factual claim as a numbered list.

A checkable claim is any statement a reader could verify or dispute: a number, a date, a
company action, a regulatory event, a model output, a characterisation of what someone
said. Tag each with the claims-ladder tier it belongs to and the source the draft cites
for it (or NONE).

Be exhaustive. A claim you skip is a claim nobody checks.`,
  { label: 'extract:claims', model: 'sonnet', effort: 'medium', schema: CLAIMS })

const claims = (extracted && extracted.claims) || []
log(`${claims.length} checkable claims extracted.`)

// Chunk into at most 5 groups so one agent owns a coherent slice.
const GROUPS = 5
const groups = []
for (let i = 0; i < GROUPS; i++) groups.push(claims.filter((_, j) => j % GROUPS === i))

const checkResults = await parallel(
  groups.filter((g) => g.length).map((g, i) => () =>
    agent(`${CONTEXT}

TASK: Fact-check this group of claims from the draft. Verify each against its cited source
— read the repo file, re-run the model command, or fetch the published source on the web.

${JSON.stringify(g, null, 2)}

For each claim report: does the source say what the draft says it says? Is the number
right? Is a Tier 3 number stated as a point estimate where A24 requires a range? Is a claim
tagged Tier 1 or 2 actually resting on a fitted parameter (which would be a fatal
misclassification)? Is a source cited at all?

Severity: 'blocking' = would have to be corrected before publication; 'serious' = weakens
the piece or invites a credible challenge; 'minor' = tidy-up.`,
      { label: `check:group-${i + 1}`, phase: 'Check', model: 'opus', effort: 'high', schema: FINDINGS })),
)

const adversary = await parallel([
  () => agent(`${CONTEXT}

TASK: You are the incumbent's expert witness. You have been retained by Bunge to discredit
this piece. Write the strongest good-faith rebuttal you can, then report it as findings.

Go after: the choice-geometry methodology (is drive time the right measure of competitive
constraint at all, when growers also have on-farm storage, forward contracts, and
non-network buyers?); the assumption stack (A1 payload, A2 service time, A4 capacities,
A24 identification); the attribution of the 2019 closures given the simultaneous rail
closure; whether a public-data model can say anything about a business whose real
capacities and cycle times are confidential; and the piece's standing to comment at all.

For each line of attack, say whether the draft already defends against it. The ones it
does not defend against are the findings.`,
    { label: 'adversary:incumbent', phase: 'Adversary', model: 'opus', effort: 'xhigh', schema: FINDINGS }),

  () => agent(`${CONTEXT}

TASK: Defamation and fairness pass. This is not legal advice; it is the standard editorial
check before naming a company.

Flag every place where the draft: imputes motive or strategy to a company rather than
describing an effect; states as fact something that is inference; uses loaded language
where neutral language would carry the same information; juxtaposes two facts so as to
imply a causal or intentional link that is not established (especially the Lock/Kimba
bunker closures and the 2019 site closures — commercial and drought explanations are
entirely plausible and the draft must say so); or characterises a third party's position
without quoting a published statement.

Also check that every company named gets a fair statement of its position and that the
right-of-reply offer is described in the piece.`,
    { label: 'adversary:fairness', phase: 'Adversary', model: 'opus', effort: 'xhigh', schema: FINDINGS }),

  () => agent(`${CONTEXT}

TASK: Completeness critic. What is MISSING?

Ask: which published source that bears on this was not consulted? Which stakeholder's
position is absent? Which obvious reader question does the piece fail to answer? Which
model run would a sceptical reader immediately ask for that we did not do? Is there a
counter-story the evidence supports that the draft ignores — e.g. that competition on EP
has actually improved since T-Ports arrived, or that the 2019 rationalisation was
efficiency rather than market power?

Report each gap as a finding with a concrete fix.`,
    { label: 'adversary:completeness', phase: 'Adversary', model: 'opus', effort: 'high', schema: FINDINGS }),
])

const all = [...checkResults, ...adversary].filter(Boolean).flatMap((r) => r.findings || [])
const blocking = all.filter((f) => f.severity === 'blocking')
log(`${all.length} findings; ${blocking.length} blocking.`)

phase('Report')
const report = await agent(`${CONTEXT}

TASK: Write docs/prepublication_review.md.

Findings:
${JSON.stringify(all, null, 2)}

Sections:
1. PUBLISH / HOLD verdict in the first line. HOLD if there is any blocking finding.
2. Blocking issues, each with the exact fix.
3. Serious issues, ranked.
4. Minor issues, as a checklist.
5. The right-of-reply pack: for each of Bunge (media), T-Ports (CEO Nathan Kent) and Nash
   Advisory, Grain Producers SA, DIT / RDA Eyre Peninsula, and the ACCC mergers team —
   the specific claims in the piece that concern them, drafted as neutral questions with a
   five-working-day deadline. These letters are the customer-discovery round as well as
   the fairness round, so they must read as a serious analyst's enquiry, not a gotcha.

Deduplicate findings that three agents each raised. Do not pad.`,
  { label: 'report:prepublication', model: 'opus', effort: 'high' })

return { claimsChecked: claims.length, findings: all.length, blocking: blocking.length, report }
