import os
import sys

import numpy as np

from utils.config import CHUNK_DURATION, SAMPLE_RATE
from utils.normalize import fix_words


_MODEL = None


def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def _patch_faster_whisper_assets():
    try:
        import faster_whisper.utils as fw_utils
        import faster_whisper.vad as fw_vad
    except ImportError:
        return

    def _assets_path():
        bundled_assets = resource_path(os.path.join("faster_whisper", "assets"))
        if os.path.exists(bundled_assets):
            return bundled_assets
        return os.path.join(os.path.dirname(os.path.abspath(fw_utils.__file__)), "assets")

    fw_utils.get_assets_path = _assets_path
    fw_vad.get_assets_path = _assets_path


def _get_model():
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel

        _patch_faster_whisper_assets()

        model_name = os.getenv("WHISPER_MODEL", "small")
        model_device = os.getenv("WHISPER_DEVICE", "cpu")
        compute_type = os.getenv(
            "WHISPER_COMPUTE_TYPE",
            "float16" if model_device == "cuda" else "int8",
        )
        _MODEL = WhisperModel(model_name, device=model_device, compute_type=compute_type)
    return _MODEL


def is_valid_text(text):
    if not text:
        return False

    normalized = text.strip().lower()
    if len(normalized) < 3:
        return False

    if normalized in {"ай", "е", "а", "мм", "эм", "uh", "um"}:
        return False

    unique_chars = set(normalized.replace(" ", ""))
    if len(normalized) > 12 and len(unique_chars) <= 2:
        return False

    return True


def _postprocess_text(text):
    normalized = fix_words(text.strip().lower())
    return normalized.strip()


def recognize(audio_data, samplerate=SAMPLE_RATE):
    if audio_data is None:
        return ""

    audio_input = np.asarray(audio_data).reshape(-1).astype("float32") / 32768.0

    segments, info = _get_model().transcribe(
        audio_input,
        language="uk",
        beam_size=3,
        best_of=3,
        temperature=0.0,
        condition_on_previous_text=False,
        vad_filter=True,
        without_timestamps=True,
        initial_prompt=(
            "edit едіт едит stop стоп вистачить "
            "увімкни вимкни ігрове середовище робоче середовище "
            "відкрий github steam discord telegram chatgpt sublime text microsoft store"
        ),
    )
    text = " ".join(segment.text.strip() for segment in segments).strip()
    text = _postprocess_text(text)

    if text:
        print("[speech:uk] recognized")

    return text if is_valid_text(text) else ""


class StreamingRecognizer:
    def __init__(
        self,
        samplerate=SAMPLE_RATE,
        silence_chunks=5,
        threshold=400,
        min_speech_seconds=0.35,
    ):
        self.samplerate = samplerate
        self.silence_limit = max(1, silence_chunks)
        self.threshold = threshold
        self.min_speech_samples = int(self.samplerate * min_speech_seconds)
        self.speech_active = False
        self.silence_counter = 0
        self.audio_buffer = []
        self.utterance_id = 0
        self.chunk_samples = max(1, int(self.samplerate * CHUNK_DURATION))

    def process_chunk(self, chunk):
        if chunk is None:
            return []

        flattened = np.asarray(chunk).reshape(-1).astype(np.int16)
        volume = float(np.abs(flattened).mean())

        if volume > self.threshold:
            if not self.speech_active:
                self.utterance_id += 1
                self.audio_buffer = []
                self.speech_active = True

            self.silence_counter = 0
            self.audio_buffer.append(flattened)
            return []

        if self.speech_active:
            self.audio_buffer.append(flattened)
            self.silence_counter += 1

            if self.silence_counter > self.silence_limit:
                full_audio = np.concatenate(self.audio_buffer, axis=0)
                current_utterance_id = self.utterance_id
                self.audio_buffer = []
                self.speech_active = False
                self.silence_counter = 0

                if len(full_audio) < self.min_speech_samples:
                    return []

                text = recognize(full_audio, samplerate=self.samplerate)
                if not is_valid_text(text):
                    return []

                return [
                    {
                        "type": "final",
                        "utterance_id": current_utterance_id,
                        "text": text,
                    }
                ]

        return []
