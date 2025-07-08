"""Configuration avancée du système de logging pour l'application.

Ce module offre une configuration complète du logging avec les fonctionnalités suivantes :
- Gestion de plusieurs gestionnaires (handlers) : console, fichier, rotation
- Filtrage des logs par niveau et par module
- Formatage personnalisé avec couleurs pour la console
- Rotation des fichiers de log avec conservation
- Configuration via variables d'environnement
"""
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

# Niveaux de log
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}
DEFAULT_LOG_LEVEL = logging.INFO

# Configuration par défaut
DEFAULT_CONFIG = {
    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO').upper(),
    'LOG_TO_CONSOLE': os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true',
    'LOG_TO_FILE': os.getenv('LOG_TO_FILE', 'true').lower() == 'true',
    'LOG_DIR': os.getenv('LOG_DIR', 'logs'),
    'LOG_FILE': 'app.log',
    'MAX_LOG_SIZE': 10 * 1024 * 1024,  # 10 MB
    'BACKUP_COUNT': 5,
    'ENABLE_COLORS': os.getenv('LOG_COLORS', 'true').lower() == 'true',
    'LOG_FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'LOG_DATE_FORMAT': '%Y-%m-%d %H:%M:%S',
    'LOG_LEVEL_OVERRIDES': {
        # Exemple: 'app.database': 'DEBUG'
    }
}

# Couleurs pour la console (si activé)
if DEFAULT_CONFIG['ENABLE_COLORS'] and sys.stderr.isatty():
    import colorama
    from colorama import Fore, Style
    
    colorama.init()
    
    class ColoredFormatter(logging.Formatter):
        """Formateur de logs avec couleurs pour la console."""
        COLORS = {
            'DEBUG': Fore.CYAN,
            'INFO': Fore.GREEN,
            'WARNING': Fore.YELLOW,
            'ERROR': Fore.RED,
            'CRITICAL': Fore.RED + Style.BRIGHT
        }
        
        def format(self, record):
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
                record.name = f"{Fore.BLUE}{record.name}{Style.RESET_ALL}"
            return super().format(record)
else:
    class ColoredFormatter(logging.Formatter):
        """Formateur de logs sans couleurs."""
        pass


def get_log_level(level_name: str) -> int:
    """Convertit un nom de niveau de log en valeur de niveau.
    
    Args:
        level_name: Nom du niveau de log (ex: 'DEBUG', 'INFO')
        
    Returns:
        La valeur du niveau de log correspondante
        
    Raises:
        ValueError: Si le nom du niveau est invalide
    """
    level = LOG_LEVELS.get(level_name.upper())
    if level is None:
        raise ValueError(f"Niveau de log invalide: {level_name}")
    return level


def setup_logging(
    level: Union[str, int] = DEFAULT_CONFIG['LOG_LEVEL'],
    log_dir: Optional[str] = None,
    log_file: Optional[str] = None,
    log_to_console: Optional[bool] = None,
    log_to_file: Optional[bool] = None,
    max_log_size: Optional[int] = None,
    backup_count: Optional[int] = None,
    enable_colors: Optional[bool] = None,
    log_format: Optional[str] = None,
    log_date_format: Optional[str] = None,
    log_level_overrides: Optional[Dict[str, Union[str, int]]] = None
) -> None:
    """Configure le système de logging global de l'application.
    
    Args:
        level: Niveau de log global (par défaut: INFO)
        log_dir: Répertoire pour les fichiers de log (par défaut: 'logs')
        log_file: Nom du fichier de log (par défaut: 'app.log')
        log_to_console: Active la sortie console (par défaut: True)
        log_to_file: Active l'écriture dans un fichier (par défaut: True)
        max_log_size: Taille maximale d'un fichier de log en octets (par défaut: 10 Mo)
        backup_count: Nombre de fichiers de sauvegarde à conserver (par défaut: 5)
        enable_colors: Active les couleurs dans la console (par défaut: True)
        log_format: Format des messages de log
        log_date_format: Format des dates dans les logs
        log_level_overrides: Surcharges de niveau par module (ex: {'app.database': 'DEBUG'})
    """
    # Application des valeurs par défaut
    config = DEFAULT_CONFIG.copy()
    
    # Remplacement des valeurs par celles fournies
    if isinstance(level, str):
        level = get_log_level(level)
    
    log_dir = log_dir or config['LOG_DIR']
    log_file = log_file or config['LOG_FILE']
    log_to_console = log_to_console if log_to_console is not None else config['LOG_TO_CONSOLE']
    log_to_file = log_to_file if log_to_file is not None else config['LOG_TO_FILE']
    max_log_size = max_log_size or config['MAX_LOG_SIZE']
    backup_count = backup_count or config['BACKUP_COUNT']
    enable_colors = enable_colors if enable_colors is not None else config['ENABLE_COLORS']
    log_format = log_format or config['LOG_FORMAT']
    log_date_format = log_date_format or config['LOG_DATE_FORMAT']
    log_level_overrides = log_level_overrides or config['LOG_LEVEL_OVERRIDES']
    
    # Création du répertoire de logs si nécessaire
    if log_to_file:
        os.makedirs(log_dir, exist_ok=True)
    
    # Configuration du logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Suppression des gestionnaires existants
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Création des gestionnaires
    handlers = []
    
    # Gestionnaire console
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        if enable_colors and sys.stderr.isatty():
            formatter = ColoredFormatter(log_format, log_date_format)
        else:
            formatter = logging.Formatter(log_format, log_date_format)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)
    
    # Gestionnaire fichier avec rotation
    if log_to_file:
        log_path = Path(log_dir) / log_file
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path,
            maxBytes=max_log_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(log_format, log_date_format)
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)
    
    # Ajout des gestionnaires au logger racine
    for handler in handlers:
        root_logger.addHandler(handler)
    
    # Application des surcharges de niveau par module
    for module, module_level in log_level_overrides.items():
        if isinstance(module_level, str):
            module_level = get_log_level(module_level)
        logging.getLogger(module).setLevel(module_level)


def get_logger(name: Optional[str] = None, level: Optional[Union[str, int]] = None) -> logging.Logger:
    """Retourne un logger configuré avec le nom spécifié.
    
    Si aucun nom n'est fourni, le nom du module appelant est utilisé.
    
    Args:
        name: Nom du logger (optionnel)
        level: Niveau de log spécifique pour ce logger (optionnel)
        
    Returns:
        Un logger configuré avec les gestionnaires appropriés
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Message d'information")
        >>> 
        >>> # Avec un niveau personnalisé
        >>> debug_logger = get_logger('app.debug', 'DEBUG')
    """
    if name is None:
        # Utilise le nom du module appelant
        import inspect
        frm = inspect.stack()[1]
        mod = inspect.getmodule(frm[0])
        name = mod.__name__ if mod else '__main__'
    
    logger = logging.getLogger(name)
    
    # Applique un niveau spécifique si fourni
    if level is not None:
        if isinstance(level, str):
            level = get_log_level(level)
        logger.setLevel(level)
    
    return logger


# Configuration initiale au chargement du module
setup_logging()

# Exemple d'utilisation :
# from app.logging_config import get_logger
# 
# # Création d'un logger avec le nom du module actuel
# logger = get_logger(__name__)
# 
# # Utilisation du logger
# logger.debug("Message de débogage")
# logger.info("Message d'information")
# logger.warning("Avertissement")
# logger.error("Erreur", exc_info=True)  # Inclut la stack trace pour les erreurs
# logger.critical("Erreur critique")
# 
# # Création d'un logger avec un niveau personnalisé
# debug_logger = get_logger('app.debug', 'DEBUG')
# debug_logger.debug("Ce message ne s'affichera que si le niveau est DEBUG")
# 
# # Configuration avancée (à faire au démarrage de l'application)
# if __name__ == "__main__":
#     setup_logging(
#         level='DEBUG',
#         log_dir='logs',
#         log_file='app.log',
#         log_to_console=True,
#         log_to_file=True,
#         max_log_size=10 * 1024 * 1024,  # 10 MB
#         backup_count=5,
#         enable_colors=True,
#         log_level_overrides={
#             'app.database': 'DEBUG',
#             'app.api': 'INFO',
#             'uvicorn': 'WARNING',
#             'uvicorn.error': 'WARNING',
#             'uvicorn.access': 'WARNING',
#             'fastapi': 'WARNING',
#             'sqlalchemy.engine': 'WARNING'
#         }
#     )
