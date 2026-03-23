import json
import os
import shutil
import subprocess
import webbrowser

from utils.commands_config import COMMANDS
from utils.app_finder import find_app
from utils.normalize import normalize_text


def _open_path(path):
    try:
        os.startfile(path)
        return True
    except OSError:
        result = subprocess.run(
            ["cmd", "/c", "start", "", path],
            check=False
        )
        return result.returncode == 0


def _try_system_launch(app_name):
    candidates = [app_name]

    if not app_name.endswith(".exe"):
        candidates.append(f"{app_name}.exe")

    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved and _open_path(resolved):
            return True

    return False


def _find_start_app_id(app_name):
    script = f"""
    $query = "{app_name.replace('"', '`"')}"
    $apps = Get-StartApps | Where-Object {{ $_.Name -like "*$query*" }}
    $apps | Select-Object Name, AppID | ConvertTo-Json -Compress
    """

    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        check=False
    )

    if result.returncode != 0 or not result.stdout.strip():
        return None

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    if isinstance(data, list):
        if not data:
            return None
        return data[0].get("AppID")

    return data.get("AppID")


def _try_special_case_launch(app_name):
    start_app_id = _find_start_app_id(app_name)
    if start_app_id:
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f'Start-Process "shell:AppsFolder\\{start_app_id}"'
            ],
            check=False
        )
        return True

    if app_name in ["youtube", "ютуб"]:
        webbrowser.open("https://youtube.com")
        return True

    if app_name in ["instagram", "інстаграм"]:
        webbrowser.open("https://instagram.com")
        return True

    return False


def execute_action(action, data=None):
    command = COMMANDS.get(action)

    if action == "open_app":
        app_name = normalize_text((data or {}).get("app", ""))

        if not app_name:
            return "Не зрозумів, який саме додаток потрібно відкрити."

        # 1. System
        if _try_system_launch(app_name):
            return f"Відкриваю {app_name}"

        # 2. Index
        path = find_app(app_name)
        if path and _open_path(path):
            return f"Відкриваю {app_name}"

        # 3. Special cases
        if _try_special_case_launch(app_name):
            return f"Відкриваю {app_name}"

        # 4. Failback
        return f"Не вдалося знайти додаток {app_name}"

    if not command:
        return "Не знаю такої команди"

    if command["kind"] == "url":
        webbrowser.open(command["target"])
        return command["response"]

    if command["kind"] == "command":
        os.system(command["target"])
        return command["response"]

    return "Не знаю, як виконати цю команду"
