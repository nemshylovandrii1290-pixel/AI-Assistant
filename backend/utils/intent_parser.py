import re


OPEN_PREFIXES = [
    "відкрий",
    "відкрій",
    "запусти",
    "запустить",
    "open",
]


def extract_open_target(text):
    stripped = text.strip()

    for prefix in OPEN_PREFIXES:
        if stripped.startswith(f"{prefix} "):
            target = stripped[len(prefix):].strip()
            return target or None

    pattern = re.compile(r"\b(" + "|".join(re.escape(prefix) for prefix in OPEN_PREFIXES) + r")\b\s+(.+)")
    match = pattern.search(stripped)
    if match:
        target = match.group(2).strip()
        return target or None

    return None
