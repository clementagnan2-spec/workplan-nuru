"""Point d'entrée de Nuru Workplan Manager (fonction `main` réutilisable)."""

import sys
import traceback
import tkinter as tk
from tkinter import messagebox


def main():
    from .gui.app_window import AppWindow

    app = AppWindow()
    app.mainloop()


def run_safely():
    try:
        main()
    except Exception:  # noqa: BLE001
        err = traceback.format_exc()
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Erreur au démarrage", err)
        except Exception:  # noqa: BLE001
            print(err)
        sys.exit(1)
