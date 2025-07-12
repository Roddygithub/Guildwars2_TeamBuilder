"""Utilitaires de débogage pour SQLAlchemy.

Ce module fournit des outils pour surveiller et déboguer les requêtes SQLAlchemy,
y compris le suivi des performances, le logging des requêtes et l'analyse des relations.
"""

import time
import logging
from contextlib import contextmanager
from typing import Optional, Dict, List, Any, Callable
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, class_mapper, RelationshipProperty
from sqlalchemy import event, inspect

# Configuration du logger
logger = logging.getLogger('sqlalchemy_debug')

class QueryAnalyzer:
    """Analyseur de requêtes SQLAlchemy."""
    
    def __init__(self, session: Session):
        """Initialise l'analyseur avec une session SQLAlchemy."""
        self.session = session
        self.queries: List[Dict[str, Any]] = []
        self._enabled = False
    
    def start(self) -> None:
        """Active la surveillance des requêtes."""
        if self._enabled:
            return
            
        @event.listens_for(self.session.bind, 'before_cursor_execute')
        def before_cursor_execute(conn, cursor, statement, params, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
            
        @event.listens_for(self.session.bind, 'after_cursor_execute')
        def after_cursor_execute(conn, cursor, statement, params, context, executemany):
            total = time.time() - conn.info['query_start_time'].pop(-1)
            self.queries.append({
                'statement': statement,
                'parameters': params,
                'duration': total,
                'context': str(context.statement) if context else None,
                'timestamp': time.time()
            })
        
        self._enabled = True
        logger.info("Surveillance des requêtes SQL activée")
    
    def stop(self) -> None:
        """Désactive la surveillance des requêtes."""
        if not self._enabled:
            return
            
        event.remove(self.session.bind, 'before_cursor_execute', None)
        event.remove(self.session.bind, 'after_cursor_execute', None)
        self._enabled = False
        logger.info("Surveillance des requêtes SQL désactivée")
    
    def get_slow_queries(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """Retourne les requêtes plus lentes que le seuil donné (en secondes)."""
        return [q for q in self.queries if q['duration'] > threshold]
    
    def get_duplicate_queries(self) -> Dict[str, List[Dict[str, Any]]]:
        """Identifie les requêtes en double."""
        duplicates = {}
        for query in self.queries:
            stmt = query['statement'].strip()
            if stmt not in duplicates:
                duplicates[stmt] = []
            duplicates[stmt].append(query)
        
        return {k: v for k, v in duplicates.items() if len(v) > 1}
    
    def generate_report(self) -> str:
        """Génère un rapport d'analyse des requêtes."""
        if not self.queries:
            return "Aucune requête enregistrée."
        
        total_queries = len(self.queries)
        total_time = sum(q['duration'] for q in self.queries)
        avg_time = total_time / total_queries if total_queries > 0 else 0
        
        slow_queries = self.get_slow_queries()
        duplicates = self.get_duplicate_queries()
        
        report = [
            "=== Rapport d'analyse des requêtes SQL ===",
            f"Période d'analyse: {time.ctime(self.queries[0]['timestamp'])} - {time.ctime(self.queries[-1]['timestamp'])}",
            f"Total des requêtes: {total_queries}",
            f"Temps total d'exécution: {total_time:.4f} secondes",
            f"Temps moyen par requête: {avg_time*1000:.2f} ms",
            f"Requêtes lentes (>1s): {len(slow_queries)}",
            f"Requêtes en double: {sum(len(v) for v in duplicates.values())}",
            ""
        ]
        
        if slow_queries:
            report.append("=== REQUÊTES LENTES ===")
            for i, query in enumerate(sorted(slow_queries, key=lambda x: x['duration'], reverse=True)[:5], 1):
                report.append(f"{i}. {query['duration']:.3f}s - {query['statement'][:100]}...")
        
        if duplicates:
            report.append("\n=== REQUÊTES EN DOUBLE ===")
            for i, (stmt, queries) in enumerate(duplicates.items(), 1):
                report.append(f"{i}. {len(queries)} occurrences de la même requête")
                report.append(f"   Exemple: {stmt[:200]}...")
        
        return "\n".join(report)

@contextmanager
def sql_profiler(session: Session):
    """Contexte pour le profilage des requêtes SQL.
    
    Exemple d'utilisation:
        with sql_profiler(session) as profiler:
            # Votre code avec des requêtes SQL
            result = session.query(User).all()
        
        # Afficher le rapport
        print(profiler.generate_report())
    """
    analyzer = QueryAnalyzer(session)
    analyzer.start()
    try:
        yield analyzer
    finally:
        analyzer.stop()

def log_sql_statements(engine: Engine, level: int = logging.INFO) -> None:
    """Active le logging des requêtes SQL.
    
    Args:
        engine: Moteur SQLAlchemy
        level: Niveau de log (par défaut: logging.INFO)
    """
    logging.basicConfig()
    logger = logging.getLogger('sqlalchemy.engine')
    logger.setLevel(level)
    
    if level <= logging.DEBUG:
        # Niveau DEBUG: affiche les requêtes et les résultats
        logging.getLogger('sqlalchemy').setLevel(logging.DEBUG)
    else:
        # Niveau INFO: affiche uniquement les requêtes
        logging.getLogger('sqlalchemy').setLevel(logging.INFO)

def get_relationships(model_class: type) -> Dict[str, RelationshipProperty]:
    """Retourne les relations d'un modèle SQLAlchemy.
    
    Args:
        model_class: Classe du modèle SQLAlchemy
        
    Returns:
        Dictionnaire des relations {nom: propriété}
    """
    mapper = class_mapper(model_class)
    return {
        prop.key: prop 
        for prop in mapper.iterate_properties 
        if isinstance(prop, RelationshipProperty)
    }

def print_model_relationships(model_class: type) -> None:
    """Affiche les relations d'un modèle SQLAlchemy."""
    print(f"\nRelations pour {model_class.__name__}:")
    print("-" * 50)
    
    for name, prop in get_relationships(model_class).items():
        print(f"{name}: {prop}")
    
    print("" * 50)

def explain_query(query, session: Optional[Session] = None) -> str:
    """Génère et retourne le plan d'exécution d'une requête."""
    if session is None:
        session = query.session
    
    # Crée une requête EXPLAIN
    explain_sql = str(
        query.statement.compile(
            dialect=session.bind.dialect,
            compile_kwargs={"literal_binds": True}
        )
    )
    
    # Exécute la requête EXPLAIN
    if 'postgresql' in str(session.bind.dialect):
        explain_sql = f"EXPLAIN ANALYZE {explain_sql}"
    elif 'sqlite' in str(session.bind.dialect):
        explain_sql = f"EXPLAIN QUERY PLAN {explain_sql}"
    else:
        explain_sql = f"EXPLAIN {explain_sql}"
    
    result = session.execute(explain_sql)
    return "\n".join(" | ".join(str(col) for col in row) for row in result)

# Exemple d'utilisation
if __name__ == "__main__":
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    # Configuration de base
    engine = create_engine('sqlite:///:memory:')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Exemple d'utilisation du profileur
    with sql_profiler(session) as profiler:
        # Exécutez vos requêtes ici
        session.execute(text("SELECT 1"))
    
    # Affiche le rapport
    print(profiler.generate_report())
    
    # Affiche les relations d'un modèle
    # print_model_relationships(YourModel)
