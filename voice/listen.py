import sounddevice as sd
import wave

from utils.config import LISTEN_DURATION, SAMPLE_RATE


def listen(duration=LISTEN_DURATION, filename="audio.wav"):
  samplerate = SAMPLE_RATE

  print("Listening...")
  audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
  sd.wait()

  with wave.open(filename, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(samplerate)
    wf.writeframes(audio.tobytes())

    return filename
