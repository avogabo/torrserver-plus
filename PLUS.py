import requests
import json

# Configuración
TORRSERVER_URL = "TU_URL_TORRSERVER"  # URL de TorrServer
QBITTORRENT_URL = "TU_URL"  # URL de qBittorrent
QBITTORRENT_USERNAME = "admin"  # Usuario de qBittorrent
QBITTORRENT_PASSWORD = "adminadmin"  # Contraseña de qBittorrent
QBT_DOWNLOAD_THRESHOLD = 7  # Umbral de descarga (en %)
QBT_ADD_PAUSED = True  # Añadir torrent pausado en qBittorrent
TRACKERS = [
    "tu_url_announce1",  # Añadir tu tracker privado aquí
    "tu_url_announce2"
]

def obtener_progreso_torrent(hash):
    """Obtiene el progreso real del torrent desde TorrServer usando PiecesCount y Readers[].Reader"""
    try:
        response = requests.post(f"{TORRSERVER_URL}/cache", json={"action": "get", "hash": hash})
        response.raise_for_status()
        data = response.json()

        # Obtener cantidad total de piezas y piezas leídas
        pieces_count = data.get("PiecesCount", 0)
        readers = data.get("Readers", [])

        # Calcular progreso si hay datos válidos
        if pieces_count > 0 and readers:
            pieces_read = sum(reader.get("Reader", 0) for reader in readers)
            progreso = (pieces_read / pieces_count) * 100
            print(f"Progreso del torrent ({hash}): {progreso:.2f}%")
            return progreso
    except requests.RequestException as e:
        print(f"Error al obtener progreso de torrent {hash}: {e}")

    return 0

def obtener_torrents_qbittorrent(session):
    """Obtiene la lista de torrents activos en qBittorrent usando una sesión autenticada."""
    try:
        response = session.get(f"{QBITTORRENT_URL}/api/v2/torrents/info")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error al obtener torrents de qBittorrent: {e}")
        return []

def agregar_torrent_a_qbittorrent(magnet_link, session):
    """Añade un torrent a qBittorrent en modo pausado usando una sesión autenticada."""
    try:
        data = {"urls": magnet_link, "start_paused_enabled": "true" if QBT_ADD_PAUSED else "false"}
        response = session.post(f"{QBITTORRENT_URL}/api/v2/torrents/add", data=data)
        if response.status_code == 200:
            print(f"Torrent añadido en pausa: {magnet_link}")
            return True
        else:
            print(f"Error al añadir torrent a qBittorrent: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"Error al conectar con qBittorrent: {e}")
        return False

def iniciar_sesion_qbittorrent():
    """Inicia sesión en qBittorrent y devuelve la sesión con la cookie SID."""
    try:
        session = requests.Session()
        login_data = {"username": QBITTORRENT_USERNAME, "password": QBITTORRENT_PASSWORD}
        login_response = session.post(f"{QBITTORRENT_URL}/api/v2/auth/login", data=login_data)
        if login_response.status_code == 200 and "SID" in login_response.cookies:
            print("Autenticación exitosa en qBittorrent")
            return session
        else:
            print(f"Error de autenticación en qBittorrent: {login_response.text}")
            return None
    except requests.RequestException as e:
        print(f"Error al iniciar sesión en qBittorrent: {e}")
        return None

def obtener_torrents_torrserver():
    """Obtiene la lista de torrents activos en TorrServer usando un POST."""
    try:
        response = requests.post(f"{TORRSERVER_URL}/torrents", json={"action": "list"})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error al obtener torrents de TorrServer: {e}")
        return []

def generar_magnet_con_trackers(torrent_hash):
    """Genera el enlace magnet con los trackers privados."""
    magnet_link = f"magnet:?xt=urn:btih:{torrent_hash}"
    for tracker in TRACKERS:
        magnet_link += f"&tr={tracker}"
    return magnet_link

def main():
    session = iniciar_sesion_qbittorrent()
    if not session:
        return
    
    torrents_torrserver = obtener_torrents_torrserver()
    torrents_qbittorrent = obtener_torrents_qbittorrent(session)
    qbt_hashes = [torrent['hash'] for torrent in torrents_qbittorrent]
    
    for torrent in torrents_torrserver:
        torrent_hash = torrent['hash']
        print(f"Procesando torrent: {torrent['title']}")
        
        if torrent_hash in qbt_hashes:
            print(f"El torrent {torrent['title']} ya está en qBittorrent.")
            continue
        
        torrent_progress = obtener_progreso_torrent(torrent_hash)
        
        if torrent_progress >= QBT_DOWNLOAD_THRESHOLD:
            magnet_link = generar_magnet_con_trackers(torrent_hash)
            if QBT_ADD_PAUSED:
                print(f"Añadiendo torrent {torrent['title']} a qBittorrent en modo pausado.")
            else:
                print(f"Añadiendo torrent {torrent['title']} a qBittorrent.")
            agregar_torrent_a_qbittorrent(magnet_link, session)
        else:
            print(f"El progreso del torrent {torrent['title']} no ha alcanzado el umbral de {QBT_DOWNLOAD_THRESHOLD}%." )

if __name__ == "__main__":
    main()
