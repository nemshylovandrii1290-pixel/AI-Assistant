import json
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
    ("youtube music", "ютуб м'юзік"),
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

def speak_stream(generator):
    buffer = ""

    for chunk in generator:
        buffer += chunk

        if len(buffer) > 30:
            speak(buffer)
            buffer = ""

    if buffer:
        speak(buffer)


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
