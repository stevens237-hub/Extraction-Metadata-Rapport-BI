"""
Calcule les champs et tables non utilisés dans un rapport,
par soustraction entre le modèle complet et les usages effectifs.
"""


def calculer_champs_non_utilises(champs_modele, champs_utilises):
    """
    Identifie les champs définis dans le modèle mais non utilisés dans les visuels.
    
    Args:
        champs_modele: liste de dicts produits par model_parser
                       (avec NomRapport, NomTable, NomChamp, TypeChamp, EstMasque)
        champs_utilises: liste de dicts produits par fields_parser
                         (avec NomRapport, NomTable, NomChamp, ...)
    
    Returns:
        liste de dicts pour UnusedFields.csv
    """
    # Construction d'un set des champs utilisés pour recherche rapide
    # Clé : (NomRapport, NomTable, NomChamp)
    champs_utilises_set = set()
    for champ in champs_utilises:
        cle = (champ['NomRapport'], champ['NomTable'], champ['NomChamp'])
        champs_utilises_set.add(cle)
    
    # Filtrage des champs du modèle pour ne garder que les non utilisés
    champs_non_utilises = []
    for champ in champs_modele:
        cle = (champ['NomRapport'], champ['NomTable'], champ['NomChamp'])
        
        if cle not in champs_utilises_set:
            champs_non_utilises.append({
                'NomRapport': champ['NomRapport'],
                'NomTable': champ['NomTable'],
                'NomChamp': champ['NomChamp'],
                'TypeChamp': champ['TypeChamp'],
                'EstMasque': champ['EstMasque']
            })
    
    # Tri par rapport, puis table, puis champ
    champs_non_utilises.sort(key=lambda c: (c['NomRapport'], c['NomTable'], c['NomChamp']))
    
    return champs_non_utilises


