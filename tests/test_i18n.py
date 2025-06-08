import utils.i18n as i18n


def test_set_language_and_translate(monkeypatch):
    translations = {"en": {}, "ru": {"Hello": "Привет"}}
    monkeypatch.setattr(i18n, "TRANSLATIONS", translations)
    monkeypatch.setattr(i18n, "CURRENT_LANGUAGE", "en")
    called = []
    def cb():
        called.append(i18n.CURRENT_LANGUAGE)
    i18n.add_callback(cb)
    i18n.set_language("ru")
    assert i18n.CURRENT_LANGUAGE == "ru"
    assert called == ["ru"]
    assert i18n.translate("Hello") == "Привет"
    i18n.remove_callback(cb)
    i18n.set_language("en")
    assert called == ["ru"]  # callback not called after removal
    assert i18n.translate("Hello") == "Hello"


def test_set_language_invalid(monkeypatch):
    monkeypatch.setattr(i18n, "TRANSLATIONS", {"en": {}})
    monkeypatch.setattr(i18n, "CURRENT_LANGUAGE", "en")
    i18n.set_language("fr")
    assert i18n.CURRENT_LANGUAGE == "en"

