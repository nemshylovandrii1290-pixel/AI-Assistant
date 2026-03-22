import os
import webbrowser

from utils.commands_config import COMMANDS


def execute_action(action):
    command = COMMANDS.get(action)

    if not command:
        return "Не знаю такої команди"

    if command["kind"] == "url":
        webbrowser.open(command["target"])
        return command["response"]

    if command["kind"] == "command":
        os.system(command["target"])
        return command["response"]

    return "Не знаю, як виконати цю команду"
