"""Test d'import des modules avancés."""

def test_import_item():
    """Teste l'import du module Item."""
    from app.models.item import Item, ItemType, Rarity
    assert Item is not None
    assert ItemType is not None
    assert Rarity is not None

def test_import_item_stats():
    """Teste l'import du module ItemStats."""
    from app.models.item_stats import ItemStats
    assert ItemStats is not None

def test_import_item_stat_mapping():
    """Teste l'import du module ItemStatMapping."""
    from app.models.item_stat_mapping import ItemStatMapping
    assert ItemStatMapping is not None
