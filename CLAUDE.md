# voice_pubmed_bot

A live, interactive voice tool for Andrew (blind retired cardiologist) to search PubMed and hear results by voice — mic input, spoken output, no screen needed. Runs locally on Steve's Mac (needs a real microphone), unlike CardioClaw's headless server pipeline.

**This is a separate project from `~/CardioClaw/`.** Don't mix work on the two in one conversation — if a session drifts into CardioClaw, say so and suggest picking it up in its own thread.

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
