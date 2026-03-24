import os
import sys


STARTUP_DIR = os.path.join(
    os.environ.get("APPDATA", ""),
    "Microsoft",
    "Windows",
    "Start Menu",
    "Programs",
    "Startup",
)
STARTUP_FILE = os.path.join(STARTUP_DIR, "AI Assistant Tray.vbs")
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _pythonw_path():
    executable = sys.executable
    directory = os.path.dirname(executable)
    pythonw = os.path.join(directory, "pythonw.exe")
    return pythonw if os.path.exists(pythonw) else executable


def ensure_startup_entry():
    if not STARTUP_DIR:
        return None

    os.makedirs(STARTUP_DIR, exist_ok=True)
    pythonw_path = _pythonw_path()
    repo_root = REPO_ROOT.replace("\\", "\\\\")
    pythonw_path = pythonw_path.replace("\\", "\\\\")

    script = (
        'Set WshShell = CreateObject("WScript.Shell")\n'
        f'WshShell.CurrentDirectory = "{repo_root}"\n'
        f'WshShell.Run chr(34) & "{pythonw_path}" & chr(34) & " -m ui.app", 0\n'
    )

    with open(STARTUP_FILE, "w", encoding="utf-8") as startup_file:
        startup_file.write(script)

    return STARTUP_FILE
