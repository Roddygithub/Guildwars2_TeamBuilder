import logging
import sys
from app.models import Base
from app.models.relationships import setup_relationships

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

def main():
    logger.info("Début du test des relations...")
    
    try:
        # Appel à la configuration des relations
        setup_relationships()
        logger.info("Test des relations terminé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors du test des relations: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
