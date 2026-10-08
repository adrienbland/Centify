import os
import random
from moviepy.editor import VideoFileClip, AudioFileClip, vfx
import moviepy.video.fx.all as vfx_all

class VideoProcessor:
    """
    Moteur de rendu vidéo automatisé.
    Applique des transformations dynamiques pour éviter le shadowban (contenu dupliqué).
    """
    def __init__(self, target_resolution=(1080, 1920)):
        self.target_resolution = target_resolution
        
    def apply_transformations(self, clip):
        """
        Applique un ensemble de transformations aléatoires mais esthétiques
        pour rendre chaque vidéo unique.
        """
        # 1. Flip horizontal aléatoire (très efficace contre le hachage vidéo)
        if random.choice([True, False]):
            clip = clip.fx(vfx_all.mirror_x)
            
        # 2. Variation infime de la vitesse (Speed Ramp) pour changer la durée exacte
        speed_factor = random.uniform(0.95, 1.05)
        clip = clip.fx(vfx_all.speedx, speed_factor)
        
        # 3. Ajustement colorimétrique léger
        # On ajuste le gamma ou la luminosité très légèrement
        lum_factor = random.uniform(0.9, 1.1)
        clip = clip.fx(vfx_all.colorx, lum_factor)
        
        return clip

    def crop_to_vertical(self, clip):
        """
        Recadre la vidéo au format vertical (9:16) en centrant l'action.
        """
        w, h = clip.size
        target_ratio = self.target_resolution[0] / self.target_resolution[1]
        clip_ratio = w / h
        
        if clip_ratio > target_ratio:
            # La vidéo est trop large, on coupe les bords gauche/droite
            new_w = int(h * target_ratio)
            x_center = w / 2
            clip = clip.crop(x_center=x_center, width=new_w)
        else:
            # La vidéo est trop haute, on coupe en haut/bas (rare pour du scrape)
            new_h = int(w / target_ratio)
            y_center = h / 2
            clip = clip.crop(y_center=y_center, height=new_h)
            
        # Redimensionnement final pour correspondre exactement à 1080x1920
        clip = clip.resize(self.target_resolution)
        return clip

    def assemble_video(self, source_video_path, voiceover_path, output_path):
        """
        Assemble la vidéo source avec la voix off générée.
        """
        print(f"[VideoProcessor] Traitement de {source_video_path}...")
        
        try:
            # Chargement des médias
            video_clip = VideoFileClip(source_video_path)
            audio_clip = AudioFileClip(voiceover_path)
            
            # Application des filtres anti-shadowban
            video_clip = self.apply_transformations(video_clip)
            
            # Recadrage TikTok/Reels/Shorts
            video_clip = self.crop_to_vertical(video_clip)
            
            # Couper la vidéo à la durée exacte de la voix off
            video_clip = video_clip.subclip(0, audio_clip.duration)
            
            # Ajouter la piste audio
            final_clip = video_clip.set_audio(audio_clip)
            
            # Rendu final
            print(f"[VideoProcessor] Rendu en cours vers {output_path}...")
            final_clip.write_videofile(
                output_path, 
                codec="libx264", 
                audio_codec="aac", 
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
                fps=30,
                threads=4,
                preset="ultrafast" # Rapide pour les tests
            )
            
            print("[VideoProcessor] Rendu terminé avec succès !")
            
            # Nettoyage mémoire
            video_clip.close()
            audio_clip.close()
            final_clip.close()
            
            return True
            
        except Exception as e:
            print(f"[VideoProcessor] Erreur lors du rendu : {e}")
            return False

if __name__ == "__main__":
    # Test local simulé
    processor = VideoProcessor()
    # Remplacer par des chemins valides pour tester
    # processor.assemble_video("brut.mp4", "test_audio.mp3", "rendu_tiktok.mp4")
    print("VideoProcessor initialisé. Prêt pour l'assemblage.")
