import sounddevice as sd
import torch


_MODEL = None
_SPEAKER = "v4_ua"
_SAMPLE_RATE = 48000


def _get_model():
    global _MODEL

    if _MODEL is None:
        torch.set_num_threads(1)
        model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-models",
            model="silero_tts",
            language="ua",
            speaker=_SPEAKER,
        )
        _MODEL = model

    return _MODEL


def speak(text):
    if not text:
        return

    print("Асистент:", text)

    try:
        audio = _get_model().apply_tts(
            text=text,
            speaker=_SPEAKER,
            sample_rate=_SAMPLE_RATE,
        )

        if hasattr(audio, "cpu"):
            audio = audio.cpu().numpy()

        sd.play(audio, _SAMPLE_RATE)
        sd.wait()
    except Exception as error:
        print(f"Voice playback error: {error}")
