import speech_recognition as sr

from utils.config import LANGUAGE


def recognize(audio_file):
    r = sr.Recognizer()

    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)
        try:
            return r.recognize_google(audio, language=LANGUAGE)

        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
            return None
