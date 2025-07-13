"""Tests de performance pour le modèle Skill."""

import time
import statistics
from datetime import datetime
from typing import Dict, List, Tuple, Any
import pytest
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.database import SessionLocal

# Nombre d'itérations pour les tests de performance
NUM_ITERATIONS = 100


def measure_time(func, *args, **kwargs) -> Tuple[float, Any]:
    """Mesure le temps d'exécution d'une fonction.
    
    Args:
        func: Fonction à mesurer
        *args: Arguments positionnels à passer à la fonction
        **kwargs: Arguments nommés à passer à la fonction
        
    Returns:
        Tuple[float, Any]: (temps d'exécution en secondes, résultat de la fonction)
    """
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    return (end_time - start_time) * 1000, result  # en millisecondes


class TestSkillPerformance:
    """Classe de tests de performance pour le modèle Skill."""
    
    @pytest.fixture(scope="class")
    def db_session(self) -> Session:
        """Session de base de données pour les tests."""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    @pytest.fixture(scope="class")
    def test_skill(self, db_session: Session) -> Skill:
        """Compétence de test pour les benchmarks."""
        # Récupère une compétence avec des relations
        skill = db_session.query(Skill).filter(
            (Skill.flip_skill.isnot(None)) | 
            (Skill.next_chain.isnot(None)) |
            (Skill.toolbelt_skill.isnot(None))
        ).first()
        
        if not skill:
            pytest.skip("Aucune compétence avec des relations trouvée pour les tests")
        
        return skill
    
    def test_get_related_skills_performance(self, test_skill: Skill, db_session: Session):
        """Teste les performances de get_related_skills()."""
        # Mesure avec la nouvelle implémentation
        new_times = []
        for _ in range(NUM_ITERATIONS):
            test_skill.clear_cache()
            time_taken, _ = measure_time(test_skill.get_related_skills, db_session)
            new_times.append(time_taken)
        
        avg_new = statistics.mean(new_times)
        min_new = min(new_times)
        max_new = max(new_times)
        
        print(f"\n[get_related_skills] Nouvelle implémentation:")
        print(f"  - Moyenne: {avg_new:.2f} ms")
        print(f"  - Min: {min_new:.2f} ms")
        print(f"  - Max: {max_new:.2f} ms")
        
        # Vérifie que la performance est raisonnable
        assert avg_new < 50.0  # Moins de 50ms en moyenne
    
    def test_get_skill_facts_performance(self, test_skill: Skill):
        """Teste les performances de get_skill_facts() avec et sans cache."""
        # Premier appel (sans cache)
        first_call, _ = measure_time(test_skill.get_skill_facts)
        
        # Appels suivants (avec cache)
        cached_times = []
        for _ in range(NUM_ITERATIONS):
            time_taken, _ = measure_time(test_skill.get_skill_facts)
            cached_times.append(time_taken)
        
        avg_cached = statistics.mean(cached_times)
        
        print(f"\n[get_skill_facts] Performance du cache:")
        print(f"  - Premier appel: {first_call:.4f} ms")
        print(f"  - Appels suivants (moyenne): {avg_cached:.4f} ms")
        print(f"  - Accélération: {first_call / avg_cached if avg_cached > 0 else 'inf':.1f}x")
        
        # Vérifie que le cache fonctionne
        assert avg_cached < first_call * 0.1  # Au moins 10x plus rapide avec le cache
    
    def test_batch_loading_performance(self, test_skill: Skill, db_session: Session):
        """Teste les performances du chargement par lots."""
        # Récupère les IDs des compétences liées
        related_ids = []
        if test_skill.transform_skills:
            related_ids.extend(test_skill.transform_skills)
        if test_skill.bundle_skills:
            related_ids.extend(test_skill.bundle_skills)
        
        if not related_ids:
            pytest.skip("Aucune compétence liée pour tester le chargement par lots")
        
        # Méthode 1: Chargement un par un (ancienne méthode)
        def load_one_by_one():
            skills = []
            for skill_id in related_ids:
                skill = db_session.query(Skill).filter(Skill.id == skill_id).first()
                if skill:
                    skills.append(skill)
            return skills
        
        # Méthode 2: Chargement par lots (nouvelle méthode)
        def load_batch():
            return db_session.query(Skill).filter(Skill.id.in_(related_ids)).all()
        
        # Mesure des performances
        one_by_one_times = []
        for _ in range(NUM_ITERATIONS // 10):  # Moins d'itérations car c'est plus lent
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
        tester = TestSkillPerformance()
        test_skill = tester.test_skill.__wrapped__(tester, session)
        
        # Exécute les tests
        tester.test_get_related_skills_performance(test_skill, session)
        tester.test_get_skill_facts_performance(test_skill)
        tester.test_batch_loading_performance(test_skill, session)
        
        print("\nTous les tests de performance ont été exécutés avec succès!")
    finally:
        session.close()
