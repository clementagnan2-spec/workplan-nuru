# Nuru Workplan Manager

Logiciel de bureau (Windows, `.exe`) pour suivre le **planning (Gantt)**, le
**budget par bailleur** et le **suivi des achats (procurement)** de vos
projets multi-pays (Togo, Bénin, Niger, Ghana), à partir du modèle de fichier
`WORKPLAN_MULTIPAYS.xlsx`.

## Fonctionnalités

- Un onglet **Consolidation** avec les totaux coûts / budget / solde de tous les pays.
- Un menu **Rapports** avec 3 vues transversales, filtrables par pays, exportables en Excel :
  - **Par catégorie** : nombre d'activités, coût total, budget total et solde regroupés par catégorie (Programme, Sensibilisation, Admin, Collecte) et par pays.
  - **Par budget** : coût / budget / solde par bailleur (NI/HCT, TIFR-USAID, FTIT) et par pays.
  - **Par code de charge** : montant total des achats regroupés par code de charge.
- Un onglet par **pays** avec :
  - le **planning** des activités (phase, code, tâche, avancement, dates, budget par bailleur NI/HCT, TIFR-USAID, FTIT) avec ajout / modification / suppression,
  - un **diagramme de Gantt** simple généré automatiquement à partir des dates,
  - le **suivi des achats** (PR, RFQ, Bon de commande, fournisseur, statut, paiement...).
- Un menu **Référentiels** pour créer/modifier/supprimer les listes utilisées dans les formulaires :
  - **Codes d'activité** (ex : A1XX, A2XX...)
  - **Catégories** (Programme, Sensibilisation, Admin, Collecte)
  - **Budget (bailleurs)** (NI/HCT, TIFR-USAID, FTIT)
  - **Codes de charge**

  Ces listes alimentent automatiquement les menus déroulants des formulaires d'activité et d'achat (vous pouvez aussi taper une nouvelle valeur directement dans le formulaire).
- **Import** d'un classeur Excel existant (feuilles `WORKPLAN <PAYS>` et `procurement <PAYS>`).
- **Export** de toutes les données vers un nouveau classeur Excel.
- Les données sont stockées **localement** dans une base SQLite (aucune connexion internet requise), dans :
  - Windows : `%APPDATA%\NuruWorkplanManager\nuru_workplan.db`
  - macOS/Linux : `~/NuruWorkplanManager/nuru_workplan.db`

## Obtenir le fichier `.exe`

Le `.exe` est **compilé automatiquement par GitHub Actions**, vous n'avez
rien à installer sur votre machine pour l'obtenir :

1. Poussez ce dossier dans un dépôt GitHub (voir ci-dessous).
2. Allez dans l'onglet **Actions** du dépôt : le workflow *Build Windows .exe*
   se lance automatiquement à chaque `push` sur `main`.
3. Une fois le workflow terminé (icône verte ✅), ouvrez son résumé et
   téléchargez l'archive **NuruWorkplanManager-windows** dans la section
   *Artifacts* : elle contient `NuruWorkplanManager.exe`.
4. Pour obtenir une **release téléchargeable en un clic** (avec un lien
   stable), créez un tag de version, par exemple :
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
   Le workflow publiera alors automatiquement `NuruWorkplanManager.exe`
   dans l'onglet **Releases** du dépôt.

## Mettre le projet sur GitHub

```bash
cd nuru-workplan
git init
git add .
git commit -m "Nuru Workplan Manager - version initiale"
git branch -M main
git remote add origin https://github.com/<votre-compte>/<votre-depot>.git
git push -u origin main
```

## Utilisation

1. Lancez `NuruWorkplanManager.exe` (double-clic).
2. Pour découvrir l'application tout de suite : menu **Fichier > Charger
   des données d'exemple** (données fictives sur les 4 pays).
3. Pour vos propres données : menu **Fichier > Importer un classeur
   Excel...** afin de charger un fichier `WORKPLAN_MULTIPAYS.xlsx` (même
   structure que le modèle Vertex42 utilisé par Nuru).
4. Naviguez entre les onglets pays pour consulter et modifier le planning,
   le Gantt et les achats.
5. Menu **Fichier > Exporter vers Excel...** pour générer un classeur à jour.

## Développement local (sans compiler le .exe)

Nécessite Python 3.10+ :

```bash
pip install -r requirements.txt
python run_app.py
```

## Compiler le .exe soi-même (optionnel)

Sous Windows, avec Python installé :

```bash
pip install -r requirements.txt
pyinstaller --noconfirm --onefile --windowed --name "NuruWorkplanManager" --add-data "app;app" run_app.py
```

L'exécutable est généré dans `dist\NuruWorkplanManager.exe`.

## Structure du projet

```
nuru-workplan/
├── app/
│   ├── database.py         # Schéma SQLite + fonctions CRUD
│   ├── excel_import.py     # Import d'un classeur WORKPLAN_MULTIPAYS.xlsx
│   ├── excel_export.py     # Export vers Excel
│   ├── main.py              # Démarrage de l'application
│   └── gui/
│       ├── app_window.py    # Fenêtre principale (menu, onglets)
│       ├── country_tab.py   # Onglet planning/Gantt + achats par pays
│       └── dialogs.py       # Formulaires génériques d'ajout/édition
├── run_app.py               # Point d'entrée (et cible PyInstaller)
├── requirements.txt
└── .github/workflows/build-exe.yml   # Compilation automatique du .exe
```

## Notes sur l'import Excel

L'import reconnaît automatiquement les feuilles nommées `WORKPLAN <PAYS>`
(ou `WORKPLA <PAYS>`) pour le planning, et `procurement <PAYS>` pour les
achats — insensible à la casse. Les lignes "Phase 1", "Phase 2"... créent
des regroupements ; la ligne marquant la fin du planning ("Cette ligne
marque la fin...") arrête la lecture. Après import, vérifiez et complétez
les données directement dans l'application si besoin (certains classeurs
sources ont des colonnes décalées ligne par ligne).
