import re


REPLACEMENTS = [
    ("nxt come", "nxt cam"),
    ("хоёво play", "hoyoplay"),
    ("хойово play", "hoyoplay"),
    ("хоёво", "hoyoplay"),
    ("хойово", "hoyoplay"),
    ("хойолаб", "hoyolab"),
    ("хойо лаб", "hoyolab"),
    ("hoyo lab", "hoyolab"),
    ("hojo", "hoyolab"),
    ("блендер", "blender"),
    ("кодекс", "codex"),
    ("чат gpt", "chatgpt"),
    ("chat gpt", "chatgpt"),
    ("чат джипити", "chatgpt"),
    ("кьют лок", "cute lock"),
    ("кьютлок", "cute lock"),
    ("кют лок", "cute lock"),
    ("qt lock", "cute lock"),
    ("qute lock", "cute lock"),
    ("cut lock", "cute lock"),
    ("енвідіа", "nvidia"),
    ("нвідіа", "nvidia"),
    ("інвідіа", "nvidia"),
    ("эм эс ай", "msi"),
    ("ем ес ай", "msi"),
    ("емесіай", "msi"),
    ("автобернер", "afterburner"),
    ("афтербернер", "afterburner"),
    ("фурмарк", "furmark"),
    ("фурма", "furmark"),
    ("аїда", "aida"),
    ("анлок гоу", "unlock go"),
    ("мета академія", "mate academy"),
    ("эл конект", "l connect"),
    ("ел конект", "l connect"),
    ("ел-конект", "l connect"),
    ("обс студіо", "obs studio"),
    ("обс студио", "obs studio"),
    ("обс", "obs studio"),
    ("адоб", "adobe"),
    ("віндхавк", "windhawk"),
    ("едід", "edit"),
    ("едит", "edit"),
    ("эдит", "edit"),
    ("эдід", "edit"),
    ("эдид", "edit"),
    ("увимкни", "увімкни"),
    ("вимкни", "вимкни"),
    ("вімкни", "увімкни"),
    ("игровый", "ігровий"),
    ("игровое", "ігрове"),
    ("рабочий", "робочий"),
    ("рабочее", "робоче"),
    ("пространство", "простір"),
    ("відкрай", "відкрий"),
    ("відкрив", "відкрий"),
]

LEADING_FILLERS = {
    "а",
    "а ну",
    "ви",
    "ти",
    "ну",
    "ой",
    "hey",
    "please",
}


def _replace_phrase(text: str, source: str, target: str) -> str:
    pattern = re.compile(rf"(?<![\w]){re.escape(source)}(?![\w])", re.IGNORECASE)
    return pattern.sub(target, text)


def normalize_text(text: str) -> str:
    normalized = text.lower().strip()
    normalized = normalized.replace("...", " ")
    normalized = re.sub(r"[.,!?;:]+", " ", normalized)

    for wrong, correct in REPLACEMENTS:
        normalized = _replace_phrase(normalized, wrong, correct)

    normalized = re.sub(r"\s+", " ", normalized).strip()

    for filler in sorted(LEADING_FILLERS, key=len, reverse=True):
        if normalized.startswith(f"{filler} "):
            normalized = normalized[len(filler):].strip()
            break

    normalized = normalized.replace("obs studio studio", "obs studio")
    normalized = normalized.replace("the telegram", "telegram")
    return normalized.strip()
