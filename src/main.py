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
from csv_config import FICHIERS_CSV_CLASSIQUES, FICHIERS_CSV_PAGINES, NOMS_FICHIERS_CSV
from logging_config import configurer_logging, obtenir_logger

logger = obtenir_logger()


def charger_configuration():
    """Lit le fichier config.ini situé à la racine du projet."""
    chemin_config = Path(__file__).parent.parent / "config.ini"

    if not chemin_config.exists():
        logger.error(f"[ERREUR] Fichier config.ini introuvable : {chemin_config}")
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
    logger.info("  Extraction en cours via pbi-tools...")

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
            logger.error(f"  [ERREUR] pbi-tools a échoué : {resultat.stderr}")
            return None

        if not dossier_extrait.exists():
            logger.error("  [ERREUR] Le dossier d'extraction n'a pas été créé")
            return None

        return dossier_extrait

    except subprocess.TimeoutExpired:
        logger.error("  [ERREUR] Timeout (>2min) lors de l'extraction")
        return None
    except Exception as e:
        logger.error(f"  [ERREUR] Exception lors de l'extraction : {e}")
        return None


def ecrire_csv(donnees, chemin_sortie, colonnes):
    """Écrit une liste de dictionnaires dans un fichier CSV."""
    with open(chemin_sortie, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=colonnes, delimiter=';')
        writer.writeheader()
        writer.writerows(donnees)


def ecrire_csv_si_donnees(donnees, nom_fichier, colonnes, dossier_sortie):
    """Écrit le CSV s'il y a des données et logue le résultat."""
    if not donnees:
        return
    chemin_csv = dossier_sortie / nom_fichier
    ecrire_csv(donnees, chemin_csv, colonnes)
    logger.info(f"  [OK] {nom_fichier} : {len(donnees)} ligne(s)")


def main():
    """Point d'entrée principal."""
    configurer_logging()
    logger.info("=" * 60)
    logger.info("  EXTRACTION DE MÉTADONNÉES POWER BI")
    logger.info("=" * 60)
    logger.info("")

    # Chargement config et vérifications (inchangé)
    config = charger_configuration()
    logger.info("[OK] Configuration chargée")

    erreurs = verifier_environnement(config)
    if erreurs:
        logger.error("\n[ERREUR] Problèmes détectés :")
        for erreur in erreurs:
            logger.error(f"  - {erreur}")
        sys.exit(1)
    logger.info("[OK] Environnement vérifié")

    # Une fois le dossier de sortie garanti, on y duplique aussi les logs
    dossier_sortie = Path(config['Chemins']['dossier_sortie'])
    configurer_logging(fichier_log=dossier_sortie / "extraction.log")

    # Vérification des fichiers de sortie
    erreurs_fichiers = verifier_fichiers_sortie_accessibles(dossier_sortie, NOMS_FICHIERS_CSV)
    if erreurs_fichiers:
        logger.error("\n[ERREUR] Fichiers de sortie inaccessibles :")
        for erreur in erreurs_fichiers:
            logger.error(f"  - {erreur}")
        sys.exit(1)

    rapports = lister_rapports(config)
    if not rapports:
        logger.info("\n[INFO] Aucun fichier .pbix ou .rdl trouvé.")
        sys.exit(0)

    logger.info(f"\n[INFO] {len(rapports)} rapport(s) à traiter")

    # Récupération des chemins
    dossier_temp = Path(config['Chemins']['dossier_temp'])
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
        logger.info(f"\n[{i}/{len(rapports)}] Traitement : {rapport.name}")

        # Détection du type
        type_fichier = detecter_type_fichier(rapport)

        if type_fichier == TYPE_PBIX_CLASSIQUE:
            logger.info("  [TYPE] Rapport Power BI classique")

            dossier_extrait = extraire_avec_pbi_tools(rapport, dossier_temp, chemin_pbi_tools)
            if dossier_extrait is None:
                logger.warning("  [SKIP] Rapport ignoré suite à l'erreur d'extraction")
                continue

            pages = parser_pages_rapport(dossier_extrait, rapport.stem)
            logger.info(f"  [OK] {len(pages)} page(s) extraite(s)")
            toutes_les_pages.extend(pages)

            visuels = parser_visuels_rapport(dossier_extrait, rapport.stem)
            logger.info(f"  [OK] {len(visuels)} visuel(s) extrait(s)")
            tous_les_visuels.extend(visuels)

            champs = parser_champs_rapport(dossier_extrait, rapport.stem)
            logger.info(f"  [OK] {len(champs)} usage(s) de champ extrait(s)")
            tous_les_champs.extend(champs)

            champs_modele = parser_modele_rapport(dossier_extrait, rapport.stem)
            logger.info(f"  [OK] {len(champs_modele)} champ(s) trouvé(s) dans le modèle")
            tous_les_champs_modele.extend(champs_modele)

        elif type_fichier == TYPE_RDL:
            logger.info("  [TYPE] Rapport paginé (RDL)")

            resultat = parser_rapport_rdl(rapport, rapport.stem)
            if resultat is None:
                logger.warning("  [SKIP] Rapport paginé ignoré")
                continue

            paginated_syntheses.append(resultat['synthese'])
            paginated_sources.extend(resultat['sources'])
            paginated_datasets.extend(resultat['datasets'])
            paginated_fields.extend(resultat['fields'])
            paginated_visuels.extend(resultat['visuels'])

            logger.info(f"  [OK] {len(resultat['datasets'])} dataset(s), "
                        f"{len(resultat['fields'])} champ(s), "
                        f"{len(resultat['visuels'])} visuel(s)")

        elif type_fichier == TYPE_PBIX_PAGINE:
            logger.info("  [TYPE] Rapport paginé embarqué dans un .pbix")

            # Extraire le .rdl du conteneur
            chemin_rdl = extraire_rdl_du_pbix_pagine(rapport, dossier_temp)
            if chemin_rdl is None:
                logger.warning("  [SKIP] Impossible d'extraire le .rdl du .pbix")
                continue

            resultat = parser_rapport_rdl(chemin_rdl, rapport.stem)
            if resultat is None:
                logger.warning("  [SKIP] Rapport paginé ignoré")
                continue

            paginated_syntheses.append(resultat['synthese'])
            paginated_sources.extend(resultat['sources'])
            paginated_datasets.extend(resultat['datasets'])
            paginated_fields.extend(resultat['fields'])
            paginated_visuels.extend(resultat['visuels'])

            logger.info(f"  [OK] {len(resultat['datasets'])} dataset(s), "
                        f"{len(resultat['fields'])} champ(s), "
                        f"{len(resultat['visuels'])} visuel(s)")

        else:
            logger.warning("  [SKIP] Type de fichier non reconnu")

    # Génération des CSV Power BI classiques
    logger.info("\n[INFO] Génération des fichiers CSV...")

    ecrire_csv_si_donnees(toutes_les_pages, 'ReportPages.csv',
                           FICHIERS_CSV_CLASSIQUES['ReportPages.csv'], dossier_sortie)
    ecrire_csv_si_donnees(tous_les_visuels, 'Visuals.csv',
                           FICHIERS_CSV_CLASSIQUES['Visuals.csv'], dossier_sortie)
    ecrire_csv_si_donnees(tous_les_champs, 'UsedFields.csv',
                           FICHIERS_CSV_CLASSIQUES['UsedFields.csv'], dossier_sortie)

    if tous_les_champs:
        tables_utilisees = agreger_tables_utilisees(tous_les_champs)
        ecrire_csv_si_donnees(tables_utilisees, 'UsedTables.csv',
                               FICHIERS_CSV_CLASSIQUES['UsedTables.csv'], dossier_sortie)

    if tous_les_champs_modele:
        champs_non_utilises = calculer_champs_non_utilises(tous_les_champs_modele, tous_les_champs)
        ecrire_csv_si_donnees(champs_non_utilises, 'UnusedFields.csv',
                               FICHIERS_CSV_CLASSIQUES['UnusedFields.csv'], dossier_sortie)

        tables_non_utilisees = calculer_tables_non_utilisees(tous_les_champs_modele, tous_les_champs)
        ecrire_csv_si_donnees(tables_non_utilisees, 'UnusedTables.csv',
                               FICHIERS_CSV_CLASSIQUES['UnusedTables.csv'], dossier_sortie)

    # Génération des CSV rapports paginés
    ecrire_csv_si_donnees(paginated_syntheses, 'PaginatedReports.csv',
                           FICHIERS_CSV_PAGINES['PaginatedReports.csv'], dossier_sortie)
    ecrire_csv_si_donnees(paginated_sources, 'PaginatedDataSources.csv',
                           FICHIERS_CSV_PAGINES['PaginatedDataSources.csv'], dossier_sortie)
    ecrire_csv_si_donnees(paginated_datasets, 'PaginatedDataSets.csv',
                           FICHIERS_CSV_PAGINES['PaginatedDataSets.csv'], dossier_sortie)
    ecrire_csv_si_donnees(paginated_fields, 'PaginatedFields.csv',
                           FICHIERS_CSV_PAGINES['PaginatedFields.csv'], dossier_sortie)
    ecrire_csv_si_donnees(paginated_visuels, 'PaginatedVisuals.csv',
                           FICHIERS_CSV_PAGINES['PaginatedVisuals.csv'], dossier_sortie)

    logger.info("\nTerminé.")


if __name__ == "__main__":
    main()
