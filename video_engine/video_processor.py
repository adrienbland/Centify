import os
import random
import subprocess
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, vfx
from config import Config
from logger import setup_logger

logger = setup_logger("VideoProcessor")

class VideoProcessor:
    """
    Moteur de rendu vidéo automatisé (MoviePy 2.x).
    Applique des transformations dynamiques pour éviter le shadowban (contenu dupliqué),
    gère le bouclage automatique du B-Roll et mixe la voix-off + sous-titres en une seule passe.
    """
    def __init__(self):
        self.target_resolution = Config.TARGET_RESOLUTION

    @staticmethod
    def ensure_default_broll(default_broll_path):
        """
        Si aucun B-Roll n'est présent sur le disque, génère automatiquement une vidéo
        verticale (1080x1920) fluide et moderne via FFmpeg pour garantir que le pipeline
        puisse toujours tourner sans erreur.
        """
        if os.path.exists(default_broll_path) and os.path.getsize(default_broll_path) > 10000:
            return default_broll_path

        os.makedirs(os.path.dirname(default_broll_path), exist_ok=True)
        logger.info(f"Génération d'un B-Roll vertical par défaut vers {default_broll_path}...")

        # Génère un fond animé dégradé sombre/violet esthétique en 1080x1920 (20 secondes, 24 fps)
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", (
                "gradients=s=1080x1920:r=24:d=20:c0=0x1e1b4b:c1=0x581c87:c2=0x0f172a:c3=0x3b0764:speed=0.03"
            ),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            default_broll_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            # Fallback universel si le filtre gradients n'est pas compilé dans cette version de ffmpeg
            cmd_fallback = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", "color=c=0x1e1b4b:s=1080x1920:r=24:d=20",
                "-vf", "geq=r='30+25*sin(2*PI*(T/4+Y/1920))':g='15+10*cos(2*PI*(T/5+X/1080))':b='65+45*sin(2*PI*(T/3+(X+Y)/3000))'",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "ultrafast",
                default_broll_path
            ]
            subprocess.run(cmd_fallback, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        logger.info("B-Roll vertical par défaut généré avec succès.")
        return default_broll_path

    def apply_transformations(self, clip):
        """
        Applique un ensemble de transformations aléatoires mais esthétiques (MoviePy 2.x)
        pour rendre le hash visuel de chaque vidéo unique (Anti-Shadowban).
        """
        try:
            effects = []
            # 1. Flip horizontal aléatoire
            if random.choice([True, False]):
                effects.append(vfx.MirrorX())

            # 2. Ajustement colorimétrique subtil (+/- 6%)
            lum_factor = random.uniform(0.94, 1.06)
            effects.append(vfx.MultiplyColor(lum_factor))

            if effects:
                clip = clip.with_effects(effects)

            return clip
        except Exception as e:
            logger.error(f"Erreur lors de l'application des transformations: {e}")
            return clip

    def crop_to_vertical(self, clip):
        """
        Recadre la vidéo au format vertical (9:16 - 1080x1920) en centrant l'action.
        """
        try:
            w, h = clip.size
            target_w, target_h = self.target_resolution
            if (w, h) == (target_w, target_h):
                return clip

            target_ratio = target_w / target_h
            clip_ratio = w / h

            if clip_ratio > target_ratio:
                new_w = int(h * target_ratio)
                clip = clip.cropped(x_center=w / 2, width=new_w)
            elif clip_ratio < target_ratio:
                new_h = int(w / target_ratio)
                clip = clip.cropped(y_center=h / 2, height=new_h)

            clip = clip.resized(self.target_resolution)
            return clip
        except Exception as e:
            logger.error(f"Erreur lors du recadrage vertical: {e}")
            raise

    def assemble_video(
        self,
        source_video_path,
        voiceover_path,
        output_path,
        subtitle_clips=None,
        bg_music_path=None
    ):
        """
        Assemble en une seule passe :
        - Vidéo B-Roll (bouclée ou coupée à la durée exacte de la voix-off)
        - Transformations Anti-Shadowban + Recadrage 9:16
        - Voix-off IA (+ musique de fond optionnelle à volume réduit)
        - Sous-titres dynamiques TikTok
        Retourne (success: bool, duration_seconds: int)
        """
        logger.info(f"Assemblage vidéo depuis la source : {source_video_path}...")
        video_clip = None
        audio_clip = None
        bg_music_clip = None
        final_clip = None

        try:
            video_clip = VideoFileClip(source_video_path)
            audio_clip = AudioFileClip(voiceover_path)

            # Durée cible = durée de la voix-off + 0.3s de respiration finale
            target_duration = max(audio_clip.duration + 0.3, 1.0)

            video_clip = self.apply_transformations(video_clip)
            video_clip = self.crop_to_vertical(video_clip)

            # Si le B-Roll est plus court que la voix-off, on le boucle automatiquement
            if video_clip.duration < target_duration:
                video_clip = video_clip.with_effects([vfx.Loop(duration=target_duration)])
            else:
                video_clip = video_clip.subclipped(0, target_duration)

            # Mixage audio : Voix-off + Musique de fond optionnelle (à 12% du volume)
            final_audio = audio_clip
            if bg_music_path and os.path.exists(bg_music_path):
                try:
                    bg_music_clip = AudioFileClip(bg_music_path)
                    if bg_music_clip.duration < target_duration:
                        # Répétition simple si la musique est plus courte
                        loops = int(target_duration // bg_music_clip.duration) + 1
                        from moviepy import concatenate_audioclips
                        bg_music_clip = concatenate_audioclips([bg_music_clip] * loops)
                    bg_music_clip = bg_music_clip.subclipped(0, target_duration).with_volume_scaled(0.12)
                    final_audio = CompositeAudioClip([bg_music_clip, audio_clip])
                except Exception as music_err:
                    logger.warning(f"Musique de fond ignorée ({music_err}), utilisation de la voix-off seule.")

            video_clip = video_clip.with_audio(final_audio)

            # Superposition des sous-titres dynamiques en une seule passe d'encodage
            if subtitle_clips:
                final_clip = CompositeVideoClip([video_clip] + subtitle_clips).with_duration(target_duration)
            else:
                final_clip = video_clip

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            temp_audio = os.path.join(os.path.dirname(output_path), f"temp_audio_{random.randint(1000,9999)}.m4a")

            logger.info(f"Encodage MP4 en cours vers {output_path} ({target_duration:.1f}s)...")
            final_clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=temp_audio,
                remove_temp=True,
                fps=24,
                threads=4,
                preset="ultrafast",
                logger=None
            )

            logger.info("Rendu vidéo terminé avec succès !")
            return True, int(round(target_duration))

        except Exception as e:
            logger.error(f"Erreur lors de l'assemblage de la vidéo : {e}")
            raise
        finally:
            for c in (final_clip, video_clip, audio_clip, bg_music_clip):
                if c is not None:
                    try:
                        c.close()
                    except Exception:
                        pass
