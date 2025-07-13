"""
Service unifié pour l'import/export des builds au format natif.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

from fastapi import HTTPException, UploadFile
from pydantic import ValidationError, HttpUrl

from app.models.build import BuildData, ProfessionType, RoleType
from app.scoring.engine import PlayerBuild


class BuildIO:
    """
    Service unifié pour l'import et l'export des builds.
    Gère à la fois le format natif JSON et la conversion vers/depuis PlayerBuild.
    """
    
    # ===== IMPORT =====
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> PlayerBuild:
        """
        Importe un build depuis un fichier JSON.
        
        Args:
            file_path: Chemin vers le fichier JSON
            
        Returns:
            Un objet PlayerBuild
            
        Raises:
            HTTPException: En cas d'erreur de lecture ou de validation
        """
        try:
            # Lire le contenu du fichier
            content = Path(file_path).read_text(encoding='utf-8')
            return cls.from_json(content)
            
        except (IOError, OSError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erreur lors de la lecture du fichier: {str(e)}"
            )
    
    @classmethod
    async def from_upload(cls, file: UploadFile) -> PlayerBuild:
        """
        Importe un build depuis un fichier uploadé.
        
        Args:
            file: Fichier uploadé via une requête HTTP
            
        Returns:
            Un objet PlayerBuild
        """
        try:
            content = await file.read()
            return cls.from_json(content.decode('utf-8'))
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erreur lors de la lecture du fichier uploadé: {str(e)}"
            )
    
    @classmethod
    def from_json(cls, json_str: str) -> PlayerBuild:
        """
        Importe un build depuis une chaîne JSON.
        
        Args:
            json_str: Chaîne JSON représentant le build
            
        Returns:
            Un objet PlayerBuild
            
        Raises:
            HTTPException: En cas d'erreur de validation
        """
        try:
            # Parser le JSON
            build_data = json.loads(json_str)
            
            # Valider avec le modèle Pydantic
            build = BuildData(**build_data)
            
            # Extraire les buffs en fonction du rôle et de la profession
            buffs = cls._extract_buffs(build)
            
            # Créer le PlayerBuild
            return PlayerBuild(
                profession_id=build.profession.value,
                roles={build.role.value},
                buffs=buffs,
                source=str(build.source) if build.source else None,
                metadata={
                    "name": build.name,
                    "description": build.description or "",
                    "specializations": [
                        {"id": spec.id, "name": spec.name, "traits": spec.traits}
                        for spec in build.specializations
                    ],
                    "skills": build.skills or [],
                    "equipment": build.equipment
                }
            )
            
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"JSON invalide: {str(e)}"
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Données de build invalides: {str(e)}"
            )
    
    # ===== EXPORT =====
    
    @classmethod
    def to_json(cls, build: Union[BuildData, PlayerBuild], pretty: bool = True) -> str:
        """
        Exporte un build en JSON.
        
        Args:
            build: Le build à exporter (BuildData ou PlayerBuild)
            pretty: Si True, formate le JSON pour une meilleure lisibilité
            
        Returns:
            Une chaîne JSON
        """
        if isinstance(build, PlayerBuild):
            build = cls._player_build_to_build_data(build)
        
        indent = 2 if pretty else None
        return build.model_dump_json(indent=indent, exclude_unset=True)
    
    @classmethod
    def to_file(
        cls, 
        build: Union[BuildData, PlayerBuild], 
        file_path: Union[str, Path], 
        pretty: bool = True
    ) -> str:
        """
        Exporte un build dans un fichier.
        
        Args:
            build: Le build à exporter
            file_path: Chemin du fichier de sortie
            pretty: Si True, formate le JSON pour une meilleure lisibilité
            
        Returns:
            Le chemin du fichier créé
        """
        # S'assurer que le répertoire existe
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Exporter en JSON
        json_data = cls.to_json(build, pretty)
        
        # Écrire dans le fichier
        output_path.write_text(json_data, encoding='utf-8')
        
        return str(output_path.absolute())
    
    @classmethod
    def generate_filename(
        cls, 
        build: Union[BuildData, PlayerBuild], 
        base_dir: str = "exports"
    ) -> str:
        """
        Génère un nom de fichier unique pour un build.
        
        Args:
            build: Le build à exporter
            base_dir: Répertoire de base pour l'export
            
        Returns:
            Chemin complet du fichier
        """
        from datetime import datetime
        
        if isinstance(build, PlayerBuild):
            name = build.metadata.get("name", "build")
            profession = build.profession_id
        else:
            name = build.name
            profession = build.profession.value
            
        # Créer un nom de fichier sécurisé
        safe_name = "".join(c if c.isalnum() else "_" for c in name.lower())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{profession}_{timestamp}.json"
        
        # Retourner le chemin complet
        return str(Path(base_dir) / filename)
    
    # ===== UTILITAIRES =====
    
    @staticmethod
    def _player_build_to_build_data(player_build: PlayerBuild) -> BuildData:
        """Convertit un PlayerBuild en BuildData."""
        metadata = player_build.metadata or {}
        
        return BuildData(
            name=metadata.get("name", "Build sans nom"),
            profession=ProfessionType(player_build.profession_id),
            role=RoleType(next(iter(player_build.roles), "dps")),
            specializations=metadata.get("specializations", []),
            skills=metadata.get("skills", []),
            equipment=metadata.get("equipment", {}),
            description=metadata.get("description", ""),
            source=metadata.get("source")
        )
    
    @staticmethod
    def _extract_buffs(build: BuildData) -> List[str]:
        """Extrait les buffs fournis par le build."""
        buffs = []
        
        # Buffs basés sur le rôle
        if build.role == RoleType.QUICKNESS:
            buffs.append("quickness")
        elif build.role == RoleType.ALACRITY:
            buffs.append("alacrity")
            
        # Buffs basés sur la profession et les spécialisations
        if build.profession == ProfessionType.GUARDIAN:
            buffs.extend(["aegis", "stability"])
            if build.role in [RoleType.HEAL, RoleType.SUPPORT]:
                buffs.extend(["protection", "regeneration"])
                
        elif build.profession == ProfessionType.REVENANT:
            buffs.append("alacrity")
            if build.role in [RoleType.HEAL, RoleType.SUPPORT]:
                buffs.extend(["protection", "regeneration"])
        
        # Buffs de base pour les rôles de support
        if build.role != RoleType.DPS:
            buffs.extend(["might", "fury"])
            
        return list(set(buffs))  # Éliminer les doublons
