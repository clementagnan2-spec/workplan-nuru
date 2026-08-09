"""Boîtes de dialogue réutilisables : formulaire générique d'ajout/édition."""

import tkinter as tk
from tkinter import ttk


class FormDialog(tk.Toplevel):
    """
    Fenêtre modale générique construisant un formulaire à partir d'une
    liste de champs. `fields` est une liste de tuples :
        (clé, libellé, type, options)
    où type ∈ {"text", "float", "percent", "date", "choice", "multiline"}
    et options est la liste de choix pour le type "choice" (sinon None).

    Après fermeture, `self.result` contient soit None (annulé) soit un
    dict {clé: valeur}.
    """

    def __init__(self, parent, title, fields, initial: dict = None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.fields = fields
        self.initial = initial or {}
        self.result = None
        self.vars = {}

        container = ttk.Frame(self, padding=12)
        container.grid(row=0, column=0, sticky="nsew")

        canvas = tk.Canvas(container, width=460, height=min(520, 46 * len(fields) + 20), highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        for i, (key, label, ftype, options) in enumerate(fields):
            ttk.Label(inner, text=label).grid(row=i, column=0, sticky="w", padx=4, pady=4)
            value = self.initial.get(key, "")

            if ftype == "choice":
                var = tk.StringVar(value=str(value) if value is not None else "")
                widget = ttk.Combobox(inner, textvariable=var, values=options, width=32, state="readonly")
            elif ftype == "multiline":
                widget = tk.Text(inner, width=34, height=3)
                widget.insert("1.0", "" if value is None else str(value))
                var = widget
            elif ftype == "percent":
                display = "" if value in (None, "") else str(round(float(value) * 100, 2))
                var = tk.StringVar(value=display)
                widget = ttk.Entry(inner, textvariable=var, width=34)
            else:
                var = tk.StringVar(value="" if value is None else str(value))
                widget = ttk.Entry(inner, textvariable=var, width=34)

            widget.grid(row=i, column=1, sticky="w", padx=4, pady=4)
            if ftype == "date":
                ttk.Label(inner, text="(aaaa-mm-jj)", foreground="#888").grid(row=i, column=2, sticky="w")
            self.vars[key] = (ftype, var)

        btns = ttk.Frame(self, padding=(12, 0, 12, 12))
        btns.grid(row=1, column=0, sticky="e")
        ttk.Button(btns, text="Annuler", command=self._cancel).pack(side="right", padx=4)
        ttk.Button(btns, text="Enregistrer", command=self._save).pack(side="right", padx=4)

        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self._cancel())
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.wait_window(self)

    def _save(self):
        data = {}
        for key, (ftype, var) in self.vars.items():
            if ftype == "multiline":
                raw = var.get("1.0", "end").strip()
            else:
                raw = var.get().strip()

            if ftype == "float":
                data[key] = _parse_float(raw)
            elif ftype == "percent":
                data[key] = _parse_float(raw) / 100.0
            else:
                data[key] = raw if raw != "" else None

        self.result = data
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


def _parse_float(raw: str) -> float:
    if not raw:
        return 0.0
    try:
        return float(raw.replace(",", ".").replace(" ", ""))
    except ValueError:
        return 0.0


def ask_yes_no(parent, title, message) -> bool:
    from tkinter import messagebox
    return messagebox.askyesno(title, message, parent=parent)


def show_info(parent, title, message):
    from tkinter import messagebox
    messagebox.showinfo(title, message, parent=parent)


def show_error(parent, title, message):
    from tkinter import messagebox
    messagebox.showerror(title, message, parent=parent)
