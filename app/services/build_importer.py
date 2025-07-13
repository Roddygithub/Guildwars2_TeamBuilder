"""Service pour importer et convertir des builds depuis différents formats."""
from typing import List, Dict, Any, Optional, Union
from pydantic import HttpUrl, ValidationError

from app.models.build import BuildData, ProfessionType, RoleType
from app.scoring.engine import PlayerBuild

class BuildImporter:
    """Service pour importer et convertir des builds depuis différents formats."""
    
    @staticmethod
    def from_dict(build_data: Dict[str, Any]) -> PlayerBuild:
        """Crée un PlayerBuild à partir d'un dictionnaire de données.
        
        Args:
            build_data: Données du build au format dictionnaire
            
        Returns:
            Un objet PlayerBuild prêt à être utilisé par le système de scoring
            
        Raises:
            ValueError: Si les données du build sont invalides
        """
        try:
            # Valider les données avec le modèle Pydantic
            build = BuildData(**build_data)
            
            # Extraire les buffs en fonction du rôle et de la profession
            buffs = BuildImporter._extract_buffs(build)
            
            # Préparer les métadonnées avec l'équipement converti en objets EquipmentItem
            metadata = {
                "name": build.name,
                "description": build.description or "",
                "specializations": [
                    {"id": spec.id, "name": spec.name, "traits": spec.traits}
                    for spec in build.specializations
                ],
                "skills": build.skills or []
            }
            
            # Si l'équipement est présent, le convertir en objets EquipmentItem
            if hasattr(build, 'equipment') and build.equipment:
                from app.models.build import EquipmentItem
                equipment_dict = {}
                for slot, item_data in build.equipment.items():
                    if isinstance(item_data, dict):
                        equipment_dict[slot] = EquipmentItem(**item_data)
                    else:
                        # Si c'est déjà un EquipmentItem, on le garde tel quel
                        equipment_dict[slot] = item_data
                metadata["equipment"] = equipment_dict
            
            # Créer et retourner le PlayerBuild
            return PlayerBuild(
                profession_id=build.profession.value,
                roles={build.role.value},  # Utiliser un ensemble avec le rôle
                buffs=buffs,
                source=build.source,
                metadata=metadata
            )
        except ValidationError as e:
            raise ValueError(f"Données de build invalides: {str(e)}")
    
    @staticmethod
    def _extract_buffs(build: BuildData) -> List[str]:
        """Extrait les buffs fournis par le build en fonction de sa configuration.
        
        Args:
            build: Le build à analyser
            
        Returns:
            Liste des buffs fournis par le build
        """
        buffs = []
        
        # Buffs basés sur le rôle
        if build.role == RoleType.QUICKNESS:
            buffs.append("quickness")
        elif build.role == RoleType.ALACRITY:
            buffs.append("alacrity")
            
        # Buffs basés sur la profession et les spécialisations
        if build.profession == ProfessionType.GUARDIAN:
            buffs.append("aegis")
            buffs.append("stability")
            if build.role in [RoleType.HEAL, RoleType.SUPPORT]:
                buffs.append("protection")
                buffs.append("regeneration")
                
        elif build.profession == ProfessionType.REVENANT:
            buffs.append("alacrity")
            if build.role in [RoleType.HEAL, RoleType.SUPPORT]:
                buffs.append("protection")
                buffs.append("regeneration")
        
        # Ajouter les buffs de base
        if build.role != RoleType.DPS:
            buffs.append("might")
            buffs.append("fury")
            
        return list(set(buffs))  # Éliminer les doublons
    
    @staticmethod
    def from_gw2skilleditor_url(url: Union[HttpUrl, str]) -> PlayerBuild:
        """Crée un PlayerBuild à partir d'une URL gw2skilleditor.
        
        Args:
            url: URL du build gw2skilleditor (peut être un objet HttpUrl ou une chaîne)
            
        Returns:
            Un objet PlayerBuild
            
        Raises:
            ValueError: Si l'URL n'est pas valide ou si le parsing échoue
        """
        try:
            from bs4 import BeautifulSoup
            import httpx
            from urllib.parse import urlparse, parse_qs
            
            # Convertir l'URL en chaîne si c'est un objet HttpUrl
            url_str = str(url)
            
            # Vérifier que c'est bien une URL gw2skilleditor
            if "lucky-noobs.com/builds/view/" not in url_str:
                raise ValueError("L'URL doit être un lien vers un build gw2skilleditor (lucky-noobs.com/builds/)")
            
            # Récupérer le contenu de la page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            with httpx.Client() as client:
                response = client.get(url_str, headers=headers, follow_redirects=True)
                response.raise_for_status()
                
                # Parser le HTML
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Extraire les informations du build
                build_data = {}
                
                # 1. Nom du build
                title_elem = soup.find('h1', class_='build-title')
                build_data['name'] = title_elem.text.strip() if title_elem else "Build sans nom"
                
                # 2. Profession et spécialisation
                profession_elem = soup.find('div', class_='profession-icon')
                if profession_elem:
                    profession_class = next((c for c in profession_elem.get('class', []) if c != 'profession-icon'), '')
                    build_data['profession'] = profession_class.lower()
                
                # 3. Rôle (heal, dps, support, etc.)
                role_elem = soup.find('span', class_='build-role')
                if role_elem:
                    role_text = role_elem.text.strip().lower()
                    if 'heal' in role_text:
                        build_data['role'] = 'heal'
                    elif 'support' in role_text:
                        build_data['role'] = 'support'
                    elif 'dps' in role_text:
                        build_data['role'] = 'dps'
                    else:
                        build_data['role'] = 'dps'  # Par défaut
                
                # 4. Spécialisations
                specializations = []
                spec_elems = soup.select('.specialization')
                for spec_elem in spec_elems:
                    spec_name = spec_elem.get('data-specialization', '').lower()
                    traits = []
                    
                    # Extraire les traits sélectionnés
                    trait_elems = spec_elem.select('.trait.active')
                    for trait_elem in trait_elems:
                        trait_id = trait_elem.get('data-trait-id')
                        if trait_id:
                            traits.append(int(trait_id))
                    
                    if spec_name:
                        specializations.append({
                            'id': spec_name,
                            'name': spec_name.capitalize(),
                            'traits': traits if traits else [0, 0, 0]  # Valeurs par défaut
                        })
                
                build_data['specializations'] = specializations
                
                # 5. Compétences
                skills = []
                skill_elems = soup.select('.skill-slot .skill-icon')
                for skill_elem in skill_elems:
                    skill_id = skill_elem.get('data-skill-id')
                    if skill_id:
                        skills.append(int(skill_id))
                
                build_data['skills'] = skills
                
                # 6. Équipement
                equipment = {}
                
                # Définition des emplacements d'équipement principaux
                equipment_slots = {
                    'Helm': 'equipment-helm',
                    'Shoulders': 'equipment-shoulders',
                    'Coat': 'equipment-coat',
                    'Gloves': 'equipment-gloves',
                    'Leggings': 'equipment-leggings',
                    'Boots': 'equipment-boots',
                    'Amulet': 'equipment-amulet',
                    'Ring1': 'equipment-ring-1',
                    'Ring2': 'equipment-ring-2',
                    'Accessory1': 'equipment-accessory-1',
                    'Accessory2': 'equipment-accessory-2',
                    'Back': 'equipment-backpack',
                    'WeaponA1': 'equipment-weapon-a1',
                    'WeaponA2': 'equipment-weapon-a2',
                    'WeaponB1': 'equipment-weapon-b1',
                    'WeaponB2': 'equipment-weapon-b2',
                    'WeaponB3': 'equipment-weapon-b3',
                }
                
                # Extraire chaque pièce d'équipement
                for slot_name, slot_id in equipment_slots.items():
                    item_elem = soup.find('div', id=slot_id)
                    if item_elem and 'data-item-id' in item_elem.attrs:
                        item_id = item_elem['data-item-id']
                        item_name = item_elem.get('data-item-name', 'Unknown Item')
                        
                        # Extraire les infusions et améliorations
                        infusions = []
                        upgrades = []
                        
                        # Chercher les infusions (généralement dans des éléments enfants)
                        for infusion_elem in item_elem.select('.infusion-slot'):
                            infusion_id = infusion_elem.get('data-item-id')
                            if infusion_id and infusion_id.isdigit():
                                infusions.append(int(infusion_id))
                        
                        # Chercher les améliorations (runes, sigils, etc.)
                        for upgrade_elem in item_elem.select('.upgrade-slot'):
                            upgrade_id = upgrade_elem.get('data-item-id')
                            if upgrade_id and upgrade_id.isdigit():
                                upgrades.append(int(upgrade_id))
                        
                        # Ajouter l'équipement au dictionnaire
                        equipment[slot_name] = {
                            'id': int(item_id),
                            'name': item_name,
                            'infusions': infusions,
                            'upgrades': upgrades
                        }
                
                build_data['equipment'] = equipment
                
                # 7. Source
                build_data['source'] = url_str
                
                # Utiliser la méthode from_dict pour créer le PlayerBuild
                return BuildImporter.from_dict(build_data)
                
        except Exception as e:
            raise ValueError(f"Erreur lors de l'import du build depuis gw2skilleditor: {str(e)}")
