"""
Utilitaires pour la CLI.

Ce module contient des fonctions utilitaires pour l'interface en ligne de commande.
"""
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import json
import yaml

from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

def print_success(message: str) -> None:
    """Affiche un message de succès."""
    console.print(f"[green]✓[/green] {message}")

def print_error(message: str) -> None:
    """Affiche un message d'erreur."""
    console.print(f"[red]✗[/red] {message}", style="bold red")

def print_warning(message: str) -> None:
    """Affiche un message d'avertissement."""
    console.print(f"[yellow]![/yellow] {message}", style="yellow")

def format_output(data: Any, output_format: str = "text") -> str:
    """Formate les données de sortie selon le format spécifié.
    
    Args:
        data: Données à formater
        output_format: Format de sortie (text, json, yaml, table)
        
    Returns:
        str: Données formatées
    """
    if output_format == "json":
        return json.dumps(data, indent=2, ensure_ascii=False)
    elif output_format == "yaml":
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    elif output_format == "table" and isinstance(data, (list, tuple)):
        return format_as_table(data)
    else:
        return str(data)

def format_as_table(items: List[Dict[str, Any]], 
                   columns: Optional[List[str]] = None, 
                   title: str = "") -> str:
    """Formate une liste de dictionnaires en tableau.
    
    Args:
        items: Liste d'éléments à afficher
        columns: Liste des colonnes à afficher (si None, toutes les colonnes sont affichées)
        title: Titre du tableau
        
    Returns:
        str: Tableau formaté
    """
    if not items:
        return "Aucune donnée à afficher"
    
    # Déterminer les colonnes à afficher
    if columns is None:
        columns = list(items[0].keys())
    
    # Créer le tableau
    table = Table(box=box.ROUNDED, title=title, show_header=True, header_style="bold magenta")
    
    # Ajouter les colonnes
    for col in columns:
        table.add_column(col.capitalize())
    
    # Ajouter les lignes
    for item in items:
        row = [str(item.get(col, "")) for col in columns]
        table.add_row(*row)
    
    # Afficher le tableau
    console.print(table)
    return ""

def parse_bool(value: str) -> bool:
    """Convertit une chaîne en booléen."""
    if isinstance(value, bool):
        return value
    return value.lower() in ('true', '1', 't', 'y', 'yes')
