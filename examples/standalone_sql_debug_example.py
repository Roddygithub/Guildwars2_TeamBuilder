"""Exemple autonome d'utilisation de SQLAlchemy avec débogage.

Ce script montre comment utiliser les fonctionnalités de débogage et d'analyse
des performances des requêtes SQLAlchemy sans dépendre d'autres modules du projet.
"""

import logging
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Any

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, select, event, func
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=None  # Utilise stderr par défaut
)
logger = logging.getLogger('sqlalchemy_debug')

# Création des modèles
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), index=True)
    email = Column(String(120), unique=True, index=True)
    posts = relationship("Post", back_populates="author", lazy="selectin")

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), index=True)
    content = Column(String(5000))
    author_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(String(50), default=lambda: datetime.utcnow().isoformat())
    
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", lazy="selectin")

class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    content = Column(String(1000))
    post_id = Column(Integer, ForeignKey('posts.id'))
    author_name = Column(String(100))
    created_at = Column(String(50), default=lambda: datetime.utcnow().isoformat())
    
    post = relationship("Post", back_populates="comments")

# Outils de débogage
@contextmanager
def sql_profiler(session: Session):
    """Contexte pour le profilage des requêtes SQL."""
    queries: List[Dict[str, Any]] = []
    
    def before_cursor_execute(conn, cursor, statement, params, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())
    
    def after_cursor_execute(conn, cursor, statement, params, context, executemany):
        total = time.time() - conn.info['query_start_time'].pop(-1)
        queries.append({
            'statement': statement,
            'parameters': params,
            'duration': total,
            'context': str(context.statement) if context else None,
            'timestamp': time.time()
        })
    
    # Enregistre les écouteurs d'événements
    event.listen(session.bind, 'before_cursor_execute', before_cursor_execute)
    event.listen(session.bind, 'after_cursor_execute', after_cursor_execute)
    
    try:
        yield queries
    finally:
        # Nettoie les écouteurs d'événements
        event.remove(session.bind, 'before_cursor_execute', before_cursor_execute)
        event.remove(session.bind, 'after_cursor_execute', after_cursor_execute)

def log_sql_statements(engine, level=logging.INFO):
    """Active le logging des requêtes SQL."""
    logging.getLogger('sqlalchemy.engine').setLevel(level)

def print_queries(queries):
    """Affiche un résumé des requêtes exécutées."""
    if not queries:
        print("Aucune requête exécutée.")
        return
    
    total_time = sum(q['duration'] for q in queries)
    avg_time = total_time / len(queries)
    
    print(f"\n=== Résumé des requêtes ===")
    print(f"Nombre total de requêtes : {len(queries)}")
    print(f"Temps total d'exécution : {total_time:.4f} secondes")
    print(f"Temps moyen par requête : {avg_time*1000:.2f} ms")
    
    print("\nDétail des requêtes les plus longues :")
    for i, q in enumerate(sorted(queries, key=lambda x: x['duration'], reverse=True)[:5], 1):
        print(f"{i}. {q['duration']:.4f}s - {q['statement'][:100]}...")

def setup_database():
    """Configure et initialise la base de données de test."""
    # Crée une base de données SQLite en mémoire
    engine = create_engine('sqlite:///:memory:', echo=False)
    
    # Crée toutes les tables
    Base.metadata.create_all(engine)
    
    # Ajoute des données de test
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Crée des utilisateurs
    users = [
        User(name=f"User {i}", email=f"user{i}@example.com") 
        for i in range(1, 6)
    ]
    
    # Crée des posts
    posts = []
    for i, user in enumerate(users, 1):
        for j in range(1, 4):  # 3 posts par utilisateur
            post = Post(
                title=f"Post {i}.{j} par {user.name}",
                content=f"Contenu du post {i}.{j}...",
                author=user
            )
            posts.append(post)
    
    # Crée des commentaires
    for i, post in enumerate(posts, 1):
        for j in range(1, 4):  # 3 commentaires par post
            comment = Comment(
                content=f"Commentaire {j} sur le post {post.title[:20]}...",
                author_name=f"Commentateur {j}",
                post=post
            )
    
    # Valide les changements
    session.commit()
    
    return engine

def example_n_plus_one_problem():
    """Démontre et corrige le problème N+1."""
    print("\n=== Exemple: Problème N+1 ===\n")
    
    # Configuration de la base de données
    engine = setup_database()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 1. Approche problématique (N+1)
    print("1. Approche problématique (N+1):")
    with sql_profiler(session) as profiler:
        # Récupère tous les utilisateurs
        users = session.execute(select(User)).scalars().all()
        
        # Pour chaque utilisateur, accède à ses posts (provoque N requêtes supplémentaires)
        for user in users[:3]:  # Limité à 3 pour l'exemple
            print(f"\nUtilisateur: {user.name}")
            for post in user.posts:
                print(f"- {post.title}")
                for comment in post.comments:
                    print(f"  - {comment.author_name}: {comment.content[:30]}...")
    
    print("\nRapport de performance (approche problématique):")
    print_queries(profiler)
    
    # 2. Approche optimisée
    print("\n2. Approche optimisée (avec selectinload):")
    from sqlalchemy.orm import selectinload
    
    with sql_profiler(session) as profiler:
        # Charge tout en une seule requête avec des sous-requêtes
        users = session.execute(
            select(User)
            .options(
                selectinload(User.posts)
                .selectinload(Post.comments)
            )
            .limit(3)  # Limité à 3 pour l'exemple
        ).scalars().all()
        
        # Accès aux données déjà chargées (pas de requêtes supplémentaires)
        for user in users:
            print(f"\nUtilisateur: {user.name}")
            for post in user.posts:
                print(f"- {post.title}")
                for comment in post.comments:
                    print(f"  - {comment.author_name}: {comment.content[:30]}...")
    
    print("\nRapport de performance (approche optimisée):")
    print_queries(profiler)

def example_complex_queries():
    """Montre des exemples de requêtes complexes."""
    print("\n=== Exemple: Requêtes complexes ===\n")
    
    # Configuration de la base de données
    engine = setup_database()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 1. Requête avec agrégation
    print("1. Nombre de posts par utilisateur:")
    with sql_profiler(session) as profiler:
        result = session.execute(
            select(
                User.name,
                func.count(Post.id).label('post_count')
            )
            .join(Post, User.posts)
            .group_by(User.id)
            .order_by(func.count(Post.id).desc())
        ).all()
        
        for name, count in result:
            print(f"- {name}: {count} posts")
    
    print("\n2. Derniers commentaires par post:")
    with sql_profiler(session) as profiler:
        # Sous-requête pour obtenir le dernier commentaire par post
        subq = (
            select(
                Comment.post_id,
                func.max(Comment.created_at).label('max_date')
            )
            .group_by(Comment.post_id)
            .subquery()
        )
        
        # Requête principale
        result = session.execute(
            select(
                Post.title,
                Comment.content,
                Comment.author_name,
                Comment.created_at
            )
            .join(Comment, Post.comments)
            .join(
                subq,
                (Comment.post_id == subq.c.post_id) & 
                (Comment.created_at == subq.c.max_date)
            )
            .order_by(Post.title)
        ).all()
        
        for title, content, author, created_at in result[:5]:  # Limité à 5 pour l'exemple
            print(f"\nPost: {title[:50]}...")
            print(f"Dernier commentaire par {author} le {created_at}:")
            print(f"  {content[:70]}...")
    
    print("\n3. Utilisateurs les plus actifs (avec nombre de commentaires):")
    with sql_profiler(session) as profiler:
        result = session.execute(
            select(
                User.name,
                func.count(Comment.id).label('comment_count')
            )
            .select_from(User)
            .join(Post, User.posts)
            .join(Comment, Post.comments)
            .group_by(User.id)
            .order_by(func.count(Comment.id).desc())
            .limit(5)
        ).all()
        
        for name, count in result:
            print(f"- {name}: {count} commentaires")

def main():
    """Fonction principale."""
    print("=== Exemple de débogage SQLAlchemy ===\n")
    
    # Active le logging SQL
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    
    # Exécute les exemples
    example_n_plus_one_problem()
    example_complex_queries()
    
    print("\n=== Fin des exemples ===")

if __name__ == "__main__":
    main()
