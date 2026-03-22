import os
import webbrowser

def handle_command(text):
    if not text:
        return None

    text = text.lower()

    # 🌐 Відкрити Google
    if "гугл" in text or "google" in text:
        webbrowser.open("https://www.google.com")
        return "Відкриваю Google."

    # 💻 Відкрити VS Code
    if "code" in text or "visual studio code" in text:
        os.system("code")
        return "Відкриваю VS Code"

    # 📁 Відкрити папку
    if "провідник" in text or "explorer" in text:
        os.system("explorer")
        return "Відкриваю провідник"

    return None
