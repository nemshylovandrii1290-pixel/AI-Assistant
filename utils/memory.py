import json
import os
from datetime import datetime

from utils.normalize import normalize_text


MEMORY_DIR = os.path.join(os.getcwd(), ".cache")
MEMORY_FILE = os.path.join(MEMORY_DIR, "assistant_memory.json")

NON_TEACHABLE_PHRASES = {
    "відкрий",
    "open",
    "запусти",
    "запустить",
    "увімкни",
    "включи",
    "play",
    "stop",
    "стоп",
    "edit",
}

NON_TEACHABLE_PREFIXES = {
    "відкрий",
    "open",
    "запусти",
    "увімкни",
    "включи",
}


def _default_memory():
    return {
        "phrase_actions": {},
        "app_launch_counts": {},
    }


def _is_teachable_phrase(phrase):
    normalized_phrase = normalize_text(phrase)
    if not normalized_phrase or normalized_phrase in NON_TEACHABLE_PHRASES:
        return False

    tokens = normalized_phrase.split()
    if len(tokens) < 2:
        return False

    if tokens[0] in NON_TEACHABLE_PREFIXES:
        return False

    return len(normalized_phrase) >= 8


def _sanitize_memory(data):
    phrase_actions = {}
    for phrase, payload in (data.get("phrase_actions") or {}).items():
        if not _is_teachable_phrase(phrase):
            continue

        actions = payload.get("actions") or []
        if not actions:
            continue

        phrase_actions[normalize_text(phrase)] = {
            "actions": actions,
            "uses": int(payload.get("uses", 0)),
            "last_used_at": payload.get("last_used_at"),
        }

    app_counts = {}
    for app_name, count in (data.get("app_launch_counts") or {}).items():
        normalized_name = normalize_text(app_name)
        if normalized_name:
            app_counts[normalized_name] = app_counts.get(normalized_name, 0) + int(count)

    return {
        "phrase_actions": phrase_actions,
        "app_launch_counts": app_counts,
    }


def _load_memory():
    if not os.path.exists(MEMORY_FILE):
        return _default_memory()

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as memory_file:
            data = json.load(memory_file)
            if isinstance(data, dict):
                return _sanitize_memory(data)
    except (OSError, json.JSONDecodeError, ValueError):
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
    if not _is_teachable_phrase(normalized_phrase) or not actions:
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
    if not _is_teachable_phrase(normalized_phrase):
        return None

    memory = _load_memory()
    learned = memory["phrase_actions"].get(normalized_phrase)
    if not learned or learned.get("uses", 0) < 2:
        return None

    actions = learned.get("actions") or []
    if not actions:
        return None

    return actions


def get_memory_summary(limit=5):
    memory = _load_memory()

    top_apps = sorted(
        memory["app_launch_counts"].items(),
        key=lambda item: item[1],
        reverse=True,
    )[:limit]

    phrase_samples = sorted(
        memory["phrase_actions"].items(),
        key=lambda item: item[1].get("uses", 0),
        reverse=True,
    )[:limit]

    return {
        "top_apps": top_apps,
        "phrase_samples": [
            {
                "phrase": phrase,
                "uses": data.get("uses", 0),
                "actions": data.get("actions", []),
            }
            for phrase, data in phrase_samples
        ],
    }
