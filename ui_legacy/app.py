import threading

from ui_legacy.service import AssistantService
from ui_legacy.startup import ensure_startup_entry
from ui_legacy.tray import run_tray
from ui_legacy.window import open_window
AUTO_INSTALL_STARTUP = False


SERVICE = AssistantService()


def main():
    if AUTO_INSTALL_STARTUP:
        try:
            ensure_startup_entry()
        except OSError as error:
            print(f"Startup install error: {error}")

    SERVICE.start()
    tray_thread = threading.Thread(target=run_tray, args=(SERVICE,), name="tray-thread")
    tray_thread.start()
    open_window(SERVICE)


if __name__ == "__main__":
    main()
