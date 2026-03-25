import time

from brain.ai import ask_ai
from brain.commands import execute_action, execute_actions
from utils.app_finder import ensure_app_index
from utils.config import ACTIVE_LISTEN_DURATION, IDLE_LISTEN_DURATION
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


def _emit(status_callback, status, message=""):
    if status_callback:
        status_callback(status, message)


def run_assistant(stop_event=None, quiet=False, status_callback=None):
    global last_activation_time

    index_source, app_count = ensure_app_index()
    if not quiet:
        print(f"[index:{index_source}] loaded {app_count} app entries")
    _emit(status_callback, "running", f"Index: {app_count} apps")

    while not (stop_event and stop_event.is_set()):
        listen_duration = ACTIVE_LISTEN_DURATION if is_active() else IDLE_LISTEN_DURATION
        audio_data = listen(duration=listen_duration, stop_event=stop_event, quiet=quiet)

        if stop_event and stop_event.is_set():
            break

        text = recognize(audio_data)
        if not text:
            _emit(status_callback, "listening", "Очікую активаційну команду")
            continue

        original_text = text
        text_lower = normalize_text(text).lower()

        if not quiet:
            print("Ти сказав:", original_text)
        _emit(status_callback, "heard", original_text)

        if any(stop_word in text_lower for stop_word in STOP_WORDS):
            last_activation_time = 0
            speak("Окей, вимикаюсь")
            _emit(status_callback, "stopped", "Асистент зупинений")
            return

        direct_open_target = extract_open_target(text_lower)
        if direct_open_target:
            result = execute_action("open_app", {"app": direct_open_target})
            remember_app_launch(direct_open_target)
            speak(result)
            _emit(status_callback, "action", result)
            continue

        if any(wake_word in text_lower for wake_word in WAKE_WORDS):
            last_activation_time = time.time()
            for wake_word in WAKE_WORDS:
                text_lower = text_lower.replace(wake_word, "").strip()

            if not text_lower:
                speak("Так?")
                _emit(status_callback, "active", "Активований і чекає запит")
                continue

        if not is_active():
            _emit(status_callback, "listening", "Працює у фоновому режимі")
            continue

        context = get_runtime_context()
        local_intent = resolve_local_intent(text_lower, context)
        if local_intent:
            if local_intent.get("type") == "chat":
                response = local_intent.get("response", "Не зрозумів запит.")
                speak(response)
                _emit(status_callback, "chat", response)
                continue

            result = execute_actions(local_intent.get("actions", []))
            remember_phrase_actions(text_lower, local_intent.get("actions", []))
            speak(local_intent.get("response") or result)
            _emit(status_callback, "action", local_intent.get("response") or result)
            continue

        ai_result = ask_ai(text_lower)
        result_type = ai_result.get("type")

        if result_type == "command":
            result = execute_action(ai_result.get("action"), ai_result)
            if ai_result.get("action") == "open_app" and ai_result.get("app"):
                remember_app_launch(ai_result["app"])
            speak(result)
            _emit(status_callback, "action", result)
            continue

        if result_type == "chat":
            response = ai_result.get("response", "Не зрозумів запит.")
            speak(response)
            _emit(status_callback, "chat", response)
            continue

        speak("Не зрозумів запит.")
        _emit(status_callback, "chat", "Не зрозумів запит.")

    _emit(status_callback, "stopped", "Асистент зупинений")


def main():
    try:
        run_assistant()
    except KeyboardInterrupt:
        print("\nАсистент зупинений.")
    else:
        print("Асистент зупинений.")


if __name__ == "__main__":
    main()
