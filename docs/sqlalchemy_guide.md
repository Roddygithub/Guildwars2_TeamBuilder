# Guide de Référence SQLAlchemy

## Sommaire
1. [Modèles Principaux](#modèles-principaux)
2. [Relations Clés](#relations-clés)
3. [Stratégies de Chargement](#stratégies-de-chargement)
4. [Exemples de Requêtes](#exemples-de-requêtes)
5. [Bonnes Pratiques](#bonnes-pratiques)
6. [Débogage](#débogage)

## Modèles Principaux

### Item
Classe de base pour tous les objets du jeu.
- **Relations** :
  - `stats`: ItemStats (many-to-one)
  - `weapon`: Weapon (one-to-one, optionnel)
  - `armor`: Armor (one-to-one, optionnel)
  - `trinket`: Trinket (one-to-one, optionnel)
  - `upgrade_component`: UpgradeComponent (one-to-one, optionnel)

### Skill
Représente une compétence du jeu.
- **Relations** :
  - `weapons`: Weapon (many-to-many via `weapon_skills`)
  - `traits`: Trait (many-to-many via `trait_skills`)
  - `profession`: Profession (many-to-one)
  - `specialization`: Specialization (many-to-one)
  - `profession_weapon_types`: ProfessionWeaponType (many-to-many via `profession_weapon_skills`)

### Weapon
Représente une arme dans le jeu.
- **Relations** :
  - `skills`: Skill (many-to-many via `weapon_skills`)
  - `profession_weapon_types`: ProfessionWeaponType (one-to-many)

## Stratégies de Chargement

### 1. Lazy Loading (Par Défaut)
```python
# Déclenche une requête par accès à la relation
skill = db.get(Skill, 1)
weapons = skill.weapons  # Requête supplémentaire
```

### 2. Eager Loading avec joinedload
Idéal pour les relations many-to-one.
```python
from sqlalchemy.orm import joinedload

skills = db.execute(
    select(Skill)
    .options(joinedload(Skill.profession))
    .limit(10)
).scalars().all()
```

### 3. Eager Loading avec selectinload
Idéal pour les collections (one-to-many, many-to-many).
```python
from sqlalchemy.orm import selectinload

skills = db.execute(
    select(Skill)
    .options(selectinload(Skill.weapons))
    .limit(10)
).scalars().all()
```

## Exemples de Requêtes

### Récupérer les compétences d'une arme spécifique
```python
from sqlalchemy import select

# Requête optimisée avec jointure
query = select(Skill)\
    .join(weapon_skills, Skill.id == weapon_skills.c.skill_id)\
    .where(weapon_skills.c.weapon_id == "Sword")

skills = db.execute(query).scalars().all()
```

### Compter les compétences par type d'arme
```python
from sqlalchemy import func, select

query = select(
    Weapon.type,
    func.count(Skill.id).label('count')
).join(
    weapon_skills, Weapon.type == weapon_skills.c.weapon_id
).join(
    Skill, Skill.id == weapon_skills.c.skill_id
).group_by(
    Weapon.type
).order_by(
    func.count(Skill.id).desc()
)

result = db.execute(query).all()
```

## Bonnes Pratiques

1. **Éviter le N+1**
   ```python
   # À éviter
   for skill in skills:
       print(skill.weapons)  # Requête à chaque itération
   
   # Préférez
   skills = db.execute(select(Skill).options(selectinload(Skill.weapons))).scalars().all()
   ```

2. **Utiliser les index**
   ```python
   # Dans votre modèle
   name = Column(String(100), index=True)
   ```

3. **Limiter les colonnes**
   ```python
   # Ne sélectionnez que ce dont vous avez besoin
   query = select(Skill.name, Skill.type).limit(10)
   ```

## Débogage

### Activer le logging SQL
```python
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Vérifier les requêtes générées
```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import logging

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, params, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())
    logging.info(f"Début de la requête: {statement}")

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, params, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    logging.info(f"Fin de la requête (temps: {total:.6f}s)")
```

### Vérifier l'état des relations
```python
from sqlalchemy import inspect

# Voir les relations chargées
inspect(skill).attrs['weapons'].loaded

# Voir les relations disponibles
print(inspect(Skill).relationships.keys())
```

## Index Recommandés

```python
# Dans vos modèles
class Skill(Base):
    __tablename__ = 'skills'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)  # Pour les recherches par nom
    type = Column(String(50), index=True)   # Pour le filtrage par type
    profession_id = Column(Integer, ForeignKey('professions.id'), index=True)
    specialization_id = Column(Integer, ForeignKey('specializations.id'), index=True)
```

## Mémo sur les Relations

| Relation | Type | Chargement Recommandé |
|----------|------|----------------------|
| Skill.weapons | many-to-many | selectinload |
| Skill.traits | many-to-many | selectinload |
| Skill.profession | many-to-one | joinedload |
| Skill.specialization | many-to-one | joinedload |
| Weapon.skills | many-to-many | selectinload |
| Item.stats | many-to-one | joinedload |
