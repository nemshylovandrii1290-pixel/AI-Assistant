import os

from dotenv import load_dotenv


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_flash_v2_5")
ELEVENLABS_OUTPUT_FORMAT = os.getenv("ELEVENLABS_OUTPUT_FORMAT", "pcm_24000")
LANGUAGE = os.getenv("LANGUAGE", "uk-UA")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
RECOGNITION_LANGUAGES = [
    language.strip()
    for language in os.getenv("RECOGNITION_LANGUAGES", "uk-UA,ru-RU,en-US").split(",")
    if language.strip()
]
WHISPER_LANGUAGES = [
    language.strip()
    for language in os.getenv("WHISPER_LANGUAGES", "uk").split(",")
    if language.strip()
]
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
LISTEN_DURATION = float(os.getenv("LISTEN_DURATION", "12"))
IDLE_LISTEN_DURATION = float(os.getenv("IDLE_LISTEN_DURATION", "3.2"))
ACTIVE_LISTEN_DURATION = float(os.getenv("ACTIVE_LISTEN_DURATION", "7.5"))
CHUNK_DURATION = float(os.getenv("CHUNK_DURATION", "0.2"))
SILENCE_TIMEOUT = float(os.getenv("SILENCE_TIMEOUT", "0.8"))
MIN_SPEECH_DURATION = float(os.getenv("MIN_SPEECH_DURATION", "0.3"))
SPEECH_THRESHOLD = int(os.getenv("SPEECH_THRESHOLD", "250"))
PRE_ROLL_DURATION = float(os.getenv("PRE_ROLL_DURATION", "0.4"))
AMBIENT_CHUNKS = int(os.getenv("AMBIENT_CHUNKS", "6"))
DYNAMIC_THRESHOLD_MULTIPLIER = float(os.getenv("DYNAMIC_THRESHOLD_MULTIPLIER", "2.2"))
AUTO_INSTALL_STARTUP = os.getenv("AUTO_INSTALL_STARTUP", "true").lower() == "true"
