"""Continuous Muse playback commands with early pause and bounded cleanup."""
import queue
import threading
import time
import muse_stt
from nova_speech import control, normalize_command


class PlaybackControls:
    def __init__(self, device):
        self.device = device
        self.ready = threading.Event()
        self.stop_event = threading.Event()
        self.muted = threading.Event()
        self.events = queue.Queue(maxsize=16)
        self.error = None
        self.early = None
        self.attention_sent = False
        self.suppressed_turn = False
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _offer(self, command):
        try:
            self.events.put_nowait(command)
        except queue.Full:
            pass  # Bound stale commands; don't block audio streaming.

    def _transcript(self, text, final):
        if self.muted.is_set():
            self.suppressed_turn = True
        if self.suppressed_turn:
            if final:
                self.suppressed_turn = False
                self.early = None
                self.attention_sent = False
            return
        command = control(text)
        # Early commands must be exact phrases or follow the explicit wake word.
        if command in ('pause', 'stop') and self.early is None:
            self.early = command
            self._offer(command)
        elif not self.attention_sent and self.early is None:
            normalized = normalize_command(text)
            if normalized.endswith('reader'):
                self.attention_sent = True
                self._offer('attention')
        if final:
            if command and self.early is None:
                self._offer(command)
            print(f'[control] {text[:160]!r} -> {command or "unrecognized"}', flush=True)
            self.early = None
            self.attention_sent = False

    def _run(self):
        try:
            muse_stt.stream_commands(
                self.device, self._transcript, self.ready.set,
                self.stop_event, self.muted,
            )
        except Exception:
            self.error = RuntimeError('Continuous Muse controls disconnected.')
            self.ready.set()

    def start(self):
        self.thread.start()
        # Both websocket connect and authorization have their own 15s bound.
        if not self.ready.wait(35):
            self.close()
            raise RuntimeError('Muse controls did not become ready.')
        if self.error:
            self.close()
            raise self.error
        return self

    def get(self, timeout=.1):
        if self.error:
            raise self.error
        try:
            return self.events.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self):
        self.stop_event.set()
        if self.thread.ident is not None:
            self.thread.join(3)
        if self.thread.is_alive():
            raise RuntimeError('Microphone did not close; restart the reader before listening again.')
