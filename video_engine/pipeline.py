import os
import time
import asyncio
import traceback
from ai_generator import AIGenerator
from video_processor import VideoProcessor
from subtitle_generator import SubtitleGenerator
from config import Config
from logger import setup_logger

logger = setup_logger("VideoPipeline")


class VideoPipeline:
    """
    Orchestrateur final qui lie toutes les briques (Voix-Off Edge-TTS, Horodatages WordBoundary,
    Incrustation Image Produit, Montage Anti-Shadowban MoviePy 2.x et Sous-titres Dynamiques).
    """
    def __init__(self, workspace_dir=None):
        self.workspace = workspace_dir or Config.WORKSPACE_DIR
        self.library_dir = os.path.join(self.workspace, "library")
        self.renders_dir = os.path.join(self.workspace, "renders")

        os.makedirs(self.library_dir, exist_ok=True)
        os.makedirs(self.renders_dir, exist_ok=True)

        try:
            self.video_processor = VideoProcessor()
            self.subtitle_generator = SubtitleGenerator(
                model_size=Config.WHISPER_MODEL,
                compute_type=Config.WHISPER_COMPUTE_TYPE
            )
        except Exception as e:
            logger.critical(f"Erreur fatale lors de l'initialisation des composants : {e}")
            logger.critical(traceback.format_exc())
            raise

    async def render_for_video_record(
        self,
        video_id: int,
        product_name: str,
        niche: str,
        script_text: str,
        source_video_path: str = None,
        bg_music_path: str = None,
        product_image_url: str = None,
        voice: str = None
    ):
        """
        Exécute le pipeline complet pour un enregistrement `videos` du Hub Laravel.
        Retourne (success: bool, web_relative_path: str, duration_seconds: int)
        """
        logger.info(f"=== DÉBUT DU PIPELINE VIDÉO #{video_id} ({product_name}) ===")

        timestamp = int(time.time())
        audio_path = os.path.join(self.renders_dir, f"temp_voice_{video_id}_{timestamp}.mp3")
        final_filename = f"video_{video_id}_{timestamp}.mp4"
        final_output_path = os.path.join(self.renders_dir, final_filename)
        web_relative_path = f"/medias/renders/{final_filename}"

        if not source_video_path or not os.path.exists(source_video_path):
            default_broll = os.path.join(self.library_dir, "default_broll.mp4")
            source_video_path = self.video_processor.ensure_default_broll(default_broll)

        try:
            if not script_text or not script_text.strip():
                logger.info("Étape 1/3 : Aucun script fourni, génération via Ollama...")
                script_text = AIGenerator.generate_script(product_name, niche)
            else:
                logger.info("Étape 1/3 : Utilisation du script approuvé dans le Hub.")

            logger.info("Étape 2/3 : Synthèse vocale Edge-TTS & Horodatage des mots...")
            word_timestamps = await AIGenerator.generate_voiceover_with_timestamps(
                script_text,
                audio_path,
                voice=voice
            )

            logger.info("Étape 3/3 : Création des sous-titres dynamiques, incrustation image & Montage MP4...")
            subtitle_clips = self.subtitle_generator.build_subtitle_clips(
                word_timestamps=word_timestamps,
                video_size=Config.TARGET_RESOLUTION,
                audio_path=audio_path
            )

            success, duration_sec = self.video_processor.assemble_video(
                source_video_path=source_video_path,
                voiceover_path=audio_path,
                output_path=final_output_path,
                subtitle_clips=subtitle_clips,
                bg_music_path=bg_music_path,
                product_image_url=product_image_url,
                product_name=product_name
            )

            if not success or not os.path.exists(final_output_path):
                raise RuntimeError("Le fichier MP4 final n'a pas pu être généré.")

            logger.info(f"=== PIPELINE TERMINÉ AVEC SUCCÈS : {web_relative_path} ({duration_sec}s) ===")
            return True, web_relative_path, duration_sec

        finally:
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception:
                    pass
