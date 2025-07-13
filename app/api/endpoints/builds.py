"""
Endpoints pour l'import et l'export des builds.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional
import logging
import os
from pathlib import Path

from ...models.build import BuildData
from ...services.build_io import BuildIO
from ...scoring.engine import PlayerBuild

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/builds", tags=["builds"])

# Dossier pour les exports
export_dir = Path("exports")
export_dir.mkdir(exist_ok=True)

@router.post("/import", response_model=PlayerBuild, summary="Importer un build depuis un fichier")
async def import_build(
    file: UploadFile = File(..., description="Fichier JSON contenant le build à importer"),
    background_tasks: BackgroundTasks = None
) -> PlayerBuild:
    """
    Importe un build depuis un fichier JSON.
    
    Le fichier doit être au format natif de l'application.
    """
    try:
        # Vérifier le type de fichier
        if not file.filename.lower().endswith('.json'):
            raise HTTPException(status_code=400, detail="Le fichier doit être au format JSON")
        
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
        
        return build
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'import du build: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du fichier: {str(e)}")

@router.get("/export/{build_id}", response_class=FileResponse, summary="Exporter un build existant")
async def export_build(
    build_id: str,
    background_tasks: BackgroundTasks = None
) -> FileResponse:
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
        # TODO: Récupérer le build depuis votre base de données
        # build = get_build_from_database(build_id)
        # if not build:
        #     raise HTTPException(status_code=404, detail="Build non trouvé")
        
        # Pour l'exemple, on crée un build factice
        from ...models.build import ProfessionType, RoleType, TraitLine
        build = BuildData(
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
        logger.error(f"Erreur lors de l'export du build: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'export du build: {str(e)}")

@router.post("/export", response_class=FileResponse, summary="Exporter un build directement")
async def export_build_directly(
    build: BuildData,
    background_tasks: BackgroundTasks = None
) -> FileResponse:
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
        logger.error(f"Erreur lors de l'export direct du build: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'export du build: {str(e)}")

@router.get("/template", response_model=BuildData, summary="Obtenir un modèle de build vide")
async def get_build_template() -> BuildData:
    """
    Retourne un modèle de build vide avec des valeurs par défaut.
    """
    from ...models.build import ProfessionType, RoleType, TraitLine
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
