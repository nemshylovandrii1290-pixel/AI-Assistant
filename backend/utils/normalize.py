import re


PHRASE_REPLACEMENTS = [
    ("nxt come", "nxt cam"),
    ("hoyo lab", "hoyolab"),
    ("hojo", "hoyolab"),
    ("chat gpt", "chatgpt"),
    ("чат gpt", "chatgpt"),
    ("чат джіпіті", "chatgpt"),
    ("телеграм", "telegram"),
    ("соблайм текст", "sublime text"),
    ("саблайм текст", "sublime text"),
    ("кьют лок", "cute lock"),
    ("кют лок", "cute lock"),
    ("кьют лог", "cute log"),
    ("кют лог", "cute log"),
    ("qt lock", "cute lock"),
    ("qute lock", "cute lock"),
    ("cut lock", "cute lock"),
    ("анлок гоу", "unlock go"),
    ("мета академія", "mate academy"),
    ("ел конект", "l connect"),
    ("эл конект", "l connect"),
    ("обс студіо", "obs studio"),
    ("обс студио", "obs studio"),
    ("обс", "obs studio"),
    ("блендер", "blender"),
    ("кодекс", "codex"),
    ("фурмарк", "furmark"),
    ("фурма", "furmark"),
    ("аїда", "aida"),
    ("аида", "aida"),
    ("автобернер", "afterburner"),
    ("афтербернер", "afterburner"),
    ("енвідіа", "nvidia"),
    ("нвідіа", "nvidia"),
    ("інвідіа", "nvidia"),
    ("їгровий", "ігровий"),
    ("игровый", "ігровий"),
    ("игровое", "ігрове"),
    ("рабочий", "робочий"),
    ("рабочее", "робоче"),
    ("пространство", "простір"),
    ("відкрай", "відкрий"),
    ("відкрив", "відкрий"),
    ("едіт", "edit"),
    ("едит", "edit"),
    ("эдит", "edit"),
]

WORD_FIXES = {
    "закрій": "закрий",
    "замкни": "закрий",
    "vidcray": "відкрий",
    "odkrey": "відкрий",
    "gray": "відкрий",
    "prey": "відкрий",
    "відкрай": "відкрий",
    "відкре": "відкрий",
    "vidkry": "відкрий",
    "vidkriy": "відкрий",
}

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


def fix_words(text: str) -> str:
    words = text.split()
    return " ".join(WORD_FIXES.get(word, word) for word in words)


def normalize_text(text: str) -> str:
    normalized = text.lower().strip()
    normalized = normalized.replace("...", " ")
    normalized = re.sub(r"[.,!?;:]+", " ", normalized)

    for wrong, correct in PHRASE_REPLACEMENTS:
        normalized = _replace_phrase(normalized, wrong, correct)

    normalized = fix_words(normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    for filler in sorted(LEADING_FILLERS, key=len, reverse=True):
        if normalized.startswith(f"{filler} "):
            normalized = normalized[len(filler):].strip()
            break

    normalized = normalized.replace("obs studio studio", "obs studio")
    normalized = normalized.replace("the telegram", "telegram")
    return normalized.strip()
