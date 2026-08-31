# Nuru Workplan Manager

Logiciel de bureau (Windows, `.exe`) pour suivre le **planning (Gantt)**, le
**budget par bailleur** et le **suivi des achats (procurement)** de vos
projets multi-pays (Togo, Bénin, Niger, Ghana).

## Fonctionnalités

- Un onglet **Consolidation** avec les totaux coûts / budget / solde de tous les pays, et deux boutons bien visibles :
  - **📥 Importer un classeur Excel...**
  - **📄 Télécharger le modèle (.xlsx)** — génère un classeur vierge (avec une ligne d'exemple) à la structure exacte attendue, à remplir puis importer.
- Un onglet par **pays** avec :
  - le **planning** des activités (phase, code, tâche, dates, budget par bailleur NI/HCT, TIFR-USAID, FTIT) avec ajout / modification / suppression,
  - **l'avancement (%) est calculé automatiquement** = coût total ÷ budget total. Ce n'est jamais une saisie manuelle. En cas de dépassement de budget, l'avancement peut dépasser 100 % (affiché tel quel, comme signal d'alerte) — le curseur visuel dans le diagramme de Gantt est cependant plafonné visuellement à 100 % pour rester lisible,
  - **le coût (%) d'une activité est lui aussi calculé automatiquement** : c'est la somme des achats au statut **« Livré »** dans le Suivi des achats dont le **code activité** correspond, ventilée par bailleur via le champ **« Bailleur »** de l'achat (NI/HCT, TIFR-USAID ou FTIT). Le champ Coût n'existe plus dans le formulaire d'activité — seul le **Budget** (la prévision) reste saisi manuellement. Si un achat livré a un code activité introuvable ou un bailleur non reconnu, un message liste les achats concernés pour correction,
  - le tableau affiche aussi **Non livré** (somme des achats liés encore engagés — statut différent de « Livré » et « Annulé ») et **Solde global** = Solde − Non livré, pour voir en un coup d'œil le budget réellement encore disponible une fois les engagements en cours pris en compte,
  - un **diagramme de Gantt** simple généré automatiquement à partir des dates,
  - le **suivi des achats** (PR, RFQ, Bon de commande, fournisseur, statut, paiement...).
- Un menu **Référentiels** pour créer/modifier/supprimer les listes utilisées dans les formulaires : Codes d'activité, Catégories, Budget (bailleurs), Codes de charge. Chaque onglet du menu Référentiels propose désormais :
  - **📥 Importer (.xlsx)** — charge en une fois toute une liste (fichier à 2 colonnes Code/Libellé). Réimportable sans risque : une valeur déjà présente voit son libellé mis à jour plutôt que d'être dupliquée.
  - **📄 Télécharger le modèle** — génère le fichier vierge à remplir pour cet onglet précis.

  Ces listes alimentent les menus déroulants des formulaires d'activité et d'achat (vous pouvez aussi taper une nouvelle valeur directement).
- Un menu **Rapports** — répartition des fonds à deux sélecteurs :
  - **Pays** : Tous les pays, ou un pays précis
  - **Répartir par** : Catégorie, Pays *(si "Tous les pays")*, Bailleur (budget), Code comptable

  Tableau avec **% du total** (ligne TOTAL = 100 %) + **graphique en barres** (style cylindrique) à côté, mis à jour automatiquement. Export Excel du rapport affiché.
- **Export** de toutes les données vers un nouveau classeur Excel.
- **Données d'exemple** (Fichier > Charger des données d'exemple) pour découvrir l'application sans importer de fichier.
- Les données sont stockées **localement** dans une base SQLite (aucune connexion internet requise), dans :
  - Windows : `%APPDATA%\NuruWorkplanManager\nuru_workplan.db`
  - macOS/Linux : `~/NuruWorkplanManager/nuru_workplan.db`

## Obtenir le fichier `.exe`

Le `.exe` est **compilé automatiquement par GitHub Actions** :

1. Poussez ce dossier dans un dépôt GitHub (voir ci-dessous).
2. Onglet **Actions** du dépôt : le workflow *Build Windows .exe* se lance automatiquement à chaque `push` sur `main`.
3. Une fois terminé (✅), téléchargez l'archive **NuruWorkplanManager-windows** dans *Artifacts* : elle contient `NuruWorkplanManager.exe`.
4. Pour une **release téléchargeable en un clic** :
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
   Le workflow publie alors `NuruWorkplanManager.exe` dans l'onglet **Releases**.

## Mettre le projet sur GitHub

```bash
cd nuru-workplan
git init
git add .
git commit -m "Nuru Workplan Manager"
git branch -M main
git remote add origin https://github.com/<votre-compte>/<votre-depot>.git
git push -u origin main
```

## Utilisation

1. Lancez `NuruWorkplanManager.exe`.
2. Onglet Consolidation > **📄 Télécharger le modèle (.xlsx)** si vous n'avez pas encore de fichier, remplissez-le, puis **📥 Importer un classeur Excel...**. Ou : **Fichier > Charger des données d'exemple** pour tester tout de suite.
3. Naviguez entre les onglets pays pour consulter/modifier le planning, le Gantt et les achats — l'avancement s'affiche mais ne se saisit pas.
4. Menu **Référentiels** pour gérer vos listes de codes/catégories/bailleurs.
5. Menu **Rapports** pour la répartition des fonds avec graphique.
6. Menu **Fichier > Exporter vers Excel...** pour générer un classeur à jour.

## Développement local

```bash
pip install -r requirements.txt
python run_app.py
```

## Compiler le .exe soi-même (optionnel)

```bash
pip install -r requirements.txt
pyinstaller --noconfirm --onefile --windowed --name "NuruWorkplanManager" --add-data "app;app" run_app.py
```

## Structure du projet

```
nuru-workplan/
├── app/
│   ├── database.py            # Schéma SQLite, CRUD, référentiels, rapports (avancement auto)
│   ├── excel_import.py        # Import d'un classeur WORKPLAN_MULTIPAYS.xlsx
│   ├── excel_export.py        # Export vers Excel
│   ├── template_generator.py  # Génération du modèle Excel vierge à télécharger
│   ├── sample_data.py         # Données d'exemple
│   ├── main.py
│   └── gui/
│       ├── app_window.py        # Fenêtre principale (menu, boutons, onglets)
│       ├── country_tab.py       # Onglet planning/Gantt + achats par pays
│       ├── reports_window.py    # Rapports (répartition des fonds + graphique)
│       ├── referentials_window.py  # Gestion des référentiels
│       └── dialogs.py           # Formulaires génériques d'ajout/édition
├── run_app.py                 # Point d'entrée (cible PyInstaller)
├── requirements.txt
└── .github/workflows/build-exe.yml
```

## Avancement automatique — détail

L'avancement d'une activité n'est **jamais saisi** : il est recalculé à
chaque ajout/modification comme `coût total ÷ budget total`. Si le coût
dépasse le budget, l'avancement dépasse 100 % et s'affiche tel quel
(ex : « 138 % ») — c'est volontaire, ça sert de signal d'alerte de
dépassement budgétaire. Seule la mini barre de progression dessinée dans
le diagramme de Gantt est plafonnée visuellement à 100 % pour rester
lisible ; le pourcentage textuel, lui, n'est jamais tronqué.
