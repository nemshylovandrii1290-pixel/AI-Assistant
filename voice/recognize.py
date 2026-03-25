import os
import tempfile
import wave

from faster_whisper import WhisperModel


_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = WhisperModel("base", device="cpu", compute_type="int8")
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
        segments, info = _get_model().transcribe(audio_path, beam_size=1)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        if text:
            detected_language = getattr(info, "language", "unknown")
            print(f"[speech:{detected_language}] recognized")
        return text
    finally:
        if remove_after and os.path.exists(audio_path):
            os.remove(audio_path)
