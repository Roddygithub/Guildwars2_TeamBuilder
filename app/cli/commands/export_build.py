"""
Commande d'export de builds.

Cette commande permet d'exporter un build vers un fichier JSON ou YAML.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.cli.commands import BaseCommand, register_command
from app.cli.utils import print_error, print_success, print_warning

@register_command("export-build")
class ExportBuildCommand(BaseCommand):
    """Commande pour exporter un build vers un fichier."""
    
    @classmethod
    def register_parser(cls, subparsers):
        """Enregistre les arguments de la commande."""
        parser = subparsers.add_parser(
            "export-build",
            help="Exporter un build vers un fichier"
        )
        
        # Arguments requis
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "build_id",
            nargs="?",
            help="ID du build à exporter"
        )
        group.add_argument(
            "--file",
            help="Chemin vers un fichier de build à exporter"
        )
        
        # Options
        parser.add_argument(
            "--output", "-o",
            help="Fichier de sortie (par défaut: nom du build avec l'extension appropriée)"
        )
        parser.add_argument(
            "--format",
            choices=["json", "yaml"],
            default="json",
            help="Format de sortie (défaut: json)"
        )
        parser.add_argument(
            "--api-url",
            default=os.getenv("API_BASE_URL", "http://localhost:8000/api"),
            help="URL de base de l'API (défaut: http://localhost:8000/api)"
        )
        parser.set_defaults(handler=cls())
    
    def execute(self, args) -> int:
        """Exécute la commande d'export."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task("Export du build...", total=None)
                
                try:
                    # Récupérer les données du build
                    if args.file:
                        build_data = self._get_build_from_file(args.file)
                    else:
                        build_data = self._get_build_from_api(args.build_id, args.api_url)
                    
                    # Déterminer le fichier de sortie
                    output_file = self._get_output_file(args, build_data)
                    
                    # Exporter vers le fichier
                    self.save_build(build_data, str(output_file), args.format)
                    
                    progress.update(task, completed=1, description="Terminé!")
                    print_success(f"Build exporté avec succès vers {output_file}")
                    return 0
                    
                except Exception as e:
                    progress.stop()
                    raise e
        
        except HTTPException as e:
            return self.handle_http_error(e)
        except Exception as e:
            print_error(f"Erreur lors de l'export du build: {str(e)}")
            return 1
    
    def _get_build_from_file(self, file_path: str) -> Dict[str, Any]:
        """Charge un build depuis un fichier local."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")
        return self.load_build(file_path)
    
    def _get_build_from_api(self, build_id: str, api_url: str) -> Dict[str, Any]:
        """Récupère un build depuis l'API."""
        try:
            with httpx.Client() as client:
                response = client.get(f"{api_url}/builds/{build_id}", timeout=10.0)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise FileNotFoundError(f"Aucun build trouvé avec l'ID {build_id}") from e
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Erreur lors de la récupération du build: {str(e)}"
            ) from e
    
    def _get_output_file(self, args, build_data: Dict[str, Any]) -> Path:
        """Détermine le fichier de sortie."""
        if args.output:
            output_file = Path(args.output)
        else:
            # Générer un nom de fichier basé sur le nom du build
            safe_name = "".join(c if c.isalnum() else "_" for c in build_data.get("name", "build")).strip("_")
            ext = args.format if args.format != "yaml" else "yml"
            output_file = Path(f"{safe_name}.{ext}")
        
        # Créer les répertoires parents si nécessaire
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Vérifier si le fichier existe déjà
        if output_file.exists():
            print_warning(f"Le fichier {output_file} existe déjà et sera écrasé")
        
        return output_file
