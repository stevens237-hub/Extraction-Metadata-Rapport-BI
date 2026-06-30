"""
Parser des champs utilisés dans les visuels d'un rapport Power BI.
Lit les fichiers config.json dans Report/sections/*/visualContainers/*/
et extrait la liste des mesures et colonnes utilisées par chaque visuel.
"""

import json
from pathlib import Path
from pages_parser import extraire_ordre_page


def construire_dictionnaire_alias(from_section):
    """
    Construit un dictionnaire {alias: nom_table} depuis la section From
    d'un prototypeQuery.
    
    Exemple : [{"Name": "i", "Entity": "Incidents"}] devient {"i": "Incidents"}
    """
    alias = {}
    for entry in from_section:
        nom_alias = entry.get('Name', '')
        nom_table = entry.get('Entity', '')
        if nom_alias and nom_table:
            alias[nom_alias] = nom_table
    return alias


def extraire_champ(select_entry, alias_table):
    """
    Extrait les informations d'un champ depuis une entrée 'Select' du prototypeQuery.
    
    Args:
        select_entry: dict, une entrée de la liste 'Select'
        alias_table: dict, le dictionnaire des alias {alias: nom_table}
    
    Returns:
        dict avec NomTable, NomChamp, TypeChamp, Agregation
        ou None si la structure n'est pas reconnue
    """
    # Cas 1 : Mesure
    if 'Measure' in select_entry:
        measure = select_entry['Measure']
        source = measure.get('Expression', {}).get('SourceRef', {}).get('Source', '')
        nom_champ = measure.get('Property', '')
        nom_table = alias_table.get(source, source)
        
        return {
            'NomTable': nom_table,
            'NomChamp': nom_champ,
            'TypeChamp': 'Mesure',
            'Agregation': ''
        }
    
    # Cas 2 : Colonne simple
    if 'Column' in select_entry:
        column = select_entry['Column']
        source = column.get('Expression', {}).get('SourceRef', {}).get('Source', '')
        nom_champ = column.get('Property', '')
        nom_table = alias_table.get(source, source)
        
        return {
            'NomTable': nom_table,
            'NomChamp': nom_champ,
            'TypeChamp': 'Colonne',
            'Agregation': ''
        }
    
    # Cas 3 : Agrégation (colonne avec SUM, AVERAGE, etc.)
    if 'Aggregation' in select_entry:
        agg = select_entry['Aggregation']
        expression = agg.get('Expression', {})
        column = expression.get('Column', {})
        source = column.get('Expression', {}).get('SourceRef', {}).get('Source', '')
        nom_champ = column.get('Property', '')
        nom_table = alias_table.get(source, source)
        
        # Le type d'agrégation est un code numérique :
        # 0=Sum, 1=Avg, 2=Count, 3=Min, 4=Max, 5=CountNonNull, 6=Median, 7=StdDev, 8=Var
        codes_agregation = {
            0: 'Sum',
            1: 'Average',
            2: 'Count',
            3: 'Min',
            4: 'Max',
            5: 'CountNonNull',
            6: 'Median',
            7: 'StdDev',
            8: 'Variance'
        }
        code = agg.get('Function', 0)
        nom_agregation = codes_agregation.get(code, f'Inconnu({code})')
        
        return {
            'NomTable': nom_table,
            'NomChamp': nom_champ,
            'TypeChamp': 'Colonne',
            'Agregation': nom_agregation
        }
    
    return None


def parser_champs_visuel(dossier_visuel, nom_rapport, nom_page, type_visuel):
    """
    Extrait tous les champs utilisés par un visuel.
    
    Returns:
        liste de dictionnaires, un par champ utilisé
    """
    fichier_config = dossier_visuel / "config.json"
    
    if not fichier_config.exists():
        return []
    
    try:
        with open(fichier_config, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return []
    
    # Récupération du prototypeQuery
    prototype_query = data.get('singleVisual', {}).get('prototypeQuery', {})
    if not prototype_query:
        return []
    
    # Construction du dictionnaire d'alias
    from_section = prototype_query.get('From', [])
    alias_table = construire_dictionnaire_alias(from_section)
    
    # Extraction des champs depuis Select
    select_section = prototype_query.get('Select', [])
    champs = []
    
    for select_entry in select_section:
        champ = extraire_champ(select_entry, alias_table)
        if champ is not None:
            champ['NomRapport'] = nom_rapport
            champ['NomPage'] = nom_page
            champ['TypeVisuel'] = type_visuel
            champs.append(champ)
    
    return champs


def parser_champs_rapport(dossier_rapport_extrait, nom_rapport):
    """
    Parse tous les champs utilisés dans tous les visuels d'un rapport.
    
    Returns:
        liste de dictionnaires, un par usage de champ
    """
    dossier_sections = dossier_rapport_extrait / "Report" / "sections"
    
    if not dossier_sections.exists():
        return []
    
    tous_les_champs = []
    
    dossiers_pages = sorted([
        d for d in dossier_sections.iterdir() 
        if d.is_dir()
    ])
    
    for dossier_page in dossiers_pages:
        # Récupération du nom de la page
        fichier_section = dossier_page / "section.json"
        nom_page = ""
        if fichier_section.exists():
            try:
                with open(fichier_section, 'r', encoding='utf-8') as f:
                    section_data = json.load(f)
                nom_page = section_data.get('displayName', '').strip()
            except json.JSONDecodeError:
                pass
        
        # Parcours des visuels
        dossier_visuels = dossier_page / "visualContainers"
        if not dossier_visuels.exists():
            continue
        
        for dossier_visuel in sorted(dossier_visuels.iterdir()):
            if not dossier_visuel.is_dir():
                continue
            
            # Récupération du type de visuel
            fichier_config = dossier_visuel / "config.json"
            type_visuel = "inconnu"
            if fichier_config.exists():
                try:
                    with open(fichier_config, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    type_visuel = config_data.get('singleVisual', {}).get('visualType', 'inconnu')
                except json.JSONDecodeError:
                    pass
            
            # Extraction des champs du visuel
            champs = parser_champs_visuel(dossier_visuel, nom_rapport, nom_page, type_visuel)
            tous_les_champs.extend(champs)
    
    return tous_les_champs