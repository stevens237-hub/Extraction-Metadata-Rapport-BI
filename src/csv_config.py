"""
Définition centralisée des fichiers CSV de sortie et de leurs colonnes.
Toute nouvelle colonne ou tout nouveau fichier de sortie se déclare ici,
plutôt que dans main.py.
"""

COLONNES_REPORT_PAGES = ['NomRapport', 'NomPage', 'OrdrePage', 'Largeur', 'Hauteur', 'EstVisible', 'NbVisuels']
COLONNES_VISUALS = ['NomRapport', 'NomPage', 'OrdrePage', 'TypeVisuel', 'Titre',
                     'PositionX', 'PositionY', 'Largeur', 'Hauteur', 'AFiltre']
COLONNES_USED_FIELDS = ['NomRapport', 'NomPage', 'TypeVisuel', 'NomTable', 'NomChamp', 'TypeChamp', 'Agregation']
COLONNES_USED_TABLES = ['NomRapport', 'NomTable', 'NbChampsUtilises', 'NbVisuelsUtilisant']
COLONNES_UNUSED_FIELDS = ['NomRapport', 'NomTable', 'NomChamp', 'TypeChamp', 'EstMasque']
COLONNES_UNUSED_TABLES = ['NomRapport', 'NomTable', 'NbColonnes', 'NbMesures', 'EstMasqueeGlobalement']

COLONNES_PAGINATED_REPORTS = ['NomRapport', 'NbDataSources', 'NbDataSets', 'NbChampsTotal',
                               'NbParametres', 'NbTablix', 'NbCharts', 'NbTextbox', 'NbSubreports']
COLONNES_PAGINATED_DATASOURCES = ['NomRapport', 'NomSource', 'Provider', 'ConnectString', 'AuthMode']
COLONNES_PAGINATED_DATASETS = ['NomRapport', 'NomDataSet', 'NomSource', 'TypeCommande', 'NbChamps', 'ExtraitRequete']
COLONNES_PAGINATED_FIELDS = ['NomRapport', 'NomDataSet', 'NomChamp', 'SourceField', 'Formule']
COLONNES_PAGINATED_VISUALS = ['NomRapport', 'NomVisuel', 'TypeVisuel', 'SousType', 'NomDataSet']

# Fichiers CSV pour les rapports Power BI classiques (.pbix)
FICHIERS_CSV_CLASSIQUES = {
    'ReportPages.csv': COLONNES_REPORT_PAGES,
    'Visuals.csv': COLONNES_VISUALS,
    'UsedFields.csv': COLONNES_USED_FIELDS,
    'UsedTables.csv': COLONNES_USED_TABLES,
    'UnusedFields.csv': COLONNES_UNUSED_FIELDS,
    'UnusedTables.csv': COLONNES_UNUSED_TABLES,
}

# Fichiers CSV pour les rapports paginés (.rdl / .pbix paginé)
FICHIERS_CSV_PAGINES = {
    'PaginatedReports.csv': COLONNES_PAGINATED_REPORTS,
    'PaginatedDataSources.csv': COLONNES_PAGINATED_DATASOURCES,
    'PaginatedDataSets.csv': COLONNES_PAGINATED_DATASETS,
    'PaginatedFields.csv': COLONNES_PAGINATED_FIELDS,
    'PaginatedVisuals.csv': COLONNES_PAGINATED_VISUALS,
}

NOMS_FICHIERS_CSV = list(FICHIERS_CSV_CLASSIQUES) + list(FICHIERS_CSV_PAGINES)
