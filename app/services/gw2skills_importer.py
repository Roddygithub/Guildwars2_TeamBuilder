"""
Service pour importer des builds depuis gw2skills.net
"""
from typing import Dict, Any, Optional, Union
import re
import base64
import zlib
import json
from urllib.parse import urlparse, parse_qs

from fastapi import HTTPException
from pydantic import HttpUrl, ValidationError

from app.models.build import BuildData, ProfessionType, RoleType, EquipmentItem
from app.scoring.engine import PlayerBuild

class Gw2SkillsImporter:
    """
    Service pour importer des builds depuis gw2skills.net
    """
    
    @staticmethod
    def from_url(url: Union[HttpUrl, str]) -> PlayerBuild:
        """
        Crée un PlayerBuild à partir d'une URL gw2skills.net
        
        Args:
            url: URL du build gw2skills.net (peut être un objet HttpUrl ou une chaîne)
            
        Returns:
            Un objet PlayerBuild
            
        Raises:
            ValueError: Si l'URL n'est pas valide ou si le parsing échoue
            HTTPException: Si la récupération ou le traitement échoue
        """
        try:
            # Convertir l'URL en chaîne si c'est un objet HttpUrl
            url_str = str(url)
            
            # Vérifier que c'est bien une URL gw2skills.net
            if "gw2skills.net/editor/" not in url_str:
                raise ValueError("L'URL doit être un lien vers un build gw2skills.net")
            
            # Extraire le code du build depuis l'URL
            parsed_url = urlparse(url_str)
            query = parse_qs(parsed_url.query)
            
            # Le code du build est dans la partie query de l'URL
            if not parsed_url.query:
                raise ValueError("Aucun code de build trouvé dans l'URL")
                
            # Le code est la partie avant le '?' (s'il y a des paramètres supplémentaires)
            build_code = parsed_url.query.split('?')[0]
            
            # Décoder le code du build
            build_data = Gw2SkillsImporter._decode_build_code(build_code)
            
            # Convertir en PlayerBuild
            return Gw2SkillsImporter._map_to_player_build(build_data)
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erreur lors de l'import du build depuis gw2skills.net: {str(e)}"
            )
    
    @staticmethod
    def _decode_build_code(build_code: str) -> Dict[str, Any]:
        """
        Décode le code du build depuis l'URL gw2skills.net
        
        Args:
            build_code: Code du build extrait de l'URL
            
        Returns:
            Dictionnaire contenant les données du build
            
        Raises:
            ValueError: Si le décodage échoue
        """
        try:
            # Le code est encodé en base64 avec des caractères URL-safe
            # et compressé avec zlib
            
            # Nettoyer le code (supprimer les éventuels paramètres supplémentaires)
            if '?' in build_code:
                build_code = build_code.split('?')[0]
            
            # Remplacer les caractères URL-safe
            build_code = build_code.replace('-', '+').replace('_', '/')
            
            # Ajouter le padding manquant si nécessaire
            padding = len(build_code) % 4
            if padding:
                build_code += '=' * (4 - padding)
            
            # Décoder le base64
            try:
                compressed_data = base64.b64decode(build_code)
            except Exception as e:
                raise ValueError(f"Échec du décodage base64: {str(e)}")
            
            # Décompresser avec zlib (avec différentes méthodes de décompression)
            try:
                # Essayer avec la méthode standard
                try:
                    json_data = zlib.decompress(compressed_data).decode('utf-8')
                except zlib.error:
                    # Essayer avec une fenêtre de décompression plus grande
                    json_data = zlib.decompress(compressed_data, 15 + 32).decode('utf-8')
                
                # Parser le JSON
                return json.loads(json_data)
                
            except zlib.error as e:
                # Si la décompression échoue, essayer d'interpréter directement comme JSON
                try:
                    return json.loads(compressed_data.decode('utf-8'))
                except Exception:
                    raise ValueError(f"Échec de la décompression zlib: {str(e)}")
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Erreur de parsing JSON: {str(e)}")
            
        except Exception as e:
            raise ValueError(f"Échec du décodage du code du build: {str(e)}")
    
    @staticmethod
    def _map_to_player_build(build_data: Dict[str, Any]) -> PlayerBuild:
        """
        Convertit les données brutes du build en objet PlayerBuild
        
        Args:
            build_data: Données brutes du build
            
        Returns:
            Un objet PlayerBuild
            
        Raises:
            ValueError: Si la conversion échoue
        """
        try:
            # Extraire les informations de base
            profession = build_data.get('profession', '').lower()
            
            # Mapper la profession vers notre énumération
            profession_map = {
                'guardian': ProfessionType.GUARDIAN,
                'warrior': ProfessionType.WARRIOR,
                'engineer': ProfessionType.ENGINEER,
                'ranger': ProfessionType.RANGER,
                'thief': ProfessionType.THIEF,
                'elementalist': ProfessionType.ELEMENTALIST,
                'mesmer': ProfessionType.MESMER,
                'necromancer': ProfessionType.NECROMANCER,
                'revenant': ProfessionType.REVENANT
            }
            
            profession_enum = profession_map.get(profession)
            if not profession_enum:
                raise ValueError(f"Profession non reconnue: {profession}")
            
            # Déterminer le rôle (simplifié pour l'instant)
            role = RoleType.DPS  # Par défaut
            
            # Extraire les spécialisations
            specializations = []
            for spec in build_data.get('specializations', []):
                specializations.append({
                    'id': spec.get('id', '').lower(),
                    'name': spec.get('name', 'Sans nom'),
                    'traits': spec.get('traits', [0, 0, 0])
                })
            
            # Extraire les compétences
            skills = build_data.get('skills', {
                'heal': 0,
                'utilities': [0, 0, 0],
                'elite': 0
            })
            
            # Extraire l'équipement (simplifié pour l'instant)
            equipment = {}
            for slot, item in build_data.get('equipment', {}).items():
                if item:
                    equipment[slot] = EquipmentItem(
                        id=item.get('id', 0),
                        name=item.get('name', 'Inconnu'),
                        rarity=item.get('rarity', 'Basic'),
                        stats=item.get('stats', {})
                    )
            
            # Créer l'objet BuildData
            build_data_obj = BuildData(
                name=build_data.get('name', 'Build sans nom'),
                profession=profession_enum,
                role=role,
                specializations=specializations,
                skills=skills,
                equipment=equipment,
                source='gw2skills.net'
            )
            
            # Créer et retourner le PlayerBuild
            return PlayerBuild(
                profession_id=profession_enum.value,
                roles={role.value},
                buffs=[],  # À déterminer à partir des compétences et spécialisations
                source='gw2skills.net',
                metadata={
                    'name': build_data.get('name', 'Build sans nom'),
                    'specializations': specializations,
                    'skills': skills,
                    'equipment': {k: v.dict() for k, v in equipment.items()}
                }
            )
            
        except Exception as e:
            raise ValueError(f"Échec de la conversion en PlayerBuild: {str(e)}")

# Exemple d'utilisation
if __name__ == "__main__":
    # Exemple d'URL de test
    test_url = "https://fr.gw2skills.net/editor/?PWhEQLUmQCrJs5k4w6alN6Qv43WB-DWpYChANESIUxQVZNHVrgjQIKkmKiOjoKSVbfEEiRkAGUVd/QKVFAbR/zIA-w"
    
    try:
        player_build = Gw2SkillsImporter.from_url(test_url)
        print(f"Build importé avec succès: {player_build}")
    except Exception as e:
        print(f"Erreur lors de l'import: {str(e)}")
