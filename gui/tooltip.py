
import tkinter as tk
from utils.window_utils import set_window_icon


class ToolTip:
    def __init__(self, widget, delay=500):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.delay = delay
        self.text = None
        self.pos = (0, 0)
        self.label = None

    def showtip(self, text, x, y):
        if self.tipwindow or not text:
            return
        self.text = text
        self.pos = (x, y)
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.withdraw()
        tw.wm_overrideredirect(1)
        set_window_icon(tw)
        tw.wm_geometry(f"+{x+10}+{y+10}")
        self.label = tk.Label(
            tw,
            text=text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("tahoma", "8", "normal"),
        )
        self.label.pack(ipadx=1)
        tw.deiconify()

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
        self.tipwindow = None
        self.text = None
        self.label = None

    def schedule(self, text, x, y):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

        if self.tipwindow:
            self.pos = (x, y)
            self.tipwindow.wm_geometry(f"+{x+10}+{y+10}")
            if self.text != text and self.label:
                self.text = text
                self.label.config(text=text)
        else:
            self.id = self.widget.after(self.delay, self.showtip, text, x, y)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        self.hidetip()

