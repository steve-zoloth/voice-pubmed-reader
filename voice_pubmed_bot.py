import speech_recognition as sr
import pyttsx3
import os
import xml.etree.ElementTree as ET
from Bio import Entrez

# Required by NCBI's usage policy for Entrez API calls.
Entrez.email = "zoloth1@verizon.net"

# Initialize text-to-speech
tts = pyttsx3.init()
tts.setProperty('rate', 150)

# Reference file inside the same folder
REF_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references.txt")


def speak(text):
    print(text)
    tts.say(text)
    tts.runAndWait()


def listen_for_speech(prompt=None, timeout=5):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    if prompt:
        speak(prompt)
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=timeout)
            text = recognizer.recognize_google(audio)
            return text.lower()
        except sr.WaitTimeoutError:
            speak("I did not hear anything. Please try again.")
            return None
        except sr.UnknownValueError:
            speak("Sorry, I did not understand. Please try again.")
            return None
        except sr.RequestError as e:
            speak(f"Speech recognition error: {e}")
            return None


def select_microphone():
    mics = sr.Microphone.list_microphone_names()
    while True:
        answer = listen_for_speech(
            "Do you want to use the MacBook microphone and speakers? Say yes or no."
        )
        if answer in ["yes", "no"]:
            break
        speak("Please say yes or no.")

    if answer == "yes":
        for i, name in enumerate(mics):
            if "Built-in" in name or "MacBook" in name:
                speak(f"Selected microphone: {name}")
                return i
        speak("MacBook microphone not found. Moving to manual selection.")

    speak("Listing available microphones.")
    for i, name in enumerate(mics):
        speak(f"Microphone {i}: {name}")

    while True:
        choice = listen_for_speech(
            "Say the number of the microphone you want to use."
        )
        if choice is None:
            continue
        try:
            index = int(''.join(filter(str.isdigit, choice)))
            if 0 <= index < len(mics):
                speak(f"Selected microphone: {mics[index]}")
                return index
            else:
                speak("That number is out of range. Try again.")
        except ValueError:
            speak("I could not understand the number. Try again.")


def listen_for_query(mic_index):
    recognizer = sr.Recognizer()
    with sr.Microphone(device_index=mic_index) as source:
        recognizer.adjust_for_ambient_noise(source)
        speak("Listening now. Please say your PubMed query.")
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio)
        speak(f"You said: {text}")
        return text.lower()
    except sr.UnknownValueError:
        speak("Sorry, could not understand audio.")
        return None
    except sr.RequestError as e:
        speak(f"Could not request results; {e}")
        return None


# Uses NCBI's official Entrez E-utilities API (not HTML scraping) — reliable and
# won't silently break if PubMed changes its page markup. Same approach used in
# CardioClaw's cardio_claw.py. Still abstract-only, not full paper text.

def search_pubmed(query, max_results=5):
    """Search PubMed and return (titles, pmids) for the top results."""
    try:
        with Entrez.esearch(db="pubmed", term=query, retmax=max_results) as handle:
            record = Entrez.read(handle)
        pmids = record.get("IdList", [])
        if not pmids:
            return [], []
        with Entrez.esummary(db="pubmed", id=",".join(pmids)) as handle:
            summaries = Entrez.read(handle)
        titles = [s.get("Title", "No title").rstrip(".") for s in summaries]
        return titles, pmids
    except Exception as e:
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


def save_reference(title, pmid):
    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    with open(REF_FILE, "a") as f:
        f.write(f"{title} - {url}\n")
    speak("Reference saved.")


def navigate_results(titles, pmids):
    index = 0
    while index < len(titles):
        speak(f"Article {index + 1}: {titles[index]}")
        while True:
            cmd = listen_for_speech(
                "Say 'abstract', 'full text', 'next', 'previous', or 'save'."
            )
            if cmd is None:
                continue
            if "full text" in cmd:
                full = fetch_full_text(pmids[index])
                if full:
                    speak("Full text is available. Reading now. This may take a while.")
                    speak(full)
                else:
                    speak(
                        "Full text is not available in PubMed Central for this "
                        "article — likely paywalled. Here is the abstract instead."
                    )
                    speak(fetch_abstract(pmids[index]))
            elif "abstract" in cmd:
                abstract = fetch_abstract(pmids[index])
                speak(f"Abstract: {abstract}")
            elif "next" in cmd:
                index += 1
                break
            elif "previous" in cmd:
                if index > 0:
                    index -= 1
                break
            elif "save" in cmd:
                save_reference(titles[index], pmids[index])
            else:
                speak("Command not recognized. Say 'abstract', 'full text', 'next', 'previous', or 'save'.")
        if index >= len(titles):
            speak("No more articles.")


def main():
    mic_index = select_microphone()
    query = listen_for_query(mic_index)
    if query:
        titles, pmids = search_pubmed(query)
        if titles:
            navigate_results(titles, pmids)
        else:
            speak("No results found.")


if __name__ == "__main__":
    main()
