import json
import os

CURRENT_LANGUAGE = 'en'

TRANSLATIONS = {
    'en': {},
    'ru': {}
}

def load_translations():
    global TRANSLATIONS
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'translations.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            TRANSLATIONS['ru'] = json.load(f)

load_translations()

CALLBACKS = []

def set_language(lang: str):
    global CURRENT_LANGUAGE
    if lang in TRANSLATIONS:
        CURRENT_LANGUAGE = lang
        for cb in list(CALLBACKS):
            try:
                cb()
            except Exception:
                pass


def translate(text: str) -> str:
    return TRANSLATIONS.get(CURRENT_LANGUAGE, {}).get(text, text)

def add_callback(cb):
    CALLBACKS.append(cb)

def remove_callback(cb):
    if cb in CALLBACKS:
        CALLBACKS.remove(cb)
