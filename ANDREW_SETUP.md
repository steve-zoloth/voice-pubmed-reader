# Voice PubMed Reader — Mac launch and Andrew handoff

## On Steve's configured Mac

Open **Voice PubMed Reader.app** in your home Applications folder
(`/Users/stevezoloth/Applications/Voice PubMed Reader.app`). You can drag it to
the Dock. This launcher runs the existing reader without opening Terminal.
It uses the existing .env and installed Python environment; no key is embedded
in the app. Keep the current repository folder in place.

The browser opens after the Nova announcement. Press Enter or activate Start
voice, then allow microphone access if requested. Marin says “PubMed ready.
I am listening.” The app does not bypass microphone permissions or start capture
automatically. Choose **End session** in the browser before quitting the launcher:
quitting the launcher stops the local server, but does not itself close a live
browser/OpenAI voice connection. Close old reader sessions before using the app.

## Siri setup on Mac

Create a Shortcut named **Read PubMed**, with one **Open App** action targeting
**Voice PubMed Reader**. Then ask Siri “Read PubMed.” The browser still requires
Start voice/Enter. VoiceOver can activate Start voice. Siri invocation has not
been tested on Steve's or Andrew's Mac.

Apple documents running a shortcut by speaking its name:
https://support.apple.com/guide/shortcuts-mac/apd07c25bb38/mac

## Andrew's Mac — one-time installation still required

This is a launcher for a configured installation, not a standalone distributable.
Do not send the app alone and assume Andrew is set up. On Andrew's Mac, a helper
must install the repository and compatible Python dependencies (biopython,
websockets, sounddevice, openai, pyobjc-framework-AVFoundation), configure his
API access locally, build the app with mac_app/build_mac_app.py, and complete
browser microphone permission. Do not copy Steve's credentials or saved research
into a distribution archive. The builder uses the local Python path and refuses
to overwrite an existing app. A built app is specific to the build Mac's CPU
architecture; build on the target Mac. It is locally signed, not notarized for
public distribution.

Example for the helper, from the repository:

    python3 mac_app/build_mac_app.py --destination "$HOME/Applications/Voice PubMed Reader.app"

If the repository has moved, the launcher offers a folder chooser. It keeps the
repository path in local application preferences. The app does not package Python,
install dependencies or log keys/transcripts. A stopped-server message means
installation/configuration needs checking; it is not an API billing diagnosis.

## iPhone/iPad — not yet delivered

The current loopback address works on the Mac only. An iPhone/iPad needs a secure
HTTPS backend with authenticated access and server-side API credentials, then a
Home Screen link / Open URL shortcut. It must be tested with Safari, VoiceOver,
real interruption and audio output; a Mac test does not establish mobile support.

Pending choice: independent hosted backend (works with Mac off) versus a private
connection to Andrew's running Mac. No public port, hosting deployment, new
account or CardioClaw server changes have been made. A Siri shortcut will open
the eventual reader; it cannot promise automatic microphone permission or bypass
Safari's user activation requirements.

## Response refinements — September 18

- Silent tool invocation; read the requested result, then stop, with no extra
  acknowledgment, summary or invitation.
- Semantic VAD eagerness is high for quicker turn completion. Set
  VOICE_PUBMED_TURN_EAGERNESS=auto in the existing .env to restore the previous
  wait if pauses within a sentence are cut short. This is a tradeoff, not measured
  proof of a latency reduction.
- Per-session 12-entry cache reuses successfully fetched abstract/full text on
  revisits. Failed or unavailable fetches remain retryable. No disk research cache.
- Realtime model, voice and PubMed retrieval functions are unchanged.

44 offline tests pass. Native app compilation and local signature validation
passed. Automated UI launch/quit verification was blocked by macOS computer-use
permissions; no live microphone or API audio test was run. Andrew's independent
launch and voice workflow acceptance remains required.
