"""Tests pour l'importation de builds depuis gw2skilleditor."""
import pytest
from unittest.mock import patch, MagicMock
from pydantic import HttpUrl

from app.services.build_importer import BuildImporter
from app.scoring.engine import PlayerBuild

# Données de test simulées pour une page de build gw2skilleditor
MOCK_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Build - gw2skilleditor</title>
</head>
<body>
    <h1 class="build-title">Test Heal Firebrand</h1>
    
    <div class="profession-icon guardian"></div>
    
    <div class="build-meta">
        <span class="build-role">Heal Support</span>
    </div>
    
    <div class="specializations">
        <div class="specialization" data-specialization="firebrand">
            <div class="trait active" data-trait-id="1"></div>
            <div class="trait active" data-trait-id="2"></div>
            <div class="trait active" data-trait-id="3"></div>
        </div>
        <div class="specialization" data-specialization="honor">
            <div class="trait active" data-trait-id="4"></div>
            <div class="trait active" data-trait-id="5"></div>
            <div class="trait active" data-trait-id="6"></div>
        </div>
        <div class="specialization" data-specialization="valor">
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
        mock_response = MockResponse(MOCK_HTML)
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        yield mock_client

def test_from_gw2skilleditor_url_valid(mock_requests):
    """Teste l'importation d'un build depuis une URL valide."""
    url = "https://lucky-noobs.com/builds/view/12345"
    
    # Appel de la méthode à tester
    build = BuildImporter.from_gw2skilleditor_url(url)
    
    # Vérifications
    assert isinstance(build, PlayerBuild)
    assert build.profession_id == "guardian"
    assert "heal" in build.roles
    assert build.source == url
    
    # Vérification des métadonnées
    assert "name" in build.metadata
    assert build.metadata["name"] == "Test Heal Firebrand"
    
    # Vérification des spécialisations
    assert "specializations" in build.metadata
    assert len(build.metadata["specializations"]) == 3
    assert build.metadata["specializations"][0]["id"] == "firebrand"
    
    # Vérification des compétences
    assert "skills" in build.metadata
    assert len(build.metadata["skills"]) == 5

def test_from_gw2skilleditor_invalid_url():
    """Teste qu'une erreur est levée pour une URL invalide."""
    with pytest.raises(ValueError, match="L'URL doit être un lien vers un build gw2skilleditor"):
        BuildImporter.from_gw2skilleditor_url("https://example.com/invalid")

def test_from_gw2skilleditor_http_error(mock_requests):
    """Teste la gestion des erreurs HTTP."""
    # Configurer le mock pour simuler une erreur HTTP
    mock_client = mock_requests.return_value.__enter__.return_value
    mock_response = MockResponse("Not Found", 404)
    mock_client.get.return_value = mock_response
    
    with pytest.raises(ValueError, match="Erreur lors de l'import du build"):
        BuildImporter.from_gw2skilleditor_url("https://lucky-noobs.com/builds/view/99999")

def test_from_gw2skilleditor_missing_data(mock_requests):
    """Teste le comportement avec des données manquantes dans la page HTML."""
    # Simuler une page HTML avec des données minimales mais valides
    mock_client = mock_requests.return_value.__enter__.return_value
    html = """
    <html>
    <body>
        <h1 class="build-title">Build Minimal</h1>
        <div class="profession-icon guardian"></div>
        <div class="build-meta"><span class="build-role">DPS</span></div>
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
            <div class="skill-slot"><div class="skill-icon" data-skill-id="1"></div></div>
            <div class="skill-slot"><div class="skill-icon" data-skill-id="2"></div></div>
            <div class="skill-slot"><div class="skill-icon" data-skill-id="3"></div></div>
            <div class="skill-slot"><div class="skill-icon" data-skill-id="4"></div></div>
            <div class="skill-slot"><div class="skill-icon" data-skill-id="5"></div></div>
        </div>
    </body>
    </html>
    """
    mock_response = MockResponse(html)
    mock_client.get.return_value = mock_response
    
    # Le parsing doit fonctionner avec les données minimales
    build = BuildImporter.from_gw2skilleditor_url("https://lucky-noobs.com/builds/view/12345")
    
    # Vérifier que le build a été correctement créé
    assert build.profession_id == "guardian"
    assert "dps" in build.roles
    assert build.metadata["name"] == "Build Minimal"
