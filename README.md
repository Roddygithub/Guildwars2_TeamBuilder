# Guild Wars 2 WvW Team Builder

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Netlify Status](https://api.netlify.com/api/v1/badges/
YOUR_NETLIFY_SITE_ID/deploy-status)]
(https://app.netlify.com/sites/YOUR_NETLIFY_SITE_NAME/deploys)
[![GitHub stars](https://img.shields.io/github/stars/Roddygithub/Guildwars2_TeamBuilder?style=social)](https://github.com/Roddygithub/Guildwars2_TeamBuilder/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/Roddygithub/Guildwars2_TeamBuilder)](https://github.com/Roddygithub/Guildwars2_TeamBuilder/issues)

Un outil avancé pour optimiser les compositions d'équipe dans Guild Wars 2, spécialement conçu pour le mode Monde contre Monde (WvW).

## 🚀 Fonctionnalités

- 🎯 **Génération intelligente de builds** basée sur des algorithmes d'optimisation avancés
- 🤖 **Algorithme génétique** pour trouver les meilleures combinaisons de builds
- 🤝 **Synergies automatiques** entre les membres de l'équipe
- 🎮 **Support multi-mode** : Zerg, Havoc, Roaming, GvG
- 📊 **Analyse détaillée** des forces et faiblesses des compositions
- 🔄 **Intégration** avec l'API officielle de Guild Wars 2
- 🌐 **Application web complète** avec interface utilisateur moderne
- 🚀 **Déploiement facile** avec Netlify

## 🛠 Prérequis

### Pour le développement local

- Python 3.9 ou supérieur
- Node.js 18+ et npm 9+
- Compte API Guild Wars 2 (optionnel, pour les fonctionnalités avancées)

### Pour le déploiement

- Compte Netlify (gratuit)

## 🚀 Démarrage rapide

### 📚 Documentation complète

Pour une documentation complète sur le déploiement et la configuration, consultez les ressources suivantes :

- [Guide de déploiement Netlify](README_NETLIFY.md) - Instructions détaillées pour le déploiement
- [Wiki du projet](https://github.com/Roddygithub/Guildwars2_TeamBuilder/wiki) - Documentation complète du projet
- [Documentation Supabase](https://supabase.com/docs) - Guide d'utilisation de Supabase
- [Documentation Netlify](https://docs.netlify.com/) - Guide de déploiement sur Netlify

### Développement local

1. Cloner le dépôt :
   ```bash
   git clone https://github.com/Roddygithub/Guildwars2_TeamBuilder.git
   cd Guildwars2_TeamBuilder
   ```

2. Configurer l'environnement :
   - Copier `.env.example` vers `.env`
   - Mettre à jour les variables d'environnement si nécessaire

3. Installer les dépendances du backend :
   ```bash
   python -m pip install -r requirements.txt
   ```

4. Installer les dépendances du frontend :
   ```bash
   cd ui
   npm install
   cd ..
   ```

5. Démarrer le serveur de développement :
   ```bash
   # Dans un premier terminal (backend) :
   uvicorn app.main:app --reload --port 8001
   
   # Dans un second terminal (frontend) :
   cd ui
   npm run dev
   ```

L'application sera disponible à l'adresse : `http://localhost:5173`

## 🚀 Déploiement sur Netlify avec Supabase

### Configuration requise
- Un compte [Netlify](https://www.netlify.com/)
- Un compte [Supabase](https://supabase.com/) (gratuit)
- Un compte [GitHub](https://github.com/) (recommandé pour le déploiement continu)

## Configuration de Supabase

1. **Créez un projet Supabase** :
   - Connectez-vous à [Supabase](https://supabase.com/)
   - Créez un nouveau projet dans une région proche de vos utilisateurs
   - Notez les informations de connexion (URL et mot de passe)

2. **Configurez la base de données** :
   - Installez les dépendances requises :
     ```bash
     pip install -r scripts/requirements-db.txt
     ```
   - Exécutez le script de configuration :
     ```bash
     python scripts/setup_supabase.py --database-url "postgresql://postgres:VOTRE_MOT_DE_PASSE@db.VOTRE_PROJET_REF.supabase.co:5432/postgres"
     ```
   - Remplacez `VOTRE_MOT_DE_PASSE` et `VOTRE_PROJET_REF` par vos informations Supabase

## Déploiement sur Netlify

### 1. Préparation du dépôt
- Forkez ce dépôt sur votre compte GitHub
- Clonez votre fork en local

### 2. Configuration de Netlify
1. Connectez-vous à [Netlify](https://app.netlify.com/)
2. Cliquez sur "Add new site" > "Import an existing project"
3. Sélectionnez votre dépôt GitHub forké

### 3. Configuration du build
- **Référence de la branche** : `main` (ou votre branche de production)
- **Commande de build** : `cd ui && npm install && npm run build`
- **Répertoire de publication** : `ui/dist`
- **Fonctions** : `netlify/functions`

### 4. Variables d'environnement
Ajoutez ces variables dans les paramètres de votre site Netlify :

```
# Configuration de l'application
ENVIRONMENT=production
DEBUG=false

# URL du frontend (à mettre à jour après le déploiement)
FRONTEND_URL=https://votre-site.netlify.app

# Origines autorisées (séparées par des virgules)
ALLOWED_ORIGINS=https://votre-site.netlify.app,http://localhost:3000

# Configuration Supabase (remplacer avec vos informations)
DATABASE_URL=postgresql://postgres:VOTRE_MOT_DE_PASSE@db.VOTRE_PROJET_REF.supabase.co:5432/postgres

# Clé secrète (générée automatiquement ou utilisez le script scripts/generate_secret_key.py)
SECRET_KEY=votre_clé_secrète_très_longue_et_sécurisée
```

### 5. Déclenchement du déploiement
- Poussez vos modifications sur la branche `main` pour déclencher un déploiement automatique
- Vérifiez les logs de déploiement dans l'onglet "Deploys" de Netlify
   - `NETLIFY`: `true`

5. **Déclenchez le déploiement**
   - Netlify détectera automatiquement les changements et déploiera votre application

## 🛠 Structure du projet

```text
Guildwars2_TeamBuilder/
├── app/                    # Code source Python du backend
│   ├── api/                # Points de terminaison API
│   ├── models/             # Modèles de données
│   ├── optimizer/          # Algorithmes d'optimisation
│   └── scoring/            # Système de notation
├── netlify/
│   └── functions/          # Fonctions serverless pour Netlify
├── ui/                     # Application frontend React
│   ├── public/             # Fichiers statiques
│   └── src/                # Code source React
├── .env.example            # Exemple de configuration
├── netlify.toml            # Configuration Netlify
└── requirements.txt        # Dépendances Python
```

### Activation de l'environnement virtuel

```bash
# Sous Windows
.\venv\Scripts\activate

# Sous macOS/Linux
source venv/bin/activate
```

3. Installer en mode développement :

   ```bash
   pip install -e .[dev]
   ```

## 🛠 Développement

### Configuration requise

- Python 3.9+
- pip
- git

### Installation des dépendances de développement

```bash
# Installer les dépendances de développement
pip install -r requirements-dev.txt

# Configurer les hooks git
pre-commit install
```

### Tests

```bash
# Exécuter les tests
pytest

# Avec couverture de code
pytest --cov=app tests/
```

### Construction du package

```bash
# Nettoyer les builds précédents
rm -rf dist/ build/ *.egg-info/

# Construire le package
python setup.py sdist bdist_wheel
```

### Publication sur PyPI

1. Créer un fichier `.pypirc` à la racine du projet (basé sur `.pypirc.example`)
2. Construire et publier :

   ```bash
   # Test sur TestPyPI
   twine upload --repository testpypi dist/*
   
   # Publication sur PyPI
   twine upload dist/*
   ```

   > **Note** : Assurez-vous d'avoir un compte sur [PyPI](https://pypi.org/) et [TestPyPI](https://test.pypi.org/) avant de publier.

## Utilisation

### Ligne de commande

```bash
# Générer une équipe optimale pour du zerg (10 joueurs)
python -m app.cli generate --team-size 10 --playstyle zerg

# Exporter un build spécifique au format gw2skills.net
python -m app.cli export --build "Heal Firebrand" --format gw2skills
```

### API

L'application expose une API REST complète :

```python
import requests

# Obtenir des suggestions d'équipe
response = requests.post(
    "http://localhost:8000/api/teams/suggest",
    json={
        "team_size": 5,
        "playstyle": "havoc",
        "allowed_professions": [
            "Guardian",
            "Necromancer",
            "Engineer"
        ]
    }
)
print(response.json())
```

## Structure du projet

```text
Guildwars2_TeamBuilder/
├── app/                     # Code source principal
│   ├── api/                 # Points d'entrée de l'API
│   ├── builds/              # Générateurs de builds
│   ├── data/                # Données et modèles
│   ├── exporters/           # Export vers différents formats
│   ├── models/              # Modèles de données
│   ├── optimizer/           # Algorithmes d'optimisation
│   └── scoring/             # Système de notation
├── tests/                   # Tests automatisés
├── .env.example             # Exemple de configuration
├── .gitignore
├── README.md
├── requirements.txt         # Dépendances Python
└── setup.py
```

## Contribution

Les contributions sont les bienvenues ! Voici comment procéder :

1. Forkez le projet

2. Créez une branche pour votre fonctionnalité :

   ```bash
   git checkout -b feature/AmazingFeature
   ```

3. Committez vos changements :

   ```bash
   git commit -m 'Add some AmazingFeature'
   ```

4. Poussez vers la branche :

   ```bash
   git push origin feature/AmazingFeature
   ```
5. Ouvrez une Pull Request

## Licence

Distribué sous la licence MIT. Voir `LICENSE` pour plus d'informations.

## Contact

Votre Nom - [@votre_twitter](https://twitter.com/votre_twitter) - votre.email@example.com

Lien du projet : [https://github.com/votre-utilisateur/gw2-team-builder](https://github.com/votre-utilisateur/gw2-team-builder)

## Remerciements

- L'équipe d'ArenaNet pour Guild Wars 2
- La communauté GW2 pour son soutien
- Tous les contributeurs qui ont rendu ce projet possible
