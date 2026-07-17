"""
Agrégation des tables utilisées à partir des champs utilisés.
Consolide UsedFields en UsedTables : une ligne par couple (rapport, table)
avec le nombre de champs distincts et de visuels distincts.
"""


def agreger_tables_utilisees(liste_champs_utilises):
    """
    Agrège la liste des champs utilisés en une liste de tables utilisées,
    avec compteurs.
    
    Args:
        liste_champs_utilises: liste de dicts produits par fields_parser
                              (chaque dict contient NomRapport, NomPage, TypeVisuel,
                               NomTable, NomChamp, TypeChamp, Agregation)
    
    Returns:
        liste de dicts avec NomRapport, NomTable, NbChampsUtilises, NbVisuelsUtilisant
    """
    # On construit une structure intermédiaire pour compter les éléments distincts
    # Clé : (rapport, table) → valeur : {'champs': set, 'visuels': set}
    agregation = {}
    
    for champ in liste_champs_utilises:
        cle = (champ['NomRapport'], champ['NomTable'])
        
        if cle not in agregation:
            agregation[cle] = {
                'champs': set(),
                'visuels': set()
            }
        
        # Ajout du champ (le set garantit l'unicité)
        agregation[cle]['champs'].add(champ['NomChamp'])
        
        # Pour identifier un visuel de manière unique, on combine page + type + ordre dans la page
        # (on n'a pas d'identifiant explicite, mais cette combinaison est suffisamment unique)
        identifiant_visuel = f"{champ['NomPage']}|{champ['TypeVisuel']}"
        agregation[cle]['visuels'].add(identifiant_visuel)
    
    # Conversion en liste de dicts pour le CSV final
    resultats = []
    for (nom_rapport, nom_table), donnees in agregation.items():
        resultats.append({
            'NomRapport': nom_rapport,
            'NomTable': nom_table,
            'NbChampsUtilises': len(donnees['champs']),
            'NbVisuelsUtilisant': len(donnees['visuels'])
        })
    
    # Tri par rapport puis par nombre d'usages décroissant
    resultats.sort(key=lambda r: (r['NomRapport'], -r['NbVisuelsUtilisant']))
    
    return resultats