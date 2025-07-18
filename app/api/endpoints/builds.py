"""
Endpoints pour l'import et l'export des builds.
"""
import logging
import os
import traceback
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from fastapi.background import BackgroundTasks

from app.models.build import BuildData, ProfessionType, RoleType, TraitLine
from app.services.build_io import BuildIO
from app.schemas.build import PlayerBuildResponse, player_build_to_response

# Configuration du logger
logger = logging.getLogger(__name__)

# Le préfixe est maintenant géré dans app/api/endpoints/__init__.py
router = APIRouter(tags=["builds"])

# Dossier pour les exports
export_dir = Path("exports")
export_dir.mkdir(exist_ok=True)


async def get_build_from_database(build_id: str) -> Optional[BuildData]:
    """
    Récupère un build depuis la base de données.
    
    Args:
        build_id: Identifiant unique du build à récupérer
        
    Returns:
        Le BuildData correspondant ou None si non trouvé
        
    Note:
        Cette fonction est un exemple et doit être implémentée avec votre système de base de données.
    """
    # TODO: Implémenter la récupération depuis la base de données
    # Exemple d'implémentation factice pour les tests
    logger.debug("Récupération du build depuis la base de données (ID: %s)", build_id)
    
    # Simuler un build factice pour les tests
    if build_id == "example":
        return BuildData(
            name="Exemple de build",
            profession=ProfessionType.GUARDIAN,
            role=RoleType.HEAL,
            specializations=[
                TraitLine(id=46, name="Zeal", traits=[909, 914, 909]),
                TraitLine(id=27, name="Honor", traits=[915, 908, 894]),
                TraitLine(id=62, name="Firebrand", traits=[904, 0, 0])
            ],
            skills=[62561, 9153, 0, 0, 0],
            equipment={},
            description="Exemple de build pour démonstration"
        )
    
    return None

@router.post(
    "/import",
    response_model=None,  # Désactiver le modèle de réponse automatique
    status_code=status.HTTP_201_CREATED,
    summary="Importer un build depuis un fichier",
    responses={
        201: {"description": "Build importé avec succès", "model": PlayerBuildResponse},
        400: {"description": "Format de fichier invalide"},
        500: {"description": "Erreur lors du traitement du fichier"}
    }
)
async def import_build(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Fichier JSON contenant le build à importer")
):
    """
    Importe un build depuis un fichier JSON.
    
    Le fichier doit être au format natif de l'application.
    """
    try:
        # Vérifier le type de fichier
        if not file.filename.lower().endswith('.json'):
            logger.warning("Tentative d'import d'un fichier non JSON: %s", file.filename)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le fichier doit être au format JSON"
            )
        
        # Lire et valider le build
        build = await BuildIO.from_upload(file)
        
        # Enregistrer le build importé (optionnel)
        if background_tasks:
            output_path = BuildIO.generate_filename(build)
            background_tasks.add_task(
                BuildIO.to_file,
                build=build,
                file_path=output_path
            )
        
        # Convertir le PlayerBuild en PlayerBuildResponse
        response = player_build_to_response(build)
        
        logger.info(
            "Build importé avec succès pour la profession: %s",
            build.profession_id
        )
        return response
        
    except HTTPException as http_exc:
        logger.warning(
            "Erreur HTTP lors de l'import du build: %s",
            str(http_exc.detail)
        )
        raise http_exc
        
    except Exception as e:
        error_msg = f"Erreur lors du traitement du fichier: {str(e)}"
        logger.error(
            "%s\nTraceback:\n%s",
            error_msg,
            traceback.format_exc()
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        ) from e

@router.get(
    "/export/{build_id}",
    response_model=None,  # Désactiver le modèle de réponse automatique
    summary="Exporter un build existant",
    responses={
        200: {"description": "Fichier JSON contenant le build"},
        404: {"description": "Build non trouvé"}
    }
)
async def export_build(
    background_tasks: BackgroundTasks,
    build_id: str
): 
    """
    Exporte un build existant au format JSON natif.
    
    Args:
        build_id: ID du build à exporter
        
    Returns:
        Fichier JSON contenant le build
        
    Note:
        Cette version est un exemple et nécessite d'être adaptée à votre système de stockage des builds.
    """
    try:
        logger.info("Tentative d'export du build ID: %s", build_id)
        
        # Récupérer le build depuis la base de données
        build = await get_build_from_database(build_id)
        if not build:
            logger.warning("Build non trouvé avec l'ID: %s", build_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucun build trouvé avec l'ID: {build_id}"
            )
            
        logger.debug("Build trouvé: %s", build.name)
        
        # Exporter vers un fichier temporaire
        output_path = BuildIO.generate_filename(build, str(export_dir))
        BuildIO.to_file(build, output_path)
        
        # Configurer la suppression du fichier après envoi
        if background_tasks:
            background_tasks.add_task(lambda: os.remove(output_path))
        
        # Retourner le fichier
        return FileResponse(
            path=output_path,
            filename=Path(output_path).name,
            media_type='application/json',
            background=background_tasks
        )
        
    except Exception as e:
        logger.error("Erreur lors de l'export du build: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'export du build: {str(e)}") from e

@router.post(
    "/export",
    response_model=None,  # Désactiver le modèle de réponse automatique
    summary="Exporter un build directement depuis les données fournies",
    responses={
        200: {"description": "Fichier JSON contenant le build"},
        400: {"description": "Données du build invalides"}
    }
)
async def export_build_directly(
    background_tasks: BackgroundTasks,
    build: BuildData
): 
    """
    Exporte un build directement depuis les données fournies.
    
    Args:
        build: Données du build à exporter
        
    Returns:
        Fichier JSON contenant le build
    """
    try:
        # Exporter vers un fichier temporaire
        output_path = BuildIO.generate_filename(build, str(export_dir))
        BuildIO.to_file(build, output_path)
        
        # Configurer la suppression du fichier après envoi
        if background_tasks:
            background_tasks.add_task(lambda: os.remove(output_path))
        
        # Retourner le fichier
        return FileResponse(
            path=output_path,
            filename=Path(output_path).name,
            media_type='application/json',
            background=background_tasks
        )
        
    except Exception as e:
        logger.error("Erreur lors de l'export direct du build: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'export du build: {str(e)}") from e

@router.get(
    "/template",
    response_model=BuildData,
    status_code=status.HTTP_200_OK,
    summary="Obtenir un modèle de build vide",
    responses={
        200: {"description": "Modèle de build vide avec des valeurs par défaut"}
    }
)
async def get_build_template() -> BuildData:
    """
    Retourne un modèle de build vide avec des valeurs par défaut.
    """
    logger.debug("Génération d'un modèle de build vide")
    
    return BuildData(
        name="Nouveau build",
        profession=ProfessionType.GUARDIAN,
        role=RoleType.DPS,
        specializations=[
            TraitLine(id=0, name="", traits=[0, 0, 0]),
            TraitLine(id=0, name="", traits=[0, 0, 0]),
            TraitLine(id=0, name="", traits=[0, 0, 0])
        ],
        skills=[0, 0, 0, 0, 0],
        equipment={},
        description=""
    )

# Export du routeur pour une utilisation dans __init__.py
__all__ = ["router"]
