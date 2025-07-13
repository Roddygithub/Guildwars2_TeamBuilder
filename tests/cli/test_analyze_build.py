"""
Tests pour la commande analyze-build.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
import yaml
from fastapi import HTTPException

from app.cli.commands.analyze_build import AnalyzeBuildCommand

# Données de test
SAMPLE_BUILD = {
    "id": "test-123",
    "name": "Test Build",
    "profession": "Guardian",
    "roles": ["DPS"],
    "equipment": {
        "Helm": {"id": 1, "name": "Test Helm", "rarity": "Exotic"},
        "WeaponA1": {"id": 2, "name": "Test Sword", "type": "Sword"},
        "WeaponA2": {"id": 3, "name": "Test Focus", "type": "Focus"}
    },
    "skills": [1, 2, 3, 4, 5, 6, 7, 8, 9, 0],
    "specializations": [
        {"id": 1, "traits": [1, 2, 3]},
        {"id": 2, "traits": [4, 5, 6]},
        {"id": 3, "traits": [7, 8, 9]}
    ]
}

@pytest.fixture
def command():
    """Retourne une instance de la commande à tester."""
    return AnalyzeBuildCommand()

@pytest.fixture
def mock_response():
    """Crée une réponse HTTP simulée."""
    response = MagicMock()
    response.json.return_value = SAMPLE_BUILD
    response.status_code = 200
    return response

@patch('httpx.Client')
def test_analyze_build_from_api(mock_client_class, command, mock_response):
    """Teste l'analyse d'un build via l'API."""
    # Configurer le mock pour le client et sa méthode get
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__.return_value = mock_client
    mock_client_class.return_value = mock_client
    
    # Configurer les arguments de la commande
    args = MagicMock()
    args.build_id = "test-123"
    args.file = None
    args.show_equipment = True
    args.show_skills = True
    args.show_stats = True
    args.suggestions = True
    args.format = "text"
    args.api_url = "http://test-api"
    
    # Exécution
    result = command.execute(args)
    
    # Vérifications
    assert result == 0
    mock_client.get.assert_called_once_with("http://test-api/builds/test-123")

def test_analyze_build_from_file_json(command):
    """Teste l'analyse d'un build depuis un fichier JSON."""
    with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as f:
        json.dump(SAMPLE_BUILD, f)
        temp_path = f.name
    
    try:
        args = MagicMock()
        args.build_id = None
        args.file = temp_path
        args.show_equipment = False
        args.show_skills = False
        args.show_stats = False
        args.suggestions = False
        args.format = "text"
        
        # Exécution
        result = command.execute(args)
        assert result == 0
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def test_analyze_build_from_file_yaml(command):
    """Teste l'analyse d'un build depuis un fichier YAML."""
    with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w', delete=False) as f:
        yaml.dump(SAMPLE_BUILD, f)
        temp_path = f.name
    
    try:
        args = MagicMock()
        args.build_id = None
        args.file = temp_path
        args.show_equipment = False
        args.show_skills = False
        args.show_stats = False
        args.suggestions = False
        args.format = "text"
        
        # Exécution
        result = command.execute(args)
        assert result == 0
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def test_analyze_build_invalid_file(command):
    """Teste le cas d'un fichier invalide."""
    with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', delete=False) as f:
        f.write("ceci n'est pas du JSON ni du YAML valide")
        temp_path = f.name
    
    try:
        args = MagicMock()
        args.build_id = None
        args.file = temp_path
        args.format = "text"
        args.show_equipment = False
        args.show_skills = False
        args.show_stats = False
        args.suggestions = False
        args._is_test = True  # Pour forcer la propagation des exceptions
        
        # Exécution et vérification de l'erreur
        with pytest.raises(ValueError) as exc_info:
            command.execute(args)
            
        # Vérifier que l'erreur contient un message pertinent
        assert "Format de fichier non reconnu" in str(exc_info.value)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

@patch('httpx.Client')
def test_analyze_build_api_error(mock_client_class, command):
    """Teste la gestion des erreurs d'API."""
    # Configurer le mock pour lever une exception de connexion
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.RequestError("Erreur de connexion")
    mock_client.__enter__.return_value = mock_client
    mock_client_class.return_value = mock_client
    
    args = MagicMock()
    args.build_id = "test-123"
    args.file = None
    args.format = "text"
    args.api_url = "http://test-api"
    args._is_test = True  # Pour forcer la propagation des erreurs
    
    # Exécution et vérification de l'erreur
    with pytest.raises(ConnectionError) as exc_info:
        command.execute(args)
    
    # Vérifier que le message d'erreur contient bien l'information attendue
    assert "Erreur de connexion à l'API" in str(exc_info.value)

@patch('httpx.Client')
def test_analyze_build_output_formats(mock_client_class, command, mock_response):
    """Teste les différents formats de sortie."""
    # Configurer le mock pour le client et sa méthode get
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__.return_value = mock_client
    mock_client_class.return_value = mock_client
    
    for fmt in ["text", "json", "yaml"]:
        args = MagicMock()
        args.build_id = "test-123"
        args.file = None
        args.show_equipment = True
        args.show_skills = True
        args.show_stats = True
        args.suggestions = True
        args.format = fmt
        args.api_url = "http://test-api"
        args._is_test = True  # Pour forcer l'utilisation de print au lieu de self.console.print
        
        # Vérification qu'aucune exception n'est levée
        result = command.execute(args)
        assert result == 0, f"Le format {fmt} n'a pas été géré correctement"

def test_analyze_build_missing_fields(command):
    """Teste l'analyse d'un build avec des champs manquants."""
    # Création d'un build incomplet
    incomplete_build = {"name": "Incomplete Build"}
    
    with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as f:
        json.dump(incomplete_build, f)
        temp_path = f.name
    
    try:
        args = MagicMock()
        args.build_id = None
        args.file = temp_path
        args.show_equipment = False
        args.show_skills = False
        args.show_stats = False
        args.suggestions = True  # Activer les suggestions pour détecter les champs manquants
        args.format = "text"
        
        # Exécution
        result = command.execute(args)
        assert result == 0  # Doit réussir mais avec des avertissements
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

@patch('httpx.Client')
def test_analyze_build_verbose_output(mock_client_class, command, capsys):
    """Teste que la sortie contient bien les informations attendues."""
    # Créer un mock pour la réponse HTTP
    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_BUILD
    mock_response.status_code = 200
    
    # Configurer le mock pour le client et sa méthode get
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__.return_value = mock_client
    mock_client_class.return_value = mock_client
    
    # Configurer les arguments de la commande
    args = MagicMock()
    args.build_id = "test-123"
    args.file = None
    args.show_equipment = True
    args.show_skills = True
    args.show_stats = True
    args.suggestions = True
    args.format = "text"
    args.api_url = "http://test-api"
    args._is_test = True  # Pour forcer l'utilisation de print au lieu de self.console.print
    
    # Exécution
    command.execute(args)
    
    # Récupérer la sortie capturée
    captured = capsys.readouterr()
    output = captured.out
    
    # Vérifier que les chaînes attendues sont bien dans la sortie
    assert "Analyse du build: Test Build" in output
    assert "Profession: Guardian" in output
    assert "Rôle: DPS" in output
    assert "Statistiques" in output
    assert "Suggestions" in output
