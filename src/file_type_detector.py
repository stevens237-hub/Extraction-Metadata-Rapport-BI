"""
Détection du type de fichier Power BI :
- .pbix classique (avec modèle et rapport)
- .rdl (rapport paginé standalone)
- .pbix paginé (conteneur ZIP avec un .rdl à l'intérieur)
"""

import zipfile
from pathlib import Path

from logging_config import obtenir_logger

logger = obtenir_logger()


TYPE_PBIX_CLASSIQUE = 'pbix_classique'
TYPE_RDL = 'rdl'
TYPE_PBIX_PAGINE = 'pbix_pagine'
TYPE_INCONNU = 'inconnu'


def detecter_type_fichier(chemin_fichier):
    """
    Détermine le type d'un fichier Power BI.
    
    Args:
        chemin_fichier: Path vers le fichier à analyser
    
    Returns:
        str : une des constantes TYPE_* définies ci-dessus
    """
    chemin = Path(chemin_fichier)
    extension = chemin.suffix.lower()
    
    # Cas simple : fichier RDL standalone
    if extension == '.rdl':
        return TYPE_RDL
    
    # Cas .pbix : il faut regarder à l'intérieur pour distinguer classique vs paginé
    if extension == '.pbix':
        try:
            with zipfile.ZipFile(chemin, 'r') as zf:
                noms_fichiers = zf.namelist()
                
                # Un .pbix paginé contient un fichier .rdl à sa racine
                for nom in noms_fichiers:
                    if nom.lower().endswith('.rdl'):
                        return TYPE_PBIX_PAGINE
                
                # Sinon c'est un .pbix classique
                return TYPE_PBIX_CLASSIQUE
                
        except zipfile.BadZipFile:
            logger.error(f"  [ERREUR] Fichier corrompu ou non-ZIP : {chemin.name}")
            return TYPE_INCONNU
    
    return TYPE_INCONNU


def extraire_rdl_du_pbix_pagine(chemin_pbix, dossier_sortie):
    """
    Extrait le fichier .rdl contenu dans un .pbix paginé.
    
    Args:
        chemin_pbix: Path vers le fichier .pbix paginé
        dossier_sortie: Path vers le dossier où extraire le .rdl
    
    Returns:
        Path vers le fichier .rdl extrait, ou None en cas d'erreur
    """
    chemin = Path(chemin_pbix)
    
    try:
        with zipfile.ZipFile(chemin, 'r') as zf:
            for nom in zf.namelist():
                if nom.lower().endswith('.rdl'):
                    # Extraction dans le dossier de sortie
                    dossier_sortie.mkdir(parents=True, exist_ok=True)
                    chemin_rdl = dossier_sortie / f"{chemin.stem}.rdl"
                    
                    with zf.open(nom) as source, open(chemin_rdl, 'wb') as cible:
                        cible.write(source.read())
                    
                    return chemin_rdl
        
        return None
    
    except zipfile.BadZipFile:
        return None