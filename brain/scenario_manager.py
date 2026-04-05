import json
import os

from utils.normalize import normalize_text
from utils.scenario_config import SCENARIO_ACTIONS


BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
CACHE_DIR = os.path.join(PROJECT_ROOT, ".cache")
SCENARIO_FILE = os.path.join(CACHE_DIR, "scenario_memory.json")


def _default_state():
    return {
        "extra_apps": {},
    }


class ScenarioManager:
    def __init__(self):
        self.active = None
        self.pending_app = None
        self.pending_source = None
        self._state = self._load_state()

    def _load_state(self):
        if not os.path.exists(SCENARIO_FILE):
            return _default_state()

        try:
            with open(SCENARIO_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError, ValueError):
            return _default_state()

        if not isinstance(data, dict):
            return _default_state()

        extra_apps = data.get("extra_apps")
        if not isinstance(extra_apps, dict):
            return _default_state()

        sanitized = {}
        for scenario_name, apps in extra_apps.items():
            if isinstance(apps, list):
                sanitized[scenario_name] = [normalize_text(app) for app in apps if normalize_text(app)]

        return {"extra_apps": sanitized}

    def _save_state(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(SCENARIO_FILE, "w", encoding="utf-8") as file:
            json.dump(self._state, file, ensure_ascii=False, indent=2)

    def activate(self, name):
        self.active = name if name in SCENARIO_ACTIONS else None
        self.pending_app = None
        self.pending_source = None

    def deactivate(self):
        self.active = None
        self.pending_app = None
        self.pending_source = None

    def get_actions(self, name):
        base_actions = [dict(action) for action in SCENARIO_ACTIONS.get(name, [])]
        extra_apps = self._state["extra_apps"].get(name, [])

        known_apps = {
            normalize_text(action.get("app", ""))
            for action in base_actions
            if action.get("type") == "open_app"
        }

        for app_name in extra_apps:
            if app_name not in known_apps:
                base_actions.append({"type": "open_app", "app": app_name})
                known_apps.add(app_name)

        return base_actions

    def is_app_in_active_scenario(self, app_name):
        if not self.active:
            return False

        normalized_app = normalize_text(app_name)
        for action in self.get_actions(self.active):
            if action.get("type") == "open_app" and normalize_text(action.get("app", "")) == normalized_app:
                return True
        return False

    def should_offer_app(self, app_name):
        normalized_app = normalize_text(app_name)
        if not self.active or not normalized_app:
            return False
        if self.pending_app:
            return False
        return not self.is_app_in_active_scenario(normalized_app)

    def queue_app_offer(self, app_name, source="manual"):
        normalized_app = normalize_text(app_name)
        if not self.should_offer_app(normalized_app):
            return None

        self.pending_app = normalized_app
        self.pending_source = source
        return f"Цього додатка ще немає в сценарії {self.active}. Додати {normalized_app} в сценарій?"

    def has_pending_offer(self):
        return bool(self.pending_app and self.active)

    def confirm_pending(self):
        if not self.has_pending_offer():
            return None

        scenario_name = self.active
        app_name = self.pending_app
        apps = self._state["extra_apps"].setdefault(scenario_name, [])
        if app_name not in apps:
            apps.append(app_name)
            apps.sort()
            self._save_state()

        self.pending_app = None
        self.pending_source = None
        return scenario_name, app_name

    def reject_pending(self):
        self.pending_app = None
        self.pending_source = None
