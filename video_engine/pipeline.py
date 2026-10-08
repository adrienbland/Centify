import os
import asyncio
import traceback
from ai_generator import AIGenerator
from video_processor import VideoProcessor
from subtitle_generator import SubtitleGenerator
from logger import setup_logger

logger = setup_logger("VideoPipeline")

class VideoPipeline:
    """
    Orchestrateur final qui lie toutes les briques pour générer une vidéo prête à être publiée.
    """
    def __init__(self, workspace_dir="/app/medias"):
        self.workspace = workspace_dir
        
        try:
            self.video_processor = VideoProcessor()
            self.subtitle_generator = SubtitleGenerator(model_size="small")
        except Exception as e:
            logger.critical(f"Erreur fatale lors de l'initialisation des composants : {e}")
            logger.critical(traceback.format_exc())
            raise
        
        # Création des dossiers si nécessaire
        os.makedirs(self.workspace, exist_ok=True)

    async def run(self, product_name, niche, source_video_path):
        """
        Exécute le pipeline de bout en bout.
        """
        logger.info(f"=== DEBUT DU PIPELINE POUR : {product_name} ===")
        
        # Chemins temporaires et finaux
        base_name = product_name.replace(" ", "_").lower()
        audio_path = os.path.join(self.workspace, f"{base_name}_audio.mp3")
        temp_video_path = os.path.join(self.workspace, f"{base_name}_temp.mp4")
        final_output_path = os.path.join(self.workspace, f"{base_name}_final.mp4")
        
        if not os.path.exists(source_video_path):
            logger.error(f"Vidéo source introuvable : {source_video_path}")
            return False

        try:
            # 1. IA : Script
            logger.info("Étape 1/4 : Génération du script IA...")
            script_text = AIGenerator.generate_script(product_name, niche)
            logger.debug(f"Script final : {script_text}")
            
            # 2. IA : Voix-off
            logger.info("Étape 2/4 : Génération de la voix-off...")
            await AIGenerator.generate_voiceover(script_text, audio_path)
            
            # 3. Vidéo : Traitement Anti-Shadowban + Crop + Audio
            logger.info("Étape 3/4 : Traitement vidéo anti-shadowban...")
            success = self.video_processor.assemble_video(source_video_path, audio_path, temp_video_path)
            if not success:
                logger.error("Échec du traitement vidéo de base.")
                return False
                
            # 4. Vidéo : Sous-titrage Dynamique (Whisper)
            logger.info("Étape 4/4 : Incrustation des sous-titres dynamiques...")
            self.subtitle_generator.overlay_subtitles_on_video(temp_video_path, audio_path, final_output_path)
            
            logger.info(f"=== PIPELINE TERMINE AVEC SUCCÈS ! ===")
            logger.info(f"Vidéo finale disponible : {final_output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur inattendue pendant l'exécution du pipeline : {e}")
            logger.error(traceback.format_exc())
            return False
            
        finally:
            # Nettoyage
            logger.info("Nettoyage des fichiers temporaires...")
            if os.path.exists(audio_path):
                os.remove(audio_path)
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)

if __name__ == "__main__":
    # Test local simulé
    try:
        pipeline = VideoPipeline(workspace_dir="./medias")
        logger.info("Pipeline initialisé et prêt à l'emploi.")
    except Exception as e:
        logger.error("Impossible de démarrer le pipeline.")
