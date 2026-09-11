> **Start here:** Read [AGENTS.md](AGENTS.md) and [CURRENT_BASELINE.md](CURRENT_BASELINE.md). The audited working version is **GPT-Realtime-2.1 in this repository**, on `muse-upgrade`. Do not restart from the older VoicePubMedWeb or mistake GPT-Live for the tested baseline. The history and version map are in [PROJECT_HISTORY_AUDIT.md](PROJECT_HISTORY_AUDIT.md).

# Voice PubMed Reader

Launch `run_realtime_pubmed.command` from Finder, then activate **Start voice**.
GPT-Realtime-2.1 duplex voice is the primary, already tested reader and was
reported significantly better than Muse. It is not awaiting feasibility testing.
GPT-Live-1 has not replaced it. See [Realtime notes](REALTIME_NOTES.md).

Say search and your topic, next, previous, repeat, stop, abstract, full text,
keep reading, or go to results/conclusions. Titles announce article position;
search announces total matches and loaded results. Reading uses passages of up
to 180 words: keep reading requests the next passage; repeat rereads the current
passage. Silence never requests another passage. Exact audio seeking and exact
word-level resume are not supported; time skips remain approximate.

The sections below describe the retained **Muse/Nova fallback**, launched with
`run_voice_pubmed_bot.command`. End the Realtime session before using it.

## Configuration
The existing `.env` holds `MODEL_API_KEY` for Muse and `OPENAI_API_KEY` for
Nova. Keep this file private. Speech generation sends article text to OpenAI
and uses API credits. Muse recognition and its Google fallback are preserved.

## More search results
The first five results are loaded initially. Say **more results** (or **Reader
more results** during reading) to load the next five and hear the first new title.
Saying **next** at the last loaded article also loads another batch automatically.
Previous still returns to earlier articles. A failed request can be retried.

## Reading controls
When using speakers, say **Reader**, wait for narration to quiet, then say
**pause**, **resume**, or another command. You can also say **Reader pause**
in one phrase. Headphones improve recognition if the speaker audio is loud.
Say **abstract** or **full text** at the article menu. During reading:

- **Pause** / **resume**: hold and continue at the same position.
- **Stop reading**: return to the article menu.
- **Repeat paragraph**: restart the current paragraph.
- **Next paragraph** / **previous paragraph**: navigate the reading.
- **Faster** / **slower**: change playback speed.
- **Next article** / **previous article**: switch results.
- **Save**: stop reading and save this citation.
- **Help**: hear the commands again.

You can prefix a command with "reader", for example "reader pause".
While paused, paragraph navigation preserves the paused state; say resume.
Muse stays connected throughout reading. Pause and stop can act on partial
transcripts; other commands wait for the completed phrase. Common variations
such as "please pause", "slow down", and "read that again" are accepted.
Saying Reader alone temporarily pauses for up to eight seconds to hear you.
Control-C exits. This is not acoustic echo cancellation; overlapping speaker
audio may still obscure your voice.

## Test
`./run_voice_pubmed_bot.command --speech-test` plays Nova without microphone
or PubMed access. `python3 -m unittest -v test_voice_output test_playback_controls` runs offline tests.

Dependencies on this Mac: Python 3, openai, biopython, sounddevice, websockets,
pyobjc-framework-AVFoundation, and optionally SpeechRecognition/PyAudio for
Google fallback. The existing launcher loads configuration from this folder.
