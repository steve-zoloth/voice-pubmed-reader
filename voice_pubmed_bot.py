import speech_recognition as sr
import pyttsx3
import requests
from bs4 import BeautifulSoup
import os

# Initialize text-to-speech
tts = pyttsx3.init()
tts.setProperty('rate', 150)

# Reference file
REF_FILE = os.path.expanduser("~/Downloads/references.txt")

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
        answer = listen_for_speech("Do you want to use the MacBook microphone and speakers? Say yes or no.")
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
        choice = listen_for_speech("Say the number of the microphone you want to use.")
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
    with sr.Microphone(device_index=mic_i
