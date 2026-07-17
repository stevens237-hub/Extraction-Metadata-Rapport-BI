"""
Parser des rapports paginés Power BI (fichiers .rdl).
Extrait les métadonnées structurelles : sources, requêtes, champs, 
paramètres et éléments visuels.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

from logging_config import obtenir_logger

logger = obtenir_logger()


def local_name(tag):
    """
    Retourne le nom local d'un tag XML en ignorant le namespace.
    Exemple : '{http://schemas.microsoft.com/...}DataSource' → 'DataSource'
    """
    return tag.split('}')[-1] if '}' in tag else tag


def find_all_by_name(elem, tag_name):
    """
    Trouve tous les descendants ayant un nom de tag donné (namespace-agnostic).
    """
    return [e for e in elem.iter() if local_name(e.tag) == tag_name]


def get_child_text(elem, tag_name):
    """
    Récupère le texte du premier enfant direct portant un nom de tag donné.
    Retourne une chaîne vide si non trouvé.
    """
    for child in elem:
        if local_name(child.tag) == tag_name:
            return (child.text or '').strip()
    return ''


def get_descendant_text(elem, tag_name):
    """
    Récupère le texte du premier descendant (à tout niveau) portant un nom de tag donné.
    """
    for descendant in elem.iter():
        if local_name(descendant.tag) == tag_name:
            return (descendant.text or '').strip()
    return ''


def parser_datasources(root, nom_rapport):
    """Extrait les sources de données d'un rapport RDL."""
    sources = []
    for ds in find_all_by_name(root, 'DataSource'):
        nom_source = ds.get('Name', '')
        
        # Les propriétés de connexion sont dans ConnectionProperties
        provider = get_descendant_text(ds, 'DataProvider')
        connect_string = get_descendant_text(ds, 'ConnectString')
        integrated_security = get_descendant_text(ds, 'IntegratedSecurity')
        
        # Mode d'authentification
        if integrated_security.lower() == 'true':
            auth_mode = 'Windows Integrated'
        elif connect_string:
            auth_mode = 'Credentials'
        else:
            auth_mode = 'Non défini'
        
        sources.append({
            'NomRapport': nom_rapport,
            'NomSource': nom_source,
            'Provider': provider,
            'ConnectString': connect_string[:200] if connect_string else '',
            'AuthMode': auth_mode
        })
    
    return sources


def parser_datasets(root, nom_rapport):
    """Extrait les DataSets (requêtes) d'un rapport RDL."""
    datasets = []
    for dset in find_all_by_name(root, 'DataSet'):
        nom_dataset = dset.get('Name', '')
        
        # Trouve les infos de la Query
        nom_source = ''
        type_commande = 'Text'  # valeur par défaut RDL
        commande = ''
        
        for query in find_all_by_name(dset, 'Query'):
            nom_source = get_descendant_text(query, 'DataSourceName')
            type_commande = get_descendant_text(query, 'CommandType') or 'Text'
            commande = get_descendant_text(query, 'CommandText')
            break  # un seul Query par DataSet
        
        # Compte les champs
        nb_champs = len(find_all_by_name(dset, 'Field'))
        
        # Extrait un aperçu de la requête (premiers caractères)
        extrait = commande.replace('\n', ' ').replace('\r', '').strip()
        if len(extrait) > 200:
            extrait = extrait[:200] + '...'
        
        datasets.append({
            'NomRapport': nom_rapport,
            'NomDataSet': nom_dataset,
            'NomSource': nom_source,
            'TypeCommande': type_commande,
            'NbChamps': nb_champs,
            'ExtraitRequete': extrait
        })
    
    return datasets


def parser_fields(root, nom_rapport):
    """Extrait les champs de tous les DataSets d'un rapport RDL."""
    fields = []
    for dset in find_all_by_name(root, 'DataSet'):
        nom_dataset = dset.get('Name', '')
        
        for field in find_all_by_name(dset, 'Field'):
            nom_champ = field.get('Name', '')
            
            # DataField : nom du champ dans la source
            source_field = get_descendant_text(field, 'DataField')
            
            # Value : formule si champ calculé
            formule = get_descendant_text(field, 'Value')
            
            fields.append({
                'NomRapport': nom_rapport,
                'NomDataSet': nom_dataset,
                'NomChamp': nom_champ,
                'SourceField': source_field,
                'Formule': formule if formule.startswith('=') else ''
            })
    
    return fields


def parser_visuels(root, nom_rapport):
    """Extrait tous les éléments visuels d'un rapport RDL."""
    visuels = []
    
    # Types de visuels à extraire avec leur libellé
    types_visuels = {
        'Tablix': 'Tablix',
        'Chart': 'Chart',
        'Textbox': 'Textbox',
        'Image': 'Image',
        'Subreport': 'Subreport'
    }
    
    for tag_recherche, type_visuel in types_visuels.items():
        for elem in find_all_by_name(root, tag_recherche):
            nom_visuel = elem.get('Name', '')
            
            # DataSet associé (peut ne pas exister pour Textbox, Image)
            nom_dataset = ''
            for child in elem.iter():
                if local_name(child.tag) == 'DataSetName':
                    nom_dataset = child.text or ''
                    break
            
            # Sous-type pour les charts
            sous_type = ''
            if type_visuel == 'Chart':
                type_chart = get_descendant_text(elem, 'Type')
                subtype_chart = get_descendant_text(elem, 'Subtype')
                if type_chart and subtype_chart:
                    sous_type = f"{type_chart} - {subtype_chart}"
                elif type_chart:
                    sous_type = type_chart
            elif type_visuel == 'Subreport':
                # Pour un Subreport, capture le nom du rapport référencé
                ref = get_descendant_text(elem, 'ReportName')
                if ref:
                    sous_type = f"Ref: {ref}"
            
            visuels.append({
                'NomRapport': nom_rapport,
                'NomVisuel': nom_visuel,
                'TypeVisuel': type_visuel,
                'SousType': sous_type,
                'NomDataSet': nom_dataset
            })
    
    return visuels


def parser_synthese_rapport(root, nom_rapport, sources, datasets, fields, visuels):
    """Génère la ligne de synthèse pour PaginatedReports.csv."""
    parametres = find_all_by_name(root, 'ReportParameter')
    
    # Comptages par type de visuel
    nb_tablix = sum(1 for v in visuels if v['TypeVisuel'] == 'Tablix')
    nb_charts = sum(1 for v in visuels if v['TypeVisuel'] == 'Chart')
    nb_textbox = sum(1 for v in visuels if v['TypeVisuel'] == 'Textbox')
    nb_subreports = sum(1 for v in visuels if v['TypeVisuel'] == 'Subreport')
    
    return {
        'NomRapport': nom_rapport,
        'NbDataSources': len(sources),
        'NbDataSets': len(datasets),
        'NbChampsTotal': len(fields),
        'NbParametres': len(parametres),
        'NbTablix': nb_tablix,
        'NbCharts': nb_charts,
        'NbTextbox': nb_textbox,
        'NbSubreports': nb_subreports
    }


def parser_rapport_rdl(chemin_rdl, nom_rapport):
    """
    Point d'entrée principal : parse un rapport RDL complet.
    
    Args:
        chemin_rdl: Path vers le fichier .rdl
        nom_rapport: nom du rapport (sans extension)
    
    Returns:
        dict avec 5 clés : 'synthese', 'sources', 'datasets', 'fields', 'visuels'
        chacune contenant une liste de dicts
    """
    try:
        tree = ET.parse(chemin_rdl)
        root = tree.getroot()
    except ET.ParseError as e:
        logger.error(f"  [ERREUR] Fichier RDL invalide : {e}")
        return None
    except IOError as e:
        logger.error(f"  [ERREUR] Impossible de lire {chemin_rdl.name} : {e}")
        return None
    
    # Extraction de toutes les catégories
    sources = parser_datasources(root, nom_rapport)
    datasets = parser_datasets(root, nom_rapport)
    fields = parser_fields(root, nom_rapport)
    visuels = parser_visuels(root, nom_rapport)
    synthese = parser_synthese_rapport(root, nom_rapport, sources, datasets, fields, visuels)
    
    return {
        'synthese': synthese,
        'sources': sources,
        'datasets': datasets,
        'fields': fields,
        'visuels': visuels
    }