import os
import utils.window_utils as window_utils


class DummyWindow:
    def __init__(self):
        self.called_with = None

    def iconbitmap(self, path):
        self.called_with = path


def test_get_icon_path(monkeypatch):
    monkeypatch.setattr(window_utils, "resource_path", lambda *p: os.path.join("/tmp", *p))
    assert window_utils.get_icon_path() == os.path.join("/tmp", "icon", "ALLtoCEF.ico")


def test_set_window_icon_success(monkeypatch, tmp_path):
    icon_file = tmp_path / "ALLtoCEF.ico"
    icon_file.write_text("icon")
    monkeypatch.setattr(window_utils, "get_icon_path", lambda: str(icon_file))
    window = DummyWindow()
    window_utils.set_window_icon(window)
    assert window.called_with == str(icon_file)


def test_set_window_icon_no_file(monkeypatch):
    monkeypatch.setattr(window_utils, "get_icon_path", lambda: "missing.ico")
    window = DummyWindow()
    window_utils.set_window_icon(window)
    assert window.called_with is None


def test_set_window_icon_error(monkeypatch, tmp_path):
    icon_file = tmp_path / "ALLtoCEF.ico"
    icon_file.write_text("icon")
    monkeypatch.setattr(window_utils, "get_icon_path", lambda: str(icon_file))

    class ErrorWindow(DummyWindow):
        def iconbitmap(self, path):
            raise RuntimeError("fail")

    # Should not raise even if iconbitmap fails
    window_utils.set_window_icon(ErrorWindow())

