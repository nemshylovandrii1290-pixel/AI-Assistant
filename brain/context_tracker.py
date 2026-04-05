import psutil

from utils.normalize import normalize_text


IGNORE_PROCESSES = {
    "audiodg.exe",
    "backgroundtaskhost.exe",
    "cmd.exe",
    "conhost.exe",
    "dllhost.exe",
    "git.exe",
    "mousocoreworker.exe",
    "oawrapper.exe",
    "python.exe",
    "pythonw.exe",
    "searchhost.exe",
    "searchprotocolhost.exe",
    "shellexperiencehost.exe",
    "startmenuexperiencehost.exe",
    "updater.exe",
    "wermgr.exe",
    "widgets.exe",
}


PROCESS_NAME_ALIASES = {
    "chatgpt.exe": "chatgpt",
    "chrome.exe": "google chrome",
    "code.exe": "visual studio code",
    "discord.exe": "discord",
    "githubdesktop.exe": "github desktop",
    "msedge.exe": "microsoft edge",
    "notepad.exe": "notepad",
    "obs64.exe": "obs studio",
    "outlook.exe": "microsoft outlook",
    "steam.exe": "steam",
    "telegram.exe": "telegram",
}


class ContextTracker:
    def __init__(self):
        self.baseline_apps = set()

    def get_current_apps(self):
        apps = set()

        for proc in psutil.process_iter(["name"]):
            try:
                name = (proc.info.get("name") or "").lower().strip()
                if not name or name in IGNORE_PROCESSES:
                    continue
                apps.add(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return apps

    def start_tracking(self):
        self.baseline_apps = self.get_current_apps()

    def detect_new_apps(self):
        current_apps = self.get_current_apps()
        new_apps = current_apps - self.baseline_apps
        self.baseline_apps = current_apps
        return sorted(new_apps)

    def to_app_name(self, process_name):
        normalized = (process_name or "").lower().strip()
        if normalized in PROCESS_NAME_ALIASES:
            return PROCESS_NAME_ALIASES[normalized]
        if normalized.endswith(".exe"):
            normalized = normalized[:-4]
        return normalize_text(normalized)
