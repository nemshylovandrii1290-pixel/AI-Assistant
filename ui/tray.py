import os
import sys
import threading

from PIL import Image, ImageDraw

from ui.window import open_window


def _build_icon_image():
    image = Image.new("RGB", (64, 64), color="#111827")
    draw = ImageDraw.Draw(image)
    draw.ellipse((10, 10, 54, 54), fill="#22c55e")
    draw.ellipse((22, 22, 42, 42), fill="#111827")
    return image


def _open_window_thread(service):
    threading.Thread(
        target=open_window,
        args=(service,),
        name="assistant-window",
        daemon=True,
    ).start()


def _toggle_service(icon, service):
    if service.is_running():
        service.stop()
    else:
        service.start()
    icon.update_menu()


def _exit_app(icon, item, service):
    service.stop()
    icon.stop()
    os._exit(0)


def run_tray(service):
    try:
        import pystray
    except ImportError as error:
        raise RuntimeError(
            f"pystray is not installed for this Python: {sys.executable}. "
            "Install dependencies in the active environment to use tray mode."
        ) from error

    menu = pystray.Menu(
        pystray.MenuItem("Показати", lambda icon, item: _open_window_thread(service)),
        pystray.MenuItem(
            lambda item: "Стоп" if service.is_running() else "Старт",
            lambda icon, item: _toggle_service(icon, service),
        ),
        pystray.MenuItem("Вийти", lambda icon, item: _exit_app(icon, item, service)),
    )

    icon = pystray.Icon("assistant", _build_icon_image(), "AI Assistant", menu)
    icon.run()
