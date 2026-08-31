"""Fenêtre "Référentiels" : gérer les listes de valeurs utilisées dans les
formulaires (codes d'activité, catégories, lignes budgétaires/bailleurs,
codes de charge)."""

import tkinter as tk
from tkinter import ttk

from .. import database as db
from .dialogs import FormDialog, ask_yes_no, show_error

TABS = [
    ("activity_codes", "Codes d'activité", "Code", "Libellé"),
    ("categories", "Catégories", "Code", "Libellé"),
    ("budget_lines", "Budget (bailleurs)", "Nom", "Libellé"),
    ("charge_codes", "Codes de charge", "Code", "Libellé"),
]


class ReferentialsWindow(tk.Toplevel):
    def __init__(self, parent, conn, on_change=None):
        super().__init__(parent)
        self.conn = conn
        self.on_change = on_change or (lambda: None)
        self.title("Référentiels")
        self.geometry("560x520")
        self.minsize(420, 360)

        ttk.Label(
            self, text="Gérez ici les listes utilisées dans les formulaires "
                       "d'activité et d'achat.",
            padding=(10, 8, 10, 0), foreground="#555",
        ).pack(anchor="w")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.panels = {}
        for table, title, col1, col2 in TABS:
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=title)
            panel = _ReferentialPanel(frame, self.conn, table, col1, col2, self._changed)
            panel.pack(fill="both", expand=True)
            self.panels[table] = panel

    def _changed(self):
        self.on_change()


class _ReferentialPanel(ttk.Frame):
    def __init__(self, master, conn, table, col1_label, col2_label, on_change):
        super().__init__(master)
        self.conn = conn
        self.table = table
        self.col1_label = col1_label
        self.col2_label = col2_label
        self.on_change = on_change

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=6)
        ttk.Button(toolbar, text="+ Ajouter", command=self._add).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Modifier", command=self._edit).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Supprimer", command=self._delete).pack(side="left", padx=4)

        self.tree = ttk.Treeview(self, columns=("value", "label"), show="headings", height=14)
        self.tree.heading("value", text=col1_label)
        self.tree.heading("label", text=col2_label)
        self.tree.column("value", width=160, anchor="w")
        self.tree.column("label", width=280, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=4)
        self.tree.bind("<Double-1>", lambda e: self._edit())

        self.refresh()

    def _fields(self):
        return [
            ("value", self.col1_label, "text", None),
            ("label", self.col2_label, "text", None),
        ]

    def _selected_id(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _add(self):
        dlg = FormDialog(self, f"Ajouter — {self.col1_label}", self._fields())
        if dlg.result is None:
            return
        value = dlg.result.get("value")
        if not value:
            show_error(self, "Erreur", f"Le champ « {self.col1_label} » est obligatoire.")
            return
        try:
            db.add_referential(self.conn, self.table, value, dlg.result.get("label"))
        except Exception as exc:  # noqa: BLE001
            show_error(self, "Erreur", f"Impossible d'ajouter cette valeur :\n{exc}")
            return
        self.refresh()
        self.on_change()

    def _edit(self):
        item_id = self._selected_id()
        if item_id is None:
            return
        row = self.conn.execute(f"SELECT * FROM {self.table} WHERE id = ?", (item_id,)).fetchone()
        key = db.REFERENTIAL_TABLES[self.table]
        initial = {"value": row[key], "label": row["label"]}
        dlg = FormDialog(self, f"Modifier — {self.col1_label}", self._fields(), initial)
        if dlg.result is None:
            return
        value = dlg.result.get("value")
        if not value:
            show_error(self, "Erreur", f"Le champ « {self.col1_label} » est obligatoire.")
            return
        try:
            db.update_referential(self.conn, self.table, item_id, value, dlg.result.get("label"))
        except Exception as exc:  # noqa: BLE001
            show_error(self, "Erreur", f"Impossible de modifier cette valeur :\n{exc}")
            return
        self.refresh()
        self.on_change()

    def _delete(self):
        item_id = self._selected_id()
        if item_id is None:
            return
        if ask_yes_no(self, "Confirmer", "Supprimer cette valeur du référentiel ?\n"
                                          "(les activités/achats qui l'utilisent déjà ne sont pas modifiés)"):
            db.delete_referential(self.conn, self.table, item_id)
            self.refresh()
            self.on_change()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for row in db.list_referential(self.conn, self.table):
            key = db.REFERENTIAL_TABLES[self.table]
            self.tree.insert("", "end", iid=str(row["id"]), values=(row[key], row["label"] or ""))
