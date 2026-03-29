import subprocess
import os

try:
    import psutil
except ImportError:
    psutil = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None


def _normalize_process_name(name):
    if not name:
        return ""
    lowered = name.lower().strip()
    if lowered.endswith(".exe"):
        lowered = lowered[:-4]
    return lowered


def close_by_window(app_name):
    if gw is None:
        return False

    try:
        windows = gw.getWindowsWithTitle(app_name)
        for window in windows:
            if window.title:
                window.close()
                return True
    except Exception as error:
        print(f"[close:window] {error}")
    return False


def close_by_psutil(process_name):
    if psutil is None:
        return False

    targets = process_name if isinstance(process_name, list) else [process_name]

    try:
        for proc in psutil.process_iter(["name"]):
            name = proc.info.get("name")
            if not name:
                continue
            for target in targets:
                if _normalize_process_name(name) == _normalize_process_name(target):
                    try:
                        proc.terminate()
                        return True
                    except Exception as error:
                        print(f"[close:psutil] {error}")
    except Exception as error:
        print(f"[close:psutil] {error}")
    return False


def close_by_taskkill_image(app_name):
    targets = app_name if isinstance(app_name, list) else [app_name]
    for target in targets:
        process_name = target if target.lower().endswith(".exe") else f"{target}.exe"
        result = subprocess.run(
            ["taskkill", "/im", process_name],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return True
    return False


def close_by_taskkill_force(app_name):
    targets = app_name if isinstance(app_name, list) else [app_name]
    for target in targets:
        process_name = target if target.lower().endswith(".exe") else f"{target}.exe"
        result = subprocess.run(
            ["taskkill", "/f", "/t", "/im", process_name],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return True
    return False


def smart_close(app_name, path=None, aliases=None):
    if not app_name:
        return {"status": "error", "reason": "missing_app_name"}

    resolved_name = aliases.get(app_name, app_name) if aliases else app_name
    process_name = os.path.basename(path) if path else resolved_name

    if isinstance(resolved_name, list):
        process_names = resolved_name
    else:
        process_names = [resolved_name]

    if path and process_name not in process_names:
        process_names = [process_name, *process_names]

    if close_by_window(app_name):
        print(f"[close:window] closed '{resolved_name}'")
        return {
            "status": "success",
            "action": "close_app",
            "app": app_name,
            "resolved_app": resolved_name,
            "source": "window",
        }

    if close_by_psutil(process_names):
        print(f"[close:psutil] closed '{process_name}'")
        return {
            "status": "success",
            "action": "close_app",
            "app": app_name,
            "resolved_app": resolved_name,
            "source": "psutil",
        }

    if close_by_taskkill_image(process_names):
        print(f"[close:taskkill] closed '{process_name}'")
        return {
            "status": "success",
            "action": "close_app",
            "app": app_name,
            "resolved_app": resolved_name,
            "source": "taskkill",
        }

    if close_by_taskkill_force(process_names):
        print(f"[close:force] closed '{process_name}'")
        return {
            "status": "success",
            "action": "close_app",
            "app": app_name,
            "resolved_app": resolved_name,
            "source": "force",
        }

    print(f"[close:failback] app '{app_name}' not found")
    return {
        "status": "error",
        "reason": "app_not_found",
        "app": app_name,
        "resolved_app": resolved_name,
    }
