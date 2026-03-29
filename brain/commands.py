import json
import os
import shutil
import subprocess
import webbrowser

from system.closer import smart_close
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

CLOSE_PREFIXES = (
    "закрий",
    "закрити",
    "close",
    "kill",
    "вимкни",
    "выключи",
)

_ALIASES = None


def _load_aliases():
    global _ALIASES
    if _ALIASES is not None:
        return _ALIASES

    aliases_path = os.path.join("config", "aliases.json")
    if not os.path.exists(aliases_path):
        _ALIASES = {}
        return _ALIASES

    try:
        with open(aliases_path, "r", encoding="utf-8") as file:
            _ALIASES = json.load(file)
    except (OSError, json.JSONDecodeError):
        _ALIASES = {}

    return _ALIASES


def _extract_close_target(text):
    normalized = normalize_text(text)
    for prefix in CLOSE_PREFIXES:
        if normalized.startswith(f"{prefix} "):
            return normalized[len(prefix):].strip()
    return normalized.strip()


def handle_close(text, context=None):
    original_app_name = normalize_text(_extract_close_target(text))
    aliases = (context or {}).get("aliases") or _load_aliases()
    path = find_app(original_app_name)
    return smart_close(original_app_name, path=path, aliases=aliases)


def _open_path(path):
    try:
        os.startfile(path)
        return True
    except OSError:
        if path.lower().endswith((".lnk", ".url")):
            explorer_result = subprocess.run(
                ["explorer", path],
                check=False,
                capture_output=True,
                text=True,
            )
            if explorer_result.returncode == 0:
                return True

        cmd_result = subprocess.run(
            ["cmd", "/c", "start", "", path],
            check=False,
            capture_output=True,
            text=True,
        )
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
                "source": "index",
            }

        path = find_app(app_name)
        if path:
            if _open_path(path):
                _log_stage("index", f"resolved '{app_name}' via app index: {path}")
                return {"status": "success", "action": "open_app", "app": app_name, "source": "index"}
            _log_stage("index", f"resolved '{app_name}' via app index but launch failed: {path}")
            return {
                "status": "error",
                "reason": "launch_failed",
                "app": app_name,
                "path": path,
                "source": "index",
            }

        if try_special_case_launch(app_name):
            _log_stage("special", f"resolved '{app_name}' via special launcher")
            return {"status": "success", "action": "open_app", "app": app_name, "source": "special"}

        if _try_system_launch(app_name):
            return {"status": "success", "action": "open_app", "app": app_name, "source": "system"}

        _log_stage("failback", f"app '{app_name}' not found")
        return {"status": "error", "reason": "app_not_found", "app": app_name}

    if action == "close_app":
        app_name = normalize_text((data or {}).get("app", ""))
        aliases = _load_aliases()
        path = find_app(app_name)
        return smart_close(app_name, path=path, aliases=aliases)

    if not command:
        return {"status": "error", "reason": "unknown_command"}

    if command["kind"] == "url":
        webbrowser.open(command["target"])
        return {
            "status": "success",
            "action": action,
            "meta": data,
        }

    if command["kind"] == "command":
        os.system(command["target"])
        return {
            "status": "success",
            "action": action,
            "meta": data,
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
