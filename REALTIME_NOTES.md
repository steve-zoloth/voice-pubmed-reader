# Realtime reader baseline and setup

## Launch and retained versions

Open `run_realtime_pubmed.command` and activate Start voice in the browser. Allow browser microphone access. Close the old browser session and restart the launcher after updates. Terminal alternative:

```bash
bash "$HOME/Documents/voice_pubmed_bot/run_realtime_pubmed.command"
```

The original `run_voice_pubmed_bot.command` still runs Muse recognition, Google fallback, and Nova output. End the browser session before switching. Both use the same saved references file. There is no CardioClaw dependency.

The existing `.env` supplies `OPENAI_API_KEY` for Realtime and Nova and `MODEL_API_KEY` for Muse. Optional `OPENAI_REALTIME_MODEL` overrides the default `gpt-realtime-2.1`; the account must have model access and API billing. Realtime uses Marin, while the original reader retains Nova. No additional Python packages are required beyond the original installation. Browser WebRTC support is required. The API key stays on the local Python server. Microphone audio and requested source passages are sent to OpenAI.

## Refined interaction

Search directly with a clear query; the reader no longer routinely asks for confirmation or recites command menus. Abstracts use the structured abstract body, omitting the title/citation/author preamble. Ask “who are the authors?” to retrieve names.

Try “go to methods,” “read the results,” “skip to conclusions,” “what sections are available?”, “read full text,” “keep reading,” “repeat,” “next article,” or “stop.” Section jumps match headings actually provided by PubMed or PMC, including nested PMC headings. Unstructured abstracts do not gain invented sections. Load full text to navigate its headings. Full-text availability remains limited to PMC.

“Skip ahead ten seconds” and “go back twenty seconds” estimate a source-text position at 150 words/minute using elapsed browser playback. These are approximate, not seeks within a recorded audio timeline. Natural speech speed, acknowledgments and network timing affect precision. Reading continues in passages of at most 180 words; “continue” moves to the next passage, while “repeat” restarts the last passage. Resume at the exact interrupted word, continuous automatic long-form narration, and exact time seeking remain future work.

## Architecture

- Original microphone/STT: `muse_stt.py`, selected-device capture, and `capture()` in `voice_pubmed_bot.py`; optional Google fallback.
- Original command interpretation: procedural navigation in `voice_pubmed_bot.py`, normalized controls in `nova_speech.py`, continuous reading controls in `playback_controls.py`.
- Original output: Nova generation and local playback in `nova_speech.py`, invoked by `speak()` and `read_article()`.
- Existing PubMed logic: Entrez search/title retrieval, abstract retrieval, PMC lookup/full text, and reference saving in `voice_pubmed_bot.py`. The checkout has no independent DOI full-text retrieval or broader bibliography system.
- Realtime adapter: browser microphone/output over WebRTC; model interprets intent through an allowlisted reader tool. Python owns article state, source position, pagination and saving. `structured_reader.py` adds structured XML retrieval for headings and abstract-only reading without changing the legacy functions.

GPT-Realtime-2.1 duplex has already been implemented and tested; Steve reported a significant improvement over Muse. This is the established primary voice path. Do not restart feasibility work or switch to GPT-Live-1 without a separate explicit comparison request. Existing retrieval functions and legacy navigation remain present. The only legacy compatibility changes are an optional silent save acknowledgment and the Realtime launch option. Realtime has its own navigation adapter. Muse is retained: Steve reported successful live use and interruption, but Andrew has not yet compared recognition accuracy or usability.

## Verification and remaining comparison

Offline tests cover legacy voice/playback/pagination, adapter navigation and retry, preservation of source words, full-text fallback, save, sections, authors, skip boundaries, and XML heading extraction. Browser event checks cover tool results, suppressing narration after interrupted retrieval, and stop cancellation. Both launchers previously passed controlled environment/routing checks with external services/audio mocked. These checks do not establish live recognition or speech accuracy.

Compare both versions with Andrew using medical queries (including “sarcopenia and elderly males”), interruptions with speakers and headphones, results/conclusion navigation, author omission, and numerical source fidelity. Record recognition corrections, missed/false interruptions, usability and API cost before retiring either version. Generated narration is instructed to read faithfully, but verbatim fidelity still requires listening validation.

## Official API sources consulted

- [WebRTC](https://developers.openai.com/api/docs/guides/voice-webrtc): Realtime unified `/v1/realtime/calls`, server-side credentials, WebRTC audio and model example.
- [Realtime conversations](https://developers.openai.com/api/docs/guides/realtime-conversations): tool results, interruption and output-buffer clearing.
- [Voice activity detection](https://developers.openai.com/api/docs/guides/realtime-vad): semantic VAD and automatic interruption.

This adapter uses Realtime interfaces, not GPT-Live interfaces.

## Counts, review articles, and shorter replies

Search now announces PubMed's total match count separately from the number loaded. Ask “how many articles were found?” at any time. Count failures are reported as unavailable, never replaced with the loaded count. Article titles announce Review, Systematic Review, or Meta-Analysis when present in PubMed publication-type metadata. Ask “is this a review?” for publication types. “Only reviews” reruns the current topic with publication-type filters; a new plain search removes that filter. These labels depend on PubMed indexing, not a model's guess, so recently added or unclassified reviews can be missed.

Tool responses now explicitly request only the result text, without chatter or follow-up questions. Stop tool results no longer trigger another spoken response. Long article passages are still read when requested.

## Accessibility audit — 2026-09-11

Local branch: muse-upgrade, HEAD a745c08. The five local commits contain the
original reader, PMC full text, Entrez repair and project instructions. The
Realtime adapter, browser, structured reader, tests and recent notes are
untracked; Muse/Nova changes also include staged and unstaged work. Thus the
working Realtime baseline and subsequent enhancements are not in local Git
history. Remote branch freshness was not established by the offline audit.

Already implemented before this audit: WebRTC duplex with automatic interruption
and browser echo cancellation, structured abstracts without author preambles,
PMC full-text fallback, sections, pagination, total counts, publication-type
labels and review filters, concise tool narration, and suppression of late
speech after interrupted retrieval. PubMed retrieval remains shared with the
legacy app; no CardioClaw dependency or GPT-Live replacement was introduced.

Targeted changes: titles announce position out of total results (or loaded
results when total is unavailable); informational commands preserve the passage
for repeat; continue without loaded text explains how to start reading. Queued
commands superseded by interruption are cancelled before submitting retrieval
or navigation. In-flight retrieval can still finish and update state, but its
late result must not restart speech. Status updates expose retrieval activity
while microphone/barge-in remains available. Instructions explicitly prohibit
advancing on silence, acknowledgments or unclear speech, and distinguish repeat
on resume from explicit next-passage continuation. This instruction guard cannot
guarantee recognition accuracy. README now identifies Realtime as primary.

Validation: 40 offline Python tests pass; browser JavaScript and both launcher
shell syntax checks pass. The actual Realtime launcher loads configuration and
routes to the Realtime entry point in a controlled test with network/audio
mocked. These checks do not replace live listening. Still needs Andrew's test
of title/abstract/full-text fidelity, speaker barge-in, pauses and mistaken
recognition. Reading remains explicit 180-word passages; exact audio seeking,
word-level resume and automatic continuous long-form reading remain absent.
