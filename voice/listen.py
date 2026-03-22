import sounddevice as sd
import wave

def listen(duration=5, filename="audio.wav"):
  samplerate = 16000

  print("Listening...")
  audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
  sd.wait()

  with wave.open(filename, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(samplerate)
    wf.writeframes(audio.tobytes())

    return filename
