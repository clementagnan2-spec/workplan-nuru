"""
Données d'exemple pour découvrir Nuru Workplan Manager sans avoir à
importer un fichier Excel. Utilisable via le menu Fichier > Charger des
données d'exemple.

L'avancement n'est pas défini ici : il est recalculé automatiquement par
database.add_activity() comme (coût total / budget total).
"""

import datetime

from . import database as db

TODAY = datetime.date.today()


def _d(offset_days: int) -> str:
    return (TODAY + datetime.timedelta(days=offset_days)).isoformat()


SAMPLE_PLAN = {
    "TOGO": [
        ("Phase 1 - Terrain", [
            dict(code="A1XX", task="Activités agricoles et parcelle de démonstration",
                 assigned_to="Équipe terrain", start=_d(-10), end=_d(5),
                 nb_pieces=2, category="P",
                 cost_ni_hct=74100, cost_tifr_usaid=114000, cost_ftit=0,
                 budget_ni_hct=100000, budget_tifr_usaid=200000, budget_ftit=500000),
            dict(code="A2XX", task="Formation des coopératives",
                 assigned_to="Chef de projet", start=_d(-5), end=_d(40),
                 nb_pieces=2, category="P",
                 cost_ni_hct=74100, cost_tifr_usaid=0, cost_ftit=0,
                 budget_ni_hct=10000, budget_tifr_usaid=11000000, budget_ftit=0),
            dict(code="A3XX", task="Service numérique et climatique (IGNITIA)",
                 assigned_to="Coordination", start=_d(2), end=_d(12),
                 nb_pieces=1, category="I",
                 cost_ni_hct=0, cost_tifr_usaid=250000, cost_ftit=0,
                 budget_ni_hct=5000, budget_tifr_usaid=0, budget_ftit=1500000),
        ]),
        ("Phase 2 - Admin", [
            dict(code="A6XX", task="Frais administratifs et audit",
                 assigned_to="Administration", start=_d(-15), end=_d(180),
                 nb_pieces=None, category="A",
                 cost_ni_hct=12000000, cost_tifr_usaid=0, cost_ftit=3000000,
                 budget_ni_hct=0, budget_tifr_usaid=0, budget_ftit=30000000),
            dict(code="A7XX", task="Salaires",
                 assigned_to="RH", start=_d(0), end=_d(6),
                 nb_pieces=None, category="A",
                 cost_ni_hct=74100, cost_tifr_usaid=0, cost_ftit=0,
                 budget_ni_hct=0, budget_tifr_usaid=0, budget_ftit=0),
        ]),
        ("Phase 3 - Missions", [
            dict(code="A11XX", task="Missions de suivi",
                 assigned_to="Superviseur", start=_d(6), end=_d(11),
                 nb_pieces=None, category="A",
                 cost_ni_hct=0, cost_tifr_usaid=0, cost_ftit=0,
                 budget_ni_hct=0, budget_tifr_usaid=0, budget_ftit=0),
        ]),
    ],
    "BENIN": [
        ("Phase 1 - Terrain", [
            dict(code="A1XX", task="Distribution d'intrants agricoles",
                 assigned_to="Équipe terrain", start=_d(-8), end=_d(7),
                 nb_pieces=3, category="P",
                 cost_ni_hct=50000, cost_tifr_usaid=90000, cost_ftit=0,
                 budget_ni_hct=80000, budget_tifr_usaid=180000, budget_ftit=400000),
            dict(code="A2XX", task="Sensibilisation communautaire",
                 assigned_to="Chargé de sensibilisation", start=_d(-3), end=_d(20),
                 nb_pieces=1, category="I",
                 cost_ni_hct=20000, cost_tifr_usaid=0, cost_ftit=0,
                 budget_ni_hct=25000, budget_tifr_usaid=0, budget_ftit=0),
        ]),
        ("Phase 2 - Admin", [
            dict(code="A6XX", task="Audit financier annuel",
                 assigned_to="Administration", start=_d(10), end=_d(40),
                 nb_pieces=None, category="A",
                 cost_ni_hct=0, cost_tifr_usaid=0, cost_ftit=2500000,
                 budget_ni_hct=0, budget_tifr_usaid=0, budget_ftit=5400000),
        ]),
    ],
    "NIGER": [
        ("Phase 1 - Terrain", [
            dict(code="A1XX", task="Forage et point d'eau",
                 assigned_to="Équipe technique", start=_d(0), end=_d(30),
                 nb_pieces=1, category="P",
                 cost_ni_hct=300000, cost_tifr_usaid=0, cost_ftit=0,
                 budget_ni_hct=600000, budget_tifr_usaid=0, budget_ftit=0),
            dict(code="A2XX", task="Formation des relais communautaires",
                 assigned_to="Chef de projet", start=_d(-20), end=_d(-2),
                 nb_pieces=2, category="P",
                 cost_ni_hct=45000, cost_tifr_usaid=60000, cost_ftit=0,
                 budget_ni_hct=50000, budget_tifr_usaid=70000, budget_ftit=0),
        ]),
        ("Phase 4 - Collecte", [
            dict(code="A16XX", task="Collecte de fonds locale",
                 assigned_to="Fundraising", start=_d(15), end=_d(60),
                 nb_pieces=None, category="C",
                 cost_ni_hct=0, cost_tifr_usaid=0, cost_ftit=0,
                 budget_ni_hct=0, budget_tifr_usaid=0, budget_ftit=0),
        ]),
    ],
    "GHANA": [
        ("Phase 1 - Terrain", [
            dict(code="A1XX", task="Mise en place de parcelles pilotes",
                 assigned_to="Équipe agronomie", start=_d(-25), end=_d(-1),
                 nb_pieces=4, category="P",
                 cost_ni_hct=120000, cost_tifr_usaid=200000, cost_ftit=0,
                 budget_ni_hct=150000, budget_tifr_usaid=250000, budget_ftit=0),
        ]),
        ("Phase 3 - Missions", [
            dict(code="A12XX", task="Mission d'évaluation à mi-parcours",
                 assigned_to="Coordination régionale", start=_d(20), end=_d(25),
                 nb_pieces=None, category="A",
                 cost_ni_hct=0, cost_tifr_usaid=0, cost_ftit=0,
                 budget_ni_hct=0, budget_tifr_usaid=0, budget_ftit=0),
        ]),
    ],
}

SAMPLE_PROCUREMENT = {
    "TOGO": [
        dict(dossier_workplan="A1XX", n_pr="PR_2026_0001", n_rfq="RFQ_2026_0001",
             n_bc="BC_2026_0001", date_bc=_d(-12), n_proforma="N°012-26",
             demandeur="Chef de projet", designation="Achat de semences améliorées",
             fournisseur="Agro Plus Togo", date_fournisseur=_d(-9), montant=250000,
             categorie="P", lieu_livraison="Bureau Nuru", statut_bc="Livré",
             type_procurement="National", project="TIFR-USAID", validation="Payé"),
        dict(dossier_workplan="A2XX", n_pr="PR_2026_0002", n_rfq="RFQ_2026_0002",
             n_bc="BC_2026_0002", date_bc=_d(-4), n_proforma="N°013-26",
             demandeur="Chef de projet", designation="Location de salle de formation",
             fournisseur="Hôtel Central", date_fournisseur=_d(-2), montant=90000,
             categorie="P", lieu_livraison="Lomé", statut_bc="En cours",
             type_procurement="National", project="NI/HCT", validation="En cours"),
    ],
    "BENIN": [
        dict(dossier_workplan="A1XX", n_pr="PR_2026_0010", n_rfq="RFQ_2026_0010",
             n_bc="BC_2026_0010", date_bc=_d(-6), n_proforma="N°004-26",
             demandeur="Équipe terrain", designation="Intrants agricoles (semences, engrais)",
             fournisseur="AgroBenin SARL", date_fournisseur=_d(-1), montant=140000,
             categorie="P", lieu_livraison="Bureau Nuru Bénin", statut_bc="Livré",
             type_procurement="National", project="TIFR-USAID", validation="Payé"),
    ],
    "NIGER": [
        dict(dossier_workplan="A1XX", n_pr="PR_2026_0020", n_rfq="RFQ_2026_0020",
             n_bc="BC_2026_0020", date_bc=_d(1), n_proforma="N°021-26",
             demandeur="Équipe technique", designation="Matériel de forage",
             fournisseur="Forage Niger SA", date_fournisseur=None, montant=600000,
             categorie="P", lieu_livraison="Zone Niger", statut_bc="En attente",
             type_procurement="International", project="NI/HCT", validation="En cours"),
    ],
    "GHANA": [
        dict(dossier_workplan="A1XX", n_pr="PR_2026_0030", n_rfq="RFQ_2026_0030",
             n_bc="BC_2026_0030", date_bc=_d(-20), n_proforma="N°008-26",
             demandeur="Équipe agronomie", designation="Outils et matériel agricole",
             fournisseur="Ghana Farm Supplies", date_fournisseur=_d(-15), montant=175000,
             categorie="P", lieu_livraison="Accra", statut_bc="Livré",
             type_procurement="National", project="TIFR-USAID", validation="Payé"),
    ],
}


def load_sample_data(conn, clear_existing: bool = False) -> dict:
    summary = {}

    for country_name, phases in SAMPLE_PLAN.items():
        country_id = db.get_or_create_country(conn, country_name)

        if clear_existing:
            conn.execute("DELETE FROM activities WHERE country_id = ?", (country_id,))
            conn.execute("DELETE FROM procurements WHERE country_id = ?", (country_id,))
            conn.execute("DELETE FROM phases WHERE country_id = ?", (country_id,))
            conn.commit()

        n_act = 0
        for position, (phase_name, activities) in enumerate(phases, start=1):
            phase_id = db.get_or_create_phase(conn, country_id, phase_name, position)
            for a in activities:
                db.add_activity(conn, country_id, {
                    "phase_id": phase_id,
                    "code": a["code"],
                    "task": a["task"],
                    "assigned_to": a["assigned_to"],
                    "start_date": a["start"],
                    "end_date": a["end"],
                    "nb_pieces": a["nb_pieces"],
                    "category": a["category"],
                    "cost_ni_hct": a["cost_ni_hct"],
                    "cost_tifr_usaid": a["cost_tifr_usaid"],
                    "cost_ftit": a["cost_ftit"],
                    "budget_ni_hct": a["budget_ni_hct"],
                    "budget_tifr_usaid": a["budget_tifr_usaid"],
                    "budget_ftit": a["budget_ftit"],
                    "comment": "Donnée d'exemple",
                })
                n_act += 1

        n_proc = 0
        for p in SAMPLE_PROCUREMENT.get(country_name, []):
            db.add_procurement(conn, country_id, p)
            n_proc += 1

        summary[country_name] = {"activities": n_act, "procurements": n_proc}

    return summary
