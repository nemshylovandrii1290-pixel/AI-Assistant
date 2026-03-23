import os

from dotenv import load_dotenv


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGUAGE = os.getenv("LANGUAGE", "uk-UA")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
RECOGNITION_LANGUAGES = [
    language.strip()
    for language in os.getenv("RECOGNITION_LANGUAGES", "uk-UA,ru-RU,en-US").split(",")
    if language.strip()
]
LISTEN_DURATION = float(os.getenv("LISTEN_DURATION", "7"))
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
