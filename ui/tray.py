import os
import threading

from PIL import Image, ImageDraw

from ui.window import open_window


def _build_icon_image():
    image = Image.new("RGB", (64, 64), color="#111827")
    draw = ImageDraw.Draw(image)
    draw.ellipse((10, 10, 54, 54), fill="#22c55e")
    draw.ellipse((22, 22, 42, 42), fill="#111827")
    return image


def open_window_thread():
    threading.Thread(target=open_window, name="assistant-window", daemon=True).start()


def exit_app(icon, item):
    icon.stop()
    os._exit(0)


def run_tray():
    try:
        import pystray
    except ImportError as error:
        raise RuntimeError(
            "pystray is not installed. Install dependencies from requirements.txt to use tray mode."
        ) from error

    menu = pystray.Menu(
        pystray.MenuItem("Відкрити", lambda icon, item: open_window_thread()),
        pystray.MenuItem("Вийти", exit_app),
    )

    icon = pystray.Icon("assistant", _build_icon_image(), "AI Assistant", menu)
    icon.run()
