"""Muse Voice Transcribe streaming client for voice_pubmed_bot.

Wraps Meta's Muse Voice Transcribe realtime endpoint
(``wss://api.meta.ai/v1/asr/realtime``) in one blocking call,
:func:`transcribe_once`, that records from the microphone until the model
detects the end of the utterance and hands back the final transcript.

Why this exists: it replaces ``speech_recognition.recognize_google`` — an
unofficial, no-SLA endpoint with no endpointing and no timeout. Muse gives us
native speech-boundary detection (mode ``ENDPOINTING``), so a listen call
returns as soon as the speaker stops instead of blocking forever.

Docs: https://dev.meta.ai/docs/speech-to-text
Needs: ``websockets``, ``sounddevice``, and ``MODEL_API_KEY`` in the environment.
Pricing: ~$0.18 per audio-hour ($3 / 1000 audio-minutes) as of Sept 2026.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid

try:
    import sounddevice as sd
except (OSError, ImportError) as exc:  # PortAudio missing, or package absent
    sd = None
    _SD_IMPORT_ERROR = exc
else:
    _SD_IMPORT_ERROR = None

import websockets

# Both Muse endpoints are served from the Model API host; this is the streaming
# one. The public model name is fixed at the handshake.
STREAM_URL = "wss://api.meta.ai/v1/asr/realtime"
MODEL = "muse-voice-transcribe-1.0"

# 24 kHz is the engine-native rate. Frames are raw signed 16-bit little-endian
# mono PCM with no container — just the sample bytes.
SAMPLE_RATE = 24_000
BYTES_PER_SEC = SAMPLE_RATE * 2
CHUNK_MS = 80
FRAME_SAMPLES = SAMPLE_RATE * CHUNK_MS // 1000

# Cap the capture queue at ~240 ms of audio. The server drops any session whose
# ingress falls more than 5 s behind real time, so hoarding PCM during a network
# stall helps nothing — better to drop the oldest frame and stay current.
MAX_QUEUE_FRAMES = 3

# Connecting and the handshake reply should both be quick; fail loudly if not.
CONNECT_TIMEOUT = 15.0

# Once the speaker has started, this is how long a gap in server events we
# tolerate before giving up on `speechComplete` and returning the best partial.
POST_SPEECH_TIMEOUT = 6.0


class STTError(RuntimeError):
    """Muse Voice Transcribe was unreachable, refused the key, or errored.

    Raised so the caller can fall back to another recognizer rather than crash.
    """


def available() -> tuple[bool, str]:
    """Return ``(ok, reason)``. ``ok`` is False when Muse cannot be used."""
    if sd is None:
        return False, f"sounddevice unavailable ({_SD_IMPORT_ERROR})"
    if not os.environ.get("MODEL_API_KEY"):
        return False, "MODEL_API_KEY is not set"
    return True, ""


def _close_code(exc: BaseException) -> int | None:
    """Pull the WebSocket close code off a ConnectionClosed, if there is one."""
    code = getattr(exc, "code", None)
    if code is None:
        rcvd = getattr(exc, "rcvd", None)
        code = getattr(rcvd, "code", None)
    return code


def _closed_to_error(exc: BaseException) -> STTError:
    advice = {
        1008: "audio was paced too slow or too fast for the server",
        1011: "server error, or the 60-minute session cap was reached",
        1013: "rate limited; wait a moment and try again",
    }.get(_close_code(exc), "the connection closed unexpectedly")
    return STTError(advice)


async def _record_utterance(
    device: int | None, initial_timeout: float, max_seconds: float,
    *, on_text=None, on_ready=None, muted=None,
) -> str:
    """Open the mic and the WebSocket, stream until the turn ends, return text."""
    token = os.environ["MODEL_API_KEY"]
    url = f"{STREAM_URL}?sessionId=pubmedbot-{uuid.uuid4()}"

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=MAX_QUEUE_FRAMES)

    def on_audio(indata, _frames, _time, status) -> None:
        # Runs on sounddevice's own thread, so hand the frame to the loop.
        if status:
            print(status, file=sys.stderr)
        loop.call_soon_threadsafe(_offer, bytes(indata))

    def _offer(frame: bytes) -> None:
        if queue.full():
            queue.get_nowait()  # drop the oldest frame; stay real time
        queue.put_nowait(frame)

    try:
        connection = websockets.connect(
            url, open_timeout=CONNECT_TIMEOUT, close_timeout=1.0, max_size=None
        )
        async with connection as ws:
            # The credential rides inside the first JSON frame — a browser
            # cannot set headers on a WebSocket, so the server ignores the
            # Authorization header here and reads this instead.
            await ws.send(
                json.dumps(
                    {
                        "authorization": {"accessToken": f"Bearer {token}"},
                        "audioEncoding": "PCM_24KHZ",
                        "model": MODEL,
                        # Let the model find the end of the utterance; this is
                        # the whole point of the swap.
                        "mode": "ENDPOINTING",
                        # Each partial replaces the last.
                        "partialMode": "CUMULATIVE",
                        "emitAudioProgress": False,
                    }
                )
            )

            # The server always answers the handshake first. Read it before
            # sending audio so a bad key / model surfaces as a clean error.
            try:
                ack = json.loads(
                    await asyncio.wait_for(ws.recv(), timeout=CONNECT_TIMEOUT)
                )
            except asyncio.TimeoutError as exc:
                raise STTError("no handshake response from Muse") from exc
            if ack.get("type") == "error" or "sessionId" not in ack:
                raise STTError(f"handshake rejected: {ack.get('message', ack)}")

            stream = sd.RawInputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
                blocksize=FRAME_SAMPLES,
                device=device,
                callback=on_audio,
            )

            best = ""
            heard_speech = False

            async def pump_audio() -> None:
                while True:
                    frame = await queue.get()
                    # Keep the stream alive during spoken feedback, sending silence.
                    if muted is not None and muted.is_set():
                        frame = bytes(len(frame))
                    await ws.send(frame)  # binary frame

            with stream:
                if on_ready is not None:
                    on_ready()
                pump = asyncio.create_task(pump_audio())
                try:
                    deadline = loop.time() + max_seconds
                    while True:
                        remaining = deadline - loop.time()
                        if remaining <= 0:
                            break
                        quiet = 30.0 if on_text is not None else (POST_SPEECH_TIMEOUT if heard_speech else initial_timeout)
                        try:
                            raw = await asyncio.wait_for(
                                ws.recv(), timeout=min(remaining, quiet)
                            )
                        except asyncio.TimeoutError:
                            if on_text is not None:
                                continue
                            # Silence: either nothing was ever said, or the
                            # speaker stopped and endpointing did not fire.
                            break
                        except websockets.exceptions.ConnectionClosed as exc:
                            raise _closed_to_error(exc) from exc

                        if isinstance(raw, bytes):
                            continue
                        event = json.loads(raw)
                        etype = event.get("type")
                        if etype == "error":
                            raise STTError(
                                event.get("message", "transcription error")
                            )
                        if etype == "speechStart":
                            heard_speech = True
                            best = ""
                        elif etype == "transcript" and event.get("transcript"):
                            best = event["transcript"]
                            if on_text is not None:
                                on_text(best, False)
                            elif event.get("final"):
                                break
                        elif etype == "speechComplete":
                            # Whole-turn text; the model may post-process it, so
                            # it can differ from the last partial. Prefer it.
                            if event.get("transcript"):
                                best = event["transcript"]
                            if on_text is not None:
                                on_text(best, True)
                                best = ""
                                heard_speech = False
                            else:
                                break
                finally:
                    pump.cancel()
                    await asyncio.gather(pump, return_exceptions=True)
                    # Half-close the input so the server finalises the turn.
                    try:
                        await ws.send(json.dumps({"type": "endStream"}))
                    except websockets.exceptions.WebSocketException:
                        pass

            return best.strip()

    except STTError:
        raise
    except (OSError, asyncio.TimeoutError) as exc:
        raise STTError(f"could not reach Muse Voice Transcribe ({exc})") from exc
    except websockets.exceptions.WebSocketException as exc:
        raise STTError(f"Muse Voice Transcribe connection failed ({exc})") from exc


def transcribe_once(
    device: int | None = None,
    *,
    initial_timeout: float = 8.0,
    max_seconds: float = 45.0,
) -> str:
    """Record one spoken utterance and return it as lowercase text.

    Returns ``""`` if nothing was heard within ``initial_timeout`` seconds, or
    if the speaker runs past ``max_seconds``. Raises :class:`STTError` on any
    transport or API failure so the caller can fall back to another recognizer.

    ``device`` is a sounddevice input-device index (see ``sd.query_devices()``),
    or ``None`` for the system default input.
    """
    ok, reason = available()
    if not ok:
        raise STTError(reason)
    text = asyncio.run(_record_utterance(device, initial_timeout, max_seconds))
    return text.lower()


def stream_commands(device, on_text, on_ready, stop_event, muted):
    """Continuous endpointed turns for playback only; one-shot API is unchanged.

    Cancel the async task on stop, including while connecting or handshaking,
    so the old microphone cannot leak into the next article/menu capture.
    """
    ok, reason = available()
    if not ok:
        raise STTError(reason)

    async def run():
        async def watch_stop():
            while not stop_event.is_set():
                await asyncio.sleep(0.05)
        while not stop_event.is_set():
            # Renew before the provider's session ceiling on very long readings.
            record = asyncio.create_task(_record_utterance(
                device, 30.0, 55 * 60, on_text=on_text,
                on_ready=on_ready, muted=muted,
            ))
            stopper = asyncio.create_task(watch_stop())
            try:
                done, _ = await asyncio.wait((record, stopper), return_when=asyncio.FIRST_COMPLETED)
                if record in done:
                    await record
            finally:
                record.cancel()
                stopper.cancel()
                await asyncio.gather(record, stopper, return_exceptions=True)
    asyncio.run(run())


if __name__ == "__main__":  # quick self-check: python3 muse_stt.py
    ok, why = available()
    print(f"Muse Voice Transcribe available: {ok}" + (f"  ({why})" if why else ""))
    if sd is not None:
        print("\nInput devices:")
        for i, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] > 0:
                mark = " (default)" if i == sd.default.device[0] else ""
                print(f"  {i}: {dev['name']}{mark}")
