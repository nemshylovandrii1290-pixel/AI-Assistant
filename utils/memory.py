import json
import os
import threading
from datetime import datetime, timezone

from utils.normalize import normalize_text

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

MEMORY_DIR = os.path.join(PROJECT_ROOT, ".cache")
MEMORY_FILE = os.path.join(MEMORY_DIR, "assistant_memory.json")

_memory_cache = None
_save_timer = None
_memory_lock = threading.RLock()

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
        if not isinstance(payload, dict):
            continue

        actions = payload.get("actions") or []
        if not actions:
            continue

        normalized = normalize_text(phrase)

        if normalized not in phrase_actions:
            phrase_actions[normalized] = {
                "actions": actions,
                "uses": int(payload.get("uses", 0)),
                "last_used_at": payload.get("last_used_at"),
                "originals": [phrase],
            }
        else:
            existing = phrase_actions[normalized]

            existing["uses"] += int(payload.get("uses", 0))
            existing["originals"].append(phrase)

            new_time = payload.get("last_used_at")
            old_time = existing.get("last_used_at")

            if new_time and (not old_time or new_time > old_time):
                existing["actions"] = actions
                existing["last_used_at"] = new_time

    return {
        "phrase_actions": phrase_actions,
        "app_launch_counts": data.get("app_launch_counts", {}),
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


def _get_memory():
    global _memory_cache

    if _memory_cache is None:
        _memory_cache = _load_memory()

    return _memory_cache


def _save_memory(data):
    global _memory_cache

    with _memory_lock:
        os.makedirs(MEMORY_DIR, exist_ok=True)
        with open(MEMORY_FILE, "w", encoding="utf-8") as memory_file:
            json.dump(data, memory_file, ensure_ascii=False, indent=2)

        _memory_cache = data


def _schedule_save():
    global _save_timer

    with _memory_lock:
        if _save_timer is not None:
            _save_timer.cancel()

        _save_timer = threading.Timer(1.0, _flush_save)
        _save_timer.start()


def _flush_save():
    global _memory_cache, _save_timer

    with _memory_lock:
        if _memory_cache is None:
            return

        _save_timer = None
        _save_memory(_memory_cache)


def remember_app_launch(app_name):
    normalized_name = normalize_text(app_name)
    if not normalized_name:
        return

    with _memory_lock:
        memory = _get_memory()
        stats = memory["app_launch_counts"]
        stats[normalized_name] = stats.get(normalized_name, 0) + 1

    _schedule_save()


def remember_phrase_actions(phrase, actions):
    normalized_phrase = normalize_text(phrase)
    if not _is_teachable_phrase(normalized_phrase) or not actions:
        return

    with _memory_lock:
        memory = _get_memory()
        phrase_actions = memory["phrase_actions"]
        current = phrase_actions.get(normalized_phrase, {})
        phrase_actions[normalized_phrase] = {
            "actions": actions,
            "uses": current.get("uses", 0) + 1,
            "last_used_at": datetime.now(timezone.utc).isoformat(),
        }

    _schedule_save()


def get_learned_actions(phrase):
    normalized_phrase = normalize_text(phrase)
    if not _is_teachable_phrase(normalized_phrase):
        return None

    with _memory_lock:
        memory = _get_memory()
        learned = memory["phrase_actions"].get(normalized_phrase)
        if not learned or learned.get("uses", 0) < 2:
            return None

        actions = learned.get("actions") or []
        if not actions:
            return None

    return actions


def get_memory_summary(limit=5):
    with _memory_lock:
        memory = _get_memory()

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
                "uses": item.get("uses", 0),
                "actions": item.get("actions", []),
            }
            for phrase, item in phrase_samples
        ],
    }
