import json
import os
import re
import subprocess

from difflib import SequenceMatcher
from difflib import get_close_matches

from backend.utils.normalize import normalize_text


SEARCH_PATHS = [
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps"),
    os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"),
    os.path.join(os.environ.get("PROGRAMDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"),
    os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
    os.path.join(os.environ.get("USERPROFILE", ""), "Documents"),
    os.path.join(os.environ.get("USERPROFILE", ""), "Downloads"),
    os.path.join(os.environ.get("PUBLIC", "C:\\Users\\Public"), "Desktop"),
    os.path.join(os.environ.get("USERPROFILE", ""), "OneDrive", "Desktop"),
]

SKIP_DIRS = {
    "__pycache__",
    ".git",
    ".venv",
    "cache",
    "node_modules",
    "temp",
    "tmp",
}

BAD_EXECUTABLE_TOKENS = {
    "7z",
    "amf",
    "browser",
    "checker",
    "crash",
    "darkmodecheck",
    "diagnostics",
    "directvobsub",
    "ffmpeg",
    "graphics",
    "helper",
    "install",
    "installer",
    "nvenc",
    "offsets",
    "overlay",
    "page",
    "permission",
    "qsv",
    "redist",
    "redistributable",
    "report",
    "service",
    "setup",
    "support",
    "telemetry",
    "test",
    "tool",
    "tweak",
    "uninstall",
    "update",
    "updater",
    "vc_redist",
    "vobsub",
}

APP_CACHE = []
CACHE_READY = False
CACHE_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "data")
APP_CACHE_FILE = os.path.join(CACHE_DIR, "app_index.json")
LAST_CACHE_SOURCE = "none"
START_APP_CACHE = []
START_APP_FILE = os.path.join(CACHE_DIR, "start_apps.json")
CACHE_VERSION = 4


def _is_valid_start_app_entry(app):
    app_id = (app or {}).get("app_id", "")
    return bool(app_id) and not app_id.lower().startswith(("http://", "https://"))


def _sanitize_start_apps(apps):
    return [app for app in apps if isinstance(app, dict) and _is_valid_start_app_entry(app)]


def _clean_variant(text):
    normalized = normalize_text(text)
    normalized = re.sub(r"[^a-z0-9а-яіїєґ]+", " ", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _split_camel(name):
    return re.sub(r"(?<=[a-zа-яіїєґ])(?=[A-ZА-ЯІЇЄҐ0-9])", " ", name)


def _iter_app_files(base):
    for root, dirs, files in os.walk(base):
        dirs[:] = [directory for directory in dirs if directory.lower() not in SKIP_DIRS]

        for file_name in files:
            lower_name = file_name.lower()
            if lower_name.endswith((".exe", ".lnk", ".url", ".bat", ".cmd")):
                yield root, file_name


def _name_variants(file_name, root):
    base_name, _ = os.path.splitext(file_name)
    split_base_name = _split_camel(base_name)
    compact_base = _clean_variant(split_base_name)
    simplified_base = re.sub(r"(?<=\D)(32|64)$", "", compact_base).strip(" -_")
    simplified_base = re.sub(r"\b(app|launcher)\b", "", simplified_base).strip()

    variants = {
        _clean_variant(file_name),
        _clean_variant(base_name),
        compact_base,
        simplified_base,
    }

    current_root = root
    for _ in range(3):
        parent = os.path.basename(current_root)
        if not parent:
            break

        normalized_parent = _clean_variant(parent)
        variants.add(normalized_parent)

        if compact_base:
            variants.add(_clean_variant(f"{normalized_parent} {compact_base}"))
            variants.add(_clean_variant(f"{compact_base} {normalized_parent}"))

        current_root = os.path.dirname(current_root)

    return {variant for variant in variants if variant}


def _tokens(text):
    return [token for token in re.split(r"[^a-z0-9а-яіїєґ]+", text.lower()) if token]


def _is_false_positive(query, entry):
    path = entry["path"].lower()
    base_name = entry["base_name"]
    if query == "codec" and (
        "tweak" in path
        or "tool" in path
        or "tweak" in base_name
        or "tool" in base_name
    ):
        return True
    return False


def _entry_penalty(entry):
    penalty = 0.0
    base_name = entry["base_name"]
    path = entry["path"].lower()

    if entry["ext"] == ".exe" and any(token in base_name for token in BAD_EXECUTABLE_TOKENS):
        penalty += 0.24

    if entry["ext"] in {".bat", ".cmd"} and any(token in base_name for token in {"install", "setup", "uninstall"}):
        penalty += 0.35

    if "windowsapps" in path:
        penalty += 0.08

    if "\\bin\\" in path or "\\resources\\" in path:
        penalty += 0.04

    if "\\scripts\\" in path or "\\obs-plugins\\" in path:
        penalty += 0.18

    if entry["ext"] == ".url":
        penalty += 0.35

    if path.endswith("\\chrome.exe"):
        penalty += 0.08

    return penalty


def _score_match(query, entry):
    query_tokens = _tokens(query)
    base_name = entry["base_name"]
    parent_name = entry["parent_name"]
    names = entry["names"]
    base_tokens = _tokens(base_name)
    parent_tokens = _tokens(parent_name)
    score = 0.0

    if query in names:
        score = max(score, 1.0 if entry["ext"] == ".lnk" else 0.97)

    if query == base_name:
        score = max(score, 0.99)

    if parent_name and query == parent_name:
        score = max(score, 0.84)

    if len(query) >= 4 and len(base_name) >= 4 and (query in base_name or base_name in query):
        score = max(score, 0.965)

    if parent_name and len(query) >= 4 and len(parent_name) >= 4 and (query in parent_name or parent_name in query):
        score = max(score, 0.8)

    if query_tokens:
        overlap = sum(1 for token in query_tokens if token in base_tokens or token in parent_tokens)
        score = max(score, overlap / len(query_tokens))

        if base_tokens[: len(query_tokens)] == query_tokens:
            score = max(score, 0.985 if entry["ext"] in {".lnk", ".bat", ".cmd"} else 0.955)

        for variant in names:
            variant_tokens = _tokens(variant)
            if variant_tokens and all(token in variant_tokens for token in query_tokens):
                score = max(score, 0.99 if entry["ext"] == ".lnk" else 0.95)
            if variant_tokens[: len(query_tokens)] == query_tokens:
                score = max(score, 0.99 if entry["ext"] == ".lnk" else 0.955)

    score = max(score, SequenceMatcher(None, query, base_name).ratio() * 0.95)

    if parent_name:
        score = max(score, SequenceMatcher(None, query, parent_name).ratio() * 0.72)

    for variant in names:
        score = max(score, SequenceMatcher(None, query, variant).ratio() * 0.88)

    if entry["ext"] == ".lnk":
        score += 0.03

    if query == "codex" and "code" == base_name:
        score -= 0.25

    if query == "codec" and ("tweak" in base_name or "tool" in base_name):
        score -= 0.3

    score -= _entry_penalty(entry)
    return max(score, 0.0)


def _serialize_entry(entry):
    return {
        "path": entry["path"],
        "ext": entry["ext"],
        "names": sorted(entry["names"]),
        "base_name": entry["base_name"],
        "parent_name": entry["parent_name"],
    }


def _deserialize_entry(entry):
    return {
        "path": entry["path"],
        "ext": entry["ext"],
        "names": set(entry["names"]),
        "base_name": entry["base_name"],
        "parent_name": entry["parent_name"],
    }


def _run_powershell_json(script):
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def _load_start_apps():
    script = """
    Get-StartApps |
        Select-Object Name, AppID |
        ConvertTo-Json -Compress
    """
    data = _run_powershell_json(script)
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return []

    apps = []
    for item in data:
        name = (item.get("Name") or "").strip()
        app_id = (item.get("AppID") or "").strip()
        if not name or not app_id:
            continue
        if app_id.lower().startswith(("http://", "https://")):
            continue
        normalized_name = _clean_variant(name)
        apps.append(
            {
                "name": name,
                "app_id": app_id,
                "normalized_name": normalized_name,
                "tokens": _tokens(normalized_name),
            }
        )
    return apps


def _is_cache_valid():
    if not os.path.exists(APP_CACHE_FILE):
        return False

    cache_mtime = os.path.getmtime(APP_CACHE_FILE)

    for base in SEARCH_PATHS:
        if base and os.path.exists(base) and os.path.getmtime(base) > cache_mtime:
            return False

    return True


def _load_cache_from_disk():
    global APP_CACHE, CACHE_READY, LAST_CACHE_SOURCE, START_APP_CACHE

    if not _is_cache_valid():
        return False

    try:
        with open(APP_CACHE_FILE, "r", encoding="utf-8") as cache_file:
            data = json.load(cache_file)
    except (OSError, json.JSONDecodeError, KeyError):
        return False

    if not isinstance(data, dict) or data.get("version") != CACHE_VERSION:
        return False

    APP_CACHE = [_deserialize_entry(entry) for entry in data.get("entries", [])]
    START_APP_CACHE = _sanitize_start_apps(data.get("start_apps", []))
    CACHE_READY = True
    LAST_CACHE_SOURCE = "disk"
    return True


def _save_cache_to_disk():
    os.makedirs(CACHE_DIR, exist_ok=True)

    with open(APP_CACHE_FILE, "w", encoding="utf-8") as cache_file:
        json.dump(
            {
                "version": CACHE_VERSION,
                "entries": [_serialize_entry(entry) for entry in APP_CACHE],
                "start_apps": START_APP_CACHE,
            },
            cache_file,
            ensure_ascii=False,
        )


def _rebuild_cache():
    global APP_CACHE, CACHE_READY, LAST_CACHE_SOURCE, START_APP_CACHE

    APP_CACHE = []
    CACHE_READY = False
    START_APP_CACHE = _sanitize_start_apps(_load_start_apps())

    for base in SEARCH_PATHS:
        if not base or not os.path.exists(base):
            continue

        for root, file_name in _iter_app_files(base):
            full_path = os.path.join(root, file_name)
            APP_CACHE.append(
                {
                    "path": full_path,
                    "ext": os.path.splitext(file_name)[1].lower(),
                    "names": _name_variants(file_name, root),
                    "base_name": _clean_variant(os.path.splitext(file_name)[0]),
                    "parent_name": _clean_variant(os.path.basename(root)),
                }
            )

    _save_cache_to_disk()
    CACHE_READY = True
    LAST_CACHE_SOURCE = "rebuilt"


def ensure_app_index(force_refresh=False):
    global CACHE_READY

    if force_refresh:
        _rebuild_cache()
        return LAST_CACHE_SOURCE, len(APP_CACHE)

    if CACHE_READY:
        return "memory", len(APP_CACHE)

    if _load_cache_from_disk():
        return LAST_CACHE_SOURCE, len(APP_CACHE)

    _rebuild_cache()
    return LAST_CACHE_SOURCE, len(APP_CACHE)


def find_app(app_name):
    app_name = normalize_text(app_name.lower()).strip()

    ensure_app_index()

    if not app_name:
        return None

    if app_name == "codec":
        for entry in APP_CACHE:
            if entry["base_name"] == "codec":
                return entry["path"]
        return None

    query_tokens = _tokens(app_name)

    for entry in APP_CACHE:
        if _is_false_positive(app_name, entry):
            continue
        if app_name == entry["base_name"] and _entry_penalty(entry) < 0.1:
            return entry["path"]

    for entry in APP_CACHE:
        if _is_false_positive(app_name, entry):
            continue
        base_tokens = _tokens(entry["base_name"])
        if query_tokens and base_tokens[: len(query_tokens)] == query_tokens and _entry_penalty(entry) < 0.12:
            return entry["path"]

    for entry in APP_CACHE:
        if _is_false_positive(app_name, entry):
            continue
        if entry["ext"] == ".lnk" and app_name in entry["names"] and _entry_penalty(entry) < 0.15:
            return entry["path"]

    if " " not in app_name:
        try:
            executable_name = app_name if app_name.endswith(".exe") else f"{app_name}.exe"
            where_result = subprocess.run(
                ["where", executable_name],
                capture_output=True,
                text=True,
                check=False,
            )
            first_path = where_result.stdout.strip().splitlines()
            if first_path:
                return first_path[0]
        except OSError:
            pass

    best_score = 0.0
    best_path = None

    for entry in APP_CACHE:
        if _is_false_positive(app_name, entry):
            continue
        score = _score_match(app_name, entry)
        if score > best_score:
            best_score = score
            best_path = entry["path"]

    if best_score >= 0.78:
        if app_name == "codec" and best_path and any(token in best_path.lower() for token in ("tweak", "tool")):
            return None
        return best_path

    candidate_names = [entry["base_name"] for entry in APP_CACHE]
    fuzzy = get_close_matches(app_name, candidate_names, n=1, cutoff=0.8)
    if fuzzy:
        matched_name = fuzzy[0]
        for entry in APP_CACHE:
            if _is_false_positive(app_name, entry):
                continue
            if entry["base_name"] == matched_name:
                return entry["path"]

    return None


def find_start_app(app_name):
    normalized_name = normalize_text(app_name.lower()).strip()
    ensure_app_index()

    if not normalized_name:
        return None

    START_APP_CACHE[:] = _sanitize_start_apps(START_APP_CACHE)

    for app in START_APP_CACHE:
        if normalized_name == app["normalized_name"]:
            return app

    query_tokens = _tokens(normalized_name)
    for app in START_APP_CACHE:
        if query_tokens and app["tokens"][: len(query_tokens)] == query_tokens:
            return app

    best_score = 0.0
    best_app = None
    for app in START_APP_CACHE:
        score = SequenceMatcher(None, normalized_name, app["normalized_name"]).ratio()
        if score > best_score:
            best_score = score
            best_app = app

    if best_score >= 0.72:
        return best_app

    close = get_close_matches(
        normalized_name,
        [app["normalized_name"] for app in START_APP_CACHE],
        n=1,
        cutoff=0.72,
    )
    if close:
        for app in START_APP_CACHE:
            if app["normalized_name"] == close[0]:
                return app

    return None
