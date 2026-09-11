"""Nova narration and interruptible local playback; no dependency on CardioClaw."""
from collections import OrderedDict
import os
import re
import threading
import time
import textwrap

MODEL = 'gpt-4o-mini-tts'
VOICE = 'nova'
INSTRUCTIONS = (
    'Speak clearly and professionally at a measured, calm pace. '
    'You are a knowledgeable medical colleague briefing a physician. '
    'Pronounce medical terminology carefully and accurately. '
    'Pause naturally between sentences. Do not rush.'
)


def segments(text):
    """Keep paragraph boundaries and bound requests well below the token limit."""
    result = []
    for paragraph, block in enumerate(re.split(r'\n\s*\n', text.strip())):
        for chunk in textwrap.wrap(block, width=1200):
            result.append((paragraph, chunk))
    return result


class NovaAudio:
    def __init__(self, client=None):
        if client is None:
            from openai import OpenAI
            if not os.environ.get('OPENAI_API_KEY'):
                raise RuntimeError('Set OPENAI_API_KEY in the Voice PubMed .env file for Nova speech.')
            client = OpenAI(timeout=30.0, max_retries=0)
        self.client = client
        self.cache = OrderedDict()
        self.lock = threading.Lock()

    def synthesize(self, text):
        with self.lock:
            if text in self.cache:
                self.cache.move_to_end(text)
                return self.cache[text]
            try:
                response = self.client.audio.speech.create(
                    model=MODEL, voice=VOICE, input=text,
                    instructions=INSTRUCTIONS, response_format='mp3',
                )
                audio = response.content
            except Exception as exc:
                # Avoid logging provider responses or credentials.
                raise RuntimeError('Nova speech generation failed. Check the OpenAI key, credit balance, and connection.') from exc
            if not audio:
                raise RuntimeError('Nova returned empty audio.')
            self.cache[text] = audio
            if len(self.cache) > 64:
                self.cache.popitem(last=False)
            return audio


class MacPlayer:
    def __init__(self, audio):
        from AVFoundation import AVAudioPlayer
        from Foundation import NSData
        data = NSData.dataWithBytes_length_(audio, len(audio))
        self.player, error = AVAudioPlayer.alloc().initWithData_error_(data, None)
        if self.player is None or self.player.duration() < 0.05:
            raise RuntimeError('Could not decode speech audio.')
        self.player.setEnableRate_(True)
        self.player.prepareToPlay()

    def play(self):
        if not self.player.play():
            raise RuntimeError('Audio playback could not start. Check the Mac output device.')

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()

    def playing(self):
        return bool(self.player.isPlaying())

    def rate(self, value):
        self.player.setRate_(value)


class Reading:
    """Playback worker; microphone capture stays in the application's main loop."""
    def __init__(self, text, audio, player_factory=MacPlayer):
        self.parts = segments(text)
        self.audio = audio
        self.player_factory = player_factory
        self.lock = threading.RLock()
        self.done = threading.Event()
        self.index = 0
        self.version = 0
        self.player = None
        self.paused = False
        self.speed = 1.0
        self.error = None
        self.stopped = False
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        return self

    def _run(self):
        try:
            while not self.stopped:
                with self.lock:
                    if self.index >= len(self.parts):
                        break
                    version, index = self.version, self.index
                    needs_audio = self.player is None and not self.paused
                if needs_audio:
                    audio = self.audio.synthesize(self.parts[index][1])
                    with self.lock:
                        # Discard an in-flight generation after skip/stop.
                        if self.stopped or version != self.version:
                            continue
                        self.player = self.player_factory(audio)
                        self.player.rate(self.speed)
                        if not self.paused:
                            self.player.play()
                else:
                    with self.lock:
                        if self.player and not self.paused and not self.player.playing():
                            self.player.stop()
                            self.player = None
                            self.index += 1
                            self.version += 1
                time.sleep(0.03)
        except Exception as exc:
            self.error = exc
        finally:
            with self.lock:
                if self.player:
                    self.player.stop()
            self.done.set()

    def pause(self):
        with self.lock:
            was_playing = not self.paused
            self.paused = True
            if self.player:
                self.player.pause()
            return was_playing

    def resume(self):
        with self.lock:
            if self.paused:
                self.paused = False
                if self.player:
                    self.player.play()

    def stop(self):
        with self.lock:
            self.stopped = True
            self.version += 1
            if self.player:
                self.player.stop()
            self.done.set()

    def _move(self, index):
        with self.lock:
            self.index = max(0, min(index, len(self.parts)))
            self.version += 1
            if self.player:
                self.player.stop()
            self.player = None

    def paragraph(self, direction):
        with self.lock:
            if self.index >= len(self.parts):
                return
            current = self.parts[self.index][0]
            target = max(0, current + direction)
            index = next((i for i, (p, _) in enumerate(self.parts) if p >= target), len(self.parts))
            self._move(index)

    def change_speed(self, delta):
        with self.lock:
            self.speed = round(max(0.5, min(2.0, self.speed + delta)), 2)
            if self.player:
                self.player.rate(self.speed)
            return self.speed


def normalize_command(text):
    text = re.sub(r"[^a-z ]", " ", (text or "").lower())
    return re.sub(r"\s+", " ", text).strip()


def control(text):
    """Accept polite command phrases; require a wake word inside longer text."""
    text = normalize_command(text)
    if 'reader' in text.split():
        # Narration may precede the user's wake word when using speakers.
        text = text.rsplit('reader', 1)[1].strip()
    text = re.sub(r'^(?:please |can you |could you |would you )+', '', text)
    text = re.sub(r'(?: please| now| thank you| thanks)+$', '', text)
    return {
        'pause': 'pause', 'pause reading': 'pause', 'pause the reading': 'pause',
        'hold on': 'pause', 'wait': 'pause',
        'resume': 'resume', 'resume reading': 'resume', 'continue': 'resume',
        'continue reading': 'resume', 'keep reading': 'resume', 'go on': 'resume',
        'stop': 'stop', 'stop reading': 'stop', 'stop the reading': 'stop',
        'repeat': 'repeat', 'repeat paragraph': 'repeat', 'repeat that': 'repeat',
        'read that again': 'repeat', 'repeat the paragraph': 'repeat',
        'next paragraph': 'forward', 'skip paragraph': 'forward',
        'skip this paragraph': 'forward', 'skip to the next paragraph': 'forward',
        'previous paragraph': 'back', 'go back': 'back', 'back a paragraph': 'back',
        'go back a paragraph': 'back',
        'faster': 'faster', 'read faster': 'faster', 'speed up': 'faster',
        'slower': 'slower', 'read slower': 'slower', 'slow down': 'slower',
        'next': 'next', 'next article': 'next', 'next paper': 'next',
        'previous': 'previous', 'previous article': 'previous', 'previous paper': 'previous',
        'save': 'save', 'save this': 'save', 'save article': 'save',
        'more': 'more', 'more results': 'more', 'more articles': 'more',
        'show more': 'more', 'show more results': 'more', 'next five': 'more',
        'five more': 'more', 'next results': 'more',
        'help': 'help',
    }.get(text)
