# Utilisation de la ligne de commande (CLI)

Ce document explique comment utiliser les fonctionnalités d'import/export de builds via la ligne de commande.

## Installation

Assurez-vous d'avoir Python 3.8+ installé, puis installez les dépendances :

```bash
pip install -r requirements.txt
```

## Commandes disponibles

### Importer un build

```bash
python -m app.cli import-build chemin/vers/mon_build.json
```

Options :
- `--output-format FORMAT` : Format de sortie (json, text, table). Par défaut : text
- `--save` : Enregistre le build importé dans la base de données

### Exporter un build

```bash
python -m app.cli export-build 123
```

Où `123` est l'ID du build à exporter.

Options :
- `--output FILE` : Fichier de sortie. Si non spécifié, affiche sur la sortie standard
- `--format FORMAT` : Format de sortie (json, yaml). Par défaut : json

### Lister les builds

```bash
python -m app.cli list-builds
```

Options :
- `--format FORMAT` : Format de sortie (table, json, csv). Par défaut : table
- `--limit N` : Nombre maximum de builds à afficher
- `--role ROLE` : Filtrer par rôle (dps, heal, etc.)
- `--profession PROF` : Filtrer par profession

### Analyser un build

```bash
python -m app.cli analyze-build chemin/vers/mon_build.json
```

Options :
- `--output-format FORMAT` : Format de sortie (json, text, table). Par défaut : text
- `--verbose` : Afficher plus de détails

## Exemples

### Exemple 1 : Importer un build et l'enregistrer

```bash
python -m app.cli import-build builds/heal_firebrand.json --save
```

### Exemple 2 : Exporter un build au format YAML

```bash
python -m app.cli export-build 42 --format yaml --output firebrand_build.yaml
```

### Exemple 3 : Lister les builds de soigneur

```bash
python -m app.cli list-builds --role heal --format table
```

### Exemple 4 : Analyser un build local

```bash
python -m app.cli analyze-build my_build.json --verbose
```

## Codes de sortie

- `0` : Succès
- `1` : Erreur de validation
- `2` : Fichier non trouvé
- `3` : Erreur d'entrée/sortie
- `4` : Erreur de l'API
- `5` : Erreur inattendue

## Configuration

Créez un fichier `.env` à la racine du projet pour configurer la connexion à l'API :

```ini
API_BASE_URL=http://localhost:8000/api
# Optionnel : authentification
# API_KEY=votre_cle_api
```

## Dépannage

### Erreur de connexion à l'API

Vérifiez que l'API est en cours d'exécution et que l'URL de base est correctement configurée.

### Erreur de validation

Assurez-vous que le fichier JSON est bien formaté et contient tous les champs requis. Consultez la documentation du format natif pour plus de détails.

### Problèmes de performance

Pour les gros fichiers, utilisez l'option `--output` pour rediriger la sortie vers un fichier plutôt que de l'afficher dans le terminal.
