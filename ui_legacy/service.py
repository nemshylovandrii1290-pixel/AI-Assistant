import threading


class AssistantService:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self.status = "legacy"
        self.message = "Legacy UI відключений від backend"

    def _set_status(self, status, message=""):
        with self._lock:
            self.status = status
            self.message = message

    def status_callback(self, status, message=""):
        self._set_status(status, message)

    def is_running(self):
        return False

    def start(self):
        self._set_status("legacy", "Legacy UI відключений від backend")
        return False

    def stop(self):
        self._set_status("legacy", "Legacy UI відключений від backend")
        return False

    def snapshot(self):
        with self._lock:
            return {
                "status": self.status,
                "message": self.message,
                "running": False,
            }
