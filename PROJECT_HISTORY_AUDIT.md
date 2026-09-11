# Voice PubMed project history audit

Current GitHub name: **steve-zoloth/voice-pubmed-reader**, default branch
**realtime-reader**. Renamed September 11 from voice_pubmed_bot / muse-upgrade;
older names below are historical. The local checkout remains
~/Documents/voice_pubmed_bot. The rename preserves checkpoint da6237f and all
application code; see CURRENT_BASELINE.md.

Audited September 11, 2026 at Steve's request after a mistaken GPT-Live test
reopened issues already solved in the working version.

## Coverage

Read the complete available paginated text histories of all seven project tasks
exposed by the app: **302 returned turns across 34 pages**. The project contained
four ChatGPT conversations and three Codex tasks. A user message in Return to
Voice PubMed explicitly confirms the four conversation names. Also reviewed
Credit Payments Chat and Project Priority Planning for billing and UI decisions,
and the current task's failed comparison and corrective instructions.

| Exact task title | Available turns | Task ID |
| --- | ---: | --- |
| Voice PubMed Reader-Recovery & Realtikme Fix | 123 | 6a91ae26-b398-83ea-ab4a-e7a5e6d057bd |
| Return to Voice PubMed | 32 | 69264cf0-9eb4-8329-8977-9301043e752a |
| Improve Realtime voice experience | 19 | 01a09162-2df3-7ca1-86c6-5a7d07a87c7a |
| Assess Realtime Voice Prototype | 14 | 01a08c9d-63c3-7110-a1d9-9b1cb6f99ed2 |
| Fix Voice PubMed speech output | 11 | 01a082d0-257e-7283-bf97-247cd20b7c24 |
| Add reader current endpoint | 99 | 69a87b7d-e034-832c-b9c0-d1d89c936cfc |
| Save server.py correctly | 4 | 6a9226f4-52a0-83e9-ba75-7e855b9de23a |

Every available older-page cursor was followed to completion. This is a text
history audit, not a claim to have inspected unavailable screenshots, attachment
contents, deleted tasks or unexposed Claude history. No archived Codex tasks were
returned. Raw chat exports and credentials are not included in this repository.

## Version map: the source of repeated confusion

| Location | Repository / role | Baseline decision |
| --- | --- | --- |
| ~/Documents/voice_pubmed_bot | steve-zoloth/voice-pubmed-reader; current Realtime and Muse/Nova readers | Latest user-confirmed voice baseline. |
| ~/Desktop/VoiceBot_New-main | steve-zoloth/VoicePubMedReader; Researcher Pro, library/citation/bibliography features | Separate older feature-rich implementation; preserve and identify explicitly. |
| ~/VoicePubMedWeb | March Flask app and Apple Shortcuts reader endpoints | Older implementation, not the Sept 10 tested Realtime voice reader. |
| ~/CardioClaw | Automated cardiology podcast and separate voice companion | Separate project, not Voice PubMed. |

Local source inspection agrees with this distinction. Researcher Pro includes
manage_list, surf_citations, get_full_text and export_bibliography. The current
Realtime reader has a different scoped tool adapter and no broader bibliography
system. Shared historical names must not be treated as shared code or state.

## Chronology and source evidence

### March: Flask reader and Shortcuts

Add reader current endpoint records working current/next/previous/repeat routes
and Steve confirming he heard abstracts. Later voice-search Shortcuts used stale
or literal FinalQuery values, creating mismatches between displayed and spoken
results. This history is not evidence that Sept 10 Realtime needed a new Flask
implementation. Recovering old endpoint work is different from selecting the
current voice baseline.

### August: Researcher Pro recovery

Voice PubMed Reader-Recovery & Realtikme Fix distinguishes the small March Flask
app from Desktop/VoiceBot_New-main. It records microphone/AEC and outdated beta
Realtime configuration work. Save server.py correctly records a supplied fix for
actual PMC body retrieval and fallback to abstract/DOI, but an assistant's claim
of a supplied ZIP is not itself proof that the file was installed. The local
Researcher Pro source is retained, not merged into the new reader by assumption.

### September 8: speech output and fallback controls

Fix Voice PubMed speech output establishes that speech calls already existed.
An initial suspected speech-engine fault was followed by a concrete observation:
the system default voice produced almost empty audio. Samantha was a diagnostic
workaround, and Steve rejected its voice. Nova was then implemented with separate
local playback controls. Steve explicitly reported: “it runs and speaks well”.

Muse capture and speaker interruption handling were subsequently improved;
more-results pagination was added. Return to Voice PubMed records successful
MacBook Air microphone selection and recognition of sarcopenia/elderly-male
queries. These were not open requirements to rediscover in September 11.

### September 10: successful Realtime and enhancements

Assess Realtime Voice Prototype is the decisive implementation/testing source.
At 1789067360 (Unix seconds), Steve said “wow that works really well, allows
interrupts”. Later he said the new AI reader was much better than Muse and asked
to retain both versions. The assistant added reduced chatter, omission of author
preambles, section navigation and approximate time skipping. Steve then requested
actual result counts and identification/filtering of review articles; those
were implemented in the existing Realtime adapter.

The same task explicitly corrects model identity: the tested implementation was
GPT-Realtime-2.1, NOT GPT-Live-1. GPT-Live was an optional subsequent comparison.
Return to Voice PubMed repeats this correction and instructs continued refinement
of the working version rather than restarting feasibility.

### September 11: targeted refinements and billing

Improve Realtime voice experience audited the existing code, added article
position announcements, preserved the passage for repeat after informational
commands, blocked superseded queued navigation and updated the README to identify
Realtime as primary. At that time the task reported 40 offline tests. A later
billing classification test is present in the checkout; the current complete
five-module run passes 41 tests.

Live retesting then failed with HTTP 429 / exhausted API balance. Credit Payments
Chat records the separate ChatGPT-credit purchase and Steve's subsequent $10 API
funding with auto-recharge. Billing is resolved by user report; do not keep
repeating its old diagnosis in the absence of a fresh error.

### September 11: failed comparison in the current task

The current task found the correct notes but nevertheless built an optional
GPT-Live adapter against the old ~/VoicePubMedWeb. It started a browser-default
microphone test without clearly preparing Steve; the iPhone microphone appeared.
An API connection and displayed title were mistakenly treated as stronger
progress than they established. Steve reported the reader did NOT report the
results aloud and directed a full history audit.

This was a continuity and validation failure. The proven current repository was
not modified by that experiment. Its session/server were stopped. The experimental
entry point in the old app is removed and its new files parked separately; none
are part of the canonical Realtime GitHub checkpoint. Do not infer that the
working Realtime microphone or speech stack is broken from that experiment.

## What to do next

Use CURRENT_BASELINE.md and AGENTS.md as the starting instructions. Continue
from the existing Realtime launcher and code after this GitHub checkpoint. Do
not launch another microphone test unless Steve initiates or explicitly requests
it. The next live test should exercise the established reader after billing
recovery, with its normal microphone/output setup, and record audible results.
Andrew's independent-use acceptance remains outstanding. Only then consider a
scoped GPT-Live comparison on the same backend, if still requested.
