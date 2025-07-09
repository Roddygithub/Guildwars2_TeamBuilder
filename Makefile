.PHONY: help install test lint format clean build run stop migrate

# Affiche l'aide
default: help

help: ## Affiche cette aide
	@echo 'Commandes disponibles :'
	@echo ''
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\$$//' | sed -e 's/##//' | column -t -s ':'

# Installation
install: ## Installe les dépendances
	pip install -r requirements.txt

# Développement
dev: ## Lance le serveur de développement
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-docker: ## Lance le serveur de développement avec Docker Compose
	docker-compose up --build

# Tests
test: ## Exécute les tests
	pytest

# Linting
lint: ## Vérifie le style du code
	black --check .
	isort --check-only .
	mypy .
	pylint app tests

format: ## Formate le code automatiquement
	black .
	isort .

# Nettoyage
clean: ## Nettoie les fichiers temporaires
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.py[co]" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +

# Docker
docker-build: ## Construit l'image Docker
	docker build -t gw2-teambuilder .

docker-run: ## Exécute le conteneur Docker
	docker run -p 8000:8000 gw2-teambuilder

# Déploiement
deploy: ## Déploie l'application (à personnaliser)
	echo "Déploiement en cours..."

# Base de données
db-migrate: ## Exécute les migrations de la base de données
	alembic upgrade head

db-shell: ## Ouvre un shell psql vers la base de données
	docker-compose exec db psql -U postgres -d gw2_teambuilder

# Mise à jour des données
update-data: ## Met à jour les données depuis l'API GW2
	python -m app.tasks.update_data

# Documentation
docs: ## Génère la documentation
	mkdocs build

docs-serve: ## Lance le serveur de documentation en local
	mkdocs serve
