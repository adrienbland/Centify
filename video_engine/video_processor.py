import os
import random
from moviepy.editor import VideoFileClip, AudioFileClip, vfx
import moviepy.video.fx.all as vfx_all
from config import Config
from logger import setup_logger

logger = setup_logger("VideoProcessor")

class VideoProcessor:
    """
    Moteur de rendu vidéo automatisé.
    Applique des transformations dynamiques pour éviter le shadowban (contenu dupliqué).
    """
    def __init__(self):
        self.target_resolution = Config.TARGET_RESOLUTION
        
    def apply_transformations(self, clip):
        """
        Applique un ensemble de transformations aléatoires mais esthétiques
        pour rendre chaque vidéo unique.
        """
        try:
            # 1. Flip horizontal aléatoire
            if random.choice([True, False]):
                clip = clip.fx(vfx_all.mirror_x)
                
            # 2. Variation de la vitesse (Speed Ramp)
            speed_factor = random.uniform(Config.SPEED_RAMP_MIN, Config.SPEED_RAMP_MAX)
            clip = clip.fx(vfx_all.speedx, speed_factor)
            
            # 3. Ajustement colorimétrique léger
            lum_factor = random.uniform(0.9, 1.1)
            clip = clip.fx(vfx_all.colorx, lum_factor)
            
            return clip
        except Exception as e:
            logger.error(f"Erreur lors de l'application des transformations: {e}")
            raise

    def crop_to_vertical(self, clip):
        """
        Recadre la vidéo au format vertical (9:16) en centrant l'action.
        """
        try:
            w, h = clip.size
            target_ratio = self.target_resolution[0] / self.target_resolution[1]
            clip_ratio = w / h
            
            if clip_ratio > target_ratio:
                new_w = int(h * target_ratio)
                x_center = w / 2
                clip = clip.crop(x_center=x_center, width=new_w)
            else:
                new_h = int(w / target_ratio)
                y_center = h / 2
                clip = clip.crop(y_center=y_center, height=new_h)
                
            clip = clip.resize(self.target_resolution)
            return clip
        except Exception as e:
            logger.error(f"Erreur lors du recadrage vertical: {e}")
            raise

    def assemble_video(self, source_video_path, voiceover_path, output_path):
        """
        Assemble la vidéo source avec la voix off générée.
        """
        logger.info(f"Traitement de la vidéo source : {source_video_path}...")
        
        try:
            video_clip = VideoFileClip(source_video_path)
            audio_clip = AudioFileClip(voiceover_path)
            
            video_clip = self.apply_transformations(video_clip)
            video_clip = self.crop_to_vertical(video_clip)
            
            video_clip = video_clip.subclip(0, audio_clip.duration)
            final_clip = video_clip.set_audio(audio_clip)
            
            logger.info(f"Rendu en cours vers {output_path}...")
            final_clip.write_videofile(
                output_path, 
                codec="libx264", 
                audio_codec="aac", 
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
                fps=30,
                threads=4,
                preset="ultrafast",
                logger=None # Désactive le logging interne très verbeux de moviepy
            )
            
            logger.info("Rendu vidéo terminé avec succès !")
            
            # Libération mémoire
            video_clip.close()
            audio_clip.close()
            final_clip.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'assemblage de la vidéo : {e}")
            return False

if __name__ == "__main__":
    logger.info("VideoProcessor initialisé. Prêt pour l'assemblage.")
