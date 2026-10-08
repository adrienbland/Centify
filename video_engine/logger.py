import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_file='logs/engine.log', level=logging.INFO):
    """
    Configuration d'un logger robuste avec rotation de fichiers.
    Permet de ne rien rater si le script plante.
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Handler pour écrire dans le fichier avec rotation (max 5 MB par fichier, garde 3 backups)
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # Handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Évite d'ajouter plusieurs handlers si le logger est appelé plusieurs fois
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger
