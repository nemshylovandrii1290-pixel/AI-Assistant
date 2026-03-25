import pyttsx3
import sounddevice as sd
import torch


_MODEL = None
_MODEL_SPEAKER = "v4_ua"
_VOICE_SPEAKER = "mykyta"
_SAMPLE_RATE = 48000

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


def _get_silero_model():
    global _MODEL

    if _MODEL is None:
        torch.set_num_threads(1)
        model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-models",
            model="silero_tts",
            language="ua",
            speaker=_MODEL_SPEAKER,
        )
        _MODEL = model

    return _MODEL


def _try_silero(text):
    audio = _get_silero_model().apply_tts(
        text=text,
        speaker=_VOICE_SPEAKER,
        sample_rate=_SAMPLE_RATE,
    )

    if hasattr(audio, "cpu"):
        audio = audio.cpu().numpy()

    sd.play(audio, _SAMPLE_RATE)
    sd.wait()


def _prepare_tts_text(text):
    spoken = text
    for source, target in TTS_ALIASES:
        spoken = spoken.replace(source, target)
        spoken = spoken.replace(source.title(), target)
        spoken = spoken.replace(source.upper(), target)
    return spoken


def speak(text):
    if not text:
        return

    print("Асистент:", text)
    spoken_text = _prepare_tts_text(text)

    try:
        _try_silero(spoken_text)
    except Exception as error:
        print(f"Silero error: {error}")
        try:
            _speak_with_pyttsx3(spoken_text)
        except Exception as fallback_error:
            print(f"Voice error: {fallback_error}")
