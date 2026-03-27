import numpy as np

from utils.config import WHISPER_LANGUAGES


_MODEL = None
_STREAM_BUFFER = np.zeros(0, dtype=np.int16)


def _get_model():
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel

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
        initial_prompt=(
            "edit edid edit stop stop stop uvimkny vymkny "
            "ihrove seredovyshche robochyi prostir vidkryi "
            "github github desktop telegram microsoft store "
            "chatgpt sublime text cute lock steam discord"
        ),
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

        if any(
            word in lowered
            for word in (
                "edit",
                "edid",
                "stop",
                "uvimkny",
                "vymkny",
                "vidkryi",
                "github",
                "telegram",
                "microsoft",
                "steam",
                "discord",
            )
        ):
            score += 20

        if language == "uk" and any(
            word in lowered
            for word in ("uvimkny", "vymkny", "vidkryi", "ihrov", "roboch")
        ):
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


def reset_stream_buffer():
    global _STREAM_BUFFER
    _STREAM_BUFFER = np.zeros(0, dtype=np.int16)


def process_chunk(chunk):
    global _STREAM_BUFFER

    if chunk is None:
        return ""

    flattened = np.asarray(chunk).reshape(-1).astype(np.int16)
    _STREAM_BUFFER = np.concatenate([_STREAM_BUFFER, flattened])

    max_samples = 16000 * 2
    if len(_STREAM_BUFFER) > max_samples:
        _STREAM_BUFFER = _STREAM_BUFFER[-max_samples:]

    if len(_STREAM_BUFFER) < 16000:
        return ""

    return recognize(_STREAM_BUFFER)
