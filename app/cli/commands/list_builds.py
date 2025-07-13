"""
Commande de liste des builds.

Cette commande permet de lister les builds disponibles avec des options de filtrage.
"""
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException
from rich.console import Console
from rich.table import Table

from app.cli.commands import BaseCommand, register_command
from app.cli.utils import format_as_table, print_error

@register_command("list-builds")
class ListBuildsCommand(BaseCommand):
    """Commande pour lister les builds."""
    
    def __init__(self):
        """Initialise la commande avec un client HTTP."""
        self.console = Console()
    
    @classmethod
    def register_parser(cls, subparsers):
        """Enregistre les arguments de la commande."""
        parser = subparsers.add_parser(
            "list-builds",
            help="Lister les builds disponibles"
        )
        
        # Options de filtrage
        filter_group = parser.add_argument_group("Filtres")
        filter_group.add_argument(
            "--role",
            help="Filtrer par rôle (ex: dps, heal, tank)"
        )
        filter_group.add_argument(
            "--profession",
            help="Filtrer par profession (ex: guardian, elementalist)"
        )
        filter_group.add_argument(
            "--search",
            help="Rechercher dans les noms et descriptions"
        )
        
        # Options de sortie
        output_group = parser.add_argument_group("Options de sortie")
        output_group.add_argument(
            "--format",
            choices=["table", "json", "yaml"],
            default="table",
            help="Format de sortie (défaut: table)"
        )
        output_group.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Nombre maximum de résultats à afficher (défaut: 20)"
        )
        output_group.add_argument(
            "--offset",
            type=int,
            default=0,
            help="Décalage des résultats (pour la pagination)"
        )
        
        # Options d'API
        parser.add_argument(
            "--api-url",
            default=os.getenv("API_BASE_URL", "http://localhost:8000/api"),
            help="URL de base de l'API (défaut: http://localhost:8000/api)"
        )
        
        parser.set_defaults(handler=cls())
    
    def execute(self, args) -> int:
        """Exécute la commande de liste."""
        try:
            # Récupérer les builds depuis l'API
            builds = self._fetch_builds(args)
            
            # Formater la sortie
            if args.format == "table":
                self._display_as_table(builds, args.limit)
            else:
                self._display_as_structured(builds, args.format)
            
            return 0
            
        except HTTPException as e:
            return self.handle_http_error(e)
        except Exception as e:
            print_error(f"Erreur lors de la récupération des builds: {str(e)}")
            return 1
    
    def _fetch_builds(self, args) -> List[Dict[str, Any]]:
        """Récupère les builds depuis l'API avec les filtres appliqués."""
        params = {
            "limit": args.limit,
            "offset": args.offset,
        }
        
        # Ajouter les filtres s'ils sont spécifiés
        if args.role:
            params["role"] = args.role
        if args.profession:
            params["profession"] = args.profession
        if args.search:
            params["search"] = args.search
        
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{args.api_url}/builds",
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json().get("items", [])
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Erreur lors de la récupération des builds: {str(e)}"
            ) from e
    
    def _display_as_table(self, builds: List[Dict[str, Any]], limit: int) -> None:
        """Affiche les builds sous forme de tableau."""
        if not builds:
            self.console.print("[yellow]Aucun build trouvé.[/yellow]")
            return
        
        # Préparer les données pour l'affichage
        table_data = []
        for build in builds[:limit]:
            table_data.append({
                "ID": str(build.get("id", "N/A")),
                "Nom": build.get("name", "Sans nom"),
                "Profession": build.get("profession", "Inconnue").capitalize(),
                "Rôle": ", ".join(build.get("roles", [])),
                "Créé le": build.get("created_at", "Inconnu")[:10],
            })
        
        # Afficher le tableau
        format_as_table(
            table_data,
            columns=["ID", "Nom", "Profession", "Rôle", "Créé le"],
            title=f"Builds disponibles (affichés: {len(table_data)})"
        )
        
        # Afficher un avertissement si certains résultats ne sont pas affichés
        if len(builds) > limit:
            self.console.print(
                f"[yellow]Avertissement: Seuls les {limit} premiers résultats sont affichés. "
                "Utilisez --limit pour en afficher plus.[/yellow]"
            )
    
    def _display_as_structured(self, builds: List[Dict[str, Any]], format: str) -> None:
        """Affiche les builds dans un format structuré (JSON/YAML)."""
        if format == "json":
            import json
            print(json.dumps(builds, indent=2, ensure_ascii=False))
        else:  # yaml
            import yaml
            print(yaml.dump(builds, default_flow_style=False, allow_unicode=True))
