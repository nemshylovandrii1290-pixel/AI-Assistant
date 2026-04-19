import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from backend.brain.ai import ask_ai, ask_gpt_text, compose_assistant_reply
from backend.brain.commands import execute_action, execute_actions
from backend.utils.context import get_runtime_context
from backend.utils.intent_parser import extract_open_target
from backend.utils.intent_router import resolve_local_intent
from backend.utils.memory import remember_app_launch, remember_phrase_actions
from backend.utils.normalize import normalize_text
from backend.voice.speak import speak


API_HOST = os.getenv("BACKEND_API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("BACKEND_API_PORT", "8008"))
WAKE_WORDS = {"edit", "едіт", "едит"}


def _action_result_to_fallback(result):
    if isinstance(result, str):
        return result

    if not isinstance(result, dict):
        return "Щось сталося, але я не можу нормально це пояснити."

    status = result.get("status")
    action = result.get("action")
    app_name = result.get("app", "")
    reason = result.get("reason")

    if status == "success":
        if action == "open_app" and app_name:
            return f"Відкриваю {app_name}."
        if action == "close_app" and app_name:
            return f"Закриваю {app_name}."
        return "Готово."

    if reason == "missing_app_name":
        return "Скажи, будь ласка, який саме додаток відкрити."
    if reason == "ambiguous_app" and app_name:
        return f"Уточни, будь ласка, що саме ти маєш на увазі під {app_name}."
    if reason == "launch_failed" and app_name:
        return f"Знайшла {app_name}, але не вдалося запустити."
    if reason == "app_not_found" and app_name:
        return f"Не вдалося знайти додаток {app_name}."
    return "Щось пішло не так, спробуй ще раз."


def _run_voice_request(transcript):
    context = get_runtime_context()
    normalized_text = normalize_text(transcript).lower().strip()

    if not normalized_text:
        return "Я не розчула команду.", context

    if normalized_text in WAKE_WORDS:
        return "Привіт, я тут. Що будемо робити?", context

    direct_open_target = extract_open_target(normalized_text)
    if direct_open_target:
        result = execute_action("open_app", {"app": direct_open_target})
        if isinstance(result, dict) and result.get("status") == "success":
            remember_app_launch(direct_open_target)

        reply = _action_result_to_fallback(result)
        return reply, context

    local_intent = resolve_local_intent(normalized_text, context)
    if local_intent:
        if local_intent.get("type") == "chat":
            reply = compose_assistant_reply(
                user_text=normalized_text,
                fallback_text=local_intent.get("response", "Добре."),
                context=context,
            ) or local_intent.get("response", "Добре.")
            return reply, context

        actions = local_intent.get("actions", [])
        result = execute_actions(actions)
        remember_phrase_actions(normalized_text, actions)
        reply = local_intent.get("response") or _action_result_to_fallback(result)
        return reply, context

    ai_result = ask_ai(normalized_text, context=context)
    if ai_result.get("type") == "command":
        result = execute_action(ai_result.get("action"), ai_result)
        if (
            ai_result.get("action") == "open_app"
            and ai_result.get("app")
            and isinstance(result, dict)
            and result.get("status") == "success"
        ):
            remember_app_launch(ai_result["app"])

        reply = _action_result_to_fallback(result)
        return reply, context

    reply = ai_result.get("response") or ask_gpt_text(normalized_text, context=context) or "Я почула тебе, але зараз не змогла відповісти."
    return reply, context


class AssistantApiHandler(BaseHTTPRequestHandler):
    server_version = "EdithApi/1.0"

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/health":
            self._send_json({"ok": True, "service": "edith-backend-api"})
            return

        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/voice":
            self._handle_voice()
            return

        self._send_json({"error": "Not found"}, status=404)

    def log_message(self, format, *args):
        return

    def _handle_voice(self):
        payload = self._read_json()
        if payload is None:
            self._send_json({"error": "Invalid JSON body"}, status=400)
            return

        transcript = (payload.get("transcript") or "").strip()
        if not transcript:
            self._send_json({"error": "Transcript is required"}, status=400)
            return

        speak_enabled = bool(payload.get("speak"))
        reply, context = _run_voice_request(transcript)

        if speak_enabled:
            speak(reply)

        self._send_json(
            {
                "reply": reply,
                "transcript": transcript,
                "context": {"mode": context.get("mode")},
            }
        )

    def _read_json(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None

        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return None

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def run_api_server(host=API_HOST, port=API_PORT):
    server = ThreadingHTTPServer((host, port), AssistantApiHandler)
    print(f"Edith backend API running at http://{host}:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
