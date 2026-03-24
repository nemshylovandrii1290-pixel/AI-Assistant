import json
import os
from datetime import datetime

from utils.normalize import normalize_text


MEMORY_DIR = os.path.join(os.getcwd(), ".cache")
MEMORY_FILE = os.path.join(MEMORY_DIR, "assistant_memory.json")


def _default_memory():
    return {
        "phrase_actions": {},
        "app_launch_counts": {},
    }


def _load_memory():
    if not os.path.exists(MEMORY_FILE):
        return _default_memory()

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as memory_file:
            data = json.load(memory_file)
            if isinstance(data, dict):
                return {
                    "phrase_actions": data.get("phrase_actions", {}),
                    "app_launch_counts": data.get("app_launch_counts", {}),
                }
    except (OSError, json.JSONDecodeError):
        pass

    return _default_memory()


def _save_memory(data):
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as memory_file:
        json.dump(data, memory_file, ensure_ascii=False, indent=2)


def remember_app_launch(app_name):
    normalized_name = normalize_text(app_name)
    if not normalized_name:
        return

    memory = _load_memory()
    stats = memory["app_launch_counts"]
    stats[normalized_name] = stats.get(normalized_name, 0) + 1
    _save_memory(memory)


def remember_phrase_actions(phrase, actions):
    normalized_phrase = normalize_text(phrase)
    if not normalized_phrase or not actions:
        return

    memory = _load_memory()
    phrase_actions = memory["phrase_actions"]
    current = phrase_actions.get(normalized_phrase, {})
    phrase_actions[normalized_phrase] = {
        "actions": actions,
        "uses": current.get("uses", 0) + 1,
        "last_used_at": datetime.utcnow().isoformat(),
    }
    _save_memory(memory)


def get_learned_actions(phrase):
    normalized_phrase = normalize_text(phrase)
    if not normalized_phrase:
        return None

    memory = _load_memory()
    learned = memory["phrase_actions"].get(normalized_phrase)
    if not learned:
        return None

    actions = learned.get("actions") or []
    if not actions:
        return None

    return actions
