import io
import wave

import speech_recognition as sr

from utils.config import RECOGNITION_LANGUAGES


def _recognize_with_languages(recognizer, audio):
    request_error = None

    for language in RECOGNITION_LANGUAGES:
        try:
            text = recognizer.recognize_google(audio, language=language)
            if text:
                print(f"[speech:{language}] recognized")
                return text
        except sr.UnknownValueError:
            continue
        except sr.RequestError as error:
            request_error = error

    if request_error:
        print("Помилка сервісу:", request_error)

    return ""


def recognize(audio_data, samplerate=16000):
    if audio_data is None:
        return ""

    recognizer = sr.Recognizer()

    if isinstance(audio_data, str):
        with sr.AudioFile(audio_data) as source:
            audio = recognizer.record(source)
            return _recognize_with_languages(recognizer, audio)

    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(samplerate)
        wav_file.writeframes(audio_data.tobytes())

    wav_buffer.seek(0)

    with sr.AudioFile(wav_buffer) as source:
        audio = recognizer.record(source)
        return _recognize_with_languages(recognizer, audio)
