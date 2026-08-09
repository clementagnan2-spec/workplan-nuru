"""Onglet d'un pays : tableau de bord + planning (Gantt) + achats."""

import tkinter as tk
from tkinter import ttk
import datetime

from .. import database as db
from .dialogs import FormDialog, ask_yes_no, show_error

CATEGORY_CHOICES = ["P", "I", "A", "C"]
STATUT_CHOICES = ["En cours", "Livré", "Annulé", "En attente"]
TYPE_PROC_CHOICES = ["National", "International"]

ACTIVITY_FORM_FIELDS = [
    ("phase", "Phase", "text", None),
    ("code", "Code (ex: A1XX)", "text", None),
    ("task", "Tâche / Activité", "text", None),
    ("assigned_to", "Assigné à", "text", None),
    ("progress", "Avancement (%)", "percent", None),
    ("start_date", "Date début", "date", None),
    ("end_date", "Date fin", "date", None),
    ("nb_pieces", "Nb pièces", "float", None),
    ("category", "Catégorie (P/I/A/C)", "choice", CATEGORY_CHOICES),
    ("cost_ni_hct", "Coût NI/HCT", "float", None),
    ("cost_tifr_usaid", "Coût TIFR-USAID", "float", None),
    ("cost_ftit", "Coût FTIT", "float", None),
    ("budget_ni_hct", "Budget NI/HCT", "float", None),
    ("budget_tifr_usaid", "Budget TIFR-USAID", "float", None),
    ("budget_ftit", "Budget FTIT", "float", None),
    ("comment", "Commentaire", "multiline", None),
]

PROCUREMENT_FORM_FIELDS = [
    ("dossier_workplan", "Code activité (workplan)", "text", None),
    ("n_pr", "N° PR", "text", None),
    ("n_rfq", "N° RFQ", "text", None),
    ("n_bc", "N° BC", "text", None),
    ("date_bc", "Date BC", "date", None),
    ("n_proforma", "N° Proforma", "text", None),
    ("demandeur", "Demandeur", "text", None),
    ("designation", "Désignation", "text", None),
    ("fournisseur", "Fournisseur", "text", None),
    ("date_fournisseur", "Date fournisseur", "date", None),
    ("montant", "Montant", "float", None),
    ("categorie", "Catégorie (P/I/A/C)", "choice", CATEGORY_CHOICES),
    ("lieu_livraison", "Lieu de livraison", "text", None),
    ("date_livraison_prevue", "Date livraison prévue", "date", None),
    ("statut_bc", "Statut du BC", "choice", STATUT_CHOICES),
    ("type_procurement", "Type (National/Intl)", "choice", TYPE_PROC_CHOICES),
    ("project", "Projet", "text", None),
    ("charge_code", "Charge code", "text", None),
    ("code", "Code", "text", None),
    ("bon_livraison", "Bon de livraison", "text", None),
    ("facture_definitive", "Facture définitive", "text", None),
    ("date_reception_facture", "Date réception facture", "date", None),
    ("rib", "RIB", "text", None),
    ("banque", "Banque du fournisseur", "text", None),
    ("mode_paiement", "Mode de paiement", "text", None),
    ("date_paiement", "Date de paiement", "date", None),
    ("validation", "Validation / Autorisation", "text", None),
    ("commentaires", "Commentaires", "multiline", None),
]


def _fmt_money(v):
    try:
        return f"{v:,.0f}".replace(",", " ")
    except (TypeError, ValueError):
        return "0"


class CountryTab(ttk.Frame):
    def __init__(self, master, conn, country_row, on_change=None):
        super().__init__(master)
        self.conn = conn
        self.country = country_row
        self.on_change = on_change or (lambda: None)

        self._build_dashboard()

        sub = ttk.Notebook(self)
        sub.pack(fill="both", expand=True, padx=6, pady=6)

        self.planning_frame = ttk.Frame(sub)
        self.procurement_frame = ttk.Frame(sub)
        sub.add(self.planning_frame, text="Planning / Gantt")
        sub.add(self.procurement_frame, text="Suivi des achats")

        self._build_planning_tab()
        self._build_procurement_tab()

        self.refresh()

    # ------------------------------------------------------------ dashboard
    def _build_dashboard(self):
        frame = ttk.LabelFrame(self, text=f"Résumé budgétaire — {self.country['name']}")
        frame.pack(fill="x", padx=6, pady=(6, 0))

        self.dash_labels = {}
        cols = ["cost_total", "budget_total", "solde"]
        titles = {"cost_total": "Dépenses totales", "budget_total": "Budget total", "solde": "Solde"}
        for i, key in enumerate(cols):
            cell = ttk.Frame(frame, padding=8)
            cell.grid(row=0, column=i, sticky="nsew")
            ttk.Label(cell, text=titles[key], font=("Segoe UI", 9, "bold")).pack(anchor="w")
            val_label = ttk.Label(cell, text="0", font=("Segoe UI", 13))
            val_label.pack(anchor="w")
            self.dash_labels[key] = val_label
            frame.columnconfigure(i, weight=1)

    def _refresh_dashboard(self):
        totals = db.country_totals(self.conn, self.country["id"])
        self.dash_labels["cost_total"].config(text=_fmt_money(totals["cost_total"]))
        self.dash_labels["budget_total"].config(text=_fmt_money(totals["budget_total"]))
        solde = totals["solde"]
        color = "#1a7f37" if solde >= 0 else "#b3261e"
        self.dash_labels["solde"].config(text=_fmt_money(solde), foreground=color)

    # ------------------------------------------------------------- planning
    def _build_planning_tab(self):
        toolbar = ttk.Frame(self.planning_frame)
        toolbar.pack(fill="x", pady=4)
        ttk.Button(toolbar, text="+ Ajouter une activité", command=self._add_activity).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Modifier", command=self._edit_activity).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Supprimer", command=self._delete_activity).pack(side="left", padx=4)

        columns = ("phase", "code", "task", "progress", "start", "end", "cost", "budget", "solde")
        headers = ["Phase", "Code", "Tâche", "Avanc.", "Début", "Fin", "Coût", "Budget", "Solde"]
        self.activity_tree = ttk.Treeview(self.planning_frame, columns=columns, show="headings", height=10)
        for c, h in zip(columns, headers):
            self.activity_tree.heading(c, text=h)
            self.activity_tree.column(c, width=100, anchor="w")
        self.activity_tree.column("task", width=220)
        self.activity_tree.pack(fill="both", expand=True, padx=4, pady=4)
        self.activity_tree.bind("<Double-1>", lambda e: self._edit_activity())

        gantt_frame = ttk.LabelFrame(self.planning_frame, text="Diagramme de Gantt")
        gantt_frame.pack(fill="both", expand=True, padx=4, pady=4)
        self.gantt_canvas = tk.Canvas(gantt_frame, bg="white", height=220)
        self.gantt_canvas.pack(fill="both", expand=True)

    def _selected_activity_id(self):
        sel = self.activity_tree.selection()
        if not sel:
            return None
        return int(sel[0])

    def _add_activity(self):
        dlg = FormDialog(self, "Ajouter une activité", ACTIVITY_FORM_FIELDS)
        if dlg.result is None:
            return
        self._save_activity(None, dlg.result)

    def _edit_activity(self):
        act_id = self._selected_activity_id()
        if act_id is None:
            return
        row = db.get_activity(self.conn, act_id)
        initial = dict(row)
        if row["phase_id"]:
            phase = self.conn.execute("SELECT name FROM phases WHERE id = ?", (row["phase_id"],)).fetchone()
            initial["phase"] = phase["name"] if phase else ""
        dlg = FormDialog(self, "Modifier l'activité", ACTIVITY_FORM_FIELDS, initial)
        if dlg.result is None:
            return
        self._save_activity(act_id, dlg.result)

    def _save_activity(self, act_id, data):
        phase_name = data.pop("phase", None)
        phase_id = None
        if phase_name:
            phase_id = db.get_or_create_phase(self.conn, self.country["id"], phase_name)
        data["phase_id"] = phase_id

        try:
            if act_id is None:
                db.add_activity(self.conn, self.country["id"], data)
            else:
                db.update_activity(self.conn, act_id, data)
        except Exception as exc:  # noqa: BLE001
            show_error(self, "Erreur", f"Impossible d'enregistrer l'activité :\n{exc}")
            return

        self.refresh()
        self.on_change()

    def _delete_activity(self):
        act_id = self._selected_activity_id()
        if act_id is None:
            return
        if ask_yes_no(self, "Confirmer", "Supprimer cette activité ?"):
            db.delete_activity(self.conn, act_id)
            self.refresh()
            self.on_change()

    def _refresh_planning(self):
        self.activity_tree.delete(*self.activity_tree.get_children())
        rows = db.list_activities(self.conn, self.country["id"])
        for r in rows:
            cost_total = r["cost_ni_hct"] + r["cost_tifr_usaid"] + r["cost_ftit"]
            budget_total = r["budget_ni_hct"] + r["budget_tifr_usaid"] + r["budget_ftit"]
            self.activity_tree.insert("", "end", iid=str(r["id"]), values=(
                r["phase_name"] or "", r["code"] or "", r["task"],
                f"{round((r['progress'] or 0) * 100)}%",
                r["start_date"] or "", r["end_date"] or "",
                _fmt_money(cost_total), _fmt_money(budget_total),
                _fmt_money(budget_total - cost_total),
            ))
        self._draw_gantt(rows)

    def _draw_gantt(self, rows):
        canvas = self.gantt_canvas
        canvas.delete("all")
        dated = [r for r in rows if r["start_date"] and r["end_date"]]
        if not dated:
            canvas.create_text(20, 20, anchor="nw", text="Aucune activité datée à afficher.")
            return

        def parse(d):
            return datetime.date.fromisoformat(d)

        min_date = min(parse(r["start_date"]) for r in dated)
        max_date = max(parse(r["end_date"]) for r in dated)
        span_days = max((max_date - min_date).days, 1)

        canvas.update_idletasks()
        width = max(canvas.winfo_width(), 600)
        left_margin = 220
        right_margin = 20
        top_margin = 10
        row_h = 22
        chart_w = max(width - left_margin - right_margin, 100)

        colors = {"P": "#4C78A8", "I": "#F58518", "A": "#54A24B", "C": "#E45756"}

        for i, r in enumerate(dated):
            y = top_margin + i * row_h
            label = f"{r['code'] or ''} {r['task']}"[:34]
            canvas.create_text(4, y + row_h / 2, anchor="w", text=label, font=("Segoe UI", 8))

            start_off = (parse(r["start_date"]) - min_date).days
            duration = max((parse(r["end_date"]) - parse(r["start_date"])).days, 1)
            x0 = left_margin + (start_off / span_days) * chart_w
            x1 = left_margin + ((start_off + duration) / span_days) * chart_w
            color = colors.get(r["category"], "#4C78A8")
            canvas.create_rectangle(x0, y + 3, x1, y + row_h - 3, fill=color, outline="")

            progress = r["progress"] or 0
            if progress > 0:
                px = x0 + (x1 - x0) * progress
                canvas.create_rectangle(x0, y + row_h - 6, px, y + row_h - 3, fill="#1a3d5c", outline="")

        total_h = top_margin + len(dated) * row_h + 20
        canvas.configure(scrollregion=(0, 0, width, total_h), height=min(max(total_h, 120), 400))

    # ---------------------------------------------------------- procurement
    def _build_procurement_tab(self):
        toolbar = ttk.Frame(self.procurement_frame)
        toolbar.pack(fill="x", pady=4)
        ttk.Button(toolbar, text="+ Ajouter un achat", command=self._add_procurement).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Modifier", command=self._edit_procurement).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Supprimer", command=self._delete_procurement).pack(side="left", padx=4)

        columns = ("code", "n_bc", "designation", "fournisseur", "montant", "statut", "paiement")
        headers = ["Code", "N° BC", "Désignation", "Fournisseur", "Montant", "Statut", "Paiement"]
        self.procurement_tree = ttk.Treeview(self.procurement_frame, columns=columns, show="headings", height=16)
        for c, h in zip(columns, headers):
            self.procurement_tree.heading(c, text=h)
            self.procurement_tree.column(c, width=110, anchor="w")
        self.procurement_tree.column("designation", width=240)
        self.procurement_tree.pack(fill="both", expand=True, padx=4, pady=4)
        self.procurement_tree.bind("<Double-1>", lambda e: self._edit_procurement())

    def _selected_procurement_id(self):
        sel = self.procurement_tree.selection()
        if not sel:
            return None
        return int(sel[0])

    def _add_procurement(self):
        dlg = FormDialog(self, "Ajouter un achat", PROCUREMENT_FORM_FIELDS)
        if dlg.result is None:
            return
        try:
            db.add_procurement(self.conn, self.country["id"], dlg.result)
        except Exception as exc:  # noqa: BLE001
            show_error(self, "Erreur", f"Impossible d'enregistrer l'achat :\n{exc}")
            return
        self.refresh()

    def _edit_procurement(self):
        proc_id = self._selected_procurement_id()
        if proc_id is None:
            return
        row = db.get_procurement(self.conn, proc_id)
        dlg = FormDialog(self, "Modifier l'achat", PROCUREMENT_FORM_FIELDS, dict(row))
        if dlg.result is None:
            return
        try:
            db.update_procurement(self.conn, proc_id, dlg.result)
        except Exception as exc:  # noqa: BLE001
            show_error(self, "Erreur", f"Impossible d'enregistrer l'achat :\n{exc}")
            return
        self.refresh()

    def _delete_procurement(self):
        proc_id = self._selected_procurement_id()
        if proc_id is None:
            return
        if ask_yes_no(self, "Confirmer", "Supprimer cet achat ?"):
            db.delete_procurement(self.conn, proc_id)
            self.refresh()

    def _refresh_procurement(self):
        self.procurement_tree.delete(*self.procurement_tree.get_children())
        for p in db.list_procurements(self.conn, self.country["id"]):
            self.procurement_tree.insert("", "end", iid=str(p["id"]), values=(
                p["dossier_workplan"] or "", p["n_bc"] or "", p["designation"] or "",
                p["fournisseur"] or "", _fmt_money(p["montant"]), p["statut_bc"] or "",
                p["validation"] or "",
            ))

    # ------------------------------------------------------------- general
    def refresh(self):
        self._refresh_dashboard()
        self._refresh_planning()
        self._refresh_procurement()
