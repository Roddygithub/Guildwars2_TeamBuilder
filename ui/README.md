# Guild Wars 2 Team Builder - Interface Utilisateur

Cette application React constitue l'interface utilisateur du Guild Wars 2 Team Builder.

## Prérequis

- Node.js v18 ou supérieur
- npm ou yarn

## Installation

1. Accédez au répertoire du projet :
   ```bash
   cd ui
   ```

2. Installez les dépendances :
   ```bash
   npm install
   ```

## Développement local

Pour lancer l'application en mode développement :

```bash
npm run dev
```

L'application sera disponible à l'adresse : [http://localhost:5173](http://localhost:5173)

## Construction pour la production

Pour construire l'application pour la production :

```bash
npm run build
```

Les fichiers de production seront générés dans le dossier `dist/`.

## Déploiement sur Netlify

Le projet est configuré pour être déployé sur Netlify. Le déploiement se fera automatiquement à chaque push sur la branche `main`.

### Configuration requise

- Compte Netlify
- Variables d'environnement (si nécessaire) configurées dans les paramètres de votre site Netlify

### Déploiement manuel

1. Connectez-vous à votre compte Netlify
2. Sélectionnez "New site from Git"
3. Choisissez votre dépôt
4. Configurez les paramètres de build :
   - Build command: `cd ui && npm install && npm run build`
   - Publish directory: `dist`
5. Cliquez sur "Deploy site"

## Structure du projet

- `/src` - Code source de l'application
  - `/components` - Composants réutilisables
  - `/pages` - Pages de l'application
  - `/services` - Services pour les appels API
  - `/assets` - Ressources statiques (images, polices, etc.)
- `/public` - Fichiers statiques copiés tels quels dans le build

## Licence

MIT
