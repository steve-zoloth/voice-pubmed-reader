# voice_pubmed_bot

A live, interactive voice tool for Andrew (blind retired cardiologist) to search PubMed and hear results by voice — mic input, spoken output, no screen needed. Runs locally on Steve's Mac (needs a real microphone), unlike CardioClaw's headless server pipeline.

**This is a separate project from `~/CardioClaw/`.** Don't mix work on the two in one conversation — if a session drifts into CardioClaw, say so and suggest picking it up in its own thread.

## Starting a session for this project
1. Open the sidebar (left panel listing your chats/sessions).
2. Either click an existing session already scoped to this project, **or** start a new chat.
3. If starting new: set the working directory to `~/Documents/voice_pubmed_bot` before/when the session begins (in a terminal: `cd ~/Documents/voice_pubmed_bot` before launching; in a GUI client, use its folder picker for a new chat) — this is what makes this file load automatically.
4. Confirm it loaded — the session should already know about the mic/STT issues, the Muse plan, etc. without you re-explaining.
5. Rename the session (sidebar ⋮ menu, or ask Claude to do it) to something clear, e.g. "voice_pubmed_bot — <what you're doing>", so it's findable later.
6. For the Muse upgrade specifically: work on the `muse-upgrade` branch (already created, pushed to GitHub) — `git checkout muse-upgrade` — so `main` stays untouched until it's verified.

## Architecture
- Single file, `voice_pubmed_bot.py`. Procedural, synchronous: prompt → listen → parse → act, looped.
- Search/fetch layer: `Bio.Entrez` against the real PubMed API (esearch/esummary/efetch) — reliable, fixed from an earlier BeautifulSoup-scraping version.
- Full text: `get_pmc_id()`/`fetch_full_text()` pull from PMC when available (same PMC-only caveat as CardioClaw — most paywalled journals won't have it; "open access on the publisher's site" ≠ "in PMC").
- Voice I/O: `speech_recognition` (PyAudio capture + Google's free, unofficial STT) for input, `pyttsx3` (local macOS voices) for output.
- References get appended to `references.txt` in this folder.

## Known issues, don't rediscover these
- **`listen_for_query()` has no timeout** (unlike `listen_for_speech()`'s 5s default) — can hang indefinitely if nothing is heard.
- **STT reliability**: `recognize_google()` is Google's free, unsupported endpoint — no SLA, can degrade silently, no offline fallback, requires live internet per phrase.
- **Device-selection prompts always listen on the system default mic**, regardless of which device ends up selected — inconsistent, worth fixing alongside the STT swap.
- **No accessible launch mechanism for Andrew** — someone sighted has to start this from a terminal every time. Bigger practical gap than the STT engine itself; worth solving before or alongside further STT work.
- **macOS mic permission is per-app (TCC), not system-wide** — if input silently stops working after changing how the script is launched (different terminal, double-click, packaged app), check System Settings → Privacy & Security → Microphone before assuming it's a code bug.

## Planned: Muse Voice Transcribe upgrade
Meta Superintelligence Labs' streaming ASR model (launched Sept 1, 2026) — SOTA accuracy, native endpointing, real developer API (Meta Model API, pay-as-you-go, ~$0.18/hour). Directly addresses the STT reliability and no-timeout issues above by replacing `recognize_google()`. Not yet built — see git log/session history for status when picking this up.

## Repo
Pushed to GitHub — check `git remote -v` for the URL if unsure it's still connected.
