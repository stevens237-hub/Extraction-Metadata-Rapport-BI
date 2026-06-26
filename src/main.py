"""
Outil d'extraction automatique des métadonnées de rapports Power BI.
Orchestrateur principal.
"""

import configparser
import os
import sys
from pathlib import Path


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
    
    # On crée les dossiers de sortie et temp s'ils n'existent pas
    dossier_sortie = Path(config['Chemins']['dossier_sortie'])
    dossier_sortie.mkdir(parents=True, exist_ok=True)
    
    dossier_temp = Path(config['Chemins']['dossier_temp'])
    dossier_temp.mkdir(parents=True, exist_ok=True)
    
    return erreurs


def lister_rapports(config):
    """Retourne la liste des fichiers .pbix dans le dossier source."""
    dossier_rapports = Path(config['Chemins']['dossier_rapports'])
    rapports = list(dossier_rapports.glob("*.pbix"))
    return rapports


def main():
    """Point d'entrée principal."""
    print("=" * 60)
    print("  EXTRACTION DE MÉTADONNÉES POWER BI")
    print("=" * 60)
    print()
    
    # Chargement de la configuration
    config = charger_configuration()
    print("[OK] Configuration chargée")
    
    # Vérification de l'environnement
    erreurs = verifier_environnement(config)
    if erreurs:
        print("\n[ERREUR] Problèmes détectés dans la configuration :")
        for erreur in erreurs:
            print(f"  - {erreur}")
        sys.exit(1)
    print("[OK] Environnement vérifié")
    
    # Listing des rapports à traiter
    rapports = lister_rapports(config)
    if not rapports:
        print("\n[INFO] Aucun fichier .pbix trouvé dans le dossier source.")
        sys.exit(0)
    
    print(f"\n[INFO] {len(rapports)} rapport(s) à traiter :")
    for r in rapports:
        print(f"  - {r.name}")
    
    print("\n[INFO] Le traitement des rapports sera implémenté à l'étape suivante.")
    print("\nTerminé.")


if __name__ == "__main__":
    main()