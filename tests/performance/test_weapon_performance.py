"""Tests de performance pour le modèle Weapon."""

import time
import statistics
from datetime import datetime
from typing import Dict, List, Tuple, Any
import pytest
from sqlalchemy.orm import Session, joinedload

from app.models.weapon import Weapon, WeaponType, ProfessionWeapon, ProfessionWeaponType
from app.database import SessionLocal
from app.utils.db_utils import with_session

# Nombre d'itérations pour les tests de performance
NUM_ITERATIONS = 50


def measure_time(func, *args, **kwargs) -> Tuple[float, Any]:
    """Mesure le temps d'exécution d'une fonction."""
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    return (end_time - start_time) * 1000, result  # en millisecondes


class TestWeaponPerformance:
    """Classe de tests de performance pour le modèle Weapon."""
    
    @pytest.fixture(scope="class")
    def db_session(self) -> Session:
        """Session de base de données pour les tests."""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    @pytest.fixture(scope="class")
    def test_weapon(self, db_session: Session) -> Weapon:
        """Arme de test pour les benchmarks."""
        # Récupère une arme avec des relations
        weapon = db_session.query(Weapon).options(
            joinedload(Weapon.profession_weapons)
                .joinedload(ProfessionWeapon.weapon_type)
                .joinedload(ProfessionWeaponType.weapon_skills)
                .joinedload(ProfessionWeapon.skill),
            joinedload(Weapon.skills)
        ).first()
        
        if not weapon:
            pytest.skip("Aucune arme avec des relations trouvée pour les tests")
        
        return weapon
    
    def test_get_skills_by_type(self, test_weapon: Weapon, db_session: Session):
        """Teste les performances de get_skills_by_type()."""
        # Mesure avec la nouvelle implémentation
        new_times = []
        for _ in range(NUM_ITERATIONS):
            if hasattr(test_weapon, 'clear_cache'):
                test_weapon.clear_cache()
                
            time_taken, _ = measure_time(
                test_weapon.get_skills_by_type, 
                'weapon', 
                session=db_session
            )
            new_times.append(time_taken)
        
        avg_new = statistics.mean(new_times)
        min_new = min(new_times)
        max_new = max(new_times)
        
        print(f"\n[get_skills_by_type] Nouvelle implémentation:")
        print(f"  - Moyenne: {avg_new:.2f} ms")
        print(f"  - Min: {min_new:.2f} ms")
        print(f"  - Max: {max_new:.2f} ms")
        
        # Vérifie que la performance est raisonnable
        assert avg_new < 50.0  # Moins de 50ms en moyenne
    
    def test_get_profession_weapons_performance(self, test_weapon: Weapon, db_session: Session):
        """Teste les performances de get_profession_weapons()."""
        # Mesure avec la nouvelle implémentation
        new_times = []
        for _ in range(NUM_ITERATIONS):
            if hasattr(test_weapon, 'clear_cache'):
                test_weapon.clear_cache()
                
            time_taken, _ = measure_time(
                test_weapon.get_profession_weapons,
                session=db_session
            )
            new_times.append(time_taken)
        
        avg_new = statistics.mean(new_times)
        
        print(f"\n[get_profession_weapons] Performance:")
        print(f"  - Temps moyen: {avg_new:.2f} ms")
        
        # Vérifie que la performance est raisonnable
        assert avg_new < 50.0  # Moins de 50ms en moyenne
    
    def test_batch_loading_performance(self, db_session: Session):
        """Teste les performances du chargement par lots des armes."""
        # Récupère les IDs des armes
        weapon_ids = [w[0] for w in db_session.query(Weapon.id).limit(10).all()]
        
        if not weapon_ids:
            pytest.skip("Aucune arme trouvée pour tester le chargement par lots")
        
        # Méthode 1: Chargement un par un
        def load_one_by_one():
            weapons = []
            for weapon_id in weapon_ids:
                weapon = db_session.query(Weapon).get(weapon_id)
                if weapon:
                    weapons.append(weapon)
            return weapons
        
        # Méthode 2: Chargement par lots
        def load_batch():
            return db_session.query(Weapon).filter(Weapon.id.in_(weapon_ids)).all()
        
        # Mesure des performances
        one_by_one_times = []
        for _ in range(NUM_ITERATIONS // 5):  # Moins d'itérations car c'est plus lent
            time_taken, _ = measure_time(load_one_by_one)
            one_by_one_times.append(time_taken)
        
        batch_times = []
        for _ in range(NUM_ITERATIONS):
            time_taken, _ = measure_time(load_batch)
            batch_times.append(time_taken)
        
        avg_one_by_one = statistics.mean(one_by_one_times)
        avg_batch = statistics.mean(batch_times)
        
        print(f"\n[Batch Loading] Comparaison des méthodes:")
        print(f"  - Un par un: {avg_one_by_one:.2f} ms")
        print(f"  - Par lots: {avg_batch:.2f} ms")
        print(f"  - Accélération: {avg_one_by_one / avg_batch if avg_batch > 0 else 'inf':.1f}x")
        
        # Vérifie que le chargement par lots est plus rapide
        assert avg_batch < avg_one_by_one * 0.8  # Au moins 20% plus rapide


if __name__ == "__main__":
    # Exécution directe des tests (sans pytest)
    print(f"Début des tests de performance - {datetime.now().isoformat()}")
    
    # Crée une session pour les tests
    session = SessionLocal()
    try:
        tester = TestWeaponPerformance()
        test_weapon = tester.test_weapon.__wrapped__(tester, session)
        
        # Exécute les tests
        tester.test_get_skills_by_type(test_weapon, session)
        tester.test_get_profession_weapons_performance(test_weapon, session)
        tester.test_batch_loading_performance(session)
        
        print("\nTous les tests de performance ont été exécutés avec succès!")
    finally:
        session.close()
