from ui.service import AssistantService
from ui.startup import ensure_startup_entry
from ui.tray import run_tray
from utils.config import AUTO_INSTALL_STARTUP


SERVICE = AssistantService()


def main():
    if AUTO_INSTALL_STARTUP:
        try:
            ensure_startup_entry()
        except OSError as error:
            print(f"Startup install error: {error}")

    SERVICE.start()
    run_tray(SERVICE)


if __name__ == "__main__":
    main()
