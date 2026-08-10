"""
Couche d'accès aux données (SQLite) pour Nuru Workplan Manager.

La base est stockée dans un unique fichier .db à côté de l'exécutable
(ou dans le dossier de données utilisateur). Toutes les fonctions de ce
module prennent une connexion sqlite3 en premier argument.
"""

import sqlite3
import os
import sys
from datetime import date

DEFAULT_COUNTRIES = ["TOGO", "BENIN", "NIGER", "GHANA"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS countries (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS phases (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    country_id  INTEGER NOT NULL REFERENCES countries(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    position    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS activities (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    country_id          INTEGER NOT NULL REFERENCES countries(id) ON DELETE CASCADE,
    phase_id            INTEGER REFERENCES phases(id) ON DELETE SET NULL,
    code                TEXT,
    task                TEXT NOT NULL,
    assigned_to         TEXT,
    progress            REAL DEFAULT 0,        -- 0..1
    start_date          TEXT,                  -- ISO yyyy-mm-dd
    end_date            TEXT,                  -- ISO yyyy-mm-dd
    nb_pieces           REAL DEFAULT 0,
    category             TEXT,                  -- P / I / A / C
    cost_ni_hct         REAL DEFAULT 0,
    cost_tifr_usaid     REAL DEFAULT 0,
    cost_ftit           REAL DEFAULT 0,
    budget_ni_hct       REAL DEFAULT 0,
    budget_tifr_usaid   REAL DEFAULT 0,
    budget_ftit         REAL DEFAULT 0,
    comment             TEXT
);

CREATE TABLE IF NOT EXISTS procurements (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    country_id              INTEGER NOT NULL REFERENCES countries(id) ON DELETE CASCADE,
    dossier_workplan        TEXT,
    n_pr                    TEXT,
    n_rfq                   TEXT,
    n_bc                    TEXT,
    date_bc                 TEXT,
    n_proforma              TEXT,
    demandeur                TEXT,
    designation              TEXT,
    fournisseur              TEXT,
    date_fournisseur         TEXT,
    montant                  REAL DEFAULT 0,
    categorie                TEXT,              -- P / I / A / C
    lieu_livraison           TEXT,
    date_livraison_prevue    TEXT,
    statut_bc                TEXT,
    type_procurement         TEXT,              -- National / International
    project                  TEXT,
    charge_code              TEXT,
    code                     TEXT,
    bon_livraison            TEXT,
    facture_definitive       TEXT,
    date_reception_facture   TEXT,
    rib                      TEXT,
    banque                   TEXT,
    mode_paiement            TEXT,
    date_paiement            TEXT,
    validation               TEXT,
    commentaires             TEXT
);

CREATE TABLE IF NOT EXISTS activity_codes (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    code    TEXT UNIQUE NOT NULL,
    label   TEXT
);

CREATE TABLE IF NOT EXISTS categories (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    code    TEXT UNIQUE NOT NULL,
    label   TEXT
);

CREATE TABLE IF NOT EXISTS budget_lines (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT UNIQUE NOT NULL,
    label   TEXT
);

CREATE TABLE IF NOT EXISTS charge_codes (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    code    TEXT UNIQUE NOT NULL,
    label   TEXT
);
"""


def get_app_data_dir() -> str:
    """Retourne un dossier écrivable pour stocker la base de données,
    que l'app soit lancée en .py ou compilée en .exe (PyInstaller)."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~")
    data_dir = os.path.join(base, "NuruWorkplanManager")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def default_db_path() -> str:
    return os.path.join(get_app_data_dir(), "nuru_workplan.db")


def connect(db_path: str = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = default_db_path()
    # check_same_thread=False : l'import Excel s'exécute dans un thread
    # d'arrière-plan (pour ne pas geler l'interface) et doit pouvoir
    # utiliser la même connexion que le thread principal.
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA)
    _seed_countries(conn)
    _seed_referentials(conn)
    conn.commit()
    return conn


def _seed_countries(conn: sqlite3.Connection):
    for name in DEFAULT_COUNTRIES:
        conn.execute(
            "INSERT OR IGNORE INTO countries(name) VALUES (?)", (name,)
        )


# ------------------------------------------------------------- référentiels
# Listes de valeurs modifiables par l'utilisateur (menu "Référentiels") :
# codes d'activité, catégories, lignes budgétaires (bailleurs), codes de charge.
REFERENTIAL_TABLES = {
    "activity_codes": "code",
    "categories": "code",
    "budget_lines": "name",
    "charge_codes": "code",
}

_DEFAULT_REFERENTIALS = {
    "categories": [
        ("P", "Programme"),
        ("I", "Sensibilisation"),
        ("A", "Admin"),
        ("C", "Collecte"),
    ],
    "budget_lines": [
        ("NI/HCT", "NI/HCT"),
        ("TIFR-USAID", "TIFR-USAID"),
        ("FTIT", "FTIT"),
    ],
}


def _seed_referentials(conn: sqlite3.Connection):
    for table, items in _DEFAULT_REFERENTIALS.items():
        key = REFERENTIAL_TABLES[table]
        for value, label in items:
            conn.execute(
                f"INSERT OR IGNORE INTO {table} ({key}, label) VALUES (?, ?)",
                (value, label),
            )


def list_referential(conn, table: str):
    key = REFERENTIAL_TABLES[table]
    return conn.execute(f"SELECT * FROM {table} ORDER BY {key}").fetchall()


def referential_values(conn, table: str):
    """Liste simple des codes/noms (pour peupler les listes déroulantes)."""
    key = REFERENTIAL_TABLES[table]
    rows = conn.execute(f"SELECT {key} FROM {table} ORDER BY {key}").fetchall()
    return [r[0] for r in rows]


def add_referential(conn, table: str, value: str, label: str = None) -> int:
    key = REFERENTIAL_TABLES[table]
    cur = conn.execute(
        f"INSERT INTO {table} ({key}, label) VALUES (?, ?)", (value, label)
    )
    conn.commit()
    return cur.lastrowid


def update_referential(conn, table: str, item_id: int, value: str, label: str = None):
    key = REFERENTIAL_TABLES[table]
    conn.execute(
        f"UPDATE {table} SET {key} = ?, label = ? WHERE id = ?", (value, label, item_id)
    )
    conn.commit()


def delete_referential(conn, table: str, item_id: int):
    conn.execute(f"DELETE FROM {table} WHERE id = ?", (item_id,))
    conn.commit()


# ---------------------------------------------------------------- countries
def list_countries(conn):
    return conn.execute("SELECT * FROM countries ORDER BY id").fetchall()


def get_or_create_country(conn, name: str) -> int:
    row = conn.execute(
        "SELECT id FROM countries WHERE name = ?", (name.upper(),)
    ).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO countries(name) VALUES (?)", (name.upper(),))
    conn.commit()
    return cur.lastrowid


# ------------------------------------------------------------------ phases
def get_or_create_phase(conn, country_id: int, name: str, position: int = 0) -> int:
    row = conn.execute(
        "SELECT id FROM phases WHERE country_id = ? AND name = ?",
        (country_id, name),
    ).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO phases(country_id, name, position) VALUES (?, ?, ?)",
        (country_id, name, position),
    )
    conn.commit()
    return cur.lastrowid


def list_phases(conn, country_id: int):
    return conn.execute(
        "SELECT * FROM phases WHERE country_id = ? ORDER BY position, id",
        (country_id,),
    ).fetchall()


# -------------------------------------------------------------- activities
ACTIVITY_FIELDS = [
    "phase_id", "code", "task", "assigned_to", "progress", "start_date",
    "end_date", "nb_pieces", "category", "cost_ni_hct", "cost_tifr_usaid",
    "cost_ftit", "budget_ni_hct", "budget_tifr_usaid", "budget_ftit", "comment",
]


def list_activities(conn, country_id: int):
    return conn.execute(
        "SELECT a.*, p.name AS phase_name FROM activities a "
        "LEFT JOIN phases p ON p.id = a.phase_id "
        "WHERE a.country_id = ? ORDER BY p.position, a.start_date, a.id",
        (country_id,),
    ).fetchall()


def get_activity(conn, activity_id: int):
    return conn.execute(
        "SELECT * FROM activities WHERE id = ?", (activity_id,)
    ).fetchone()


def add_activity(conn, country_id: int, data: dict) -> int:
    cols = ["country_id"] + [f for f in ACTIVITY_FIELDS if f in data]
    placeholders = ", ".join(["?"] * len(cols))
    values = [country_id] + [data[f] for f in cols[1:]]
    cur = conn.execute(
        f"INSERT INTO activities ({', '.join(cols)}) VALUES ({placeholders})",
        values,
    )
    conn.commit()
    return cur.lastrowid


def update_activity(conn, activity_id: int, data: dict):
    fields = [f for f in ACTIVITY_FIELDS if f in data]
    if not fields:
        return
    set_clause = ", ".join(f"{f} = ?" for f in fields)
    values = [data[f] for f in fields] + [activity_id]
    conn.execute(f"UPDATE activities SET {set_clause} WHERE id = ?", values)
    conn.commit()


def delete_activity(conn, activity_id: int):
    conn.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
    conn.commit()


# ------------------------------------------------------------ procurements
PROCUREMENT_FIELDS = [
    "dossier_workplan", "n_pr", "n_rfq", "n_bc", "date_bc", "n_proforma",
    "demandeur", "designation", "fournisseur", "date_fournisseur", "montant",
    "categorie", "lieu_livraison", "date_livraison_prevue", "statut_bc",
    "type_procurement", "project", "charge_code", "code", "bon_livraison",
    "facture_definitive", "date_reception_facture", "rib", "banque",
    "mode_paiement", "date_paiement", "validation", "commentaires",
]


def list_procurements(conn, country_id: int):
    return conn.execute(
        "SELECT * FROM procurements WHERE country_id = ? ORDER BY id",
        (country_id,),
    ).fetchall()


def get_procurement(conn, proc_id: int):
    return conn.execute(
        "SELECT * FROM procurements WHERE id = ?", (proc_id,)
    ).fetchone()


def add_procurement(conn, country_id: int, data: dict) -> int:
    cols = ["country_id"] + [f for f in PROCUREMENT_FIELDS if f in data]
    placeholders = ", ".join(["?"] * len(cols))
    values = [country_id] + [data[f] for f in cols[1:]]
    cur = conn.execute(
        f"INSERT INTO procurements ({', '.join(cols)}) VALUES ({placeholders})",
        values,
    )
    conn.commit()
    return cur.lastrowid


def update_procurement(conn, proc_id: int, data: dict):
    fields = [f for f in PROCUREMENT_FIELDS if f in data]
    if not fields:
        return
    set_clause = ", ".join(f"{f} = ?" for f in fields)
    values = [data[f] for f in fields] + [proc_id]
    conn.execute(f"UPDATE procurements SET {set_clause} WHERE id = ?", values)
    conn.commit()


def delete_procurement(conn, proc_id: int):
    conn.execute("DELETE FROM procurements WHERE id = ?", (proc_id,))
    conn.commit()


# --------------------------------------------------------------- dashboard
def country_totals(conn, country_id: int) -> dict:
    row = conn.execute(
        """
        SELECT
            COALESCE(SUM(cost_ni_hct), 0)        AS cost_ni_hct,
            COALESCE(SUM(cost_tifr_usaid), 0)    AS cost_tifr_usaid,
            COALESCE(SUM(cost_ftit), 0)          AS cost_ftit,
            COALESCE(SUM(budget_ni_hct), 0)      AS budget_ni_hct,
            COALESCE(SUM(budget_tifr_usaid), 0)  AS budget_tifr_usaid,
            COALESCE(SUM(budget_ftit), 0)        AS budget_ftit
        FROM activities WHERE country_id = ?
        """,
        (country_id,),
    ).fetchone()
    totals = dict(row)
    totals["cost_total"] = (
        totals["cost_ni_hct"] + totals["cost_tifr_usaid"] + totals["cost_ftit"]
    )
    totals["budget_total"] = (
        totals["budget_ni_hct"] + totals["budget_tifr_usaid"] + totals["budget_ftit"]
    )
    totals["solde"] = totals["budget_total"] - totals["cost_total"]
    return totals


# ---------------------------------------------------------------- rapports
CATEGORY_LABELS = {
    "P": "Programme (P)",
    "I": "Sensibilisation (I)",
    "A": "Admin (A)",
    "C": "Collecte (C)",
}


def activities_by_category(conn, country_id: int = None):
    """Rapport activités regroupées par catégorie (P/I/A/C), avec le
    nombre d'activités, le coût total et le budget total par pays."""
    sql = (
        "SELECT c.name AS country_name, "
        "COALESCE(NULLIF(TRIM(a.category), ''), '(sans catégorie)') AS category, "
        "COUNT(*) AS n_activites, "
        "COALESCE(SUM(a.cost_ni_hct + a.cost_tifr_usaid + a.cost_ftit), 0) AS cost_total, "
        "COALESCE(SUM(a.budget_ni_hct + a.budget_tifr_usaid + a.budget_ftit), 0) AS budget_total "
        "FROM activities a JOIN countries c ON c.id = a.country_id "
    )
    params = ()
    if country_id is not None:
        sql += "WHERE a.country_id = ? "
        params = (country_id,)
    sql += "GROUP BY c.name, category ORDER BY c.name, category"
    rows = conn.execute(sql, params).fetchall()

    result = []
    for r in rows:
        d = dict(r)
        d["category_label"] = CATEGORY_LABELS.get(d["category"], d["category"])
        d["solde"] = d["budget_total"] - d["cost_total"]
        result.append(d)
    return result


def list_all_activities(conn, country_id: int = None):
    """Toutes les activités, toutes régions confondues (ou d'un seul pays),
    avec le nom du pays et de la phase pour les rapports."""
    sql = (
        "SELECT a.*, c.name AS country_name, p.name AS phase_name "
        "FROM activities a "
        "JOIN countries c ON c.id = a.country_id "
        "LEFT JOIN phases p ON p.id = a.phase_id "
    )
    params = ()
    if country_id is not None:
        sql += "WHERE a.country_id = ? "
        params = (country_id,)
    sql += "ORDER BY c.name, p.position, a.start_date, a.id"
    return conn.execute(sql, params).fetchall()


DONOR_LABELS = [("ni_hct", "NI/HCT"), ("tifr_usaid", "TIFR-USAID"), ("ftit", "FTIT")]


def budget_by_donor(conn, country_id: int = None):
    """Rapport budget : une ligne par pays x bailleur, avec coût, budget
    et solde. Si country_id est fourni, un seul pays est renvoyé."""
    countries = (
        [get_country(conn, country_id)] if country_id is not None
        else list_countries(conn)
    )
    rows = []
    for country in countries:
        totals = country_totals(conn, country["id"])
        for key, label in DONOR_LABELS:
            cost = totals[f"cost_{key}"]
            budget = totals[f"budget_{key}"]
            rows.append({
                "country": country["name"],
                "donor": label,
                "cost": cost,
                "budget": budget,
                "solde": budget - cost,
            })
        rows.append({
            "country": country["name"],
            "donor": "TOTAL",
            "cost": totals["cost_total"],
            "budget": totals["budget_total"],
            "solde": totals["solde"],
        })
    return rows


def get_country(conn, country_id: int):
    return conn.execute("SELECT * FROM countries WHERE id = ?", (country_id,)).fetchone()


def procurement_by_charge_code(conn, country_id: int = None):
    """Rapport achats regroupés par code de charge (charge_code), avec le
    nombre d'achats et le montant total par pays."""
    sql = (
        "SELECT c.name AS country_name, "
        "COALESCE(NULLIF(TRIM(pr.charge_code), ''), '(sans code de charge)') AS charge_code, "
        "COUNT(*) AS n_achats, COALESCE(SUM(pr.montant), 0) AS montant_total "
        "FROM procurements pr JOIN countries c ON c.id = pr.country_id "
    )
    params = ()
    if country_id is not None:
        sql += "WHERE pr.country_id = ? "
        params = (country_id,)
    sql += "GROUP BY c.name, charge_code ORDER BY c.name, charge_code"
    return conn.execute(sql, params).fetchall()


# ------------------------------------------------- répartition des fonds (%)
def breakdown_by_category(conn, country_id: int = None):
    """Répartition du budget (et du nombre d'activités) par catégorie,
    en valeur et en % du total, avec une ligne TOTAL = 100%."""
    sql = (
        "SELECT COALESCE(NULLIF(TRIM(category), ''), '') AS cat_code, "
        "COUNT(*) AS n_activities, "
        "COALESCE(SUM(budget_ni_hct + budget_tifr_usaid + budget_ftit), 0) AS budget "
        "FROM activities "
    )
    params = ()
    if country_id is not None:
        sql += "WHERE country_id = ? "
        params = (country_id,)
    sql += "GROUP BY cat_code ORDER BY cat_code"
    rows = conn.execute(sql, params).fetchall()

    total_budget = sum(r["budget"] for r in rows)
    total_n = sum(r["n_activities"] for r in rows)

    result = []
    for r in rows:
        code = r["cat_code"]
        label = CATEGORY_LABELS.get(code, code) if code else "(sans catégorie)"
        result.append({
            "label": label,
            "budget": r["budget"],
            "pct_budget": (r["budget"] / total_budget * 100) if total_budget else 0.0,
            "n_activities": r["n_activities"],
            "pct_activities": (r["n_activities"] / total_n * 100) if total_n else 0.0,
        })
    result.append({
        "label": "TOTAL", "budget": total_budget,
        "pct_budget": 100.0 if total_budget else 0.0,
        "n_activities": total_n,
        "pct_activities": 100.0 if total_n else 0.0,
        "is_total": True,
    })
    return result


def breakdown_by_country(conn):
    """Répartition du budget (et du nombre d'activités) par pays, en % du
    total général. Utilisé uniquement quand « Tous les pays » est choisi."""
    sql = (
        "SELECT c.name AS label, COUNT(a.id) AS n_activities, "
        "COALESCE(SUM(a.budget_ni_hct + a.budget_tifr_usaid + a.budget_ftit), 0) AS budget "
        "FROM countries c LEFT JOIN activities a ON a.country_id = c.id "
        "GROUP BY c.name ORDER BY c.name"
    )
    rows = conn.execute(sql).fetchall()

    total_budget = sum(r["budget"] for r in rows)
    total_n = sum(r["n_activities"] for r in rows)

    result = []
    for r in rows:
        result.append({
            "label": r["label"],
            "budget": r["budget"],
            "pct_budget": (r["budget"] / total_budget * 100) if total_budget else 0.0,
            "n_activities": r["n_activities"],
            "pct_activities": (r["n_activities"] / total_n * 100) if total_n else 0.0,
        })
    result.append({
        "label": "TOTAL", "budget": total_budget,
        "pct_budget": 100.0 if total_budget else 0.0,
        "n_activities": total_n,
        "pct_activities": 100.0 if total_n else 0.0,
        "is_total": True,
    })
    return result


def breakdown_by_donor(conn, country_id: int = None):
    """Répartition du budget par bailleur (NI/HCT, TIFR-USAID, FTIT), en %
    du total. Pas de colonne « activités » : une même activité peut être
    financée par plusieurs bailleurs à la fois."""
    sql = (
        "SELECT COALESCE(SUM(budget_ni_hct), 0) AS ni_hct, "
        "COALESCE(SUM(budget_tifr_usaid), 0) AS tifr, "
        "COALESCE(SUM(budget_ftit), 0) AS ftit FROM activities "
    )
    params = ()
    if country_id is not None:
        sql += "WHERE country_id = ? "
        params = (country_id,)
    row = conn.execute(sql, params).fetchone()

    items = [("NI/HCT", row["ni_hct"]), ("TIFR-USAID", row["tifr"]), ("FTIT", row["ftit"])]
    total = sum(v for _, v in items)

    result = []
    for label, budget in items:
        result.append({
            "label": label, "budget": budget,
            "pct_budget": (budget / total * 100) if total else 0.0,
        })
    result.append({
        "label": "TOTAL", "budget": total,
        "pct_budget": 100.0 if total else 0.0, "is_total": True,
    })
    return result


def breakdown_by_charge_code_pct(conn, country_id: int = None):
    """Répartition du montant des achats par code de charge, en % du total
    (basé sur le suivi des achats, pas sur le planning)."""
    sql = (
        "SELECT COALESCE(NULLIF(TRIM(charge_code), ''), '(sans code de charge)') AS label, "
        "COALESCE(SUM(montant), 0) AS montant FROM procurements "
    )
    params = ()
    if country_id is not None:
        sql += "WHERE country_id = ? "
        params = (country_id,)
    sql += "GROUP BY label ORDER BY label"
    rows = conn.execute(sql, params).fetchall()

    total = sum(r["montant"] for r in rows)

    result = []
    for r in rows:
        result.append({
            "label": r["label"], "montant": r["montant"],
            "pct_montant": (r["montant"] / total * 100) if total else 0.0,
        })
    result.append({
        "label": "TOTAL", "montant": total,
        "pct_montant": 100.0 if total else 0.0, "is_total": True,
    })
    return result
