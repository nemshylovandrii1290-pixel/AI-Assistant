from datetime import datetime

import psutil


GAMING_PROCESSES = {
    "steam.exe",
    "discord.exe",
    "genshinimpact.exe",
    "hoyoplaylauncher.exe",
    "starrail.exe",
    "zenlesszonezero.exe",
}

WORK_PROCESSES = {
    "chrome.exe",
    "msedge.exe",
    "code.exe",
    "pycharm64.exe",
    "webstorm64.exe",
    "rider64.exe",
    "sublime_text.exe",
    "notepad.exe",
}


def _list_open_processes():
    processes = []
    for proc in psutil.process_iter(["name"]):
        try:
            name = (proc.info.get("name") or "").strip().lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

        if name:
            processes.append(name)

    return processes


def _detect_mode(processes):
    process_set = set(processes)

    if process_set & GAMING_PROCESSES:
        return "gaming"

    if process_set & WORK_PROCESSES:
        return "work"

    return "default"


def get_runtime_context():
    now = datetime.now()
    processes = _list_open_processes()

    if 5 <= now.hour < 12:
        time_of_day = "morning"
    elif 12 <= now.hour < 18:
        time_of_day = "day"
    elif 18 <= now.hour < 23:
        time_of_day = "evening"
    else:
        time_of_day = "night"

    return {
        "hour": now.hour,
        "time_of_day": time_of_day,
        "open_processes": processes,
        "mode": _detect_mode(processes),
    }
