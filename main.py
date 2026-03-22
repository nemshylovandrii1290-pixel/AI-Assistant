import time

from voice.listen import listen
from voice.speak import speak
from brain.ai import ask_ai
from voice.recognize import recognize
from brain.commands import execute_action
from utils.normalize import normalize_text

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

    original_text = text

    if any(word in text_lower for word in WAKE_WORDS):
      last_activation_time = time.time()

      for word in WAKE_WORDS:
        text_lower = text_lower.replace(word, "").strip()

      if not text_lower:
        speak("Так?")
        continue
      text = text_lower

    if not is_active():
      continue

    if text == original_text and any(word in original_text.lower() for word in WAKE_WORDS):
      text = text_lower

    text = normalize_text(text)
    ai_result = ask_ai(text)
    result_type = ai_result.get("type")

    if result_type == "command":
      result = execute_action(ai_result.get("action"), ai_result)
      speak(result)
      continue

    if result_type == "chat":
      speak(ai_result.get("response", "Не зрозумів запит."))
      continue

    speak("Не зрозумів запит.")


if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    print("\nАсистент зупинений.")
  else:
    print("Асистент зупинений.")
