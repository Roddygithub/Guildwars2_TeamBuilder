import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Ajouter le répertoire racine au path Python
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Importer les modèles de l'application
from app.models import Base
from app.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Utiliser l'URL de la base de données depuis les paramètres de l'application
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Utiliser les métadonnées de notre modèle SQLAlchemy
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Exécute les migrations en mode 'hors-ligne'.
    
    Configure le contexte avec uniquement une URL et non un moteur.
    Utile pour générer des scripts SQL sans connexion à la base de données.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=True,  # Important pour SQLite
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Exécute les migrations en mode 'en ligne'.
    
    Crée un moteur de base de données et associe une connexion au contexte.
    """
    # Utiliser l'URL de la base de données depuis les paramètres
    configuration = config.get_section(config.config_ini_section, {})
    configuration['sqlalchemy.url'] = settings.DATABASE_URL
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,  # Important pour SQLite
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
