"""Tests pour l'extraction de l'équipement depuis gw2skilleditor."""
import pytest
from unittest.mock import patch, MagicMock
from pydantic import HttpUrl

from app.services.build_importer import BuildImporter
from app.scoring.engine import PlayerBuild

# Données de test simulées pour une page de build avec équipement
MOCK_HTML_WITH_EQUIPMENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Build with Equipment - gw2skilleditor</title>
</head>
<body>
    <h1 class="build-title">Test Build with Equipment</h1>
    
    <div class="profession-icon guardian"></div>
    
    <div class="build-meta">
        <span class="build-role">DPS</span>
    </div>
    
    <div class="specializations">
        <div class="specialization" data-specialization="1">
            <div class="trait active" data-trait-id="1"></div>
            <div class="trait active" data-trait-id="2"></div>
            <div class="trait active" data-trait-id="3"></div>
        </div>
        <div class="specialization" data-specialization="2">
            <div class="trait active" data-trait-id="4"></div>
            <div class="trait active" data-trait-id="5"></div>
            <div class="trait active" data-trait-id="6"></div>
        </div>
        <div class="specialization" data-specialization="3">
            <div class="trait active" data-trait-id="7"></div>
            <div class="trait active" data-trait-id="8"></div>
            <div class="trait active" data-trait-id="9"></div>
        </div>
    </div>
    
    <div class="skills">
        <div class="skill-slot">
            <div class="skill-icon" data-skill-id="12345"></div>
        </div>
        <div class="skill-slot">
            <div class="skill-icon" data-skill-id="23456"></div>
        </div>
        <div class="skill-slot">
            <div class="skill-icon" data-skill-id="34567"></div>
        </div>
        <div class="skill-slot">
            <div class="skill-icon" data-skill-id="45678"></div>
        </div>
        <div class="skill-slot">
            <div class="skill-icon" data-skill-id="56789"></div>
        </div>
    </div>
    
    <!-- Équipement de test -->
    <div id="equipment-helm" data-item-id="1234" data-item-name="Test Helm">
        <div class="upgrade-slot" data-item-id="1111" data-item-name="Superior Rune of the Scholar"></div>
    </div>
    <div id="equipment-coat" data-item-id="2345" data-item-name="Test Coat">
        <div class="infusion-slot" data-item-id="2222" data-item-name="+9 Agony Infusion"></div>
        <div class="upgrade-slot" data-item-id="1111" data-item-name="Superior Rune of the Scholar"></div>
    </div>
    <div id="equipment-weapon-a1" data-item-id="3456" data-item-name="Test Sword">
        <div class="upgrade-slot" data-item-id="3333" data-item-name="Superior Sigil of Force"></div>
    </div>
</body>
</html>
"""

class MockResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")

@pytest.fixture
def mock_requests():
    with patch('httpx.Client') as mock_client:
        mock_response = MockResponse(MOCK_HTML_WITH_EQUIPMENT)
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        yield mock_client

def test_equipment_extraction_basic(mock_requests):
    """Teste l'extraction de base de l'équipement."""
    url = "https://lucky-noobs.com/builds/view/12345"
    
    # Appel de la méthode à tester
    build = BuildImporter.from_gw2skilleditor_url(url)
    
    # Vérifications
    assert isinstance(build, PlayerBuild)
    assert 'equipment' in build.metadata
    equipment = build.metadata['equipment']
    
    # Vérifier que les pièces d'équipement attendues sont présentes
    assert 'Helm' in equipment
    assert 'Coat' in equipment
    assert 'WeaponA1' in equipment
    
    # Vérifier les détails du casque
    helm = equipment['Helm']
    assert helm.id == 1234
    assert helm.name == 'Test Helm'
    assert len(helm.upgrades) == 1
    assert helm.upgrades[0] == 1111  # Rune
    
    # Vérifier les détails de la cotte de mailles
    coat = equipment['Coat']
    assert coat.id == 2345
    assert coat.name == 'Test Coat'
    assert len(coat.infusions) == 1
    assert coat.infusions[0] == 2222  # Infusion
    assert len(coat.upgrades) == 1
    assert coat.upgrades[0] == 1111  # Rune
    
    # Vérifier les détails de l'arme
    weapon = equipment['WeaponA1']
    assert weapon.id == 3456
    assert weapon.name == 'Test Sword'
    assert len(weapon.upgrades) == 1
    assert weapon.upgrades[0] == 3333  # Sigil

def test_equipment_missing_slots(mock_requests):
    """Teste que les emplacements d'équipement manquants ne sont pas inclus."""
    url = "https://lucky-noobs.com/builds/view/12345"
    build = BuildImporter.from_gw2skilleditor_url(url)
    assert 'equipment' in build.metadata
    equipment = build.metadata['equipment']
    
    # Vérifier que seuls les emplacements avec des données sont inclus
    assert 'Helm' in equipment
    assert 'Coat' in equipment
    assert 'WeaponA1' in equipment
    
    # Vérifier qu'un emplacement non présent dans le HTML n'est pas inclus
    assert 'Boots' not in equipment
    assert 'Gloves' not in equipment
    assert 'Amulet' not in equipment

def test_equipment_without_upgrades(mock_requests):
    """Teste qu'un équipement sans améliorations a des listes vides."""
    # Modifier le HTML pour avoir un équipement sans améliorations
    html = MOCK_HTML_WITH_EQUIPMENT.replace(
        '<div id="equipment-helm" data-item-id="1234" data-item-name="Test Helm">\n        <div class="upgrade-slot" data-item-id="1111" data-item-name="Superior Rune of the Scholar"></div>',
        '<div id="equipment-helm" data-item-id="1234" data-item-name="Test Helm">'
    )
    
    with patch('httpx.Client') as mock_client:
        mock_response = MockResponse(html)
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        build = BuildImporter.from_gw2skilleditor_url("https://lucky-noobs.com/builds/view/12345")
        assert 'equipment' in build.metadata
        equipment = build.metadata['equipment']
        
        # Vérifier que les listes d'améliorations sont vides
        helm = equipment['Helm']
        assert helm.upgrades == []
        assert helm.infusions == []
