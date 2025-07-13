# Configuration de Supabase pour Guild Wars 2 Team Builder

Ce guide vous explique comment configurer un projet Supabase pour déployer l'application Guild Wars 2 Team Builder.

## Prérequis

- Un compte [Supabase](https://supabase.com/)
- Python 3.8 ou supérieur
- Un terminal avec accès à la ligne de commande
- Un éditeur de texte

## Étape 1 : Créer un projet Supabase

1. Connectez-vous à [Supabase](https://supabase.com/)
2. Cliquez sur "New Project"
3. Remplissez les informations du projet :
   - Nom du projet : `gw2-teambuilder` (ou un nom de votre choix)
   - Mot de passe de la base de données : Notez ce mot de passe en lieu sûr
   - Région : Choisissez une région proche de vos utilisateurs
4. Cliquez sur "Create new project"

## Étape 2 : Récupérer les informations de connexion

1. Une fois le projet créé, allez dans les paramètres du projet (icône d'engrenage en bas à gauche)
2. Dans l'onglet "Database", notez :
   - Host
   - Port (par défaut 5432)
   - Database name (par défaut "postgres")
   - Username (par défaut "postgres")
   - Password (celui que vous avez défini à l'étape 1)
3. Dans l'onglet "API", notez :
   - Project URL
   - anon/public key
   - service_role key (gardez cette information sécurisée)

## Étape 3 : Configurer le fichier de configuration

1. Copiez le fichier `supabase-config.json.example` vers `supabase-config.json` :
   ```bash
   cp supabase-config.json.example supabase-config.json
   ```

2. Modifiez le fichier `supabase-config.json` avec les informations de votre projet :
   ```json
   {
     "supabase": {
       "project_id": "votre_project_id",
       "project_url": "https://votre_project_ref.supabase.co",
       "public_anon_key": "votre_anon_key",
       "public_url": "https://votre_project_ref.supabase.co",
       "jwt_secret": "votre_jwt_secret",
       "service_role_key": "votre_service_role_key"
     },
     "database": {
       "host": "db.votre_project_ref.supabase.co",
       "port": 5432,
       "name": "postgres",
       "user": "postgres",
       "password": "votre_mot_de_passe",
       "ssl_mode": "prefer"
     },
     "deployment": {
       "auto_migrate": true,
       "migrations_path": "./migrations"
     }
   }
   ```

## Étape 4 : Exécuter le script de configuration

1. Installez les dépendances requises :
   ```bash
   pip install -r scripts/requirements-db.txt
   ```

2. Exécutez le script de configuration :
   ```bash
   python scripts/configure_supabase.py --generate-secret
   ```

   Ce script va :
   - Générer une clé secrète JWT sécurisée
   - Mettre à jour le fichier `.env` avec les informations de connexion
   - Configurer le fichier `netlify.toml` pour le déploiement

## Étape 5 : Configurer la base de données

1. Exécutez le script de configuration de la base de données :
   ```bash
   python scripts/setup_supabase.py --database-url "postgresql://postgres:votre_mot_de_passe@db.votre_project_ref.supabase.co:5432/postgres"
   ```

   Ce script va créer les tables nécessaires dans votre base de données Supabase.

## Étape 6 : Vérifier la configuration

1. Vérifiez que le fichier `.env` a été créé avec les bonnes informations
2. Vérifiez que le fichier `netlify.toml` contient les variables d'environnement nécessaires
3. Vérifiez dans l'interface Supabase que les tables ont été créées

## Dépannage

### Erreur de connexion à la base de données
- Vérifiez que le mot de passe est correct
- Vérifiez que l'adresse de l'hôte est correcte
- Vérifiez que votre adresse IP est dans la liste blanche des adresses IP autorisées dans les paramètres de la base de données Supabase

### Tables non créées
- Vérifiez que le script s'est exécuté sans erreur
- Vérifiez que l'utilisateur a les droits nécessaires pour créer des tables

## Sécurité

- Ne partagez jamais votre fichier `.env` ou votre clé `service_role`
- Utilisez toujours HTTPS pour les connexions à la base de données
- Limitez les adresses IP qui peuvent se connecter à votre base de données
- Activez l'authentification à deux facteurs sur votre compte Supabase

## Ressources supplémentaires

- [Documentation Supabase](https://supabase.com/docs)
- [Guide de déploiement Netlify](README_NETLIFY.md)
- [Documentation de l'API](API_DOCS.md)
