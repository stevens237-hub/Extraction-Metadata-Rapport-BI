"""
Configuration centralisée du logging de l'application.
Tous les modules récupèrent le même logger via obtenir_logger().
"""

import logging
import sys

NOM_LOGGER = "extraction_metadata"


def configurer_logging(fichier_log=None, niveau=logging.INFO):
    """
    Configure le logger de l'application.

    Args:
        fichier_log: Path optionnel vers un fichier où dupliquer les logs
        niveau: niveau de log minimal (logging.INFO par défaut)

    Returns:
        le logger configuré
    """
    logger = logging.getLogger(NOM_LOGGER)
    logger.setLevel(niveau)
    logger.handlers.clear()

    formatteur = logging.Formatter('%(message)s')

    handler_console = logging.StreamHandler(sys.stdout)
    handler_console.setFormatter(formatteur)
    logger.addHandler(handler_console)

    if fichier_log is not None:
        handler_fichier = logging.FileHandler(fichier_log, encoding='utf-8-sig')
        handler_fichier.setFormatter(formatteur)
        logger.addHandler(handler_fichier)

    return logger


def obtenir_logger():
    """Retourne le logger de l'application (à appeler depuis chaque module)."""
    return logging.getLogger(NOM_LOGGER)
