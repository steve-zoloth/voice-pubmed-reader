> **Start here:** Read [AGENTS.md](AGENTS.md) and [CURRENT_BASELINE.md](CURRENT_BASELINE.md). The audited working version is **GPT-Realtime-2.1 in this repository**, on `muse-upgrade`. Do not restart from the older VoicePubMedWeb or mistake GPT-Live for the tested baseline. The history and version map are in [PROJECT_HISTORY_AUDIT.md](PROJECT_HISTORY_AUDIT.md).

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

## Current primary path — 2026-09-11

GPT-Realtime-2.1 duplex is implemented, tested and preferred over Muse by Steve.
Launch run_realtime_pubmed.command. Read REALTIME_NOTES.md for the established
baseline and accessibility audit. Do not restart feasibility or replace it with
GPT-Live-1 without an explicit separate comparison request. The Muse/Nova notes
below document the retained fallback and historical work.

## Legacy architecture
- Single file, `voice_pubmed_bot.py`. Procedural, synchronous: prompt → listen → parse → act, looped.
- Search/fetch layer: `Bio.Entrez` against the real PubMed API (esearch/esummary/efetch) — reliable, fixed from an earlier BeautifulSoup-scraping version.
- Full text: `get_pmc_id()`/`fetch_full_text()` pull from PMC when available (same PMC-only caveat as CardioClaw — most paywalled journals won't have it; "open access on the publisher's site" ≠ "in PMC").
- Voice input: **Muse Voice Transcribe** streaming ASR (`muse_stt.py`), with `speech_recognition` (PyAudio + Google's free STT) as an automatic fallback. Output: OpenAI `gpt-4o-mini-tts`, voice `nova`, played locally through AVAudioPlayer (`nova_speech.py`).
- References get appended to `references.txt` in this folder.

## Muse Voice Transcribe upgrade — DONE (on `muse-upgrade`, in test)
Meta Superintelligence Labs' streaming ASR (launched Sept 1, 2026) — native endpointing, `wss://api.meta.ai/v1/asr/realtime`, ~$0.18/audio-hour via a Meta Model API key.
- **`muse_stt.py`** — self-contained client. `transcribe_once(device, initial_timeout, max_seconds)` opens the mic (`sounddevice`, 24 kHz mono s16) + WebSocket, streams in `ENDPOINTING` mode, returns the final transcript when the model detects end-of-turn. Raises `STTError` on any transport/API failure. `available()` reports whether it can run.
- **`voice_pubmed_bot.py`** — `capture()` is the single listen entry point: tries Muse, falls back to Google on `STTError` or when `MODEL_API_KEY` is unset (warns once). `listen_for_speech()` / `listen_for_query()` are thin wrappers over it.
- **Verified**: handshake JSON accepted by the live endpoint (tested with a bad key → clean `STTError`); backend selection + fallback unit-tested. **Not yet verified**: a real transcription — needs Steve's `MODEL_API_KEY` and a voice.
- Config: `MODEL_API_KEY` env var, or a `.env` file next to the script (see `.env.example`).

## Known issues
- ~~`listen_for_query()` has no timeout~~ — **fixed**: `capture()` can't block indefinitely; Muse endpointing ends the listen, `max_seconds` is a hard ceiling, fallback uses `phrase_time_limit`.
- ~~STT reliability (`recognize_google` only)~~ — **fixed**: Muse is primary (real API, SLA), Google is now just the offline-ish fallback.
- ~~Device-selection prompts ignore the selected mic~~ — **fixed**: `SELECTED_DEVICE` (a `sounddevice` index) is set once by `select_microphone()` and passed to every Muse listen. Caveat: the **Google fallback still uses the system default mic** — it can't share `sounddevice` indices.
- **Accessible launch for Andrew** — partly addressed: `run_voice_pubmed_bot.command` is double-clickable from Finder and loads `.env`. Still needs a sighted person for the one-time macOS mic-permission prompt (it attaches to Terminal.app).
- **macOS mic permission is per-app (TCC), not system-wide** — if input silently stops after changing how the script is launched (different terminal, double-click, packaged app), check System Settings → Privacy & Security → Microphone before assuming it's a code bug.

## Repo
Pushed to GitHub — check `git remote -v` for the URL if unsure it's still connected.

## Speech output repair — 2026-09-08
- Inspection of current code and the pre-Muse commit confirms titles, abstracts,
  and PMC full text already called `speak()`. No missing speech call was found.
- The suspected fault is playback through the shared pyttsx3 macOS Cocoa engine,
  not Muse recognition. In the automated environment repeated utterances returned
  almost immediately; native speech also reported audio-service errors, so this
  does not establish the precise cause on a normal Terminal session.
- macOS `speak()` now uses `/usr/bin/say` at 150 words/minute, sends text through
  stdin in chunks of at most 1200 characters, and waits for each chunk. Terminal
  printing remains. Non-macOS keeps pyttsx3. Nonzero playback failures stop the
  session rather than continuing silently.
- Muse client, MODEL_API_KEY loading, launcher, retrieval and commands unchanged.
  This checkout has PMC full-text retrieval, not a separate DOI retrieval path.
- Five offline regression tests pass: `python3 -m unittest -v test_voice_output`.
  The actual launcher also passed a controlled test with transcription, Entrez,
  and physical speech mocked; `.env` key presence was verified without logging it.
- Live microphone/audio and live PubMed/Muse services remain unverified here.
  Test in Terminal with a query, then abstract, full text, and next; confirm the
  entire content is audible and the next prompt follows completion.
- Reading is still synchronous: spoken pause/resume/stop during playback are not
  implemented. A future playback controller is needed for those capabilities.

### Confirmed silent default voice — follow-up
Outside the sandbox, the default macOS voice generated only 0.005351 seconds
(236 audio bytes) for a complete sentence, while explicit Samantha generated
3.833560 seconds (169060 audio bytes). Both commands returned success. Output
volume was 63 and not muted. This identifies a silent default-voice synthesis
failure; the earlier shared-engine hypothesis was not established.
The app now explicitly selects Samantha. Optionally set
VOICE_PUBMED_TTS_VOICE in the environment or existing .env to another installed
voice. MODEL_API_KEY and Muse remain unchanged. Audible user confirmation is
still needed; a successful exit alone is insufficient evidence of speech.

## Current speech and playback — Nova (2026-09-08)
This supersedes the Samantha/default-voice workaround above. The user preferred
CardioClaw's narration; inspected CardioClaw settings confirm OpenAI Nova, not
Siri, generates that audio. Voice PubMed uses the same model, voice, and calm
medical narration instructions, with no runtime dependency on CardioClaw.

- MODEL_API_KEY remains exclusively Muse recognition. OPENAI_API_KEY powers
  Nova; the launcher loads both from the existing local .env. Do not print keys.
- nova_speech.py handles bounded paragraph chunks, 64-entry session audio cache,
  and asynchronous AVAudioPlayer playback. Only playback runs in a worker;
  Muse capture remains on the main application loop with selected mic intact.
- During article reading: pause, resume/continue, stop reading, repeat paragraph,
  next paragraph, previous paragraph, faster, slower, next article, previous
  article, save, help. Optional prefix: "reader". Commands use exact matching.
- Pause/resume preserves the audio position. Repeat restarts the current
  paragraph; paragraphs longer than 1200 characters span multiple audio chunks.
  Speed changes by 0.25, bounded to 0.5–2.0. Stop returns to the article menu;
  say abstract/full text to restart. Save during reading returns to the menu
  and saves the citation. Next/previous keep their existing article meaning.
- Spoken acknowledgements temporarily pause article playback. Use headphones
  for controls while reading: this integration has no acoustic echo cancellation.
  Recognition occurs after Muse detects the end of the command, not instantly
  when the first sound is made. Network latency affects response time.
- OpenAI requests time out after 30 seconds without automatic retries. Stopping
  prevents late audio from playing; an already submitted synthesis request may
  still complete and be billed. Audio cache lives in memory only and is bounded.
- No silent Samantha fallback. Speech failures report an error and end the app.
- Launch as before; `./run_voice_pubmed_bot.command --speech-test` gives a short
  Nova-only test without microphone use or PubMed lookup. Restart existing app
  instances to load these changes.
- Validation: 13 offline tests passed. The actual launcher generated and played
  a live Nova sample successfully. A real AVAudioPlayer test verified pause holds
  currentTime, resume advances it, speed changes to 1.25x, and stop returns.
  End-to-end spoken Muse commands still need the user microphone/headphone test.

## Playback command reliability — continuous Muse (2026-09-08)
User reports missed controls with Mac speakers. Found: previous control loop
opened and closed Muse/mic every 2–5 seconds and only accepted exact phrases.
New playback_controls.py keeps the Muse ENDPOINTING stream open across turns;
muse_stt.transcribe_once and MODEL_API_KEY selection remain compatible.
Narration begins only after the microphone session reports ready. Pause/stop
use partial transcripts with per-turn deduplication; navigation waits for the
complete turn to distinguish next article from next paragraph. The listener is
cancelled and joined before returning to menu microphone capture.

Speaker usage: "Reader", wait for narration to quiet, then command. An early
Reader transcript temporarily pauses playback for eight seconds. Natural command
variants are accepted; longer narration only permits an embedded command after
Reader. No acoustic echo cancellation is implemented: headset still preferable
for loud playback. Prompt speech mutes outbound command audio temporarily; normal
playback feedback avoids extra synthesis so resume is not blocked by an ack.
If continuous Muse fails, reading pauses and the existing capture/fallback path
is used. Control transcripts are printed briefly for diagnosis, not saved.
Validation: 21 offline tests passed, including repeated endpointed turns over one
mocked connection and unchanged one-shot query behavior. A live Muse test with
prerecorded Nova commands recognized Reader pause and Reader resume in the same
connection and closed cleanly. This used no live microphone and does not verify
room acoustics or speaker/user overlap. User speaker test remains necessary.

## More results (2026-09-08)
The initial batch remains five. More results / show more / next five fetch the
next PubMed page using retstart, append unseen PMIDs, and navigate to its first
new title. Next at the last loaded result also fetches another page. Previous
works across batches. On retrieval failure the offset and current article are
preserved. Main passes the original search query into navigation. During article
reading, more results is deferred back to the article navigation loop, stopping
playback and closing its microphone first. Nova and Muse configuration unchanged.
Validation: all 27 tests pass, including offset use, boundary navigation,
previous across batches, duplicate filtering, and retry after fetch failure.
