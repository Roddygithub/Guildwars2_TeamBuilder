# Guide de déploiement Netlify pour Guild Wars 2 Team Builder

Ce guide vous explique comment déployer l'application Guild Wars 2 Team Builder sur Netlify avec une base de données Supabase gratuite.

## Prérequis

1. Un compte [Netlify](https://www.netlify.com/)
2. Un compte [Supabase](https://supabase.com/)
3. Un compte [GitHub](https://github.com/) (recommandé pour le déploiement continu)

## Étape 1 : Configurer Supabase

1. Connectez-vous à [Supabase](https://supabase.com/)
2. Créez un nouveau projet
   - Choisissez une région proche de vos utilisateurs
   - Utilisez un mot de passe fort pour la base de données
3. Une fois le projet créé, allez dans l'onglet "Table Editor"
4. Importez la structure de la base de données (voir section "Structure de la base de données" ci-dessous)
5. Allez dans "Project Settings" > "Database" et notez les informations de connexion

## Étape 2 : Configurer Netlify

1. Connectez-vous à [Netlify](https://www.netlify.com/)
2. Cliquez sur "Add new site" > "Import an existing project"
3. Liez votre dépôt GitHub (ou autre fournisseur Git)
4. Configurez les paramètres de build :
   - **Référence de la branche** : `main` (ou votre branche de production)
   - **Commande de build** : `cd ui && npm install && npm run build`
   - **Répertoire de publication** : `ui/dist`
   - **Fonctions** : `netlify/functions`
5. Configurez les variables d'environnement dans "Site settings" > "Build & deploy" > "Environment"

## Variables d'environnement requises

Ajoutez les variables suivantes dans les paramètres de votre site Netlify :

```
# Configuration de l'application
ENVIRONMENT=production
DEBUG=false

# URL du frontend (remplacez par votre URL Netlify après le déploiement)
FRONTEND_URL=https://votre-site.netlify.app

# Origines autorisées (séparées par des virgules)
ALLOWED_ORIGINS=https://votre-site.netlify.app,http://localhost:3000

# Configuration de la base de données Supabase
DATABASE_URL=postgresql://postgres:VOTRE_MOT_DE_PASSE@db.VOTRE_PROJET_REF.supabase.co:5432/postgres

# Clé secrète (générée automatiquement ou créez-en une sécurisée)
SECRET_KEY=votre_clé_secrète_très_longue_et_sécurisée

# Configuration du cache (optionnel)
CACHE_TTL=3600
```

## Structure de la base de données

Exécutez le script SQL suivant dans l'éditeur SQL de Supabase pour créer les tables nécessaires :

```sql
-- Table des professions
CREATE TABLE IF NOT EXISTS professions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(50) NOT NULL,
    icon VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table des spécialisations
CREATE TABLE IF NOT EXISTS specializations (
    id SERIAL PRIMARY KEY,
    profession_id INTEGER REFERENCES professions(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    display_name VARCHAR(50) NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(profession_id, name)
);

-- Table des compétences
CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    specialization_id INTEGER REFERENCES specializations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    slot VARCHAR(20),
    type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table des builds sauvegardés
CREATE TABLE IF NOT EXISTS builds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    profession_id INTEGER REFERENCES professions(id) ON DELETE CASCADE,
    specialization_id INTEGER REFERENCES specializations(id) ON DELETE SET NULL,
    skills JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_public BOOLEAN DEFAULT false,
    created_by UUID
);

-- Index pour améliorer les performances des requêtes
CREATE INDEX idx_builds_profession ON builds(profession_id);
CREATE INDEX idx_builds_specialization ON builds(specialization_id);
CREATE INDEX idx_builds_created_by ON builds(created_by);
CREATE INDEX idx_builds_is_public ON builds(is_public);

-- Fonction pour mettre à jour automatiquement les champs updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Déclencheurs pour mettre à jour automatiquement les champs updated_at
CREATE TRIGGER update_professions_updated_at
BEFORE UPDATE ON professions
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_specializations_updated_at
BEFORE UPDATE ON specializations
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_skills_updated_at
BEFORE UPDATE ON skills
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_builds_updated_at
BEFORE UPDATE ON builds
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## Déploiement

1. Poussez votre code sur votre dépôt Git
2. Netlify détectera automatiquement les changements et déclenchera un nouveau déploiement
3. Vérifiez les logs de déploiement dans l'onglet "Deploys" de votre tableau de bord Netlify

## Dépannage

### Erreurs de connexion à la base de données
- Vérifiez que l'URL de la base de données est correcte
- Assurez-vous que votre base de données Supabase est en cours d'exécution
- Vérifiez que les paramètres de pare-feu de Supabase autorisent les connexions depuis Netlify

### Problèmes de build
- Vérifiez les logs de build dans Netlify pour plus de détails
- Assurez-vous que toutes les dépendances sont correctement installées
- Vérifiez que les chemins des fichiers sont corrects (respectez la casse)

### Problèmes de CORS
- Vérifiez que `FRONTEND_URL` et `ALLOWED_ORIGINS` sont correctement configurés
- Assurez-vous que les en-têtes CORS sont correctement définis dans `netlify.toml`

## Sécurité

- Ne partagez jamais vos informations d'identification de base de données
- Utilisez toujours HTTPS pour les connexions à votre API
- Limitez les autorisations de votre utilisateur de base de données au strict nécessaire
- Activez l'authentification à deux facteurs sur vos comptes Netlify et Supabase

## Maintenance

### Mises à jour de la base de données

Pour mettre à jour la structure de la base de données :

1. Créez un nouveau fichier de migration dans le répertoire `migrations/`
2. Nommez-le avec le format `YYYYMMDD_HHMMSS_description_du_changement.sql`
3. Exécutez la migration via l'interface Supabase ou en utilisant un client PostgreSQL

### Sauvegardes

Configurez des sauvegardes automatiques dans Supabase :

1. Allez dans "Database" > "Backups"
2. Configurez des sauvegardes automatiques quotidiennes
3. Téléchargez régulièrement une copie de sauvegarde

## Support

Pour toute question ou problème, veuillez ouvrir une issue sur le dépôt GitHub du projet.
