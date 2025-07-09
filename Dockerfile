# Étape de construction
FROM python:3.11-slim as builder

# Définir les variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.2

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installer Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY pyproject.toml poetry.lock* ./

# Installer les dépendances Python
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copier le reste du code source
COPY . .

# Installer l'application en mode développement
RUN poetry install --no-interaction --no-ansi

# Étape d'exécution finale
FROM python:3.11-slim

# Définir les variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH"

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Créer un utilisateur non-root
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Copier l'environnement virtuel depuis le builder
COPY --from=builder /usr/local /usr/local

# Copier les fichiers de l'application
COPY --from=builder /app /app

# Définir le répertoire de travail
WORKDIR /app

# Exposer le port utilisé par FastAPI
EXPOSE 8000

# Commande par défaut pour exécuter l'application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
