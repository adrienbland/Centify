import time
import os
import json
import uuid
import asyncio
import logging
import traceback
import mysql.connector
from pipeline import VideoPipeline
from ai_generator import AIGenerator
from config import Config

# Configuration des logs détaillés
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/worker_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CentifyWorker")

DB_HOST = os.getenv("DB_HOST", "db")
DB_USER = os.getenv("DB_USER", "centify_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "centify_pass")
DB_NAME = os.getenv("DB_NAME", "centify_db")


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


def send_filament_notification(cursor, title: str, body: str, status: str = "success"):
    """
    Envoie une notification directement dans la table `notifications` de Filament
    pour faire apparaître la bulle rouge en haut à droite du Dashboard en temps réel.
    """
    icon_map = {
        "success": ("heroicon-o-check-circle", "success"),
        "warning": ("heroicon-o-exclamation-triangle", "warning"),
        "danger": ("heroicon-o-x-circle", "danger"),
        "info": ("heroicon-o-information-circle", "info"),
    }
    icon, icon_color = icon_map.get(status, ("heroicon-o-bell", "primary"))

    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()

    payload = json.dumps({
        "actions": [],
        "body": body,
        "color": None,
        "duration": "persistent",
        "icon": icon,
        "iconColor": icon_color,
        "status": status,
        "title": title,
        "view": "filament-notifications::notification",
        "viewData": [],
        "format": "filament"
    }, ensure_ascii=False)

    for user in users:
        user_id = user["id"] if isinstance(user, dict) else user[0]
        cursor.execute(
            """
            INSERT INTO notifications (id, type, notifiable_type, notifiable_id, data, read_at, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NULL, NOW(), NOW())
            """,
            (
                str(uuid.uuid4()),
                "Filament\\Notifications\\DatabaseNotification",
                "App\\Models\\User",
                user_id,
                payload
            )
        )


def log_api_event(cursor, service: str, endpoint: str, payload_dict: dict, response_dict: dict, status_code: int, error_msg: str = None):
    """
    Enregistre proprement les logs dans `api_logs` (en respectant les colonnes JSON et ENUM).
    """
    valid_service = service if service in ("shopify", "tiktok", "ollama", "system") else "system"
    cursor.execute(
        """
        INSERT INTO api_logs (service, endpoint, payload, response, status_code, error_message, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        """,
        (
            valid_service,
            endpoint,
            json.dumps(payload_dict, ensure_ascii=False),
            json.dumps(response_dict, ensure_ascii=False),
            status_code,
            error_msg
        )
    )


def resolve_media_asset(cursor, asset_type: str):
    """
    Cherche un asset (b_roll ou audio) dans la table `media_library`.
    Retourne le chemin absolu sur le disque `/app/medias/...` s'il existe.
    """
    cursor.execute(
        "SELECT file_path FROM media_library WHERE type = %s ORDER BY RAND() LIMIT 1",
        (asset_type,)
    )
    row = cursor.fetchone()
    if not row or not row.get("file_path"):
        return None

    rel_path = row["file_path"].lstrip("/")
    if rel_path.startswith("medias/"):
        rel_path = rel_path[len("medias/"):]

    candidate = os.path.join(Config.WORKSPACE_DIR, rel_path)
    if os.path.exists(candidate):
        return candidate
    return None


def ensure_default_broll_registered(pipeline: VideoPipeline):
    """
    S'assure au démarrage qu'un B-Roll par défaut existe physiquement ET dans la table `media_library`.
    """
    default_broll_abs = os.path.join(Config.LIBRARY_DIR, "default_broll.mp4")
    pipeline.video_processor.ensure_default_broll(default_broll_abs)

    conn = connect_db()
    if not conn:
        return
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM media_library WHERE file_path LIKE '%default_broll.mp4%' LIMIT 1")
        if not cursor.fetchone():
            cursor.execute(
                """
                INSERT INTO media_library (type, name, file_path, tags, created_at, updated_at)
                VALUES ('b_roll', 'Fond Dynamique Neon Purple (9:16)', 'library/default_broll.mp4', 'default,neon,vertical,tiktok', NOW(), NOW())
                """
            )
            conn.commit()
            logger.info("B-Roll par défaut enregistré dans la Médiathèque (media_library).")
        cursor.close()
    except Exception as e:
        logger.warning(f"Impossible d'enregistrer le B-Roll par défaut en BDD : {e}")
    finally:
        conn.close()


def process_pending_videos(pipeline: VideoPipeline):
    conn = connect_db()
    if not conn:
        return

    try:
        cursor = conn.cursor(dictionary=True)
        # Récupère les vidéos en attente de rendu ('rendering') OU demandant une retouche IA ('needs_revision')
        cursor.execute(
            """
            SELECT v.id, v.status, v.product_id, v.script_id, v.user_feedback, v.social_network,
                   p.name AS product_name, p.niche AS product_niche, p.description AS product_description,
                   p.image_url AS product_image_url, p.gallery_images AS product_gallery_images,
                   s.full_text AS script_full_text, s.hook AS script_hook, s.body AS script_body, s.cta AS script_cta
            FROM videos v
            LEFT JOIN products p ON v.product_id = p.id
            LEFT JOIN scripts s ON v.script_id = s.id
            WHERE v.status IN ('rendering', 'needs_revision')
            ORDER BY v.updated_at ASC
            """
        )
        videos = cursor.fetchall()

        for video in videos:
            vid_id = video["id"]
            initial_status = video["status"]
            product_name = video["product_name"] or f"Produit #{video['product_id']}"
            niche = video["product_niche"] or "E-commerce"
            script_text = video["script_full_text"] or ""
            product_image_url = video.get("product_image_url")
            product_gallery_images = video.get("product_gallery_images")
            script_hook = video.get("script_hook")

            logger.info(f"🎬 Début du traitement de la vidéo #{vid_id} (statut: {initial_status}) pour '{product_name}'")

            try:
                # Si la vidéo est en statut 'needs_revision' avec un commentaire utilisateur,
                # on utilise Ollama pour réécrire le script selon la consigne avant de relancer le rendu !
                if initial_status == "needs_revision" and video.get("user_feedback"):
                    feedback = video["user_feedback"].strip()
                    logger.info(f"🔄 Retouche IA demandée sur la vidéo #{vid_id} : {feedback}")
                    script_text = AIGenerator.revise_script_with_feedback(
                        original_text=script_text,
                        product_name=product_name,
                        user_feedback=feedback
                    )
                    if video.get("script_id"):
                        cursor.execute(
                            "UPDATE scripts SET full_text = %s, updated_at = NOW() WHERE id = %s",
                            (script_text, video["script_id"])
                        )
                        conn.commit()

                # Sélection d'un B-Roll et d'une musique de fond éventuelle depuis la Médiathèque
                broll_path = resolve_media_asset(cursor, "b_roll")
                bg_music_path = resolve_media_asset(cursor, "audio")

                # Exécution du pipeline complet (Edge-TTS + WordBoundary + Multi-Scènes Ken Burns + Sous-titres)
                success, web_path, duration_sec = asyncio.run(
                    pipeline.render_for_video_record(
                        video_id=vid_id,
                        product_name=product_name,
                        niche=niche,
                        script_text=script_text,
                        source_video_path=broll_path,
                        bg_music_path=bg_music_path,
                        product_image_url=product_image_url,
                        gallery_images=product_gallery_images,
                        hook_text=script_hook
                    )
                )

                # Mise à jour de la vidéo en statut 'ready'
                cursor.execute(
                    """
                    UPDATE videos
                    SET status = 'ready',
                        file_path = %s,
                        duration_seconds = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (web_path, duration_sec, vid_id)
                )

                # Log dans api_logs
                log_api_event(
                    cursor,
                    service="system",
                    endpoint="video_engine/pipeline",
                    payload_dict={"video_id": vid_id, "product": product_name, "initial_status": initial_status},
                    response_dict={"file_path": web_path, "duration_seconds": duration_sec, "status": "ready"},
                    status_code=200
                )

                # Notification dans la cloche Filament
                notif_title = "🎬 Vidéo prête à être visionnée !" if initial_status == "rendering" else "🔄 Vidéo retouchée par l'IA prête !"
                send_filament_notification(
                    cursor,
                    title=notif_title,
                    body=f"Le montage MP4 ({duration_sec}s) pour « {product_name} » est terminé.",
                    status="success"
                )

                conn.commit()
                logger.info(f"✅ Vidéo #{vid_id} disponible sur {web_path} ({duration_sec}s)")

            except Exception as e:
                error_msg = traceback.format_exc()
                logger.error(f"❌ Erreur lors du traitement de la vidéo #{vid_id}:\n{error_msg}")

                cursor.execute(
                    "UPDATE videos SET status = 'failed', updated_at = NOW() WHERE id = %s",
                    (vid_id,)
                )
                log_api_event(
                    cursor,
                    service="system",
                    endpoint="video_engine/pipeline",
                    payload_dict={"video_id": vid_id, "product": product_name},
                    response_dict={"status": "failed"},
                    status_code=500,
                    error_msg=str(e)
                )
                send_filament_notification(
                    cursor,
                    title="❌ Échec du rendu vidéo",
                    body=f"Une erreur est survenue sur la vidéo #{vid_id} ({product_name}) : {str(e)[:120]}",
                    status="danger"
                )
                conn.commit()

        cursor.close()
    except Exception:
        logger.error(f"Erreur DB globale:\n{traceback.format_exc()}")
    finally:
        conn.close()


if __name__ == "__main__":
    logger.info("🚀 Démarrage du Centify Video Daemon Worker (MoviePy 2.x + Edge-TTS)...")
    pipeline_instance = VideoPipeline()
    ensure_default_broll_registered(pipeline_instance)
    while True:
        process_pending_videos(pipeline_instance)
        time.sleep(5)
