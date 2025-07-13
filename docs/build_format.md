# Format natif des builds

Ce document décrit le format JSON natif utilisé pour l'import/export des builds dans l'application GW2 Team Builder.

## Structure générale

Un build est représenté par un objet JSON avec les propriétés suivantes :

```json
{
  "name": "Nom du build",
  "profession": "type_de_profession",
  "role": "type_de_role",
  "specializations": [
    { "id": 1, "name": "Nom de la spécialisation", "traits": [1, 2, 3] }
  ],
  "skills": [1, 2, 3, 4, 5],
  "equipment": {
    "slot": { "id": 123, "name": "Nom de l'objet", "infusions": [], "upgrades": [] }
  },
  "description": "Description optionnelle",
  "source": "URL ou source du build"
}
```

## Détails des champs

### `name` (string, requis)
Le nom du build.

### `profession` (string, requis)
La profession du personnage. Doit être l'une des valeurs suivantes :
- `elementalist`
- `engineer`
- `guardian`
- `mesmer`
- `necromancer`
- `ranger`
- `revenant`
- `thief`
- `warrior`

### `role` (string, requis)
Le rôle principal du build. Doit être l'une des valeurs suivantes :
- `dps`
- `heal`
- `quickness`
- `alacrity`
- `support`
- `tank`

### `specializations` (array, requis)
Un tableau contenant exactement 3 spécialisations, dans l'ordre :
- Ligne majeure 1
- Ligne majeure 2
- Ligne majeure 3

Chaque spécialisation est un objet avec :
- `id` (number): L'identifiant de la spécialisation
- `name` (string): Le nom de la spécialisation
- `traits` (array): Un tableau de 3 nombres représentant les traits sélectionnés

### `skills` (array, requis)
Un tableau de 5 nombres représentant les compétences équipées, dans l'ordre :
1. Compétence de soin (6)
2. Compétence utilitaire 1 (7)
3. Compétence utilitaire 2 (8)
4. Compétence utilitaire 3 (9)
5. Compétence d'élite (0)

### `equipment` (object, optionnel)
Un objet où chaque clé est un emplacement d'équipement et chaque valeur est un objet représentant l'objet équipé.

Emplacements possibles :
- `Helm`, `Shoulders`, `Chest`, `Gloves`, `Leggings`, `Boots`
- `Backpack`
- `Accessory1`, `Accessory2`
- `Ring1`, `Ring2`
- `WeaponA1`, `WeaponA2`, `WeaponB1`, `WeaponB2`

Chaque objet d'équipement contient :
- `id` (number): L'identifiant de l'objet
- `name` (string): Le nom de l'objet
- `infusions` (array, optionnel): Tableau d'IDs d'infusions
- `upgrades` (array, optionnel): Tableau d'IDs d'améliorations

### `description` (string, optionnel)
Une description du build.

### `source` (string, optionnel)
L'URL ou la source d'où provient le build.

## Exemple complet

```json
{
  "name": "Heal Firebrand",
  "profession": "guardian",
  "role": "heal",
  "specializations": [
    {
      "id": 46,
      "name": "Zeal",
      "traits": [909, 0, 909]
    },
    {
      "id": 27,
      "name": "Honor",
      "traits": [915, 0, 894]
    },
    {
      "id": 62,
      "name": "Firebrand",
      "traits": [904, 0, 0]
    }
  ],
  "skills": [62561, 9153, 0, 0, 0],
  "equipment": {
    "Helm": {
      "id": 48033,
      "name": "Harrier's Wreath of the Diviner",
      "infusions": [49432],
      "upgrades": [24615]
    },
    "Shoulders": {
      "id": 48034,
      "name": "Harrier's Pauldrons of the Diviner",
      "infusions": [49432],
      "upgrades": [24615]
    },
    "Chest": {
      "id": 48035,
      "name": "Harrier's Breastplate of the Diviner",
      "infusions": [49432],
      "upgrades": []
    },
    "Gloves": {
      "id": 48036,
      "name": "Harrier's Armguards of the Diviner",
      "infusions": [49432],
      "upgrades": []
    },
    "Leggings": {
      "id": 48037,
      "name": "Harrier's Tassets of the Diviner",
      "infusions": [49432],
      "upgrades": []
    },
    "Boots": {
      "id": 48038,
      "name": "Harrier's Greaves of the Diviner",
      "infusions": [49432],
      "upgrades": []
    },
    "Backpack": {
      "id": 48039,
      "name": "Harrier's Cape of the Diviner",
      "infusions": [49432],
      "upgrades": []
    },
    "Accessory1": {
      "id": 48040,
      "name": "Harrier's Earring of the Diviner",
      "infusions": [49432],
      "upgrades": []
    },
    "Accessory2": {
      "id": 48041,
      "name": "Harrier's Amulet of the Diviner",
      "infusions": [],
      "upgrades": []
    },
    "Ring1": {
      "id": 48042,
      "name": "Harrier's Band of the Diviner",
      "infusions": [49432],
      "upgrades": []
    },
    "Ring2": {
      "id": 48042,
      "name": "Harrier's Band of the Diviner",
      "infusions": [49432],
      "upgrades": []
    },
    "WeaponA1": {
      "id": 30699,
      "name": "Harrier's Staff",
      "infusions": [49432],
      "upgrades": [24615, 24554]
    },
    "WeaponA2": {
      "id": 0,
      "name": "",
      "infusions": [],
      "upgrades": []
    },
    "WeaponB1": {
      "id": 0,
      "name": "",
      "infusions": [],
      "upgrades": []
    },
    "WeaponB2": {
      "id": 0,
      "name": "",
      "infusions": [],
      "upgrades": []
    }
  },
  "description": "Heal Firebrand avec Quickness et stabilité. Idéal pour les raids et les fractales.",
  "source": "https://snowcrows.com/builds/guardian/firebrand-heal"
}
```

## Utilisation avec l'API

### Importer un build

```bash
curl -X POST "http://localhost:8000/api/builds/import" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@mon_build.json"
```

### Exporter un build

```bash
# Exporter un build existant (par ID)
curl -X GET "http://localhost:8000/api/builds/export/123" \
  -H "accept: application/json" \
  --output mon_build_export.json

# Exporter directement un build
curl -X POST "http://localhost:8000/api/builds/export" \
  -H "Content-Type: application/json" \
  -d @mon_build.json \
  --output mon_build_export.json
```

### Obtenir un modèle vide

```bash
curl -X GET "http://localhost:8000/api/builds/template" \
  -H "accept: application/json"
```

## Bonnes pratiques

1. **Validation** : Tous les champs sont validés côté serveur.
2. **Rétrocompatibilité** : Les futurs champs seront optionnels pour maintenir la compatibilité.
3. **Sécurité** : Ne pas inclure d'informations sensibles dans les champs de texte.
4. **Performance** : Pour les builds complexes, préférez les appels API directs au format JSON plutôt que les fichiers.
