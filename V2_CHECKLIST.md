# VPR V2 — proposed checklist, pending Andrew’s feedback

Status: planning only. Do not begin implementation from this checklist. Steve
asked to hold all recommendations until Andrew responds. Created September 18,
2026. This supersedes prioritization in earlier discussions, not working code.

## Direction and scope

The goal is independent, dependable access to medical evidence for a blind
physician. Success means Andrew can find, hear, verify, save and return to
information without sighted assistance. Feature parity with OpenEvidence is
not the acceptance criterion. Keep direct source reading and optional generated
clinical answers as distinct modes. Keep CardioClaw entirely separate.

Preserve GPT-Realtime-2.1/Marin, working duplex interruptions, existing PubMed
backend, cloud website launch, private access, source-faithful abstracts and
PMC full text. No voice-engine replacement or GPT-Live experiment in V2 scope.
Muse remains the local fallback. Preserve older library/export code as reference.

Already implemented: search, pagination, counts/position, reviews filter,
next/previous, stop/repeat/continue, labeled sections, authors/journal/PMID/citation
on request, abstract/full-text caching, concise instructions, and unavailable
full text announcing failure without automatically replaying the abstract.
Do not rebuild these as new features. Exact audio seeking/resume and continuous
long-form reading are not implemented.

## Gate 0 — Andrew’s independent test and selection

- [ ] Andrew opens the website, signs in using saved code, starts microphone,
      searches and ends session without Terminal or a helper.
- [ ] Test his actual Mac/iPhone/iPad, VoiceOver and normal audio device.
- [ ] Test interruptions, pauses/corrections, stop, repeat, next/previous,
      no advancing on silence, metadata requests, full-text availability,
      sections and returning after failure.
- [ ] Record exact failures, device, expected result and article identifiers.
      Distinguish recognition errors, slow retrieval and slow turn completion.
- [ ] Confirm the session-expiry/login process is usable independently.
- [ ] Ask Andrew to select his three highest-value improvements.
- [ ] Confirm desired spending controls separately: monthly auto-recharge cap
      is not an exact API usage cap; current app has no dollar cap. Verify actual
      account settings before claiming protection. Do not change billing silently.

## V2A — dependable independent use (recommended first release)

- [ ] Fix reproduced Andrew blockers before adding features.
- [ ] Add “Where am I?” with title, article position and section.
- [ ] Add reversible navigation/history (“go back”), without losing searches.
- [ ] Restore search and passage after disconnection; define private storage,
      retention and per-user separation before persisting research history.
- [ ] Improve accessible sign-in, errors, focus, controls and listening status.
- [ ] Document WCAG-based manual and automated review; test with VoiceOver.
      Do not call this certification or equate passing code tests with usability.
- [ ] Keep stop responsive during retrieval; prevent late results from speaking
      or changing navigation unexpectedly after newer commands.
- [ ] Offer optional quiet progress feedback for retrieval, not repetitive speech.
- [ ] Measure stop latency, turn-to-response and retrieval time separately;
      set targets from user tests, not the unsupported 1.5-second claim.
- [ ] Evaluate reading speed and brief/detailed response preferences on the
      existing architecture before promising implementation.
- [ ] Add session/concurrency safeguards and usage visibility appropriate to
      private sharing. Assess provider-side termination for enforceable session
      limits; browser timers alone are not a hard billing safeguard.

## V2B — research workflow (select by Andrew’s priorities)

- [ ] Refine an existing search conversationally: population, dates, study type,
      inclusion/exclusion, broaden/narrow, recent versus relevant sorting.
- [ ] Test medical synonyms and PubMed term mapping; expose interpreted searches
      on request rather than claiming a new MeSH engine is automatically needed.
- [ ] Add date/DOI and fuller citation metadata; do not add routine spoken clutter.
- [ ] Add named reading lists, article/passage bookmarks and dictated notes.
- [ ] Add citation exports and restoration of saved sessions.
- [ ] Evaluate older reference implementations for reusable library/export logic.
- [ ] Distinguish no accessible full text from network/parser failure.
- [ ] Find legitimate full text via DOI, publishers and open-access repositories;
      use an open-access locator where appropriate. Do not bypass subscriptions.
- [ ] Assess institutional access separately; depends on Andrew’s library and
      publisher permissions and cannot be promised as a simple API addition.
- [ ] Improve labeled section and reference navigation.
- [ ] Explore accessible table reading with groups, units and uncertainty intact.
      Preserve “read original” and explicitly label any transformed summary.
- [ ] Keep sending/emailing opt-in with explicit recipient and content review.

## V2C — broader sources and optional clinical synthesis

- [ ] Add targeted official guideline search with issuing body, date,
      jurisdiction and version; identify superseded recommendations.
- [ ] Add ClinicalTrials.gov records and results, distinct from publications.
- [ ] Consider FDA safety communications; Cochrane/Embase or other licensed
      sources only where access and integration rights are available.
- [ ] Offer explicitly requested preprints, announcing peer-review status.
- [ ] Deduplicate across sources using DOI/PMID/other identifiers; retain provenance.
- [ ] Add optional concise evidence answers, distinct from article reading.
- [ ] Provide spoken source navigation: “Which study supports that?”, “Read source
      two”, “Read the supporting paragraph”, then return to the answer.
- [ ] Compare selected studies: populations, designs, outcomes, limitations and
      conflicting findings. Do not turn the first five abstracts into “consensus”.
- [ ] Label abstract-only versus full-text-supported claims and missing data.
- [ ] Explain statistics on request without silently removing them from originals.
- [ ] Check retractions/corrections where supported and disclose search coverage.
- [ ] Reassess intended use, clinical validation and applicable requirements before
      offering patient-specific diagnosis/treatment recommendations. FDA status
      depends on function and intended use; physician use alone does not decide it.

## EvidenceMD evaluation — candidate, not selected dependency

- [ ] Compare on a fixed set of approximately 15–20 de-identified research questions:
      answer usefulness, claim-to-source support, citation identity, recency,
      contradictory evidence, missing full text and actual response time.
- [ ] Verify current API schema, source fields, terms, pricing and data handling.
- [ ] Compare against the existing reader plus a simple source-grounded synthesis
      baseline; include manual source checking by a physician.
- [ ] If useful, add only behind an explicit evidence-answer command; preserve
      Realtime voice and original-source navigation. No automatic paid calls.
- [ ] Do not assume this API supplies licensed publisher full text or improves
      voice latency. Published vendor timings are not measurements of our app.

## Deferred unless testing justifies the cost

- [ ] Exact sentence/word resume and exact time seeking: prototype feasibility
      first; may require a different playback design and risk current barge-in.
- [ ] Automatic continuous long reading and locked-screen/background use:
      separate device tests and intentional start/stop behavior required.
- [ ] Broad public release, independent accounts, subscriptions, EHR integration,
      patient records and hospital procurement: separate projects, not this V2.
- [ ] Independent accessibility audit can supplement Andrew’s tests; external
      audit schedules, fees and institutional requirements are not estimated here.

## Review of the Google comparison

Keep optional synthesis, spoken citation navigation and easy saving. Reject
unsupported uniqueness claims, a universal 1.5-second requirement, conflating
voice dictation with full accessibility, silent removal of source statistics,
and replacing the proven engine to follow a competitor architecture. OpenEvidence
is a useful usability benchmark, but licensed content is a separate capability.
Google S2R research is not a ready-made replacement clinical backend.

## Provisional effort, not a promise or an automatic work authorization

Estimates are hands-on development/review/test hours with Codex, not token cost,
unattended runtime or guaranteed elapsed completion. Include focused regression
checks and deployment/rollback work. Feedback and external access can add days.

| Stage | Estimated hands-on work | External dependency |
| --- | --- | --- |
| Andrew feedback triage and scoped plan | 2–4 hours | Andrew’s actual test |
| V2A dependable-use release | 12–24 hours | 2–3 short user test rounds |
| Selected V2B workflow additions | 16–32 hours | Which features Andrew selects |
| EvidenceMD evaluation only | 6–12 hours | API access and physician review |
| Selected V2C integration after evaluation | 20–40 hours | Source APIs, terms and clinical review |

Core V2 (triage + V2A + selected V2B): approximately 30–60 hands-on hours;
roughly 1–3 calendar weeks with timely feedback. Adding EvidenceMD evaluation
and a limited synthesis/broader-source release: about 56–112 hours total,
roughly 3–6 calendar weeks. This does NOT include every optional checklist item,
institutional full-text integration, playback redesign or public-product work.
Exact scope will change these estimates; re-estimate after Andrew’s feedback.

Use Astra for architecture, difficult debugging, evidence/citation behavior,
security boundaries and final review. Sol or another available coding model can
handle bounded UI, export, documentation and test tasks against explicit criteria.
There is no measured project-specific evidence that another model or multiple
agents would shorten these estimates by a particular percentage. User testing,
clinical source review and third-party access do not become faster just because
code generation is faster. Model names alone are not a completion-time guarantee.

Suggested first authorized work session after feedback: 30 minutes to reproduce
and rank issues, then select a narrow V2A release. Do not start all tracks at once.
