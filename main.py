from voice.listen import listen
from voice.speak import speak
from brain.ai import ask_ai
from voice.recognize import recognize

def main():
  while True:
    audio_file = listen()
    text = recognize(audio_file)

    if not text:
      print("Не вдалося розпізнати мову.")
      continue

    print("Ти сказав:", text)

    response = ask_ai(text)
    speak(response)


if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    print("\nАсистент зупинений.")
