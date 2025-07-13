#!/usr/bin/env python3
"""
Générateur de clé secrète sécurisée pour les environnements de production.

Ce script génère une clé aléatoire sécurisée qui peut être utilisée comme SECRET_KEY
pour les applications Django, Flask ou autres applications web.
"""
import secrets
import string

def generate_secret_key(length=50):
    """Génère une clé secrète aléatoire sécurisée.
    
    Args:
        length (int): Longueur de la clé à générer. Par défaut à 50 caractères.
        
    Returns:
        str: Une chaîne de caractères aléatoires sécurisée.
    """
    # Caractères possibles pour la clé secrète
    chars = string.ascii_letters + string.digits + string.punctuation
    
    # Suppression des caractères qui pourraient poser problème dans les variables d'environnement
    for char in '\'"`${}()[]<>|&;':
        chars = chars.replace(char, '')
    
    # Génération de la clé
    return ''.join(secrets.choice(chars) for _ in range(length))

def update_netlify_config(secret_key):
    """Met à jour le fichier netlify.toml avec la nouvelle clé secrète.
    
    Args:
        secret_key (str): La clé secrète à insérer dans la configuration.
    """
    import os
    import re
    
    # Chemin vers le fichier netlify.toml
    netlify_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'netlify.toml')
    
    try:
        # Lire le contenu actuel
        with open(netlify_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Échapper les caractères spéciaux pour l'expression régulière
        secret_key_escaped = re.escape(secret_key)
        
        # Remplacer la clé secrète existante ou l'ajouter si elle n'existe pas
        if 'SECRET_KEY = ' in content:
            new_content = re.sub(
                r'SECRET_KEY\s*=\s*"[^"]*"',
                f'SECRET_KEY = "{secret_key}"',
                content
            )
        else:
            # Trouver la section [build.environment] et ajouter la clé secrète
            if '[build.environment]' in content:
                new_content = content.replace(
                    '[build.environment]',
                    f'[build.environment]\n  SECRET_KEY = "{secret_key}"',
                    1
                )
            else:
                # Si la section n'existe pas, l'ajouter à la fin du fichier
                new_content = f"{content}\n\n[build.environment]\n  SECRET_KEY = \"{secret_key}\""
        
        # Écrire le nouveau contenu
        with open(netlify_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"✅ Clé secrète générée et ajoutée à {netlify_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour du fichier netlify.toml : {e}")
        return False

if __name__ == "__main__":
    print("\n🔑 Génération d'une clé secrète sécurisée...")
    
    # Générer une clé secrète
    secret_key = generate_secret_key()
    
    print(f"\nVotre nouvelle clé secrète est :\n{secret_key}")
    
    # Mettre à jour le fichier netlify.toml
    if update_netlify_config(secret_key):
        print("\n✅ Configuration mise à jour avec succès !")
        print("\n⚠️  Assurez-vous de ne pas partager cette clé et de la garder secrète !")
        print("   Cette clé est utilisée pour sécuriser les sessions et les tokens d'authentification.")
    else:
        print("\n❌ Une erreur est survenue lors de la mise à jour de la configuration.")
        print("   Veuillez ajouter manuellement la clé secrète à votre fichier netlify.toml :")
        print(f"   SECRET_KEY = \"{secret_key}\"")
    
    print("\n✨ Opération terminée !")
