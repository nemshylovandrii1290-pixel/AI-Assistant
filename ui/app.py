import threading

from main import main as run_assistant
from ui.tray import run_tray


def start_assistant_loop():
    worker = threading.Thread(target=run_assistant, name="assistant-loop", daemon=True)
    worker.start()
    return worker


def main():
    start_assistant_loop()
    run_tray()


if __name__ == "__main__":
    main()
