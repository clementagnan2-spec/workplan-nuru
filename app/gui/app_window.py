"""Fenêtre principale : menu, onglet Consolidation + un onglet par pays."""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog

from .. import database as db
from .. import excel_import
from .. import excel_export
from .. import sample_data
from .country_tab import CountryTab
from .reports_window import ReportsWindow
from .referentials_window import ReferentialsWindow
from .dialogs import show_info, show_error, ask_yes_no

APP_TITLE = "Nuru Workplan Manager"


def _fmt_money(v):
    try:
        return f"{v:,.0f}".replace(",", " ")
    except (TypeError, ValueError):
        return "0"


class AppWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(900, 600)

        self.conn = db.connect()

        self._build_menu()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.consolidation_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.consolidation_frame, text="Consolidation")
        self._build_consolidation_tab()

        self.country_tabs = {}
        self._build_country_tabs()

        self.status_var = tk.StringVar(value=f"Base de données : {db.default_db_path()}")
        status_bar = ttk.Label(self, textvariable=self.status_var, anchor="w", relief="sunken")
        status_bar.pack(fill="x", side="bottom")

        self.refresh_all()

    # ---------------------------------------------------------------- menu
    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Importer un classeur Excel...", command=self._import_excel)
        file_menu.add_command(label="Exporter vers Excel...", command=self._export_excel)
        file_menu.add_separator()
        file_menu.add_command(label="Charger des données d'exemple", command=self._load_sample_data)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.destroy)
        menubar.add_cascade(label="Fichier", menu=file_menu)

        reports_menu = tk.Menu(menubar, tearoff=0)
        reports_menu.add_command(label="Ouvrir les rapports...", command=self._open_reports)
        menubar.add_cascade(label="Rapports", menu=reports_menu)

        ref_menu = tk.Menu(menubar, tearoff=0)
        ref_menu.add_command(
            label="Codes activité, catégories, budget, codes de charge...",
            command=self._open_referentials,
        )
        menubar.add_cascade(label="Référentiels", menu=ref_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="À propos", command=self._show_about)
        menubar.add_cascade(label="Aide", menu=help_menu)

        self.config(menu=menubar)

    # --------------------------------------------------------- consolidation
    def _build_consolidation_tab(self):
        ttk.Label(
            self.consolidation_frame,
            text="Vue consolidée multi-pays",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w", padx=12, pady=(12, 4))

        columns = ("country", "cost", "budget", "solde")
        headers = ["Pays", "Coût total", "Budget total", "Solde"]
        self.consolidation_tree = ttk.Treeview(
            self.consolidation_frame, columns=columns, show="headings", height=8
        )
        for c, h in zip(columns, headers):
            self.consolidation_tree.heading(c, text=h)
            self.consolidation_tree.column(c, width=180, anchor="w")
        self.consolidation_tree.pack(fill="x", padx=12, pady=8)

        ttk.Label(
            self.consolidation_frame,
            text="Utilisez le menu Fichier > Importer un classeur Excel pour charger vos données\n"
                 "à partir d'un fichier WORKPLAN_MULTIPAYS (.xlsx), ou ajoutez des activités\n"
                 "directement dans l'onglet de chaque pays.",
            foreground="#666",
            justify="left",
        ).pack(anchor="w", padx=12, pady=8)

    def _refresh_consolidation(self):
        self.consolidation_tree.delete(*self.consolidation_tree.get_children())
        for country in db.list_countries(self.conn):
            totals = db.country_totals(self.conn, country["id"])
            self.consolidation_tree.insert("", "end", values=(
                country["name"], _fmt_money(totals["cost_total"]),
                _fmt_money(totals["budget_total"]), _fmt_money(totals["solde"]),
            ))

    # ------------------------------------------------------------ countries
    def _build_country_tabs(self):
        for country in db.list_countries(self.conn):
            tab = CountryTab(self.notebook, self.conn, country, on_change=self._refresh_consolidation)
            self.notebook.add(tab, text=country["name"].title())
            self.country_tabs[country["name"]] = tab

    def refresh_all(self):
        self._refresh_consolidation()
        for tab in self.country_tabs.values():
            tab.refresh()

    # ------------------------------------------------------------- actions
    def _import_excel(self):
        path = filedialog.askopenfilename(
            title="Choisir un classeur Excel à importer",
            filetypes=[("Classeurs Excel", "*.xlsx *.xlsm"), ("Tous les fichiers", "*.*")],
        )
        if not path:
            return

        self.status_var.set(f"Import en cours depuis {os.path.basename(path)}...")
        self.update_idletasks()

        def worker():
            try:
                summary = excel_import.import_workbook(self.conn, path, progress_callback=self._set_status_threadsafe)
            except Exception as exc:  # noqa: BLE001
                self.after(0, lambda: show_error(self, "Erreur d'import", str(exc)))
                self.after(0, lambda: self.status_var.set("Import échoué."))
                return

            def done():
                self.refresh_all()
                lines = [f"{c} : {d.get('activities', 0)} activités, {d.get('procurements', 0)} achats"
                         for c, d in summary.items()]
                show_info(self, "Import terminé", "Import réussi :\n" + "\n".join(lines) if lines else
                          "Aucune feuille reconnue n'a été trouvée dans ce classeur.")
                self.status_var.set(f"Base de données : {db.default_db_path()}")

            self.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    def _set_status_threadsafe(self, text):
        self.after(0, lambda: self.status_var.set(text))

    def _export_excel(self):
        path = filedialog.asksaveasfilename(
            title="Exporter vers un classeur Excel",
            defaultextension=".xlsx",
            filetypes=[("Classeur Excel", "*.xlsx")],
            initialfile="nuru_workplan_export.xlsx",
        )
        if not path:
            return
        try:
            excel_export.export_workbook(self.conn, path)
        except Exception as exc:  # noqa: BLE001
            show_error(self, "Erreur d'export", str(exc))
            return
        show_info(self, "Export terminé", f"Le fichier a été enregistré :\n{path}")

    def _load_sample_data(self):
        clear = ask_yes_no(
            self, "Données d'exemple",
            "Cela va ajouter des activités et achats fictifs dans les 4 pays "
            "(Togo, Bénin, Niger, Ghana) pour découvrir l'application.\n\n"
            "Voulez-vous d'abord effacer les données existantes de ces pays ?\n\n"
            "Oui = remplacer • Non = ajouter en plus des données actuelles",
        )

        try:
            summary = sample_data.load_sample_data(self.conn, clear_existing=clear)
        except Exception as exc:  # noqa: BLE001
            show_error(self, "Erreur", str(exc))
            return

        self.refresh_all()
        lines = [f"{c} : {d['activities']} activités, {d['procurements']} achats"
                 for c, d in summary.items()]
        show_info(self, "Données d'exemple chargées", "\n".join(lines))

    def _open_reports(self):
        ReportsWindow(self, self.conn)

    def _open_referentials(self):
        ReferentialsWindow(self, self.conn, on_change=self._refresh_consolidation)

    def _show_about(self):
        show_info(
            self, "À propos",
            f"{APP_TITLE}\n\n"
            "Suivi de planning, budget et achats multi-pays.\n"
            "Développé pour Nuru — Burkina Faso et pays voisins.\n\n"
            f"Base de données locale :\n{db.default_db_path()}",
        )
