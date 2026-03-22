import os

from dotenv import load_dotenv


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGUAGE = os.getenv("LANGUAGE", "uk-UA")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
