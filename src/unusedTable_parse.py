def calculer_tables_non_utilisees(champs_modele, champs_utilises):
    """
    Identifie les tables définies dans le modèle mais dont aucun champ
    n'est utilisé dans les visuels.
    
    Args:
        champs_modele: liste de dicts produits par model_parser
        champs_utilises: liste de dicts produits par fields_parser
    
    Returns:
        liste de dicts pour UnusedTables.csv
    """
    # Construction du set des tables utilisées
    # Clé : (NomRapport, NomTable)
    tables_utilisees_set = set()
    for champ in champs_utilises:
        cle = (champ['NomRapport'], champ['NomTable'])
        tables_utilisees_set.add(cle)
    
    # Construction de la liste des tables du modèle avec leurs propriétés
    # Pour chaque table : nombre de colonnes/mesures, statut masqué
    tables_modele = {}  # {(rapport, table): {'nb_colonnes': X, 'nb_mesures': Y, 'est_masquee': bool}}
    
    for champ in champs_modele:
        cle = (champ['NomRapport'], champ['NomTable'])
        
        if cle not in tables_modele:
            tables_modele[cle] = {
                'nb_colonnes': 0,
                'nb_mesures': 0,
                'champs_masques': 0,
                'total_champs': 0
            }
        
        tables_modele[cle]['total_champs'] += 1
        
        if champ['TypeChamp'] == 'Colonne':
            tables_modele[cle]['nb_colonnes'] += 1
        elif champ['TypeChamp'] == 'Mesure':
            tables_modele[cle]['nb_mesures'] += 1
        
        if champ['EstMasque'] == 'Oui':
            tables_modele[cle]['champs_masques'] += 1
    
    # Filtrage : on ne garde que les tables non utilisées
    tables_non_utilisees = []
    for (nom_rapport, nom_table), stats in tables_modele.items():
        if (nom_rapport, nom_table) not in tables_utilisees_set:
            # Une table est considérée comme "globalement masquée" si tous ses champs le sont
            est_masquee_globalement = (
                stats['champs_masques'] == stats['total_champs'] 
                and stats['total_champs'] > 0
            )
            
            tables_non_utilisees.append({
                'NomRapport': nom_rapport,
                'NomTable': nom_table,
                'NbColonnes': stats['nb_colonnes'],
                'NbMesures': stats['nb_mesures'],
                'EstMasqueeGlobalement': 'Oui' if est_masquee_globalement else 'Non'
            })
    
    # Tri par rapport puis par nom de table
    tables_non_utilisees.sort(key=lambda t: (t['NomRapport'], t['NomTable']))
    
    return tables_non_utilisees