from googletrans import Translator

def translate_text(text, dest_lang):
    """
    Translates text to the specified destination language.
    """
    if not text or dest_lang == "en":
        return text
    
    translator = Translator()
    try:
        translated = translator.translate(text, dest=dest_lang)
        return translated.text
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def get_language_code(language):
    """
    Returns the ISO 639-1 code for a given language name.
    """
    lang_map = {
        "English": "en",
        "Spanish": "es",
        "French": "fr",
        "Hindi": "hi",
        "Bengali": "bn",
        "Tamil": "ta",
        "Telugu": "te",
        "Malayalam": "ml",
        "Kannada": "kn"
    }
    return lang_map.get(language, "en")