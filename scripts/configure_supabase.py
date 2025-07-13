#!/usr/bin/env python3
"""
Script de configuration de Supabase pour Guild Wars 2 Team Builder.

Ce script permet de configurer automatiquement un projet Supabase avec les paramètres nécessaires.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_path: str) -> Dict[str, Any]:
    """Charge le fichier de configuration Supabase.
    
    Args:
        config_path: Chemin vers le fichier de configuration.
        
    Returns:
        Un dictionnaire contenant la configuration.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Le fichier de configuration {config_path} n'existe pas.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Erreur de syntaxe dans le fichier de configuration: {e}")
        sys.exit(1)

def update_env_file(env_path: str, config: Dict[str, Any]) -> None:
    """Met à jour le fichier .env avec les informations de configuration.
    
    Args:
        env_path: Chemin vers le fichier .env
        config: Dictionnaire de configuration
    """
    # Lire le contenu actuel du fichier .env s'il existe
    env_lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            env_lines = f.readlines()
    
    # Mettre à jour ou ajouter les variables d'environnement
    env_vars = {
        'SUPABASE_URL': config['supabase']['project_url'],
        'SUPABASE_ANON_KEY': config['supabase']['public_anon_key'],
        'SUPABASE_JWT_SECRET': config['supabase']['jwt_secret'],
        'DATABASE_URL': f"postgresql://{config['database']['user']}:{config['database']['password']}@{config['database']['host']}:{config['database']['port']}/{config['database']['name']}",
        'SUPABASE_SERVICE_ROLE': config.get('supabase', {}).get('service_role_key', 'your-service-role-key')
    }
    
    # Mettre à jour les variables existantes ou les ajouter
    updated_vars = set()
    for i, line in enumerate(env_lines):
        if '=' in line:
            var_name = line.split('=')[0].strip()
            if var_name in env_vars:
                env_lines[i] = f"{var_name}={env_vars[var_name]}\n"
                updated_vars.add(var_name)
    
    # Ajouter les variables manquantes
    for var_name, var_value in env_vars.items():
        if var_name not in updated_vars:
            env_lines.append(f"{var_name}={var_value}\n")
    
    # Écrire le fichier .env mis à jour
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(env_lines)
    
    logger.info(f"Fichier {env_path} mis à jour avec succès")

def update_netlify_config(netlify_path: str, config: Dict[str, Any]) -> None:
    """Met à jour le fichier de configuration Netlify.
    
    Args:
        netlify_path: Chemin vers le fichier netlify.toml
        config: Dictionnaire de configuration
    """
    if not os.path.exists(netlify_path):
        logger.warning(f"Le fichier {netlify_path} n'existe pas, création...")
        with open(netlify_path, 'w', encoding='utf-8') as f:
            f.write("[build]\n")
    
    # Lire le contenu actuel du fichier netlify.toml
    with open(netlify_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Vérifier si la section [build.environment] existe
    env_section_start = -1
    env_section_end = -1
    for i, line in enumerate(lines):
        if line.strip() == '[build.environment]':
            env_section_start = i
        elif env_section_start != -1 and line.startswith('[') and line.strip() != '':
            env_section_end = i
            break
    
    # Préparer les variables d'environnement pour Netlify
    env_vars = {
        'DATABASE_URL': f"postgresql://{config['database']['user']}:{config['database']['password']}@{config['database']['host']}:{config['database']['port']}/{config['database']['name']}",
        'SUPABASE_URL': config['supabase']['project_url'],
        'SUPABASE_ANON_KEY': config['supabase']['public_anon_key'],
        'SUPABASE_JWT_SECRET': config['supabase']['jwt_secret'],
        'ENVIRONMENT': 'production',
        'NODE_VERSION': '18',
        'NPM_FLAGS': '--legacy-peer-deps',
        'YARN_VERSION': '1.22.19',
        'YARN_FLAGS': '--network-timeout 60000',
        'NEXT_TELEMETRY_DISABLED': '1',
        'NODE_OPTIONS': '--max_old_space_size=4096'
    }
    
    # Créer ou mettre à jour la section [build.environment]
    env_section = ['[build.environment]\n']
    for key, value in env_vars.items():
        env_section.append(f'  {key} = "{value}"\n')
    
    # Mettre à jour ou ajouter la section [build.environment]
    if env_section_start != -1:
        # Mettre à jour la section existante
        if env_section_end == -1:
            env_section_end = len(lines)
        
        # Supprimer les lignes existantes de la section
        del lines[env_section_start:env_section_end]
        
        # Insérer les nouvelles lignes
        lines[env_section_start:env_section_start] = env_section
    else:
        # Ajouter une nouvelle section à la fin du fichier
        lines.extend(['\n'] + env_section)
    
    # Écrire le fichier netlify.toml mis à jour
    with open(netlify_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    logger.info(f"Fichier {netlify_path} mis à jour avec succès")

def generate_secret_key() -> str:
    """Génère une clé secrète sécurisée.
    
    Returns:
        Une chaîne de caractères aléatoire sécurisée.
    """
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits + "-._~"
    return ''.join(secrets.choice(alphabet) for _ in range(64))

def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(description='Configure Supabase pour Guild Wars 2 Team Builder')
    parser.add_argument(
        '--config',
        type=str,
        default='supabase-config.json',
        help='Chemin vers le fichier de configuration Supabase (défaut: supabase-config.json)'
    )
    parser.add_argument(
        '--env',
        type=str,
        default='.env',
        help='Chemin vers le fichier .env (défaut: .env)'
    )
    parser.add_argument(
        '--netlify',
        type=str,
        default='netlify.toml',
        help='Chemin vers le fichier netlify.toml (défaut: netlify.toml)'
    )
    parser.add_argument(
        '--generate-secret',
        action='store_true',
        help='Génère une nouvelle clé secrète pour JWT'
    )
    
    args = parser.parse_args()
    
    # Charger la configuration
    config = load_config(args.config)
    
    # Générer une nouvelle clé secrète si demandé
    if args.generate_secret:
        new_secret = generate_secret_key()
        config['supabase']['jwt_secret'] = new_secret
        logger.info(f"Nouvelle clé secrète JWT générée: {new_secret}")
    
    # Mettre à jour les fichiers de configuration
    update_env_file(args.env, config)
    update_netlify_config(args.netlify, config)
    
    logger.info("Configuration terminée avec succès!")
    
    # Afficher les informations de connexion
    print("\n🔑 Informations de configuration :")
    print(f"URL du projet Supabase: {config['supabase']['project_url']}")
    print(f"Clé anonyme: {config['supabase']['public_anon_key']}")
    print(f"Hôte de la base de données: {config['database']['host']}")
    print(f"Utilisateur de la base de données: {config['database']['user']}")
    print(f"Nom de la base de données: {config['database']['name']}")
    
    # Avertissement concernant la sécurité
    print("\n⚠️ IMPORTANT: Assurez-vous de ne pas partager ces informations sensibles!")
    print("  - Le fichier .env est dans .gitignore pour des raisons de sécurité")
    print("  - Ne partagez jamais les clés secrètes ou les mots de passe")
    print("  - Régénérez les clés si elles sont compromises")

if __name__ == "__main__":
    main()
