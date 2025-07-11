"""Script pour vérifier les statistiques d'objets problématiques dans l'API GW2."""

import asyncio
import aiohttp
import json
from datetime import datetime

# IDs problématiques identifiés
PROBLEMATIC_IDS = [50, 112, 115, 520, 575, 625, 626, 636, 689, 740, 800, 1419, 1548]

async def check_itemstat(session, itemstat_id):
    """Vérifie une statistique d'objet spécifique dans l'API GW2."""
    url = f"https://api.guildwars2.com/v2/itemstats/{itemstat_id}"
    
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return {"id": itemstat_id, "status": "ok", "data": data}
            else:
                return {"id": itemstat_id, "status": "error", "status_code": response.status, "error": "Non-200 status code"}
    except Exception as e:
        return {"id": itemstat_id, "status": "exception", "error": str(e)}

async def main():
    """Fonction principale pour vérifier les statistiques d'objets problématiques."""
    print(f"Vérification de {len(PROBLEMATIC_IDS)} statistiques d'objets problématiques...")
    
    async with aiohttp.ClientSession() as session:
        tasks = [check_itemstat(session, itemstat_id) for itemstat_id in PROBLEMATIC_IDS]
        results = await asyncio.gather(*tasks)
    
    # Afficher les résultats
    valid = []
    invalid = []
    
    for result in results:
        if result["status"] == "ok":
            valid.append(result)
        else:
            invalid.append(result)
    
    print(f"\n=== RÉSULTATS ===")
    print(f"Statistiques valides: {len(valid)}")
    print(f"Statistiques invalides: {len(invalid)}")
    
    if valid:
        print("\n=== STATISTIQUES VALIDES ===")
        for item in valid:
            print(f"\nID: {item['id']}")
            print(f"Nom: {item['data'].get('name', 'N/A')}")
            print(f"Attributs: {json.dumps(item['data'].get('attributes', []), indent=2, ensure_ascii=False)}")
    
    if invalid:
        print("\n=== STATISTIQUES INVALIDES ===")
        for item in invalid:
            print(f"\nID: {item['id']}")
            print(f"Statut: {item['status']}")
            if 'status_code' in item:
                print(f"Code d'état: {item['status_code']}")
            print(f"Erreur: {item.get('error', 'N/A')}")
    
    # Sauvegarder les résultats dans un fichier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"itemstats_validation_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "valid": valid,
            "invalid": invalid
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nRésultats enregistrés dans : {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
