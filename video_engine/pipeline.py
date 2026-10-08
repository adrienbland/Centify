import os
import asyncio
from ai_generator import AIGenerator
from video_processor import VideoProcessor
from subtitle_generator import SubtitleGenerator

class VideoPipeline:
    """
    Orchestrateur final qui lie toutes les briques pour générer une vidéo prête à être publiée.
    """
    def __init__(self, workspace_dir="/app/medias"):
        self.workspace = workspace_dir
        self.video_processor = VideoProcessor()
        self.subtitle_generator = SubtitleGenerator(model_size="small")
        
        # Création des dossiers si nécessaire
        os.makedirs(self.workspace, exist_ok=True)

    async def run(self, product_name, niche, source_video_path):
        """
        Exécute le pipeline de bout en bout.
        """
        print(f"=== DEBUT DU PIPELINE POUR : {product_name} ===")
        
        # Chemins temporaires et finaux
        base_name = product_name.replace(" ", "_").lower()
        audio_path = os.path.join(self.workspace, f"{base_name}_audio.mp3")
        temp_video_path = os.path.join(self.workspace, f"{base_name}_temp.mp4")
        final_output_path = os.path.join(self.workspace, f"{base_name}_final.mp4")
        
        if not os.path.exists(source_video_path):
            print(f"[ERREUR] Vidéo source introuvable : {source_video_path}")
            return False

        # 1. IA : Script
        script_text = AIGenerator.generate_script(product_name, niche)
        print(f"--- Script final ---\n{script_text}\n--------------------")
        
        # 2. IA : Voix-off
        await AIGenerator.generate_voiceover(script_text, audio_path)
        
        # 3. Vidéo : Traitement Anti-Shadowban + Crop + Audio
        success = self.video_processor.assemble_video(source_video_path, audio_path, temp_video_path)
        if not success:
            print("[ERREUR] Échec du traitement vidéo de base.")
            return False
            
        # 4. Vidéo : Sous-titrage Dynamique (Whisper)
        self.subtitle_generator.overlay_subtitles_on_video(temp_video_path, audio_path, final_output_path)
        
        # Nettoyage
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
            
        print(f"=== PIPELINE TERMINE ! ===")
        print(f"Vidéo finale prête : {final_output_path}")
        return True

if __name__ == "__main__":
    # Test local simulé
    pipeline = VideoPipeline(workspace_dir="./medias")
    
    # Pour que cela fonctionne, il faut un fichier 'brut.mp4' dans le dossier courant
    # asyncio.run(pipeline.run("Projecteur LED 4K", "Tech/Gadgets", "./brut.mp4"))
    print("Pipeline initialisé et prêt à l'emploi.")
