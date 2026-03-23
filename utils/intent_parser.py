OPEN_PREFIXES = [
    "відкрий ",
    "відкрій ",
    "запусти ",
    "запустить ",
    "open ",
]


def extract_open_target(text):
    stripped = text.strip()

    for prefix in OPEN_PREFIXES:
        if stripped.startswith(prefix):
            target = stripped[len(prefix):].strip()
            return target or None

    return None
