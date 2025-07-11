"""Tests d'intégration pour le service de données GW2."""

import asyncio
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.services.gw2_data_service import GW2DataService
from app.models.base import Base
from app.models import (
    Profession, Specialization, Skill, Trait, 
    Item, Weapon, Armor, Trinket, UpgradeComponent, ItemStat, ItemStats
)

# Configuration des tests
TEST_DB_URL = "sqlite:///:memory:"
TEST_API_KEY = os.getenv("GW2_API_KEY", "test_api_key")

# Fixture pour la base de données de test
@pytest.fixture(scope="module")
def db_engine():
    """Crée une base de données SQLite en mémoire pour les tests."""
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    # Créer les tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Nettoyage
    engine.dispose()

# Fixture pour la session de base de données
@pytest.fixture
def db_session(db_engine):
    """Crée une session de base de données pour les tests."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    # Nettoyage après le test
    session.close()
    transaction.rollback()
    connection.close()

# Fixture pour le service de données
@pytest.fixture
async def gw2_service(db_session):
    """Crée une instance du service de données pour les tests."""
    service = GW2DataService(db_session=db_session)
    await service.initialize()
    
    yield service
    
    # Nettoyage
    await service.close()

# Fixture pour les données de test
@pytest.fixture
def mock_api_responses():
    """Retourne des réponses simulées de l'API GW2 pour les tests."""
    return {
        "professions": ["Guardian", "Warrior", "Elementalist"],
        "specializations": [1, 2, 3, 4, 5],
        "skills": [10001, 10002, 10003],
        "traits": [20001, 20002, 20003],
        "items": [30001, 30002, 30003],
        "itemstats": [40001, 40002, 40003],
    }

# Tests d'intégration
class TestGW2DataServiceIntegration:
    """Tests d'intégration pour le service de données GW2."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, gw2_service):
        """Teste l'initialisation du service."""
        assert gw2_service is not None
        assert gw2_service._initialized is True
    
    @pytest.mark.asyncio
    async def test_sync_professions(self, gw2_service, db_session, mock_api_responses):
        """Teste la synchronisation des professions."""
        # Mock de l'appel API
        with patch.object(gw2_service._api, 'get_professions', 
                         return_value=mock_api_responses["professions"]) as mock_get:
            
            # Appel de la méthode à tester
            result = await gw2_service.sync_professions()
            
            # Vérifications
            mock_get.assert_called_once()
            assert result is not None
            assert "processed" in result
            assert result["processed"] > 0
            
            # Vérification en base de données
            professions = db_session.query(Profession).all()
            assert len(professions) == len(mock_api_responses["professions"])
    
    @pytest.mark.asyncio
    async def test_sync_skills(self, gw2_service, db_session, mock_api_responses):
        """Teste la synchronisation des compétences."""
        # Mock de l'appel API
        with patch.object(gw2_service._api, 'get_skills', 
                         return_value=mock_api_responses["skills"]) as mock_get_skills,\
             patch.object(gw2_service, '_batch_api_request', 
                        return_value={}) as mock_batch:
            
            # Configuration du mock pour _batch_api_request
            mock_batch.return_value = {
                skill_id: {"id": skill_id, "name": f"Skill {skill_id}", "type": "Utility"} 
                for skill_id in mock_api_responses["skills"]
            }
            
            # Appel de la méthode à tester
            result = await gw2_service.sync_skills()
            
            # Vérifications
            mock_get_skills.assert_called_once()
            mock_batch.assert_called_once()
            assert result is not None
            assert "processed" in result
            assert result["processed"] == len(mock_api_responses["skills"])
            
            # Vérification en base de données
            skills = db_session.query(Skill).all()
            assert len(skills) == len(mock_api_responses["skills"])
    
    @pytest.mark.asyncio
    async def test_sync_items(self, gw2_service, db_session, mock_api_responses):
        """Teste la synchronisation des objets."""
        # Mock de l'appel API
        with patch.object(gw2_service._api, 'get_items', 
                         return_value=mock_api_responses["items"]) as mock_get_items,\
             patch.object(gw2_service, '_batch_api_request') as mock_batch:
            
            # Configuration du mock pour _batch_api_request
            mock_batch.return_value = {
                item_id: {
                    "id": item_id, 
                    "name": f"Item {item_id}", 
                    "type": "Weapon",
                    "details": {"type": "Axe"}
                } 
                for item_id in mock_api_responses["items"]
            }
            
            # Appel de la méthode à tester
            result = await gw2_service.sync_items()
            
            # Vérifications
            mock_get_items.assert_called_once()
            mock_batch.assert_called_once()
            assert result is not None
            assert "weapons" in result
            assert result["weapons"]["processed"] == len(mock_api_responses["items"])
            
            # Vérification en base de données
            items = db_session.query(Item).all()
            assert len(items) == len(mock_api_responses["items"])
    
    @pytest.mark.asyncio
    async def test_cache_management(self, gw2_service):
        """Teste la gestion du cache."""
        # Test de mise en cache
        test_data = {"test": "data"}
        cache_key = "test:key"
        
        # Ajout au cache
        await gw2_service._cached_api_call(
            "/v2/test", 
            params={"id": 1}, 
            cache_key=cache_key,
            cache_ttl=60
        )
        
        # Récupération des informations du cache
        cache_info = await gw2_service.get_cache_info()
        assert cache_info["api_cache"]["size"] > 0
        
        # Test de vidage du cache
        await gw2_service.clear_cache()
        cache_info = await gw2_service.get_cache_info()
        assert cache_info["api_cache"]["size"] == 0
    
    @pytest.mark.asyncio
    async def test_sync_itemstats(self, gw2_service, db_session, mock_api_responses):
        """Teste la synchronisation des statistiques d'objets."""
        # Données de test pour les statistiques
        test_itemstats = [
            {
                "id": 1,
                "name": "Berserker's",
                "attributes": {
                    "Power": 42,
                    "Precision": 42,
                    "Ferocity": 42
                }
            },
            {
                "id": 2,
                "name": "Viper's",
                "attributes": {
                    "Power": 42,
                    "ConditionDamage": 42,
                    "Precision": 42,
                    "Expertise": 42
                }
            }
        ]
        
        # Mock de l'appel API
        with patch.object(gw2_service._api, 'get', 
                         return_value=[s['id'] for s in test_itemstats]) as mock_get_ids, \
             patch.object(gw2_service._api, 'get_itemstats', 
                         return_value=test_itemstats) as mock_get_itemstats:
            
            # Appel de la méthode à tester
            result = await gw2_service.sync_itemstats()
            
            # Vérifications
            mock_get_ids.assert_called_once_with('/v2/itemstats')
            mock_get_itemstats.assert_called_once()
            
            # Vérifier le résultat
            assert result is not None
            assert "total" in result
            assert "processed" in result
            assert "errors" in result
            assert result["total"] == len(test_itemstats)
            assert result["processed"] == len(test_itemstats)
            assert result["errors"] == 0
            
            # Vérification en base de données
            itemstats = db_session.query(ItemStats).all()
            assert len(itemstats) == len(test_itemstats)
            
            # Vérifier que les attributs ont été correctement mappés
            for stat in itemstats:
                if stat.name == "Berserker's":
                    assert stat.power == 42
                    assert stat.precision == 42
                    assert stat.ferocity == 42
                elif stat.name == "Viper's":
                    assert stat.power == 42
                    assert stat.condition_damage == 42
                    assert stat.precision == 42
                    assert stat.expertise == 42
    
    @pytest.mark.asyncio
    async def test_error_handling(self, gw2_service):
        """Teste la gestion des erreurs d'API."""
        # Mock d'une erreur d'API
        with patch.object(gw2_service._api, 'get_professions', 
                         side_effect=Exception("API Error")) as mock_get:
            
            # Appel de la méthode à tester
            result = await gw2_service.sync_professions()
            
            # Vérifications
            mock_get.assert_called_once()
            assert result is not None
            assert "error" in result
            assert "API Error" in result["error"]

# Tests de performance
class TestGW2DataServicePerformance:
    """Tests de performance pour le service de données GW2."""
    
    @pytest.mark.asyncio
    async def test_batch_processing_performance(self, gw2_service):
        """Teste les performances du traitement par lots."""
        # Données de test
        test_items = [{"id": i, "name": f"Item {i}"} for i in range(1, 1001)]
        
        # Fonction de traitement
        async def process_item(item):
            await asyncio.sleep(0.001)  # Simulation d'un traitement court
            return item
        
        # Mesure du temps d'exécution
        start_time = asyncio.get_event_loop().time()
        
        # Appel de la méthode à tester
        result = await gw2_service._batch_process(
            test_items,
            process_item,
            batch_size=100
        )
        
        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time
        
        # Vérifications
        assert result is not None
        assert result["total"] == len(test_items)
        assert result["succeeded"] == len(test_items)
        
        # Vérification des performances (doit être plus rapide que le traitement séquentiel)
        sequential_time_estimate = len(test_items) * 0.001  # 1ms par élément
        assert execution_time < sequential_time_estimate * 0.5  # Au moins 2x plus rapide

# Exemple d'utilisation avec pytest-asyncio
if __name__ == "__main__":
    import pytest
    import sys
    
    sys.exit(pytest.main(["-v", __file__]))
