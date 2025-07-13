"""
Service pour exporter les builds au format natif de l'application.
"""
from typing import Dict, Any, Optional
import json
from pathlib import Path
from datetime import datetime

from fastapi import HTTPException
from pydantic import ValidationError

from app.models.build import BuildData


class BuildExporter:
    """Classe pour exporter les builds dans différents formats."""
    
    @staticmethod
    def to_json(build: BuildData, pretty: bool = True) -> str:
        """
        Exporte un build au format JSON.
        
        Args:
            build: Le build à exporter
            pretty: Si True, formate le JSON pour une meilleure lisibilité
            
        Returns:
            Une chaîne JSON représentant le build
        """
        indent = 2 if pretty else None
        return build.model_dump_json(indent=indent, exclude_unset=True)
    
    @staticmethod
    def to_file(build: BuildData, file_path: str, pretty: bool = True) -> str:
        """
        Exporte un build dans un fichier.
        
        Args:
            build: Le build à exporter
            file_path: Chemin du fichier de sortie
            pretty: Si True, formate le JSON pour une meilleure lisibilité
            
        Returns:
            Le chemin du fichier créé
            
        Raises:
            HTTPException: En cas d'erreur lors de l'export
        """
        try:
            # S'assurer que le répertoire existe
            output_path = Path(file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Exporter en JSON
            json_data = BuildExporter.to_json(build, pretty)
            
            # Écrire dans le fichier
            output_path.write_text(json_data, encoding='utf-8')
            
            return str(output_path.absolute())
            
        except (IOError, OSError) as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de l'écriture du fichier : {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de l'export du build : {str(e)}"
            )
    
    @classmethod
    def generate_filename(cls, build: BuildData, base_dir: str = "exports") -> str:
        """
        Génère un nom de fichier unique pour un build.
        
        Args:
            build: Le build à exporter
            base_dir: Répertoire de base pour l'export
            
        Returns:
            Chemin complet du fichier
        """
        # Créer un nom de fichier sécurisé
        safe_name = "".join(c if c.isalnum() else "_" for c in build.name.lower())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{build.profession}_{timestamp}.json"
        
        # Retourner le chemin complet
        return str(Path(base_dir) / filename)


# Fonction utilitaire pour faciliter l'export
def export_build(build: BuildData, output_path: Optional[str] = None, pretty: bool = True) -> str:
    """
    Exporte un build au format natif.
    
    Args:
        build: Le build à exporter
        output_path: Chemin du fichier de sortie (optionnel)
        pretty: Si True, formate le JSON pour une meilleure lisibilité
        
    Returns:
        Le chemin du fichier créé
        
    Exemple d'utilisation:
        # Exporter avec un nom de fichier généré automatiquement
        path = export_build(my_build)
        
        # Exporter vers un emplacement spécifique
        path = export_build(my_build, "mon_build.json")
    """
    if output_path is None:
        output_path = BuildExporter.generate_filename(build)
    
    return BuildExporter.to_file(build, output_path, pretty)
