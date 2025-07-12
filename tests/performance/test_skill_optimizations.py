"""Script de benchmark pour mesurer l'impact des optimisations sur le modèle Skill."""

import time
import statistics
from functools import partial
from typing import Callable, Dict, Any, List, Tuple
import cProfile
import pstats
import io
import os
import sys
from pathlib import Path

# Ajout du répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.models.skill import Skill
from app.database import SessionLocal

def time_it(func: Callable, *args, **kwargs) -> Tuple[float, Any]:
    """Exécute une fonction et retourne le temps d'exécution et le résultat."""
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    return (end_time - start_time) * 1000, result  # en millisecondes

def profile_function(func: Callable, *args, **kwargs) -> str:
    """Profile une fonction et retourne les statistiques."""
    pr = cProfile.Profile()
    pr.enable()
    result = func(*args, **kwargs)
    pr.disable()
    
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats()
    return s.getvalue()

class SkillBenchmark:
    """Classe pour exécuter des benchmarks sur le modèle Skill."""
    
    def __init__(self, session: Session):
        self.session = session
        self.sample_size = 10  # Nombre d'itérations pour les tests
        
    def _get_sample_skills(self, count: int = 10) -> List[Skill]:
        """Récupère un échantillon de compétences pour les tests."""
        return self.session.query(Skill).limit(count).all()
    
    def benchmark_to_dict(self) -> Dict[str, Any]:
        """Benchmark de la méthode to_dict."""
        skills = self._get_sample_skills()
        times = []
        
        # Test avec include_related=True
        for skill in skills:
            if hasattr(skill.to_dict, 'cache_clear'):
                skill.to_dict.cache_clear()
                
            time_taken, _ = time_it(skill.to_dict, include_related=True)
            times.append(time_taken)
            
        # Test avec include_related=False
        times_no_related = []
        for skill in skills:
            if hasattr(skill.to_dict, 'cache_clear'):
                skill.to_dict.cache_clear()
                
            time_taken, _ = time_it(skill.to_dict, include_related=False)
            times_no_related.append(time_taken)
        
        return {
            'to_dict_with_related': {
                'min': min(times),
                'max': max(times),
                'avg': statistics.mean(times),
                'median': statistics.median(times),
                'stdev': statistics.stdev(times) if len(times) > 1 else 0,
                'unit': 'ms'
            },
            'to_dict_without_related': {
                'min': min(times_no_related),
                'max': max(times_no_related),
                'avg': statistics.mean(times_no_related),
                'median': statistics.median(times_no_related),
                'stdev': statistics.stdev(times_no_related) if len(times_no_related) > 1 else 0,
                'unit': 'ms'
            }
        }
    
    def benchmark_related_skills(self) -> Dict[str, Any]:
        """Benchmark de la méthode get_related_skills."""
        skills = self._get_sample_skills()
        times = []
        
        for skill in skills:
            # Vider le cache avant chaque test
            if hasattr(skill.get_related_skills, 'cache_clear'):
                skill.get_related_skills.cache_clear()
                
            time_taken, _ = time_it(skill.get_related_skills)
            times.append(time_taken)
        
        # Test avec cache (deuxième appel)
        cached_times = []
        for skill in skills:
            time_taken, _ = time_it(skill.get_related_skills)
            cached_times.append(time_taken)
        
        return {
            'get_related_skills': {
                'first_call': {
                    'min': min(times),
                    'max': max(times),
                    'avg': statistics.mean(times),
                    'median': statistics.median(times),
                    'stdev': statistics.stdev(times) if len(times) > 1 else 0,
                    'unit': 'ms'
                },
                'cached_call': {
                    'min': min(cached_times),
                    'max': max(cached_times),
                    'avg': statistics.mean(cached_times),
                    'median': statistics.median(cached_times),
                    'stdev': statistics.stdev(cached_times) if len(cached_times) > 1 else 0,
                    'unit': 'ms'
                }
            }
        }
    
    def benchmark_transform_skills(self) -> Dict[str, Any]:
        """Benchmark de la méthode get_transform_skills."""
        skills = self._get_sample_skills()
        times = []
        
        for skill in skills:
            if hasattr(skill.get_transform_skills, 'cache_clear'):
                skill.get_transform_skills.cache_clear()
                
            time_taken, _ = time_it(skill.get_transform_skills)
            times.append(time_taken)
        
        return {
            'get_transform_skills': {
                'min': min(times) if times else 0,
                'max': max(times) if times else 0,
                'avg': statistics.mean(times) if times else 0,
                'median': statistics.median(times) if times else 0,
                'stdev': statistics.stdev(times) if len(times) > 1 else 0,
                'unit': 'ms'
            }
        }
    
    def benchmark_bundle_skills(self) -> Dict[str, Any]:
        """Benchmark de la méthode get_bundle_skills."""
        skills = self._get_sample_skills()
        times = []
        
        for skill in skills:
            if hasattr(skill.get_bundle_skills, 'cache_clear'):
                skill.get_bundle_skills.cache_clear()
                
            time_taken, _ = time_it(skill.get_bundle_skills)
            times.append(time_taken)
        
        return {
            'get_bundle_skills': {
                'min': min(times) if times else 0,
                'max': max(times) if times else 0,
                'avg': statistics.mean(times) if times else 0,
                'median': statistics.median(times) if times else 0,
                'stdev': statistics.stdev(times) if len(times) > 1 else 0,
                'unit': 'ms'
            }
        }
    
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Exécute tous les benchmarks et retourne les résultats."""
        print("Démarrage des benchmarks...\n")
        
        results = {}
        
        # Benchmark to_dict
        print("Benchmark de to_dict...")
        results.update(self.benchmark_to_dict())
        
        # Benchmark get_related_skills
        print("Benchmark de get_related_skills...")
        results.update(self.benchmark_related_skills())
        
        # Benchmark get_transform_skills
        print("Benchmark de get_transform_skills...")
        results.update(self.benchmark_transform_skills())
        
        # Benchmark get_bundle_skills
        print("Benchmark de get_bundle_skills...")
        results.update(self.benchmark_bundle_skills())
        
        print("\nBenchmarks terminés.")
        return results

def print_benchmark_results(results: Dict[str, Any], indent: int = 0) -> None:
    """Affiche les résultats des benchmarks de manière lisible."""
    indent_str = ' ' * indent
    
    for key, value in results.items():
        if isinstance(value, dict):
            if 'min' in value and 'max' in value and 'avg' in value:
                # C'est une métrique de temps
                print(f"{indent_str}{key}:")
                print(f"{indent_str}  Min: {value['min']:.4f} {value.get('unit', 'ms')}")
                print(f"{indent_str}  Max: {value['max']:.4f} {value.get('unit', 'ms')}")
                print(f"{indent_str}  Moyenne: {value['avg']:.4f} {value.get('unit', 'ms')}")
                print(f"{indent_str}  Médiane: {value['median']:.4f} {value.get('unit', 'ms')}")
                print(f"{indent_str}  Écart-type: {value['stdev']:.4f} {value.get('unit', 'ms')}")
            else:
                # C'est un dictionnaire imbriqué
                print(f"{indent_str}{key}:")
                print_benchmark_results(value, indent + 2)
        else:
            print(f"{indent_str}{key}: {value}")

if __name__ == "__main__":
    print("=== Benchmark des optimisations du modèle Skill ===\n")
    
    # Création d'une session de base de données
    db = SessionLocal()
    
    try:
        # Création du benchmark
        benchmark = SkillBenchmark(db)
        
        # Exécution des benchmarks
        results = benchmark.run_all_benchmarks()
        
        # Affichage des résultats
        print("\n=== Résultats des benchmarks ===\n")
        print_benchmark_results(results)
        
        # Profilage d'une méthode spécifique
        print("\n=== Profilage de get_related_skills ===\n")
        sample_skill = benchmark._get_sample_skills(1)[0]
        if hasattr(sample_skill.get_related_skills, 'cache_clear'):
            sample_skill.get_related_skills.cache_clear()
        
        profile_output = profile_function(sample_skill.get_related_skills)
        print(profile_output)
        
    finally:
        # Nettoyage
        db.close()
        print("\n=== Benchmark terminé ===")
