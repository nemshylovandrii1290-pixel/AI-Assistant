import numpy as np

from faster_whisper import WhisperModel

from utils.config import WHISPER_LANGUAGES


_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = WhisperModel("small", device="cpu", compute_type="int8")
    return _MODEL


def _transcribe_once(audio_input, language):
    segments, info = _get_model().transcribe(
        audio_input,
        language=language,
        beam_size=1,
        best_of=2,
        temperature=0.0,
        condition_on_previous_text=False,
        vad_filter=True,
        initial_prompt="edit едіт едит стоп вистачить увімкни ігровий режим робочий режим відкрий telegram chatgpt sublime text",
    )
    text = " ".join(segment.text.strip() for segment in segments).strip()
    probability = getattr(info, "language_probability", 0.0) or 0.0
    return text, probability


def _pick_best_transcript(audio_input):
    best_text = ""
    best_language = None
    best_score = -1.0

    for language in WHISPER_LANGUAGES:
        text, probability = _transcribe_once(audio_input, language)
        if not text:
            continue

        lowered = text.lower()
        score = len(text) + probability * 5

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
        audio_input = audio_data
    else:
        audio_input = np.asarray(audio_data).reshape(-1).astype("float32") / 32768.0

    return _pick_best_transcript(audio_input)
