import os
import json
import subprocess
import re

from difflib import SequenceMatcher

from utils.normalize import normalize_text

SEARCH_PATHS = [
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
    os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"),
    os.path.join(os.environ.get("PROGRAMDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"),
    os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
    os.path.join(os.environ.get("PUBLIC", "C:\\Users\\Public"), "Desktop"),
    os.path.join(os.environ.get("USERPROFILE", ""), "OneDrive", "Desktop")
]

APP_CACHE = []
CACHE_READY = False
CACHE_DIR = os.path.join(os.getcwd(), ".cache")
APP_CACHE_FILE = os.path.join(CACHE_DIR, "app_index.json")
LAST_CACHE_SOURCE = "none"
BAD_EXECUTABLE_TOKENS = {
    "crash", "helper", "service", "setup", "uninstall", "update", "updater",
    "diagnostics", "report", "redist", "redistributable", "vc_redist", "7z",
    "installer", "install", "telemetry", "test", "ffmpeg", "browser",
    "page", "qsv", "nvenc", "amf", "vobsub", "directvobsub"
}


def _iter_app_files(base):
    for root, dirs, files in os.walk(base):
        dirs[:] = [directory for directory in dirs if directory.lower() not in {
            "__pycache__", ".git", ".venv", "node_modules", "temp", "tmp", "cache"
        }]

        for file_name in files:
            lower_name = file_name.lower()
            if lower_name.endswith(".exe") or lower_name.endswith(".lnk") or lower_name.endswith(".url"):
                yield root, file_name


def _name_variants(file_name, root):
    base_name, _ = os.path.splitext(file_name)
    split_base_name = re.sub(r"(?<=[a-zа-яіїєґ])(?=[A-ZА-ЯІЇЄҐ0-9])", " ", base_name)
    normalized_split_base_name = normalize_text(split_base_name.lower())
    compact_base_name = re.sub(r"[^a-z0-9а-яіїєґ]+", " ", normalized_split_base_name).strip()

    variants = {
        normalize_text(file_name.lower()),
        normalize_text(base_name.lower()),
        normalized_split_base_name,
        compact_base_name,
    }

    current_root = root
    for _ in range(3):
        parent = os.path.basename(current_root).lower()
        if not parent:
            break

        normalized_parent = normalize_text(parent)
        compact_parent = re.sub(r"[^a-z0-9а-яіїєґ]+", " ", normalized_parent).strip()

        variants.add(normalized_parent)
        variants.add(compact_parent)
        variants.add(normalize_text(f"{normalized_parent} {normalized_split_base_name}"))

        current_root = os.path.dirname(current_root)

    return {variant.strip() for variant in variants if variant.strip()}


def _tokens(text):
    return [token for token in re.split(r"[^a-z0-9а-яіїєґ]+", text.lower()) if token]


def _entry_penalty(entry):
    base_name = entry["base_name"]
    penalty = 0.0

    if entry["ext"] == ".exe" and any(token in base_name for token in BAD_EXECUTABLE_TOKENS):
        penalty += 0.22

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
        score = max(score, 1.0 if entry["ext"] in {".lnk", ".url"} else 0.97)

    if query == base_name:
        score = max(score, 0.99)

    if parent_name and query == parent_name:
        score = max(score, 0.82)

    if len(query) >= 4 and len(base_name) >= 4 and (query in base_name or base_name in query):
        score = max(score, 0.96)

    if parent_name and len(query) >= 4 and len(parent_name) >= 4 and (query in parent_name or parent_name in query):
        score = max(score, 0.78)

    if query_tokens:
        overlap = sum(1 for token in query_tokens if token in base_tokens or token in parent_tokens)
        score = max(score, overlap / len(query_tokens))

        for variant in names:
            variant_tokens = _tokens(variant)
            if query_tokens and all(token in variant_tokens for token in query_tokens):
                score = max(score, 0.99 if entry["ext"] in {".lnk", ".url"} else 0.95)

    score = max(score, SequenceMatcher(None, query, base_name).ratio() * 0.95)

    if parent_name:
        score = max(score, SequenceMatcher(None, query, parent_name).ratio() * 0.72)

    for variant in names:
        score = max(score, SequenceMatcher(None, query, variant).ratio() * 0.88)

    if entry["ext"] in {".lnk", ".url"}:
        score += 0.03

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
    path = entry["path"]
    parent_name = entry.get("parent_name")
    if parent_name is None:
        parent_name = normalize_text(os.path.basename(os.path.dirname(path)).lower())

    base_name = entry.get("base_name")
    if base_name is None:
        base_name = normalize_text(os.path.splitext(os.path.basename(path))[0].lower())

    return {
        "path": path,
        "ext": entry["ext"],
        "names": set(entry["names"]),
        "base_name": base_name,
        "parent_name": parent_name,
    }


def _is_cache_valid():
    if not os.path.exists(APP_CACHE_FILE):
        return False

    cache_mtime = os.path.getmtime(APP_CACHE_FILE)

    for base in SEARCH_PATHS:
        if base and os.path.exists(base) and os.path.getmtime(base) > cache_mtime:
            return False

    return True


def _load_cache_from_disk():
    global APP_CACHE, CACHE_READY, LAST_CACHE_SOURCE

    if not _is_cache_valid():
        return False

    try:
        with open(APP_CACHE_FILE, "r", encoding="utf-8") as cache_file:
            data = json.load(cache_file)
    except (OSError, json.JSONDecodeError, KeyError):
        return False

    APP_CACHE = [_deserialize_entry(entry) for entry in data]
    CACHE_READY = True
    LAST_CACHE_SOURCE = "disk"
    return True


def _save_cache_to_disk():
    os.makedirs(CACHE_DIR, exist_ok=True)

    with open(APP_CACHE_FILE, "w", encoding="utf-8") as cache_file:
        json.dump(
            [_serialize_entry(entry) for entry in APP_CACHE],
            cache_file,
            ensure_ascii=False
        )


def _rebuild_cache():
    global APP_CACHE, CACHE_READY, LAST_CACHE_SOURCE

    APP_CACHE = []
    CACHE_READY = False

    for base in SEARCH_PATHS:
        if not base or not os.path.exists(base):
            continue

        for root, file_name in _iter_app_files(base):
            full_path = os.path.join(root, file_name)
            APP_CACHE.append({
                "path": full_path,
                "ext": os.path.splitext(file_name)[1].lower(),
                "names": _name_variants(file_name, root),
                "base_name": normalize_text(os.path.splitext(file_name)[0].lower()),
                "parent_name": normalize_text(os.path.basename(root).lower()),
            })

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

    for entry in APP_CACHE:
        if app_name == entry["base_name"] and _entry_penalty(entry) < 0.1:
            return entry["path"]

    for entry in APP_CACHE:
        if entry["ext"] in {".lnk", ".url"} and app_name in entry["names"]:
            return entry["path"]

    if " " not in app_name:
        try:
            exe_name = app_name if app_name.endswith(".exe") else f"{app_name}.exe"
            where_result = subprocess.run(
                ["where", exe_name],
                capture_output=True,
                text=True,
                check=False
            )
            first_path = where_result.stdout.strip().splitlines()
            if first_path:
                return first_path[0]
        except OSError:
            pass

    best_score = 0.0
    best_path = None

    for entry in APP_CACHE:
        score = _score_match(app_name, entry)
        if score > best_score:
            best_score = score
            best_path = entry["path"]

    if best_score >= 0.78:
        return best_path

    return None
