"""
Point d'entrée principal pour l'interface en ligne de commande (CLI) de GW2 Team Builder.

Ce module gère le parsing des arguments de ligne de commande et le routage
vers les différentes commandes disponibles.
"""
import argparse
import importlib
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Type

from dotenv import load_dotenv
from rich.console import Console

from app.cli.commands import BaseCommand, COMMANDS
from app.cli.utils import print_error, print_success

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dossier contenant les commandes
COMMANDS_DIR = Path(__file__).parent / "commands"

class CLIManager:
    """Gestionnaire principal de l'interface en ligne de commande."""
    
    def __init__(self):
        """Initialise le gestionnaire CLI."""
        self.console = Console()
        self.parser = self._create_parser()
        self.commands: Dict[str, Type[BaseCommand]] = {}
        
    def _create_parser(self) -> argparse.ArgumentParser:
        """Crée le parseur d'arguments principal."""
        parser = argparse.ArgumentParser(
            description="GW2 Team Builder - Outil d'import/export de builds",
            epilog="Utilisez 'commande --help' pour plus d'informations sur une commande spécifique."
        )
        
        # Arguments globaux
        parser.add_argument(
            '--version',
            action='version',
            version=f"%(prog)s {self._get_version()}"
        )
        
        # Sous-commandes
        subparsers = parser.add_subparsers(
            dest='command',
            help='Commande à exécuter',
            required=True
        )
        
        return parser
    
    def _get_version(self) -> str:
        """Retourne la version actuelle de l'application."""
        try:
            from app import __version__
            return __version__
        except ImportError:
            return "0.1.0"
    
    def load_commands(self) -> None:
        """Charge dynamiquement toutes les commandes disponibles."""
        # Importer les commandes enregistrées
        for cmd_name in COMMANDS:
            try:
                # Le module doit être importé pour que le décorateur @register_command s'exécute
                module_name = f"app.cli.commands.{cmd_name}"
                importlib.import_module(module_name)
            except ImportError as e:
                logger.warning("Impossible de charger la commande %s: %s", cmd_name, e)
        
        # Enregistrer les commandes
        self.commands = COMMANDS.copy()
        
        # Configurer les sous-commandes
        for cmd_name, cmd_class in self.commands.items():
            try:
                cmd_class.register_parser(self.parser.add_subparsers())
            except Exception as e:
                logger.error("Erreur lors de l'enregistrement de la commande %s: %s", 
                           cmd_name, e, exc_info=True)
    
    def run(self, args=None) -> int:
        """Exécute la commande demandée.
        
        Args:
            args: Arguments de ligne de commande (par défaut: sys.argv[1:])
            
        Returns:
            int: Code de sortie (0 pour succès, >0 pour erreur)
        """
        try:
            # Charger les commandes
            self.load_commands()
            
            # Parser les arguments
            parsed_args = self.parser.parse_args(args)
            
            # Trouver et exécuter la commande
            command_name = parsed_args.command
            if command_name not in self.commands:
                print_error(f"Commande inconnue: {command_name}")
                self.parser.print_help()
                return 1
            
            # Exécuter la commande
            command = self.commands[command_name]()
            return command.execute(parsed_args)
            
        except KeyboardInterrupt:
            print_error("\nOpération annulée par l'utilisateur")
            return 1
        except Exception as e:
            logger.exception("Une erreur inattendue s'est produite")
            print_error(f"Erreur: {str(e)}")
            return 1

def main() -> int:
    """Point d'entrée principal du script."""
    try:
        # Créer et exécuter le gestionnaire CLI
        cli = CLIManager()
        return cli.run()
    except Exception as e:
        logger.exception("Erreur critique")
        print_error(f"Erreur critique: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
