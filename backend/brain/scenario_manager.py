from backend.utils.normalize import normalize_text
from backend.utils.scenario_config import SCENARIO_ACTIONS
from backend.utils.memory import get_scenario_apps, remember_scenario_app


class ScenarioManager:
    def __init__(self):
        self.active = None
        self.apps = []
        self.pending_app = None
        self.pending_source = None

    def activate(self, name):
        normalized_name = normalize_text(name)
        self.active = normalized_name if normalized_name in SCENARIO_ACTIONS else None
        self.apps = self._merge_apps(self.active) if self.active else []
        self.pending_app = None
        self.pending_source = None

    def deactivate(self):
        self.active = None
        self.apps = []
        self.pending_app = None
        self.pending_source = None

    def _merge_apps(self, scenario_name):
        if not scenario_name:
            return []

        merged = []
        seen = set()
        for action in SCENARIO_ACTIONS.get(scenario_name, []):
            if action.get("type") != "open_app":
                continue
            app_name = normalize_text(action.get("app", ""))
            if app_name and app_name not in seen:
                seen.add(app_name)
                merged.append(app_name)

        for app_name in get_scenario_apps(scenario_name):
            normalized_app = normalize_text(app_name)
            if normalized_app and normalized_app not in seen:
                seen.add(normalized_app)
                merged.append(normalized_app)

        return merged

    def get_actions(self, name):
        normalized_name = normalize_text(name)
        base_actions = [dict(action) for action in SCENARIO_ACTIONS.get(normalized_name, [])]
        scenario_apps = self._merge_apps(normalized_name)

        known_apps = {
            normalize_text(action.get("app", ""))
            for action in base_actions
            if action.get("type") == "open_app"
        }

        for app_name in scenario_apps:
            if app_name not in known_apps:
                base_actions.append({"type": "open_app", "app": app_name})
                known_apps.add(app_name)

        return base_actions

    def get_active_apps(self):
        return list(self.apps)

    def add_app(self, app_name):
        normalized_app = normalize_text(app_name)
        if not self.active or not normalized_app:
            return False

        if normalized_app not in self.apps:
            self.apps.append(normalized_app)

        return remember_scenario_app(self.active, normalized_app)

    def is_app_in_active_scenario(self, app_name):
        if not self.active:
            return False

        normalized_app = normalize_text(app_name)
        return normalized_app in self.apps

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
        self.add_app(app_name)

        self.pending_app = None
        self.pending_source = None
        return scenario_name, app_name

    def handle_new_app(self, app_name):
        normalized_app = normalize_text(app_name)
        prompt = self.queue_app_offer(normalized_app, source="tracker")
        if not prompt:
            return None

        answer = input(f"{prompt} (y/n): ").strip().lower()
        if answer in {"y", "yes", "так", "ага", "да"}:
            return self.confirm_pending()

        self.reject_pending()
        return None

    def reject_pending(self):
        self.pending_app = None
        self.pending_source = None
