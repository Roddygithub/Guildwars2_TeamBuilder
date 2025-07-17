"""Script de test HTTP minimal avec gestion des erreurs."""
import http.server
import socketserver
import logging
import sys

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = b'{"status": "success", "message": "Hello, World!"}'
            self.wfile.write(response)
            logger.info(f"Requête reçue sur {self.path}")
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la requête: {e}", exc_info=True)
            self.send_error(500, str(e))

def run(port=5000):
    handler = SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
            logger.info(f"Démarrage du serveur HTTP sur http://127.0.0.1:{port}")
            logger.info("Appuyez sur Ctrl+C pour arrêter le serveur")
            httpd.serve_forever()
    except PermissionError as e:
        logger.error(f"Erreur de permission: {e}")
        logger.error("Assurez-vous que le port n'est pas déjà utilisé et que vous avez les droits nécessaires.")
    except OSError as e:
        logger.error(f"Erreur système: {e}")
        logger.error("Vérifiez votre configuration réseau et vos paramètres de pare-feu.")
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}", exc_info=True)
    finally:
        logger.info("Arrêt du serveur HTTP")

if __name__ == "__main__":
    logger.info("Démarrage du script de test HTTP")
    run()
    logger.info("Fin du script de test HTTP")
