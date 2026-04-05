import queue
import threading
import time

from brain.ai import ask_ai, ask_gpt_stream, compose_assistant_reply
from brain.commands import execute_action, execute_actions
from utils.app_finder import ensure_app_index
from utils.context import get_runtime_context
from utils.intent_parser import extract_open_target
from utils.intent_router import resolve_local_intent
from utils.memory import remember_app_launch, remember_phrase_actions
from utils.normalize import normalize_text
from voice.listen import AudioStream
from voice.recognize import StreamingRecognizer, is_valid_text
from voice.speak import StreamingSpeechPlayer, speak
from brain.context_tracker import ContextTracker
from brain.scenario_manager import ScenarioManager

WAKE_WORDS = ("edit", "едіт", "едит")
STOP_WORDS = ("stop", "стоп", "вистачить")
YES_WORDS = ("так", "ага", "да", "yes", "угу")
COMMAND_PREFIXES = (
    "відкрий",
    "open",
    "запусти",
    "launch",
    "увімкни",
    "включи",
    "вимкни",
    "выключи",
    "закрий",
    "close",
)
INCOMPLETE_ENDINGS = ("якийсь", "якась", "якесь", "some", "який", "яку", "what")
ACTIVE_TIMEOUT = 90
NO_WORDS = ("ні", "не", "no", "не треба")


def _emit(status_callback, status, message=""):
    if status_callback:
        status_callback(status, message)


def _contains_wake_word(text):
    return any(word in text for word in WAKE_WORDS)


def _strip_wake_words(text):
    stripped = text
    for word in WAKE_WORDS:
        stripped = stripped.replace(word, " ")
    return " ".join(stripped.split())


def _contains_stop_command(text):
    tokens = set(text.split())
    return any(word in tokens for word in STOP_WORDS)


def _is_plain_wake_word(text):
    return text.strip() in WAKE_WORDS


def _is_yes_answer(text):
    return text.strip() in YES_WORDS


def _is_no_answer(text):
    return text.strip() in NO_WORDS


def _looks_incomplete(text):
    stripped = text.strip()
    if not stripped:
        return True
    if stripped.endswith(INCOMPLETE_ENDINGS):
        return True
    if len(stripped.split()) < 3:
        return True
    return False


def _action_result_to_fallback(result):
    if isinstance(result, str):
        return result

    if not isinstance(result, dict):
        return "Щось сталося, але я не можу це нормально пояснити."

    status = result.get("status")
    action = result.get("action")
    app_name = result.get("app", "")
    reason = result.get("reason")

    if status == "success":
        if action == "open_app" and app_name:
            return f"Відкриваю {app_name}."
        if action == "close_app" and app_name:
            return f"Закриваю {app_name}."
        if action == "stop":
            return "Добре, чекаю на тебе."
        return "Готово."

    if reason == "missing_app_name":
        return "Скажи, будь ласка, який саме додаток відкрити."
    if reason == "ambiguous_app" and app_name:
        return f"Уточни, будь ласка, що саме ти маєш на увазі під {app_name}."
    if reason == "launch_failed" and app_name:
        return f"Знайшов {app_name}, але не вдалося запустити. Спробуй ще раз."
    if reason == "app_not_found" and app_name:
        return f"Не вдалося знайти додаток {app_name}."
    return "Щось пішло не так, спробуй ще раз."


class AssistantRuntime:
    def __init__(self, stop_event=None, quiet=False, status_callback=None):
        self.stop_event = stop_event or threading.Event()
        self.quiet = quiet
        self.status_callback = status_callback
        self.audio_stream = AudioStream()
        self.recognizer = StreamingRecognizer()
        self.speech_player = StreamingSpeechPlayer()
        self.recognition_events = queue.Queue()
        self.gpt_requests = queue.Queue()
        self.recognition_thread = None
        self.gpt_thread = None
        self.gpt_running = False
        self.stop_generation = 0
        self.gpt_lock = threading.Lock()
        self.state = "SLEEP"
        self.last_active_time = 0.0
        self.last_question = None
        self.tracker = ContextTracker()
        self.tracker.start_tracking()
        self.scenario_manager = ScenarioManager()

    def activate(self):
        self.state = "ACTIVE"
        self.last_active_time = time.time()

    def sleep(self):
        self.state = "SLEEP"

    def _refresh_activity(self):
        self.last_active_time = time.time()

    def _check_timeout(self):
        if self.state == "ACTIVE" and (time.time() - self.last_active_time > ACTIVE_TIMEOUT):
            self.state = "SLEEP"
            _emit(self.status_callback, "sleep", "Асистент перейшов у режим очікування")

    def start(self):
        index_source, app_count = ensure_app_index()
        if not self.quiet:
            print(f"[index:{index_source}] loaded {app_count} app entries")
        _emit(self.status_callback, "running", f"Index: {app_count} apps")

        self.audio_stream.start()
        self.speech_player.start()

        self.recognition_thread = threading.Thread(
            target=self._recognition_loop,
            name="speech-recognition",
            daemon=True,
        )
        self.gpt_thread = threading.Thread(
            target=self._gpt_loop,
            name="gpt-stream",
            daemon=True,
        )

        self.recognition_thread.start()
        self.gpt_thread.start()

        try:
            self._event_loop()
        finally:
            self.stop()

    def stop(self):
        self.stop_event.set()
        try:
            self.audio_stream.stop()
        except Exception:
            pass
        try:
            self.speech_player.stop()
        except Exception:
            pass
        _emit(self.status_callback, "stopped", "Assistant stopped")

    def _recognition_loop(self):
        while not self.stop_event.is_set():
            chunk = self.audio_stream.read_chunk(timeout=0.1)
            if chunk is None:
                continue

            try:
                events = self.recognizer.process_chunk(chunk)
            except Exception as error:
                print(f"Recognition error: {error}")
                _emit(self.status_callback, "error", f"Recognition error: {error}")
                continue

            for event in events:
                self.recognition_events.put(event)

    def _gpt_loop(self):
        while not self.stop_event.is_set():
            try:
                request_item = self.gpt_requests.get(timeout=0.1)
            except queue.Empty:
                continue

            if request_item is None:
                continue

            prompt = request_item["text"]
            context = request_item["context"]
            generation_marker = request_item["generation"]

            with self.gpt_lock:
                self.gpt_running = True

            generation_id = self.speech_player.begin()
            try:
                for delta in ask_gpt_stream(prompt, context=context):
                    if self.stop_event.is_set() or generation_marker != self.stop_generation:
                        break
                    self.speech_player.push_text(generation_id, delta)
                self.speech_player.end(generation_id)
            except Exception as error:
                fallback = compose_assistant_reply(
                    user_text=prompt,
                    fallback_text=f"Щось пішло не так: {error}",
                    context=context,
                )
                self.speech_player.push_text(generation_id, fallback)
                self.speech_player.end(generation_id)
            finally:
                with self.gpt_lock:
                    self.gpt_running = False

    def _event_loop(self):
        while not self.stop_event.is_set():
            for process_name in self.tracker.detect_new_apps():
                app_name = self.tracker.to_app_name(process_name)
                prompt = self.scenario_manager.queue_app_offer(app_name, source="tracker")
                if prompt:
                    speak(prompt)
                    _emit(self.status_callback, "scenario", prompt)

            self._check_timeout()
            try:
                event = self.recognition_events.get(timeout=0.1)
            except queue.Empty:
                continue

            if event["type"] == "final":
                self._handle_final(event)

    def _handle_final(self, event):
        original_text = event["text"]
        text = normalize_text(original_text).lower().strip()
        if not is_valid_text(text):
            return

        if not self.quiet:
            print("You said:", original_text)
        _emit(self.status_callback, "heard", original_text)

        context = get_runtime_context()

        if _contains_stop_command(text):
            self.stop_generation += 1
            with self.gpt_lock:
                self.gpt_running = False
            self.sleep()
            speak("Добре, чекаю на тебе.")
            _emit(self.status_callback, "sleep", "Асистент у режимі очікування")
            return

        if _contains_wake_word(text):
            self.activate()
            if _is_plain_wake_word(text):
                speak("Привіт, я тут. Що будемо робити?")
                _emit(self.status_callback, "active", "Активований і чекає запит")
                return
            text = _strip_wake_words(text)
        elif self.state == "SLEEP":
            return

        if not text:
            return

        self._refresh_activity()

        if self.scenario_manager.has_pending_offer():
            if _is_yes_answer(text):
                confirmed = self.scenario_manager.confirm_pending()
                if confirmed:
                    scenario_name, app_name = confirmed
                    response = f"Добре, додала {app_name} в сценарій {scenario_name}."
                    speak(response)
                    _emit(self.status_callback, "scenario", response)
                return
            if _is_no_answer(text):
                self.scenario_manager.reject_pending()
                response = "Добре, не додаю."
                speak(response)
                _emit(self.status_callback, "scenario", response)
                return

        if _is_yes_answer(text) and self.last_question == "fact":
            speak("Ще один факт: восьминоги мають три серця.")
            self.last_question = None
            return

        direct_open_target = extract_open_target(text)
        if direct_open_target:
            self._handle_direct_open(text, direct_open_target, context)
            return

        local_intent = resolve_local_intent(text, context)
        if local_intent:
            self._handle_local_intent(text, local_intent, context)
            return

        ai_result = ask_ai(text, context=context)
        if ai_result.get("type") == "command":
            self._handle_ai_command(text, ai_result, context)
            return

        if self.gpt_running or _looks_incomplete(text):
            return

        if "факт" in text or "цікавий факт" in text:
            self.last_question = "fact"
        else:
            self.last_question = None

        self.gpt_requests.put(
            {
                "utterance_id": event["utterance_id"],
                "text": text,
                "context": context,
                "generation": self.stop_generation,
            }
        )

    def _handle_direct_open(self, user_text, app_name, context):
        direct_local_intent = resolve_local_intent(app_name, context)
        if direct_local_intent:
            self._handle_local_intent(app_name, direct_local_intent, context)
            return

        result = execute_action("open_app", {"app": app_name})
        if isinstance(result, dict) and result.get("status") == "success":
            remember_app_launch(app_name)
            prompt = self.scenario_manager.queue_app_offer(app_name, source="direct")
            if prompt:
                speak(prompt)
                _emit(self.status_callback, "scenario", prompt)
                return

        response = compose_assistant_reply(
            user_text=user_text,
            action_result=result,
            context=context,
            action_summary=[{"type": "open_app", "app": app_name}],
        ) or _action_result_to_fallback(result)
        speak(response)
        _emit(self.status_callback, "action", response)

    def _handle_local_intent(self, user_text, local_intent, context):
        if local_intent.get("type") == "chat":
            response = compose_assistant_reply(
                user_text=user_text,
                fallback_text=local_intent.get("response", "Добре."),
                context=context,
            )
            speak(response)
            _emit(self.status_callback, "chat", response)
            return

        actions = local_intent.get("actions", [])
        scenario_name = local_intent.get("scenario")
        if scenario_name:
            self.scenario_manager.activate(scenario_name)
            actions = self.scenario_manager.get_actions(scenario_name)

        result = execute_actions(actions)
        remember_phrase_actions(user_text, actions)
        response = compose_assistant_reply(
            user_text=user_text,
            action_result=result,
            context=context,
            action_summary=actions,
        ) or local_intent.get("response") or _action_result_to_fallback(result)
        speak(response)
        _emit(self.status_callback, "action", response)

    def _handle_ai_command(self, user_text, ai_result, context):
        result = execute_action(ai_result.get("action"), ai_result)
        if (
            ai_result.get("action") == "open_app"
            and ai_result.get("app")
            and isinstance(result, dict)
            and result.get("status") == "success"
        ):
            remember_app_launch(ai_result["app"])
            prompt = self.scenario_manager.queue_app_offer(ai_result["app"], source="ai")
            if prompt:
                speak(prompt)
                _emit(self.status_callback, "scenario", prompt)
                return

        response = compose_assistant_reply(
            user_text=user_text,
            action_result=result,
            context=context,
            action_summary=[ai_result],
        ) or _action_result_to_fallback(result)
        speak(response)
        _emit(self.status_callback, "action", response)


def run_assistant(stop_event=None, quiet=False, status_callback=None):
    runtime = AssistantRuntime(stop_event=stop_event, quiet=quiet, status_callback=status_callback)
    runtime.start()


def main():
    try:
        run_assistant()
    except KeyboardInterrupt:
        print("\nAssistant stopped.")
    else:
        print("Assistant stopped.")


if __name__ == "__main__":
    main()
