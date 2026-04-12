import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from backend.brain.ai import ask_gpt_text
from backend.utils.context import get_runtime_context
from backend.voice.speak import speak


API_HOST = os.getenv("BACKEND_API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("BACKEND_API_PORT", "8008"))


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

        if parsed.path == "/api/chat":
            self._handle_chat()
            return

        if parsed.path == "/api/voice":
            self._handle_voice()
            return

        self._send_json({"error": "Not found"}, status=404)

    def log_message(self, format, *args):
        return

    def _handle_chat(self):
        payload = self._read_json()
        if payload is None:
            self._send_json({"error": "Invalid JSON body"}, status=400)
            return

        message = (payload.get("message") or "").strip()
        if not message:
            self._send_json({"error": "Message is required"}, status=400)
            return

        speak_enabled = bool(payload.get("speak"))
        context = get_runtime_context()
        reply = ask_gpt_text(message, context=context) or "Я тут, але зараз не змогла сформувати відповідь."

        if speak_enabled:
            speak(reply)

        self._send_json(
            {
                "reply": reply,
                "context": {"mode": context.get("mode")},
            }
        )

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
        context = get_runtime_context()
        reply = ask_gpt_text(transcript, context=context) or "Я почула тебе, але зараз не змогла відповісти."

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
