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
from pages_parser import parser_pages_rapport


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


def lister_rapports(config):
    """Retourne la liste des fichiers .pbix dans le dossier source."""
    dossier_rapports = Path(config['Chemins']['dossier_rapports'])
    rapports = list(dossier_rapports.glob("*.pbix"))
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
    
    # Chargement de la configuration
    config = charger_configuration()
    print("[OK] Configuration chargée")
    
    # Vérification de l'environnement
    erreurs = verifier_environnement(config)
    if erreurs:
        print("\n[ERREUR] Problèmes détectés :")
        for erreur in erreurs:
            print(f"  - {erreur}")
        sys.exit(1)
    print("[OK] Environnement vérifié")
    
    # Listing des rapports à traiter
    rapports = lister_rapports(config)
    if not rapports:
        print("\n[INFO] Aucun fichier .pbix trouvé dans le dossier source.")
        sys.exit(0)
    
    print(f"\n[INFO] {len(rapports)} rapport(s) à traiter")
    
    # Récupération des chemins de configuration
    dossier_temp = Path(config['Chemins']['dossier_temp'])
    dossier_sortie = Path(config['Chemins']['dossier_sortie'])
    chemin_pbi_tools = Path(config['Chemins']['chemin_pbi_tools'])
    
    # Collecte des données de toutes les pages
    toutes_les_pages = []
    
    for i, rapport in enumerate(rapports, 1):
        print(f"\n[{i}/{len(rapports)}] Traitement : {rapport.name}")
        
        # Étape 1 : extraction du .pbix avec pbi-tools
        dossier_extrait = extraire_avec_pbi_tools(rapport, dossier_temp, chemin_pbi_tools)
        if dossier_extrait is None:
            print(f"  [SKIP] Rapport ignoré suite à l'erreur d'extraction")
            continue
        
        # Étape 2 : parsing des pages
        pages = parser_pages_rapport(dossier_extrait, rapport.stem)
        print(f"  [OK] {len(pages)} page(s) extraite(s)")
        
        toutes_les_pages.extend(pages)
    
    # Écriture du CSV consolidé
    if toutes_les_pages:
        chemin_csv = dossier_sortie / "ReportPages.csv"
        colonnes = ['NomRapport', 'NomPage', 'OrdrePage', 'Largeur', 'Hauteur', 'EstVisible', 'NbVisuels']
        ecrire_csv(toutes_les_pages, chemin_csv, colonnes)
        print(f"\n[OK] Fichier généré : {chemin_csv}")
        print(f"     {len(toutes_les_pages)} ligne(s) au total")
    else:
        print("\n[INFO] Aucune page à exporter.")
    
    print("\nTerminé.")


if __name__ == "__main__":
    main()