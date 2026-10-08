import time
import os
import mysql.connector
from datetime import datetime
import logging
import traceback

# Setup detailed logging for debug phase
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("logs/worker_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB_HOST = os.getenv('DB_HOST', 'db')
DB_USER = os.getenv('DB_USER', 'centify')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'centify')
DB_NAME = os.getenv('DB_NAME', 'centify')

def connect_db():
    try:
        return mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
    except Exception as e:
        logger.error(f"Erreur de connexion BDD: {e}")
        return None

def process_rendering_videos():
    conn = connect_db()
    if not conn:
        return
        
    try:
        cursor = conn.cursor(dictionary=True)
        # Find videos in 'rendering' status
        cursor.execute("SELECT id, status, product_id FROM videos WHERE status = 'rendering'")
        videos = cursor.fetchall()
        
        for video in videos:
            logger.info(f"Traitement de la vidéo ID: {video['id']}")
            try:
                # TODO: Integrate pipeline.py here (Ollama, Edge-TTS, MoviePy)
                # For now, simulate work
                time.sleep(2)
                
                # Update status to ready
                cursor.execute(
                    "UPDATE videos SET status = 'ready', updated_at = NOW() WHERE id = %s", 
                    (video['id'],)
                )
                conn.commit()
                logger.info(f"Vidéo ID: {video['id']} générée avec succès (statut: ready)")
                
                # Log success to api_logs
                cursor.execute(
                    "INSERT INTO api_logs (service, endpoint, payload, response, status_code, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())",
                    ("VideoEngine", "pipeline", f"video_id:{video['id']}", "Success", 200)
                )
                conn.commit()

            except Exception as e:
                error_msg = traceback.format_exc()
                logger.error(f"Erreur lors du traitement de la vidéo {video['id']}:\n{error_msg}")
                # Set status to failed
                cursor.execute(
                    "UPDATE videos SET status = 'failed', updated_at = NOW() WHERE id = %s", 
                    (video['id'],)
                )
                conn.commit()
                
                # Log error in db
                cursor.execute(
                    "INSERT INTO api_logs (service, endpoint, payload, response, status_code, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())",
                    ("VideoEngine", "pipeline", f"video_id:{video['id']}", error_msg, 500)
                )
                conn.commit()
                
        cursor.close()
    except Exception as e:
        logger.error(f"Erreur DB globale:\n{traceback.format_exc()}")
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Démarrage du Centify Video Daemon Worker...")
    while True:
        process_rendering_videos()
        time.sleep(5)  # Poll every 5 seconds
