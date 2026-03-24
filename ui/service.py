import threading

from main import run_assistant


class AssistantService:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self.status = "idle"
        self.message = "Асистент ще не запущений"

    def _set_status(self, status, message=""):
        with self._lock:
            self.status = status
            self.message = message

    def status_callback(self, status, message=""):
        self._set_status(status, message)

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.is_running():
            return False

        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=run_assistant,
            kwargs={
                "stop_event": self._stop_event,
                "quiet": True,
                "status_callback": self.status_callback,
            },
            name="assistant-loop",
            daemon=True,
        )
        self._thread.start()
        self._set_status("running", "Асистент працює у tray")
        return True

    def stop(self):
        if not self.is_running():
            self._set_status("stopped", "Асистент зупинений")
            return False

        self._stop_event.set()
        self._thread.join(timeout=2.5)
        self._set_status("stopped", "Асистент зупинений")
        return True

    def snapshot(self):
        with self._lock:
            return {
                "status": self.status,
                "message": self.message,
                "running": self.is_running(),
            }
