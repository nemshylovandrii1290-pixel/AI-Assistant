import os
import time

import numpy as np

from utils.config import (
    DYNAMIC_THRESHOLD_MULTIPLIER,
    SAMPLE_RATE,
    SILENCE_TIMEOUT,
    SPEECH_THRESHOLD,
    WHISPER_LANGUAGES,
)


_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel

        model_name = os.getenv("WHISPER_MODEL", "small")
        model_device = os.getenv("WHISPER_DEVICE", "cpu")
        compute_type = os.getenv(
            "WHISPER_COMPUTE_TYPE",
            "float16" if model_device == "cuda" else "int8",
        )
        _MODEL = WhisperModel(model_name, device=model_device, compute_type=compute_type)
    return _MODEL


def _transcribe_once(audio_input, language):
    segments, info = _get_model().transcribe(
        audio_input,
        language=language,
        beam_size=1,
        best_of=1,
        temperature=0.0,
        condition_on_previous_text=False,
        vad_filter=True,
        without_timestamps=True,
        initial_prompt=(
            "edit едіт едит stop стоп вистачить "
            "увімкни вимкни ігрове середовище робоче середовище "
            "відкрий open github steam discord telegram chatgpt sublime text microsoft store"
        ),
    )
    text = " ".join(segment.text.strip() for segment in segments).strip()
    probability = getattr(info, "language_probability", 0.0) or 0.0
    return text, probability


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


def _pick_best_transcript(audio_input):
    language = WHISPER_LANGUAGES[0] if WHISPER_LANGUAGES else "uk"
    text, probability = _transcribe_once(audio_input, language)

    if text:
        print(f"[speech:{language}] recognized")
    return text if is_valid_text(text) else ""


def recognize(audio_data, samplerate=SAMPLE_RATE):
    if audio_data is None:
        return ""

    if isinstance(audio_data, str):
        audio_input = audio_data
    else:
        audio_input = np.asarray(audio_data).reshape(-1).astype("float32") / 32768.0

    return _pick_best_transcript(audio_input)


class StreamingRecognizer:
    def __init__(
        self,
        samplerate=SAMPLE_RATE,
        partial_interval=0.9,
        max_window_seconds=1.6,
        silence_timeout=SILENCE_TIMEOUT,
        min_speech_seconds=0.35,
    ):
        self.samplerate = samplerate
        self.partial_interval = partial_interval
        self.max_window_samples = int(self.samplerate * max_window_seconds)
        self.silence_timeout = silence_timeout
        self.min_speech_samples = int(self.samplerate * min_speech_seconds)
        self.ambient_levels = []
        self.speech_active = False
        self.current_utterance = []
        self.current_utterance_id = 0
        self.last_voice_time = 0.0
        self.last_partial_time = 0.0
        self.last_partial_text = ""
        self.stable_count = 0
        self.trailing_buffer = np.zeros(0, dtype=np.int16)

    def _speech_level_threshold(self):
        if not self.ambient_levels:
            return SPEECH_THRESHOLD
        ambient = float(np.median(self.ambient_levels))
        return max(SPEECH_THRESHOLD, int(ambient * DYNAMIC_THRESHOLD_MULTIPLIER))

    def _append_ambient(self, level):
        self.ambient_levels.append(level)
        if len(self.ambient_levels) > 12:
            self.ambient_levels = self.ambient_levels[-12:]

    def _append_chunk(self, chunk):
        flattened = np.asarray(chunk).reshape(-1).astype(np.int16)
        self.trailing_buffer = np.concatenate([self.trailing_buffer, flattened])
        if len(self.trailing_buffer) > self.max_window_samples:
            self.trailing_buffer = self.trailing_buffer[-self.max_window_samples:]
        return flattened

    def process_chunk(self, chunk):
        if chunk is None:
            return []

        now = time.monotonic()
        flattened = self._append_chunk(chunk)
        level = float(np.abs(flattened).mean())
        threshold = self._speech_level_threshold()
        is_speech = level >= threshold

        if not self.speech_active:
            self._append_ambient(level)

        events = []

        if is_speech:
            if not self.speech_active:
                self.speech_active = True
                self.current_utterance_id += 1
                self.current_utterance = [self.trailing_buffer.copy()]
                self.last_partial_text = ""
                self.last_partial_time = 0.0
                self.stable_count = 0
            else:
                self.current_utterance.append(flattened)

            self.last_voice_time = now

            if (
                now - self.last_partial_time >= self.partial_interval
                and sum(len(part) for part in self.current_utterance) >= self.min_speech_samples
            ):
                partial_audio = np.concatenate(self.current_utterance[-8:], axis=0)
                partial_text = recognize(partial_audio, samplerate=self.samplerate)
                self.last_partial_time = now

                if partial_text == self.last_partial_text:
                    self.stable_count += 1
                else:
                    self.stable_count = 0
                    self.last_partial_text = partial_text

                if (
                    is_valid_text(partial_text)
                    and self.stable_count >= 2
                    and len(partial_text.strip()) > 5
                ):
                    events.append(
                        {
                            "type": "partial",
                            "utterance_id": self.current_utterance_id,
                            "text": partial_text,
                        }
                    )

            return events

        if self.speech_active:
            self.current_utterance.append(flattened)
            if now - self.last_voice_time >= self.silence_timeout:
                audio = np.concatenate(self.current_utterance, axis=0)
                self.speech_active = False
                self.current_utterance = []
                self.last_partial_time = 0.0
                self.stable_count = 0
                self.trailing_buffer = np.zeros(0, dtype=np.int16)

                if len(audio) >= self.min_speech_samples:
                    final_text = recognize(audio, samplerate=self.samplerate)
                    if is_valid_text(final_text):
                        events.append(
                            {
                                "type": "final",
                                "utterance_id": self.current_utterance_id,
                                "text": final_text,
                            }
                        )

        return events
