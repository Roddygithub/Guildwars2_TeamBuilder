"""Script de test pour vérifier la liaison de port avec les sockets Python."""
import socket
import sys
import time

def test_bind(port=3000):
    """Teste la liaison à un port spécifique."""
    try:
        # Créer un socket TCP/IP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Essayer de lier le socket à l'adresse et au port
        server_address = ('127.0.0.1', port)
        print(f'Démarrage sur {server_address[0]} port {server_address[1]}')
        sock.bind(server_address)
        
        # Mettre le socket en mode écoute
        sock.listen(1)
        print(f'En écoute sur le port {port}...')
        
        # Attendre une connexion
        print('En attente de connexion...')
        connection, client_address = sock.accept()
        
        try:
            print(f'Connexion de {client_address}')
            
            # Réception des données
            while True:
                data = connection.recv(16)
                print(f'Reçu: {data.decode()}')
                if data:
                    print('Envoi des données au client')
                    connection.sendall(b'Bonjour, client')
                else:
                    print('Plus de données de la part du client')
                    break
                    
        finally:
            # Nettoyer la connexion
            connection.close()
            
    except Exception as e:
        print(f'Erreur: {e}')
        raise
    finally:
        sock.close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    test_bind(port)
