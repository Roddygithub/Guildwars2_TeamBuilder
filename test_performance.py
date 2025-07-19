"""
Script de test des performances de l'API de génération d'équipe.
"""
import time
import requests
import json
import statistics
from typing import List, Dict, Any

# Configuration du test
BASE_URL = "http://localhost:8000/api/teams"
TEST_CONFIGS = [
    {
        "team_size": 5, 
        "playstyle": "zerg",
        "description": "Petite équipe Zerg"
    },
    {
        "team_size": 10, 
        "playstyle": "havoc",
        "allowed_professions": ["Guardian", "Warrior", "Revenant", "Ranger", "Thief", "Engineer", "Necromancer", "Elementalist", "Mesmer"],
        "description": "Équipe Havoc complète"
    },
    {
        "team_size": 5, 
        "playstyle": "gvg",
        "required_roles": {"heal": 1, "dps": 3, "quickness": 1, "alacrity": 1},
        "description": "Équipe GvG avec rôles spécifiques"
    }
]

def test_generate_team(team_size: int, playstyle: str, allowed_professions: List[str] = None, 
                      required_roles: Dict[str, int] = None) -> Dict[str, Any]:
    """Teste la génération d'équipe avec les paramètres donnés."""
    url = f"{BASE_URL}/generate"
    headers = {"Content-Type": "application/json"}
    
    # Préparation des paramètres de la requête
    params = {
        "team_size": team_size,
        "playstyle": playstyle,
    }
    
    # Ajout des paramètres optionnels
    if allowed_professions:
        params["allowed_professions"] = allowed_professions
    if required_roles:
        params["required_roles"] = required_roles
    
    # Envoi de la requête et mesure du temps
    start_time = time.time()
    try:
        print(f"Envoi de la requête à {url} avec les paramètres: {json.dumps(params, indent=2)}")
        response = requests.post(url, json=params, headers=headers)
        
        # Vérification du statut HTTP
        if response.status_code != 200:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = json.dumps(error_json, indent=2)
            except:
                pass
                
            return {
                "success": False,
                "error": f"Erreur HTTP {response.status_code}: {response.reason}\nDétails: {error_detail}",
                "duration": time.time() - start_time,
                "team_size": team_size,
                "playstyle": playstyle
            }
            
        # Traitement de la réponse réussie
        result = response.json()
        duration = time.time() - start_time
        
        return {
            "success": True,
            "duration": duration,
            "team_size": team_size,
            "playstyle": playstyle,
            "score": result.get("score", 0),
            "team": [p.get("profession") for p in result.get("team", [])] if result.get("team") else []
        }
        
    except requests.exceptions.RequestException as e:
        # Erreur de connexion ou de requête
        return {
            "success": False,
            "error": f"Erreur de connexion: {str(e)}",
            "duration": time.time() - start_time,
            "team_size": team_size,
            "playstyle": playstyle
        }
    except Exception as e:
        # Autres erreurs inattendues
        return {
            "success": False,
            "error": f"Erreur inattendue: {str(e)}\n{traceback.format_exc()}",
            "duration": time.time() - start_time,
            "team_size": team_size,
            "playstyle": playstyle
        }

def run_tests():
    """Exécute une série de tests de performance."""
    print("=== Début des tests de performance ===\n")
    
    results = []
    
    # Exécution des tests
    for config in TEST_CONFIGS:
        print(f"Test: {config['description']}")
        print(f"- Taille d'équipe: {config['team_size']}")
        print(f"- Style de jeu: {config['playstyle']}")
        if 'allowed_professions' in config:
            print(f"- Professions autorisées: {', '.join(config['allowed_professions'])}")
        if 'required_roles' in config:
            print(f"- Rôles requis: {config['required_roles']}")
        print("Lancement du test...")
        
        # Exécution du test
        result = test_generate_team(
            team_size=config['team_size'],
            playstyle=config['playstyle'],
            allowed_professions=config.get('allowed_professions'),
            required_roles=config.get('required_roles')
        )
        
        # Affichage des résultats
        if result['success']:
            print(f"✅ Réussi en {result['duration']:.2f} secondes")
            print(f"- Score: {result.get('score', 0):.2f}")
            if result.get('team'):
                print(f"- Composition: {', '.join(result['team'])}")
            else:
                print("- Aucune équipe générée")
        else:
            print(f"❌ Échec: {result.get('error', 'Erreur inconnue')}")
            
            # Afficher plus de détails pour le débogage
            if 'response' in result and hasattr(result['response'], 'text'):
                print(f"Réponse du serveur: {result['response'].text[:500]}...")
        
        results.append(result)
        print("\n" + "-"*50 + "\n")
    
    # Affichage du récapitulatif
    print("=== Récapitulatif des performances ===\n")
    
    for i, result in enumerate(results, 1):
        if result['success']:
            print(f"Test {i}:")
            print(f"- Description: {TEST_CONFIGS[i-1]['description']}")
            print(f"- Durée: {result['duration']:.2f} secondes")
            print(f"- Taille d'équipe: {result.get('team_size', 'N/A')}")
            print(f"- Style de jeu: {result.get('playstyle', 'N/A')}")
            print(f"- Score: {result.get('score', 0):.2f}")
            if 'team' in result and result['team']:
                print(f"- Composition: {', '.join(result['team'])}")
            if 'error' in result and result['error']:
                print(f"- Erreur: {result['error']}")
            print()
    
    print("=== Fin des tests ===")

if __name__ == "__main__":
    run_tests()
