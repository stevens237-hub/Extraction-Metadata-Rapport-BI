"""
Parser du modèle de données d'un rapport Power BI extrait par pbi-tools.
Lit les fichiers TMDL dans Model/tables/ pour produire l'inventaire complet
des tables, colonnes et mesures définies dans le modèle.
"""

import re
from pathlib import Path


# Préfixes de noms de fichiers qui correspondent à des tables système
# (générées automatiquement par Power BI, à ignorer dans l'inventaire)
PREFIXES_TABLES_SYSTEME = (
    'DateTableTemplate_',
    'LocalDateTable_',
)


def decoder_nom_fichier(nom):
    """
    Décode les caractères Unicode encodés dans les noms de fichiers.
    Exemple : 'Priorit#U00e9.tmdl' devient 'Priorité.tmdl'
    """
    def remplacer(match):
        return chr(int(match.group(1), 16))
    
    return re.sub(r'#U([0-9a-fA-F]{4})', remplacer, nom)


def est_table_systeme(nom_fichier):
    """
    Détermine si un fichier TMDL correspond à une table système
    générée automatiquement par Power BI.
    """
    return nom_fichier.startswith(PREFIXES_TABLES_SYSTEME)


def extraire_nom_table(lignes):
    """
    Extrait le nom de la table depuis la première ligne TMDL.
    
    Exemple de ligne : "table Incidents" ou "table 'Nom avec espaces'"
    """
    for ligne in lignes:
        ligne_strip = ligne.strip()
        if ligne_strip.startswith('table '):
            nom = ligne_strip[6:].strip()  # on enlève "table "
            # Supprime les apostrophes si le nom est entre apostrophes
            if nom.startswith("'") and nom.endswith("'"):
                nom = nom[1:-1]
            return nom
    return None


def detecter_debut_objet(ligne):
    """
    Détecte si une ligne marque le début d'une colonne ou d'une mesure.
    
    Returns:
        tuple (type_objet, nom_objet) ou (None, None)
        type_objet vaut 'Colonne' ou 'Mesure'
    """
    ligne_strip = ligne.strip()
    
    # Détection des mesures : "measure 'Nom mesure' = ..." ou "measure NomSansEspace = ..."
    match_measure = re.match(r"^measure\s+(?:'([^']+)'|(\S+?))\s*=", ligne_strip)
    if match_measure:
        nom = match_measure.group(1) or match_measure.group(2)
        return ('Mesure', nom)
    
    # Détection des colonnes : "column NomColonne" ou "column 'Nom avec espaces'"
    match_column = re.match(r"^column\s+(?:'([^']+)'|(\S+))", ligne_strip)
    if match_column:
        nom = match_column.group(1) or match_column.group(2)
        return ('Colonne', nom)
    
    return (None, None)


def est_objet_cache(lignes_bloc):
    """
    Détermine si un objet (colonne ou mesure) est marqué comme caché.
    Cherche la ligne 'changedProperty = IsHidden' dans le bloc de l'objet.
    """
    for ligne in lignes_bloc:
        if 'changedProperty' in ligne and 'IsHidden' in ligne:
            return True
    return False


def parser_fichier_tmdl(chemin_fichier, nom_rapport):
    """
    Parse un fichier TMDL pour extraire la table, ses colonnes et ses mesures.
    
    Args:
        chemin_fichier: Path vers le fichier .tmdl
        nom_rapport: nom du rapport (pour la colonne NomRapport du CSV)
    
    Returns:
        liste de dictionnaires, un par champ (colonne ou mesure) trouvé
    """
    try:
        with open(chemin_fichier, 'r', encoding='utf-8-sig') as f:
            lignes = f.readlines()
    except IOError as e:
        print(f"    [ERREUR] Impossible de lire {chemin_fichier.name} : {e}")
        return []
    
    # Récupération du nom de la table
    nom_table = extraire_nom_table(lignes)
    if nom_table is None:
        print(f"    [AVERTISSEMENT] Table sans nom dans {chemin_fichier.name}")
        return []
    
    # Parcours du fichier pour extraire les colonnes et mesures
    champs = []
    objet_courant = None
    lignes_objet_courant = []
    
    for ligne in lignes:
        # On détecte si on commence un nouvel objet (column ou measure)
        type_objet, nom_objet = detecter_debut_objet(ligne)
        
        if type_objet is not None:
            # On termine l'objet précédent s'il y en avait un
            if objet_courant is not None:
                est_cache = est_objet_cache(lignes_objet_courant)
                champs.append({
                    'NomRapport': nom_rapport,
                    'NomTable': nom_table,
                    'NomChamp': objet_courant['nom'],
                    'TypeChamp': objet_courant['type'],
                    'EstMasque': 'Oui' if est_cache else 'Non'
                })
            
            # On démarre le nouvel objet
            objet_courant = {'type': type_objet, 'nom': nom_objet}
            lignes_objet_courant = [ligne]
        else:
            # On continue à accumuler les lignes de l'objet courant
            if objet_courant is not None:
                lignes_objet_courant.append(ligne)
    
    # Ne pas oublier le dernier objet du fichier
    if objet_courant is not None:
        est_cache = est_objet_cache(lignes_objet_courant)
        champs.append({
            'NomRapport': nom_rapport,
            'NomTable': nom_table,
            'NomChamp': objet_courant['nom'],
            'TypeChamp': objet_courant['type'],
            'EstMasque': 'Oui' if est_cache else 'Non'
        })
    
    return champs


def parser_modele_rapport(dossier_rapport_extrait, nom_rapport):
    """
    Parse tous les fichiers TMDL du modèle d'un rapport.
    Ignore les tables système (LocalDateTable, DateTableTemplate, etc.).
    
    Args:
        dossier_rapport_extrait: Path vers le dossier extrait
        nom_rapport: nom du rapport (sans extension)
    
    Returns:
        liste de dictionnaires avec tous les champs du modèle
    """
    dossier_tables = dossier_rapport_extrait / "Model" / "tables"
    
    if not dossier_tables.exists():
        print(f"  [ERREUR] Dossier Model/tables introuvable pour {nom_rapport}")
        return []
    
    tous_les_champs = []
    
    for fichier_tmdl in sorted(dossier_tables.glob("*.tmdl")):
        # Ignorer les tables système
        if est_table_systeme(fichier_tmdl.name):
            continue
        
        champs = parser_fichier_tmdl(fichier_tmdl, nom_rapport)
        tous_les_champs.extend(champs)
    
    return tous_les_champs