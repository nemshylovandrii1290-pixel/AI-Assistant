import time

from brain.ai import ask_ai
from brain.commands import execute_action, execute_actions
from utils.app_finder import ensure_app_index
from utils.context import get_runtime_context
from utils.intent_parser import extract_open_target
from utils.intent_router import resolve_local_intent
from utils.memory import remember_app_launch, remember_phrase_actions
from utils.normalize import normalize_text
from voice.listen import listen
from voice.recognize import recognize
from voice.speak import speak


WAKE_WORDS = ["edit", "едіт", "едит"]
STOP_WORDS = ["стоп", "вистачить"]
ACTIVE_TIMEOUT = 300
last_activation_time = 0


def is_active():
    return time.time() - last_activation_time < ACTIVE_TIMEOUT


def main():
    global last_activation_time

    index_source, app_count = ensure_app_index()
    print(f"[index:{index_source}] loaded {app_count} app entries")

    while True:
        audio_data = listen()
        text = recognize(audio_data)

        if not text:
            print("Не вдалося розпізнати мову.")
            continue

        original_text = text
        normalized_text = normalize_text(text)
        text_lower = normalized_text.lower()
        print("Ти сказав:", original_text)

        if any(stop_word in text_lower for stop_word in STOP_WORDS):
            last_activation_time = 0
            speak("Окей, вимикаюсь")
            return

        direct_open_target = extract_open_target(text_lower)
        if direct_open_target:
            result = execute_action("open_app", {"app": direct_open_target})
            remember_app_launch(direct_open_target)
            speak(result)
            continue

        if any(wake_word in text_lower for wake_word in WAKE_WORDS):
            last_activation_time = time.time()
            for wake_word in WAKE_WORDS:
                text_lower = text_lower.replace(wake_word, "").strip()

            if not text_lower:
                speak("Так?")
                continue

        if not is_active():
            continue

        context = get_runtime_context()
        local_intent = resolve_local_intent(text_lower, context)
        if local_intent:
            result = execute_actions(local_intent.get("actions", []))
            remember_phrase_actions(text_lower, local_intent.get("actions", []))
            speak(local_intent.get("response") or result)
            continue

        ai_result = ask_ai(text_lower)
        result_type = ai_result.get("type")

        if result_type == "command":
            result = execute_action(ai_result.get("action"), ai_result)
            if ai_result.get("action") == "open_app" and ai_result.get("app"):
                remember_app_launch(ai_result["app"])
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
