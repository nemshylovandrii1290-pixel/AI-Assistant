import speech_recognition as sr
import io
import wave

from utils.config import LANGUAGE


def recognize(audio_data, samplerate=16000):
    r = sr.Recognizer()

    if isinstance(audio_data, str):
        with sr.AudioFile(audio_data) as source:
            audio = r.record(source)
            try:
                return r.recognize_google(audio, language=LANGUAGE)
            except sr.UnknownValueError:
                print("Не вдалося розпізнати мову.")
                return ""
            except sr.RequestError as e:
                print("Помилка сервісу:", e)
                return ""

    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(samplerate)
        f.writeframes(audio_data.tobytes())

    wav_buffer.seek(0)

    with sr.AudioFile(wav_buffer) as source:
        audio = r.record(source)
        try:
            return r.recognize_google(audio, language=LANGUAGE)

        except sr.UnknownValueError:
            print("Не вдалося розпізнати мову.")
            return ""
        except sr.RequestError as e:
            print("Помилка сервісу:", e)
            return ""
