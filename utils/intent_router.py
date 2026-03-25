from utils.app_finder import find_app
from utils.memory import get_learned_actions
from utils.normalize import normalize_text
from utils.phrase_match import contains_phrase
from utils.scenario_config import (
    DISABLE_SCENARIO_TRIGGERS,
    MUSIC_TRIGGERS,
    SCENARIO_ACTIONS,
    SCENARIOS,
)


DISABLE_WORDS = (
    "вимкни",
    "выключи",
    "виключи",
    "зупини",
    "stop",
    "disable",
)


def _contains_trigger(text, triggers):
    return contains_phrase(text, triggers)


def _is_disable_request(text):
    return any(word in text for word in DISABLE_WORDS)


def _clone_actions(actions):
    return [dict(action) for action in actions]


def _build_music_actions(context):
    preferred_app = "spotify" if context.get("mode") == "gaming" else "youtube music"
    fallback_app = "youtube music" if preferred_app == "spotify" else "spotify"

    if find_app(preferred_app):
        target_app = preferred_app
    elif find_app(fallback_app):
        target_app = fallback_app
    else:
        target_app = "youtube music"

    response = "Відкриваю музику."
    if target_app == "spotify":
        response = "Відкриваю Spotify для ігрового режиму."
    elif target_app == "youtube music" and context.get("mode") == "work":
        response = "Відкриваю YouTube Music для роботи."

    return {
        "type": "multi_action",
        "source": "context",
        "response": response,
        "actions": [{"type": "open_app", "app": target_app}],
    }


def _build_work_actions():
    browser_app = "google chrome" if find_app("google chrome") else "microsoft edge"
    actions = _clone_actions(SCENARIO_ACTIONS["work"])
    actions[0] = {"type": "open_app", "app": browser_app}

    return {
        "type": "multi_action",
        "source": "scenario",
        "scenario": "work",
        "response": SCENARIOS["work"]["response"],
        "actions": actions,
    }


def _build_static_scenario(name):
    return {
        "type": "multi_action",
        "source": "scenario",
        "scenario": name,
        "response": SCENARIOS[name]["response"],
        "actions": _clone_actions(SCENARIO_ACTIONS[name]),
    }


def resolve_local_intent(text, context):
    normalized_text = normalize_text(text)
    scenario_labels = {
        "gaming": "ігрового",
        "work": "робочого",
    }

    if _is_disable_request(normalized_text):
        for scenario_name, triggers in DISABLE_SCENARIO_TRIGGERS.items():
            if _contains_trigger(normalized_text, triggers):
                return {
                    "type": "chat",
                    "source": "scenario",
                    "response": f"Вимкнення {scenario_labels.get(scenario_name, scenario_name)} режиму поки не підтримується.",
                }

    if _contains_trigger(normalized_text, SCENARIOS["gaming"]["triggers"]):
        return _build_static_scenario("gaming")

    if _contains_trigger(normalized_text, SCENARIOS["work"]["triggers"]):
        return _build_work_actions()

    if _contains_trigger(normalized_text, MUSIC_TRIGGERS):
        return _build_music_actions(context)

    learned_actions = get_learned_actions(normalized_text)
    if learned_actions:
        return {
            "type": "multi_action",
            "source": "memory",
            "response": "Запускаю те, що ти зазвичай відкриваєш для цього запиту.",
            "actions": learned_actions,
        }

    return None
