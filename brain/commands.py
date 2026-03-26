import os
import shutil
import subprocess
import webbrowser

from utils.app_finder import find_app
from utils.commands_config import COMMANDS
from utils.normalize import normalize_text
from utils.special_launchers import try_special_case_launch


SPECIAL_APP_COMMANDS = {
    "github": "open_github",
    "google": "open_google",
    "youtube": "open_youtube",
}

AMBIGUOUS_APP_NAMES = {
    "adobe",
    "google",
    "microsoft",
    "office",
}


def _open_path(path):
    try:
        os.startfile(path)
        return True
    except OSError:
        if path.lower().endswith((".lnk", ".url")):
            explorer_result = subprocess.run(["explorer", path], check=False)
            if explorer_result.returncode == 0:
                return True

        powershell_result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", f'Start-Process -FilePath "{path}"'],
            check=False,
        )
        if powershell_result.returncode == 0:
            return True

        cmd_result = subprocess.run(["cmd", "/c", "start", "", path], check=False)
        return cmd_result.returncode == 0


def _log_stage(stage, message):
    print(f"[launch:{stage}] {message}")


def _try_system_launch(app_name):
    candidates = [app_name]
    if not app_name.endswith(".exe"):
        candidates.append(f"{app_name}.exe")

    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved and _open_path(resolved):
            _log_stage("system", f"resolved '{app_name}' via PATH: {resolved}")
            return True

    return False


def execute_action(action, data=None):
    command = COMMANDS.get(action)

    if action == "open_app":
        app_name = normalize_text((data or {}).get("app", ""))

        if not app_name:
            return {"status": "error", "reason": "missing_app_name"}

        redirected_action = SPECIAL_APP_COMMANDS.get(app_name)
        if redirected_action:
            return execute_action(redirected_action, data)

        if app_name in AMBIGUOUS_APP_NAMES:
            return {
                "status": "error",
                "reason": "ambiguous_app",
                "app": app_name,
                "source": "index"
            }

        path = find_app(app_name)
        if path and _open_path(path):
            _log_stage("index", f"resolved '{app_name}' via app index: {path}")
            return {"status": "success", "action": "open_app", "app": app_name, "source": "index"}

        if try_special_case_launch(app_name):
            _log_stage("special", f"resolved '{app_name}' via special launcher")
            return {"status": "success", "action": "open_app", "app": app_name, "source": "special"}

        if _try_system_launch(app_name):
            return {"status": "success", "action": "open_app", "app": app_name, "source": "system"}

        _log_stage("failback", f"app '{app_name}' not found")
        return {"status": "error", "reason": "app_not_found", "app": app_name}

    if not command:
        return {"status": "error", "reason": "unknown_command"}

    if command["kind"] == "url":
        webbrowser.open(command["target"])
        return {
            "status": "success",
            "action": action,
            "meta": data
        }

    if command["kind"] == "command":
        os.system(command["target"])
        return {
            "status": "success",
            "action": action,
            "meta": data
        }

    return {"status": "error", "reason": "unknown_command"}


def execute_actions(actions):
    if not actions:
        return {"status": "error", "reason": "no_actions_to_execute"}

    responses = []

    for action in actions:
        action_type = action.get("type")

        if action_type == "open_app":
            responses.append(execute_action("open_app", {"app": action.get("app", "")}))
            continue

        if action_type == "command":
            responses.append(execute_action(action.get("action"), action))
            continue

    successful_responses = [
        response for response in responses
        if isinstance(response, dict) and response.get("status") == "success"
    ]
    if successful_responses:
        return successful_responses[-1]

    if responses:
        return responses[-1]

    return {"status": "error", "reason": "app_not_found", "app": actions[-1].get("app", "")}
