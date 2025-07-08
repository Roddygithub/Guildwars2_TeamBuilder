"""Module pour récupérer des données du wiki officiel de Guild Wars 2.

Ce module fournit des fonctions pour interagir avec l'API du wiki GW2 et extraire
des informations détaillées sur les compétences, les caractéristiques, les objets, etc.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

WIKI_API_URL = "https://wiki.guildwars2.com/api.php"
WIKI_BASE_URL = "https://wiki.guildwars2.com"

# En-têtes pour les requêtes HTTP
HEADERS = {
    "User-Agent": "GW2TeamBuilder/1.0 (https://github.com/yourusername/gw2-team-builder)",
    "Accept": "application/json"
}

# Cache pour les requêtes au wiki
_wiki_cache: Dict[str, Any] = {}


def _fetch_wiki_page(title: str) -> Optional[Dict[str, Any]]:
    """Récupère le contenu d'une page du wiki.
    
    Args:
        title: Titre de la page wiki (par exemple "Binding Blade")
        
    Returns:
        Un dictionnaire contenant les données de la page ou None en cas d'erreur
    """
    if title in _wiki_cache:
        return _wiki_cache[title]
    
    params = {
        "action": "parse",
        "format": "json",
        "page": title,
        "prop": "text|properties",
        "utf8": 1,
        "formatversion": 2
    }
    
    try:
        response = requests.get(
            WIKI_API_URL, 
            params=params, 
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if "parse" in data:
            _wiki_cache[title] = data["parse"]
            return data["parse"]
        return None
    except (requests.RequestException, ValueError) as e:
        logger.error("Erreur lors de la récupération de la page wiki '%s': %s", title, e)
        return None


def _extract_infobox_data(html_content: str) -> Dict[str, Any]:
    """Extrait les données d'une boîte d'information (infobox) d'une page wiki.
    
    Args:
        html_content: Contenu HTML de la page wiki
        
    Returns:
        Un dictionnaire contenant les données extraites de l'infobox
    """
    if not html_content:
        return {}
    
    soup = BeautifulSoup(html_content, 'html.parser')
    infobox = soup.find('table', class_='infobox')
    
    if not infobox:
        return {}
    
    data = {}
    rows = infobox.find_all('tr')
    
    for row in rows:
        th = row.find('th')
        td = row.find('td')
        
        if th and td:
            key = th.get_text(strip=True).lower().replace(' ', '_')
            value = td.get_text(strip=True)
            data[key] = value
    
    return data


def get_skill_details(skill_name: str) -> Dict[str, Any]:
    """Récupère les détails d'une compétence depuis le wiki.
    
    Args:
        skill_name: Nom de la compétence (par exemple "Binding Blade")
        
    Returns:
        Un dictionnaire contenant les détails de la compétence
    """
    page_data = _fetch_wiki_page(skill_name)
    if not page_data:
        return {}
    
    html_content = page_data.get("text", "")
    infobox_data = _extract_infobox_data(html_content)
    
    # Extraction des informations spécifiques aux compétences
    details = {
        "name": skill_name,
        "description": "",  # À extraire du contenu
        "type": infobox_data.get("type", ""),
        "recharge": infobox_data.get("recharge", ""),
        "facts": [],  # À extraire du contenu
        "traited_facts": []  # À extraire du contenu
    }
    
    # Extraction de la description et des faits (simplifiée)
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extraction de la description (premier paragraphe après l'infobox)
    first_paragraph = soup.find('div', class_='skill-description')
    if first_paragraph:
        details["description"] = first_paragraph.get_text(strip=True)
    
    # Extraction des faits (simplifiée)
    fact_sections = soup.find_all('div', class_='skill-fact')
    for fact in fact_sections:
        fact_text = fact.get_text(strip=True)
        if fact_text:
            details["facts"].append(fact_text)
    
    return details


def get_trait_details(trait_name: str) -> Dict[str, Any]:
    """Récupère les détails d'une caractéristique depuis le wiki.
    
    Args:
        trait_name: Nom de la caractéristique
        
    Returns:
        Un dictionnaire contenant les détails de la caractéristique
    """
    page_data = _fetch_wiki_page(trait_name)
    if not page_data:
        return {}
    
    html_content = page_data.get("text", "")
    infobox_data = _extract_infobox_data(html_content)
    
    details = {
        "name": trait_name,
        "description": "",
        "tier": infobox_data.get("tier", ""),
        "slot": infobox_data.get("slot", ""),
        "facts": []
    }
    
    # Extraction de la description
    soup = BeautifulSoup(html_content, 'html.parser')
    description_div = soup.find('div', class_='trait-description')
    if description_div:
        details["description"] = description_div.get_text(strip=True)
    
    return details


def get_item_details(item_name: str) -> Dict[str, Any]:
    """Récupère les détails d'un objet depuis le wiki.
    
    Args:
        item_name: Nom de l'objet
        
    Returns:
        Un dictionnaire contenant les détails de l'objet
    """
    page_data = _fetch_wiki_page(item_name)
    if not page_data:
        return {}
    
    html_content = page_data.get("text", "")
    infobox_data = _extract_infobox_data(html_content)
    
    details = {
        "name": item_name,
        "type": infobox_data.get("type", ""),
        "rarity": infobox_data.get("rarity", ""),
        "level": infobox_data.get("level", ""),
        "value": infobox_data.get("value", ""),
        "attributes": {}
    }
    
    # Extraction des attributs (simplifiée)
    soup = BeautifulSoup(html_content, 'html.parser')
    attribute_rows = soup.select('div.attribute-row')
    
    for row in attribute_rows:
        name_span = row.find('span', class_='attribute-name')
        value_span = row.find('span', class_='attribute-value')
        
        if name_span and value_span:
            attr_name = name_span.get_text(strip=True).lower()
            attr_value = value_span.get_text(strip=True)
            details["attributes"][attr_name] = attr_value
    
    return details


def search_wiki(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Recherche des pages sur le wiki GW2.
    
    Args:
        query: Termes de recherche
        limit: Nombre maximum de résultats à retourner
        
    Returns:
        Une liste de résultats de recherche
    """
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "utf8": 1,
        "formatversion": 2
    }
    
    try:
        response = requests.get(
            WIKI_API_URL, 
            params=params, 
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if "query" in data and "search" in data["query"]:
            return data["query"]["search"]
        return []
    except (requests.RequestException, ValueError) as e:
        logger.error("Erreur lors de la recherche sur le wiki: %s", e)
        return []


# Exemple d'utilisation
if __name__ == "__main__":
    import json
    
    # Exemple: Récupérer les détails d'une compétence
    skill_name = "Binding Blade"
    skill_details = get_skill_details(skill_name)
    print(f"Détails de la compétence '{skill_name}':")
    print(json.dumps(skill_details, indent=2, ensure_ascii=False))
    
    # Exemple: Rechercher des compétences
    search_results = search_wiki("heal", limit=3)
    print("\nRésultats de recherche pour 'heal':")
    for result in search_results:
        print(f"- {result['title']} (score: {result['score']:.2f})")
