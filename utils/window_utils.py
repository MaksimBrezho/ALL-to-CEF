import os
import tkinter as tk
from utils.json_utils import resource_path


def get_icon_path() -> str:
    """Return the absolute path to the application icon."""
    return resource_path("icon", "ALLtoCEF.ico")


def set_window_icon(window: tk.Misc) -> None:
    """Apply the application icon to the given Tkinter window."""
    icon_path = get_icon_path()
    if os.path.exists(icon_path):
        try:
            window.iconbitmap(icon_path)
        except Exception:
            pass
