import tkinter as tk
from gui.app_window import AppWindow
from utils.window_utils import set_window_icon
from utils.i18n import translate as _

def main():
    root = tk.Tk()
    root.title(_("LogParserHelper"))
    root.geometry("1000x700")

    set_window_icon(root)

    app = AppWindow(master=root)
    app.pack(fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()
