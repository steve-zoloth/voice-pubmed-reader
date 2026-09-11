import os
import sys
import time
from nova_speech import NovaAudio, Reading, control
from playback_controls import PlaybackControls
import xml.etree.ElementTree as ET

from Bio import Entrez

import muse_stt

# speech_recognition is now only the fallback recognizer, used when Muse Voice
# Transcribe is unavailable (no MODEL_API_KEY) or fails mid-session.
try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover - fallback is optional
    sr = None

# Required by NCBI's usage policy for Entrez API calls.
Entrez.email = "zoloth1@verizon.net"

# Speech output is independent of Muse recognition.
_NOVA = None
_ACTIVE_READING = None
_ACTIVE_CONTROLS = None

# Reference file inside the same folder
REF_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references.txt")

# sounddevice input-device index chosen at startup, or None for the system
# default. Set once by select_microphone() and used by every listen call, so
# the selection is actually honoured (it used to be ignored outside the query).
SELECTED_DEVICE = None

_MUSE_OK, _MUSE_WHY = muse_stt.available()
_warned_no_muse = False


def nova():
    global _NOVA
    if _NOVA is None:
        _NOVA = NovaAudio()
    return _NOVA


def speak(text):
    """Speak prompts with Nova; temporarily pause any article for feedback."""
    print(text, flush=True)
    active = _ACTIVE_READING
    resume = active.pause() if active and not active.done.is_set() else False
    controls = _ACTIVE_CONTROLS
    if controls:
        controls.muted.set()
    reading = Reading(str(text), nova()).start()
    try:
        while not reading.done.wait(0.05):
            pass
        if reading.error:
            raise reading.error
    finally:
        reading.stop()
        if controls:
            time.sleep(0.2)  # Let the speaker tail decay before unmuting capture.
            controls.muted.clear()
        if resume and not active.done.is_set():
            active.resume()


READING_HELP = (
    "For voice controls, say Reader, then pause, resume, stop reading, "
    "repeat paragraph, next paragraph, previous paragraph, faster, or slower. "
    "With speakers, say Reader, wait for the narration to quiet, then your command. "
    "Say more results to load more articles. "
    "Headphones improve recognition if the speaker audio is too loud."
)


def read_article(text):
    """Keep Muse's microphone session open throughout article playback."""
    global _ACTIVE_READING, _ACTIVE_CONTROLS
    speak(READING_HELP)
    print(text, flush=True)
    reading = Reading(text, nova())
    controls = None
    attention_until = None
    attention_resume = False
    try:
        if _MUSE_OK:
            try:
                controls = PlaybackControls(SELECTED_DEVICE).start()
            except RuntimeError:
                speak('Continuous controls are unavailable. Using basic command listening.')
        # Never start narration before Muse has opened the microphone.
        reading.start()
        _ACTIVE_READING = reading
        _ACTIVE_CONTROLS = controls
        while not reading.done.is_set():
            if controls:
                try:
                    command = controls.get()
                except RuntimeError:
                    reading.pause()
                    _ACTIVE_CONTROLS = None
                    controls.close()
                    controls = None
                    speak('Command listening disconnected. Reading is paused. Say resume when ready.')
                    continue
            else:
                command = control(capture(initial_timeout=8.0, max_seconds=10.0))
            if command == 'attention':
                if attention_until is None:
                    attention_resume = reading.pause()
                attention_until = time.monotonic() + 8.0
                continue
            if command:
                # Navigation/speed after a wake word preserves the prior state.
                if attention_until is not None and attention_resume and command not in ('pause', 'stop'):
                    reading.resume()
                attention_until = None
            elif attention_until is not None and time.monotonic() >= attention_until:
                if attention_resume:
                    reading.resume()
                attention_until = None
            if command in ('next', 'previous', 'save', 'more'):
                return command
            if command == 'stop':
                reading.stop()
                speak('Reading ended. You are back at the article menu.')
                return None
            if command == 'pause':
                reading.pause()
                # Narration becoming quiet is immediate feedback; don't block the
                # command loop on another cloud synthesis before accepting resume.
                print('Paused. Say Reader resume.', flush=True)
            elif command == 'resume':
                reading.resume()
            elif command in ('repeat', 'forward', 'back'):
                reading.paragraph({'repeat': 0, 'forward': 1, 'back': -1}[command])
            elif command in ('faster', 'slower'):
                speed = reading.change_speed(0.25 if command == 'faster' else -0.25)
                print(f'Reading speed {speed} times.', flush=True)
            elif command == 'help':
                speak(READING_HELP)
        if reading.error:
            raise reading.error
    finally:
        reading.stop()
        _ACTIVE_READING = None
        _ACTIVE_CONTROLS = None
        if controls:
            controls.close()
    speak('Reading complete.')
    return None


def _google_once(initial_timeout, max_seconds):
    """Fallback recognizer: PyAudio capture + Google's free STT endpoint.

    Always listens on the system default microphone — the fallback path does
    not honour SELECTED_DEVICE. Returns "" when nothing intelligible is heard;
    raises RuntimeError only for a hard request failure.
    """
    if sr is None:
        raise RuntimeError("speech_recognition is not installed; no fallback recognizer")
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(
                source, timeout=initial_timeout, phrase_time_limit=max_seconds
            )
        return recognizer.recognize_google(audio).lower()
    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        raise RuntimeError(f"Google speech recognition error: {e}") from e


def capture(prompt=None, *, initial_timeout=8.0, max_seconds=45.0):
    """Speak `prompt` (if any), then listen for one spoken utterance.

    Returns the utterance as lowercase text, or "" if nothing was heard.
    Prefers Muse Voice Transcribe; falls back to Google's recognizer when Muse
    is unavailable or errors. Unlike the old listen_for_speech, this never
    blocks indefinitely — Muse endpointing (or the fallback's timeout) ends the
    listen when the speaker stops, and max_seconds is a hard ceiling.
    """
    global _warned_no_muse
    if prompt:
        speak(prompt)

    if _MUSE_OK:
        try:
            return muse_stt.transcribe_once(
                device=SELECTED_DEVICE,
                initial_timeout=initial_timeout,
                max_seconds=max_seconds,
            )
        except muse_stt.STTError as exc:
            print(f"[muse_stt] {exc}", file=sys.stderr)
            speak("Voice transcription had a problem. Using the basic recognizer.")
    elif not _warned_no_muse:
        _warned_no_muse = True
        print(f"[muse_stt] unavailable: {_MUSE_WHY}", file=sys.stderr)
        speak("Muse Voice Transcribe is not configured. Using the basic recognizer.")

    try:
        return _google_once(initial_timeout, max_seconds)
    except RuntimeError as exc:
        print(f"[fallback] {exc}", file=sys.stderr)
        speak("Speech recognition is unavailable right now.")
        return ""


def listen_for_speech(prompt=None):
    """Short prompt/answer listen (yes/no, a menu word, a number)."""
    return capture(prompt, initial_timeout=8.0, max_seconds=20.0)


def select_microphone():
    """Pick the microphone to record from.

    Returns a sounddevice input-device index, or None for the system default.
    Defaults to the system default input and only lists devices if the user
    declines it, so the common case is one yes/no answer.
    """
    if muse_stt.sd is None:
        speak("Audio device library is unavailable. Using the system default microphone.")
        return None
    sd = muse_stt.sd

    try:
        devices = sd.query_devices()
        default_in = sd.default.device[0]
    except Exception as exc:  # PortAudio can raise a bare Exception here
        speak(f"Could not list microphones: {exc}. Using the system default.")
        return None

    if not isinstance(default_in, int) or default_in < 0:
        default_in = None
    inputs = [(i, d["name"]) for i, d in enumerate(devices) if d["max_input_channels"] > 0]
    if not inputs:
        speak("No input devices found. Using the system default microphone.")
        return None

    default_name = devices[default_in]["name"] if default_in is not None else "system default"
    answer = listen_for_speech(
        f"Use the default microphone, {default_name}? Say yes or no."
    )
    if answer != "no":
        speak(f"Using {default_name}.")
        return default_in

    speak("Listing available microphones.")
    for i, name in inputs:
        speak(f"Microphone {i}: {name}")

    valid = {i for i, _ in inputs}
    while True:
        choice = listen_for_speech("Say the number of the microphone you want to use.")
        if not choice:
            continue
        digits = "".join(ch for ch in choice if ch.isdigit())
        if not digits:
            speak("I could not understand the number. Try again.")
            continue
        index = int(digits)
        if index in valid:
            speak(f"Selected microphone: {devices[index]['name']}")
            return index
        speak("That number is out of range. Try again.")


def listen_for_query():
    """Listen for the PubMed search query (a longer, one-shot utterance)."""
    text = capture(
        "Listening now. Please say your PubMed query.",
        initial_timeout=10.0,
        max_seconds=60.0,
    )
    if not text:
        speak("I did not catch a query.")
        return None
    speak(f"You said: {text}")
    return text


# Uses NCBI's official Entrez E-utilities API (not HTML scraping) — reliable and
# won't silently break if PubMed changes its page markup. Same approach used in
# CardioClaw's cardio_claw.py. Still abstract-only, not full paper text.

def search_pubmed(query, max_results=5, start=0, *, raise_errors=False):
    """Return one PubMed result page, starting at the zero-based offset."""
    try:
        with Entrez.esearch(db="pubmed", term=query, retmax=max_results, retstart=start) as handle:
            record = Entrez.read(handle)
        pmids = record.get("IdList", [])
        if not pmids:
            return [], []
        with Entrez.esummary(db="pubmed", id=",".join(pmids)) as handle:
            summaries = Entrez.read(handle)
        titles = [s.get("Title", "No title").rstrip(".") for s in summaries]
        return titles, pmids
    except Exception as e:
        if raise_errors:
            raise RuntimeError("Could not load more results. Please try again.") from e
        speak(f"PubMed search failed: {e}")
        return [], []


def fetch_abstract(pmid):
    """Fetch the abstract text for one PMID."""
    try:
        with Entrez.efetch(db="pubmed", id=pmid, rettype="abstract", retmode="text") as handle:
            text = handle.read()
        text = text.strip()
        return text if text else "No abstract available."
    except Exception as e:
        return f"Could not fetch abstract: {e}"


def get_pmc_id(pmid):
    """Check whether this PubMed article has a full-text copy deposited in PMC
    (open access or NIH-funded). Returns None if not — most paywalled journal
    content (JACC, JAMA, Eur Heart J, etc.) will not have one."""
    try:
        with Entrez.elink(dbfrom="pubmed", db="pmc", id=pmid, linkname="pubmed_pmc") as handle:
            record = Entrez.read(handle)
        linksets = record[0].get("LinkSetDb", [])
        if not linksets:
            return None
        links = linksets[0].get("Link", [])
        return links[0]["Id"] if links else None
    except Exception:
        return None


def fetch_full_text(pmid):
    """Fetch full paper body text from PMC if available. Returns None if this
    article has no PMC copy (caller should fall back to the abstract)."""
    pmcid = get_pmc_id(pmid)
    if not pmcid:
        return None
    try:
        with Entrez.efetch(db="pmc", id=pmcid, rettype="full", retmode="xml") as handle:
            xml_data = handle.read()
        root = ET.fromstring(xml_data)
        body = root.find(".//body")
        if body is None:
            return None
        paragraphs = [
            "".join(p.itertext()).strip()
            for p in body.iter("p")
        ]
        full_text = "\n\n".join(p for p in paragraphs if p)
        return full_text if full_text.strip() else None
    except Exception:
        return None


def save_reference(title, pmid, *, announce=True):
    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    with open(REF_FILE, "a") as f:
        f.write(f"{title} - {url}\n")
    if announce:
        speak("Reference saved.")


def navigate_results(titles, pmids, query=None):
    # Retain loaded results so previous still works across page boundaries.
    next_start = len(pmids)

    def load_more():
        nonlocal next_start
        if query is None:
            speak('No search query is available for loading more results.')
            return None
        speak('Looking for five more results.')
        try:
            new_titles, new_pmids = search_pubmed(query, start=next_start, raise_errors=True)
        except RuntimeError as exc:
            speak(str(exc))
            return None  # A temporary failure must not advance the offset.
        next_start += len(new_pmids)
        known = set(pmids)
        additions = []
        for title, pmid in zip(new_titles, new_pmids):
            if pmid not in known:
                additions.append((title, pmid))
                known.add(pmid)
        for title, pmid in additions:
            titles.append(title)
            pmids.append(pmid)
        if additions:
            speak(f'Loaded {len(additions)} more results.')
        elif new_pmids:
            speak('Those results were already loaded. Say more results to keep looking.')
            return None
        else:
            speak('No additional PubMed results were found for this search.')
        return len(additions)

    index = 0
    pending = None
    while index < len(titles):
        speak(f"Article {index + 1}: {titles[index]}")
        while True:
            cmd = pending or listen_for_speech(
                "Say 'abstract', 'full text', 'next', 'previous', 'save', or 'more results'."
            )
            pending = None
            if not cmd:
                speak("I did not hear a command.")
                continue
            if control(cmd) == 'more':
                first_new = len(titles)
                if load_more():
                    index = first_new
                    break
            elif "full text" in cmd:
                full = fetch_full_text(pmids[index])
                if full:
                    speak("Full text is available. Reading now. This may take a while.")
                    pending = read_article(full)
                else:
                    speak(
                        "Full text is not available in PubMed Central for this "
                        "article — likely paywalled. Here is the abstract instead."
                    )
                    pending = read_article(fetch_abstract(pmids[index]))
            elif "abstract" in cmd:
                abstract = fetch_abstract(pmids[index])
                pending = read_article(f"Abstract: {abstract}")
            elif "next" in cmd:
                if index + 1 == len(titles) and query is not None:
                    count = load_more()
                    if count is None:
                        continue
                    if count == 0:
                        return
                index += 1
                break
            elif "previous" in cmd:
                if index > 0:
                    index -= 1
                break
            elif "save" in cmd:
                save_reference(titles[index], pmids[index])
            else:
                speak("Command not recognized. Say 'abstract', 'full text', 'next', 'previous', 'save', or 'more results'.")
        if index >= len(titles):
            speak("No more articles.")


def main():
    global SELECTED_DEVICE
    speak("Welcome to Voice PubMed Reader. You are hearing the AI-generated Nova voice.")
    SELECTED_DEVICE = select_microphone()
    query = listen_for_query()
    if not query:
        speak("No query received. Goodbye.")
        return
    titles, pmids = search_pubmed(query)
    if titles:
        navigate_results(titles, pmids, query=query)
    else:
        speak("No results found.")


if __name__ == "__main__":
    try:
        if '--realtime' in sys.argv:
            from realtime_adapter import main as realtime_main
            realtime_main()
        elif '--speech-test' in sys.argv:
            speak('This is Nova, the AI-generated voice for Voice PubMed Reader. I read titles, abstracts, and available full articles.')
        else:
            main()
    except KeyboardInterrupt:
        print('Voice PubMed stopped.', flush=True)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
