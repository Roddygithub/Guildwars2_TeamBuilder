# GW2 Team Builder

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Un outil avancé pour optimiser les compositions d'équipe dans Guild Wars 2, spécialement conçu pour le mode Monde contre Monde (WvW).

## Fonctionnalités

- 🎯 **Génération intelligente de builds** basée sur des algorithmes d'optimisation
- 🤝 **Synergies automatiques** entre les membres de l'équipe
- 🎮 **Support multi-mode** : Zerg, Havoc, Roaming, etc.
- 📊 **Analyse détaillée** des forces et faiblesses des compositions
- 🔄 **Intégration** avec l'API officielle de Guild Wars 2
- 📱 **Export** vers gw2skills.net et formats standards

## Démarrage rapide

### Installation

```bash
# Cloner le dépôt
git clone https://github.com/votre-utilisateur/gw2-team-builder.git
cd gw2-team-builder

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### Utilisation de base

```python
from app.optimizer.genetic import GeneticTeamOptimizer
from app.scoring.engine import ScoringConfig

# Configuration du scoring
config = ScoringConfig()

# Créer l'optimiseur
optimizer = GeneticTeamOptimizer(
    team_size=5,
    playstyle="zerg",
    scoring_config=config
)

# Générer une équipe optimale
best_team, score = optimizer.optimize()
print(f"Meilleure équipe trouvée avec un score de {score}")
```

## Documentation

Pour une documentation complète, consultez les sections suivantes :

- [Guide d'installation](user-guide/installation.md)
- [Guide de démarrage rapide](user-guide/getting-started.md)
- [Utilisation avancée](user-guide/advanced-usage.md)
- [Référence de l'API](api/modules.md)

## Contribuer

Les contributions sont les bienvenues ! Voici comment procéder :

1. Forkez le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Poussez vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

Consultez notre [guide de contribution](development/contributing.md) pour plus de détails.

## Licence

Distribué sous la licence MIT. Voir `LICENSE` pour plus d'informations.

## Remerciements

- L'équipe d'ArenaNet pour Guild Wars 2
- La communauté GW2 pour son soutien
- Tous les contributeurs qui ont rendu ce projet possible
