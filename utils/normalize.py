REPLACEMENTS = {
    "nxt come": "nxt cam",
    "хуйово play": "hoyoplay",
    "хойово": "hoyoplay",
    "хойолаб": "hoyolab",
    "хойо лаб": "hoyolab",
    "енвідіа": "nvidia",
    "нвідіа": "nvidia",
    "інвідіа": "nvidia",
    "ем еc ай": "msi",
    "емесіай": "msi",
    "автобернер": "afterburner",
    "афтербернер": "afterburner",
    "фурмарк": "furmark",
    "аїда": "aida",
    "анлок гоу": "unlock go",
    "мета академія": "mate academy",
    "ел конект": "l connect",
    "ел-конект": "l connect",
    "обс студіо": "obs studio",
    "обс": "obs studio",
    "obs": "obs studio",
    "адоб": "adobe",
    "віндхавк": "windhawk",
}

def normalize_text(text: str):
    text = text.lower()

    for wrong, correct in REPLACEMENTS.items():
        if wrong in text:
            text = text.replace(wrong, correct)

    text = text.replace("obs studio studio", "obs studio")

    return text
