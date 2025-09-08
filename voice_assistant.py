import speech_recognition as sr

def transcribe_voice_input():
    """
    Transcribes audio input from the user's microphone to text.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        try:
            audio = r.listen(source, timeout=5)
            text = r.recognize_google(audio)
            return text
        except sr.WaitTimeoutError:
            return "Error: Listening timed out. Please try again."
        except sr.UnknownValueError:
            return "Error: Could not understand audio. Please try again."
        except sr.RequestError:
            return "Error: Speech recognition service unavailable."
        except Exception as e:
            return f"Error: {str(e)}"