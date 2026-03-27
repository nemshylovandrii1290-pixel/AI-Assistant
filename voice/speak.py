import json
import queue
import re
import threading
from urllib import parse, request

import numpy as np
import pyttsx3
import sounddevice as sd

from utils.config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_MODEL_ID,
    ELEVENLABS_OUTPUT_FORMAT,
    ELEVENLABS_VOICE_ID,
)


TTS_ALIASES = [
    ("github desktop", "гітхаб десктоп"),
    ("github", "гітхаб"),
    ("microsoft store", "майкрософт стор"),
    ("sublime text", "саблайм текст"),
    ("youtube music", "ютуб мьюзік"),
    ("youtube", "ютуб"),
    ("telegram", "телеграм"),
    ("discord", "діскорд"),
    ("steam", "стім"),
    ("chatgpt", "чат джіпіті"),
    ("microsoft", "майкрософт"),
    ("google", "гугл"),
]


def _speak_with_pyttsx3(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def _prepare_tts_text(text):
    spoken = text
    for source, target in TTS_ALIASES:
        spoken = spoken.replace(source, target)
        spoken = spoken.replace(source.title(), target)
        spoken = spoken.replace(source.upper(), target)
    return spoken


def _elevenlabs_sample_rate():
    try:
        codec, sample_rate = ELEVENLABS_OUTPUT_FORMAT.split("_", 1)
        if codec != "pcm":
            return None
        return int(sample_rate)
    except (AttributeError, ValueError):
        return None


def _try_elevenlabs(text):
    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY is not configured")
    if not ELEVENLABS_VOICE_ID:
        raise RuntimeError("ELEVENLABS_VOICE_ID is not configured")

    sample_rate = _elevenlabs_sample_rate()
    if not sample_rate:
        raise RuntimeError(
            f"Unsupported ELEVENLABS_OUTPUT_FORMAT '{ELEVENLABS_OUTPUT_FORMAT}'. Use pcm_<sample_rate>."
        )

    query = parse.urlencode({"output_format": ELEVENLABS_OUTPUT_FORMAT})
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}?{query}"
    payload = json.dumps(
        {
            "text": text,
            "model_id": ELEVENLABS_MODEL_ID,
        }
    ).encode("utf-8")

    http_request = request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Accept": "audio/pcm",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY,
        },
    )

    with request.urlopen(http_request, timeout=30) as response:
        audio_bytes = response.read()

    if not audio_bytes:
        raise RuntimeError("ElevenLabs returned empty audio")

    audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    sd.play(audio, sample_rate)
    sd.wait()


def speak(text):
    if not text:
        return

    print("Асистент:", text)
    spoken_text = _prepare_tts_text(text)

    try:
        _try_elevenlabs(spoken_text)
    except Exception as error:
        print(f"ElevenLabs error: {error}")
        try:
            _speak_with_pyttsx3(spoken_text)
        except Exception as fallback_error:
            print(f"Voice error: {fallback_error}")


class StreamingSpeechPlayer:
    def __init__(self, min_chunk_chars=48):
        self.min_chunk_chars = min_chunk_chars
        self.queue = queue.Queue()
        self.stop_event = threading.Event()
        self.thread = None
        self.current_generation = 0
        self.buffer = ""

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._worker, name="tts-playback", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.queue.put(("stop", None, None))
        if self.thread:
            self.thread.join(timeout=2.0)

    def begin(self):
        generation_id = self.current_generation + 1
        self.current_generation = generation_id
        self.queue.put(("begin", generation_id, None))
        return generation_id

    def push_text(self, generation_id, text):
        if text:
            self.queue.put(("text", generation_id, text))

    def end(self, generation_id):
        self.queue.put(("flush", generation_id, None))

    def speak_stream(self, generator):
        generation_id = self.begin()
        for chunk in generator:
            self.push_text(generation_id, chunk)
        self.end(generation_id)

    def _worker(self):
        active_generation = 0

        while not self.stop_event.is_set():
            event_type, generation_id, payload = self.queue.get()

            if event_type == "stop":
                break

            if event_type == "begin":
                active_generation = generation_id
                self.buffer = ""
                continue

            if generation_id != active_generation:
                continue

            if event_type == "text":
                self.buffer += payload
                continue

            if event_type == "flush":
                full_text = self.buffer.strip()
                if full_text:
                    speak(full_text)
                self.buffer = ""


_STREAM_PLAYER = StreamingSpeechPlayer()


def speak_stream(generator):
    _STREAM_PLAYER.start()
    _STREAM_PLAYER.speak_stream(generator)
