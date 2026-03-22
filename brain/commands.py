import os
import re
import subprocess
import webbrowser

from utils.commands_config import COMMANDS
from utils.app_finder import find_app

def execute_action(action, data=None):
    command = COMMANDS.get(action)

    if action == "open_app":
        app_name = (data or {}).get("app")

        if not app_name:
            return "Не зрозумів, який саме додаток потрібно відкрити."

        path = find_app(app_name)

        if path:
            os.startfile(path)
            return f"Відкриваю {app_name}"

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
