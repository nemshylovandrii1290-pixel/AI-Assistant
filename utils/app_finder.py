import os
import subprocess

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


def _iter_app_files(base):
    for root, dirs, files in os.walk(base):
        dirs[:] = [directory for directory in dirs if directory.lower() not in {
            "__pycache__", ".git", ".venv", "node_modules", "temp", "tmp", "cache"
        }]

        for file_name in files:
            lower_name = file_name.lower()
            if lower_name.endswith(".exe") or lower_name.endswith(".lnk"):
                yield root, file_name


def _name_variants(file_name, root):
    base_name, ext = os.path.splitext(file_name)
    variants = {
        normalize_text(file_name.lower()),
        normalize_text(base_name.lower()),
    }

    parent = os.path.basename(root).lower()
    if parent:
        variants.add(normalize_text(parent))
        variants.add(normalize_text(f"{parent} {base_name.lower()}"))

    return {variant.strip() for variant in variants if variant.strip()}


def _score_match(query, entry):
    best_score = 0.0

    for variant in entry["names"]:
        if query == variant:
            return 1.0
        if query in variant or variant in query:
            best_score = max(best_score, 0.94)
        else:
            best_score = max(best_score, SequenceMatcher(None, query, variant).ratio())

    return best_score

def build_cache():
    global CACHE_READY

    if CACHE_READY:
        return

    for base in SEARCH_PATHS:
        if not base or not os.path.exists(base):
            continue

        for root, file_name in _iter_app_files(base):
            full_path = os.path.join(root, file_name)
            APP_CACHE.append({
                "path": full_path,
                "ext": os.path.splitext(file_name)[1].lower(),
                "names": _name_variants(file_name, root),
            })

    CACHE_READY = True


def find_app(app_name):
    app_name = normalize_text(app_name.lower()).strip()

    build_cache()

    if not app_name:
        return None

    for entry in APP_CACHE:
        if app_name in entry["names"]:
            return entry["path"]

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

    if best_score >= 0.72:
        return best_path

    return None
