import os
import webbrowser

def execute_action(action):
    if action == "open_google":
        webbrowser.open("https://www.google.com")
        return "Відкриваю Google"

    if action == "open_explorer":
        os.system("explorer")
        return "Відкриваю провідник"

    if action == "open_code":
        os.system("code")
        return "Відкриваю VS Code"

    return "Не знаю такої команди"
