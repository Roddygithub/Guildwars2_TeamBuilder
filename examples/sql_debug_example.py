"""Exemple d'utilisation de l'utilitaire de débogage SQLAlchemy.

Ce script montre comment utiliser les fonctionnalités de débogage et d'analyse
des performances des requêtes SQLAlchemy.
"""

import logging
from sqlalchemy import create_engine, select, Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

# Configuration des modèles pour l'exemple
Base = declarative_base()

# Modèles simplifiés pour l'exemple
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    posts = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(String)
    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")

class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    content = Column(String)
    post_id = Column(Integer, ForeignKey('posts.id'))
    post = relationship("Post", back_populates="comments")

# Ajout du répertoire parent au chemin de recherche Python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import de l'utilitaire de débogage
from app.utils.sql_debug import (
    sql_profiler,
    log_sql_statements,
    explain_query,
    print_model_relationships
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def setup_database():
    """Configure la base de données de test."""
    # Crée une base de données SQLite en mémoire
    engine = create_engine('sqlite:///:memory:', echo=True)
    
    # Crée toutes les tables
    Base.metadata.create_all(engine)
    
    # Ajoute des données de test
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Crée un utilisateur avec des posts et des commentaires
    user = User(name="Test User")
    post1 = Post(title="Premier post", content="Contenu du premier post", author=user)
    post2 = Post(title="Deuxième post", content="Contenu du deuxième post", author=user)
    
    post1.comments = [
        Comment(content="Commentaire 1 sur le premier post"),
        Comment(content="Commentaire 2 sur le premier post")
    ]
    
    session.add_all([user, post1, post2])
    session.commit()
    
    return engine

def example_basic_usage():
    """Exemple d'utilisation basique du profileur SQL."""
    print("=== Exemple d'utilisation basique du profileur SQL ===\n")
    
    # Configuration de la base de données
    engine = setup_database()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Active le logging des requêtes SQL
    log_sql_statements(engine, level=logging.INFO)
    
    # Utilisation du profileur
    with sql_profiler(session) as profiler:
        # Exécution de quelques requêtes
        users = session.execute(
            select(User)
            .where(User.name.like("%Test%"))
            .limit(2)
        ).scalars().all()
        
        # Accès aux relations (déclenche des requêtes supplémentaires)
        for user in users:
            print(f"\nUtilisateur: {user.name}")
            for post in user.posts:
                print(f"- Post: {post.title}")
                for comment in post.comments:
                    print(f"  - Commentaire: {comment.content}")
    
    # Affichage du rapport
    print("\nRapport d'analyse des requêtes :")
    print("-" * 50)
    print(profiler.generate_report())
    print("\n")

def example_advanced_analysis():
    """Exemple d'analyse avancée des requêtes."""
    print("=== Exemple d'analyse avancée des requêtes ===\n")
    
    # Configuration de la base de données
    engine = setup_database()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 1. Afficher les relations d'un modèle
    print("1. Relations du modèle User :")
    print_model_relationships(User)
    
    # 2. Explication d'une requête
    print("\n2. Plan d'exécution d'une requête :")
    query = select(User).join(Post).where(Post.title.like("%premier%"))
    explanation = explain_query(query, session)
    print("Plan d'exécution :\n", explanation)
    
    # 3. Analyse des performances avec des données plus complexes
    print("\n3. Analyse des performances :")
    with sql_profiler(session) as profiler:
        # Requête complexe avec jointure
        result = session.execute(
            select(User, Post, Comment)
            .join(Post, User.posts)
            .join(Comment, Post.comments)
            .where(Post.title.like("%post%"))
            .limit(10)
        ).all()
        
        # Accès aux données pour forcer le chargement
        for user, post, comment in result:
            _ = f"{user.name} - {post.title} - {comment.content}"
    
    print("\nRapport de performance :")
    print("-" * 50)
    print(profiler.generate_report())

def example_identify_issues():
    """Exemple d'identification de problèmes courants."""
    print("=== Exemple d'identification de problèmes courants ===\n")
    
    # Configuration de la base de données
    engine = setup_database()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 1. Détection du problème N+1
    print("1. Détection du problème N+1 :")
    with sql_profiler(session) as profiler:
        # Mauvaise approche : provoque le problème N+1
        users = session.execute(
            select(User)
            .where(User.name.like("%Test%"))
            .limit(2)
        ).scalars().all()
        
        # Accès aux relations dans une boucle (problème N+1)
        for user in users:
            for post in user.posts:  # Requête supplémentaire pour chaque utilisateur
                _ = post.comments   # Requête supplémentaire pour chaque post
    
    print("\nRapport avec problème N+1 :")
    print("-" * 50)
    print(f"Nombre total de requêtes : {len(profiler.queries)}")
    
    # 2. Solution optimisée
    print("\n2. Solution optimisée avec selectinload :")
    from sqlalchemy.orm import selectinload, joinedload
    
    with sql_profiler(session) as profiler:
        # Bonne approche : utilise selectinload pour les collections
        users = session.execute(
            select(User)
            .options(
                selectinload(User.posts)
                .selectinload(Post.comments)
            )
            .where(User.name.like("%Test%"))
            .limit(2)
        ).scalars().all()
        
        # Les relations sont déjà chargées
        for user in users:
            for post in user.posts:  # Pas de requête supplémentaire
                _ = post.comments    # Pas de requête supplémentaire
    
    print("\nRapport avec optimisation :")
    print("-" * 50)
    print(f"Nombre total de requêtes : {len(profiler.queries)}")
    print("\nNote: Le nombre de requêtes devrait être réduit grâce à l'utilisation de selectinload.")

if __name__ == "__main__":
    print("Démarrage des exemples de débogage SQLAlchemy\n")
    
    # Exécute les exemples
    try:
        print("=== Exemple 1 : Utilisation basique ===\n")
        example_basic_usage()
        
        input("\nAppuyez sur Entrée pour continuer vers l'exemple 2...")
        print("\n=== Exemple 2 : Analyse avancée ===\n")
        example_advanced_analysis()
        
        input("\nAppuyez sur Entrée pour continuer vers l'exemple 3...")
        print("\n=== Exemple 3 : Détection de problèmes ===\n")
        example_identify_issues()
        
    except Exception as e:
        print(f"\nErreur lors de l'exécution des exemples : {e}")
    
    print("\nFin des exemples de débogage SQLAlchemy")
