"""
Commande d'import de builds.

Cette commande permet d'importer un build depuis un fichier JSON ou YAML.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.cli.commands import BaseCommand, register_command
from app.cli.utils import print_error, print_success, print_warning
from app.models.build import BuildData
from app.services.build_io import BuildIO

@register_command("import-build")
class ImportBuildCommand(BaseCommand):
    """Commande pour importer un build depuis un fichier."""
    
    @classmethod
    def register_parser(cls, subparsers):
        """Enregistre les arguments de la commande."""
        parser = subparsers.add_parser(
            "import-build",
            help="Importer un build depuis un fichier"
        )
        parser.add_argument(
            "file_path",
            help="Chemin vers le fichier du build (JSON ou YAML)"
        )
        parser.add_argument(
            "--output-format",
            choices=["text", "json", "yaml"],
            default="text",
            help="Format de sortie (défaut: text)"
        )
        parser.add_argument(
            "--save",
            action="store_true",
            help="Enregistrer le build dans la base de données"
        )
        parser.add_argument(
            "--api-url",
            default=os.getenv("API_BASE_URL", "http://localhost:8000/api"),
            help="URL de base de l'API (défaut: http://localhost:8000/api)"
        )
        parser.set_defaults(handler=cls())
    
    def execute(self, args) -> int:
        """Exécute la commande d'import."""
        try:
            # Vérifier si le fichier existe
            file_path = Path(args.file_path)
            if not file_path.exists():
                print_error(f"Le fichier {file_path} n'existe pas")
                return 2
            
            # Charger le build
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task("Chargement du build...", total=None)
                
                try:
                    # Essayer d'importer via l'API si c'est une URL
                    if str(file_path).startswith(('http://', 'https://')):
                        build_data = self._import_from_url(str(file_path), args.api_url)
                    else:
                        # Sinon, charger depuis le système de fichiers
                        build_data = self.load_build(str(file_path))
                    
                    # Valider le format du build
                    build = BuildData.model_validate(build_data)
                    
                    # Enregistrer le build si demandé
                    if args.save:
                        self._save_build(build, args.api_url)
                    
                    # Afficher le résultat
                    self._display_result(build, args.output_format)
                    
                    progress.update(task, completed=1, description="Terminé!")
                    return 0
                    
                except Exception as e:
                    progress.stop()
                    raise e
        
        except HTTPException as e:
            return self.handle_http_error(e)
        except Exception as e:
            print_error(f"Erreur lors de l'import du build: {str(e)}")
            return 1
    
    def _import_from_url(self, url: str, api_url: str) -> Dict[str, Any]:
        """Importe un build depuis une URL."""
        try:
            # Si c'est une URL de l'API, on l'utilise directement
            if url.startswith(api_url):
                response = httpx.get(url)
                response.raise_for_status()
                return response.json()
            
            # Sinon, on utilise l'endpoint d'import de l'API
            with httpx.Client() as client:
                files = {"file": (url.split("/")[-1], httpx.get(url).content)}
                response = client.post(
                    f"{api_url}/builds/import",
                    files=files,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise FileNotFoundError("Le build demandé n'existe pas") from e
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Erreur lors de l'import depuis l'URL: {str(e)}"
            ) from e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de l'import depuis l'URL: {str(e)}"
            ) from e
    
    def _save_build(self, build: BuildData, api_url: str) -> None:
        """Enregistre un build via l'API."""
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{api_url}/builds",
                    json=build.model_dump(),
                    timeout=10.0
                )
                response.raise_for_status()
                
                build_id = response.json().get("id")
                print_success(f"Build enregistré avec succès (ID: {build_id})")
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                print_warning("Un build similaire existe déjà")
            else:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Erreur lors de l'enregistrement du build: {str(e)}"
                ) from e
    
    def _display_result(self, build: BuildData, output_format: str) -> None:
        """Affiche le résultat de l'import."""
        if output_format == "text":
            print_success(f"Build '{build.name}' importé avec succès")
            print(f"Profession: {build.profession}")
            print(f"Rôle: {build.role}")
            if build.description:
                print(f"Description: {build.description}")
        else:
            # Pour les formats structurés, on utilise la méthode de base
            print(self._format_output(build.model_dump(), output_format))
