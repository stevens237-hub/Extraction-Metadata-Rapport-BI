# Extraction automatique des métadonnées de rapports Power BI

Outil qui extrait en masse les métadonnées de rapports Power BI (`.pbix`) 
et de rapports paginés (`.rdl`) sous forme de fichiers CSV consolidés, 
sans manipulation rapport par rapport.

---

## Ce que l'outil produit

À chaque exécution, des fichiers CSV consolidés sont générés dans le 
dossier de sortie. Chaque CSV regroupe les données de **tous** les 
rapports traités, avec une colonne `NomRapport` pour filtrer dans Excel.

### Pour les rapports Power BI classiques (.pbix)

| Fichier | Contenu |
|---|---|
| `ReportPages.csv` | Liste des pages de tous les rapports |
| `Visuals.csv` | Détail de chaque visuel (type, position, filtres) |
| `UsedFields.csv` | Champs utilisés dans les visuels |
| `UsedTables.csv` | Tables utilisées (agrégé par rapport) |
| `UnusedFields.csv` | Champs du modèle non utilisés dans les visuels |
| `UnusedTables.csv` | Tables du modèle non utilisées |

### Pour les rapports paginés (.rdl)

| Fichier | Contenu |
|---|---|
| `PaginatedReports.csv` | Vue d'ensemble des rapports paginés |
| `PaginatedDataSources.csv` | Sources de données utilisées |
| `PaginatedDataSets.csv` | Requêtes définies dans les rapports |
| `PaginatedFields.csv` | Champs utilisés par les rapports |
| `PaginatedVisuals.csv` | Éléments visuels (Tablix, Chart, etc.) |

---

## Prérequis

- **Python 3.11+** ([python.org](https://www.python.org/downloads/), cocher "Add Python to PATH")
- **pbi-tools Desktop CLI** ([pbi.tools](https://pbi.tools))
- **Windows**

Voir [INSTALL.md](INSTALL.md) pour l'installation détaillée.

---

## Utilisation

1. Adapter les chemins dans `config.ini` à votre environnement
2. Placer les fichiers `.pbix` et `.rdl` dans le dossier configuré
3. Double-cliquer sur `LancerExtraction.bat`
4. Récupérer les CSV dans le dossier de sortie

Chaque exécution régénère intégralement les CSV. Pour ajouter ou retirer 
des rapports, il suffit d'ajuster le contenu du dossier source et de 
relancer.

---

## Configuration

Le fichier `config.ini` centralise les chemins :

```ini
[Chemins]
dossier_rapports = C:\Rapports\AAutomatiser
dossier_sortie = C:\Rapports\Resultats
chemin_pbi_tools = C:\Outils\pbi-tools\pbi-tools.exe
dossier_temp = C:\Rapports\Temp
```

---

## Limitations

- Les tables système auto-générées (`LocalDateTable_*`, `DateTableTemplate_*`) 
  sont volontairement exclues
- Les alias "role-playing" ne sont pas détectés (seul le nom canonique apparaît)
- Les rapports en Live Connection ne permettent pas de calculer les champs 
  non utilisés (modèle externe)
- Les fichiers `.pbix` protégés par mot de passe sont ignorés

---

## Problèmes fréquents

**"Le fichier est ouvert dans Excel"** → fermer le CSV dans Excel avant 
de relancer.

**"pbi-tools introuvable"** → vérifier le chemin `chemin_pbi_tools` dans 
`config.ini`.

**Aucun rapport détecté** → vérifier que `dossier_rapports` contient bien 
des fichiers `.pbix` ou `.rdl`.

---

