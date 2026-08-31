"""
Couche d'accès aux données (SQLite) pour Nuru Workplan Manager.

La base est stockée dans un unique fichier .db à côté de l'exécutable
(ou dans le dossier de données utilisateur). Toutes les fonctions de ce
module prennent une connexion sqlite3 en premier argument.

IMPORTANT : le champ `progress` (avancement) des activités n'est JAMAIS
saisi manuellement — il est recalculé automatiquement à chaque
ajout/modification comme le rapport (coût total / budget total). Il n'est
pas plafonné à 100% : un dépassement de budget se traduit par un
avancement > 100%, ce qui sert de signal d'alerte visible.
"""

import sqlite3
import os
import sys

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
    progress            REAL DEFAULT 0,        -- calculé automatiquement = cout/budget (0..N, non plafonné)
    start_date          TEXT,                  -- ISO yyyy-mm-dd
    end_date            TEXT,                  -- ISO yyyy-mm-dd
    nb_pieces           REAL DEFAULT 0,
    category            TEXT,                  -- P / I / A / C
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
    demandeur               TEXT,
    designation             TEXT,
    fournisseur             TEXT,
    date_fournisseur        TEXT,
    montant                 REAL DEFAULT 0,
    categorie               TEXT,              -- P / I / A / C
    lieu_livraison          TEXT,
    date_livraison_prevue   TEXT,
    statut_bc               TEXT,
    type_procurement        TEXT,              -- National / International
    project                 TEXT,
    charge_code             TEXT,
    code                    TEXT,
    bon_livraison           TEXT,
    facture_definitive      TEXT,
    date_reception_facture  TEXT,
    rib                     TEXT,
    banque                  TEXT,
    mode_paiement           TEXT,
    date_paiement           TEXT,
    validation               TEXT,
    commentaires              TEXT
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
        conn.execute("INSERT OR IGNORE INTO countries(name) VALUES (?)", (name,))


# ------------------------------------------------------------- référentiels
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
    key = REFERENTIAL_TABLES[table]
    rows = conn.execute(f"SELECT {key} FROM {table} ORDER BY {key}").fetchall()
    return [r[0] for r in rows]


def add_referential(conn, table: str, value: str, label: str = None) -> int:
    key = REFERENTIAL_TABLES[table]
    cur = conn.execute(f"INSERT INTO {table} ({key}, label) VALUES (?, ?)", (value, label))
    conn.commit()
    return cur.lastrowid


def update_referential(conn, table: str, item_id: int, value: str, label: str = None):
    key = REFERENTIAL_TABLES[table]
    conn.execute(f"UPDATE {table} SET {key} = ?, label = ? WHERE id = ?", (value, label, item_id))
    conn.commit()


def delete_referential(conn, table: str, item_id: int):
    conn.execute(f"DELETE FROM {table} WHERE id = ?", (item_id,))
    conn.commit()


# ---------------------------------------------------------------- countries
def list_countries(conn):
    return conn.execute("SELECT * FROM countries ORDER BY id").fetchall()


def get_country(conn, country_id: int):
    return conn.execute("SELECT * FROM countries WHERE id = ?", (country_id,)).fetchone()


def get_or_create_country(conn, name: str) -> int:
    row = conn.execute("SELECT id FROM countries WHERE name = ?", (name.upper(),)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO countries(name) VALUES (?)", (name.upper(),))
    conn.commit()
    return cur.lastrowid


# ------------------------------------------------------------------ phases
def get_or_create_phase(conn, country_id: int, name: str, position: int = 0) -> int:
    row = conn.execute(
        "SELECT id FROM phases WHERE country_id = ? AND name = ?", (country_id, name)
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
        "SELECT * FROM phases WHERE country_id = ? ORDER BY position, id", (country_id,)
    ).fetchall()


# -------------------------------------------------------------- activities
# NB : "progress" est volontairement EXCLU de cette liste de champs
# éditables : il est toujours recalculé par _compute_progress(), jamais
# pris tel quel depuis l'appelant.
ACTIVITY_FIELDS = [
    "phase_id", "code", "task", "assigned_to", "progress", "start_date",
    "end_date", "nb_pieces", "category", "cost_ni_hct", "cost_tifr_usaid",
    "cost_ftit", "budget_ni_hct", "budget_tifr_usaid", "budget_ftit", "comment",
]


def _compute_progress(data: dict, existing: dict = None) -> float:
    """Avancement = coût total / budget total. Pas de plafond à 100% :
    un dépassement de budget donne un avancement > 1 (affiché >100%)."""
    def val(key):
        if key in data and data[key] is not None:
            try:
                return float(data[key])
            except (TypeError, ValueError):
                return 0.0
        if existing and existing.get(key) is not None:
            try:
                return float(existing[key])
            except (TypeError, ValueError):
                return 0.0
        return 0.0

    cost_total = val("cost_ni_hct") + val("cost_tifr_usaid") + val("cost_ftit")
    budget_total = val("budget_ni_hct") + val("budget_tifr_usaid") + val("budget_ftit")
    if not budget_total:
        return 0.0
    return cost_total / budget_total


# --------------------------------------- ventilation coût <- achats livrés
# Le coût d'une activité n'est plus saisi manuellement : il est la somme
# des montants des achats au statut "Livré" dont le code correspond au
# code de l'activité, ventilée par bailleur (champ "project" de l'achat,
# qui doit valoir NI/HCT, TIFR-USAID ou FTIT).
DONOR_COLUMN_BY_LABEL = {
    "NI/HCT": "cost_ni_hct",
    "TIFR-USAID": "cost_tifr_usaid",
    "FTIT": "cost_ftit",
}


def _donor_column(donor_label):
    if not donor_label:
        return None
    return DONOR_COLUMN_BY_LABEL.get(str(donor_label).strip().upper())


def _is_delivered(statut_bc) -> bool:
    if not statut_bc:
        return False
    s = str(statut_bc).strip().lower()
    return s in ("livré", "livre", "livrée", "livree")


def recompute_costs_from_procurements(conn, country_id: int) -> dict:
    """Recalcule le coût (par bailleur) de chaque activité du pays comme la
    somme des achats « Livré » dont le code correspond, puis recalcule
    l'avancement. Renvoie les achats livrés qui n'ont pas pu être ventilés
    (code d'activité introuvable, ou bailleur non reconnu) pour alerte."""
    activities = list_activities(conn, country_id)
    by_code = {}
    for a in activities:
        code = (a["code"] or "").strip().upper()
        if code:
            by_code.setdefault(code, []).append(a["id"])

    sums = {a["id"]: {"cost_ni_hct": 0.0, "cost_tifr_usaid": 0.0, "cost_ftit": 0.0} for a in activities}

    unmatched_code = []
    unmatched_donor = []

    for p in list_procurements(conn, country_id):
        if not _is_delivered(p["statut_bc"]):
            continue
        code = (p["dossier_workplan"] or p["code"] or "").strip().upper()
        if not code or code not in by_code:
            unmatched_code.append(p)
            continue
        col = _donor_column(p["project"])
        if not col:
            unmatched_donor.append(p)
            continue
        for act_id in by_code[code]:
            sums[act_id][col] += (p["montant"] or 0.0)

    for act_id, cost_dict in sums.items():
        existing = get_activity(conn, act_id)
        data = dict(cost_dict)
        data["budget_ni_hct"] = existing["budget_ni_hct"]
        data["budget_tifr_usaid"] = existing["budget_tifr_usaid"]
        data["budget_ftit"] = existing["budget_ftit"]
        progress = _compute_progress(data)
        conn.execute(
            "UPDATE activities SET cost_ni_hct=?, cost_tifr_usaid=?, cost_ftit=?, progress=? WHERE id=?",
            (cost_dict["cost_ni_hct"], cost_dict["cost_tifr_usaid"], cost_dict["cost_ftit"], progress, act_id),
        )
    conn.commit()

    return {"unmatched_code": unmatched_code, "unmatched_donor": unmatched_donor}


def list_activities(conn, country_id: int):
    return conn.execute(
        "SELECT a.*, p.name AS phase_name FROM activities a "
        "LEFT JOIN phases p ON p.id = a.phase_id "
        "WHERE a.country_id = ? ORDER BY p.position, a.start_date, a.id",
        (country_id,),
    ).fetchall()


def get_activity(conn, activity_id: int):
    return conn.execute("SELECT * FROM activities WHERE id = ?", (activity_id,)).fetchone()


def add_activity(conn, country_id: int, data: dict) -> int:
    data = dict(data)
    data["progress"] = _compute_progress(data)
    cols = ["country_id"] + [f for f in ACTIVITY_FIELDS if f in data]
    placeholders = ", ".join(["?"] * len(cols))
    values = [country_id] + [data[f] for f in cols[1:]]
    cur = conn.execute(
        f"INSERT INTO activities ({', '.join(cols)}) VALUES ({placeholders})", values
    )
    conn.commit()
    return cur.lastrowid


def update_activity(conn, activity_id: int, data: dict):
    existing = get_activity(conn, activity_id)
    existing_dict = dict(existing) if existing else None
    data = dict(data)
    data["progress"] = _compute_progress(data, existing_dict)

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
        "SELECT * FROM procurements WHERE country_id = ? ORDER BY id", (country_id,)
    ).fetchall()


def get_procurement(conn, proc_id: int):
    return conn.execute("SELECT * FROM procurements WHERE id = ?", (proc_id,)).fetchone()


def add_procurement(conn, country_id: int, data: dict) -> int:
    cols = ["country_id"] + [f for f in PROCUREMENT_FIELDS if f in data]
    placeholders = ", ".join(["?"] * len(cols))
    values = [country_id] + [data[f] for f in cols[1:]]
    cur = conn.execute(
        f"INSERT INTO procurements ({', '.join(cols)}) VALUES ({placeholders})", values
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
    totals["cost_total"] = totals["cost_ni_hct"] + totals["cost_tifr_usaid"] + totals["cost_ftit"]
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


def list_all_activities(conn, country_id: int = None):
    sql = (
        "SELECT a.*, c.name AS country_name, p.name AS phase_name "
        "FROM activities a JOIN countries c ON c.id = a.country_id "
        "LEFT JOIN phases p ON p.id = a.phase_id "
    )
    params = ()
    if country_id is not None:
        sql += "WHERE a.country_id = ? "
        params = (country_id,)
    sql += "ORDER BY c.name, p.position, a.start_date, a.id"
    return conn.execute(sql, params).fetchall()


def procurement_by_charge_code(conn, country_id: int = None):
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
