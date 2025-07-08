# Guild Wars 2 WvW Team Builder

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub stars](https://img.shields.io/github/stars/Roddygithub/Guildwars2_TeamBuilder?style=social)](https://github.com/Roddygithub/Guildwars2_TeamBuilder/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/Roddygithub/Guildwars2_TeamBuilder)](https://github.com/Roddygithub/Guildwars2_TeamBuilder/issues)

Un outil avancé pour optimiser les compositions d'équipe dans Guild Wars 2, spécialement conçu pour le mode Monde contre Monde (WvW).

## 🚀 Fonctionnalités

- 🎯 **Génération intelligente de builds** basée sur des algorithmes d'optimisation avancés
- 🤖 **Algorithme génétique** pour trouver les meilleures combinaisons de builds
- 🤝 **Synergies automatiques** entre les membres de l'équipe
- 🎮 **Support multi-mode** : Zerg, Havoc, Roaming, etc.
- 📊 **Analyse détaillée** des forces et faiblesses des compositions
- 🔄 **Intégration** avec l'API officielle de Guild Wars 2
- 📱 **Export** vers [gw2skills.net](https://gw2skills.net/) et formats standards
- 🧪 **Système de notation personnalisable** pour différents rôles et stratégies

## Prérequis

- Python 3.9 ou supérieur
- Compte API Guild Wars 2 (optionnel, pour les fonctionnalités avancées)

## Installation

1. Cloner le dépôt :

   ```bash
   git clone https://github.com/Roddygithub/Guildwars2_TeamBuilder.git
   cd Guildwars2_TeamBuilder
   ```

2. Créer un environnement virtuel :

   ```bash
   python -m venv venv
   # Sur Windows :
   .\venv\Scripts\activate
   # Sur macOS/Linux :
   # source venv/bin/activate
   ```

3. Installer les dépendances :

   ```bash
   pip install -r requirements.txt
   ```

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
