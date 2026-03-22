import time

from voice.listen import listen
from voice.speak import speak
from brain.ai import ask_ai
from voice.recognize import recognize
from brain.commands import handle_command

WAKE_WORDS = ["edit", "едіт", "едит"]

ACTIVE_TIMEOUT = 300  # 🔥 секунд (можеш поставити 300 = 5 хв)
last_activation_time = 0

def is_active():
    return time.time() - last_activation_time < ACTIVE_TIMEOUT


def main():
  global last_activation_time

  while True:
    audio_file = listen()
    text = recognize(audio_file)

    if not text:
      print("Не вдалося розпізнати мову.")
      continue

    text_lower = text.lower()
    print("Ти сказав:", text)

    if "стоп" in text_lower or "вистачить" in text_lower:
      last_activation_time = 0
      speak("Окей, вимикаюсь")
      return

    # 🔥 якщо сказали wake word → активуємося
    if any(word in text_lower for word in WAKE_WORDS):
      last_activation_time = time.time()
      for word in WAKE_WORDS:
        text_lower = text_lower.replace(word, "").strip()

      if not text_lower:
        speak("Привіт! Чим можу допомогти?")
        continue

    # ❌ якщо НЕ активний → ігноруємо
    if not is_active():
      continue

    if text_lower != text.lower():
      speak("Так?")
      text = text_lower

    # 🔧 команди
    command_response = handle_command(text)
    if command_response:
      speak(command_response)
      continue

    # 🤖 AI
    response = ask_ai(text)
    speak(response)

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    print("\nАсистент зупинений.")
  else:
    print("Асистент зупинений.")
