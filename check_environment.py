"""Script pour vérifier l'environnement Python et les dépendances."""
import sys
import platform
import subprocess
from pathlib import Path

def check_python_version():
    """Vérifie la version de Python."""
    print("=== Vérification de la version de Python ===")
    print(f"Version de Python: {sys.version}")
    print(f"Exécutable Python: {sys.executable}")
    print(f"Chemin Python: {sys.path}\n")
    
    # Vérifier la version minimale requise (Python 3.7+)
    if sys.version_info < (3, 7):
        print("ERREUR: Python 3.7 ou supérieur est requis.")
        return False
    return True

def check_package(package_name):
    """Vérifie si un package est installé et retourne sa version."""
    try:
        if package_name == 'sqlite3':
            # sqlite3 est inclus dans la bibliothèque standard
            import sqlite3
            version = sqlite3.sqlite_version
        else:
            # Pour les packages installés avec pip
            module = __import__(package_name)
            version = getattr(module, '__version__', 'version non disponible')
        print(f"✅ {package_name}: {version}")
        return True
    except ImportError:
        print(f"❌ {package_name}: non installé")
        return False

def check_sqlite_version():
    """Vérifie la version de SQLite."""
    print("\n=== Vérification de SQLite ===")
    try:
        import sqlite3
        print(f"Version de SQLite: {sqlite3.sqlite_version}")
        print(f"Version du module sqlite3: {sqlite3.version}")
        
        # Vérifier la version minimale requise (3.25.0+ pour certaines fonctionnalités)
        version_parts = tuple(map(int, sqlite3.sqlite_version.split('.')))
        if version_parts < (3, 25, 0):
            print("ATTENTION: Une version plus récente de SQLite est recommandée (3.25.0+).")
            return False
        return True
    except Exception as e:
        print(f"Erreur lors de la vérification de SQLite: {e}")
        return False

def main():
    """Fonction principale."""
    print("=== Vérification de l'environnement Python ===\n")
    
    # Vérifier la version de Python
    if not check_python_version():
        return
    
    # Vérifier les packages requis
    print("\n=== Vérification des packages requis ===")
    required_packages = [
        'sqlalchemy',
        'pydantic',
        'fastapi',
        'uvicorn',
        'python-dotenv',
        'pytest',
        'pytest-cov',
        'httpx',
        'aiohttp',
        'requests',
        'numpy',
        'pandas',
        'loguru',
        'typing-extensions',
        'pydantic-settings',
        'python-dateutil',
        'pytz',
        'tzlocal',
        'pyyaml',
        'toml',
        'iniconfig',
        'filelock',
        'packaging',
        'platformdirs'
    ]
    
    # Vérifier chaque package
    for package in required_packages:
        check_package(package)
    
    # Vérifier la version de SQLite
    check_sqlite_version()
    
    print("\n=== Vérification terminée ===")

if __name__ == "__main__":
    main()
