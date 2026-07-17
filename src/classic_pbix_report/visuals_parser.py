"""
Parser des visuels d'un rapport Power BI extrait par pbi-tools.
Lit les fichiers config.json dans Report/sections/*/visualContainers/*/ 
et produit une ligne de données par visuel.
"""

import json
from pathlib import Path
from classic_pbix_report.pages_parser import decoder_nom_fichier, extraire_ordre_page


def extraire_titre_visuel(config_data):
    """
    Tente d'extraire le titre du visuel depuis sa configuration.
    Le titre peut être stocké à plusieurs endroits selon le type de visuel.
    
    Args:
        config_data: dict, contenu du config.json du visuel
    
    Returns:
        str, le titre ou chaîne vide si non trouvé
    """
    try:
        # Chemin courant pour le titre dans Power BI
        title_objects = config_data.get('singleVisual', {}).get('vcObjects', {}).get('title', [])
        if title_objects:
            properties = title_objects[0].get('properties', {})
            text = properties.get('text', {})
            
            # Le titre peut être une chaîne littérale ou une expression
            if isinstance(text, dict):
                expr = text.get('expr', {})
                literal = expr.get('Literal', {})
                if 'Value' in literal:
                    # Le format est souvent "'mon titre'" avec apostrophes
                    valeur = literal['Value']
                    return valeur.strip("'\"")
    except (AttributeError, KeyError, IndexError):
        pass
    
    return ""


def a_des_filtres(dossier_visuel):
    """
    Vérifie si le visuel a un fichier filters.json non vide.
    
    Returns:
        str, "Oui" ou "Non"
    """
    fichier_filtres = dossier_visuel / "filters.json"
    
    if not fichier_filtres.exists():
        return "Non"
    
    try:
        with open(fichier_filtres, 'r', encoding='utf-8') as f:
            contenu = json.load(f)
        
        # filters.json contient généralement une liste de filtres
        # Si la liste est vide ou nulle, pas de filtre
        if isinstance(contenu, list) and len(contenu) > 0:
            return "Oui"
        return "Non"
    except (json.JSONDecodeError, IOError):
        return "Non"


def parser_visuel(dossier_visuel, nom_rapport, nom_page, ordre_page):
    """
    Lit le fichier config.json d'un visuel et extrait les informations utiles.
    
    Args:
        dossier_visuel: Path vers le dossier du visuel
        nom_rapport: nom du rapport parent
        nom_page: nom de la page parente
        ordre_page: numéro d'ordre de la page
    
    Returns:
        dict avec les informations du visuel, ou None en cas d'erreur
    """
    fichier_config = dossier_visuel / "config.json"
    
    if not fichier_config.exists():
        print(f"    [AVERTISSEMENT] config.json introuvable dans {dossier_visuel.name}")
        return None
    
    try:
        with open(fichier_config, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"    [ERREUR] JSON invalide dans {fichier_config} : {e}")
        return None
    
    # Récupération du type de visuel
    single_visual = data.get('singleVisual', {})
    type_visuel = single_visual.get('visualType', 'inconnu')
    
    # Récupération de la position et taille (premier layout)
    layouts = data.get('layouts', [])
    if layouts:
        position = layouts[0].get('position', {})
        x = round(position.get('x', 0), 1)
        y = round(position.get('y', 0), 1)
        largeur = round(position.get('width', 0), 1)
        hauteur = round(position.get('height', 0), 1)
    else:
        x = y = largeur = hauteur = 0
    
    # Extraction du titre
    titre = extraire_titre_visuel(data)
    
    # Vérification des filtres
    a_filtre = a_des_filtres(dossier_visuel)
    
    return {
        'NomRapport': nom_rapport,
        'NomPage': nom_page,
        'OrdrePage': ordre_page,
        'TypeVisuel': type_visuel,
        'Titre': titre,
        'PositionX': x,
        'PositionY': y,
        'Largeur': largeur,
        'Hauteur': hauteur,
        'AFiltre': a_filtre
    }


def parser_visuels_rapport(dossier_rapport_extrait, nom_rapport):
    """
    Parse tous les visuels d'un rapport extrait par pbi-tools.
    
    Args:
        dossier_rapport_extrait: Path vers le dossier extrait
        nom_rapport: nom du rapport (sans extension)
    
    Returns:
        liste de dictionnaires, un par visuel
    """
    dossier_sections = dossier_rapport_extrait / "Report" / "sections"
    
    if not dossier_sections.exists():
        return []
    
    visuels = []
    
    # On parcourt chaque page (dossier de section)
    dossiers_pages = sorted([
        d for d in dossier_sections.iterdir() 
        if d.is_dir()
    ])
    
    for dossier_page in dossiers_pages:
        # Récupération du nom et de l'ordre de la page
        ordre_page = extraire_ordre_page(dossier_page.name)
        
        # On lit section.json pour récupérer le displayName officiel
        fichier_section = dossier_page / "section.json"
        nom_page = ""
        if fichier_section.exists():
            try:
                with open(fichier_section, 'r', encoding='utf-8') as f:
                    section_data = json.load(f)
                nom_page = section_data.get('displayName', '').strip()
            except json.JSONDecodeError:
                nom_page = decoder_nom_fichier(dossier_page.name)
        
        # Parcours des visuels de la page
        dossier_visuels = dossier_page / "visualContainers"
        if not dossier_visuels.exists():
            continue
        
        dossiers_visuels = sorted([
            d for d in dossier_visuels.iterdir() 
            if d.is_dir()
        ])
        
        for dossier_visuel in dossiers_visuels:
            visuel = parser_visuel(dossier_visuel, nom_rapport, nom_page, ordre_page)
            if visuel is not None:
                visuels.append(visuel)
    
    return visuels