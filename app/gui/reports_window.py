"""Fenêtre "Rapports" : vues transversales par activité, par budget ou par
code de charge, avec filtre pays et export Excel du rapport affiché."""

import tkinter as tk
from tkinter import ttk, filedialog

from .. import database as db
from .dialogs import show_info, show_error

REPORT_CATEGORY = "Par catégorie"
REPORT_BUDGET = "Par budget (bailleur)"
REPORT_CHARGE_CODE = "Par code de charge"

REPORT_TYPES = [REPORT_CATEGORY, REPORT_BUDGET, REPORT_CHARGE_CODE]


def _fmt_money(v):
    try:
        return f"{v:,.0f}".replace(",", " ")
    except (TypeError, ValueError):
        return "0"


class ReportsWindow(tk.Toplevel):
    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        self.title("Rapports")
        self.geometry("1000x600")
        self.minsize(700, 400)

        self._build_toolbar()
        self._build_table()

        self.report_var.set(REPORT_CATEGORY)
        self.country_var.set("Tous les pays")
        self.refresh()

    # ------------------------------------------------------------- toolbar
    def _build_toolbar(self):
        bar = ttk.Frame(self, padding=8)
        bar.pack(fill="x")

        ttk.Label(bar, text="Rapport :").pack(side="left", padx=(0, 4))
        self.report_var = tk.StringVar()
        report_combo = ttk.Combobox(
            bar, textvariable=self.report_var, values=REPORT_TYPES,
            state="readonly", width=26,
        )
        report_combo.pack(side="left", padx=(0, 16))
        report_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Label(bar, text="Pays :").pack(side="left", padx=(0, 4))
        self.country_var = tk.StringVar()
        countries = ["Tous les pays"] + [c["name"] for c in db.list_countries(self.conn)]
        country_combo = ttk.Combobox(
            bar, textvariable=self.country_var, values=countries,
            state="readonly", width=18,
        )
        country_combo.pack(side="left")
        country_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Button(bar, text="Exporter ce rapport (.xlsx)", command=self._export_report).pack(side="right")

    def _selected_country_id(self):
        name = self.country_var.get()
        if not name or name == "Tous les pays":
            return None
        row = self.conn.execute("SELECT id FROM countries WHERE name = ?", (name,)).fetchone()
        return row["id"] if row else None

    # --------------------------------------------------------------- table
    def _build_table(self):
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.tree = None  # (re)créé selon le rapport sélectionné, colonnes différentes

    def _make_tree(self, columns, headers, widths=None):
        if self.tree is not None:
            self.tree.destroy()
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings")
        for i, (c, h) in enumerate(zip(columns, headers)):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=(widths[i] if widths else 120), anchor="w")
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    # ------------------------------------------------------------- refresh
    def refresh(self):
        report = self.report_var.get()
        country_id = self._selected_country_id()

        if report == REPORT_CATEGORY:
            self._show_category_report(country_id)
        elif report == REPORT_BUDGET:
            self._show_budget_report(country_id)
        elif report == REPORT_CHARGE_CODE:
            self._show_charge_code_report(country_id)

    def _show_category_report(self, country_id):
        columns = ("country", "category", "n_activites", "cost", "budget", "solde")
        headers = ["Pays", "Catégorie", "Nb activités", "Coût total", "Budget total", "Solde"]
        widths = [110, 180, 100, 130, 130, 130]
        self._make_tree(columns, headers, widths)

        for row in db.activities_by_category(self.conn, country_id):
            self.tree.insert("", "end", values=(
                row["country_name"], row["category_label"], row["n_activites"],
                _fmt_money(row["cost_total"]), _fmt_money(row["budget_total"]),
                _fmt_money(row["solde"]),
            ))

    def _show_budget_report(self, country_id):
        columns = ("country", "donor", "cost", "budget", "solde")
        headers = ["Pays", "Bailleur", "Coût", "Budget", "Solde"]
        widths = [110, 140, 130, 130, 130]
        self._make_tree(columns, headers, widths)

        for row in db.budget_by_donor(self.conn, country_id):
            tags = ("total",) if row["donor"] == "TOTAL" else ()
            self.tree.insert("", "end", values=(
                row["country"], row["donor"], _fmt_money(row["cost"]),
                _fmt_money(row["budget"]), _fmt_money(row["solde"]),
            ), tags=tags)
        self.tree.tag_configure("total", font=("Segoe UI", 9, "bold"))

    def _show_charge_code_report(self, country_id):
        columns = ("country", "charge_code", "n_achats", "montant")
        headers = ["Pays", "Code de charge", "Nb achats", "Montant total"]
        widths = [110, 200, 100, 140]
        self._make_tree(columns, headers, widths)

        for row in db.procurement_by_charge_code(self.conn, country_id):
            self.tree.insert("", "end", values=(
                row["country_name"], row["charge_code"], row["n_achats"],
                _fmt_money(row["montant_total"]),
            ))

    # -------------------------------------------------------------- export
    def _export_report(self):
        if self.tree is None or not self.tree.get_children():
            show_info(self, "Rapport vide", "Aucune donnée à exporter pour ce rapport.")
            return

        path = filedialog.asksaveasfilename(
            title="Exporter le rapport",
            defaultextension=".xlsx",
            filetypes=[("Classeur Excel", "*.xlsx")],
            initialfile=f"rapport_{self.report_var.get().lower().replace(' ', '_')}.xlsx",
        )
        if not path:
            return

        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Rapport"

            headers = [self.tree.heading(c)["text"] for c in self.tree["columns"]]
            for col, h in enumerate(headers, start=1):
                cell = ws.cell(row=1, column=col, value=h)
                cell.font = Font(color="FFFFFF", bold=True)
                cell.fill = PatternFill("solid", fgColor="1F4E78")

            for r_idx, item in enumerate(self.tree.get_children(), start=2):
                values = self.tree.item(item, "values")
                for col, v in enumerate(values, start=1):
                    ws.cell(row=r_idx, column=col, value=v)

            for col in range(1, len(headers) + 1):
                ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 18

            wb.save(path)
        except Exception as exc:  # noqa: BLE001
            show_error(self, "Erreur d'export", str(exc))
            return

        show_info(self, "Export terminé", f"Le rapport a été enregistré :\n{path}")
