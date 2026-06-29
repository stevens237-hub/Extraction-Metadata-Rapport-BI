"""
Parser des pages d'un rapport Power BI extrait par pbi-tools.
Lit les fichiers section.json dans Report/sections/*/ et produit
une ligne de données par page.
"""

import json
import re
from pathlib import Path


def decoder_nom_fichier(nom):
    """
    Décode les caractères Unicode encodés dans les noms de fichiers/dossiers
    générés par pbi-tools.
    
    Exemple : 'Tableau d#U00e9tails' devient 'Tableau détails'
    """
    def remplacer(match):
        code_hex = match.group(1)
        return chr(int(code_hex, 16))
    
    return re.sub(r'#U([0-9a-fA-F]{4})', remplacer, nom)


def extraire_ordre_page(nom_dossier):
    """
    Extrait le numéro d'ordre depuis le nom du dossier de section.
    
    Exemple : '001_Tableau détails incidents' renvoie 1
    """
    match = re.match(r'^(\d+)_', nom_dossier)
    if match:
        return int(match.group(1))
    return None


def parser_page(dossier_section, nom_rapport):
    """
    Lit le fichier section.json d'une page et retourne un dictionnaire
    avec les informations à inclure dans le CSV.
    
    Args:
        dossier_section: Path vers le dossier de la section (ex: 'Report/sections/001_...')
        nom_rapport: nom du rapport parent (sans extension)
    
    Returns:
        dict avec les informations de la page, ou None en cas d'erreur
    """
    fichier_section = dossier_section / "section.json"
    
    if not fichier_section.exists():
        print(f"  [AVERTISSEMENT] section.json introuvable dans {dossier_section.name}")
        return None
    
    try:
        with open(fichier_section, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  [ERREUR] JSON invalide dans {fichier_section} : {e}")
        return None
    
    # Comptage des visuels dans la page
    dossier_visuels = dossier_section / "visualContainers"
    nb_visuels = 0
    if dossier_visuels.exists():
        nb_visuels = len([d for d in dossier_visuels.iterdir() if d.is_dir()])
    
    # Décodage du nom de dossier pour récupérer l'ordre
    nom_dossier_decode = decoder_nom_fichier(dossier_section.name)
    ordre = extraire_ordre_page(dossier_section.name)
    
    # displayOption : 1 = visible, 2 = masquée, 3 = masquée mobile
    display_option = data.get('displayOption', 1)
    est_visible = "Oui" if display_option == 1 else "Non"
    
    return {
        'NomRapport': nom_rapport,
        'NomPage': data.get('displayName', '').strip(),
        'OrdrePage': ordre,
        'Largeur': data.get('width', ''),
        'Hauteur': data.get('height', ''),
        'EstVisible': est_visible,
        'NbVisuels': nb_visuels
    }


def parser_pages_rapport(dossier_rapport_extrait, nom_rapport):
    """
    Parse toutes les pages d'un rapport extrait par pbi-tools.
    
    Args:
        dossier_rapport_extrait: Path vers le dossier extrait (ex: '.../Suivi Backlog DHS FR-EN/')
        nom_rapport: nom du rapport (sans extension .pbix)
    
    Returns:
        liste de dictionnaires, un par page
    """
    dossier_sections = dossier_rapport_extrait / "Report" / "sections"
    
    if not dossier_sections.exists():
        print(f"  [ERREUR] Dossier Report/sections introuvable pour {nom_rapport}")
        return []
    
    # On récupère tous les sous-dossiers (un par page)
    dossiers_pages = sorted([
        d for d in dossier_sections.iterdir() 
        if d.is_dir()
    ])
    
    pages = []
    for dossier_page in dossiers_pages:
        page = parser_page(dossier_page, nom_rapport)
        if page is not None:
            pages.append(page)
    
    return pages