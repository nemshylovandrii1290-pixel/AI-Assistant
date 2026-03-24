SCENARIOS = {
    "gaming": {
        "response": "Вмикаю ігрове середовище.",
        "triggers": [
            "я хочу пограти",
            "хочу пограти",
            "ігрове середовище",
            "ігровий режим",
            "gaming mode",
            "gaming",
            "play game",
            "пограти",
        ],
        "actions": [
            {"type": "open_app", "app": "steam"},
            {"type": "open_app", "app": "discord"},
        ],
    },
    "work": {
        "response": "Готую робоче середовище.",
        "triggers": [
            "робоче середовище",
            "зроби мені робоче середовище",
            "режим роботи",
            "підготуй роботу",
            "work setup",
            "work mode",
            "робота",
        ],
        "actions": [
            {"type": "open_app", "app": "google chrome"},
            {"type": "command", "action": "open_code"},
            {"type": "command", "action": "open_notepad"},
        ],
    },
}


MUSIC_TRIGGERS = [
    "відкрий музику",
    "включи музику",
    "увімкни музику",
    "музику",
    "music",
    "play music",
    "lofi",
]
