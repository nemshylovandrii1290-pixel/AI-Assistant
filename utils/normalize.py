REPLACEMENTS = {
    "nxt come": "nxt cam",
    "хуйово play": "hoyoplay",
    "хойово": "hoyoplay",
    "адоб": "adobe",
    "віндхавк": "windhawk",
}

def normalize_text(text: str):
    text = text.lower()

    for wrong, correct in REPLACEMENTS.items():
        if wrong in text:
            text = text.replace(wrong, correct)

    return text
