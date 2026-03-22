import pyttsx3

def speak(text):
    print("Асистент:", text)
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as error:
        print(f"Voice playback error: {error}")
