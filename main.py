import time

from brain.ai import ask_ai, compose_assistant_reply
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
ACTIVE_TIMEOUT = 300
last_activation_time = 0


def is_active():
    return time.time() - last_activation_time < ACTIVE_TIMEOUT


def _emit(status_callback, status, message=""):
    if status_callback:
        status_callback(status, message)


def _action_result_to_fallback(result):
    if isinstance(result, str):
        return result

    if not isinstance(result, dict):
        return "Щось сталося, але я не зміг нормально це пояснити."

    status = result.get("status")
    action = result.get("action")
    app_name = result.get("app", "")
    reason = result.get("reason")

    if status == "success":
        if action == "open_app" and app_name:
            return f"Відкриваю {app_name}."
        if action == "open_github":
            return "Відкриваю GitHub."
        if action == "open_google":
            return "Відкриваю Google."
        if action == "open_youtube":
            return "Відкриваю YouTube."
        if action == "open_code":
            return "Відкриваю Visual Studio Code."
        if action == "open_notepad":
            return "Відкриваю Блокнот."
        if action == "open_explorer":
            return "Відкриваю Провідник."
        if action == "open_calculator":
            return "Відкриваю Калькулятор."
        return "Готово."

    if reason == "missing_app_name":
        return "Уточни, будь ласка, який саме додаток потрібно відкрити."
    if reason == "ambiguous_app" and app_name:
        return f"Уточни, будь ласка, що саме ти хочеш відкрити під назвою {app_name}."
    if reason == "app_not_found" and app_name:
        return f"Не вдалося знайти додаток {app_name}."
    if reason == "unknown_command":
        return "Я поки не знаю такої команди."
    if reason == "no_actions_to_execute":
        return "Наразі немає дій для виконання."

    return "Щось пішло не так, спробуй ще раз."


def _contains_stop_command(text):
    normalized = normalize_text(text).lower().strip()
    tokens = normalized.split()

    if "стоп" in tokens or "вистачить" in tokens or "stop" in tokens:
        return True

    return normalized in {"stop stop", "стоп стоп"}


def _speak_action_reply(user_text, fallback_text, context, status_callback, action_summary=None):
    response = compose_assistant_reply(
        user_text=user_text,
        fallback_text=fallback_text,
        context=context,
        action_summary=action_summary,
    )
    speak(response)
    _emit(status_callback, "action", response)


def _handle_local_intent(local_intent, text_lower, context, status_callback):
    fallback_response = local_intent.get("response", "Зараз зроблю.")

    if local_intent.get("type") == "chat":
        response = compose_assistant_reply(
            user_text=text_lower,
            fallback_text=fallback_response,
            context=context,
        )
        speak(response)
        _emit(status_callback, "chat", response)
        return

    result = execute_actions(local_intent.get("actions", []))
    remember_phrase_actions(text_lower, local_intent.get("actions", []))
    response = compose_assistant_reply(
        user_text=text_lower,
        fallback_text=fallback_response or _action_result_to_fallback(result),
        context=context,
        action_summary=local_intent.get("actions", []),
    )
    speak(response)
    _emit(status_callback, "action", response)


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

        try:
            text = recognize(audio_data)
        except Exception as error:
            print(f"Recognition error: {error}")
            _emit(status_callback, "error", f"Recognition error: {error}")
            continue

        if not text:
            _emit(status_callback, "listening", "Очікую активаційну команду")
            continue

        original_text = text
        text_lower = normalize_text(text).lower()

        if not quiet:
            print("Ти сказав:", original_text)
        _emit(status_callback, "heard", original_text)

        if _contains_stop_command(text_lower):
            last_activation_time = 0
            speak("Окей, вимикаюсь")
            _emit(status_callback, "stopped", "Асистент зупинений")
            return

        context = get_runtime_context()

        direct_open_target = extract_open_target(text_lower)
        if direct_open_target:
            direct_local_intent = resolve_local_intent(direct_open_target, context)
            if direct_local_intent:
                _handle_local_intent(direct_local_intent, direct_open_target, context, status_callback)
                continue

            result = execute_action("open_app", {"app": direct_open_target})
            remember_app_launch(direct_open_target)
            _speak_action_reply(
                user_text=text_lower,
                fallback_text=_action_result_to_fallback(result),
                context=context,
                status_callback=status_callback,
                action_summary=[{"type": "open_app", "app": direct_open_target}],
            )
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

        local_intent = resolve_local_intent(text_lower, context)
        if local_intent:
            _handle_local_intent(local_intent, text_lower, context, status_callback)
            continue

        ai_result = ask_ai(text_lower, context=context)
        result_type = ai_result.get("type")

        if result_type == "command":
            result = execute_action(ai_result.get("action"), ai_result)
            if (
                ai_result.get("action") == "open_app"
                and ai_result.get("app")
                and isinstance(result, dict)
                and result.get("status") == "success"
            ):
                remember_app_launch(ai_result["app"])

            fallback_response = ai_result.get("response") or _action_result_to_fallback(result)
            _speak_action_reply(
                user_text=text_lower,
                fallback_text=fallback_response,
                context=context,
                status_callback=status_callback,
                action_summary=[ai_result],
            )
            continue

        if result_type == "chat":
            response = ai_result.get("response", "Щось не склалося, спробуй ще раз.")
            speak(response)
            _emit(status_callback, "chat", response)
            continue

        response = "Щось не склалося, спробуй ще раз."
        speak(response)
        _emit(status_callback, "chat", response)

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
