import time

from brain.ai import ask_ai, ask_gpt_stream, compose_assistant_reply
from brain.commands import execute_action, execute_actions
from utils.app_finder import ensure_app_index
from utils.config import ACTIVE_LISTEN_DURATION, IDLE_LISTEN_DURATION
from utils.context import get_runtime_context
from utils.intent_parser import extract_open_target
from utils.intent_router import resolve_local_intent
from utils.memory import remember_app_launch, remember_phrase_actions
from utils.normalize import normalize_text
from voice.listen import get_chunk, listen, start_stream, stop_stream
from voice.recognize import process_chunk, recognize, reset_stream_buffer
from voice.speak import speak, speak_stream


WAKE_WORDS = ["edit", "edid", "edyt"]
STOP_WORDS = {"stop", "stoph", "stopp"}
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
        return "Something happened, but I could not explain it clearly."

    status = result.get("status")
    action = result.get("action")
    app_name = result.get("app", "")
    reason = result.get("reason")

    if status == "success":
        if action == "open_app" and app_name:
            return f"Opening {app_name}."
        if action == "open_github":
            return "Opening GitHub."
        if action == "open_google":
            return "Opening Google."
        if action == "open_youtube":
            return "Opening YouTube."
        if action == "open_code":
            return "Opening Visual Studio Code."
        if action == "open_notepad":
            return "Opening Notepad."
        if action == "open_explorer":
            return "Opening File Explorer."
        if action == "open_calculator":
            return "Opening Calculator."
        if action == "stop":
            return "Okay, shutting down."
        return "Done."

    if reason == "missing_app_name":
        return "Please уточни, which app I should open."
    if reason == "ambiguous_app" and app_name:
        return f"Please clarify what exactly you want under the name {app_name}."
    if reason == "app_not_found" and app_name:
        return f"I could not find the app {app_name}."
    if reason == "unknown_command":
        return "I do not know that command yet."
    if reason == "no_actions_to_execute":
        return "There are no actions to execute right now."

    return "Something went wrong, try again."


def _contains_stop_command(text):
    normalized = normalize_text(text).lower().strip()
    tokens = normalized.split()

    if any(token in STOP_WORDS for token in tokens):
        return True

    return normalized in {"stop stop", "stop-stop"}


def _contains_wake_word(text):
    normalized = normalize_text(text).lower()
    return any(wake_word in normalized for wake_word in WAKE_WORDS)


def _remove_wake_words(text):
    normalized = normalize_text(text).lower()
    for wake_word in WAKE_WORDS:
        normalized = normalized.replace(wake_word, " ")
    return " ".join(normalized.split())


def _speak_action_reply(user_text, result, context, status_callback, action_summary=None):
    response = compose_assistant_reply(
        user_text=user_text,
        action_result=result,
        context=context,
        action_summary=action_summary,
    )

    if not response:
        response = _action_result_to_fallback(result)

    speak(response)
    _emit(status_callback, "action", response)


def _handle_local_intent(local_intent, text_lower, context, status_callback):
    fallback_response = local_intent.get("response", "Doing it now.")

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
        action_result=result,
        context=context,
        action_summary=local_intent.get("actions", []),
    )
    if not response:
        response = fallback_response or _action_result_to_fallback(result)
    speak(response)
    _emit(status_callback, "action", response)


def run_streaming_preview(stop_event=None, quiet=False, status_callback=None):
    stream = start_stream()
    last_text = ""
    reset_stream_buffer()
    _emit(status_callback, "streaming", "Streaming preview active")

    try:
        while not (stop_event and stop_event.is_set()):
            chunk = get_chunk(timeout=0.5)
            text = process_chunk(chunk)

            if not text:
                continue

            normalized_text = normalize_text(text).lower()
            if normalized_text == last_text:
                continue

            last_text = normalized_text
            if not quiet:
                print("Partial:", text)

            if len(normalized_text) < 15:
                continue

            generator = ask_gpt_stream(text)
            speak_stream(generator)
            _emit(status_callback, "streaming", text)
    finally:
        stop_stream()


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
            _emit(status_callback, "listening", "Waiting for wake word")
            continue

        original_text = text
        text_lower = normalize_text(text).lower()

        if not quiet:
            print("You said:", original_text)
        _emit(status_callback, "heard", original_text)

        context = get_runtime_context()

        if _contains_stop_command(text_lower):
            last_activation_time = 0
            response = compose_assistant_reply(
                user_text=text_lower,
                action_result={"status": "success", "action": "stop"},
                context=context,
            )
            if not response:
                response = _action_result_to_fallback({"status": "success", "action": "stop"})
            speak(response)
            _emit(status_callback, "stopped", "Assistant stopped")
            return

        direct_open_target = extract_open_target(text_lower)
        if direct_open_target:
            direct_local_intent = resolve_local_intent(direct_open_target, context)
            if direct_local_intent:
                _handle_local_intent(direct_local_intent, direct_open_target, context, status_callback)
                continue

            result = execute_action("open_app", {"app": direct_open_target})
            if isinstance(result, dict) and result.get("status") == "success":
                remember_app_launch(direct_open_target)
            _speak_action_reply(
                user_text=text_lower,
                result=result,
                context=context,
                status_callback=status_callback,
                action_summary=[{"type": "open_app", "app": direct_open_target}],
            )
            continue

        if _contains_wake_word(text_lower):
            last_activation_time = time.time()
            text_lower = _remove_wake_words(text_lower)

            if not text_lower:
                speak("Yes?")
                _emit(status_callback, "active", "Activated and waiting")
                continue

        if not is_active():
            _emit(status_callback, "listening", "Background mode")
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

            _speak_action_reply(
                user_text=text_lower,
                result=result,
                context=context,
                status_callback=status_callback,
                action_summary=[ai_result],
            )
            continue

        if result_type == "chat":
            response = ai_result.get("response", "Something went wrong, try again.")
            speak(response)
            _emit(status_callback, "chat", response)
            continue

        response = "Something went wrong, try again."
        speak(response)
        _emit(status_callback, "chat", response)

    _emit(status_callback, "stopped", "Assistant stopped")


def main():
    try:
        run_assistant()
    except KeyboardInterrupt:
        print("\nAssistant stopped.")
    else:
        print("Assistant stopped.")


if __name__ == "__main__":
    main()
