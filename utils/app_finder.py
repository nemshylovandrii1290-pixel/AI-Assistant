import os
import subprocess

SEARCH_PATHS = [
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
    "C:\\Users"
]

APP_CACHE = {}
CACHE_READY = False

def build_cache():
    global CACHE_READY

    if CACHE_READY:
        return

    for base in SEARCH_PATHS:
        if not base or not os.path.exists(base):
            continue

        for root, dirs, files in os.walk(base):
            for file in files:
                if file.endswith(".exe"):
                    APP_CACHE[file.lower()] = os.path.join(root, file)

    CACHE_READY = True


def find_app(app_name):
    app_name = app_name.lower()

    build_cache()

    if app_name in APP_CACHE:
        return APP_CACHE[app_name]

    exe_name = app_name if app_name.endswith(".exe") else f"{app_name}.exe"

    if exe_name in APP_CACHE:
        return APP_CACHE[exe_name]

    try:
        where_result = subprocess.run(
            ["where", exe_name],
            capture_output=True,
            text=True,
            check=False
        )
        first_path = where_result.stdout.strip().splitlines()
        if first_path:
            return first_path[0]
    except OSError:
        pass

    for base in SEARCH_PATHS:
        if not base or not os.path.exists(base):
            continue

        for root, dirs, files in os.walk(base):
            for file in files:
                if file.endswith(".exe") and app_name in file.lower():
                    return os.path.join(root, file)

    for file_name, file_path in APP_CACHE.items():
        normalized_name = file_name.removesuffix(".exe")
        if app_name in normalized_name:
            return file_path

    return None
