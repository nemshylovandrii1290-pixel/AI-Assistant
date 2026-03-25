import os
import tempfile
import wave

from faster_whisper import WhisperModel

from utils.config import WHISPER_LANGUAGES


_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = WhisperModel("small", device="cpu", compute_type="int8")
    return _MODEL


def _write_temp_wav(audio_data, samplerate):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_file.close()

    with wave.open(temp_file.name, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(samplerate)
        wav_file.writeframes(audio_data.tobytes())

    return temp_file.name


def _transcribe_once(audio_path, language):
    segments, info = _get_model().transcribe(
        audio_path,
        language=language,
        beam_size=1,
        best_of=2,
        temperature=0.0,
        condition_on_previous_text=False,
        vad_filter=True,
        initial_prompt="edit едіт едит стоп вистачить увімкни ігровий режим робочий режим відкрий",
    )
    text = " ".join(segment.text.strip() for segment in segments).strip()
    probability = getattr(info, "language_probability", 0.0) or 0.0
    return text, probability


def _pick_best_transcript(audio_path):
    best_text = ""
    best_language = None
    best_score = -1.0

    for language in WHISPER_LANGUAGES:
        text, probability = _transcribe_once(audio_path, language)
        if not text:
            continue

        score = len(text) + probability * 5
        lowered = text.lower()
        if any(word in lowered for word in ("edit", "едіт", "едит", "stop", "стоп", "увімкни", "вимкни", "відкрий")):
            score += 20
        if language == "uk" and any(word in lowered for word in ("увімкни", "вимкни", "відкрий", "ігровий", "робочий")):
            score += 8

        if score > best_score:
            best_text = text
            best_language = language
            best_score = score

    if best_text:
        print(f"[speech:{best_language}] recognized")
    return best_text


def recognize(audio_data, samplerate=16000):
    if audio_data is None:
        return ""

    if isinstance(audio_data, str):
        audio_path = audio_data
        remove_after = False
    else:
        audio_path = _write_temp_wav(audio_data, samplerate)
        remove_after = True

    try:
        return _pick_best_transcript(audio_path)
    finally:
        if remove_after and os.path.exists(audio_path):
            os.remove(audio_path)
