"""Script de test pour un serveur HTTP simple."""
import http.server
import socketserver
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = b'{"message": "Hello, World!"}'
        self.wfile.write(response)
        logger.info(f"Requête reçue sur {self.path}")

def run(port=8001):
    handler = SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        logger.info(f"Démarrage du serveur HTTP sur le port {port}...")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Arrêt du serveur...")
            httpd.server_close()

if __name__ == "__main__":
    run()
