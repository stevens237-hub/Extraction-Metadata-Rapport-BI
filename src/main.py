"""
Outil d'extraction automatique des métadonnées de rapports Power BI.
Orchestrateur principal.
"""

import configparser
import csv
import subprocess
import sys
from pathlib import Path

# Import du parser
sys.path.insert(0, str(Path(__file__).parent))
from classic_pbix_report.pages_parser import parser_pages_rapport
from classic_pbix_report.visuals_parser import parser_visuels_rapport
from classic_pbix_report.useField_parser import parser_champs_rapport
from classic_pbix_report.usedTable_parser import agreger_tables_utilisees
from classic_pbix_report.model_parser import parser_modele_rapport
from classic_pbix_report.unusedField_parse import calculer_champs_non_utilises
from classic_pbix_report.unusedTable_parse import calculer_tables_non_utilisees
from file_type_detector import (detecter_type_fichier, extraire_rdl_du_pbix_pagine, TYPE_PBIX_CLASSIQUE, TYPE_RDL, TYPE_PBIX_PAGINE, TYPE_INCONNU)
from paginated_report.paginated_parser import parser_rapport_rdl


def charger_configuration():
    """Lit le fichier config.ini situé à la racine du projet."""
    chemin_config = Path(__file__).parent.parent / "config.ini"
    
    if not chemin_config.exists():
        print(f"[ERREUR] Fichier config.ini introuvable : {chemin_config}")
        sys.exit(1)
    
    config = configparser.ConfigParser()
    config.read(chemin_config, encoding='utf-8')
    return config


def verifier_environnement(config):
    """Vérifie que les chemins configurés existent et que pbi-tools est accessible."""
    erreurs = []
    
    dossier_rapports = Path(config['Chemins']['dossier_rapports'])
    if not dossier_rapports.exists():
        erreurs.append(f"Le dossier de rapports n'existe pas : {dossier_rapports}")
    
    chemin_pbi_tools = Path(config['Chemins']['chemin_pbi_tools'])
    if not chemin_pbi_tools.exists():
        erreurs.append(f"pbi-tools.exe introuvable : {chemin_pbi_tools}")
    
    dossier_sortie = Path(config['Chemins']['dossier_sortie'])
    dossier_sortie.mkdir(parents=True, exist_ok=True)
    
    dossier_temp = Path(config['Chemins']['dossier_temp'])
    dossier_temp.mkdir(parents=True, exist_ok=True)
    
    return erreurs

def verifier_fichiers_sortie_accessibles(dossier_sortie, noms_csv):
    """
    Vérifie que les fichiers CSV de sortie peuvent être écrits.
    Détecte le cas où l'un d'eux est déjà ouvert dans Excel.
    
    Returns:
        liste des erreurs trouvées (vide si tout est OK)
    """
    erreurs = []
    
    for nom_csv in noms_csv:
        chemin = dossier_sortie / nom_csv
        
        if not chemin.exists():
            # Le fichier n'existe pas encore, c'est OK
            continue
        
        # On tente d'ouvrir en mode append pour vérifier l'accès en écriture
        try:
            with open(chemin, 'a', encoding='utf-8-sig'):
                pass
        except PermissionError:
            erreurs.append(
                f"Le fichier {nom_csv} est probablement ouvert dans Excel. "
                f"Fermez-le et relancez."
            )
    
    return erreurs

def lister_rapports(config):
    """Retourne la liste des fichiers .pbix et .rdl dans le dossier source."""
    dossier_rapports = Path(config['Chemins']['dossier_rapports'])
    rapports = list(dossier_rapports.glob("*.pbix"))
    rapports.extend(dossier_rapports.glob("*.rdl"))
    return rapports


def extraire_avec_pbi_tools(rapport, dossier_temp, chemin_pbi_tools):
    """
    Lance pbi-tools sur un fichier .pbix pour produire l'arborescence extraite.
    
    Returns:
        Path vers le dossier extrait, ou None en cas d'erreur
    """
    print(f"  Extraction en cours via pbi-tools...")
    
    # pbi-tools extract place le résultat à côté du .pbix par défaut
    # On utilise le paramètre -extractFolder pour le mettre dans notre dossier temp
    nom_dossier_extrait = rapport.stem  # nom du fichier sans extension
    dossier_extrait = dossier_temp / nom_dossier_extrait
    
    try:
        resultat = subprocess.run(
            [
                str(chemin_pbi_tools),
                "extract",
                str(rapport),
                "-extractFolder", str(dossier_extrait)
            ],
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes max par rapport
        )
        
        if resultat.returncode != 0:
            print(f"  [ERREUR] pbi-tools a échoué : {resultat.stderr}")
            return None
        
        if not dossier_extrait.exists():
            print(f"  [ERREUR] Le dossier d'extraction n'a pas été créé")
            return None
        
        return dossier_extrait
        
    except subprocess.TimeoutExpired:
        print(f"  [ERREUR] Timeout (>2min) lors de l'extraction")
        return None
    except Exception as e:
        print(f"  [ERREUR] Exception lors de l'extraction : {e}")
        return None


def ecrire_csv(donnees, chemin_sortie, colonnes):
    """Écrit une liste de dictionnaires dans un fichier CSV."""
    with open(chemin_sortie, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=colonnes, delimiter=';')
        writer.writeheader()
        writer.writerows(donnees)


def main():
    """Point d'entrée principal."""
    print("=" * 60)
    print("  EXTRACTION DE MÉTADONNÉES POWER BI")
    print("=" * 60)
    print()
    
    # Chargement config et vérifications (inchangé)
    config = charger_configuration()
    print("[OK] Configuration chargée")
    
    erreurs = verifier_environnement(config)
    if erreurs:
        print("\n[ERREUR] Problèmes détectés :")
        for erreur in erreurs:
            print(f"  - {erreur}")
        sys.exit(1)
    print("[OK] Environnement vérifié")
    
    # Vérification des fichiers de sortie
    noms_csv = [
        'ReportPages.csv', 'Visuals.csv', 'UsedFields.csv',
        'UsedTables.csv', 'UnusedFields.csv', 'UnusedTables.csv',
        'PaginatedReports.csv', 'PaginatedDataSources.csv',
        'PaginatedDataSets.csv', 'PaginatedFields.csv', 'PaginatedVisuals.csv'
    ]
    erreurs_fichiers = verifier_fichiers_sortie_accessibles(
        Path(config['Chemins']['dossier_sortie']), noms_csv
    )
    if erreurs_fichiers:
        print("\n[ERREUR] Fichiers de sortie inaccessibles :")
        for erreur in erreurs_fichiers:
            print(f"  - {erreur}")
        sys.exit(1)
    
    rapports = lister_rapports(config)
    if not rapports:
        print("\n[INFO] Aucun fichier .pbix ou .rdl trouvé.")
        sys.exit(0)
    
    print(f"\n[INFO] {len(rapports)} rapport(s) à traiter")
    
    # Récupération des chemins
    dossier_temp = Path(config['Chemins']['dossier_temp'])
    dossier_sortie = Path(config['Chemins']['dossier_sortie'])
    chemin_pbi_tools = Path(config['Chemins']['chemin_pbi_tools'])
    
    # Collecte des données Power BI classiques
    toutes_les_pages = []
    tous_les_visuels = []
    tous_les_champs = []
    tous_les_champs_modele = []
    
    # Collecte des données rapports paginés
    paginated_syntheses = []
    paginated_sources = []
    paginated_datasets = []
    paginated_fields = []
    paginated_visuels = []
    
    # Traitement de chaque rapport
    for i, rapport in enumerate(rapports, 1):
        print(f"\n[{i}/{len(rapports)}] Traitement : {rapport.name}")
        
        # Détection du type
        type_fichier = detecter_type_fichier(rapport)
        
        if type_fichier == TYPE_PBIX_CLASSIQUE:
            print(f"  [TYPE] Rapport Power BI classique")
            
            dossier_extrait = extraire_avec_pbi_tools(rapport, dossier_temp, chemin_pbi_tools)
            if dossier_extrait is None:
                print(f"  [SKIP] Rapport ignoré suite à l'erreur d'extraction")
                continue
            
            pages = parser_pages_rapport(dossier_extrait, rapport.stem)
            print(f"  [OK] {len(pages)} page(s) extraite(s)")
            toutes_les_pages.extend(pages)
            
            visuels = parser_visuels_rapport(dossier_extrait, rapport.stem)
            print(f"  [OK] {len(visuels)} visuel(s) extrait(s)")
            tous_les_visuels.extend(visuels)
            
            champs = parser_champs_rapport(dossier_extrait, rapport.stem)
            print(f"  [OK] {len(champs)} usage(s) de champ extrait(s)")
            tous_les_champs.extend(champs)
            
            champs_modele = parser_modele_rapport(dossier_extrait, rapport.stem)
            print(f"  [OK] {len(champs_modele)} champ(s) trouvé(s) dans le modèle")
            tous_les_champs_modele.extend(champs_modele)
        
        elif type_fichier == TYPE_RDL:
            print(f"  [TYPE] Rapport paginé (RDL)")
            
            resultat = parser_rapport_rdl(rapport, rapport.stem)
            if resultat is None:
                print(f"  [SKIP] Rapport paginé ignoré")
                continue
            
            paginated_syntheses.append(resultat['synthese'])
            paginated_sources.extend(resultat['sources'])
            paginated_datasets.extend(resultat['datasets'])
            paginated_fields.extend(resultat['fields'])
            paginated_visuels.extend(resultat['visuels'])
            
            print(f"  [OK] {len(resultat['datasets'])} dataset(s), "
                  f"{len(resultat['fields'])} champ(s), "
                  f"{len(resultat['visuels'])} visuel(s)")
        
        elif type_fichier == TYPE_PBIX_PAGINE:
            print(f"  [TYPE] Rapport paginé embarqué dans un .pbix")
            
            # Extraire le .rdl du conteneur
            chemin_rdl = extraire_rdl_du_pbix_pagine(rapport, dossier_temp)
            if chemin_rdl is None:
                print(f"  [SKIP] Impossible d'extraire le .rdl du .pbix")
                continue
            
            resultat = parser_rapport_rdl(chemin_rdl, rapport.stem)
            if resultat is None:
                print(f"  [SKIP] Rapport paginé ignoré")
                continue
            
            paginated_syntheses.append(resultat['synthese'])
            paginated_sources.extend(resultat['sources'])
            paginated_datasets.extend(resultat['datasets'])
            paginated_fields.extend(resultat['fields'])
            paginated_visuels.extend(resultat['visuels'])
            
            print(f"  [OK] {len(resultat['datasets'])} dataset(s), "
                  f"{len(resultat['fields'])} champ(s), "
                  f"{len(resultat['visuels'])} visuel(s)")
        
        else:
            print(f"  [SKIP] Type de fichier non reconnu")
    
    # Génération des CSV Power BI classiques
    print("\n[INFO] Génération des fichiers CSV...")
    
    if toutes_les_pages:
        chemin_csv = dossier_sortie / "ReportPages.csv"
        colonnes = ['NomRapport', 'NomPage', 'OrdrePage', 'Largeur', 'Hauteur', 'EstVisible', 'NbVisuels']
        ecrire_csv(toutes_les_pages, chemin_csv, colonnes)
        print(f"  [OK] ReportPages.csv : {len(toutes_les_pages)} ligne(s)")
    
    if tous_les_visuels:
        chemin_csv = dossier_sortie / "Visuals.csv"
        colonnes = ['NomRapport', 'NomPage', 'OrdrePage', 'TypeVisuel', 'Titre', 
                   'PositionX', 'PositionY', 'Largeur', 'Hauteur', 'AFiltre']
        ecrire_csv(tous_les_visuels, chemin_csv, colonnes)
        print(f"  [OK] Visuals.csv : {len(tous_les_visuels)} ligne(s)")
    
    if tous_les_champs:
        chemin_csv = dossier_sortie / "UsedFields.csv"
        colonnes = ['NomRapport', 'NomPage', 'TypeVisuel', 'NomTable', 'NomChamp', 'TypeChamp', 'Agregation']
        ecrire_csv(tous_les_champs, chemin_csv, colonnes)
        print(f"  [OK] UsedFields.csv : {len(tous_les_champs)} ligne(s)")
        
        tables_utilisees = agreger_tables_utilisees(tous_les_champs)
        if tables_utilisees:
            chemin_csv = dossier_sortie / "UsedTables.csv"
            colonnes = ['NomRapport', 'NomTable', 'NbChampsUtilises', 'NbVisuelsUtilisant']
            ecrire_csv(tables_utilisees, chemin_csv, colonnes)
            print(f"  [OK] UsedTables.csv : {len(tables_utilisees)} ligne(s)")
    
    if tous_les_champs_modele:
        champs_non_utilises = calculer_champs_non_utilises(tous_les_champs_modele, tous_les_champs)
        if champs_non_utilises:
            chemin_csv = dossier_sortie / "UnusedFields.csv"
            colonnes = ['NomRapport', 'NomTable', 'NomChamp', 'TypeChamp', 'EstMasque']
            ecrire_csv(champs_non_utilises, chemin_csv, colonnes)
            print(f"  [OK] UnusedFields.csv : {len(champs_non_utilises)} ligne(s)")
        
        tables_non_utilisees = calculer_tables_non_utilisees(tous_les_champs_modele, tous_les_champs)
        if tables_non_utilisees:
            chemin_csv = dossier_sortie / "UnusedTables.csv"
            colonnes = ['NomRapport', 'NomTable', 'NbColonnes', 'NbMesures', 'EstMasqueeGlobalement']
            ecrire_csv(tables_non_utilisees, chemin_csv, colonnes)
            print(f"  [OK] UnusedTables.csv : {len(tables_non_utilisees)} ligne(s)")
    
    # Génération des CSV rapports paginés
    if paginated_syntheses:
        chemin_csv = dossier_sortie / "PaginatedReports.csv"
        colonnes = ['NomRapport', 'NbDataSources', 'NbDataSets', 'NbChampsTotal',
                   'NbParametres', 'NbTablix', 'NbCharts', 'NbTextbox', 'NbSubreports']
        ecrire_csv(paginated_syntheses, chemin_csv, colonnes)
        print(f"  [OK] PaginatedReports.csv : {len(paginated_syntheses)} ligne(s)")
    
    if paginated_sources:
        chemin_csv = dossier_sortie / "PaginatedDataSources.csv"
        colonnes = ['NomRapport', 'NomSource', 'Provider', 'ConnectString', 'AuthMode']
        ecrire_csv(paginated_sources, chemin_csv, colonnes)
        print(f"  [OK] PaginatedDataSources.csv : {len(paginated_sources)} ligne(s)")
    
    if paginated_datasets:
        chemin_csv = dossier_sortie / "PaginatedDataSets.csv"
        colonnes = ['NomRapport', 'NomDataSet', 'NomSource', 'TypeCommande', 'NbChamps', 'ExtraitRequete']
        ecrire_csv(paginated_datasets, chemin_csv, colonnes)
        print(f"  [OK] PaginatedDataSets.csv : {len(paginated_datasets)} ligne(s)")
    
    if paginated_fields:
        chemin_csv = dossier_sortie / "PaginatedFields.csv"
        colonnes = ['NomRapport', 'NomDataSet', 'NomChamp', 'SourceField', 'Formule']
        ecrire_csv(paginated_fields, chemin_csv, colonnes)
        print(f"  [OK] PaginatedFields.csv : {len(paginated_fields)} ligne(s)")
    
    if paginated_visuels:
        chemin_csv = dossier_sortie / "PaginatedVisuals.csv"
        colonnes = ['NomRapport', 'NomVisuel', 'TypeVisuel', 'SousType', 'NomDataSet']
        ecrire_csv(paginated_visuels, chemin_csv, colonnes)
        print(f"  [OK] PaginatedVisuals.csv : {len(paginated_visuels)} ligne(s)")
    
    print("\nTerminé.")


if __name__ == "__main__":
    main()