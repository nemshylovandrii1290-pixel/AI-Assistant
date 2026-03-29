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

    try:
        for proc in psutil.process_iter(["name"]):
            name = proc.info.get("name")
            if name and process_name.lower() == name.lower():
                proc.terminate()
                return True
    except Exception as error:
        print(f"[close:psutil] {error}")
    return False


def close_by_taskkill_image(app_name):
    process_name = app_name if app_name.lower().endswith(".exe") else f"{app_name}.exe"
    result = subprocess.run(
        ["taskkill", "/im", process_name],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def close_by_taskkill_force(app_name):
    process_name = app_name if app_name.lower().endswith(".exe") else f"{app_name}.exe"
    result = subprocess.run(
        ["taskkill", "/f", "/t", "/im", process_name],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def smart_close(app_name, path=None, aliases=None):
    if not app_name:
        return {"status": "error", "reason": "missing_app_name"}

    resolved_name = aliases.get(app_name, app_name) if aliases else app_name
    process_name = os.path.basename(path) if path else resolved_name

    if close_by_window(resolved_name):
        print(f"[close:window] closed '{resolved_name}'")
        return {
            "status": "success",
            "action": "close_app",
            "app": app_name,
            "resolved_app": resolved_name,
            "source": "window",
        }

    if close_by_psutil(process_name):
        print(f"[close:psutil] closed '{process_name}'")
        return {
            "status": "success",
            "action": "close_app",
            "app": app_name,
            "resolved_app": resolved_name,
            "source": "psutil",
        }

    if close_by_taskkill_image(process_name):
        print(f"[close:taskkill] closed '{process_name}'")
        return {
            "status": "success",
            "action": "close_app",
            "app": app_name,
            "resolved_app": resolved_name,
            "source": "taskkill",
        }

    if close_by_taskkill_force(process_name):
        print(f"[close:force] closed '{process_name}'")
        return {
            "status": "success",
            "action": "close_app",
            "app": app_name,
            "resolved_app": resolved_name,
            "source": "force",
        }

    print(f"[close:failback] app '{resolved_name}' not found")
    return {
        "status": "error",
        "reason": "app_not_found",
        "app": app_name,
        "resolved_app": resolved_name,
    }
