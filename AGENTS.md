# Voice PubMed Reader — authoritative project instructions

## Start here every session

Read CURRENT_BASELINE.md before planning, changing code, choosing a model,
launching audio, or proposing a new implementation. Read PROJECT_HISTORY_AUDIT.md
when reconciling an old chat or a similarly named project. These instructions
reflect the September 11, 2026 audit of all seven accessible project tasks and
302 returned turns, plus the billing and planning conversations.

## Identify the correct version

- Authoritative working voice reader: this repository, voice-pubmed-reader.
- Local checkout: /Users/stevezoloth/Documents/voice_pubmed_bot.
- GitHub: https://github.com/steve-zoloth/voice-pubmed-reader.
- Established development branch: realtime-reader; check CURRENT_BASELINE.md and
  current Git state before selecting a different branch.
- Primary launcher: run_realtime_pubmed.command.
- Primary model: gpt-realtime-2.1, browser WebRTC, Marin voice.
- Realtime duplex HAS been implemented and tested. Steve confirmed it worked
  well and was significantly better than Muse. Do not restart feasibility work.
- Muse/Nova remains the retained fallback, launched by run_voice_pubmed_bot.command.
- ~/VoicePubMedWeb is the older March Flask/Shortcuts implementation.
- ~/Desktop/VoiceBot_New-main is a separate, older Researcher Pro implementation,
  backed by https://github.com/steve-zoloth/VoicePubMedReader. It contains broader
  library/citation/bibliography features; do not claim those all exist here.
- Do not choose an implementation from its similar name, old chat title, or
  modification timestamp. Match the launcher, model, file path, and user testing.
- CardioClaw is separate. Do not modify it or introduce runtime dependencies on it.

## Preserve verified progress

Keep working spoken titles/abstracts/PMC full text, result pagination and counts,
article position, review labels/filtering, section navigation, concise replies,
barge-in, repeat behavior and interrupted-request guards. Inspect current code
and the audit before describing a feature as missing or rebuilding it.

GPT-Live is an optional future comparison, not the current baseline. The
September 11 comparison against the older Flask app failed the user's audible
output test and unexpectedly used an iPhone microphone. Connection success and
captions did not establish working audio. Do not promote or relaunch it as the
working reader. A future comparison must reuse this established backend and
preserve this launcher's device/output behavior.

Nova was the user's preferred legacy narration voice. Samantha was a rejected
troubleshooting workaround. Do not return to Samantha/default system TTS or
replace working device routing as an assumed improvement.

Do not activate a microphone or start speaking merely to inspect the app.
Explain the exact audio test and intended device first; after the September 11
surprise, wait for the user to initiate or explicitly request another live test.
Use offline checks for routine validation. Never substitute transcript/API/test
success for the user's report of audible output and usable interaction.

## Completion and continuity

Done means Andrew can independently launch and operate the core PubMed workflow
by voice without sighted assistance. Steve's successful test is evidence of
progress, not Andrew's acceptance. Exact audio seeking, exact word-level resume,
and continuous automatic long-form narration are not implemented in Realtime.

API billing was resolved September 11: Steve added $10 API credit and enabled
auto-recharge. Do not reopen that old issue without a fresh provider error.
Keep secrets in .env. Never commit keys, audio captures, logs, or private chat
exports. Maintain the fallback and preserve existing unrelated changes.

After meaningful work, update CURRENT_BASELINE.md with implementation state,
validation, user-confirmed results, unresolved items, branch and commit evidence.
Commit and push when authorized; distinguish local-only changes from GitHub.
If a new message contradicts an old assumption, reconcile the source instead
of asking Steve to repeat the project history.
