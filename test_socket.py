"""Script de test pour vérifier l'écoute sur un port avec les sockets Python."""
import socket
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_socket(host='127.0.0.1', port=8001):
    """Teste l'écoute sur un port donné."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Essayer de lier le socket
        s.bind((host, port))
        logger.info(f"Le port {port} est disponible et peut être lié à {host}")
        return True
    except OSError as e:
        logger.error(f"Impossible de lier le port {port} à {host}: {e}")
        return False
    finally:
        s.close()

if __name__ == "__main__":
    # Tester le port par défaut
    test_socket()
    
    # Tester un autre port au cas où
    test_socket(port=8002)
